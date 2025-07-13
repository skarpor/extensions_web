#!/usr/bin/env python3
"""
测试完整功能：创建聊天室、权限验证、成员管理、消息置顶
"""

import asyncio
import aiohttp

async def test_complete_features():
    """测试完整功能"""
    
    print("🚀 测试完整功能：创建聊天室、权限验证、成员管理、消息置顶...\n")
    
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
                "name": "功能测试聊天室",
                "description": "用于测试各种功能的聊天室",
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
            
            # 3. 测试成员管理 - 获取成员列表
            print(f"\n🔄 测试成员管理 - 获取成员列表...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/members",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    members = await response.json()
                    print(f"✅ 成功获取成员列表，共 {len(members)} 个成员")
                    for member in members:
                        print(f"   - {member.get('username')} ({member.get('role')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取成员列表失败: {error_text}")
            
            # 4. 测试发送消息
            print(f"\n🔄 测试发送消息...")
            message_data = {
                "content": "这是一条测试消息，用于测试置顶功能",
                "message_type": "text"
            }
            
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages",
                json=message_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    message = await response.json()
                    print(f"✅ 消息发送成功")
                    message_id = message.get('id')
                    print(f"   消息ID: {message_id}")
                    print(f"   消息内容: {message.get('content')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 消息发送失败: {error_text}")
                    return
            
            # 5. 测试消息置顶功能
            print(f"\n🔄 测试消息置顶功能...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages/{message_id}/pin",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 消息置顶成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 消息置顶失败: {error_text}")
            
            # 6. 测试获取置顶消息列表
            print(f"\n🔄 测试获取置顶消息列表...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/pinned-messages",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    pinned_messages = await response.json()
                    print(f"✅ 成功获取置顶消息，共 {len(pinned_messages)} 条")
                    for msg in pinned_messages:
                        print(f"   - {msg.get('content')[:50]}... (置顶时间: {msg.get('pinned_at')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取置顶消息失败: {error_text}")
            
            # 7. 测试取消置顶
            print(f"\n🔄 测试取消置顶...")
            async with session.delete(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages/{message_id}/pin",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 取消置顶成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 取消置顶失败: {error_text}")
            
            # 8. 测试搜索功能
            print(f"\n🔄 测试搜索功能...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/search-rooms?q=功能测试",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"✅ 搜索成功，找到 {len(search_results)} 个聊天室")
                    for room in search_results:
                        print(f"   - {room.get('name')} (成员数: {room.get('member_count')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 搜索失败: {error_text}")
            
            print("\n🎉 完整功能测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_complete_features())
