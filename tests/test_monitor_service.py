import unittest
import os
import shutil
from unittest.mock import patch, MagicMock
from app.services.monitor_service import MonitorService

class TestMonitorService(unittest.TestCase):
    def setUp(self):
        """每个测试前的设置"""
        self.monitor_service = MonitorService()
        self.test_dir = 'test_static'
        os.makedirs(self.test_dir, exist_ok=True)
        
    def tearDown(self):
        """每个测试后的清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.Process')
    def test_get_system_stats(self, mock_process, mock_disk, mock_memory, mock_cpu):
        """测试系统状态获取功能"""
        # 配置模拟对象
        mock_cpu.return_value = 45.2
        
        mock_memory.return_value = MagicMock(
            total=1024*1024*1024,  # 1GB
            available=512*1024*1024,  # 512MB
            percent=50.0
        )
        
        mock_disk.return_value = MagicMock(
            total=10*1024*1024*1024,  # 10GB
            used=3*1024*1024*1024,   # 3GB
            free=7*1024*1024*1024,   # 7GB
            percent=30.0
        )
        
        mock_process.return_value = MagicMock(
            cpu_percent=lambda: 5.0,
            memory_percent=lambda: 2.5,
            num_threads=lambda: 4,
            open_files=lambda: [],
            connections=lambda: []
        )
        
        # 获取系统状态
        stats = self.monitor_service.get_system_stats()
        
        # 验证结果
        self.assertIsInstance(stats, dict)
        self.assertIn('uptime', stats)
        self.assertIn('cpu_usage', stats)
        self.assertIn('memory_usage', stats)
        self.assertIn('disk_usage', stats)
        self.assertIn('process', stats)
        
        # 验证CPU使用率
        self.assertEqual(stats['cpu_usage'], 45.2)
        
        # 验证内存使用情况
        memory = stats['memory_usage']
        self.assertEqual(memory['total'], 1024*1024*1024)
        self.assertEqual(memory['available'], 512*1024*1024)
        self.assertEqual(memory['percent'], 50.0)
        
        # 验证磁盘使用情况
        disk = stats['disk_usage']
        self.assertEqual(disk['total'], 10*1024*1024*1024)
        self.assertEqual(disk['used'], 3*1024*1024*1024)
        self.assertEqual(disk['free'], 7*1024*1024*1024)
        self.assertEqual(disk['percent'], 30.0)
        
        # 验证进程信息
        process = stats['process']
        self.assertEqual(process['cpu_percent'], 5.0)
        self.assertEqual(process['memory_percent'], 2.5)
        self.assertEqual(process['threads'], 4)
        self.assertEqual(process['open_files'], 0)
        self.assertEqual(process['connections'], 0)
        
    def test_get_storage_stats(self):
        """测试存储统计功能"""
        # 创建测试文件
        os.makedirs(os.path.join(self.test_dir, 'subfolder'), exist_ok=True)
        with open(os.path.join(self.test_dir, 'test1.html'), 'w') as f:
            f.write('Test content 1')
        with open(os.path.join(self.test_dir, 'test2.html'), 'w') as f:
            f.write('Test content 2')
        with open(os.path.join(self.test_dir, 'subfolder/test3.pdf'), 'w') as f:
            f.write('Test content 3')
            
        # 获取存储统计
        stats = self.monitor_service.get_storage_stats(self.test_dir)
        
        # 验证结果
        self.assertIsInstance(stats, dict)
        self.assertIn('total_notes', stats)
        self.assertIn('total_size', stats)
        self.assertIn('by_type', stats)
        
        # 验证笔记数量
        self.assertEqual(stats['total_notes'], 2)  # 2个HTML文件
        
        # 验证文件类型统计
        by_type = stats['by_type']
        self.assertIn('.html', by_type)
        self.assertIn('.pdf', by_type)
        self.assertEqual(by_type['.html']['count'], 2)
        self.assertEqual(by_type['.pdf']['count'], 1)

if __name__ == '__main__':
    unittest.main()