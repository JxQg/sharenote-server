import multiprocessing
import os

# 工作进程数，根据 CPU 核心数动态调整
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# 工作模式
worker_class = 'gevent'  # 使用 gevent 异步工作模式，提高并发性能
worker_connections = int(os.getenv('GUNICORN_WORKER_CONNECTIONS', '1000'))

# 超时设置
timeout = int(os.getenv('GUNICORN_TIMEOUT', '30'))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = 5  # 增加 keep-alive 时间

# 日志设置
logdir = os.path.join(os.getenv('LOG_DIR', 'logs'))
os.makedirs(logdir, exist_ok=True)
accesslog = os.path.join(logdir, 'access.log')
errorlog = os.path.join(logdir, 'error.log')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# 绑定地址
bind = [f"0.0.0.0:{os.getenv('PORT', '8086')}"]

# 进程名称
proc_name = 'sharenote-gunicorn'

# 预加载应用
preload_app = True

# 最大请求数和重启策略
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '50'))

# 工作进程启动超时
timeout = 30

# 性能优化
worker_tmp_dir = '/dev/shm'  # 使用内存文件系统提高性能
sendfile = True
tcp_nopush = True
tcp_nodelay = True

# SSL 配置
keyfile = os.getenv('SSL_KEYFILE')
certfile = os.getenv('SSL_CERTFILE')

# 统计信息
statsd_host = os.getenv('STATSD_HOST')
statsd_prefix = 'sharenote.gunicorn'

def on_starting(server):
    """服务启动时的钩子"""
    server.log.info("Sharenote server starting...")

def on_reload(server):
    """重新加载时的钩子"""
    server.log.info("Reloading Sharenote server...")

def post_fork(server, worker):
    """工作进程 fork 后的钩子"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_int(worker):
    """工作进程中断时的钩子"""
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """工作进程异常终止时的钩子"""
    worker.log.info("Worker received SIGABRT signal")

def pre_fork(server, worker):
    """Fork 工作进程前的钩子"""
    pass

def post_worker_init(worker):
    """工作进程初始化后的钩子"""
    worker.log.info(f"Worker {worker.pid} initialized")
