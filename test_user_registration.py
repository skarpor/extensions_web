#!/usr/bin/env python3
"""
测试用户注册和权限分配功能
"""

import asyncio
import aiohttp
import json

async def test_user_registration():
    """测试用户注册功能"""
    
    # 测试用户数据
    test_user = {
        "username": f"testuser_{asyncio.get_event_loop().time():.0f}",
        "email": f"test_{asyncio.get_event_loop().time():.0f}@example.com",
        "password": "testpassword123",
        "nickname": "测试用户"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 测试用户注册
            print("🔄 测试用户注册...")
            async with session.post(
                "http://localhost:8000/api/auth/register",
                json=test_user,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    print(f"✅ 用户注册成功: {user_data.get('username')}")
                    user_id = user_data.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 用户注册失败 ({response.status}): {error_text}")
                    return
            
            # 2. 测试用户登录
            print("🔄 测试用户登录...")
            login_data = {
                "username": test_user["username"],
                "password": test_user["password"]
            }
            
            async with session.post(
                "http://localhost:8000/api/auth/login",
                data=login_data,  # 使用 form data
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    print(f"✅ 用户登录成功")
                    access_token = login_result.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 用户登录失败 ({response.status}): {error_text}")
                    return
            
            # 3. 测试获取用户角色
            print("🔄 测试获取用户角色...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with session.get(
                f"http://localhost:8000/api/auth/users/{user_id}/roles",
                headers=headers
            ) as response:
                if response.status == 200:
                    user_roles = await response.json()
                    print(f"✅ 获取用户角色成功:")
                    print(f"   用户ID: {user_roles.get('id')}")
                    print(f"   用户名: {user_roles.get('username')}")
                    roles = user_roles.get('roles', [])
                    print(f"   角色数量: {len(roles)}")
                    for role in roles:
                        print(f"   - 角色: {role.get('name')} ({role.get('description')})")
                        permissions = role.get('permissions', [])
                        print(f"     权限数量: {len(permissions)}")
                        for perm in permissions[:5]:  # 只显示前5个权限
                            print(f"     - {perm.get('code')}: {perm.get('name')}")
                        if len(permissions) > 5:
                            print(f"     - ... 还有 {len(permissions) - 5} 个权限")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取用户角色失败 ({response.status}): {error_text}")
            
            # 4. 测试权限验证 - 尝试访问需要权限的接口
            print("🔄 测试权限验证...")
            
            # 测试文件查看权限 (普通用户应该有这个权限)
            async with session.get(
                "http://localhost:8000/api/v1/files/",
                headers=headers
            ) as response:
                if response.status == 200:
                    print("✅ 文件查看权限验证通过")
                elif response.status == 403:
                    print("❌ 文件查看权限验证失败 - 权限不足")
                else:
                    print(f"⚠️ 文件查看权限验证异常 ({response.status})")

            # 测试角色管理权限 (普通用户应该没有这个权限)
            async with session.get(
                "http://localhost:8000/api/auth/roles",
                headers=headers
            ) as response:
                if response.status == 403:
                    print("✅ 角色管理权限验证正确 - 普通用户被正确拒绝")
                elif response.status == 200:
                    print("❌ 角色管理权限验证失败 - 普通用户不应该有此权限")
                else:
                    print(f"⚠️ 角色管理权限验证异常 ({response.status})")
            
            print("\n🎉 用户注册和权限分配测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    print("🚀 开始测试用户注册和权限分配功能...\n")
    asyncio.run(test_user_registration())
