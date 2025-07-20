#!/usr/bin/env python3
"""
完整测试：创建重启脚本并测试3次
"""
import subprocess
import time
import os

def create_restart_script():
    """手动创建重启脚本"""
    script_content = '''@echo off
REM 服务重启脚本 - 自动生成
echo [%date% %time%] 开始重启服务...

REM 等待3秒，确保API响应已返回
timeout /t 3 /nobreak >nul

REM 强制结束Python进程
echo [%date% %time%] 正在停止Python进程...
TASKKILL /IM python.exe /F >nul 2>&1

REM 等待进程完全停止
timeout /t 2 /nobreak >nul

REM 启动新的Python进程
echo [%date% %time%] 正在启动新进程...
cd /d "G:\\cursor_projects\\extensions_web"
start "" "D:\\develop\\python396\\python.exe" "main.py"

echo [%date% %time%] 重启完成，新进程已在后台启动
timeout /t 3 /nobreak >nul

REM 检查进程状态
tasklist | findstr python.exe >nul
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 服务启动成功
) else (
    echo [%date% %time%] 警告：未检测到Python进程
)

REM 检查端口监听
netstat -ano | findstr :8000 >nul
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 服务端口正常监听
) else (
    echo [%date% %time%] 提示：服务可能需要更多时间启动
)
'''
    
    # 确保data目录存在
    os.makedirs('data', exist_ok=True)
    
    # 写入脚本文件
    with open('data/restart_service.bat', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✓ 重启脚本已创建: data/restart_service.bat")

def test_restart_script():
    """测试重启脚本3次"""
    script_path = "data/restart_service.bat"
    
    # 先创建脚本
    create_restart_script()
    
    for i in range(1, 4):
        print(f"\n========== 第{i}次测试 ==========")
        
        try:
            print(f"执行脚本: {script_path}")
            
            # 使用cmd执行脚本
            full_path = os.path.abspath(script_path)
            result = subprocess.run(
                f'cmd /c "{full_path}"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )
            
            print(f"返回码: {result.returncode}")
            print(f"输出: {result.stdout}")
            if result.stderr:
                print(f"错误: {result.stderr}")
            
            if result.returncode == 0:
                print("✓ 脚本执行成功")
            else:
                print("✗ 脚本执行失败")
            
            # 等待5秒检查进程
            print("等待5秒检查进程...")
            time.sleep(5)
            
            # 检查Python进程
            proc_result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                       capture_output=True, text=True)
            if 'python.exe' in proc_result.stdout:
                print("✓ Python进程正在运行")
                # 显示进程信息
                lines = proc_result.stdout.split('\n')
                for line in lines:
                    if 'python.exe' in line and 'main.py' not in line:
                        print(f"  进程: {line.strip()}")
            else:
                print("✗ 未找到Python进程")
            
            # 检查端口
            port_result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            if ':8000' in port_result.stdout:
                print("✓ 端口8000正在监听")
            else:
                print("✗ 端口8000未监听")
                
        except subprocess.TimeoutExpired:
            print("✗ 脚本执行超时")
        except Exception as e:
            print(f"✗ 执行异常: {e}")
        
        if i < 3:
            print("等待10秒进行下一次测试...")
            time.sleep(10)
    
    print("\n========== 测试完成 ==========")

if __name__ == "__main__":
    test_restart_script()
