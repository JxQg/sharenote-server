import os, logging, sys
from logging.handlers import RotatingFileHandler
from config.config_manager import config
from flask import Flask, jsonify
from flask_cors import CORS
from app.routes.note_routes import register_routes
from app.services.file_watcher import file_watcher

# 配置日志
DEBUG = config.get('server.debug', False)
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 配置日志格式和处理器
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(module)s/%(funcName)s - %(message)s')

# 文件处理器 - 按大小轮转
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
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

if not config.get('server.server_url'):
    logging.error('Setting server.server_url unset in settings.toml')
    sys.exit(1)

HOST = config.get('server.host', '0.0.0.0')
PORT = config.get('server.port', 5000)

flask_app = Flask(__name__)
CORS(flask_app)

# 配置应用
flask_app.config['SERVER_URL'] = config.get('server.server_url')
flask_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制请求大小为 16MB

# 全局错误处理
@flask_app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

@flask_app.errorhandler(500)
def internal_error(error):
    logging.exception('An internal error occurred')
    return jsonify({'error': 'Internal Server Error'}), 500

@flask_app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large'}), 413

# 注册路由
register_routes(flask_app)

# 启动文件监控
if not config.get('server.disable_file_watch', False):
    file_watcher.start('static')

if __name__ == '__main__':
    try:
        flask_app.run(host=HOST, port=PORT)
    finally:
        file_watcher.stop()

