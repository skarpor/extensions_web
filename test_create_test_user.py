#!/usr/bin/env python3
"""
创建测试用户
"""

import asyncio
import aiohttp

async def create_test_user():
    """创建测试用户"""
    
    print("🚀 开始创建测试用户...\n")
    
    # 管理员登录信息
    admin_credentials = {
        "username": "admin",
        "password": "123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 管理员登录
            print("🔄 管理员登录...")
            async with session.post(
                "http://localhost:8000/api/auth/login",
                data=admin_credentials,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    print(f"✅ 管理员登录成功")
                    access_token = login_result.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败 ({response.status}): {error_text}")
                    return
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 2. 检查现有用户
            print("\n🔄 检查现有用户...")
            async with session.get(
                "http://localhost:8000/api/users",
                headers=headers
            ) as response:
                if response.status == 200:
                    users = await response.json()
                    print(f"✅ 当前系统中有 {len(users)} 个用户:")
                    for user in users:
                        print(f"   - {user.get('username')} (ID: {user.get('id')}, 昵称: {user.get('nickname', '无')})")
                else:
                    print(f"❌ 获取用户列表失败 ({response.status})")
            
            # 3. 创建测试用户
            test_users = [
                {
                    "username": "testuser1",
                    "email": "test1@example.com",
                    "password": "test123",
                    "nickname": "测试用户1"
                },
                {
                    "username": "testuser2", 
                    "email": "test2@example.com",
                    "password": "test123",
                    "nickname": "测试用户2"
                },
                {
                    "username": "alice",
                    "email": "alice@example.com", 
                    "password": "alice123",
                    "nickname": "爱丽丝"
                },
                {
                    "username": "bob",
                    "email": "bob@example.com",
                    "password": "bob123", 
                    "nickname": "鲍勃"
                }
            ]
            
            print("\n🔄 创建测试用户...")
            created_users = []
            
            for user_data in test_users:
                async with session.post(
                    "http://localhost:8000/api/auth/register",
                    json=user_data
                ) as response:
                    if response.status == 200:
                        new_user = await response.json()
                        print(f"✅ 创建用户成功: {user_data['username']}")
                        created_users.append(new_user)
                    elif response.status == 400:
                        error_data = await response.json()
                        if "already registered" in error_data.get('detail', '').lower():
                            print(f"⚠️ 用户 {user_data['username']} 已存在")
                        else:
                            print(f"❌ 创建用户 {user_data['username']} 失败: {error_data.get('detail')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 创建用户 {user_data['username']} 失败 ({response.status}): {error_text}")
            
            # 4. 再次检查用户列表
            print("\n🔄 检查更新后的用户列表...")
            async with session.get(
                "http://localhost:8000/api/users",
                headers=headers
            ) as response:
                if response.status == 200:
                    users = await response.json()
                    print(f"✅ 现在系统中有 {len(users)} 个用户:")
                    for user in users:
                        print(f"   - {user.get('username')} (ID: {user.get('id')}, 昵称: {user.get('nickname', '无')})")
                else:
                    print(f"❌ 获取用户列表失败 ({response.status})")
            
            # 5. 测试用户搜索
            print("\n🔄 测试用户搜索...")
            search_queries = ["test", "alice", "bob", "用户"]
            
            for query in search_queries:
                async with session.get(
                    f"http://localhost:8000/api/users/search/users?q={query}&limit=5",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        search_results = await response.json()
                        print(f"✅ 搜索 '{query}' 找到 {len(search_results)} 个用户:")
                        for user in search_results:
                            print(f"   - {user.get('username')} ({user.get('nickname', '无昵称')})")
                    else:
                        error_text = await response.text()
                        print(f"❌ 搜索 '{query}' 失败 ({response.status}): {error_text}")
            
            print("\n🎉 测试用户创建完成!")
            
        except Exception as e:
            print(f"❌ 过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user())
