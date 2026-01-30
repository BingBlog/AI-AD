"""agent.main

Agent 启动入口

职责：
- 集成 WebSocket 服务器
- 实现优雅关闭
- 处理信号
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from agent.config import settings
from agent.server.ws_server import WebSocketServer
from agent.utils.logger import setup_logger

logger = setup_logger("agent")

# 全局服务器实例（用于信号处理）
_server: Optional[WebSocketServer] = None


def signal_handler(sig, frame):
    """信号处理器（用于优雅关闭）"""
    logger.info(f"收到信号 {sig}，正在关闭...")
    if _server:
        # 创建关闭任务
        asyncio.create_task(_server.shutdown())
    else:
        sys.exit(0)


async def main():
    """Agent 主入口"""
    global _server

    logger.info("=" * 60)
    logger.info("Ad Browser Agent 启动中...")
    logger.info("=" * 60)
    logger.info(f"配置信息: {settings}")

    try:
        # 创建 WebSocket 服务器
        _server = WebSocketServer()

        # 注册信号处理器（优雅关闭）
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 启动服务器
        logger.info("启动 WebSocket 服务器...")
        await _server.start()

    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    except Exception as e:
        logger.error(f"Agent 运行错误: {e}", exc_info=True)
        raise
    finally:
        if _server:
            await _server.shutdown()
        logger.info("Agent 已停止")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent 已停止")
    except Exception as e:
        logger.error(f"Agent 启动失败: {e}", exc_info=True)
        sys.exit(1)
