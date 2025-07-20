#!/usr/bin/env python3
"""
通过API接口测试重启脚本 - 3次测试
"""
import requests
import json
import time

def api_test():
    """通过API接口测试"""
    base_url = "http://localhost:8000/api/system/system"
    
    print("========== 通过API接口测试重启脚本 ==========")
    
    # 步骤1：通过接口创建重启脚本
    print("\n1. 通过接口创建重启脚本...")
    try:
        create_response = requests.post(f"{base_url}/create-restart-script")
        print(f"创建脚本状态码: {create_response.status_code}")
        if create_response.status_code == 200:
            result = create_response.json()
            print("✓ 脚本创建成功")
            print(f"创建的脚本: {result.get('scripts', [])}")
        else:
            print(f"✗ 脚本创建失败: {create_response.text}")
            return
    except Exception as e:
        print(f"✗ 创建脚本异常: {e}")
        return
    
    # 步骤2：通过接口执行重启命令 - 3次测试
    for i in range(1, 4):
        print(f"\n========== 第{i}次API接口测试 ==========")
        
        try:
            # 通过接口执行重启命令
            execute_data = {
                "command": "data\\restart_service.bat",
                "name": f"第{i}次API接口测试"
            }
            
            print(f"发送执行请求: {execute_data}")
            execute_response = requests.post(
                f"{base_url}/execute-command",
                headers={"Content-Type": "application/json"},
                json=execute_data,
                timeout=30
            )
            
            print(f"执行状态码: {execute_response.status_code}")
            
            if execute_response.status_code == 200:
                result = execute_response.json()
                print(f"成功: {result.get('success')}")
                print(f"输出: {result.get('output', '')}")
                if result.get('error'):
                    print(f"错误: {result.get('error')}")
                
                if result.get('success'):
                    print("✓ API接口执行成功")
                else:
                    print("✗ API接口执行失败")
                    
            elif execute_response.status_code == 401:
                print("✗ 需要认证，跳过认证测试")
                break
            else:
                print(f"✗ HTTP错误: {execute_response.text}")
                
        except requests.exceptions.ConnectionError:
            print("✗ 连接错误 - 服务可能已重启，等待重新连接...")
            # 等待服务重启
            for wait_time in range(10):
                time.sleep(1)
                try:
                    test_response = requests.get("http://localhost:8000/", timeout=5)
                    if test_response.status_code:
                        print(f"✓ 服务在{wait_time+1}秒后重新连接成功")
                        break
                except:
                    continue
            else:
                print("✗ 等待10秒后仍无法连接服务")
                
        except Exception as e:
            print(f"✗ 执行异常: {e}")
        
        if i < 3:
            print("等待5秒进行下一次测试...")
            time.sleep(5)
    
    print("\n========== API接口测试完成 ==========")

if __name__ == "__main__":
    api_test()
