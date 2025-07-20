@echo off
REM 服务重启脚本 - 自动生成于 2025-07-20 19:41:01
echo [%date% %time%] 开始重启服务... >> restart.log
echo [%date% %time%] 开始重启服务...

REM 等待3秒，确保API响应已返回
timeout /t 3 /nobreak >nul

REM 通过进程管理器重启
echo [%date% %time%] 通过进程管理器请求重启... >> restart.log
echo [%date% %time%] 通过进程管理器请求重启...
cd /d "G:\cursor_projects\extensions_web"
"D:\develop\python396\python.exe" parent_process.py restart

echo [%date% %time%] 后台服务启动完成 >> restart.log
echo [%date% %time%] 后台服务启动完成
timeout /t 5 /nobreak >nul

REM 检查服务状态
tasklist | findstr python.exe >nul
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 服务启动成功 >> restart.log
    echo [%date% %time%] 服务启动成功
) else (
    echo [%date% %time%] 警告：未检测到Python进程 >> restart.log
    echo [%date% %time%] 警告：未检测到Python进程
)

REM 检查端口监听
netstat -ano | findstr :8000 >nul
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 服务端口正常监听 >> restart.log
    echo [%date% %time%] 服务端口正常监听
) else (
    echo [%date% %time%] 提示：服务可能需要更多时间启动 >> restart.log
    echo [%date% %time%] 提示：服务可能需要更多时间启动
)
