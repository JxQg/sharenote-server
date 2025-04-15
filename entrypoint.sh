#!/bin/sh
set -e

# 创建必要的目录（如果还不存在）
mkdir -p /sharenote-server/logs
mkdir -p /sharenote-server/static

# 检查是否有必要的配置文件
if [ ! -f "/sharenote-server/config/settings.toml" ]; then
    echo "错误: 未找到必要的配置文件 settings.toml"
    exit 1
fi

echo "Starting sharenote server..."
exec "$@"
