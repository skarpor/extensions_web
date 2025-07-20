# 扩展Web系统 - Docker部署文档

## 📋 目录

- [系统架构](#系统架构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [环境变量配置](#环境变量配置)
- [部署方式](#部署方式)
- [服务管理](#服务管理)
- [故障排除](#故障排除)
- [性能优化](#性能优化)

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   FastAPI       │    │   Redis         │
│   (前端服务)     │────│   (后端API)     │────│   (缓存)        │
│   Port: 80/443  │    │   Port: 8000    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   SQLite/       │
                    │   PostgreSQL    │
                    │   (数据库)      │
                    └─────────────────┘
```

## 🔧 环境要求

### 系统要求
- **操作系统**: Linux/macOS/Windows
- **内存**: 最低 2GB，推荐 4GB+
- **磁盘**: 最低 10GB 可用空间
- **网络**: 需要访问互联网下载镜像

### 软件要求
- **Docker**: 20.10.0+
- **Docker Compose**: 2.0.0+
- **Git**: 用于克隆代码

### 安装Docker

#### Ubuntu/Debian
```bash
# 更新包索引
sudo apt update

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo apt install docker-compose-plugin

# 将用户添加到docker组
sudo usermod -aG docker $USER
```

#### CentOS/RHEL
```bash
# 安装Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### Windows/macOS
下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd extensions-web
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（重要！）
nano .env
```

### 3. 一键部署

#### 开发环境
```bash
# 给脚本执行权限
chmod +x scripts/deploy.sh

# 启动开发环境
./scripts/deploy.sh dev
```

#### 生产环境
```bash
# 启动生产环境
./scripts/deploy.sh prod --build
```

### 4. 访问应用
- **前端**: http://localhost (生产) 或 http://localhost:5173 (开发)
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据库管理**: http://localhost:8080 (开发环境)

## ⚙️ 环境变量配置

### 必须配置的变量

```bash
# 安全密钥（生产环境必须修改！）
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars

# 前端API地址
VITE_API_BASE_URL=http://your-domain.com:8000
VITE_WS_URL=ws://your-domain.com:8000

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///app/data/database.sqlite

# Redis密码
REDIS_PASSWORD=your-redis-password
```

### 扩展数据库配置

#### SQLite (默认)
```bash
EXT_DB_TYPE=sqlite
EXT_DB_DIR=/app/data/db
EXT_DB_FILE=app.db
```

#### MySQL
```bash
EXT_DB_TYPE=mysql
EXT_DB_HOST=mysql
EXT_DB_PORT=3306
EXT_DB_NAME=extensions
EXT_DB_USER=root
EXT_DB_PASSWORD=password
```

#### PostgreSQL
```bash
EXT_DB_TYPE=postgresql
EXT_DB_HOST=postgres
EXT_DB_PORT=5432
EXT_DB_NAME=extensions
EXT_DB_USER=postgres
EXT_DB_PASSWORD=password
```

### 前端环境变量处理

前端使用Vite构建，环境变量在构建时被注入：

```dockerfile
# Dockerfile.frontend 中的构建参数
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000

# 设置构建时环境变量
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_URL=$VITE_WS_URL
```

## 🐳 部署方式

### 开发环境部署

特点：
- 代码热重载
- 详细日志输出
- 开发工具集成
- 数据库管理界面

```bash
# 启动开发环境
./scripts/deploy.sh dev

# 重新构建并启动
./scripts/deploy.sh dev --build

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 生产环境部署

特点：
- 优化的镜像大小
- Nginx反向代理
- 安全配置
- 性能优化

```bash
# 启动生产环境
./scripts/deploy.sh prod

# 重新构建并启动
./scripts/deploy.sh prod --build

# 后台运行
docker-compose -f docker-compose.prod.yml up -d
```

### 自定义部署

如果需要自定义配置，可以直接使用docker-compose：

```bash
# 使用自定义配置文件
docker-compose -f docker-compose.custom.yml up -d

# 只启动特定服务
docker-compose -f docker-compose.prod.yml up -d backend redis

# 扩展服务实例
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

## 🔧 服务管理

### 查看服务状态
```bash
# 查看所有服务
./scripts/deploy.sh status

# 查看特定环境
docker-compose -f docker-compose.prod.yml ps
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
# 停止所有服务
./scripts/deploy.sh stop

# 停止并删除容器
docker-compose -f docker-compose.prod.yml down

# 停止并删除容器和卷
docker-compose -f docker-compose.prod.yml down -v
```

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并部署
./scripts/deploy.sh prod --build

# 或者手动操作
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## 📁 目录结构

```
extensions-web/
├── docker-data/              # Docker数据目录
│   ├── data/                 # 应用数据
│   ├── logs/                 # 日志文件
│   ├── extensions/           # 扩展脚本
│   ├── uploads/              # 上传文件
│   ├── db/                   # 数据库文件
│   ├── redis/                # Redis数据
│   └── ssl/                  # SSL证书
├── docker-config/            # Docker配置
│   ├── nginx.conf           # Nginx主配置
│   ├── default.conf         # Nginx站点配置
│   └── init.sql             # 数据库初始化
├── fr/                       # 前端代码
├── scripts/                  # 部署脚本
├── Dockerfile.backend        # 后端Dockerfile
├── Dockerfile.frontend       # 前端Dockerfile
├── docker-compose.yml        # 生产环境配置
├── docker-compose.dev.yml    # 开发环境配置
├── docker-compose.prod.yml   # 生产环境配置
└── .env.example             # 环境变量模板
```

## 🔍 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :80
netstat -tulpn | grep :8000

# 修改docker-compose.yml中的端口映射
ports:
  - "8080:80"  # 将80端口改为8080
```

#### 2. 权限问题
```bash
# 修复目录权限
sudo chown -R $USER:$USER docker-data/

# 给脚本执行权限
chmod +x scripts/deploy.sh
```

#### 3. 内存不足
```bash
# 检查内存使用
docker stats

# 清理未使用的资源
docker system prune -a
```

#### 4. 网络问题
```bash
# 检查Docker网络
docker network ls

# 重新创建网络
docker-compose down
docker-compose up -d
```

### 调试命令

```bash
# 进入容器调试
docker exec -it extensions-web-backend bash
docker exec -it extensions-web-frontend sh

# 查看容器详细信息
docker inspect extensions-web-backend

# 查看镜像构建历史
docker history extensions-web-backend

# 检查健康状态
docker-compose ps
```

## 🚀 性能优化

### 生产环境优化

1. **启用Gzip压缩** (已在nginx.conf中配置)
2. **设置缓存策略** (已在default.conf中配置)
3. **优化数据库连接池**
4. **使用Redis缓存**
5. **配置SSL/TLS**

### 监控和日志

```bash
# 查看资源使用情况
docker stats

# 设置日志轮转
# 在docker-compose.yml中添加：
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 备份策略

```bash
# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz docker-data/

# 备份数据库
docker exec extensions-web-backend sqlite3 /app/data/database.sqlite ".backup /app/data/backup.db"
```

## 📞 支持

如果遇到问题，请：

1. 查看日志文件
2. 检查环境变量配置
3. 确认Docker和Docker Compose版本
4. 查看GitHub Issues
5. 联系技术支持

---

**注意**: 生产环境部署前，请务必修改默认密码和密钥！
