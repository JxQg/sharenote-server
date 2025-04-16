import unicodedata
import re
import hashlib
import os
import shutil
import logging
from pypinyin import lazy_pinyin, Style
from app.config.config_manager import config
from app.services.cache_service import cache, cache_service

@cache(ttl=3600)
def slugify(value: str) -> str:
    """
    将标题转换为URL友好的格式
    - 中文转换为拼音
    - 特殊字符替换为连字符
    - 添加短哈希确保唯一性
    """
    # 转换中文为拼音
    pinyin_list = lazy_pinyin(value, style=Style.NORMAL)
    value_to_process = ' '.join(pinyin_list)
    
    # 标准化为 ASCII
    value_to_process = unicodedata.normalize('NFKD', value_to_process).encode('ascii', 'ignore').decode('ascii')
    # 删除非单词字符（保留空格和连字符）
    value_to_process = re.sub(r'[^\w\s-]', '', value_to_process).strip().lower()
    # 将连续的空格或连字符替换为单个连字符
    value_to_process = re.sub(r'[-\s]+', '-', value_to_process)
    
    # 添加短哈希确保唯一性
    short_code = gen_short_code(value)
    return f"{value_to_process}-{short_code}"

@cache(ttl=3600)
def gen_short_code(title):
    """根据标题生成短码"""
    string = title + config.get('security.secret_api_key')
    hash_object = hashlib.sha256(string.encode())
    digest = hash_object.hexdigest()
    return digest[:6]

@cache(ttl=300)  # 缓存5分钟
def cook_note(data):
    """处理笔记模板,保持与原版一致性"""
    template = data['template']
    
    # 读取模板文件
    template_path = config.get('templates.note_template', 'template/note-template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 获取站点名称，默认为 "Share Note"
    server_name = config.get('server.server_name', 'Share Note')
    
    # 设置页面标题，不再添加站点名称
    page_title = template['title'] if template['title'] else "Untitled"
    # 替换模板变量
    html = html.replace('TEMPLATE_TITLE', page_title)
    html = html.replace(
        'TEMPLATE_OG_TITLE',
        f'<meta property="og:title" content="{page_title}">'
    )
    
    # 替换其他模板变量
    html = html.replace(
        'TEMPLATE_META_DESCRIPTION',
        f'<meta name="description" content="{template.get("description", "")}" property="og:description">'
    )
    
    html = html.replace(   # 保持宽度设置与原版一致
        'TEMPLATE_WIDTH',
        '.markdown-preview-sizer.markdown-preview-section { max-width: 1080px !important; margin: 0 auto; }'
    )
    
    # 添加CSS路径
    theme_css_path = '/static/theme.css' if os.path.isfile('static/theme.css') else '/assets/css/theme.css'
    html = html.replace('TEMPLATE_CSS', theme_css_path)
    
    # 添加服务器URL
    html = html.replace('TEMPLATE_ASSETS_WEBROOT', config.get('server.server_url'))
    
    # 替换服务器名称
    html = html.replace('TEMPLATE_SERVER_NAME', server_name)
    
    # 替换正文内容
    html = html.replace('TEMPLATE_NOTE_CONTENT', template['content'])
    
    # 替换默认类名
    html = html.replace('TEMPLATE_BODY', 'class="mod-linux is-frameless is-hidden-frameless obsidian-app theme-light show-inline-title show-ribbon show-view-header is-focused share-note-plugin" style="--zoom-factor: 1; --font-text-size: 16px;"')
    html = html.replace('TEMPLATE_PREVIEW', 'class="markdown-preview-view markdown-rendered node-insert-event allow-fold-headings show-indentation-guide allow-fold-lists show-properties" style="tab-size: 4;"')
    html = html.replace('TEMPLATE_PUSHER', 'class="markdown-preview-pusher" style="width: 1px; height: 0.1px;"')
    
    # 替换网站标题
    html = html.replace('Share Note', server_name)
    
    # 将标题也放在面包屑导航中
    html = html.replace('TEMPLATE_TITLE</span>', page_title + '</span>')
    
    # 清空其他未使用的模板变量
    html = html.replace('TEMPLATE_SCRIPTS', '')
    html = html.replace('TEMPLATE_ENCRYPTED_DATA', '')
    
    # 生成文件名
    filename = slugify(template['title']) if template['title'] else 'untitled-' + gen_short_code('untitled')
    
    return html, filename

def create_note_assets_folder(filename: str):
    """为文档创建独立的静态资源文件夹
    
    Args:
        filename: 文档的文件名（不包含.html后缀）
    
    Returns:
        str: 资源目录的路径
    """
    assets_path = os.path.join('static', 'notes', filename)
    os.makedirs(assets_path, exist_ok=True)
    return assets_path

def handle_note_assets(data, filename: str):
    """处理文档相关的静态资源文件
    
    Args:
        data: 请求数据
        filename: 文档的文件名（不包含.html后缀）
    """
    # 创建笔记专属的资源目录
    assets_path = os.path.join('static', 'notes', filename, 'assets')
    os.makedirs(assets_path, exist_ok=True)
    
    # 如果是更新文档，先检查是否存在原有内容
    note_file = os.path.join('static', f'{filename}.html')
    update_mode = os.path.exists(note_file)
    
    # 处理文件上传的资源
    if 'files' in data:
        for file in data['files']:
            original_name = file.get('name', '')
            file_hash = file['hash']
            file_type = file['filetype']
            safe_name = f"{file_hash}{os.path.splitext(original_name)[1]}" if original_name else f"{file_hash}.{file_type}"
            
            # 检查文件是否已经在笔记目录中
            target_path = os.path.join(assets_path, safe_name)
            if not os.path.exists(target_path):
                # 如果不在笔记目录中，检查是否在临时目录
                temp_path = os.path.join('static', f"{file_hash}.{file_type}")
                if os.path.exists(temp_path):
                    try:
                        # 确保目标目录存在
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        # 移动文件到笔记目录
                        shutil.move(temp_path, target_path)
                        logging.info(f"Successfully moved file from {temp_path} to {target_path}")
                    except Exception as e:
                        logging.error(f"Error moving file {temp_path}: {e}")
                        continue
            
            # 更新文件URL
            file['url'] = f"/static/notes/{filename}/assets/{safe_name}"
            
            # 如果是图片，更新文档中的引用
            if file_type.lower() in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']:
                if 'content' in data['template']:
                    # 更新各种可能的图片引用格式
                    replacements = [
                        (f"app://{file_hash}", file['url']),
                        (f"file://{file.get('original_path', '')}", file['url']),
                        (file.get('original_path', ''), file['url']),
                        # 修复: 增加对根路径图片的替换
                        (f"/static/{file_hash}.{file_type}", file['url']),
                        (f"/static/{file_hash}{os.path.splitext(original_name)[1] if original_name else ''}", file['url'])
                    ]
                    for old_path, new_path in replacements:
                        if old_path:
                            data['template']['content'] = data['template']['content'].replace(old_path, new_path)

    # 清理旧资源
    if update_mode and os.path.exists(note_file):
        try:
            with open(note_file, 'r', encoding='utf-8') as f:
                old_content = f.read()
                # 从旧文档中提取图片资源路径
                old_assets = set()
                for line in old_content.split('\n'):
                    if 'src="/static/notes/' in line:
                        start = line.find('src="') + 5
                        end = line.find('"', start)
                        if start > 4 and end > start:
                            old_assets.add(line[start:end])
                
                # 如果旧资源在新内容中不存在，则进行清理
                new_content = data['template']['content']
                for old_asset in old_assets:
                    if old_asset not in new_content:
                        asset_path = os.path.join('static', old_asset.lstrip('/'))
                        if os.path.exists(asset_path):
                            try:
                                os.remove(asset_path)
                                logging.info(f"Removed unused asset: {asset_path}")
                            except Exception as e:
                                logging.error(f"Error removing old asset {asset_path}: {e}")
        except Exception as e:
            logging.error(f"处理旧文档资源时出错: {e}")

    # 迁移散落在根目录的资源文件
    try:
        for f in os.listdir('static'):
            file_path = os.path.join('static', f)
            if os.path.isfile(file_path):
                ext = os.path.splitext(f)[1].lower()
                # 不处理笔记文件和主题CSS文件
                if ext == '.html' or f == 'theme.css':
                    continue
                
                # 尝试从文件名中提取哈希值
                name_without_ext = os.path.splitext(f)[0]
                if re.match(r'^[a-f0-9]{40}$', name_without_ext):
                    target_path = os.path.join(assets_path, f)
                    try:
                        # 确保目标目录存在
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        # 移动文件到笔记目录
                        shutil.move(file_path, target_path)
                        logging.info(f"Migrated file from {file_path} to {target_path}")
                        # 更新文档中的引用
                        if 'content' in data['template']:
                            old_url = f"/static/{f}"
                            new_url = f"/static/notes/{filename}/assets/{f}"
                            data['template']['content'] = data['template']['content'].replace(old_url, new_url)
                    except Exception as e:
                        logging.error(f"Error migrating file {file_path}: {e}")
    except Exception as e:
        logging.error(f"迁移资源文件时出错: {e}")
    
    # 清除相关缓存
    cache_service.delete(f"note_assets:{filename}")
    return data

def delete_note_assets(filename: str):
    """删除文档相关的所有静态资源
    
    Args:
        filename: 文档的文件名（不包含.html后缀）
    """
    assets_path = os.path.join('static', 'notes', filename)
    if os.path.exists(assets_path):
        shutil.rmtree(assets_path)
    # 清除相关缓存
    cache_service.delete(f"note_assets:{filename}")

@cache(ttl=300)
def organize_notes_by_folder(notes):
    """将笔记按文件夹结构组织"""
    tree = []
    folders = {}
    
    for note in notes:
        path_parts = note['title'].split('/')
        current_level = tree
        
        # 如果有路径分隔符，创建文件夹结构
        if len(path_parts) > 1:
            for i, part in enumerate(path_parts[:-1]):
                folder_path = '/'.join(path_parts[:i+1])
                
                # 检查文件夹是否已存在
                if folder_path not in folders:
                    new_folder = {
                        'title': part,
                        'isFolder': True,
                        'children': []
                    }
                    folders[folder_path] = new_folder
                    current_level.append(new_folder)
                
                current_level = folders[folder_path]['children']
            
            # 添加文件到最后一级文件夹
            note['title'] = path_parts[-1]
            current_level.append(note)
        else:
            # 没有路径分隔符的直接添加到根级别
            tree.append(note)
    
    return tree

def convert_obsidian_images(content: str, doc_filename: str) -> str:
    """将Obsidian格式的图片链接转换为HTML格式，并调整为正确的存储路径
    
    Args:
        content: 包含Obsidian格式图片链接的文本内容
        doc_filename: 文档的文件名（不包含.html后缀）
        
    Returns:
        转换后的HTML格式内容
    """
    # 匹配Obsidian格式的图片链接 ![[_resources/filename.png]]
    pattern = r'!\[\[(_resources/([^\]]+))\]\]'
    
    # 替换为HTML img标签，并调整路径
    def replace_to_html(match):
        original_path = match.group(1)  # 完整路径
        img_filename = match.group(2)   # 仅文件名
        
        # 构建新的资源路径
        assets_path = os.path.join('static', 'notes', doc_filename, 'assets')
        new_file_path = os.path.join(assets_path, img_filename)
        web_path = f'/static/notes/{doc_filename}/assets/{img_filename}'
        
        # 尝试多个位置查找原始文件
        possible_paths = [
            original_path,  # 原始路径
            os.path.join('static', original_path),  # static下的路径
            os.path.join('static', img_filename),  # 直接在static目录下查找文件
            os.path.join('static', '_resources', img_filename),  # _resources目录
            f"static/{img_filename.split('/')[-1]}"  # 仅使用文件名在static目录下查找
        ]
        
        # 确保资源目录存在
        os.makedirs(assets_path, exist_ok=True)
        
        # 查找并复制文件
        for src_path in possible_paths:
            if os.path.exists(src_path):
                try:
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                    shutil.copy2(src_path, new_file_path)
                    logging.info(f"Successfully copied image from {src_path} to {new_file_path}")
                    break
                except Exception as e:
                    logging.error(f"Error copying file {src_path}: {e}")
                    continue
        
        return f'<img src="{web_path}" alt="图片">'
        
    return re.sub(pattern, replace_to_html, content)