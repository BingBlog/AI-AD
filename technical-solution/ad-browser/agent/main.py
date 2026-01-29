"""
Agent 启动入口

TODO: 实现 Agent 主入口（阶段四任务 4.3）
"""
import asyncio
import signal
from agent.utils.logger import setup_logger
from agent.config import settings

logger = setup_logger("agent")


async def main():
    """Agent 主入口"""
    logger.info("Agent 启动中...")
    logger.info(f"配置加载成功: {settings}")
    # TODO: 实现 WebSocket 服务器集成（阶段四）
    # TODO: 实现优雅关闭（阶段四）
    logger.info("Agent 已启动")


if __name__ == "__main__":
    asyncio.run(main())
