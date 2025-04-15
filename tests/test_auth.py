import unittest
from app.utils.auth import get_secure_hash, check_auth
from unittest.mock import MagicMock, patch

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.api_key = "test-secret-key"
        self.nonce = "test-nonce"
        
    def test_get_secure_hash(self):
        """测试安全哈希生成功能"""
        hash1 = get_secure_hash("test", self.api_key)
        hash2 = get_secure_hash("test", self.api_key)
        
        # 相同输入应该生成相同的哈希
        self.assertEqual(hash1, hash2)
        
        # 不同输入应该生成不同的哈希
        hash3 = get_secure_hash("different", self.api_key)
        self.assertNotEqual(hash1, hash3)
        
    @patch('app.utils.auth.config')
    def test_check_auth_valid(self, mock_config):
        """测试有效的认证检查"""
        mock_config.get.return_value = self.api_key
        
        # 生成有效的key
        valid_key = get_secure_hash(self.nonce, self.api_key)
        
        # 创建模拟的请求头
        headers = {
            'x-sharenote-nonce': self.nonce,
            'x-sharenote-key': valid_key
        }
        
        self.assertTrue(check_auth(headers))
        
    @patch('app.utils.auth.config')
    def test_check_auth_invalid(self, mock_config):
        """测试无效的认证检查"""
        mock_config.get.return_value = self.api_key
        
        # 测试缺少nonce
        headers1 = {
            'x-sharenote-key': 'some-key'
        }
        self.assertFalse(check_auth(headers1))
        
        # 测试缺少key
        headers2 = {
            'x-sharenote-nonce': self.nonce
        }
        self.assertFalse(check_auth(headers2))
        
        # 测试无效的key
        headers3 = {
            'x-sharenote-nonce': self.nonce,
            'x-sharenote-key': 'invalid-key'
        }
        self.assertFalse(check_auth(headers3))
        
    @patch('app.utils.auth.config')
    def test_check_auth_missing_config(self, mock_config):
        """测试缺少API密钥配置的情况"""
        mock_config.get.return_value = None
        
        headers = {
            'x-sharenote-nonce': self.nonce,
            'x-sharenote-key': 'some-key'
        }
        
        self.assertFalse(check_auth(headers))

if __name__ == '__main__':
    unittest.main()