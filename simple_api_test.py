#!/usr/bin/env python3
"""
简单API接口测试 - 直接测试执行命令（跳过认证）
"""
import requests
import json
import time

def simple_api_test():
    """简单API测试 - 不需要认证"""
    base_url = "http://localhost:8000/api/system/system"
    
    print("========== 简单API接口测试（跳过认证） ==========")
    
    # 直接测试执行命令 - 3次测试
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
                print("✗ 需要认证")
                break
            else:
                print(f"✗ HTTP错误: {execute_response.text}")
                
        except requests.exceptions.ConnectionError:
            print("✗ 连接错误 - 服务可能已重启，等待重新连接...")
            # 等待服务重启
            for wait_time in range(15):
                time.sleep(1)
                try:
                    test_response = requests.get("http://localhost:8000/", timeout=5)
                    if test_response.status_code:
                        print(f"✓ 服务在{wait_time+1}秒后重新连接成功")
                        break
                except:
                    continue
            else:
                print("✗ 等待15秒后仍无法连接服务")
                
        except Exception as e:
            print(f"✗ 执行异常: {e}")
        
        if i < 3:
            print("等待5秒进行下一次测试...")
            time.sleep(5)
    
    print("\n========== API接口测试完成 ==========")

if __name__ == "__main__":
    simple_api_test()
