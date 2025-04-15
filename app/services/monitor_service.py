import os
import psutil
import time
from typing import Dict, Any
from app.services.cache_service import cache

class MonitorService:
    _instance = None
    _start_time = time.time()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MonitorService, cls).__new__(cls)
        return cls._instance

    @cache(ttl=60)
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统状态信息"""
        process = psutil.Process()
        
        # 获取当前工作目录所在的磁盘
        current_path = os.path.abspath(os.getcwd())
        disk_root = os.path.splitdrive(current_path)[0] or '/'
        
        return {
            'uptime': int(time.time() - self._start_time),
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk_usage': {
                'total': psutil.disk_usage(disk_root).total,
                'used': psutil.disk_usage(disk_root).used,
                'free': psutil.disk_usage(disk_root).free,
                'percent': psutil.disk_usage(disk_root).percent
            },
            'process': {
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
        }
        
    @cache(ttl=300)
    def get_storage_stats(self, directory: str = 'static') -> Dict[str, Any]:
        """获取存储统计信息"""
        stats = {
            'total_notes': 0,
            'total_size': 0,
            'by_type': {}
        }
        
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                ext = os.path.splitext(file)[1].lower()
                
                if ext == '.html':
                    stats['total_notes'] += 1
                    
                stats['total_size'] += file_size
                
                if ext not in stats['by_type']:
                    stats['by_type'][ext] = {
                        'count': 0,
                        'size': 0
                    }
                stats['by_type'][ext]['count'] += 1
                stats['by_type'][ext]['size'] += file_size
                
        return stats

monitor_service = MonitorService()