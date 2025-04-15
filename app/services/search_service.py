import re
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from app.services.cache_service import cache

class SearchService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SearchService, cls).__new__(cls)
        return cls._instance

    @cache(ttl=300)
    def search_notes(self, query: str, path: str = 'static') -> List[Dict]:
        """搜索笔记内容"""
        results = []
        query = query.lower()
        
        # 遍历所有HTML文件
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # 使用BeautifulSoup解析HTML
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # 获取标题
                        title = soup.title.string if soup.title else ''
                        
                        # 获取文章主体内容
                        article = soup.find('article')
                        if article:
                            text_content = article.get_text()
                        else:
                            text_content = soup.get_text()
                            
                        # 如果查询词在标题或内容中
                        if query in title.lower() or query in text_content.lower():
                            # 构建预览文本
                            preview = self._generate_preview(text_content, query)
                            
                            # 构建URL
                            url = '/' + os.path.splitext(os.path.relpath(file_path, path))[0]
                            
                            results.append({
                                'title': title,
                                'url': url,
                                'preview': preview,
                                'highlight': self._find_highlight_positions(text_content, query)
                            })
                            
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
                        
        return sorted(results, key=lambda x: x['title'].lower())

    def _generate_preview(self, content: str, query: str, context_length: int = 100) -> str:
        """生成搜索结果预览"""
        # 找到查询词的位置
        query_pos = content.lower().find(query.lower())
        if query_pos == -1:
            return content[:context_length] + '...'
            
        # 计算预览窗口的起始和结束位置
        start = max(0, query_pos - context_length // 2)
        end = min(len(content), query_pos + len(query) + context_length // 2)
        
        # 调整到单词边界
        if start > 0:
            start = content.find(' ', start)
            if start == -1:
                start = 0
                
        if end < len(content):
            end = content.rfind(' ', 0, end)
            if end == -1:
                end = len(content)
                
        # 生成预览文本
        preview = content[start:end].strip()
        if start > 0:
            preview = '...' + preview
        if end < len(content):
            preview = preview + '...'
            
        return preview

    def _find_highlight_positions(self, content: str, query: str) -> List[Dict]:
        """找到需要高亮显示的位置"""
        positions = []
        content_lower = content.lower()
        query_lower = query.lower()
        
        start = 0
        while True:
            pos = content_lower.find(query_lower, start)
            if pos == -1:
                break
                
            positions.append({
                'start': pos,
                'length': len(query)
            })
            start = pos + len(query)
            
        return positions

search_service = SearchService()