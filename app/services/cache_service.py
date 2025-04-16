import functools
import time
from typing import Any, Dict, Optional
import logging
from threading import Lock
from flask import Response, make_response, send_file

class CacheService:
    _instance = None
    _cache: Dict[str, Dict[str, Any]] = {}
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CacheService, cls).__new__(cls)
                    cls._instance._cache = {}
        return cls._instance
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item['expires_at'] > time.time():
                    return item['value']
                else:
                    del self._cache[key]
                    logging.debug(f"Cache expired for key: {key}")
            return None
        
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值"""
        with self._lock:
            if isinstance(value, tuple):
                content, status_code, headers = value + (None,) * (3 - len(value))
                self._cache[key] = {
                    'value': (content, status_code, headers),
                    'expires_at': time.time() + ttl
                }
            else:
                self._cache[key] = {
                    'value': value,
                    'expires_at': time.time() + ttl
                }
            
    def delete(self, key: str) -> None:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
        
    def cleanup(self) -> None:
        """清理过期缓存"""
        with self._lock:
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
                # 如果是Response对象，创建新的响应
                if isinstance(cached_value, tuple):
                    content, status_code, headers = cached_value
                    response = make_response(content)
                    if headers:
                        response.headers.update(headers)
                    if status_code:
                        response.status_code = status_code
                    return response
                return cached_value
                
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 针对 send_file 等直接传递模式的响应对象特殊处理
            if isinstance(result, Response) and not hasattr(result, 'direct_passthrough'):
                try:
                    cache_value = (result.get_data(), result.status_code, dict(result.headers))
                    # 存入缓存
                    cache_service.set(cache_key, cache_value, ttl)
                    logging.debug(f"Cache miss for {cache_key}, cached new value")
                except RuntimeError:
                    # 如果是直接传递模式无法缓存，则跳过缓存
                    logging.debug(f"Cannot cache direct passthrough response for {cache_key}")
            elif not isinstance(result, Response):
                # 普通对象可以直接缓存
                cache_service.set(cache_key, result, ttl)
                logging.debug(f"Cache miss for {cache_key}, cached new value")
            else:
                # 其他无法缓存的响应对象，跳过缓存
                logging.debug(f"Skipping cache for uncacheable response: {cache_key}")
            
            return result
        return wrapper
    return decorator

# 创建单例实例
cache_service = CacheService()