import unittest
import time
from app.services.cache_service import CacheService, cache

class TestCacheService(unittest.TestCase):
    def setUp(self):
        """每个测试前的设置"""
        self.cache_service = CacheService()
        self.cache_service.clear()
        
    def test_set_get(self):
        """测试基本的设置和获取功能"""
        self.cache_service.set('test_key', 'test_value')
        value = self.cache_service.get('test_key')
        self.assertEqual(value, 'test_value')
        
    def test_expiration(self):
        """测试缓存过期功能"""
        self.cache_service.set('test_key', 'test_value', ttl=1)
        value1 = self.cache_service.get('test_key')
        self.assertEqual(value1, 'test_value')
        
        # 等待缓存过期
        time.sleep(1.1)
        value2 = self.cache_service.get('test_key')
        self.assertIsNone(value2)
        
    def test_delete(self):
        """测试删除功能"""
        self.cache_service.set('test_key', 'test_value')
        self.cache_service.delete('test_key')
        value = self.cache_service.get('test_key')
        self.assertIsNone(value)
        
    def test_clear(self):
        """测试清空功能"""
        self.cache_service.set('key1', 'value1')
        self.cache_service.set('key2', 'value2')
        self.cache_service.clear()
        
        self.assertIsNone(self.cache_service.get('key1'))
        self.assertIsNone(self.cache_service.get('key2'))
        
    def test_cleanup(self):
        """测试自动清理过期项"""
        self.cache_service.set('key1', 'value1', ttl=1)
        self.cache_service.set('key2', 'value2', ttl=10)
        
        # 等待部分缓存过期
        time.sleep(1.1)
        self.cache_service.cleanup()
        
        self.assertIsNone(self.cache_service.get('key1'))
        self.assertEqual(self.cache_service.get('key2'), 'value2')
        
    def test_cache_decorator(self):
        """测试缓存装饰器"""
        call_count = 0
        
        @cache(ttl=2)
        def test_func():
            nonlocal call_count
            call_count += 1
            return 'test_result'
        
        # 第一次调用
        result1 = test_func()
        self.assertEqual(result1, 'test_result')
        self.assertEqual(call_count, 1)
        
        # 第二次调用（应该使用缓存）
        result2 = test_func()
        self.assertEqual(result2, 'test_result')
        self.assertEqual(call_count, 1)  # 计数器不应该增加
        
        # 等待缓存过期
        time.sleep(2.1)
        
        # 第三次调用（缓存已过期）
        result3 = test_func()
        self.assertEqual(result3, 'test_result')
        self.assertEqual(call_count, 2)  # 计数器应该增加

if __name__ == '__main__':
    unittest.main()