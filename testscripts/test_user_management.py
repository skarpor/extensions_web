#!/usr/bin/env python3
"""
测试用户管理功能
"""
import requests
import json
import time

def test_user_management():
    """测试用户管理API"""
    base_url = "http://localhost:8000"
    
    print("========== 用户管理功能测试 ==========")
    
    # 首先需要登录获取token
    print("\n1. 登录获取token...")
    login_data = {
        "username": "admin",  # 假设有admin用户
        "password": "admin123"  # 假设密码
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print("✓ 登录成功，获取到token")
        else:
            print(f"✗ 登录失败: {login_response.status_code}")
            print("请确保有admin用户或修改登录信息")
            return
    except Exception as e:
        print(f"✗ 登录异常: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试获取用户列表
    print("\n2. 测试获取用户列表...")
    try:
        response = requests.get(f"{base_url}/api/v1/users", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"✓ 获取用户列表成功，共 {len(users)} 个用户")
            for user in users[:3]:  # 只显示前3个用户
                print(f"  - {user.get('username')} ({user.get('email')}) - {'活跃' if user.get('is_active') else '禁用'}")
        else:
            print(f"✗ 获取用户列表失败: {response.text}")
    except Exception as e:
        print(f"✗ 获取用户列表异常: {e}")
    
    # 测试创建用户
    print("\n3. 测试创建用户...")
    test_user_data = {
        "username": f"testuser_{int(time.time())}",
        "nickname": "测试用户",
        "email": f"test_{int(time.time())}@example.com",
        "password": "test123456",
        "is_active": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/users", 
                               json=test_user_data, 
                               headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            new_user = response.json()
            test_user_id = new_user.get("id")
            print(f"✓ 创建用户成功: {new_user.get('username')} (ID: {test_user_id})")
        else:
            print(f"✗ 创建用户失败: {response.text}")
            test_user_id = None
    except Exception as e:
        print(f"✗ 创建用户异常: {e}")
        test_user_id = None
    
    # 测试获取单个用户信息
    if test_user_id:
        print(f"\n4. 测试获取用户信息 (ID: {test_user_id})...")
        try:
            response = requests.get(f"{base_url}/api/v1/users/{test_user_id}", headers=headers)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                user = response.json()
                print(f"✓ 获取用户信息成功: {user.get('username')}")
            else:
                print(f"✗ 获取用户信息失败: {response.text}")
        except Exception as e:
            print(f"✗ 获取用户信息异常: {e}")
    
    # 测试更新用户
    if test_user_id:
        print(f"\n5. 测试更新用户 (ID: {test_user_id})...")
        update_data = {
            "nickname": "更新后的昵称",
            "is_active": True
        }
        
        try:
            response = requests.put(f"{base_url}/api/v1/users/{test_user_id}", 
                                  json=update_data, 
                                  headers=headers)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                updated_user = response.json()
                print(f"✓ 更新用户成功: {updated_user.get('nickname')}")
            else:
                print(f"✗ 更新用户失败: {response.text}")
        except Exception as e:
            print(f"✗ 更新用户异常: {e}")
    
    # 测试删除用户
    if test_user_id:
        print(f"\n6. 测试删除用户 (ID: {test_user_id})...")
        try:
            response = requests.delete(f"{base_url}/api/v1/users/{test_user_id}", headers=headers)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 删除用户成功: {result.get('message')}")
            else:
                print(f"✗ 删除用户失败: {response.text}")
        except Exception as e:
            print(f"✗ 删除用户异常: {e}")
    
    # 测试获取当前用户信息
    print("\n7. 测试获取当前用户信息...")
    try:
        response = requests.get(f"{base_url}/api/v1/users/me", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            current_user = response.json()
            print(f"✓ 获取当前用户信息成功: {current_user.get('username')}")
            print(f"  - 昵称: {current_user.get('nickname')}")
            print(f"  - 邮箱: {current_user.get('email')}")
            print(f"  - 超级管理员: {'是' if current_user.get('is_superuser') else '否'}")
        else:
            print(f"✗ 获取当前用户信息失败: {response.text}")
    except Exception as e:
        print(f"✗ 获取当前用户信息异常: {e}")
    
    print("\n========== 测试完成 ==========")
    print("✓ 用户管理API测试完成")
    print("✓ 前端页面应该能正常显示用户列表")
    print("✓ 可以在设置页面的用户配置标签中管理用户")

if __name__ == "__main__":
    test_user_management()
