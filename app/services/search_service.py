import re
import os
from typing import List, Dict
from bs4 import BeautifulSoup
import logging


class SearchService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SearchService, cls).__new__(cls)
            cls._instance._index = {}       # word -> [{title, url, text}]
            cls._instance._indexed = False
        return cls._instance

    def rebuild_index(self, path: str = 'static') -> None:
        """构建/重建倒排索引"""
        index: Dict[str, List[Dict]] = {}

        if not os.path.exists(path):
            self._index = index
            self._indexed = True
            return

        for root, _, files in os.walk(path):
            for file in files:
                if not file.endswith('.html'):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    soup = BeautifulSoup(content, 'html.parser')
                    title = soup.title.string.strip() if soup.title and soup.title.string else ''
                    article = soup.find('article')
                    text = article.get_text() if article else soup.get_text()

                    url = '/' + os.path.splitext(os.path.relpath(file_path, path))[0].replace('\\', '/')

                    doc = {'title': title, 'url': url, 'text': text}

                    # 对标题和正文分词，全部小写
                    words = set(re.findall(r'\w+', (title + ' ' + text).lower()))
                    for word in words:
                        if len(word) < 2:
                            continue
                        index.setdefault(word, []).append(doc)

                except Exception as e:
                    logging.warning(f"搜索索引构建时跳过 {file_path}: {e}")

        self._index = index
        self._indexed = True
        logging.info(f"搜索索引构建完成，共 {len(index)} 个词条")

    def _ensure_index(self, path: str = 'static') -> None:
        if not self._indexed:
            self.rebuild_index(path)

    def search_notes(self, query: str, path: str = 'static') -> List[Dict]:
        """搜索笔记内容（基于倒排索引）"""
        self._ensure_index(path)

        query_lower = query.lower()
        query_words = [w for w in re.findall(r'\w+', query_lower) if len(w) >= 2]

        if not query_words:
            return []

        # 取各词对应文档集合的交集（AND 语义）
        candidate_sets = []
        for word in query_words:
            matched = {doc['url']: doc for doc in self._index.get(word, [])}
            # 也支持包含该词的超集（前缀匹配）
            for indexed_word, docs in self._index.items():
                if indexed_word.startswith(word) and indexed_word != word:
                    for doc in docs:
                        matched[doc['url']] = doc
            candidate_sets.append(matched)

        if not candidate_sets:
            return []

        # 交集
        common_urls = set(candidate_sets[0].keys())
        for cs in candidate_sets[1:]:
            common_urls &= set(cs.keys())

        results = []
        for url in common_urls:
            doc = candidate_sets[0][url]
            preview = self._generate_preview(doc['text'], query_lower)
            results.append({
                'title': doc['title'],
                'url': url,
                'preview': preview,
            })

        return sorted(results, key=lambda x: x['title'].lower())

    def _generate_preview(self, content: str, query: str, context_length: int = 100) -> str:
        """生成搜索结果预览"""
        query_pos = content.lower().find(query.lower())
        if query_pos == -1:
            return content[:context_length] + '...'

        start = max(0, query_pos - context_length // 2)
        end = min(len(content), query_pos + len(query) + context_length // 2)

        if start > 0:
            ws = content.find(' ', start)
            start = ws if ws != -1 else start

        if end < len(content):
            ws = content.rfind(' ', 0, end)
            end = ws if ws != -1 else end

        preview = content[start:end].strip()
        if start > 0:
            preview = '...' + preview
        if end < len(content):
            preview = preview + '...'

        return preview


search_service = SearchService()
