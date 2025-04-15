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

def register_routes(app):
    @app.route('/', methods=['GET'])
    @cache(ttl=300)  # 缓存首页5分钟
    def index():
        try:
            return send_file('static/index.html')
        except FileNotFoundError:
            return 'The sharenote-py server is running. To customize this page, upload a note titled <b>Share Note Index</b>.'

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_file(f'static/{filename}')

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
        data = request.get_json()
        logging.debug('Note data: %s', json.dumps(data, indent=4))

        if data['template'].get('encrypted', False):
            logging.error('###################################################')
            logging.error('## Encrypted notes are not implemented yet.      ##')
            logging.error('## Please disable in Share Note plugin settings. ##')
            logging.error('###################################################')
            abort(400)

        title = data['template']['title']
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
            logging.error('Invalid note name, aborting')
            abort(400)

        html = cook_note(data)

        # 支持中文"首页"或英文"Share Note Index"作为首页
        if title.lower() in ['首页', 'share note index']:
            filename = 'index'

        with open('static/' + filename + '.html', 'w') as f:
            f.write(html)

        # 清除相关缓存
        cache_service.delete(f"get_note:{filename}")
        cache_service.delete("get_doc_tree")

        return dict(success=True, url=app.config['SERVER_URL'] + '/' + filename)

    @app.route('/v1/file/delete', methods=['POST'])
    @require_auth
    def delete_note():
        data = request.get_json()
        filename = data['filename']

        if filename == 'index':
            search_glob = 'static/index.html'
        else:
            search_glob = 'static/*-{}.html'.format(data['filename'])

        search_result = glob.glob(search_glob)

        if len(search_result) != 1:
            abort(404)

        note = search_result[0]
        os.remove(note)

        # 清除相关缓存
        cache_service.delete(f"get_note:{filename}")
        cache_service.delete("get_doc_tree")

        return dict(success=True)

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