import functools
import time
from typing import Any, Dict, Optional
import logging

class CacheService:
    _instance = None
    _cache: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
            cls._instance._cache = {}
        return cls._instance
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            item = self._cache[key]
            if item['expires_at'] > time.time():
                return item['value']
            else:
                del self._cache[key]
        return None
        
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值"""
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
        
    def delete(self, key: str) -> None:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
            
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        
    def cleanup(self) -> None:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self._cache.items()
            if item['expires_at'] <= current_time
        ]
        for key in expired_keys:
            del self._cache[key]

def cache(ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # 获取缓存服务实例
            cache_service = CacheService()
            
            # 尝试从缓存获取
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                logging.debug(f"Cache hit for {cache_key}")
                return cached_value
                
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache_service.set(cache_key, result, ttl)
            logging.debug(f"Cache miss for {cache_key}, cached new value")
            
            return result
        return wrapper
    return decorator

# 创建单例实例
cache_service = CacheService()