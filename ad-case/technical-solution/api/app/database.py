"""
数据库连接管理
"""
import asyncpg
from typing import Optional
from app.config import settings


class Database:
    """数据库连接管理类"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """创建数据库连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                min_size=5,
                max_size=settings.DB_POOL_SIZE,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0,
            )
            print(f"✅ 数据库连接池创建成功: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            print("✅ 数据库连接池已关闭")
    
    async def execute(self, query: str, *args):
        """执行查询（无返回结果）"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """执行查询（返回多行）"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """执行查询（返回单行）"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """执行查询（返回单个值）"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


# 全局数据库实例
db = Database()
