"""
FastAPI 应用入口
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import db
from app.routers import health, cases, crawl_tasks, task_imports


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    await db.connect()
    yield
    # 关闭时执行
    await db.disconnect()


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router)
app.include_router(cases.router)
app.include_router(crawl_tasks.router)
app.include_router(task_imports.router)

# 配置静态文件服务（图片）
image_storage_dir = Path(settings.IMAGE_STORAGE_DIR)
image_storage_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    settings.IMAGE_STATIC_URL_PREFIX,
    StaticFiles(directory=str(image_storage_dir)),
    name="images"
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用广告案例库 API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }
