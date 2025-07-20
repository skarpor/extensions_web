#!/usr/bin/env python3
"""
测试重启脚本接口 - 3次测试
"""
import requests
import json
import time

def test_restart_api():
    """测试重启API接口"""
    # 先登录获取token
    login_url = "http://localhost:8000/api/auth/login"
    login_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    login_data = "username=admin&password=123456"

    try:
        login_response = requests.post(login_url, headers=login_headers, data=login_data)
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print(f"登录成功，获取token: {token[:20]}...")
        else:
            print(f"登录失败: {login_response.text}")
            return
    except Exception as e:
        print(f"登录异常: {e}")
        return

    url = "http://localhost:8000/api/system/system/execute-command"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    for i in range(1, 4):
        print(f"\n========== 第{i}次测试 ==========")
        
        data = {
            "command": "data\\restart_service.bat",
            "name": f"第{i}次接口测试"
        }
        
        try:
            print(f"发送请求: {data}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"成功: {result.get('success')}")
                print(f"输出: {result.get('output', '')}")
                if result.get('error'):
                    print(f"错误: {result.get('error')}")
                    
                # 等待5秒检查进程
                print("等待5秒检查进程...")
                time.sleep(5)
                
                # 检查Python进程
                import subprocess
                try:
                    proc_result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                               capture_output=True, text=True)
                    if 'python.exe' in proc_result.stdout:
                        print("✓ Python进程正在运行")
                    else:
                        print("✗ 未找到Python进程")
                except:
                    print("无法检查进程状态")
                    
            else:
                print(f"HTTP错误: {response.text}")
                
        except Exception as e:
            print(f"请求异常: {e}")
        
        if i < 3:
            print("等待10秒进行下一次测试...")
            time.sleep(10)
    
    print("\n========== 测试完成 ==========")

if __name__ == "__main__":
    test_restart_api()
