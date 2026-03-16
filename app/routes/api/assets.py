import os
import logging
import re
import mimetypes
from flask import Blueprint, request, abort, jsonify
from app.utils.auth import require_auth
from app.config.config_manager import config

assets_bp = Blueprint('assets', __name__)

def validate_file_access(file_path):
    """验证文件访问的安全性"""
    # 先检查路径遍历，再进行normpath
    if '..' in file_path:
        logging.warning(f"检测到路径遍历尝试: {file_path}")
        return False

    file_path = os.path.normpath(file_path)

    if not os.path.exists(file_path):
        logging.debug(f"文件不存在: {file_path}")
        return False

    if os.path.isdir(file_path):
        return False

    _, ext = os.path.splitext(file_path)
    ext = ext.lstrip('.').lower()

    allowed_ext = config.get('files.allowed_filetypes', [])
    if ext == 'html':
        return True

    if ext not in allowed_ext:
        logging.warning(f"不允许的文件类型: {ext}")
        return False

    return True

def init_routes(limiter=None):
    """初始化资源文件相关路由"""

    @assets_bp.route('/v1/file/upload', methods=['POST'])
    @require_auth
    def upload():
        """处理文件上传"""
        if limiter:
            limiter.limit(config.get('security.rate_limit_upload', '20 per hour'))(lambda: None)()
        try:
            required_headers = ['x-sharenote-hash', 'x-sharenote-filetype']
            for header in required_headers:
                if not request.headers.get(header):
                    logging.error(f"Missing required header: {header}")
                    abort(400, description=f"Missing required header: {header}")

            name = request.headers['x-sharenote-hash']
            filetype = request.headers['x-sharenote-filetype']
            note_id = request.headers.get('x-sharenote-note-id') or request.args.get('note_id')

            if re.search(r'[^a-f0-9]', name):
                logging.error(f'Invalid hash format for file name: {name}')
                abort(400, description="Invalid file hash")

            allowed_filetypes = config.get('files.allowed_filetypes', [])
            if filetype.lower() not in allowed_filetypes:
                logging.error(f'Invalid file type: {filetype}')
                abort(415, description=f"File type not allowed. Allowed types: {', '.join(allowed_filetypes)}")

            if filetype == 'css':
                name = 'theme'
                file_path = os.path.join('static', f'{name}.{filetype}')
                url = f'{config.SERVER_URL}/static/{name}.{filetype}'
            else:
                if note_id:
                    assets_path = os.path.join('static', 'notes', note_id, 'assets')
                    os.makedirs(assets_path, exist_ok=True)
                    file_path = os.path.join(assets_path, f'{name}.{filetype}')
                    url = f'{config.SERVER_URL}/static/notes/{note_id}/assets/{name}.{filetype}'
                else:
                    os.makedirs('static', exist_ok=True)
                    file_path = os.path.join('static', f'{name}.{filetype}')
                    url = f'{config.SERVER_URL}/static/{name}.{filetype}'

            with open(file_path, 'wb') as f:
                f.write(request.data)

            logging.info(f'File uploaded: {file_path}')
            return jsonify({'success': True, 'url': url})
        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            abort(500)

    return assets_bp
