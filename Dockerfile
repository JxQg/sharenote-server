FROM python:3.11-slim-bullseye as builder

WORKDIR /build

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    wget && \
    rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用缓存
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bullseye
WORKDIR /sharenote-server

# 创建非root用户并设置权限
RUN adduser --system --group --uid 1001 sharenote && \
    mkdir -p /sharenote-server/static /sharenote-server/logs /sharenote-server/config && \
    chown -R sharenote:sharenote /sharenote-server && \
    chmod -R 755 /sharenote-server

# 从构建阶段复制依赖
COPY --from=builder /root/.local /home/sharenote/.local
COPY --chown=sharenote:sharenote . .

# 设置环境变量
ENV PATH="/home/sharenote/.local/bin:${PATH}" \
    PYTHONPATH="/sharenote-server" \
    PYTHONUNBUFFERED=1 \
    PORT=8086

# 安全配置
RUN chmod 644 /sharenote-server/config/*.* && \
    chmod 755 /sharenote-server/entrypoint.sh

# 切换到非root用户
USER sharenote

# 添加健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT}/ || exit 1

EXPOSE ${PORT}

ENTRYPOINT ["/sharenote-server/entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:flask_app"]