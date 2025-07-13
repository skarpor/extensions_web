#!/usr/bin/env python3
"""
创建公开聊天室进行测试
"""

import asyncio
import aiohttp
import json

async def create_public_room():
    """创建公开聊天室"""
    
    print("🚀 开始创建公开聊天室...\n")
    
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
                    admin_login = await response.json()
                    print(f"✅ 管理员登录成功")
                    admin_token = admin_login.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败 ({response.status}): {error_text}")
                    return
            
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # 2. 创建公开聊天室
            print("\n🔄 创建公开聊天室...")
            room_data = {
                "name": "公开测试聊天室",
                "description": "这是一个公开的测试聊天室，所有人都可以参与",
                "room_type": "public",
                "is_public": True,
                "max_members": 1000
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/rooms",
                json=room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 公开聊天室创建成功")
                    print(f"   聊天室名称: {room.get('name')}")
                    print(f"   聊天室ID: {room.get('id')}")
                    print(f"   聊天室类型: {room.get('room_type')}")
                    print(f"   是否公开: {room.get('is_public')}")
                    
                    room_id = room.get('id')
                    
                    # 3. 测试发送消息到公开聊天室
                    print(f"\n🔄 测试发送消息到公开聊天室...")
                    message_data = {
                        "content": "这是第一条测试消息！欢迎大家来到公开聊天室！",
                        "message_type": "text"
                    }
                    
                    async with session.post(
                        f"http://localhost:8000/api/modern-chat/rooms/{room_id}/messages",
                        json=message_data,
                        headers=admin_headers
                    ) as response:
                        if response.status == 200:
                            message = await response.json()
                            print(f"✅ 消息发送成功")
                            print(f"   消息ID: {message.get('id')}")
                            print(f"   消息内容: {message.get('content')}")
                        else:
                            error_text = await response.text()
                            print(f"❌ 消息发送失败 ({response.status}): {error_text}")
                    
                    # 4. 再发送几条测试消息
                    test_messages = [
                        "大家好！👋",
                        "这个聊天室支持实时消息推送",
                        "欢迎大家积极参与讨论！",
                        "如果有问题可以随时提出"
                    ]
                    
                    for i, msg_content in enumerate(test_messages, 1):
                        print(f"\n🔄 发送第{i+1}条测试消息...")
                        message_data = {
                            "content": msg_content,
                            "message_type": "text"
                        }
                        
                        async with session.post(
                            f"http://localhost:8000/api/modern-chat/rooms/{room_id}/messages",
                            json=message_data,
                            headers=admin_headers
                        ) as response:
                            if response.status == 200:
                                print(f"✅ 消息发送成功: {msg_content}")
                            else:
                                error_text = await response.text()
                                print(f"❌ 消息发送失败: {error_text}")
                        
                        # 稍微延迟一下
                        await asyncio.sleep(0.5)
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败 ({response.status}): {error_text}")
                    try:
                        error_data = json.loads(error_text)
                        print(f"   错误详情: {error_data}")
                    except:
                        pass
            
            print("\n🎉 公开聊天室创建和测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(create_public_room())
