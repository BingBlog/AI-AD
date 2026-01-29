"""
配置管理模块

从 .env 文件加载配置，定义所有配置项，提供配置验证。
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # DeepSeek API 配置
    deepseek_api_key: str = Field(
        ...,
        description="DeepSeek API Key",
        env="DEEPSEEK_API_KEY"
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="DeepSeek API Base URL",
        env="DEEPSEEK_API_BASE_URL"
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        description="DeepSeek Model Name",
        env="DEEPSEEK_MODEL"
    )
    
    # 性能限制（MVP 硬约束 - 第 14 节）
    max_items: int = Field(
        default=10,
        ge=1,
        le=10,
        description="最大详情数",
        env="MAX_ITEMS"
    )
    max_pages: int = Field(
        default=3,
        ge=1,
        le=3,
        description="最大页数",
        env="MAX_PAGES"
    )
    max_steps: int = Field(
        default=100,
        ge=1,
        le=100,
        description="最大操作步数",
        env="MAX_STEPS"
    )
    timeout_per_item: int = Field(
        default=60,
        ge=1,
        description="单条超时（秒）",
        env="TIMEOUT_PER_ITEM"
    )
    
    # WebSocket 配置
    ws_host: str = Field(
        default="localhost",
        description="WebSocket 服务器主机",
        env="WS_HOST"
    )
    ws_port: int = Field(
        default=8765,
        ge=1024,
        le=65535,
        description="WebSocket 服务器端口",
        env="WS_PORT"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别",
        env="LOG_LEVEL"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="日志文件路径（可选）",
        env="LOG_FILE"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    def __repr__(self) -> str:
        """配置的字符串表示（隐藏敏感信息）"""
        return (
            f"Settings("
            f"deepseek_base_url={self.deepseek_base_url}, "
            f"deepseek_model={self.deepseek_model}, "
            f"max_items={self.max_items}, "
            f"max_pages={self.max_pages}, "
            f"max_steps={self.max_steps}, "
            f"timeout_per_item={self.timeout_per_item}, "
            f"ws_host={self.ws_host}, "
            f"ws_port={self.ws_port}"
            f")"
        )


# 加载环境变量
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)
else:
    # 如果 .env 文件不存在，尝试从环境变量加载
    load_dotenv(override=False)

# 全局配置实例
# 注意：如果没有设置 DEEPSEEK_API_KEY，会在首次使用时抛出异常
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    获取配置实例（延迟加载）
    
    Returns:
        配置实例
        
    Raises:
        RuntimeError: 如果配置加载失败
    """
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            raise RuntimeError(
                f"配置加载失败: {e}\n"
                f"请确保已创建 .env 文件并设置 DEEPSEEK_API_KEY，"
                f"或设置环境变量 DEEPSEEK_API_KEY"
            ) from e
    return _settings


# 为了向后兼容，提供 settings 属性
# 但只有在实际使用时才会加载配置
class _SettingsProxy:
    """配置代理类，延迟加载配置"""
    
    def __getattr__(self, name: str):
        return getattr(get_settings(), name)
    
    def __repr__(self) -> str:
        if _settings is None:
            return "Settings(未初始化，请设置 DEEPSEEK_API_KEY)"
        return repr(_settings)


settings = _SettingsProxy()
