#!/usr/bin/env python3
"""
测试聊天室详情API修复
"""

import asyncio
import aiohttp

async def test_room_details_fix():
    """测试聊天室详情API修复"""
    
    print("🚀 测试聊天室详情API修复...\n")
    
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
            
            # 2. 创建测试聊天室
            print("\n🔄 创建测试聊天室...")
            room_data = {
                "name": "详情测试聊天室",
                "description": "用于测试聊天室详情API",
                "room_type": "group",
                "is_public": False,
                "max_members": 100,
                "allow_search": True,
                "enable_invite_code": True
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 聊天室创建成功: {room.get('name')} (ID: {room.get('id')})")
                    room_id = room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败: {error_text}")
                    return
            
            # 3. 测试获取聊天室详情
            print(f"\n🔄 测试获取聊天室详情...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room_details = await response.json()
                    print(f"✅ 聊天室详情获取成功")
                    print(f"   聊天室名称: {room_details.get('name')}")
                    print(f"   聊天室描述: {room_details.get('description')}")
                    print(f"   成员数量: {room_details.get('member_count')}")
                    print(f"   创建者: {room_details.get('creator', {}).get('username')}")
                    
                    members = room_details.get('members', [])
                    print(f"   成员列表 ({len(members)} 个):")
                    for member in members:
                        print(f"     - {member.get('username')} ({member.get('role')}) {'[禁言]' if member.get('is_muted') else ''}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室详情失败 ({response.status}): {error_text}")
            
            # 4. 测试获取聊天室列表
            print(f"\n🔄 测试获取聊天室列表...")
            async with session.get(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    print(f"✅ 聊天室列表获取成功，共 {len(rooms)} 个聊天室")
                    for room in rooms:
                        print(f"   - {room.get('name')} (成员数: {room.get('member_count')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室列表失败: {error_text}")
            
            # 5. 测试获取成员列表
            print(f"\n🔄 测试获取成员列表...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    members = await response.json()
                    print(f"✅ 成员列表获取成功，共 {len(members)} 个成员")
                    for member in members:
                        print(f"   - {member.get('username')} ({member.get('role')}) {'[禁言]' if member.get('is_muted') else ''}")
                        print(f"     加入时间: {member.get('joined_at')}")
                        print(f"     邮箱: {member.get('email', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取成员列表失败: {error_text}")
            
            print("\n🎉 聊天室详情API修复测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_room_details_fix())
