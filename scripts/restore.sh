#!/bin/bash

# Data Query System 2.0 恢复脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="./backups"
TEMP_DIR="/tmp/dataquery_restore"

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 列出可用备份
list_backups() {
    print_message "可用备份列表:" $BLUE
    echo ""
    
    if [ -d "${BACKUP_DIR}" ]; then
        backups=($(ls -t "${BACKUP_DIR}"/dataquery_backup_*.tar.gz 2>/dev/null || true))
        
        if [ ${#backups[@]} -eq 0 ]; then
            print_message "没有找到备份文件" $YELLOW
            return 1
        fi
        
        for i in "${!backups[@]}"; do
            backup_file=$(basename "${backups[$i]}")
            backup_date=$(echo "$backup_file" | sed 's/dataquery_backup_\([0-9_]*\)\.tar\.gz/\1/' | sed 's/_/ /')
            file_size=$(du -h "${backups[$i]}" | cut -f1)
            echo "  $((i+1)). $backup_file ($file_size) - $backup_date"
        done
        
        return 0
    else
        print_message "备份目录不存在" $YELLOW
        return 1
    fi
}

# 选择备份文件
select_backup() {
    if ! list_backups; then
        exit 1
    fi
    
    echo ""
    read -p "请选择要恢复的备份 (输入编号): " backup_choice
    
    backups=($(ls -t "${BACKUP_DIR}"/dataquery_backup_*.tar.gz 2>/dev/null))
    
    if [[ "$backup_choice" =~ ^[0-9]+$ ]] && [ "$backup_choice" -ge 1 ] && [ "$backup_choice" -le ${#backups[@]} ]; then
        selected_backup="${backups[$((backup_choice-1))]}"
        print_message "选择的备份: $(basename "$selected_backup")" $GREEN
        echo "$selected_backup"
    else
        print_message "无效的选择" $RED
        exit 1
    fi
}

# 解压备份文件
extract_backup() {
    local backup_file="$1"
    
    print_message "解压备份文件..." $BLUE
    
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    
    tar -xzf "$backup_file" -C "$TEMP_DIR"
    
    # 查找解压后的目录
    backup_name=$(basename "$backup_file" .tar.gz)
    extracted_dir="$TEMP_DIR/$backup_name"
    
    if [ ! -d "$extracted_dir" ]; then
        print_message "错误: 备份文件格式不正确" $RED
        exit 1
    fi
    
    print_message "备份文件解压完成" $GREEN
    echo "$extracted_dir"
}

# 停止服务
stop_services() {
    print_message "停止服务..." $BLUE
    ./scripts/stop.sh all 2>/dev/null || true
    print_message "服务已停止" $GREEN
}

# 备份当前数据
backup_current() {
    print_message "备份当前数据..." $BLUE
    
    current_backup_dir="./backups/before_restore_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$current_backup_dir"
    
    if [ -d "docker-data" ]; then
        cp -r docker-data "$current_backup_dir/"
    fi
    
    if [ -f ".env" ]; then
        cp .env "$current_backup_dir/"
    fi
    
    print_message "当前数据已备份到: $current_backup_dir" $GREEN
}

# 恢复数据文件
restore_data() {
    local extracted_dir="$1"
    
    print_message "恢复数据文件..." $BLUE
    
    if [ -d "$extracted_dir/data" ]; then
        mkdir -p docker-data
        rm -rf docker-data/data
        cp -r "$extracted_dir/data" docker-data/
        print_message "数据文件恢复完成" $GREEN
    else
        print_message "警告: 备份中没有数据文件" $YELLOW
    fi
}

# 恢复配置文件
restore_config() {
    local extracted_dir="$1"
    
    print_message "恢复配置文件..." $BLUE
    
    if [ -f "$extracted_dir/.env" ]; then
        cp "$extracted_dir/.env" .env
        print_message "环境配置恢复完成" $GREEN
    else
        print_message "警告: 备份中没有环境配置文件" $YELLOW
    fi
    
    if [ -d "$extracted_dir/docker-config" ]; then
        rm -rf docker-config
        cp -r "$extracted_dir/docker-config" .
        print_message "Docker配置恢复完成" $GREEN
    fi
    
    if [ -f "$extracted_dir/config.py" ]; then
        cp "$extracted_dir/config.py" .
        print_message "主配置文件恢复完成" $GREEN
    fi
}

# 恢复扩展脚本
restore_extensions() {
    local extracted_dir="$1"
    
    print_message "恢复扩展脚本..." $BLUE
    
    if [ -d "$extracted_dir/extensions" ]; then
        mkdir -p docker-data
        rm -rf docker-data/extensions
        cp -r "$extracted_dir/extensions" docker-data/
        print_message "扩展脚本恢复完成" $GREEN
    else
        print_message "警告: 备份中没有扩展脚本" $YELLOW
    fi
}

# 恢复用户文件
restore_uploads() {
    local extracted_dir="$1"
    
    print_message "恢复用户文件..." $BLUE
    
    if [ -d "$extracted_dir/uploads" ]; then
        mkdir -p docker-data
        rm -rf docker-data/uploads
        cp -r "$extracted_dir/uploads" docker-data/
        print_message "用户文件恢复完成" $GREEN
    else
        print_message "警告: 备份中没有用户文件" $YELLOW
    fi
}

# 恢复数据库
restore_database() {
    local extracted_dir="$1"
    
    print_message "恢复数据库..." $BLUE
    
    # 恢复 SQLite 数据库
    if [ -f "$extracted_dir/database.sqlite" ]; then
        mkdir -p docker-data/data
        cp "$extracted_dir/database.sqlite" docker-data/data/
        print_message "SQLite 数据库恢复完成" $GREEN
    fi
    
    # PostgreSQL 数据库恢复需要在服务启动后进行
    if [ -f "$extracted_dir/postgres_backup.sql" ]; then
        print_message "PostgreSQL 备份文件已准备，将在服务启动后恢复" $YELLOW
        mkdir -p docker-data/db
        cp "$extracted_dir/postgres_backup.sql" docker-data/db/
    fi
}

# 启动服务
start_services() {
    print_message "启动服务..." $BLUE
    ./scripts/start.sh prod
    print_message "服务启动完成" $GREEN
}

# 恢复 PostgreSQL 数据库
restore_postgres() {
    local postgres_backup="docker-data/db/postgres_backup.sql"
    
    if [ -f "$postgres_backup" ]; then
        print_message "恢复 PostgreSQL 数据库..." $BLUE
        
        # 等待 PostgreSQL 服务启动
        sleep 10
        
        # 恢复数据库
        docker exec -i data-query-postgres psql -U postgres dataquery < "$postgres_backup"
        
        print_message "PostgreSQL 数据库恢复完成" $GREEN
        rm -f "$postgres_backup"
    fi
}

# 清理临时文件
cleanup() {
    print_message "清理临时文件..." $BLUE
    rm -rf "$TEMP_DIR"
    print_message "清理完成" $GREEN
}

# 完整恢复
full_restore() {
    local backup_file
    
    if [ -n "$1" ]; then
        backup_file="$1"
        if [ ! -f "$backup_file" ]; then
            print_message "错误: 备份文件不存在: $backup_file" $RED
            exit 1
        fi
    else
        backup_file=$(select_backup)
    fi
    
    print_message "开始完整恢复..." $BLUE
    print_message "备份文件: $(basename "$backup_file")" $BLUE
    
    # 确认操作
    echo ""
    print_message "警告: 此操作将覆盖当前所有数据!" $RED
    read -p "确定要继续吗? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "操作已取消" $YELLOW
        exit 0
    fi
    
    extracted_dir=$(extract_backup "$backup_file")
    stop_services
    backup_current
    restore_data "$extracted_dir"
    restore_config "$extracted_dir"
    restore_extensions "$extracted_dir"
    restore_uploads "$extracted_dir"
    restore_database "$extracted_dir"
    start_services
    
    # 等待服务启动后恢复 PostgreSQL
    restore_postgres
    
    cleanup
    
    print_message "完整恢复完成!" $GREEN
    print_message "应用地址: http://localhost" $BLUE
}

# 显示帮助信息
show_help() {
    echo "Data Query System 2.0 恢复脚本"
    echo ""
    echo "用法: $0 [选项] [备份文件]"
    echo ""
    echo "选项:"
    echo "  full [file]     完整恢复 (默认)"
    echo "  data [file]     仅恢复数据文件"
    echo "  config [file]   仅恢复配置文件"
    echo "  list            列出可用备份"
    echo "  help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                                    # 交互式选择备份进行完整恢复"
    echo "  $0 full backup.tar.gz                # 使用指定备份进行完整恢复"
    echo "  $0 data                               # 仅恢复数据文件"
    echo ""
}

# 主函数
main() {
    case "${1:-full}" in
        "full")
            full_restore "$2"
            ;;
        "data")
            backup_file="${2:-$(select_backup)}"
            extracted_dir=$(extract_backup "$backup_file")
            stop_services
            backup_current
            restore_data "$extracted_dir"
            start_services
            cleanup
            ;;
        "config")
            backup_file="${2:-$(select_backup)}"
            extracted_dir=$(extract_backup "$backup_file")
            restore_config "$extracted_dir"
            cleanup
            ;;
        "list")
            list_backups
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
