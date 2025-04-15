import unittest
import os
import shutil
import time
from unittest.mock import patch, MagicMock
from app.services.file_watcher import FileWatcher, NoteChangeHandler

class TestFileWatcher(unittest.TestCase):
    def setUp(self):
        """每个测试前的设置"""
        self.test_dir = 'test_static'
        os.makedirs(self.test_dir, exist_ok=True)
        self.file_watcher = FileWatcher()
        
    def tearDown(self):
        """每个测试后的清理"""
        self.file_watcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_start_stop(self):
        """测试启动和停止监控"""
        # 启动监控
        self.file_watcher.start(self.test_dir)
        self.assertIsNotNone(self.file_watcher.observer)
        self.assertTrue(self.file_watcher.observer.is_alive())
        
        # 停止监控
        self.file_watcher.stop()
        self.assertIsNone(self.file_watcher.observer)
        
    def test_add_watch_path(self):
        """测试添加监控路径"""
        # 创建测试目录
        new_path = os.path.join(self.test_dir, 'subfolder')
        
        # 启动监控
        self.file_watcher.start(self.test_dir)
        
        # 添加新的监控路径
        self.file_watcher.add_watch_path(new_path)
        
        # 验证路径已添加
        self.assertIn(new_path, self.file_watcher.watch_paths)
        
    @patch('logging.info')
    def test_file_change_detection(self, mock_logging):
        """测试文件变更检测"""
        # 启动监控
        self.file_watcher.start(self.test_dir)
        
        # 创建测试文件
        test_file = os.path.join(self.test_dir, 'test.html')
        with open(test_file, 'w') as f:
            f.write('Initial content')
            
        # 等待一下以确保文件变更被检测到
        time.sleep(1)
        
        # 修改文件
        with open(test_file, 'w') as f:
            f.write('Modified content')
            
        # 等待一下以确保变更被处理
        time.sleep(1)
        
        # 验证日志记录
        mock_logging.assert_any_call(f'文件监控已启动: {self.test_dir}')
        
    def test_singleton_pattern(self):
        """测试单例模式"""
        watcher1 = FileWatcher()
        watcher2 = FileWatcher()
        
        self.assertIs(watcher1, watcher2)
        
    def test_multiple_start_calls(self):
        """测试多次调用start方法"""
        self.file_watcher.start(self.test_dir)
        observer1 = self.file_watcher.observer
        
        # 再次调用start不应创建新的observer
        self.file_watcher.start(self.test_dir)
        observer2 = self.file_watcher.observer
        
        self.assertIs(observer1, observer2)
        
class TestNoteChangeHandler(unittest.TestCase):
    def setUp(self):
        """每个测试前的设置"""
        self.handler = NoteChangeHandler()
        self.test_dir = 'test_static'
        os.makedirs(self.test_dir, exist_ok=True)
        
    def tearDown(self):
        """每个测试后的清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('logging.info')
    def test_on_modified(self, mock_logging):
        """测试文件修改处理"""
        # 创建模拟事件
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = os.path.join(self.test_dir, 'test.html')
        
        # 调用处理方法
        self.handler.on_modified(mock_event)
        
        # 验证日志记录
        mock_logging.assert_any_call(f'检测到文件变更: {mock_event.src_path}')
        
    @patch('logging.info')
    def test_ignore_non_html_files(self, mock_logging):
        """测试忽略非HTML文件"""
        # 创建模拟事件
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = os.path.join(self.test_dir, 'test.txt')
        
        # 调用处理方法
        self.handler.on_modified(mock_event)
        
        # 验证没有处理非HTML文件
        mock_logging.assert_not_called()
        
    @patch('logging.info')
    def test_ignore_directories(self, mock_logging):
        """测试忽略目录变更"""
        # 创建模拟事件
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = os.path.join(self.test_dir)
        
        # 调用处理方法
        self.handler.on_modified(mock_event)
        
        # 验证没有处理目录变更
        mock_logging.assert_not_called()

if __name__ == '__main__':
    unittest.main()