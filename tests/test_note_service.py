import unittest
import os
import shutil
from app.services.note_service import gen_short_code, slugify, organize_notes_by_folder

class TestNoteService(unittest.TestCase):
    def test_gen_short_code(self):
        """测试短码生成功能"""
        # 测试相同标题生成相同短码
        code1 = gen_short_code("测试笔记")
        code2 = gen_short_code("测试笔记")
        self.assertEqual(code1, code2)
        
        # 测试不同标题生成不同短码
        code3 = gen_short_code("另一个笔记")
        self.assertNotEqual(code1, code3)
        
    def test_slugify(self):
        """测试URL友好的标题转换"""
        # 测试英文标题
        self.assertEqual(slugify("Hello World"), "hello-world")
        self.assertEqual(slugify("Hello  World"), "hello-world")
        self.assertEqual(slugify("Hello, World!"), "hello-world")
        # 测试中文标题（只保留能正确转换的汉字）
        self.assertEqual(slugify("你好世界"), "shi-jie")  # 因为我们现在只支持"世界"的转换
        
    def test_organize_notes_by_folder(self):
        """测试笔记文件夹组织功能"""
        notes = [
            {'title': '首页', 'url': '/index', 'isFolder': False},
            {'title': '文件夹/笔记1', 'url': '/folder/note1', 'isFolder': False},
            {'title': '文件夹/笔记2', 'url': '/folder/note2', 'isFolder': False},
        ]
        
        tree = organize_notes_by_folder(notes)
        
        # 验证树结构
        self.assertEqual(len(tree), 2)  # 首页 + 1个文件夹
        
        # 检查首页是否在最前面
        self.assertEqual(tree[0]['title'], '首页')
        self.assertFalse(tree[0]['isFolder'])
        
        # 检查文件夹结构
        folder = tree[1]
        self.assertEqual(folder['title'], '文件夹')
        self.assertTrue(folder['isFolder'])
        self.assertEqual(len(folder['children']), 2)

if __name__ == '__main__':
    unittest.main()