from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import os
import threading
import time

class NoteChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.html'):
            logging.info(f"检测到文件变更: {event.src_path}")
            self._handle_note_change(event.src_path)
    
    def _handle_note_change(self, file_path):
        """处理笔记文件变更"""
        try:
            # 这里可以添加笔记更新后的处理逻辑
            # 例如：更新搜索索引、清理缓存等
            logging.info(f"正在处理文件变更: {file_path}")
        except Exception as e:
            logging.error(f"处理文件变更时出错: {e}")

class FileWatcher:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FileWatcher, cls).__new__(cls)
            cls._instance.observer = None
            cls._instance.watch_paths = set()
        return cls._instance
    
    def start(self, path='static'):
        """启动文件监控"""
        if self.observer is not None:
            return
            
        if not os.path.exists(path):
            os.makedirs(path)
            
        self.observer = Observer()
        event_handler = NoteChangeHandler()
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()
        self.watch_paths.add(path)
        
        logging.info(f"文件监控已启动: {path}")
        
    def stop(self):
        """停止文件监控"""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logging.info("文件监控已停止")
            
    def add_watch_path(self, path):
        """添加监控路径"""
        if not os.path.exists(path):
            os.makedirs(path)
            
        if path not in self.watch_paths and self.observer is not None:
            event_handler = NoteChangeHandler()
            self.observer.schedule(event_handler, path, recursive=True)
            self.watch_paths.add(path)
            logging.info(f"添加监控路径: {path}")

file_watcher = FileWatcher()