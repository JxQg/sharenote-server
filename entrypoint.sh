#!/bin/sh
set -e

# 创建必要的目录
mkdir -p /sharenote-server/logs
mkdir -p /sharenote-server/static
mkdir -p /sharenote-server/config

# 确保目录权限正确
chown -R sharenote:sharenote /sharenote-server/logs
chown -R sharenote:sharenote /sharenote-server/static

# 如果配置目录为空，复制默认配置
if [ -z "$(ls -A /sharenote-server/config 2>/dev/null)" ]; then
    echo "初始化配置文件..."
    cp -R /defaults/config/* /sharenote-server/config/ 2>/dev/null || true
fi

# 等待数据库就绪（如果需要的话）
# while ! nc -z db 5432; do
#     echo "等待数据库就绪..."
#     sleep 1
# done

echo "Starting sharenote server..."
exec "$@"
