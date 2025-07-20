#!/usr/bin/env python3
"""
最终API测试 - 验证问题是否真正解决
"""
import requests
import time
import subprocess

def wait_for_service(max_wait=30):
    """等待服务启动"""
    for i in range(max_wait):
        try:
            response = requests.get("http://localhost:8000/", timeout=2)
            if response.status_code:
                print(f"✓ 服务在{i+1}秒后启动成功")
                return True
        except:
            time.sleep(1)
    print(f"✗ 等待{max_wait}秒后服务仍未启动")
    return False

def check_python_process():
    """检查Python进程"""
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                               capture_output=True, text=True)
        if 'python.exe' in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'python.exe' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        print(f"✓ Python进程运行中 (PID: {pid})")
                        return pid
        print("✗ 未找到Python进程")
        return None
    except Exception as e:
        print(f"✗ 检查进程失败: {e}")
        return None

def final_test():
    """最终测试"""
    print("========== 最终API接口测试 ==========")
    
    # 临时禁用认证进行测试
    print("注意：需要临时禁用API认证才能测试")
    
    base_url = "http://localhost:8000/api/system/system"
    
    # 等待服务启动
    if not wait_for_service():
        return
    
    # 步骤1：重新生成脚本
    print("\n1. 通过API重新生成重启脚本...")
    try:
        create_response = requests.post(f"{base_url}/create-restart-script", timeout=10)
        if create_response.status_code == 200:
            result = create_response.json()
            print("✓ 脚本重新生成成功")
            print(f"启动命令: {result.get('start_command', 'N/A')}")
        else:
            print(f"✗ 脚本生成失败: {create_response.status_code}")
            return
    except Exception as e:
        print(f"✗ 生成脚本异常: {e}")
        return
    
    # 步骤2：进行3次API重启测试
    success_count = 0
    
    for i in range(1, 4):
        print(f"\n========== 第{i}次API重启测试 ==========")
        
        # 记录测试前的进程ID
        old_pid = check_python_process()
        
        try:
            # 通过API执行重启
            execute_data = {
                "command": "data\\restart_service.bat",
                "name": f"第{i}次最终测试"
            }
            
            print(f"发送重启请求...")
            execute_response = requests.post(
                f"{base_url}/execute-command",
                json=execute_data,
                timeout=30
            )
            
            if execute_response.status_code == 200:
                result = execute_response.json()
                if result.get('success'):
                    print("✓ API执行成功")
                else:
                    print(f"✗ API执行失败: {result.get('error')}")
                    continue
            else:
                print(f"✗ HTTP错误: {execute_response.status_code}")
                continue
                
        except requests.exceptions.ConnectionError:
            print("✓ 连接中断 - 说明重启命令被执行")
        except Exception as e:
            print(f"✗ 请求异常: {e}")
            continue
        
        # 等待重启完成
        print("等待重启完成...")
        if wait_for_service(20):
            new_pid = check_python_process()
            if new_pid and new_pid != old_pid:
                print(f"✓ 重启成功！进程ID从 {old_pid} 变为 {new_pid}")
                success_count += 1
            elif new_pid:
                print(f"✗ 进程ID未变化 ({new_pid})，可能重启失败")
            else:
                print("✗ 重启后未找到Python进程")
        else:
            print("✗ 重启后服务未启动")
        
        if i < 3:
            print("等待5秒进行下一次测试...")
            time.sleep(5)
    
    # 测试结果
    print(f"\n========== 测试结果 ==========")
    print(f"成功次数: {success_count}/3")
    if success_count == 3:
        print("🎉 所有测试通过！API重启功能正常工作！")
    else:
        print("❌ 测试失败，需要进一步修复")

if __name__ == "__main__":
    final_test()
