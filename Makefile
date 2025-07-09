# Data Query System 2.0 Makefile

.PHONY: help install dev prod build start stop restart logs clean backup restore

# 默认目标
help:
	@echo "Data Query System 2.0 - 可用命令:"
	@echo ""
	@echo "开发环境:"
	@echo "  make dev          启动开发环境"
	@echo "  make dev-logs     查看开发环境日志"
	@echo "  make dev-stop     停止开发环境"
	@echo ""
	@echo "生产环境:"
	@echo "  make prod         启动生产环境"
	@echo "  make start        启动生产环境 (别名)"
	@echo "  make stop         停止所有服务"
	@echo "  make restart      重启服务"
	@echo "  make logs         查看生产环境日志"
	@echo ""
	@echo "构建和部署:"
	@echo "  make build        构建所有镜像"
	@echo "  make build-dev    构建开发环境镜像"
	@echo "  make build-prod   构建生产环境镜像"
	@echo ""
	@echo "数据管理:"
	@echo "  make backup       创建完整备份"
	@echo "  make backup-quick 创建快速备份"
	@echo "  make restore      恢复备份"
	@echo "  make backup-list  列出所有备份"
	@echo ""
	@echo "维护:"
	@echo "  make clean        清理所有容器和镜像"
	@echo "  make clean-data   清理数据 (危险操作)"
	@echo "  make status       查看服务状态"
	@echo "  make health       检查服务健康状态"
	@echo ""
	@echo "初始化:"
	@echo "  make install      初始化项目环境"
	@echo "  make setup        设置环境配置"
	@echo ""

# 初始化和设置
install: setup
	@echo "正在初始化项目环境..."
	@chmod +x scripts/*.sh
	@./scripts/start.sh --help > /dev/null 2>&1 || echo "脚本权限设置完成"
	@echo "项目环境初始化完成!"

setup:
	@echo "设置环境配置..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "已创建 .env 文件，请根据需要修改配置"; \
	else \
		echo ".env 文件已存在"; \
	fi
	@mkdir -p docker-data/{data,logs,extensions,uploads,db,static,ssl,redis,postgres,grafana,prometheus}
	@mkdir -p docker-data/data/{extensions,file,db,logs}
	@echo "目录结构创建完成"

# 开发环境
dev: setup
	@echo "启动开发环境..."
	@./scripts/start.sh dev

dev-logs:
	@docker-compose -f docker-compose.dev.yml logs -f

dev-stop:
	@echo "停止开发环境..."
	@docker-compose -f docker-compose.dev.yml down

# 生产环境
prod: setup
	@echo "启动生产环境..."
	@./scripts/start.sh prod

start: prod

stop:
	@echo "停止所有服务..."
	@./scripts/stop.sh

restart:
	@echo "重启服务..."
	@./scripts/stop.sh
	@sleep 2
	@./scripts/start.sh prod

logs:
	@docker-compose logs -f

# 构建
build: build-prod

build-dev:
	@echo "构建开发环境镜像..."
	@docker-compose -f docker-compose.dev.yml build

build-prod:
	@echo "构建生产环境镜像..."
	@docker-compose build

# 数据管理
backup:
	@echo "创建完整备份..."
	@./scripts/backup.sh full

backup-quick:
	@echo "创建快速备份..."
	@./scripts/backup.sh quick

backup-list:
	@echo "列出所有备份..."
	@./scripts/backup.sh list

restore:
	@echo "恢复备份..."
	@./scripts/restore.sh

# 维护
clean:
	@echo "清理容器和镜像..."
	@./scripts/stop.sh
	@docker system prune -f
	@echo "清理完成"

clean-data:
	@echo "警告: 这将删除所有数据!"
	@read -p "确定要继续吗? (y/N): " confirm && [ "$$confirm" = "y" ]
	@./scripts/stop.sh
	@sudo rm -rf docker-data
	@docker volume prune -f
	@echo "数据清理完成"

status:
	@echo "服务状态:"
	@docker-compose ps

health:
	@echo "检查服务健康状态..."
	@echo "前端服务:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "前端服务不可用"
	@echo ""
	@echo "后端服务:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "后端服务不可用"
	@echo ""
	@echo "数据库服务:"
	@docker-compose exec postgres pg_isready -U postgres || echo "数据库服务不可用"

# 快捷命令
up: start
down: stop
ps: status

# 开发相关
shell-backend:
	@docker-compose exec backend bash

shell-frontend:
	@docker-compose exec frontend sh

shell-db:
	@docker-compose exec postgres psql -U postgres dataquery

# 日志查看
logs-backend:
	@docker-compose logs -f backend

logs-frontend:
	@docker-compose logs -f frontend

logs-db:
	@docker-compose logs -f postgres

# 更新和重建
update: stop
	@git pull
	@docker-compose build --no-cache
	@make start

# 测试
test:
	@echo "运行测试..."
	@docker-compose exec backend python -m pytest tests/ || echo "请确保测试目录存在"

# 数据库操作
db-migrate:
	@echo "运行数据库迁移..."
	@docker-compose exec backend python -c "from database import init_db; init_db()"

db-reset:
	@echo "重置数据库..."
	@read -p "这将删除所有数据，确定继续吗? (y/N): " confirm && [ "$$confirm" = "y" ]
	@docker-compose exec postgres dropdb -U postgres dataquery || true
	@docker-compose exec postgres createdb -U postgres dataquery
	@make db-migrate

# 监控
monitor:
	@echo "打开监控面板..."
	@echo "Grafana: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"
	@echo "Adminer: http://localhost:8080"

# SSL 证书
ssl-generate:
	@echo "生成自签名 SSL 证书..."
	@mkdir -p docker-data/ssl
	@openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout docker-data/ssl/key.pem \
		-out docker-data/ssl/cert.pem \
		-subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
	@echo "SSL 证书生成完成"
