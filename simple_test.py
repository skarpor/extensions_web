#!/usr/bin/env python3
"""
简单测试重启脚本 - 直接调用系统命令
"""
import subprocess
import time
import os

def test_restart_script():
    """测试重启脚本3次"""
    script_path = "data\\restart_service.bat"
    
    for i in range(1, 4):
        print(f"\n========== 第{i}次测试 ==========")
        
        try:
            print(f"执行脚本: {script_path}")
            
            # 使用cmd执行脚本
            result = subprocess.run(
                f'"{script_path}"',
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
                    if 'python.exe' in line:
                        print(f"  进程: {line.strip()}")
            else:
                print("✗ 未找到Python进程")
                
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
