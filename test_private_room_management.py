#!/usr/bin/env python3
"""
测试私密聊天室管理功能：踢人、邀人、禁言、退出群聊等
"""

import asyncio
import aiohttp

async def test_private_room_management():
    """测试私密聊天室管理功能"""
    
    print("🚀 测试私密聊天室管理功能：踢人、邀人、禁言、退出群聊等...\n")
    
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
            
            # 2. tyy用户登录
            print("\n🔄 tyy用户登录...")
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login-json",
                json={"username": "tyy", "password": "123"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    login_data = await response.json()
                    print(f"✅ tyy用户登录成功")
                    tyy_token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ tyy用户登录失败: {error_text}")
                    return
            
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            tyy_headers = {"Authorization": f"Bearer {tyy_token}"}
            
            # 3. 创建私密聊天室
            print("\n🔄 创建私密聊天室...")
            room_data = {
                "name": "私密管理测试群",
                "description": "用于测试私密聊天室管理功能",
                "room_type": "group",
                "is_public": False,
                "max_members": 100,
                "allow_search": True,
                "enable_invite_code": True,
                "allow_member_invite": True
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 私密聊天室创建成功: {room.get('name')} (ID: {room.get('id')})")
                    room_id = room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败: {error_text}")
                    return
            
            # 4. 测试邀请用户功能
            print(f"\n🔄 测试邀请用户功能...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members/invite",
                json={"user_id": 2},  # tyy的用户ID
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 邀请用户成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 邀请用户失败: {error_text}")
            
            # 5. 测试获取成员列表
            print(f"\n🔄 测试获取成员列表...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    members = await response.json()
                    print(f"✅ 成功获取成员列表，共 {len(members)} 个成员")
                    for member in members:
                        print(f"   - {member.get('username')} ({member.get('role')}) {'[禁言]' if member.get('is_muted') else ''}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取成员列表失败: {error_text}")
            
            # 6. 测试禁言功能
            print(f"\n🔄 测试禁言功能...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members/2/mute",
                json={"is_muted": True, "reason": "测试禁言功能"},
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 禁言成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 禁言失败: {error_text}")
            
            # 7. 测试设置管理员功能
            print(f"\n🔄 测试设置管理员功能...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members/2/role",
                json={"role": "admin"},
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 设置管理员成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 设置管理员失败: {error_text}")
            
            # 8. 测试取消禁言功能
            print(f"\n🔄 测试取消禁言功能...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members/2/mute",
                json={"is_muted": False},
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 取消禁言成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 取消禁言失败: {error_text}")
            
            # 9. 测试踢出成员功能
            print(f"\n🔄 测试踢出成员功能...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members/2/kick",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 踢出成员成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 踢出成员失败: {error_text}")
            
            # 10. 重新邀请用户用于测试退出功能
            print(f"\n🔄 重新邀请用户用于测试退出功能...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members/invite",
                json={"user_id": 2},
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    print(f"✅ 重新邀请成功")
                else:
                    error_text = await response.text()
                    print(f"❌ 重新邀请失败: {error_text}")
            
            # 11. 测试用户退出聊天室
            print(f"\n🔄 测试用户退出聊天室...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/leave",
                headers=tyy_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 用户退出成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 用户退出失败: {error_text}")
            
            # 12. 测试群主解散群聊
            print(f"\n🔄 测试群主解散群聊...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/leave",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 群聊解散成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 群聊解散失败: {error_text}")
            
            print("\n🎉 私密聊天室管理功能测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_private_room_management())
