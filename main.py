import os, logging, sys
from logging.handlers import RotatingFileHandler
from app.config.config_manager import config
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.routes import register_routes
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

# 配置 CORS
allowed_origins = config.get('security.allowed_origins', ['*'])
CORS(flask_app, origins=allowed_origins)

# 配置 Rate Limiting
limiter = None
if config.get('security.rate_limit_enabled', True):
    limiter = Limiter(
        get_remote_address,
        app=flask_app,
        default_limits=[config.get('security.rate_limit_default', '200 per day, 50 per hour')],
        storage_uri="memory://",
        strategy="fixed-window"
    )
    logging.info(f"Rate limiting enabled: {config.get('security.rate_limit_default')}")

# 配置应用
flask_app.config['SERVER_URL'] = config.SERVER_URL
flask_app.config['MAX_CONTENT_LENGTH'] = config.get('security.max_upload_size_mb', 16) * 1024 * 1024

# 全局错误处理器
@flask_app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad Request', 'message': str(e)}), 400

@flask_app.errorhandler(401)
def unauthorized(e):
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@flask_app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Forbidden', 'message': str(e)}), 403

@flask_app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404

@flask_app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'error': 'Payload Too Large', 'message': f'Maximum upload size is {config.get("security.max_upload_size_mb", 16)}MB'}), 413

@flask_app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Too Many Requests', 'message': str(e.description)}), 429

@flask_app.errorhandler(500)
def internal_error(e):
    logging.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500

# 注册路由
register_routes(flask_app, limiter)

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

