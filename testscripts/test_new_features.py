#!/usr/bin/env python3
"""
测试新功能：权限验证、成员管理、消息置顶
"""

import asyncio
import aiohttp

async def test_new_features():
    """测试新功能"""
    
    print("🚀 测试新功能：权限验证、成员管理、消息置顶...\n")
    
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
            
            # 2. 测试权限验证 - 获取聊天室列表
            print("\n🔄 测试权限验证 - 获取聊天室列表...")
            async with session.get(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    print(f"✅ 权限验证通过，获取到 {len(rooms)} 个聊天室")
                    if rooms:
                        test_room = rooms[0]
                        room_id = test_room.get('id')
                        print(f"   测试聊天室: {test_room.get('name')} (ID: {room_id})")
                else:
                    error_text = await response.text()
                    print(f"❌ 权限验证失败: {error_text}")
                    return
            
            # 3. 测试成员管理 - 获取成员列表
            if room_id:
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
            if room_id:
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
            if room_id and message_id:
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
            
            # 8. 测试无权限用户访问
            print(f"\n🔄 测试无权限访问...")
            async with session.get(
                "http://192.168.3.139:8000/api/modern-chat/rooms"
            ) as response:
                if response.status == 401:
                    print(f"✅ 权限验证正常，未授权用户被正确拒绝")
                else:
                    print(f"❌ 权限验证异常，状态码: {response.status}")
            
            print("\n🎉 新功能测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_new_features())
