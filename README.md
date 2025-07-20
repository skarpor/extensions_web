# 扩展Web系统

一个基于 FastAPI 和 Vue.js 的现代化扩展管理和数据查询系统，支持Docker一键部署。

## ✨ 功能特性

- 🔐 **用户认证和权限管理** - JWT认证，角色权限控制
- 📊 **数据查询和可视化** - 多数据源支持，图表展示
- 🔌 **扩展系统** - 动态加载Python扩展，热插拔
- 📁 **文件管理** - 文件上传、下载、预览
- 💬 **实时聊天系统** - WebSocket通信，群聊私聊
- 🎨 **现代化UI** - 响应式设计，暗色主题
- 🐳 **Docker部署** - 一键部署，容器化管理
- 🔧 **系统管理** - 进程管理器，配置管理

## 🏗️ 技术栈

### 后端
- **FastAPI** - 现代、快速的 Web 框架
- **SQLAlchemy** - ORM 数据库工具
- **Redis** - 缓存和会话存储
- **WebSocket** - 实时通信
- **Pydantic** - 数据验证

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - Vue 3 组件库
- **Vite** - 现代化构建工具
- **Pinia** - 状态管理
- **Axios** - HTTP 客户端

### 部署
- **Docker** - 容器化部署
- **Nginx** - 反向代理和静态文件服务
- **Docker Compose** - 多容器编排

## 🚀 快速开始

### 方式一：Docker 一键部署 (推荐)

1. **克隆项目**
```bash
git clone <repository-url>
cd extensions-web
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，修改SECRET_KEY等重要配置
nano .env
```

3. **一键部署**
```bash
# 给脚本执行权限
chmod +x scripts/deploy.sh

# 启动生产环境
./scripts/deploy.sh prod

# 或启动开发环境
./scripts/deploy.sh dev
```

4. **访问应用**
- 🌐 **前端**: http://localhost
- 🔧 **后端API**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs
- 🗄️ **数据库管理**: http://localhost:8080 (开发环境)

### 方式二：本地开发

#### 后端设置
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动后端
python main.py
```

#### 前端设置
```bash
cd fr
npm install
npm run dev
```

## 📁 项目结构

```
extensions-web/
├── 📂 api/                    # 后端API
│   ├── 📂 v1/                # API v1版本
│   └── 📂 models/            # 数据模型
├── 📂 core/                  # 核心功能
├── 📂 fr/                    # 前端代码
│   ├── 📂 src/              # 源代码
│   └── 📂 public/           # 静态资源
├── 📂 docker-data/           # Docker数据目录
├── 📂 docker-config/         # Docker配置
├── 📂 docs/                  # 文档
├── 📂 scripts/              # 部署脚本
├── 🐳 Dockerfile.backend     # 后端Dockerfile
├── 🐳 Dockerfile.frontend    # 前端Dockerfile
├── 🐳 docker-compose.yml     # 完整部署配置
├── 🐳 docker-compose.prod.yml # 生产环境配置
└── 🐳 docker-compose.dev.yml  # 开发环境配置
```

## ⚙️ 环境变量配置

### 🔑 必须配置的变量

```bash
# 安全密钥（生产环境必须修改！）
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars

# 前端配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///app/data/database.sqlite

# 扩展数据库配置
EXT_DB_TYPE=sqlite
EXT_DB_DIR=/app/data/db
EXT_DB_FILE=app.db
```

### 🗄️ 数据库支持

系统支持多种数据库：

#### SQLite (默认)
```bash
EXT_DB_TYPE=sqlite
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

## 🔌 扩展系统

系统支持动态加载Python扩展：

1. 在 `data/extensions/` 目录下创建扩展文件
2. 扩展文件需要包含 `query` 函数
3. 系统自动加载和注册扩展

**扩展示例**：
```python
def query(params):
    """扩展查询函数"""
    return {
        "success": True,
        "data": "Hello from extension",
        "message": "扩展执行成功"
    }
```

## 🐳 Docker部署详解

### 开发环境
- 代码热重载
- 详细日志输出
- 开发工具集成

```bash
./scripts/deploy.sh dev
```

### 生产环境
- 优化的镜像大小
- Nginx反向代理
- 安全配置优化

```bash
./scripts/deploy.sh prod --build
```

### 服务管理
```bash
# 查看状态
./scripts/deploy.sh status

# 停止服务
./scripts/deploy.sh stop

# 清理资源
./scripts/deploy.sh cleanup
```

## 📚 文档

- 📖 **[Docker部署文档](docs/DOCKER_DEPLOYMENT.md)** - 详细的Docker部署指南
- 🔧 **[API文档](http://localhost:8000/docs)** - 在线API文档
- 🎯 **[扩展开发指南](docs/EXTENSIONS.md)** - 扩展开发文档

## 🔍 故障排除

### 常见问题

1. **端口冲突**
```bash
# 检查端口占用
netstat -tulpn | grep :80
# 修改docker-compose.yml中的端口映射
```

2. **权限问题**
```bash
# 修复目录权限
sudo chown -R $USER:$USER docker-data/
```

3. **内存不足**
```bash
# 清理Docker资源
docker system prune -a
```

### 调试命令
```bash
# 查看日志
docker-compose logs -f

# 进入容器
docker exec -it extensions-web-backend bash

# 查看资源使用
docker stats
```

## 🚀 性能优化

- ✅ Nginx Gzip压缩
- ✅ 静态文件缓存
- ✅ Redis缓存
- ✅ 数据库连接池
- ✅ 前端代码分割

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请参考 [LICENSE](LICENSE) 文件。

## 💬 支持

如果您遇到问题或需要帮助：

1. 📖 查看 [部署文档](docs/DOCKER_DEPLOYMENT.md)
2. 🔍 搜索 [Issues](../../issues)
3. 💡 创建新的 Issue
4. 📧 联系技术支持

---

⚠️ **重要提醒**: 生产环境部署前，请务必修改 `.env` 文件中的默认密码和密钥配置！
