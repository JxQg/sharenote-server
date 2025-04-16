import unittest
import os
import shutil
from app.services.note_service import gen_short_code, slugify, organize_notes_by_folder, convert_obsidian_images

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
        # 测试英文标题（验证基本格式，忽略哈希后缀）
        result = slugify("Hello World")
        self.assertTrue(result.startswith("hello-world-"))
        self.assertEqual(len(result), len("hello-world") + 1 + 6)  # 基本slug + 连字符 + 6位哈希
        
        # 测试重复调用生成相同的结果
        self.assertEqual(slugify("Hello World"), slugify("Hello World"))
        
        # 测试中文标题
        result = slugify("你好世界")
        self.assertTrue(result.startswith("ni-hao-shi-jie-"))
        self.assertEqual(len(result.split('-')[-1]), 6)  # 验证6位哈希后缀
        
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

    def test_convert_obsidian_images(self):
        """测试Obsidian格式图片链接转换功能"""
        note_id = "test123"
        
        # 测试基本格式转换
        content = "这是一张图片 ![[_resources/test.png]]"
        expected = "这是一张图片 <img src=\"/static/notes/test123/assets/test.png\" alt=\"图片\">"
        self.assertEqual(convert_obsidian_images(content, note_id), expected)
        
        # 测试多个图片链接
        content = """
        第一张图 ![[_resources/1.png]]
        第二张图 ![[_resources/2.jpg]]
        """
        expected = """
        第一张图 <img src="/static/notes/test123/assets/1.png" alt="图片">
        第二张图 <img src="/static/notes/test123/assets/2.jpg" alt="图片">
        """
        self.assertEqual(convert_obsidian_images(content, note_id), expected)
        
        # 清理测试创建的资源目录
        test_assets_path = 'static/notes/test123'
        if os.path.exists(test_assets_path):
            shutil.rmtree(test_assets_path)

if __name__ == '__main__':
    unittest.main()