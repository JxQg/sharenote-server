import os
import logging
import json
import glob
import re
from flask import Blueprint, request, abort, jsonify
from app.utils.auth import require_auth
from app.services.note_service import cook_note, handle_note_assets, delete_note_assets, organize_notes_by_folder
from app.services.cache_service import cache_service
from app.config.config_manager import config

notes_bp = Blueprint('notes', __name__)

def init_routes(limiter=None):
    """初始化笔记相关路由的限流"""

    @notes_bp.route('/v1/file/create-note', methods=['POST'])
    @require_auth
    def create_note():
        if limiter:
            limiter.limit(config.get('security.rate_limit_upload', '20 per hour'))(lambda: None)()
        try:
            data = request.get_json()
            logging.debug('Note data: %s', json.dumps(data, indent=2))
            template = data.get('template', {})

            if template.get('encrypted', False):
                logging.error('Encrypted notes are not implemented yet')
                abort(400, description="Encrypted notes are not supported")

            # 检查是否是索引页面
            is_index = False
            if template.get('title') == '首页':
                is_index = True
                logging.info("创建/更新首页")

            if is_index:
                filename = 'index'
            else:
                # 先生成filename用于资源处理
                from app.services.note_service import slugify, gen_short_code
                filename = slugify(template['title']) if template['title'] else 'untitled-' + gen_short_code('untitled')

            # 先处理资源文件，替换路径
            handle_note_assets(data, filename)

            # 然后生成HTML（此时content中的路径已经被替换）
            html, _ = cook_note(data)

            os.makedirs('static', exist_ok=True)
            file_path = os.path.normpath(os.path.join('static', f'{filename}.html'))

            if not file_path.startswith('static'):
                logging.error('Invalid file path')
                abort(400)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)

            cache_service.delete(f"get_note:{filename}")
            cache_service.delete("get_doc_tree")
            if is_index:
                cache_service.delete("index")
                logging.info("首页缓存已清除")

            return jsonify({
                'success': True,
                'url': f'{config.SERVER_URL}/{filename}'
            })
        except Exception as e:
            logging.error(f"Error creating note: {e}", exc_info=True)
            abort(500, description="Internal server error")

    @notes_bp.route('/v1/file/delete', methods=['POST'])
    @require_auth
    def delete_note():
        try:
            data = request.get_json()
            filename = data.get('filename')

            if filename == 'index':
                search_glob = 'static/index.html'
                base_filename = 'index'
            else:
                search_glob = f'static/*-{filename}.html'
                base_filename = None

            search_result = glob.glob(search_glob)
            if len(search_result) != 1:
                abort(404)

            note_path = search_result[0]

            if not base_filename:
                base_filename = os.path.splitext(os.path.basename(note_path))[0]

            is_index = (base_filename == 'index')

            os.remove(note_path)
            delete_note_assets(base_filename)

            cache_service.delete(f"get_note:{base_filename}")
            cache_service.delete("get_doc_tree")
            if is_index:
                cache_service.delete("index")
                logging.info("首页已删除，缓存已清除")

            return jsonify({'success': True})
        except Exception as e:
            logging.error(f"Error deleting note: {e}")
            abort(500)

    @notes_bp.route('/v1/file/check-files', methods=['POST'])
    @require_auth
    def check_files():
        """检查文件是否存在并返回正确的URL"""
        try:
            data = request.get_json()
            files = data.get('files', [])
            result = []
            note_id = request.headers.get('x-sharenote-note-id', 'index')

            for f in files:
                name = f'{f["hash"]}.{f["filetype"]}'
                note_asset_path = os.path.join('static', 'notes', note_id, 'assets', name)
                if os.path.isfile(note_asset_path):
                    f['url'] = f'{config.SERVER_URL}/static/notes/{note_id}/assets/{name}'
                else:
                    root_path = os.path.join('static', name)
                    if os.path.isfile(root_path):
                        f['url'] = f'{config.SERVER_URL}/static/{name}'
                    else:
                        f['url'] = None
                result.append(f)

            css = None
            theme_css_path = 'static/theme.css'
            if os.path.isfile(theme_css_path):
                with open(theme_css_path, 'r', encoding='utf-8') as f:
                    css = f.read()

            return jsonify({
                'success': True,
                'files': result,
                'css': css
            })
        except Exception as e:
            logging.error(f"Error checking files: {e}")
            abort(500, description="Internal server error")

    @notes_bp.route('/api/doc-tree', methods=['GET'])
    def get_doc_tree():
        """获取文档树结构"""
        try:
            notes = []
            for file in glob.glob('static/*.html'):
                filename = os.path.splitext(os.path.basename(file))[0]
                title = filename

                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        title_match = re.search(r'<title>(.*?)</title>', content)
                        if title_match:
                            title = title_match.group(1)
                except Exception as e:
                    logging.warning(f"Error reading title from {file}: {e}")

                notes.append({
                    'title': title,
                    'url': f'/{filename}',
                    'isFolder': False
                })

            return jsonify(organize_notes_by_folder(notes))
        except Exception as e:
            logging.error(f"Error getting doc tree: {e}")
            abort(500)

    @notes_bp.route('/api/index/check', methods=['GET'])
    def check_index():
        """检查索引页面是否存在"""
        try:
            exists = os.path.exists('static/index.html')
            return jsonify({
                'exists': exists,
                'url': f'{config.SERVER_URL}/index' if exists else None
            })
        except Exception as e:
            logging.error(f"Error checking index: {e}")
            abort(500)

    @notes_bp.route('/api/index/create', methods=['POST'])
    @require_auth
    def create_index_page():
        """创建或更新索引页面"""
        if limiter:
            limiter.limit(config.get('security.rate_limit_upload', '20 per hour'))(lambda: None)()
        try:
            data = request.get_json()
            if not data or 'content' not in data:
                abort(400, description="Missing content")

            template_data = {
                'template': {
                    'title': '首页',
                    'content': data['content'],
                    'description': data.get('description', '首页')
                },
                'files': data.get('files', [])
            }

            # 先处理资源文件，替换路径
            handle_note_assets(template_data, 'index')

            # 然后生成HTML（此时content中的路径已经被替换）
            html, _ = cook_note({'template': template_data['template']})
            file_path = 'static/index.html'

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)

            cache_service.delete("index")
            cache_service.delete("get_doc_tree")

            return jsonify({
                'success': True,
                'url': f'{config.SERVER_URL}/index'
            })
        except Exception as e:
            logging.error(f"Error creating index page: {e}", exc_info=True)
            abort(500, description="Internal server error")

    return notes_bp

