import unittest
import os
import shutil
from app.services.search_service import SearchService
from bs4 import BeautifulSoup

class TestSearchService(unittest.TestCase):
    def setUp(self):
        """每个测试前的设置"""
        self.search_service = SearchService()
        self.test_dir = 'test_static'
        os.makedirs(self.test_dir, exist_ok=True)
        
    def tearDown(self):
        """每个测试后的清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def create_test_note(self, filename, title, content):
        """创建测试笔记文件"""
        html_content = f"""
        <html>
            <head><title>{title}</title></head>
            <body><article>{content}</article></body>
        </html>
        """
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    def test_search_by_title(self):
        """测试通过标题搜索"""
        self.create_test_note('note1.html', '测试笔记1', '这是第一个笔记的内容')
        self.create_test_note('note2.html', '测试笔记2', '这是第二个笔记的内容')
        
        results = self.search_service.search_notes('测试', self.test_dir)
        self.assertEqual(len(results), 2)
        
        results = self.search_service.search_notes('笔记1', self.test_dir)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], '测试笔记1')
        
    def test_search_by_content(self):
        """测试通过内容搜索"""
        self.create_test_note('note1.html', '笔记1', '这是一个包含特殊关键词的笔记')
        self.create_test_note('note2.html', '笔记2', '这是一个普通的笔记')
        
        results = self.search_service.search_notes('特殊关键词', self.test_dir)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], '笔记1')
        
    def test_preview_generation(self):
        """测试预览文本生成"""
        long_content = '前面的文字 ' * 10 + '目标关键词' + ' 后面的文字' * 10
        self.create_test_note('note.html', '长文本笔记', long_content)
        
        results = self.search_service.search_notes('目标关键词', self.test_dir)
        self.assertEqual(len(results), 1)
        
        preview = results[0]['preview']
        self.assertIn('目标关键词', preview)
        self.assertTrue(preview.startswith('...') or preview.endswith('...'))
        
    def test_highlight_positions(self):
        """测试高亮位置计算"""
        content = "这是第一个关键词，这是第二个关键词"
        self.create_test_note('note.html', '高亮测试', content)
        
        results = self.search_service.search_notes('关键词', self.test_dir)
        self.assertEqual(len(results), 1)
        
        highlights = results[0]['highlight']
        self.assertEqual(len(highlights), 2)
        self.assertTrue(all('start' in h and 'length' in h for h in highlights))
        
    def test_case_insensitive_search(self):
        """测试大小写不敏感搜索"""
        self.create_test_note('note.html', 'Test Note', 'This is a Test content')
        
        results = self.search_service.search_notes('test', self.test_dir)
        self.assertEqual(len(results), 1)
        
        results = self.search_service.search_notes('TEST', self.test_dir)
        self.assertEqual(len(results), 1)
        
    def test_minimum_query_length(self):
        """测试最小查询长度限制"""
        self.create_test_note('note.html', '测试笔记', '笔记内容')
        
        results = self.search_service.search_notes('a', self.test_dir)
        self.assertEqual(len(results), 0)
        
if __name__ == '__main__':
    unittest.main()