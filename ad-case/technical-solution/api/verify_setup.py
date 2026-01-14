#!/usr/bin/env python3
"""
环境验证脚本
用于验证开发环境是否就绪
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🔍 开始验证开发环境...")
print("=" * 60)

# 1. 检查 Python 版本
print("\n1️⃣ 检查 Python 版本...")
print(f"   Python 版本: {sys.version.split()[0]} ✅")

# 2. 检查依赖安装
print("\n2️⃣ 检查依赖安装...")
dependencies = {
    "fastapi": "FastAPI 框架",
    "uvicorn": "ASGI 服务器",
    "pydantic": "数据验证",
    "pydantic_settings": "配置管理",
    "asyncpg": "PostgreSQL 异步驱动",
    "python-dotenv": "环境变量管理",
}

missing_deps = []
for dep, desc in dependencies.items():
    try:
        # python-dotenv 的模块名是 dotenv
        module_name = "dotenv" if dep == "python-dotenv" else dep.replace("-", "_")
        __import__(module_name)
        print(f"   ✅ {dep:20} - {desc}")
    except ImportError:
        print(f"   ❌ {dep:20} - {desc} (未安装)")
        missing_deps.append(dep)

if missing_deps:
    print(f"\n   ⚠️  缺少依赖: {', '.join(missing_deps)}")
    print(f"   请运行: pip install {' '.join(missing_deps)}")
    sys.exit(1)

# 3. 检查代码导入
print("\n3️⃣ 检查代码导入...")
try:
    from app.config import settings
    print("   ✅ app.config")
    
    from app.database import db
    print("   ✅ app.database")
    
    from app.main import app
    print("   ✅ app.main")
    
    from app.schemas.response import BaseResponse
    print("   ✅ app.schemas.response")
    
    from app.routers.health import router
    print("   ✅ app.routers.health")
    
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    sys.exit(1)

# 4. 检查配置加载
print("\n4️⃣ 检查配置加载...")
try:
    print(f"   API Host: {settings.API_HOST}")
    print(f"   API Port: {settings.API_PORT}")
    print(f"   DB Host: {settings.DB_HOST}")
    print(f"   DB Name: {settings.DB_NAME}")
    print(f"   DB User: {settings.DB_USER}")
    print("   ✅ 配置加载成功")
except Exception as e:
    print(f"   ❌ 配置加载失败: {e}")
    sys.exit(1)

# 5. 检查环境文件
print("\n5️⃣ 检查环境文件...")
env_file = Path(".env")
env_example = Path("env.example")
if env_file.exists():
    print("   ✅ .env 文件存在")
else:
    print("   ⚠️  .env 文件不存在")
    if env_example.exists():
        print("   💡 提示: 可以运行 'cp env.example .env' 创建配置文件")

# 6. 测试数据库连接（可选）
print("\n6️⃣ 测试数据库连接...")
async def test_db():
    try:
        await db.connect()
        result = await db.fetchval("SELECT 1")
        if result == 1:
            print("   ✅ 数据库连接成功")
        await db.disconnect()
        return True
    except Exception as e:
        print(f"   ⚠️  数据库连接失败: {e}")
        print("   💡 提示: 请确保:")
        print("      - PostgreSQL 服务正在运行")
        print("      - 数据库 'ad_case_db' 已创建")
        print("      - .env 文件中的数据库配置正确")
        return False

db_ok = asyncio.run(test_db())

# 总结
print("\n" + "=" * 60)
print("📊 验证总结")
print("=" * 60)
print(f"✅ Python 环境: 正常")
print(f"✅ 依赖安装: 完成")
print(f"✅ 代码导入: 正常")
print(f"✅ 配置加载: 正常")
if env_file.exists():
    print(f"✅ 环境文件: 已配置")
else:
    print(f"⚠️  环境文件: 未配置（建议创建 .env 文件）")
if db_ok:
    print(f"✅ 数据库连接: 正常")
else:
    print(f"⚠️  数据库连接: 失败（不影响代码验证）")

print("\n" + "=" * 60)
if db_ok and env_file.exists():
    print("🎉 开发环境完全就绪！可以启动服务了。")
    print("\n启动命令:")
    print("  python run.py")
    print("  或")
    print("  uvicorn app.main:app --reload")
else:
    print("⚠️  开发环境基本就绪，但需要:")
    if not env_file.exists():
        print("  1. 创建 .env 文件: cp env.example .env")
    if not db_ok:
        print("  2. 配置数据库连接并确保服务运行")
print("=" * 60)
