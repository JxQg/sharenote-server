from flask import abort, request, send_file, jsonify
from app.utils.auth import check_auth, require_auth
from app.services.note_service import cook_note, gen_short_code, slugify, organize_notes_by_folder
from app.services.cache_service import cache, cache_service
from app.services.search_service import search_service
from app.services.monitor_service import monitor_service
import logging
import os
import re
import glob
import json
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from app.config.config_manager import config

def validate_file_access(filepath):
    """验证文件访问的安全性"""
    try:
        # 确保路径是在static目录下
        static_path = os.path.abspath('static')
        file_path = os.path.abspath(filepath)
        common_prefix = os.path.commonpath([static_path, file_path])
        return common_prefix == static_path
    except ValueError:
        return False

def register_routes(app):
    @app.route('/', methods=['GET'])
    @cache(ttl=300)
    def index():
        try:
            if not validate_file_access('static/index.html'):
                abort(404)
            return send_file('static/index.html')
        except FileNotFoundError:
            return 'The sharenote-py server is running. To customize this page, upload a note titled <b>Share Note Index</b>.'
        except Exception as e:
            logging.error(f"Error serving index: {e}")
            abort(500)

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        file_path = f'static/{filename}'
        if not validate_file_access(file_path):
            abort(403)
        try:
            return send_file(file_path)
        except FileNotFoundError:
            abort(404)
        except Exception as e:
            logging.error(f"Error serving static file {filename}: {e}")
            abort(500)

    @app.route('/v1/account/get-key', methods=['GET'])
    def get_key():
        return 'Please set your API key in the Share Note plugin settings to the one set in settings.py'

    @app.route('/<nid>', methods=['GET'])
    @cache(ttl=300)  # 缓存笔记内容5分钟
    def get_note(nid):
        if re.search('[^a-z0-9_-]', nid):
            abort(404)

        note = 'static/' + nid + '.html'

        if os.path.isfile(note):
            return send_file(note)
        else:
            abort(404)

    @app.route('/v1/file/check-files', methods=['POST'])
    @require_auth
    def check_files():
        data = request.get_json()
        files = data['files']
        result = []

        for f in files:
            name = f['hash'] + '.' + f['filetype']
            if os.path.isfile('static/' + name):
                f['url'] = app.config['SERVER_URL'] + '/static/' + name
            else:
                f['url'] = False

            result.append(f)
            logging.debug('File checked: %s', f)

        if os.path.isfile('static/theme.css'):
            css = dict(url=app.config['SERVER_URL'] + '/static/theme.css')
        else:
            css = False

        return dict(success=True, files=result, css=css)

    @app.route('/v1/file/create-note', methods=['POST'])
    @require_auth
    def create_note():
        try:
            if not request.is_json:
                abort(400, description="Content-Type must be application/json")
                
            data = request.get_json()
            if not data or 'template' not in data:
                abort(400, description="Invalid request body")
                
            template = data.get('template', {})
            if not isinstance(template, dict) or 'title' not in template:
                abort(400, description="Invalid template format")

            logging.debug('Note data: %s', json.dumps(data, indent=4))

            if template.get('encrypted', False):
                logging.error('Encrypted notes are not implemented yet')
                abort(400, description="Encrypted notes are not supported")

            title = template['title']
            filename = ''

            if 'filename' in data:
                short_code = data['filename']
                search_glob = 'static/*-{}.html'.format(short_code)
                search_result = glob.glob(search_glob)
                if len(search_result) == 1:
                    filename = search_result[0]
                    if filename.startswith('static/'):
                        filename = filename[7:]
                    if filename.endswith('.html'):
                        filename = filename[:-5]
                    logging.info('Using existing filename: %s', filename)

            if not filename:
                short_code = gen_short_code(title)
                slug = slugify(title)
                filename = slug + '-' + short_code
                logging.info('Generating new filename: %s', filename)

            if re.search('[^a-z0-9_-]', filename):
                logging.error('Invalid note name')
                abort(400, description="Invalid note name")

            html = cook_note(data)

            if title.lower() in ['首页', 'share note index']:
                filename = 'index'

            file_path = os.path.join('static', filename + '.html')
            if not validate_file_access(file_path):
                abort(403)

            # 确保目标目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)

            cache_service.delete(f"get_note:{filename}")
            cache_service.delete("get_doc_tree")

            return jsonify({
                'success': True,
                'url': app.config['SERVER_URL'] + '/' + filename
            })

        except Exception as e:
            logging.error(f"Error creating note: {e}")
            abort(500, description="Internal server error")

    @app.route('/v1/file/delete', methods=['POST'])
    @require_auth
    def delete_note():
        try:
            if not request.is_json:
                abort(400, description="Content-Type must be application/json")
                
            data = request.get_json()
            if not data or 'filename' not in data:
                abort(400, description="Missing filename parameter")

            filename = data['filename']
            if not isinstance(filename, str) or not filename:
                abort(400, description="Invalid filename")

            if filename == 'index':
                search_glob = 'static/index.html'
            else:
                search_glob = 'static/*-{}.html'.format(filename)

            search_result = glob.glob(search_glob)
            if len(search_result) != 1:
                abort(404)

            note_path = search_result[0]
            if not validate_file_access(note_path):
                abort(403)

            os.remove(note_path)
            cache_service.delete(f"get_note:{filename}")
            cache_service.delete("get_doc_tree")

            return jsonify({'success': True})

        except Exception as e:
            logging.error(f"Error deleting note: {e}")
            abort(500, description="Internal server error")

    @app.route('/api/doc-tree', methods=['GET'])
    @cache(ttl=300)  # 缓存文档树5分钟
    def get_doc_tree():
        """获取文档树结构"""
        notes_path = 'static'
        notes = []
        
        # 获取所有HTML文件
        html_files = glob.glob(f'{notes_path}/**/*.html', recursive=True)
        
        for file_path in html_files:
            rel_path = os.path.relpath(file_path, notes_path)
            name, _ = os.path.splitext(rel_path)
            
            # 读取文件标题
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                title_match = re.search(r'<title>(.*?)</title>', content)
                title = title_match.group(1) if title_match else name
            
            # 构建节点
            node = {
                'title': title,
                'url': f'/{name}',
                'isFolder': False
            }
            
            # 如果是index.html，放在最前面
            if name == 'index':
                notes.insert(0, node)
            else:
                notes.append(node)
        
        # 组织成树结构
        tree = organize_notes_by_folder(notes)
        return jsonify(tree)

    @app.route('/api/search', methods=['GET'])
    def search_notes():
        """搜索笔记内容"""
        query = request.args.get('q', '')
        if not query or len(query.strip()) < 2:
            return jsonify([])
            
        results = search_service.search_notes(query.strip())
        return jsonify(results)

    @app.route('/api/system/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time()
        })

    @app.route('/api/system/stats', methods=['GET'])
    @require_auth
    def system_stats():
        """获取系统状态"""
        return jsonify(monitor_service.get_system_stats())

    @app.route('/api/system/storage', methods=['GET'])
    @require_auth
    def storage_stats():
        """获取存储统计信息"""
        return jsonify(monitor_service.get_storage_stats())