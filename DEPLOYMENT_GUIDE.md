# 扩展Web系统 - Docker部署指南

## 🎯 快速部署

### 前提条件
- ✅ Docker Desktop 已安装
- ✅ Docker Compose 已安装
- ✅ Git 已安装

### 一键部署步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd extensions-web
```

2. **配置环境变量**
```bash
# 复制环境变量模板
copy .env.example .env

# 编辑 .env 文件，修改以下重要配置：
# SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
# VITE_API_BASE_URL=http://your-domain.com:8000
# VITE_WS_URL=ws://your-domain.com:8000
```

3. **部署应用**

#### Windows 用户
```powershell
# 生产环境部署
powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 prod -Build

# 开发环境部署
powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1 dev
```

#### Linux/macOS 用户
```bash
# 给脚本执行权限
chmod +x scripts/deploy.sh

# 生产环境部署
./scripts/deploy.sh prod --build

# 开发环境部署
./scripts/deploy.sh dev
```

4. **访问应用**
- 🌐 **前端**: http://localhost
- 🔧 **后端API**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs

## 📁 Docker文件说明

### 核心文件
- `Dockerfile.backend` - 后端Python应用容器
- `Dockerfile.frontend` - 前端Nginx容器
- `docker-compose.prod.yml` - 生产环境配置
- `docker-compose.dev.yml` - 开发环境配置

### 环境变量处理

#### 前端环境变量
前端使用Vite构建，环境变量在构建时注入：

```dockerfile
# 构建参数
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000

# 构建时环境变量
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_URL=$VITE_WS_URL
```

#### 后端环境变量
后端通过Docker Compose的environment配置：

```yaml
environment:
  - HOST=0.0.0.0
  - PORT=8000
  - SECRET_KEY=${SECRET_KEY}
  - DATABASE_URL=${DATABASE_URL}
  - EXT_DB_TYPE=${EXT_DB_TYPE}
```

## 🗄️ 数据库配置

### SQLite (默认)
```bash
EXT_DB_TYPE=sqlite
EXT_DB_DIR=/app/data/db
EXT_DB_FILE=app.db
```

### MySQL
```bash
EXT_DB_TYPE=mysql
EXT_DB_HOST=mysql
EXT_DB_PORT=3306
EXT_DB_NAME=extensions
EXT_DB_USER=root
EXT_DB_PASSWORD=password
```

### PostgreSQL
```bash
EXT_DB_TYPE=postgresql
EXT_DB_HOST=postgres
EXT_DB_PORT=5432
EXT_DB_NAME=extensions
EXT_DB_USER=postgres
EXT_DB_PASSWORD=password
```

## 🐳 服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   FastAPI       │    │   Redis         │
│   (前端)        │────│   (后端)        │────│   (缓存)        │
│   Port: 80      │    │   Port: 8000    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📂 数据持久化

Docker数据目录映射：
```
docker-data/
├── data/          # 应用数据
├── logs/          # 日志文件
├── extensions/    # 扩展脚本
├── uploads/       # 上传文件
├── db/           # 数据库文件
├── redis/        # Redis数据
└── ssl/          # SSL证书
```

## 🔧 常用命令

### 查看服务状态
```bash
# Windows
powershell -File scripts\deploy.ps1 status

# Linux/macOS
./scripts/deploy.sh status
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs backend

# 实时查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 重启服务
```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend
```

### 停止服务
```bash
# Windows
powershell -File scripts\deploy.ps1 stop

# Linux/macOS
./scripts/deploy.sh stop

# 手动停止
docker-compose -f docker-compose.prod.yml down
```

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并部署
# Windows
powershell -File scripts\deploy.ps1 prod -Build

# Linux/macOS
./scripts/deploy.sh prod --build
```

## 🔍 故障排除

### 1. 端口冲突
```bash
# 检查端口占用
netstat -ano | findstr :80
netstat -ano | findstr :8000

# 修改端口映射
# 编辑 docker-compose.prod.yml
ports:
  - "8080:80"  # 将80端口改为8080
```

### 2. 权限问题
```bash
# Windows (以管理员身份运行)
# Linux/macOS
sudo chown -R $USER:$USER docker-data/
```

### 3. 内存不足
```bash
# 清理Docker资源
docker system prune -a

# 查看资源使用
docker stats
```

### 4. 网络问题
```bash
# 重新创建网络
docker-compose down
docker-compose up -d
```

## 🚀 生产环境优化

### 1. SSL/HTTPS配置
将SSL证书放在 `docker-data/ssl/` 目录下，并修改nginx配置。

### 2. 环境变量安全
- 修改默认的 `SECRET_KEY`
- 设置强密码
- 使用环境变量而不是硬编码

### 3. 监控和日志
```bash
# 设置日志轮转
# 在docker-compose.yml中添加：
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 4. 备份策略
```bash
# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz docker-data/

# 备份数据库
docker exec extensions-web-backend sqlite3 /app/data/database.sqlite ".backup /app/data/backup.db"
```

## 📞 技术支持

如果遇到问题：

1. 📖 查看 [详细部署文档](docs/DOCKER_DEPLOYMENT.md)
2. 🔍 检查日志文件
3. 🐛 提交Issue到GitHub
4. 💬 联系技术支持

---

⚠️ **重要提醒**: 生产环境部署前，请务必修改 `.env` 文件中的默认密码和密钥配置！
