import os, logging, sys
from logging.handlers import RotatingFileHandler
from app.config.config_manager import config
from flask import Flask
from flask_cors import CORS
from app.routes.note_routes import register_routes
from app.services.file_watcher import file_watcher

# 配置日志,简化配置减少内存
DEBUG = config.get('server.debug', False)
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# 精简日志格式
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(module)s - %(message)s')

# 日志文件处理器
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3
)
file_handler.setFormatter(formatter)

# 控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# 配置根日志器
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# 验证必要配置
if not config.SERVER_URL:
    logging.error('server.server_url not set in settings.toml')
    sys.exit(1)

# 初始化应用
flask_app = Flask(__name__)
CORS(flask_app)

# 配置应用
flask_app.config['SERVER_URL'] = config.SERVER_URL
flask_app.config['MAX_CONTENT_LENGTH'] = config.get('security.max_upload_size_mb', 16) * 1024 * 1024

# 注册路由
register_routes(flask_app)

# 启动文件监控(可选)
if not config.get('server.disable_file_watch', False):
    file_watcher.start('static')

if __name__ == '__main__':
    try:
        flask_app.run(
            host=config.get('server.host', '0.0.0.0'),
            port=config.PORT
        )
    finally:
        file_watcher.stop()

