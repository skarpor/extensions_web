#!/bin/bash

# Data Query System 2.0 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 检查 Docker 和 Docker Compose
check_dependencies() {
    print_message "检查依赖..." $BLUE
    
    if ! command -v docker &> /dev/null; then
        print_message "错误: Docker 未安装或未在 PATH 中" $RED
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_message "错误: Docker Compose 未安装或未在 PATH 中" $RED
        exit 1
    fi
    
    print_message "依赖检查通过" $GREEN
}

# 创建必要的目录
create_directories() {
    print_message "创建必要的目录..." $BLUE
    
    mkdir -p docker-data/{data,logs,extensions,uploads,db,static,ssl,redis,postgres,grafana,prometheus}
    mkdir -p docker-data/data/{extensions,file,db,logs}
    
    # 设置权限
    chmod 755 docker-data
    chmod -R 755 docker-data/*
    
    print_message "目录创建完成" $GREEN
}

# 复制环境配置文件
setup_env() {
    if [ ! -f .env ]; then
        print_message "创建环境配置文件..." $BLUE
        cp .env.example .env
        print_message "请编辑 .env 文件配置您的环境变量" $YELLOW
    else
        print_message "环境配置文件已存在" $GREEN
    fi
}

# 构建镜像
build_images() {
    print_message "构建 Docker 镜像..." $BLUE
    
    if [ "$1" = "dev" ]; then
        docker-compose -f docker-compose.dev.yml build
    else
        docker-compose build
    fi
    
    print_message "镜像构建完成" $GREEN
}

# 启动服务
start_services() {
    print_message "启动服务..." $BLUE
    
    if [ "$1" = "dev" ]; then
        docker-compose -f docker-compose.dev.yml up -d
        print_message "开发环境启动完成" $GREEN
        print_message "前端地址: http://localhost:5173" $BLUE
        print_message "后端地址: http://localhost:8000" $BLUE
        print_message "API文档: http://localhost:8000/docs" $BLUE
    else
        docker-compose up -d
        print_message "生产环境启动完成" $GREEN
        print_message "应用地址: http://localhost" $BLUE
        print_message "API文档: http://localhost/docs" $BLUE
        print_message "数据库管理: http://localhost:8080" $BLUE
        print_message "监控面板: http://localhost:3000" $BLUE
    fi
}

# 显示帮助信息
show_help() {
    echo "Data Query System 2.0 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  dev         启动开发环境"
    echo "  prod        启动生产环境 (默认)"
    echo "  build       仅构建镜像"
    echo "  stop        停止所有服务"
    echo "  restart     重启服务"
    echo "  logs        查看日志"
    echo "  clean       清理所有容器和镜像"
    echo "  help        显示此帮助信息"
    echo ""
}

# 停止服务
stop_services() {
    print_message "停止服务..." $BLUE
    docker-compose down
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    print_message "服务已停止" $GREEN
}

# 重启服务
restart_services() {
    print_message "重启服务..." $BLUE
    stop_services
    if [ "$1" = "dev" ]; then
        start_services dev
    else
        start_services prod
    fi
}

# 查看日志
show_logs() {
    if [ "$1" = "dev" ]; then
        docker-compose -f docker-compose.dev.yml logs -f
    else
        docker-compose logs -f
    fi
}

# 清理
clean_all() {
    print_message "清理所有容器和镜像..." $YELLOW
    read -p "这将删除所有相关的容器、镜像和卷。确定继续吗? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --rmi all
        docker-compose -f docker-compose.dev.yml down -v --rmi all 2>/dev/null || true
        docker system prune -f
        print_message "清理完成" $GREEN
    else
        print_message "取消清理" $YELLOW
    fi
}

# 主函数
main() {
    case "${1:-prod}" in
        "dev")
            check_dependencies
            create_directories
            setup_env
            build_images dev
            start_services dev
            ;;
        "prod")
            check_dependencies
            create_directories
            setup_env
            build_images prod
            start_services prod
            ;;
        "build")
            check_dependencies
            if [ "$2" = "dev" ]; then
                build_images dev
            else
                build_images prod
            fi
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services $2
            ;;
        "logs")
            show_logs $2
            ;;
        "clean")
            clean_all
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_message "未知选项: $1" $RED
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
