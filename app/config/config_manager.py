import toml
import os
from typing import Dict, Any, Optional

class ConfigManager:
    _instance = None
    _config = {}
    _env_prefix = "SHARENOTE_"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """加载配置文件"""
        try:
            self._config = toml.load('config/settings.toml')
        except Exception as e:
            raise Exception(f"Error loading config file: {e}")

        # 加载环境变量配置
        self._load_from_env()
        
        # 兼容原版settings.py的配置项
        server_url = self.get('server.server_url')
        if not server_url:
            raise ValueError("Missing required configuration: server.server_url")
            
        # 简化访问常用配置
        self._config['SERVER_URL'] = server_url
        self._config['SECRET_API_KEY'] = self.get('security.secret_api_key')
        self._config['ALLOWED_FILETYPES'] = self.get('files.allowed_filetypes', [])
        self._config['PORT'] = self.get('server.port', 8086)

    def _load_from_env(self):
        """从环境变量加载配置,保持精简"""
        for key in os.environ:
            if key.startswith(self._env_prefix):
                config_key = key[len(self._env_prefix):].lower()
                value = os.environ[key]
                
                # 转换布尔值和数字
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                        
                self._config[config_key] = value

    def get(self, key: str, default=None):
        """获取配置值,支持点号分隔的键路径"""
        value = self._config
        for k in key.split('.'):
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def __getattr__(self, name):
        """兼容原版settings.py的属性访问方式"""
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

config = ConfigManager()