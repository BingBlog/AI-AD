#!/usr/bin/env python3
"""
API 服务启动脚本
支持热重载（hot reload）功能
"""
import os
import sys
from pathlib import Path
import uvicorn
from app.config import settings

if __name__ == "__main__":
    # 获取项目根目录（backend 目录）
    backend_dir = Path(__file__).parent.resolve()
    
    # 确定是否启用 reload
    # 开发环境默认启用，除非明确设置为 False
    enable_reload = settings.API_RELOAD
    
    # 如果启用 reload，设置要监视的目录
    reload_dirs = []
    if enable_reload:
        # 监视 app 目录下的所有 Python 文件
        app_dir = backend_dir / "app"
        if app_dir.exists():
            reload_dirs.append(str(app_dir))
        
        print(f"✅ 热重载已启用，监视目录: {reload_dirs}")
    else:
        print("ℹ️  热重载已禁用（生产模式）")
    
    # 启动配置
    uvicorn_config = {
        "app": "app.main:app",
        "host": settings.API_HOST,
        "port": settings.API_PORT,
        "reload": enable_reload,
        "reload_dirs": reload_dirs if enable_reload else None,
        "log_level": settings.LOG_LEVEL.lower(),
    }
    
    # 如果启用 reload，只能使用 1 个 worker
    if not enable_reload and settings.API_WORKERS > 1:
        uvicorn_config["workers"] = settings.API_WORKERS
    
    print(f"🚀 启动后端服务: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API 文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    
    uvicorn.run(**uvicorn_config)
