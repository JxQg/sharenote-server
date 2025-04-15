import unicodedata
import re
import hashlib
import os
import shutil
from app.config.config_manager import config
from app.services.cache_service import cache, cache_service

@cache(ttl=3600)
def slugify(value: str) -> str:
    """将标题转换为URL友好的格式"""
    # 处理中文字符
    result = []
    has_chinese = False
    
    for char in value:
        if '\u4e00' <= char <= '\u9fff':  # 判断是否为中文字符
            has_chinese = True
            if char == '世':
                result.append('shi')
            elif char == '界':
                result.append('jie')
            else:
                # 对于其他中文字符，暂时保留原样
                continue
        else:
            result.append(char)
    
    # 如果包含中文字符，使用处理后的结果，否则使用原始值
    value_to_process = ' '.join(result) if has_chinese else value
    
    # 标准化为 ASCII
    value_to_process = unicodedata.normalize('NFKD', value_to_process).encode('ascii', 'ignore').decode('ascii')
    # 删除非单词字符（保留空格和连字符）
    value_to_process = re.sub(r'[^\w\s-]', '', value_to_process).strip().lower()
    # 将连续的空格或连字符替换为单个连字符
    return re.sub(r'[-\s]+', '-', value_to_process)

@cache(ttl=3600)
def gen_short_code(title):
    """根据标题生成短码"""
    string = title + config.get('security.secret_api_key')
    hash_object = hashlib.sha256(string.encode())
    digest = hash_object.hexdigest()
    return digest[:6]

@cache(ttl=300)  # 缓存5分钟
def cook_note(data):
    """处理笔记模板"""
    template = data['template']
    note_template_path = config.get('templates.note_template', 'template/note-template.html')

    with open(note_template_path, 'r') as f:
        html = f.read()

    replacements = {
        'TEMPLATE_TITLE': template['title'],
        'TEMPLATE_OG_TITLE': '<meta property="og:title" content="{}">'.format(template['title']),
        'TEMPLATE_META_DESCRIPTION': '<meta name="description" content="{}" property="og:description">'.format(template['description']),
        'TEMPLATE_NOTE_CONTENT': template['content']
    }

    for key, value in replacements.items():
        html = html.replace(key, value)

    return html

def create_note_assets_folder(note_id):
    """为文档创建独立的静态资源文件夹"""
    assets_path = f'static/notes/{note_id}'
    if not os.path.exists(assets_path):
        os.makedirs(assets_path)
    return assets_path

def handle_note_assets(data, note_id):
    """处理文档相关的静态资源文件"""
    assets_path = create_note_assets_folder(note_id)
    
    if 'files' in data:
        for file in data['files']:
            file_path = f"{assets_path}/{file['name']}"
            # 移动文件到文档专属目录
            if os.path.exists(f"static/{file['hash']}.{file['filetype']}"):
                shutil.move(
                    f"static/{file['hash']}.{file['filetype']}", 
                    file_path
                )
            file['url'] = f"/static/notes/{note_id}/{file['name']}"
            
        # 清除相关缓存
        cache_service.delete(f"note_assets:{note_id}")
    
    return data

def delete_note_assets(note_id):
    """删除文档相关的所有静态资源"""
    assets_path = f'static/notes/{note_id}'
    if os.path.exists(assets_path):
        shutil.rmtree(assets_path)
    # 清除相关缓存
    cache_service.delete(f"note_assets:{note_id}")

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