import toml
import os
from typing import Dict, Any, Optional

class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}
    _env_prefix = "SHARENOTE_"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """加载配置文件并合并环境变量"""
        # 获取项目根目录的绝对路径
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # 使用绝对路径加载配置文件
        config_path = os.path.join(root_dir, 'config', 'settings.toml')
        try:
            self._config = toml.load(config_path)
        except Exception as e:
            raise Exception(f"Error loading config file: {e}")

        # 从环境变量加载配置覆盖
        self._load_from_env()

        # 验证必要的配置
        self._validate_config()

    def _load_from_env(self):
        """从环境变量加载配置"""
        for key in os.environ:
            if key.startswith(self._env_prefix):
                config_key = key[len(self._env_prefix):].lower().replace('_', '.')
                value = os.environ[key]
                
                # 尝试转换布尔值和数字
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                
                self._set_nested(config_key, value)

    def _set_nested(self, key: str, value: Any):
        """设置嵌套配置值"""
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value

    def _validate_config(self):
        """验证必要的配置项"""
        required_configs = [
            ('server.server_url', '服务器URL'),
            ('security.secret_api_key', 'API密钥'),
        ]

        for config_key, description in required_configs:
            if not self.get(config_key):
                raise ValueError(f"Missing required configuration: {description} ({config_key})")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的键路径"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._set_nested(key, value)

    @property
    def server(self) -> Dict[str, Any]:
        return self._config.get('server', {})

    @property
    def security(self) -> Dict[str, Any]:
        return self._config.get('security', {})

    @property
    def files(self) -> Dict[str, Any]:
        return self._config.get('files', {})

    @property
    def templates(self) -> Dict[str, Any]:
        return self._config.get('templates', {})

config = ConfigManager()