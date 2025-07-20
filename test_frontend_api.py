#!/usr/bin/env python3
"""
测试前端进程管理器API功能
"""
import requests
import time
import json

def test_process_manager_apis():
    """测试进程管理器API"""
    base_url = "http://localhost:8000/api/system/system"
    
    print("========== 测试进程管理器API ==========")
    
    # 1. 测试获取进程配置
    print("\n1. 测试获取进程配置...")
    try:
        response = requests.get(f"{base_url}/process-config")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                config = result.get('config', {})
                print("✓ 获取配置成功")
                print(f"  端口: {config.get('check_port')}")
                print(f"  URL: {config.get('check_url')}")
                print(f"  命令: {config.get('command')}")
                print(f"  参数: {config.get('args')}")
            else:
                print("✗ 获取配置失败:", result.get('message'))
        else:
            print(f"✗ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"✗ 异常: {e}")
    
    # 2. 测试更新进程配置
    print("\n2. 测试更新进程配置...")
    try:
        new_config = {
            "command": "D:\\develop\\python396\\python.exe",
            "args": ["main.py"],
            "cwd": "G:\\cursor_projects\\extensions_web",
            "check_port": 8000,
            "check_url": "http://localhost:8000/",
            "restart_delay": 5,  # 修改延迟时间
            "auto_restart": True,
            "max_restart_attempts": 15  # 修改最大重启次数
        }
        
        response = requests.post(f"{base_url}/process-config", json=new_config)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✓ 更新配置成功")
                print(f"  消息: {result.get('message')}")
            else:
                print("✗ 更新配置失败:", result.get('message'))
        else:
            print(f"✗ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"✗ 异常: {e}")
    
    # 3. 测试进程重启
    print("\n3. 测试进程重启...")
    try:
        response = requests.post(f"{base_url}/process-restart")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✓ 重启命令发送成功")
                print(f"  消息: {result.get('message')}")
                print(f"  命令: {result.get('command')}")
            else:
                print("✗ 重启命令发送失败:", result.get('message'))
        else:
            print(f"✗ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"✗ 异常: {e}")
    
    # 等待重启完成
    print("\n等待10秒让重启完成...")
    time.sleep(10)
    
    # 4. 测试服务是否重新启动
    print("\n4. 测试服务是否重新启动...")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✓ 服务重启成功，正常运行")
        else:
            print(f"✗ 服务状态异常: {response.status_code}")
    except Exception as e:
        print(f"✗ 服务连接失败: {e}")
    
    print("\n========== 测试完成 ==========")

if __name__ == "__main__":
    test_process_manager_apis()
