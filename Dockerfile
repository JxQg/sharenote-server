FROM python:3.11-alpine

WORKDIR /sharenote-server

# 创建非root用户和必要目录
RUN addgroup -S sharenote && \
    adduser -S -G sharenote -u 1001 sharenote && \
    mkdir -p static logs config && \
    chown -R sharenote:sharenote /sharenote-server

# 安装依赖（优先利用 Docker 缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local/lib -name "*.pyc" -delete && \
    find /usr/local/lib -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 复制应用代码
COPY --chown=sharenote:sharenote . .

ENV PYTHONPATH="/sharenote-server" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8086

RUN chmod 644 config/*.* && chmod 755 entrypoint.sh

USER sharenote

# 健康检查使用 Python stdlib，无需额外工具
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT','8086') + '/api/system/health')" || exit 1

EXPOSE ${PORT}

ENTRYPOINT ["/sharenote-server/entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:flask_app"]
