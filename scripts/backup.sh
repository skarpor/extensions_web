#!/bin/bash

# Data Query System 2.0 备份脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="dataquery_backup_${DATE}"

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 创建备份目录
create_backup_dir() {
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
    print_message "创建备份目录: ${BACKUP_DIR}/${BACKUP_NAME}" $BLUE
}

# 备份数据文件
backup_data() {
    print_message "备份数据文件..." $BLUE
    
    if [ -d "docker-data/data" ]; then
        cp -r docker-data/data "${BACKUP_DIR}/${BACKUP_NAME}/"
        print_message "数据文件备份完成" $GREEN
    else
        print_message "警告: 数据目录不存在" $YELLOW
    fi
}

# 备份数据库
backup_database() {
    print_message "备份数据库..." $BLUE
    
    # 检查 PostgreSQL 容器是否运行
    if docker ps --format "{{.Names}}" | grep -q "data-query-postgres"; then
        print_message "备份 PostgreSQL 数据库..." $YELLOW
        docker exec data-query-postgres pg_dump -U postgres dataquery > "${BACKUP_DIR}/${BACKUP_NAME}/postgres_backup.sql"
        print_message "PostgreSQL 备份完成" $GREEN
    fi
    
    # 备份 SQLite 数据库
    if [ -f "docker-data/data/database.sqlite" ]; then
        print_message "备份 SQLite 数据库..." $YELLOW
        cp docker-data/data/database.sqlite "${BACKUP_DIR}/${BACKUP_NAME}/"
        print_message "SQLite 备份完成" $GREEN
    fi
}

# 备份配置文件
backup_config() {
    print_message "备份配置文件..." $BLUE
    
    # 备份环境配置
    if [ -f ".env" ]; then
        cp .env "${BACKUP_DIR}/${BACKUP_NAME}/"
    fi
    
    # 备份 Docker 配置
    if [ -d "docker-config" ]; then
        cp -r docker-config "${BACKUP_DIR}/${BACKUP_NAME}/"
    fi
    
    # 备份主配置文件
    if [ -f "config.py" ]; then
        cp config.py "${BACKUP_DIR}/${BACKUP_NAME}/"
    fi
    
    print_message "配置文件备份完成" $GREEN
}

# 备份扩展脚本
backup_extensions() {
    print_message "备份扩展脚本..." $BLUE
    
    if [ -d "docker-data/extensions" ]; then
        cp -r docker-data/extensions "${BACKUP_DIR}/${BACKUP_NAME}/"
        print_message "扩展脚本备份完成" $GREEN
    else
        print_message "警告: 扩展目录不存在" $YELLOW
    fi
}

# 备份用户文件
backup_uploads() {
    print_message "备份用户文件..." $BLUE
    
    if [ -d "docker-data/uploads" ]; then
        cp -r docker-data/uploads "${BACKUP_DIR}/${BACKUP_NAME}/"
        print_message "用户文件备份完成" $GREEN
    else
        print_message "警告: 上传目录不存在" $YELLOW
    fi
}

# 创建备份信息文件
create_backup_info() {
    print_message "创建备份信息文件..." $BLUE
    
    cat > "${BACKUP_DIR}/${BACKUP_NAME}/backup_info.txt" << EOF
Data Query System 2.0 备份信息
==============================

备份时间: $(date)
备份名称: ${BACKUP_NAME}
系统信息: $(uname -a)
Docker 版本: $(docker --version)
Docker Compose 版本: $(docker-compose --version 2>/dev/null || docker compose version)

备份内容:
- 数据文件 (docker-data/data)
- 数据库文件
- 配置文件
- 扩展脚本
- 用户上传文件

恢复说明:
1. 停止当前服务: ./scripts/stop.sh
2. 恢复数据文件: cp -r backup/data/* docker-data/data/
3. 恢复配置文件: cp backup/.env .env
4. 启动服务: ./scripts/start.sh

注意: 恢复前请备份当前数据！
EOF
    
    print_message "备份信息文件创建完成" $GREEN
}

# 压缩备份
compress_backup() {
    print_message "压缩备份文件..." $BLUE
    
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
    rm -rf "${BACKUP_NAME}"
    cd - > /dev/null
    
    print_message "备份压缩完成: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" $GREEN
}

# 清理旧备份
cleanup_old_backups() {
    print_message "清理旧备份..." $BLUE
    
    # 保留最近 7 个备份
    cd "${BACKUP_DIR}"
    ls -t dataquery_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true
    cd - > /dev/null
    
    print_message "旧备份清理完成" $GREEN
}

# 完整备份
full_backup() {
    print_message "开始完整备份..." $BLUE
    
    create_backup_dir
    backup_data
    backup_database
    backup_config
    backup_extensions
    backup_uploads
    create_backup_info
    compress_backup
    cleanup_old_backups
    
    print_message "完整备份完成!" $GREEN
    print_message "备份文件: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" $BLUE
}

# 快速备份 (仅数据和配置)
quick_backup() {
    print_message "开始快速备份..." $BLUE
    
    create_backup_dir
    backup_data
    backup_database
    backup_config
    create_backup_info
    compress_backup
    
    print_message "快速备份完成!" $GREEN
    print_message "备份文件: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" $BLUE
}

# 显示帮助信息
show_help() {
    echo "Data Query System 2.0 备份脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  full        完整备份 (默认)"
    echo "  quick       快速备份 (仅数据和配置)"
    echo "  data        仅备份数据文件"
    echo "  db          仅备份数据库"
    echo "  config      仅备份配置文件"
    echo "  list        列出所有备份"
    echo "  help        显示此帮助信息"
    echo ""
}

# 列出备份
list_backups() {
    print_message "备份列表:" $BLUE
    
    if [ -d "${BACKUP_DIR}" ]; then
        ls -lh "${BACKUP_DIR}"/*.tar.gz 2>/dev/null || print_message "没有找到备份文件" $YELLOW
    else
        print_message "备份目录不存在" $YELLOW
    fi
}

# 主函数
main() {
    case "${1:-full}" in
        "full")
            full_backup
            ;;
        "quick")
            quick_backup
            ;;
        "data")
            create_backup_dir
            backup_data
            create_backup_info
            compress_backup
            ;;
        "db")
            create_backup_dir
            backup_database
            create_backup_info
            compress_backup
            ;;
        "config")
            create_backup_dir
            backup_config
            create_backup_info
            compress_backup
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
