#!/bin/bash

# Data Query System 2.0 停止脚本

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

# 停止所有服务
stop_all() {
    print_message "停止所有 Data Query System 服务..." $BLUE
    
    # 停止生产环境
    if [ -f docker-compose.yml ]; then
        print_message "停止生产环境服务..." $YELLOW
        docker-compose down
    fi
    
    # 停止开发环境
    if [ -f docker-compose.dev.yml ]; then
        print_message "停止开发环境服务..." $YELLOW
        docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    fi
    
    print_message "所有服务已停止" $GREEN
}

# 停止并删除卷
stop_with_volumes() {
    print_message "停止服务并删除卷..." $YELLOW
    read -p "这将删除所有数据卷，数据将丢失。确定继续吗? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
        print_message "服务和卷已删除" $GREEN
    else
        print_message "取消操作" $YELLOW
    fi
}

# 强制停止所有相关容器
force_stop() {
    print_message "强制停止所有相关容器..." $YELLOW
    
    # 获取所有相关容器
    containers=$(docker ps -a --filter "name=data-query" --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -n "$containers" ]; then
        echo "$containers" | xargs docker stop 2>/dev/null || true
        echo "$containers" | xargs docker rm 2>/dev/null || true
        print_message "强制停止完成" $GREEN
    else
        print_message "没有找到相关容器" $BLUE
    fi
}

# 显示帮助信息
show_help() {
    echo "Data Query System 2.0 停止脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  all         停止所有服务 (默认)"
    echo "  volumes     停止服务并删除卷"
    echo "  force       强制停止所有相关容器"
    echo "  help        显示此帮助信息"
    echo ""
}

# 主函数
main() {
    case "${1:-all}" in
        "all")
            stop_all
            ;;
        "volumes")
            stop_with_volumes
            ;;
        "force")
            force_stop
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
