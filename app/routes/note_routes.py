import os, logging, re, json, glob, mimetypes, shutil, time
from flask import send_file, request, abort, jsonify, send_from_directory, redirect, url_for, render_template_string
from app.utils.auth import require_auth
from app.services.note_service import cook_note, handle_note_assets, delete_note_assets, organize_notes_by_folder
from app.services.cache_service import cache, cache_service
from app.config.config_manager import config
from app.services import search_service, monitor_service

def validate_file_access(file_path):
    """验证文件访问的安全性
    
    Args:
        file_path: 请求的文件路径
    
    Returns:
        bool: 是否允许访问该文件
    """
    # 规范化路径格式
    file_path = os.path.normpath(file_path)
    
    # 检查路径是否尝试跳出根目录
    if '..' in file_path:
        logging.warning(f"检测到路径遍历尝试: {file_path}")
        return False
        
    # 验证文件是否存在
    if not os.path.exists(file_path):
        return False
        
    # 如果是目录则不允许直接访问
    if os.path.isdir(file_path):
        return False
        
    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)
    ext = ext.lstrip('.').lower()
    
    # 检查扩展名是否在允许的列表中
    allowed_ext = config.get('files.allowed_filetypes', [])
    # HTML文件单独处理
    if ext == 'html':
        return True
    
    if ext not in allowed_ext:
        logging.warning(f"不允许的文件类型: {ext}")
        return False
    
    return True

def register_routes(app):
    @app.route('/', methods=['GET'])
    @cache(ttl=300)
    def index():
        try:
            if os.path.exists('static/index.html') and validate_file_access('static/index.html'):
                return send_file('static/index.html')
                
            # 获取站点名称
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
                    .welcome-container {
                        max-width: 800px;
                        margin: 100px auto;
                        text-align: center;
                        padding: 2rem;
                        background-color: var(--theme-bg);
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                    }
                    .welcome-logo {
                        font-size: 2.5rem;
                        font-weight: 700;
                        color: var(--theme-accent);
                        margin-bottom: 1rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 0.75rem;
                    }
                    .welcome-description {
                        font-size: 1.2rem;
                        color: var(--theme-text-light);
                        margin-bottom: 2rem;
                    }
                    .welcome-help {
                        background-color: var(--theme-bg-offset);
                        padding: 1.5rem;
                        border-radius: 8px;
                        margin-top: 2rem;
                        text-align: left;
                    }
                </style>
            </head>
            <body>
                <div class="welcome-container">
                    <div class="welcome-logo">
                        {server_name}
                    </div>
                    <div class="welcome-description">
                        服务器正在运行。要自定义此页面，请上传一个标题为 <b>首页</b> 的笔记。
                    </div>
                    <div class="welcome-help">
                        <h3>快速上手</h3>
                        <p>1. 在 Obsidian 中安装 Share Note 插件</p>
                        <p>2. 设置服务器地址为 <code>{config.get('server.server_url', '')}</code></p>
                        <p>3. 打开任意笔记，通过命令面板使用"Share Note"命令分享笔记</p>
                    </div>
                </div>
            </body>
            </html>
            '''
        except FileNotFoundError:
            # 获取站点名称
            server_name = config.get('server.server_name', 'Share Note')
            return f'服务器正在运行。要自定义此页面，请上传一个标题为 <b>首页</b> 的笔记。<br><h1>{server_name}</h1>'
        except Exception as e:
            logging.error(f"Error serving index: {e}")
            abort(500)

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """提供assets目录下的静态资源"""
        file_path = f'assets/{filename}'
        if not validate_file_access(file_path):
            abort(403)
        try:
            return send_file(file_path)
        except FileNotFoundError:
            abort(404)
        except Exception as e:
            logging.error(f"Error serving asset file {filename}: {e}")
            abort(500)

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """提供static目录下的所有资源"""
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
        return 'Please set your API key in the Share Note plugin settings to the one set in settings.toml'

    @app.route('/<nid>', methods=['GET'])
    @cache(ttl=300)  # 缓存笔记内容5分钟
    def get_note(nid):
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

    @app.route('/v1/file/check-files', methods=['POST'])
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
                # 首先检查文件是否在笔记专属目录中
                note_asset_path = os.path.join('static', 'notes', note_id, 'assets', name)
                if os.path.isfile(note_asset_path):
                    f['url'] = f'{app.config["SERVER_URL"]}/static/notes/{note_id}/assets/{name}'
                else:
                    # 然后检查是否在根static目录中（兼容旧文件和主题文件）
                    root_path = os.path.join('static', name)
                    if os.path.isfile(root_path):
                        f['url'] = f'{app.config["SERVER_URL"]}/static/{name}'
                    else:
                        # 最后检查其他笔记的目录
                        for root, _, files in os.walk(os.path.join('static', 'notes')):
                            file_path = os.path.join(root, name)
                            if os.path.isfile(file_path):
                                rel_path = os.path.relpath(file_path, 'static')
                                f['url'] = f'{app.config["SERVER_URL"]}/static/{rel_path}'
                                break
                        else:
                            f['url'] = False

                result.append(f)
                logging.debug('File checked: %s', f)

            # 检查主题CSS文件
            if os.path.isfile('static/theme.css'):
                css = dict(url=f'{app.config["SERVER_URL"]}/static/theme.css')
            else:
                css = False

            return jsonify({
                'success': True, 
                'files': result, 
                'css': css
            })
        except Exception as e:
            logging.error(f"Error checking files: {e}")
            abort(500, description="Internal server error")

    @app.route('/v1/file/create-note', methods=['POST'])
    @require_auth
    def create_note():
        try:
            data = request.get_json()
            logging.debug('Note data: %s', json.dumps(data, indent=2))
            template = data.get('template', {})
            
            if template.get('encrypted', False):
                logging.error('Encrypted notes are not implemented yet')
                abort(400, description="Encrypted notes are not supported")
            
            # 检查是否是索引页面 - 根据标题是否为"首页"来判断
            is_index = False
            if template.get('title') == '首页':
                is_index = True
                logging.info("创建/更新首页")
            
            # 如果是索引页面，直接使用index作为文件名
            # 否则让cook_note处理文件名生成和内容转换
            if is_index:
                # 先处理内容转换
                html, _ = cook_note(data)
                filename = 'index'
            else:
                # 让cook_note处理文件名生成和内容转换
                html, filename = cook_note(data)
            
            # 确保静态目录存在
            os.makedirs('static', exist_ok=True)
            
            # 使用os.path.normpath确保正确的路径格式
            file_path = os.path.normpath(os.path.join('static', f'{filename}.html'))
            
            # 检查路径是否在static目录下
            if not file_path.startswith('static'):
                logging.error('Invalid file path')
                abort(400)
            
            # 处理文档中的资源文件
            handle_note_assets(data, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)

            # 清理相关缓存
            cache_service.delete(f"get_note:{filename}")
            cache_service.delete("get_doc_tree")
            if is_index:
                cache_service.delete("index")
                logging.info("首页缓存已清除")

            return jsonify({
                'success': True,
                'url': f'{app.config["SERVER_URL"]}/{filename}'
            })
        except Exception as e:
            logging.error(f"Error creating note: {e}", exc_info=True)
            abort(500, description="Internal server error")
    
    @app.route('/v1/file/delete', methods=['POST'])
    @require_auth
    def delete_note():
        try:
            data = request.get_json()
            filename = data.get('filename')
            
            # 对齐原版处理逻辑
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
            
            # 从完整路径中提取基础文件名（如果还没有）
            if not base_filename:
                base_filename = os.path.splitext(os.path.basename(note_path))[0]

            # 如果是删除索引页面，需要特殊处理
            is_index = (base_filename == 'index')
            
            # 删除HTML文件
            os.remove(note_path)
            
            # 删除相关的资源文件
            note_assets_path = os.path.join('static', 'notes', base_filename)
            if os.path.exists(note_assets_path):
                shutil.rmtree(note_assets_path)

            # 清理缓存
            cache_service.delete(f"get_note:{filename}")
            cache_service.delete("get_doc_tree")
            if is_index:
                cache_service.delete("index")
                logging.info("Index page cache cleared after deletion")

            return jsonify({'success': True})
        except Exception as e:
            logging.error(f"Error deleting note: {e}")
            abort(500)

    @app.route('/v1/file/upload', methods=['POST'])
    @require_auth
    def upload():
        """处理文件上传"""
        try:
            # 检查基本必需的头部信息
            required_headers = ['x-sharenote-hash', 'x-sharenote-filetype']
            for header in required_headers:
                if not request.headers.get(header):
                    logging.error(f"Missing required header: {header}")
                    abort(400, description=f"Missing required header: {header}")

            name = request.headers['x-sharenote-hash']
            filetype = request.headers['x-sharenote-filetype']
            
            # 从请求头或者URL参数中获取note_id，如果都没有则默认为临时文件
            note_id = request.headers.get('x-sharenote-note-id') or request.args.get('note_id')
            
            # 验证文件哈希格式
            if re.search(r'[^a-f0-9]', name):
                logging.error(f'Invalid hash format for file name: {name}')
                abort(400, description="Invalid file hash")

            # 验证文件类型
            allowed_filetypes = config.get('files.allowed_filetypes', [])
            if filetype.lower() not in allowed_filetypes:
                logging.error(f'Invalid file type: {filetype}')
                abort(415, description=f"File type not allowed. Allowed types: {', '.join(allowed_filetypes)}")

            # 处理主题CSS文件
            if filetype == 'css':
                name = 'theme'
                file_path = os.path.join('static', f'{name}.{filetype}')
                url = f'{app.config["SERVER_URL"]}/static/{name}.{filetype}'
            else:
                # 其他资源文件处理
                if note_id:
                    # 如果指定了note_id，存储到对应的笔记目录
                    assets_path = os.path.join('static', 'notes', note_id, 'assets')
                    os.makedirs(assets_path, exist_ok=True)
                    file_path = os.path.join(assets_path, f'{name}.{filetype}')
                    url = f'{app.config["SERVER_URL"]}/static/notes/{note_id}/assets/{name}.{filetype}'
                else:
                    # 如果没有指定note_id，存储到临时目录
                    os.makedirs('static', exist_ok=True)
                    file_path = os.path.join('static', f'{name}.{filetype}')
                    url = f'{app.config["SERVER_URL"]}/static/{name}.{filetype}'

            try:
                # 保存文件
                with open(file_path, 'wb') as f:
                    f.write(request.data)
                logging.info(f'Successfully saved file to: {file_path}')

                return jsonify({
                    'success': True,
                    'url': url
                })

            except IOError as e:
                logging.error(f'Error saving file {file_path}: {e}')
                abort(500, description="Error saving file")

        except Exception as e:
            logging.error(f"Error processing upload: {str(e)}", exc_info=True)
            abort(500, description="Internal server error")

    @app.route('/api/index/check', methods=['GET'])
    def check_index():
        """检查索引页面是否存在"""
        try:
            exists = os.path.exists('static/index.html')
            return jsonify({
                'exists': exists,
                'url': f'{app.config["SERVER_URL"]}/index' if exists else None
            })
        except Exception as e:
            logging.error(f"Error checking index: {e}")
            abort(500)
    
    @app.route('/api/index/create', methods=['POST'])
    @require_auth
    def create_index_page():
        """创建或更新索引页面"""
        try:
            data = request.get_json()
            if not data or 'content' not in data:
                abort(400, description="Missing content")
                
            # 准备模板数据 - 使用"首页"作为标题
            template_data = {
                'template': {
                    'title': '首页',
                    'content': data['content'],
                    'description': data.get('description', '首页')
                },
                'files': data.get('files', [])
            }
            
            # 通过cook_note处理内容
            html, _ = cook_note({'template': template_data['template']})
            
            # 指定index.html作为文件名
            file_path = 'static/index.html'
            
            # 处理文档中的资源文件
            handle_note_assets(template_data, 'index')
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
                
            # 清理缓存
            cache_service.delete("index")
            cache_service.delete("get_doc_tree")
            
            return jsonify({
                'success': True,
                'url': f'{app.config["SERVER_URL"]}/index'
            })
        except Exception as e:
            logging.error(f"Error creating index: {e}")
            abort(500)
    
    @app.route('/api/doc-tree', methods=['GET'])
    @cache(ttl=300)  # 缓存文档树5分钟
    def get_doc_tree():
        """获取文档树结构"""
        try:
            notes = []
            static_dir = 'static'
            for file in os.listdir(static_dir):
                if file.endswith('.html'):
                    with open(os.path.join(static_dir, file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 提取标题
                        title_match = re.search(r'<title>(.*?)</title>', content)
                        title = title_match.group(1) if title_match else os.path.splitext(file)[0]
                        
                        # 获取文件名并处理索引页面
                        file_name = os.path.splitext(file)[0]
                        url = f'/{file_name}'
                        is_index = (file_name == 'index')
                        
                        notes.append({
                            'title': '首页' if is_index else title,
                            'url': url,
                            'isFolder': False,
                            'isIndex': is_index
                        })
            
            # 按标题排序
            notes.sort(key=lambda x: x['title'])
            
            # 将首页放在最前面
            for i, note in enumerate(notes):
                if note.get('isIndex'):
                    notes.insert(0, notes.pop(i))
                    break
            
            # 组织成文件夹结构
            return jsonify(organize_notes_by_folder(notes))
        except Exception as e:
            logging.error(f"Error getting doc tree: {e}")
            abort(500)

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

    return app