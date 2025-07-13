#!/usr/bin/env python3
"""
测试JSON登录端点
"""

import asyncio
import aiohttp

async def test_json_login():
    """测试JSON登录端点"""
    
    print("🚀 测试JSON登录端点...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 测试新的JSON登录端点
            print("🔄 测试JSON登录端点...")
            json_data = {
                "username": "admin",
                "password": "123"
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login-json",
                json=json_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    print(f"✅ JSON登录成功")
                    print(f"   Token: {login_result.get('access_token', 'N/A')[:20]}...")
                    print(f"   用户: {login_result.get('user', {}).get('username', 'N/A')}")
                    token = login_result.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ JSON登录失败 ({response.status}): {error_text}")
                    return
            
            # 2. 测试错误的凭证
            print("\n🔄 测试错误凭证...")
            wrong_data = {
                "username": "admin",
                "password": "wrong_password"
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login-json",
                json=wrong_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 401:
                    print(f"✅ 错误凭证正确被拒绝 (401)")
                else:
                    error_text = await response.text()
                    print(f"❌ 错误凭证处理异常 ({response.status}): {error_text}")
            
            # 3. 测试使用token访问API
            if token:
                print("\n🔄 测试使用token访问API...")
                headers = {"Authorization": f"Bearer {token}"}
                
                async with session.get(
                    "http://192.168.3.139:8000/api/auth/me",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        user_info = await response.json()
                        print(f"✅ 获取用户信息成功")
                        print(f"   用户名: {user_info.get('username')}")
                        print(f"   用户ID: {user_info.get('id')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 获取用户信息失败 ({response.status}): {error_text}")
            
            # 4. 测试聊天室API
            if token:
                print("\n🔄 测试聊天室API...")
                headers = {"Authorization": f"Bearer {token}"}
                
                async with session.get(
                    "http://192.168.3.139:8000/api/modern-chat/rooms",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        rooms = await response.json()
                        print(f"✅ 获取聊天室列表成功，共 {len(rooms)} 个聊天室")
                    else:
                        error_text = await response.text()
                        print(f"❌ 获取聊天室列表失败 ({response.status}): {error_text}")
            
            print("\n🎉 JSON登录测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_json_login())
