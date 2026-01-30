"""agent.server.ws_server

WebSocket 服务器

职责：
- 实现 WebSocket 服务器
- 处理客户端连接
- 实现消息路由
- 状态更新实时推送
"""

from __future__ import annotations

import asyncio
from typing import Dict, Optional, Set

try:
    import websockets
    # websockets 15.0+ 使用 asyncio.server.ServerConnection（支持 async for）
    try:
        from websockets.asyncio.server import ServerConnection
        WebSocketServerProtocol = ServerConnection  # 兼容性别名
    except ImportError:
        # 旧版本回退
        try:
            from websockets.server import ServerConnection
            WebSocketServerProtocol = ServerConnection
        except ImportError:
            from websockets.server import WebSocketServerProtocol
except ImportError:
    websockets = None  # type: ignore
    WebSocketServerProtocol = None  # type: ignore
    ServerConnection = None  # type: ignore

from agent.config import settings
from agent.controller.state_machine import State
from agent.controller.task_controller import TaskController
from agent.exceptions import TaskException
from agent.models.task_schema import TaskRequest
from agent.server.protocol import (
    ErrorMessage,
    Message,
    StartTaskMessage,
    StatusUpdateMessage,
    TaskResultMessage,
    parse_message,
    serialize_message,
)
from agent.utils.logger import get_logger

logger = get_logger(__name__)


class WebSocketServer:
    """WebSocket 服务器"""

    def __init__(self, task_controller: Optional[TaskController] = None):
        """
        初始化 WebSocket 服务器

        Args:
            task_controller: 任务控制器实例（可选，默认创建新实例）
        """
        if websockets is None:
            raise RuntimeError("websockets 模块未安装，请运行: pip install websockets")

        self.clients: Set[WebSocketServerProtocol] = set()
        self.task_controller = task_controller or TaskController()
        self._running_tasks: Dict[str, asyncio.Task] = {}  # task_id -> task
        self._shutdown_event = asyncio.Event()

    async def register_client(self, websocket: WebSocketServerProtocol) -> None:
        """注册客户端"""
        self.clients.add(websocket)
        logger.info(f"客户端已连接，当前连接数: {len(self.clients)}")

    async def unregister_client(self, websocket: WebSocketServerProtocol) -> None:
        """注销客户端"""
        self.clients.discard(websocket)
        logger.info(f"客户端已断开，当前连接数: {len(self.clients)}")

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str) -> None:
        """处理消息"""
        msg = parse_message(message)
        
        if isinstance(msg, StartTaskMessage):
            await self._handle_start_task(websocket, msg)
        else:
            await self._send_error(websocket, f"不支持的消息类型: {msg.type}")

    async def _handle_start_task(self, websocket: WebSocketServerProtocol, message: StartTaskMessage) -> None:
        """
        处理启动任务消息

        Args:
            websocket: WebSocket 连接
            message: 启动任务消息
        """
        task_id = message.task_id
        logger.info(f"开始处理启动任务消息: task_id={task_id}")

        # 检查是否已有相同任务在执行
        if task_id in self._running_tasks:
            logger.warning(f"任务 {task_id} 已在执行中")
            await self._send_error(websocket, f"任务 {task_id} 已在执行中", task_id)
            return

        try:
            # 创建任务请求
            logger.info(f"创建任务请求: task_id={task_id}, platform={message.payload.platform}")
            task = TaskRequest(
                task_id=task_id,
                platform=message.payload.platform,
                keywords=message.payload.keywords,
                max_items=message.payload.max_items,
            )
            logger.info(f"任务请求创建成功: {task}")

            logger.info(f"启动任务: {task_id}, 平台: {task.platform}, 关键词: {task.keywords}")

            # 启动任务执行（异步）
            logger.info(f"创建异步任务: task_id={task_id}")
            try:
                task_coro = self._execute_task_with_updates(websocket, task)
                running_task = asyncio.create_task(task_coro)
                self._running_tasks[task_id] = running_task
                logger.info(f"异步任务已创建并启动: task_id={task_id}")

                # 任务完成后清理
                def cleanup_task(done_task: asyncio.Task):
                    self._running_tasks.pop(task_id, None)
                    if done_task.exception():
                        logger.error(f"任务 {task_id} 执行异常: {done_task.exception()}", exc_info=True)
                        # 如果任务失败，尝试发送错误消息（但不关闭连接）
                        try:
                            # 注意：这里不能直接使用 websocket，因为可能已经关闭
                            # 错误消息应该在 _execute_task_with_updates 中发送
                            pass
                        except Exception:
                            pass

                running_task.add_done_callback(cleanup_task)
                logger.info(f"任务 {task_id} 启动完成，已在后台执行")
            except Exception as task_create_error:
                logger.error(f"创建异步任务失败: {task_create_error}", exc_info=True)
                await self._send_error(websocket, f"创建任务失败: {str(task_create_error)}", task_id)

        except Exception as e:
            logger.error(f"启动任务失败: {e}", exc_info=True)
            try:
                await self._send_error(websocket, str(e), task_id)
            except Exception as send_error:
                logger.error(f"发送错误消息失败: {send_error}", exc_info=True)

    async def _execute_task_with_updates(
        self, websocket: WebSocketServerProtocol, task: TaskRequest
    ) -> None:
        """
        执行任务并发送状态更新

        Args:
            websocket: WebSocket 连接
            task: 任务请求
        """
        try:
            logger.info(f"开始执行任务: {task.task_id}")
            
            # 注册状态更新回调
            # 注意：需要在任务执行前注册，因为状态转换会在 execute_task 中发生
            status_updates_sent = set()  # 避免重复发送相同状态

            def on_state_change(state: State) -> None:
                """状态变化回调"""
                try:
                    state_key = (state, task.task_id)
                    if state_key not in status_updates_sent:
                        status_updates_sent.add(state_key)
                        # 异步发送状态更新
                        asyncio.create_task(self._send_status_update(websocket, state, task.task_id))
                except Exception as e:
                    logger.error(f"状态回调执行失败: {e}", exc_info=True)

            # 为所有可能的状态注册回调
            # 注意：需要在任务执行前注册，因为状态转换会在 execute_task 中发生
            logger.info(f"注册状态回调: task_id={task.task_id}")
            for state in State:
                self.task_controller.state_machine.register_callback(state, on_state_change)

            # 发送初始状态（如果不在 IDLE）
            current_state = self.task_controller.state_machine.current_state
            logger.info(f"当前状态: {current_state}, task_id={task.task_id}")
            if current_state != State.IDLE:
                await self._send_status_update(websocket, current_state, task.task_id)

            # 执行任务
            logger.info(f"开始执行任务逻辑: task_id={task.task_id}")
            results = await self.task_controller.execute_task(task)
            logger.info(f"任务执行完成: task_id={task.task_id}, 结果数: {len(results)}")

            # 发送结果
            result_msg = TaskResultMessage(
                type="TASK_RESULT",
                results=[case.model_dump() for case in results],
            )
            await websocket.send(serialize_message(result_msg))
            logger.info(f"任务 {task.task_id} 完成，返回 {len(results)} 个结果")

        except TaskException as e:
            logger.error(f"任务执行失败: {e}", exc_info=True)
            try:
                await self._send_error(websocket, str(e), task.task_id)
            except Exception as send_error:
                logger.error(f"发送错误消息失败: {send_error}", exc_info=True)
        except Exception as e:
            logger.error(f"任务执行异常: {e}", exc_info=True)
            try:
                await self._send_error(websocket, f"任务执行异常: {e}", task.task_id)
            except Exception as send_error:
                logger.error(f"发送错误消息失败: {send_error}", exc_info=True)

    async def _send_status_update(
        self, websocket: WebSocketServerProtocol, state: State, task_id: str
    ) -> None:
        """
        发送状态更新

        Args:
            websocket: WebSocket 连接
            state: 当前状态
            task_id: 任务 ID
        """
        try:
            progress = self.task_controller.get_progress()
            msg = StatusUpdateMessage(
                type="STATUS_UPDATE",
                state=state.value,
                progress=progress,
                message=f"任务状态: {state.value}",
            )
            await websocket.send(serialize_message(msg))
            logger.debug(f"发送状态更新: {state.value}, 进度: {progress}%")
        except Exception as e:
            logger.error(f"发送状态更新失败: {e}")

    async def _send_error(
        self, websocket: WebSocketServerProtocol, error: str, task_id: Optional[str] = None
    ) -> None:
        """
        发送错误消息

        Args:
            websocket: WebSocket 连接
            error: 错误消息
            task_id: 任务 ID（可选）
        """
        try:
            msg = ErrorMessage(type="ERROR", error=error, task_id=task_id)
            await websocket.send(serialize_message(msg))
            logger.error(f"发送错误消息: {error}, 任务ID: {task_id}")
        except Exception as e:
            logger.error(f"发送错误消息失败: {e}")

    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """
        处理客户端连接

        Args:
            websocket: WebSocket 连接（path 可通过 websocket.path 获取）
        """
        # websockets 15.0+ 版本：path 通过 websocket.path 属性获取
        path = getattr(websocket, 'path', '')
        logger.info(f"新客户端连接: path={path}, remote={getattr(websocket, 'remote_address', 'unknown')}")
        await self.register_client(websocket)
        logger.info("开始监听客户端消息...")
        
        try:
            while True:
                message = await websocket.recv()
                logger.info(f"收到消息: {len(message)} 字符")
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"连接已关闭: code={e.code}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
            await self._send_error(websocket, str(e))
        finally:
            await self.unregister_client(websocket)
            logger.info("客户端处理完成，已注销")

    async def start(self) -> None:
        """启动 WebSocket 服务器"""
        logger.info(f"启动 WebSocket 服务器: ws://{settings.ws_host}:{settings.ws_port}")

        # 检查端口是否被占用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((settings.ws_host, settings.ws_port))
            sock.close()
        except OSError as e:
            if e.errno == 48:  # Address already in use
                logger.error(
                    f"端口 {settings.ws_port} 已被占用。"
                    f"请关闭占用该端口的进程，或修改 .env 文件中的 WS_PORT 配置。"
                )
                logger.info(f"查找占用端口的命令: lsof -i :{settings.ws_port}")
                logger.info(f"关闭进程的命令: kill -9 <PID>")
            raise

        try:
            async with websockets.serve(
                self._handle_client,
                settings.ws_host,
                settings.ws_port,
            ):
                logger.info(f"WebSocket 服务器已启动，监听 ws://{settings.ws_host}:{settings.ws_port}")
                # 等待关闭信号
                await self._shutdown_event.wait()
        except Exception as e:
            logger.error(f"WebSocket 服务器启动失败: {e}")
            raise

    async def shutdown(self) -> None:
        """优雅关闭服务器"""
        logger.info("正在关闭 WebSocket 服务器...")

        # 取消所有运行中的任务
        for task_id, task in list(self._running_tasks.items()):
            logger.info(f"取消任务: {task_id}")
            task.cancel()

        # 等待任务完成
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks.values(), return_exceptions=True)

        # 关闭所有客户端连接
        for client in list(self.clients):
            await client.close()

        # 触发关闭事件
        self._shutdown_event.set()
        logger.info("WebSocket 服务器已关闭")
