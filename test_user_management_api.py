#!/usr/bin/env python3
"""
测试用户管理API功能
"""
import requests
import json
import time

def test_user_management_api():
    """测试用户管理API"""
    base_url = "http://localhost:8000"
    
    print("========== 用户管理API测试 ==========")
    
    # 首先测试不需要认证的接口
    print("\n1. 测试API健康检查...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ 后端服务正常运行")
        else:
            print(f"✗ 服务异常: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 服务未启动: {e}")
        return
    
    # 测试API文档访问
    print("\n2. 测试API文档访问...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ API文档可以访问: http://localhost:8000/docs")
        else:
            print(f"✗ API文档访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ API文档访问异常: {e}")
    
    # 测试用户相关API路径（无认证）
    print("\n3. 测试用户API路径...")
    
    # 测试获取用户列表（应该需要认证）
    try:
        response = requests.get(f"{base_url}/api/users", timeout=5)
        print(f"GET /api/users 状态码: {response.status_code}")
        if response.status_code == 401:
            print("✓ 用户列表API需要认证（正常）")
        elif response.status_code == 200:
            print("⚠ 用户列表API不需要认证（可能的安全问题）")
        else:
            print(f"✗ 意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"✗ 用户列表API测试异常: {e}")
    
    # 测试获取当前用户信息（应该需要认证）
    try:
        response = requests.get(f"{base_url}/api/users/me", timeout=5)
        print(f"GET /api/users/me 状态码: {response.status_code}")
        if response.status_code == 401:
            print("✓ 当前用户API需要认证（正常）")
        elif response.status_code == 200:
            print("⚠ 当前用户API不需要认证（可能的安全问题）")
        else:
            print(f"✗ 意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"✗ 当前用户API测试异常: {e}")
    
    # 测试创建用户（应该需要认证）
    try:
        test_user_data = {
            "username": "testuser",
            "nickname": "测试用户",
            "email": "test@example.com",
            "password": "test123456"
        }
        response = requests.post(f"{base_url}/api/users", 
                               json=test_user_data, 
                               timeout=5)
        print(f"POST /api/users 状态码: {response.status_code}")
        if response.status_code == 401:
            print("✓ 创建用户API需要认证（正常）")
        elif response.status_code == 200:
            print("⚠ 创建用户API不需要认证（可能的安全问题）")
        else:
            print(f"✗ 意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"✗ 创建用户API测试异常: {e}")
    
    # 测试搜索用户
    try:
        response = requests.get(f"{base_url}/api/users/search/users?q=test", timeout=5)
        print(f"GET /api/users/search/users 状态码: {response.status_code}")
        if response.status_code == 401:
            print("✓ 搜索用户API需要认证（正常）")
        elif response.status_code == 200:
            print("⚠ 搜索用户API不需要认证（可能的安全问题）")
        else:
            print(f"✗ 意外的状态码: {response.status_code}")
    except Exception as e:
        print(f"✗ 搜索用户API测试异常: {e}")
    
    print("\n4. 测试前端页面访问...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✓ 前端页面可以访问: http://localhost:8000/")
        else:
            print(f"✗ 前端页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 前端页面访问异常: {e}")
    
    print("\n========== API路径总结 ==========")
    print("用户管理相关API路径（注意：没有v1前缀）:")
    print("  GET    /api/users              - 获取用户列表")
    print("  POST   /api/users              - 创建用户")
    print("  GET    /api/users/me           - 获取当前用户信息")
    print("  PUT    /api/users/me           - 更新当前用户信息")
    print("  GET    /api/users/{id}         - 获取指定用户信息")
    print("  PUT    /api/users/{id}         - 更新指定用户信息")
    print("  DELETE /api/users/{id}         - 删除指定用户")
    print("  GET    /api/users/search/users - 搜索用户")
    print("  POST   /api/users/me/change-password - 修改密码")
    print("  POST   /api/users/me/avatar    - 上传头像")
    
    print("\n========== 前端使用说明 ==========")
    print("1. 前端已编译成功，可以访问:")
    print("   - 主页: http://localhost:8000/")
    print("   - 设置页面: http://localhost:8000/#/settings")
    print("")
    print("2. 用户管理功能位置:")
    print("   - 进入设置页面")
    print("   - 点击'用户配置'标签页")
    print("   - 在'用户列表管理'部分可以:")
    print("     * 查看所有用户")
    print("     * 搜索用户")
    print("     * 新增用户")
    print("     * 编辑用户信息")
    print("     * 删除用户")
    print("")
    print("3. 所有用户相关API已整理到:")
    print("   - 文件: fr/src/api/user.js")
    print("   - 路径: 统一使用 /api/users（无v1前缀）")
    print("   - 认证: 所有API都需要Bearer Token认证")
    
    print("\n========== 测试完成 ==========")

if __name__ == "__main__":
    test_user_management_api()
