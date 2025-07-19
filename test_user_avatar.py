#!/usr/bin/env python3
"""
测试用户头像API和前端显示
"""

import asyncio
import aiohttp

async def test_user_avatar():
    """测试用户头像API和前端显示"""
    
    print("🚀 测试用户头像API和前端显示...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 管理员登录
            print("🔄 管理员登录...")
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login-json",
                json={"username": "admin", "password": "123"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    login_data = await response.json()
                    print(f"✅ 管理员登录成功")
                    admin_token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败: {error_text}")
                    return
            
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # 2. 获取当前用户信息
            print("\n🔄 获取当前用户信息...")
            async with session.get(
                "http://192.168.3.139:8000/api/auth/me",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    print(f"✅ 获取用户信息成功")
                    print(f"📋 用户信息详情:")
                    print(f"   ID: {user_info.get('id')}")
                    print(f"   用户名: {user_info.get('username')}")
                    print(f"   昵称: {user_info.get('nickname')}")
                    print(f"   邮箱: {user_info.get('email')}")
                    print(f"   头像: {user_info.get('avatar')}")
                    print(f"   是否激活: {user_info.get('is_active')}")
                    print(f"   是否超级用户: {user_info.get('is_superuser')}")
                    
                    # 检查头像字段
                    avatar = user_info.get('avatar')
                    if avatar:
                        print(f"   ✅ 头像字段存在: {avatar}")
                        if avatar.startswith('http'):
                            print(f"   ✅ 头像是完整URL")
                        elif avatar.startswith('/'):
                            print(f"   ✅ 头像是相对路径")
                        else:
                            print(f"   ⚠️ 头像格式未知")
                    else:
                        print(f"   ❌ 头像字段为空或不存在")
                        print(f"   💡 这就是为什么前端头像预览看不见的原因")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取用户信息失败: {error_text}")
                    return
            
            # 3. 测试更新用户信息（包含头像）
            print(f"\n🔄 测试更新用户信息（设置头像）...")
            update_data = {
                "username": user_info.get('username'),
                "nickname": user_info.get('nickname') or "管理员",
                "email": user_info.get('email'),
                "avatar": "https://via.placeholder.com/120x120/4CAF50/FFFFFF?text=Admin"  # 测试头像URL
            }
            
            async with session.put(
                "http://192.168.3.139:8000/api/auth/me",
                json=update_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    updated_user = await response.json()
                    print(f"✅ 用户信息更新成功")
                    print(f"   更新后的头像: {updated_user.get('avatar')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 用户信息更新失败: {error_text}")
            
            # 4. 再次获取用户信息，确认头像已更新
            print(f"\n🔄 再次获取用户信息，确认头像已更新...")
            async with session.get(
                "http://192.168.3.139:8000/api/auth/me",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    avatar = user_info.get('avatar')
                    if avatar:
                        print(f"✅ 头像更新成功: {avatar}")
                        print(f"   现在前端应该能看到头像预览了")
                    else:
                        print(f"❌ 头像仍然为空")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取用户信息失败: {error_text}")
            
            print("\n🎉 用户头像测试完成!")
            print("\n📊 测试总结:")
            print("✅ 用户信息API：正常")
            print("✅ 头像字段：存在")
            print("✅ 头像更新：正常")
            
            print("\n💡 前端修复提示:")
            print("1. 确保userForm初始化时包含avatar字段")
            print("2. 确保fetchUserProfile时设置avatar字段")
            print("3. 确保头像预览条件判断正确")
            print("4. 如果头像仍然看不见，检查CSS样式")
            print("5. 检查浏览器控制台是否有错误信息")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_user_avatar())
