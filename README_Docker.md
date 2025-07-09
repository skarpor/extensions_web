# Data Query System 2.0 - Docker 快速部署

## 🚀 一键部署

### 生产环境
```bash
# 1. 克隆项目
git clone <repository-url>
cd extensions_web

# 2. 初始化环境
make install

# 3. 启动服务
make prod
```

### 开发环境
```bash
# 启动开发环境
make dev
```

## 📋 访问地址

### 生产环境
- **应用首页**: http://localhost
- **API 文档**: http://localhost/docs
- **数据库管理**: http://localhost:8080
- **监控面板**: http://localhost:3000

### 开发环境
- **前端开发**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 🔧 常用命令

```bash
# 服务管理
make start          # 启动生产环境
make stop           # 停止所有服务
make restart        # 重启服务
make logs           # 查看日志
make status         # 查看服务状态

# 开发环境
make dev            # 启动开发环境
make dev-logs       # 查看开发环境日志
make dev-stop       # 停止开发环境

# 数据管理
make backup         # 创建完整备份
make backup-quick   # 创建快速备份
make restore        # 恢复备份
make backup-list    # 列出所有备份

# 构建
make build          # 构建生产镜像
make build-dev      # 构建开发镜像

# 维护
make clean          # 清理容器和镜像
make health         # 健康检查
make monitor        # 打开监控面板
```

## ⚙️ 配置

### 环境变量 (.env)
```bash
# 应用配置
SECRET_KEY=your-secret-key-change-in-production
ALLOW_REGISTER=true

# 数据库配置
POSTGRES_PASSWORD=your-strong-password
REDIS_PASSWORD=your-redis-password

# 监控配置
GRAFANA_PASSWORD=your-grafana-password
```

### 目录结构
```
docker-data/
├── data/           # 应用数据
├── extensions/     # 扩展脚本
├── uploads/        # 用户文件
├── postgres/       # PostgreSQL 数据
├── redis/          # Redis 数据
└── ssl/           # SSL 证书
```

## 🛡️ 安全配置

### 生产环境必做
1. **修改默认密码**:
   ```bash
   # 编辑 .env 文件
   SECRET_KEY=your-super-secret-key
   POSTGRES_PASSWORD=your-strong-password
   REDIS_PASSWORD=your-redis-password
   GRAFANA_PASSWORD=your-grafana-password
   ```

2. **启用 HTTPS**:
   ```bash
   # 生成自签名证书 (测试用)
   make ssl-generate
   
   # 或使用真实证书
   cp your-cert.pem docker-data/ssl/cert.pem
   cp your-key.pem docker-data/ssl/key.pem
   ```

3. **配置防火墙**:
   ```bash
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw deny 8000  # 不直接暴露后端
   ```

## 📊 监控

### Grafana 仪表板
1. 访问: http://localhost:3000
2. 登录: admin / ${GRAFANA_PASSWORD}
3. 添加数据源: http://prometheus:9090

### Prometheus 指标
- 访问: http://localhost:9090
- 查看应用指标和系统监控

## 🗄️ 数据备份

### 自动备份
```bash
# 设置定时备份
crontab -e

# 添加定时任务 (每天凌晨2点备份)
0 2 * * * cd /path/to/project && make backup-quick
```

### 手动备份
```bash
# 完整备份
make backup

# 快速备份 (仅数据和配置)
make backup-quick

# 恢复备份
make restore
```

## 🐛 故障排除

### 常见问题

**1. 端口被占用**
```bash
# 检查端口使用
sudo netstat -tulpn | grep :80

# 修改端口映射
# 编辑 docker-compose.yml 中的 ports 配置
```

**2. 内存不足**
```bash
# 检查内存使用
free -h

# 增加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**3. 磁盘空间不足**
```bash
# 清理 Docker 资源
make clean

# 清理系统日志
sudo journalctl --vacuum-time=7d
```

**4. 服务启动失败**
```bash
# 查看详细日志
make logs

# 检查特定服务
docker-compose logs backend
docker-compose logs postgres
```

### 健康检查
```bash
# 检查所有服务状态
make health

# 检查特定服务
curl http://localhost/health
curl http://localhost:8000/health
```

## 📈 性能优化

### 数据库优化
```bash
# 连接到数据库
make shell-db

# 查看连接数
SELECT count(*) FROM pg_stat_activity;

# 查看慢查询
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### 应用优化
```bash
# 增加后端实例数
# 编辑 docker-compose.yml
backend:
  deploy:
    replicas: 3
```

## 📞 获取帮助

### 查看帮助
```bash
make help              # 查看所有可用命令
./scripts/start.sh help # 查看启动脚本帮助
```

### 技术支持
- **文档**: [Docker部署指南.md](./Docker部署指南.md)
- **GitHub**: 提交 Issue 报告问题
- **邮件**: support@example.com

---

## 📋 部署检查清单

- [ ] 安装 Docker 和 Docker Compose
- [ ] 克隆项目代码
- [ ] 复制并配置 .env 文件
- [ ] 修改默认密码
- [ ] 运行 `make install`
- [ ] 启动服务 `make prod`
- [ ] 访问应用验证功能
- [ ] 配置备份策略
- [ ] 设置监控告警
- [ ] 配置 SSL 证书 (生产环境)
- [ ] 配置防火墙规则

**部署完成后，请访问 http://localhost 开始使用系统！**

---

*快速部署指南最后更新: 2025-07-09*
