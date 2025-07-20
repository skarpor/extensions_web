#!/bin/bash

# 扩展Web系统 - Docker部署脚本
# 使用方法: ./scripts/deploy.sh [dev|prod] [--build]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "扩展Web系统 - Docker部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [dev|prod] [--build]"
    echo ""
    echo "参数:"
    echo "  dev     启动开发环境"
    echo "  prod    启动生产环境"
    echo "  --build 强制重新构建镜像"
    echo ""
    echo "示例:"
    echo "  $0 dev          # 启动开发环境"
    echo "  $0 prod --build # 重新构建并启动生产环境"
    echo ""
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    log_info "Docker 环境检查通过"
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，从 .env.example 复制"
        cp .env.example .env
        log_warning "请编辑 .env 文件并设置正确的环境变量"
        log_warning "特别注意修改 SECRET_KEY 和数据库密码"
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    directories=(
        "docker-data/data"
        "docker-data/logs"
        "docker-data/extensions"
        "docker-data/uploads"
        "docker-data/db"
        "docker-data/redis"
        "docker-data/ssl"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    done
}

# 部署开发环境
deploy_dev() {
    log_info "部署开发环境..."
    
    local build_flag=""
    if [ "$1" = "--build" ]; then
        build_flag="--build"
        log_info "将重新构建镜像"
    fi
    
    docker-compose -f docker-compose.dev.yml up -d $build_flag
    
    log_success "开发环境启动成功!"
    log_info "前端地址: http://localhost:5173"
    log_info "后端地址: http://localhost:8000"
    log_info "API文档: http://localhost:8000/docs"
    log_info "数据库管理: http://localhost:8080"
}

# 部署生产环境
deploy_prod() {
    log_info "部署生产环境..."
    
    local build_flag=""
    if [ "$1" = "--build" ]; then
        build_flag="--build"
        log_info "将重新构建镜像"
    fi
    
    # 构建前端
    log_info "构建前端应用..."
    cd fr
    npm ci
    npm run build
    cd ..
    
    docker-compose -f docker-compose.prod.yml up -d $build_flag
    
    log_success "生产环境启动成功!"
    log_info "应用地址: http://localhost"
    log_info "后端API: http://localhost:8000"
    log_info "Redis: localhost:6379"
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    
    if [ -f "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml down
    fi
    
    if [ -f "docker-compose.prod.yml" ]; then
        docker-compose -f docker-compose.prod.yml down
    fi
    
    log_success "所有服务已停止"
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    # 停止服务
    stop_services
    
    # 删除未使用的镜像
    docker image prune -f
    
    # 删除未使用的卷
    docker volume prune -f
    
    log_success "清理完成"
}

# 显示状态
show_status() {
    log_info "服务状态:"
    docker-compose -f docker-compose.dev.yml ps 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml ps 2>/dev/null || true
}

# 主函数
main() {
    case "$1" in
        "dev")
            check_docker
            check_env_file
            create_directories
            deploy_dev "$2"
            ;;
        "prod")
            check_docker
            check_env_file
            create_directories
            deploy_prod "$2"
            ;;
        "stop")
            stop_services
            ;;
        "cleanup")
            cleanup
            ;;
        "status")
            show_status
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "无效的参数: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
