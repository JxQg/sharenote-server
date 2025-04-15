# Share Note Server 说明文档

## 项目介绍
Share Note Server 是一个为 Obsidian Share Note 插件提供服务的后端应用。它允许用户快速分享 Obsidian 笔记,并保持与原始笔记完全相同的主题样式和排版。

### 主要功能
- 支持 Markdown 笔记分享
- 完整保留 Obsidian 主题样式
- 支持目录树结构展示
- 支持文档内目录导航
- 支持响应式布局
- 支持明暗主题切换
- 支持搜索功能
- 支持静态资源缓存
- 内置健康检查和监控

## 部署说明

### Docker 部署 (推荐)

1. 创建配置文件
```toml
[server]
debug = false
host = "0.0.0.0"
port = 8086
server_url = "http://your-domain:8086"  # 修改为你的域名
disable_file_watch = false

[security]
secret_api_key = "your-secret-key-here"  # 修改为你的密钥
max_upload_size_mb = 16

[files]
allowed_filetypes = ["png", "jpg", "jpeg", "gif", "pdf", "css", "html", "webp", "svg", "ttf", "otf", "woff", "woff2"]
```

2. 使用 docker-compose 部署
```yaml
version: '3.8'

services:
  sharenote:
    container_name: sharenote
    image: jxqg597/sharenote-server:1.0.0
    ports:
      - "8086:8086"
    volumes:
      - ./static:/sharenote-server/static:ro
      - ./config:/sharenote-server/config:ro
      - sharenote_logs:/sharenote-server/logs
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped

volumes:
  sharenote_logs:
```

3. 启动服务
```bash
docker-compose up -d
```

## Obsidian 配置说明

1. 在 Obsidian 中安装 Share Note 插件
2. 打开插件设置
3. 设置 Server URL 为你的服务器地址(如 http://your-domain:8086)
4. 设置 API Key 为你在 settings.toml 中配置的 secret_api_key
5. 完成配置后即可通过命令面板使用 "Share Note" 命令分享笔记

## 目录结构说明
```
sharenote-server/
├── app/                    # 应用主目录
│   ├── config/            # 配置相关代码
│   ├── routes/            # 路由定义
│   ├── services/          # 业务逻辑服务
│   └── utils/             # 工具函数
├── static/                # 静态资源目录
│   ├── css/              # 样式文件
│   └── js/               # JavaScript文件
├── template/             # HTML模板
├── config/               # 配置文件目录
│   └── settings.toml     # 主配置文件
├── logs/                 # 日志目录
├── docker-compose.yml    # Docker编排文件
└── requirements.txt      # Python依赖
```

## 环境要求
- Python 3.11+
- Docker (如使用容器部署)
- 2GB RAM (推荐)
- 1 CPU Core (最低)

## 注意事项
1. 首次部署时请修改配置文件中的密钥
2. 确保服务器防火墙允许对应端口访问
3. 建议在生产环境中使用反向代理(如 Nginx)
4. 定期备份 static 目录下的文件
5. 监控 logs 目录的磁盘占用情况

## 许可证
该项目基于 MIT 许可证开源。