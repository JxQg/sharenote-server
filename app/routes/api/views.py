import os
import re
import logging
from flask import Blueprint, send_file, abort
from app.services.cache_service import cache
from app.config.config_manager import config

views_bp = Blueprint('views', __name__)

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
    """初始化视图和静态文件路由"""

    @views_bp.route('/', methods=['GET'])
    @cache(ttl=300)
    def index():
        try:
            if os.path.exists('static/index.html') and validate_file_access('static/index.html'):
                return send_file('static/index.html')

            server_name = config.get('server.server_name', 'Share Note')
            return f'''
            <!DOCTYPE html>
            <html lang="zh-CN" data-theme="light">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{server_name}</title>
                <link rel="stylesheet" href="/assets/css/layout.css">
                <link rel="stylesheet" href="/assets/css/theme.css">
                <style>
                    .welcome-container {{
                        max-width: 800px;
                        margin: 100px auto;
                        text-align: center;
                        padding: 2rem;
                        background-color: var(--theme-bg);
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                    }}
                    .welcome-logo {{
                        font-size: 2.5rem;
                        font-weight: 700;
                        color: var(--theme-accent);
                        margin-bottom: 1rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 0.75rem;
                    }}
                    .welcome-description {{
                        font-size: 1.2rem;
                        color: var(--theme-text-light);
                        margin-bottom: 2rem;
                    }}
                    .welcome-help {{
                        background-color: var(--theme-bg-offset);
                        padding: 1.5rem;
                        border-radius: 8px;
                        margin-top: 2rem;
                        text-align: left;
                    }}
                    .welcome-help h3 {{
                        margin-top: 0;
                        color: var(--theme-text);
                    }}
                    .welcome-help p {{
                        color: var(--theme-text-light);
                        line-height: 1.6;
                    }}
                </style>
                <script src="/assets/js/modules/theme.js"></script>
            </head>
            <body>
                <div class="welcome-container">
                    <div class="welcome-logo">
                        <span>📝</span>
                        <span>{server_name}</span>
                    </div>
                    <p class="welcome-description">欢迎使用 Share Note 服务</p>
                    <div class="welcome-help">
                        <h3>使用说明</h3>
                        <p>1. 在 Obsidian 中安装 Share Note 插件</p>
                        <p>2. 配置服务器地址和 API Key</p>
                        <p>3. 使用命令面板中的 "Share Note" 命令分享笔记</p>
                    </div>
                </div>
            </body>
            </html>
            '''
        except Exception as e:
            logging.error(f"Error serving index: {{e}}")
            abort(500)

    @views_bp.route('/assets/<path:filename>')
    def serve_assets(filename):
        """服务assets目录下的静态文件"""
        try:
            file_path = os.path.join('assets', filename)
            if not validate_file_access(file_path):
                abort(403)
            # 设置长期缓存（1年）用于不变的资源文件
            return send_file(file_path, max_age=31536000, conditional=True)
        except FileNotFoundError:
            abort(404)
        except Exception as e:
            logging.error(f"Error serving asset {filename}: {e}")
            abort(500)

    @views_bp.route('/static/<path:filename>')
    def serve_static(filename):
        """服务static目录下的静态文件"""
        try:
            file_path = os.path.join('static', filename)
            if not validate_file_access(file_path):
                abort(403)
            # 设置中等缓存（1天）用于可能更新的文件
            return send_file(file_path, max_age=86400, conditional=True)
        except FileNotFoundError:
            abort(404)
        except Exception as e:
            logging.error(f"Error serving static file {filename}: {e}")
            abort(500)

    @views_bp.route('/notes/<doc_id>/assets/<path:filename>')
    def serve_note_assets(doc_id, filename):
        """服务笔记资源文件"""
        try:
            # 验证 doc_id 格式
            if re.search('[^a-z0-9_-]', doc_id):
                abort(404)

            file_path = os.path.join('static', 'notes', doc_id, 'assets', filename)
            if not validate_file_access(file_path):
                abort(403)
            # 设置长期缓存（1年）用于笔记资源
            return send_file(file_path, max_age=31536000, conditional=True)
        except FileNotFoundError:
            abort(404)
        except Exception as e:
            logging.error(f"Error serving note asset {doc_id}/{filename}: {e}")
            abort(500)

    @views_bp.route('/<nid>', methods=['GET'])
    @cache(ttl=300)
    def get_note(nid):
        """获取笔记页面"""
        if re.search('[^a-z0-9_-]', nid):
            abort(404)

        note = 'static/' + nid + '.html'
        if not validate_file_access(note):
            abort(403)

        try:
            return send_file(note)
        except FileNotFoundError:
            abort(404)
        except Exception as e:
            logging.error(f"Error serving note {nid}: {e}")
            abort(500)

    return views_bp
