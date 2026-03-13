import os
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

    def _read_cpu_percent(self, interval: float = 0.1) -> float:
        """从 /proc/stat 计算 CPU 使用率"""
        def _stat():
            with open('/proc/stat') as f:
                parts = f.readline().split()
            total = sum(int(x) for x in parts[1:])
            idle = int(parts[4])
            return total, idle

        t1, i1 = _stat()
        time.sleep(interval)
        t2, i2 = _stat()
        diff = t2 - t1
        return round((1 - (i2 - i1) / diff) * 100, 1) if diff else 0.0

    def _read_meminfo(self) -> Dict[str, Any]:
        """从 /proc/meminfo 读取内存信息"""
        info = {}
        with open('/proc/meminfo') as f:
            for line in f:
                k, v = line.split(':')
                info[k.strip()] = int(v.split()[0]) * 1024  # KB → bytes
        total = info.get('MemTotal', 0)
        available = info.get('MemAvailable', 0)
        return {
            'total': total,
            'available': available,
            'percent': round((total - available) / total * 100, 1) if total else 0.0,
        }

    def _read_process_mem_percent(self, total_mem: int) -> float:
        """从 /proc/self/status 读取进程物理内存占比"""
        if not total_mem:
            return 0.0
        try:
            with open('/proc/self/status') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        rss = int(line.split()[1]) * 1024
                        return round(rss / total_mem * 100, 2)
        except OSError:
            pass
        return 0.0

    @cache(ttl=60)
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统状态信息"""
        mem = self._read_meminfo()
        root = os.path.splitdrive(os.path.abspath(os.getcwd()))[1] or '/'
        vfs = os.statvfs(root)
        disk_total = vfs.f_frsize * vfs.f_blocks
        disk_free = vfs.f_frsize * vfs.f_bfree
        disk_used = disk_total - disk_free
        return {
            'uptime': int(time.time() - self._start_time),
            'cpu_usage': self._read_cpu_percent(),
            'memory_usage': mem,
            'disk_usage': {
                'total': disk_total,
                'used': disk_used,
                'free': disk_free,
                'percent': round(disk_used / disk_total * 100, 1) if disk_total else 0.0,
            },
            'process': {
                'cpu_percent': 0.0,
                'memory_percent': self._read_process_mem_percent(mem['total']),
                'threads': 0,
                'open_files': 0,
                'connections': 0,
            },
        }

    @cache(ttl=300)
    def get_storage_stats(self, directory: str = 'static') -> Dict[str, Any]:
        """获取存储统计信息"""
        stats = {'total_notes': 0, 'total_size': 0, 'by_type': {}}
        for root, _, files in os.walk(directory):
            for file in files:
                size = os.path.getsize(os.path.join(root, file))
                ext = os.path.splitext(file)[1].lower()
                if ext == '.html':
                    stats['total_notes'] += 1
                stats['total_size'] += size
                entry = stats['by_type'].setdefault(ext, {'count': 0, 'size': 0})
                entry['count'] += 1
                entry['size'] += size
        return stats


monitor_service = MonitorService()
