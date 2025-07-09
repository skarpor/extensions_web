# Data Query System 2.0 - Docker 部署指南

## 📋 概述

本指南提供了 Data Query System 2.0 的完整 Docker 部署方案，包括开发环境和生产环境的配置。

## 🏗️ 架构概览

### 服务组件

| 服务 | 容器名 | 端口 | 描述 |
|------|--------|------|------|
| Frontend | data-query-frontend | 80, 443 | Nginx + Vue3 前端 |
| Backend | data-query-backend | 8000 | FastAPI 后端服务 |
| PostgreSQL | data-query-postgres | 5432 | 主数据库 |
| Redis | data-query-redis | 6379 | 缓存和会话存储 |
| Adminer | data-query-adminer | 8080 | 数据库管理工具 |
| Prometheus | data-query-prometheus | 9090 | 监控数据收集 |
| Grafana | data-query-grafana | 3000 | 监控面板 |

### 目录映射

```
docker-data/
├── data/           # 应用数据 (SQLite, 日志等)
├── extensions/     # 扩展脚本
├── uploads/        # 用户上传文件
├── db/            # 外部数据库文件
├── static/        # 静态文件
├── ssl/           # SSL 证书
├── redis/         # Redis 数据
├── postgres/      # PostgreSQL 数据
├── grafana/       # Grafana 配置
└── prometheus/    # Prometheus 数据
```

## 🚀 快速开始

### 1. 环境准备

**系统要求:**
- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB RAM
- 至少 10GB 可用磁盘空间

**安装 Docker (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd extensions_web
```

### 3. 配置环境

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

**重要配置项:**
```bash
# 修改默认密钥 (生产环境必须)
SECRET_KEY=your-super-secret-key-change-in-production

# 数据库密码
POSTGRES_PASSWORD=your-strong-password
REDIS_PASSWORD=your-redis-password

# 监控密码
GRAFANA_PASSWORD=your-grafana-password
```

### 4. 启动服务

**生产环境:**
```bash
# 使用启动脚本 (推荐)
chmod +x scripts/*.sh
./scripts/start.sh prod

# 或直接使用 Docker Compose
docker-compose up -d
```

**开发环境:**
```bash
./scripts/start.sh dev

# 或
docker-compose -f docker-compose.dev.yml up -d
```

### 5. 访问应用

**生产环境:**
- 应用首页: http://localhost
- API 文档: http://localhost/docs
- 数据库管理: http://localhost:8080
- 监控面板: http://localhost:3000

**开发环境:**
- 前端开发服务器: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 🔧 详细配置

### 环境变量配置

创建 `.env` 文件并配置以下变量：

```bash
# 应用配置
SECRET_KEY=your-secret-key
ALLOW_REGISTER=true
APP_ENV=production

# 数据库配置
POSTGRES_DB=dataquery
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@postgres:5432/dataquery

# Redis 配置
REDIS_PASSWORD=redis123
REDIS_URL=redis://:redis123@redis:6379/0

# 安全配置
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost,http://localhost:3000

# 监控配置
GRAFANA_PASSWORD=admin123
```

### SSL/HTTPS 配置

1. **准备 SSL 证书:**
```bash
mkdir -p docker-data/ssl
# 将证书文件放入 docker-data/ssl/
# cert.pem - 证书文件
# key.pem - 私钥文件
```

2. **启用 HTTPS:**
编辑 `docker-config/default.conf`，取消注释 HTTPS 服务器配置块。

### 自定义 Nginx 配置

编辑 `docker-config/default.conf` 和 `docker-config/nginx.conf` 来自定义 Nginx 配置。

## 📊 监控配置

### Prometheus 配置

编辑 `docker-config/prometheus.yml` 来配置监控目标：

```yaml
scrape_configs:
  - job_name: 'data-query-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Grafana 仪表板

1. 访问 http://localhost:3000
2. 使用 admin / ${GRAFANA_PASSWORD} 登录
3. 添加 Prometheus 数据源: http://prometheus:9090
4. 导入预配置的仪表板

## 🗄️ 数据管理

### 数据备份

```bash
# 完整备份
./scripts/backup.sh full

# 快速备份 (仅数据和配置)
./scripts/backup.sh quick

# 仅备份数据库
./scripts/backup.sh db
```

### 数据恢复

```bash
# 列出可用备份
./scripts/restore.sh list

# 交互式恢复
./scripts/restore.sh full

# 使用指定备份文件
./scripts/restore.sh full backups/dataquery_backup_20231201_120000.tar.gz
```

### 数据库迁移

**从 SQLite 迁移到 PostgreSQL:**

1. 导出 SQLite 数据
2. 修改 `.env` 中的 `DATABASE_URL`
3. 重启服务
4. 导入数据到 PostgreSQL

## 🔧 运维操作

### 服务管理

```bash
# 启动服务
./scripts/start.sh prod

# 停止服务
./scripts/stop.sh

# 重启服务
./scripts/start.sh restart

# 查看日志
./scripts/start.sh logs

# 查看服务状态
docker-compose ps
```

### 扩容和性能优化

**增加后端实例:**
```yaml
# 在 docker-compose.yml 中修改
backend:
  deploy:
    replicas: 3
```

**数据库优化:**
```yaml
postgres:
  environment:
    - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    - POSTGRES_MAX_CONNECTIONS=200
```

### 日志管理

**查看实时日志:**
```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
```

**日志轮转配置:**
```yaml
# 在 docker-compose.yml 中添加
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🛡️ 安全配置

### 网络安全

1. **防火墙配置:**
```bash
# 仅开放必要端口
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8000  # 不直接暴露后端端口
```

2. **反向代理:**
使用 Nginx 作为反向代理，不直接暴露后端服务。

### 数据安全

1. **定期备份:**
```bash
# 设置定时备份
crontab -e
# 添加: 0 2 * * * /path/to/scripts/backup.sh quick
```

2. **敏感数据加密:**
- 使用强密码
- 定期轮换密钥
- 加密备份文件

## 🐛 故障排除

### 常见问题

**1. 容器启动失败**
```bash
# 查看详细错误
docker-compose logs backend

# 检查资源使用
docker stats
```

**2. 数据库连接失败**
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 查看数据库日志
docker-compose logs postgres
```

**3. 前端无法访问后端**
```bash
# 检查网络连接
docker-compose exec frontend ping backend

# 检查 Nginx 配置
docker-compose exec frontend nginx -t
```

### 性能问题

**1. 内存不足**
```bash
# 增加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**2. 磁盘空间不足**
```bash
# 清理 Docker 资源
docker system prune -a

# 清理日志
docker-compose exec backend find /app/logs -name "*.log" -mtime +7 -delete
```

## 📈 扩展部署

### 多节点部署

使用 Docker Swarm 或 Kubernetes 进行多节点部署：

**Docker Swarm:**
```bash
# 初始化 Swarm
docker swarm init

# 部署 Stack
docker stack deploy -c docker-compose.yml dataquery
```

### 云平台部署

**AWS ECS:**
- 使用 ECS Task Definition
- 配置 Application Load Balancer
- 使用 RDS 作为数据库

**Azure Container Instances:**
- 使用 Container Groups
- 配置 Azure Database for PostgreSQL

## 📞 技术支持

### 获取帮助

1. **查看日志:**
```bash
./scripts/start.sh logs
```

2. **健康检查:**
```bash
curl http://localhost/health
```

3. **性能监控:**
访问 Grafana 面板查看系统性能指标

### 联系支持

- GitHub Issues: 报告问题和建议
- 邮件支持: support@example.com
- 文档: 查看项目文档目录

---

*部署指南最后更新: 2025-07-09*
