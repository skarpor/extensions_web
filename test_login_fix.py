#!/usr/bin/env python3
"""
测试登录修复
"""

import asyncio
import aiohttp

async def test_login_fix():
    """测试登录修复"""
    
    print("🚀 测试登录修复...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 测试JSON格式登录（应该失败）
            print("🔄 测试JSON格式登录（应该失败）...")
            json_data = {
                "username": "admin",
                "password": "123"
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login",
                json=json_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    print(f"❌ JSON格式登录意外成功")
                else:
                    print(f"✅ JSON格式登录正确失败 ({response.status})")
            
            # 2. 测试表单格式登录（应该成功）
            print("\n🔄 测试表单格式登录（应该成功）...")
            form_data = aiohttp.FormData()
            form_data.add_field('username', 'admin')
            form_data.add_field('password', '123')
            
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login",
                data=form_data
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    print(f"✅ 表单格式登录成功")
                    print(f"   Token: {login_result.get('access_token', 'N/A')[:20]}...")
                    print(f"   Token类型: {login_result.get('token_type', 'N/A')}")
                    token = login_result.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 表单格式登录失败 ({response.status}): {error_text}")
                    return
            
            # 3. 测试URLSearchParams格式登录（模拟前端修复后的格式）
            print("\n🔄 测试URLSearchParams格式登录...")
            params_data = "username=admin&password=123"
            
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login",
                data=params_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    print(f"✅ URLSearchParams格式登录成功")
                    print(f"   Token: {login_result.get('access_token', 'N/A')[:20]}...")
                else:
                    error_text = await response.text()
                    print(f"❌ URLSearchParams格式登录失败 ({response.status}): {error_text}")
            
            # 4. 测试使用token访问受保护的API
            if token:
                print("\n🔄 测试使用token访问受保护的API...")
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
            
            print("\n🎉 登录修复测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_login_fix())
