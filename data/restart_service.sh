#!/bin/bash
# 服务重启脚本 - 自动生成于 2025-07-20 19:41:01
echo "[$(date)] 开始重启服务..."

# 等待3秒，确保API响应已返回
sleep 3

# 强制结束Python进程
echo "[$(date)] 正在停止Python进程..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true

# 等待进程完全停止
sleep 2

# 启动新的Python进程
echo "[$(date)] 正在启动新进程..."
cd "G:\cursor_projects\extensions_web"
nohup "D:\develop\python396\python.exe" parent_process.py restart > /dev/null 2>&1 &

echo "[$(date)] 重启完成"
sleep 2
