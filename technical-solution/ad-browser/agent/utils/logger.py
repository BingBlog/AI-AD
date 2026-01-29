"""
日志系统

配置日志系统，支持不同日志级别，提供文件和控制台输出。
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "agent",
    log_file: Optional[Path] = None,
    log_level: Optional[str] = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        log_level: 日志级别（可选，默认从配置读取）
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 设置日志级别
    if log_level is None:
        # 延迟导入配置，避免循环依赖
        try:
            from agent.config import settings
            level = settings.log_level
        except Exception:
            level = "INFO"  # 默认级别
    else:
        level = log_level
    logger.setLevel(getattr(logging, level))
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上级别
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        log_path = Path(log_file)
    else:
        # 延迟导入配置
        try:
            from agent.config import settings
            if settings.log_file:
                log_path = Path(settings.log_file)
            else:
                log_path = None
        except Exception:
            log_path = None
    
    if log_path:
        
        # 确保日志目录存在
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "agent") -> logging.Logger:
    """
    获取日志记录器（如果已存在则返回，否则创建）
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # 如果还没有配置，使用默认配置
        return setup_logger(name)
    return logger
