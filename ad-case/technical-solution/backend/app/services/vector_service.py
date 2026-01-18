"""
向量服务层
"""
import logging
import hashlib
from typing import List, Optional
import numpy as np
from FlagEmbedding import FlagModel
from app.config import settings

logger = logging.getLogger(__name__)

# 全局模型实例（单例模式）
_vector_model: Optional[FlagModel] = None


def get_vector_model() -> FlagModel:
    """
    获取向量模型实例（单例）
    
    Returns:
        向量模型实例
    """
    global _vector_model
    if _vector_model is None:
        model_path = settings.VECTOR_MODEL_PATH or 'BAAI/bge-large-zh-v1.5'
        logger.info(f"正在加载向量模型: {model_path}")
        try:
            _vector_model = FlagModel(
                model_path,
                query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
            )
            logger.info("向量模型加载成功")
        except Exception as e:
            logger.error(f"向量模型加载失败: {e}")
            raise RuntimeError(f"向量服务不可用: {e}")
    return _vector_model


class VectorService:
    """向量服务类"""
    
    def __init__(self):
        """初始化向量服务"""
        self.model = get_vector_model()
        self.cache: dict = {}
        self.cache_size = getattr(settings, 'VECTOR_CACHE_SIZE', 1000)
        self.cache_enabled = getattr(settings, 'VECTOR_CACHE_ENABLED', True)
    
    def _get_cache_key(self, query: str) -> str:
        """
        生成缓存键
        
        Args:
            query: 查询文本
            
        Returns:
            缓存键
        """
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    async def encode_query(self, query: str) -> List[float]:
        """
        将查询文本转换为向量
        
        Args:
            query: 查询文本
            
        Returns:
            向量列表（1024维）
        """
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")
        
        query = query.strip()
        
        # 检查缓存
        if self.cache_enabled:
            cache_key = self._get_cache_key(query)
            if cache_key in self.cache:
                logger.debug(f"向量缓存命中: {query[:50]}...")
                return self.cache[cache_key]
        
        try:
            # 使用模型编码
            logger.debug(f"正在编码查询文本: {query[:50]}...")
            vector = self.model.encode(query)
            
            # 归一化向量
            vector_norm = vector / np.linalg.norm(vector)
            vector_list = vector_norm.tolist()
            
            # 存入缓存
            if self.cache_enabled:
                cache_key = self._get_cache_key(query)
                # LRU 缓存管理
                if len(self.cache) >= self.cache_size:
                    # 删除最旧的缓存项（简单实现：删除第一个）
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                
                self.cache[cache_key] = vector_list
                logger.debug(f"向量已缓存: {query[:50]}...")
            
            return vector_list
            
        except Exception as e:
            logger.error(f"向量编码失败 [query={query[:50]}...]: {e}")
            raise ValueError(f"查询文本无法编码为向量: {e}")
    
    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量编码文本为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        vectors = []
        for text in texts:
            vector = await self.encode_query(text)
            vectors.append(vector)
        return vectors
