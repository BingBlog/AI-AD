"""
应用配置管理
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """应用配置"""
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_WORKERS: int = 1
    API_TITLE: str = "广告案例库 API"
    API_VERSION: str = "v1"
    API_DESCRIPTION: str = "广告案例库检索服务 API"
    
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ad_case_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # 向量模型配置
    VECTOR_MODEL_PATH: Optional[str] = None
    VECTOR_DIMENSION: int = 1024
    VECTOR_OFFLINE_MODE: bool = True  # 是否使用离线模式（避免请求 HuggingFace）
    
    # 缓存配置（可选）
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = False
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    # 代理配置（可选）
    HTTP_PROXY: Optional[str] = None
    HTTPS_PROXY: Optional[str] = None
    
    model_config = ConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive = True,
        # 允许额外的环境变量（忽略未定义的变量）
        extra = "ignore"
    )


# 全局配置实例
settings = Settings()
