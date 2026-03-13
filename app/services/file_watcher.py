from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import os

class NoteChangeHandler(FileSystemEventHandler):
    def __init__(self, watch_path: str = 'static'):
        super().__init__()
        self.watch_path = watch_path

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.html'):
            logging.info(f"检测到文件变更: {event.src_path}")
            self._handle_note_change(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.html'):
            logging.info(f"检测到新文件: {event.src_path}")
            self._handle_note_change(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.html'):
            logging.info(f"检测到文件删除: {event.src_path}")
            self._handle_note_change(event.src_path)

    def _handle_note_change(self, file_path):
        """处理笔记文件变更：重建搜索索引并清理缓存"""
        try:
            from app.services.search_service import search_service
            search_service.rebuild_index(self.watch_path)
            from app.services.cache_service import cache_service
            cache_service.clear()
            logging.info(f"文件变更处理完成: {file_path}")
        except Exception as e:
            logging.error(f"处理文件变更时出错: {e}")

class FileWatcher:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FileWatcher, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'observer'):
            self.observer = None
        if not hasattr(self, 'watch_paths'):
            self.watch_paths = set()
    
    def start(self, path='static'):
        """启动文件监控"""
        if self.observer is not None:
            return
            
        if not os.path.exists(path):
            os.makedirs(path)
            
        self.observer = Observer()
        event_handler = NoteChangeHandler(watch_path=path)
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
            event_handler = NoteChangeHandler(watch_path=path)
            self.observer.schedule(event_handler, path, recursive=True)
            self.watch_paths.add(path)
            logging.info(f"添加监控路径: {path}")

file_watcher = FileWatcher()