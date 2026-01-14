#!/usr/bin/env python3
"""
基础功能测试脚本
用于验证 API 框架是否正确搭建
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import db


async def test_config():
    """测试配置加载"""
    print("=" * 50)
    print("测试配置加载...")
    print(f"API Host: {settings.API_HOST}")
    print(f"API Port: {settings.API_PORT}")
    print(f"DB Host: {settings.DB_HOST}")
    print(f"DB Name: {settings.DB_NAME}")
    print("✅ 配置加载成功")
    print("=" * 50)


async def test_database_connection():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    try:
        await db.connect()
        # 测试简单查询
        result = await db.fetchval("SELECT 1")
        if result == 1:
            print("✅ 数据库连接成功")
        else:
            print("❌ 数据库查询异常")
        await db.disconnect()
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("提示: 请确保 PostgreSQL 服务正在运行，并且数据库配置正确")
    print("=" * 50)


async def main():
    """主测试函数"""
    print("\n🚀 开始测试基础框架...\n")
    
    await test_config()
    await test_database_connection()
    
    print("\n✨ 基础框架测试完成！")
    print("\n下一步:")
    print("1. 确保数据库服务正在运行")
    print("2. 检查 .env 文件配置是否正确")
    print("3. 运行: python run.py 或 uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
