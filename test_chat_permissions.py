#!/usr/bin/env python3
"""
测试聊天权限和消息发送功能
"""

import asyncio
import aiohttp
import json

async def test_chat_permissions():
    """测试聊天权限和消息发送"""
    
    print("🚀 开始测试聊天权限和消息发送功能...\n")
    
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
            
            # 2. 检查用户权限
            print("\n🔄 检查用户权限...")
            async with session.get(
                "http://localhost:8000/api/auth/me",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    print(f"✅ 用户信息获取成功")
                    print(f"   用户名: {user_info.get('username')}")
                    print(f"   权限组: {user_info.get('permission_groups', [])}")
                    
                    # 检查是否有聊天权限
                    permissions = user_info.get('permissions', [])
                    chat_permissions = [p for p in permissions if 'chat:' in p]
                    print(f"   聊天权限: {chat_permissions}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取用户信息失败 ({response.status}): {error_text}")
                    return
            
            # 3. 获取聊天室列表
            print("\n🔄 获取聊天室列表...")
            async with session.get(
                "http://localhost:8000/api/modern-chat/rooms",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    print(f"✅ 聊天室列表获取成功，共 {len(rooms)} 个聊天室")
                    
                    if rooms:
                        test_room = rooms[0]
                        print(f"   测试聊天室: {test_room.get('name')} (ID: {test_room.get('id')})")
                        
                        # 4. 测试发送消息
                        print("\n🔄 测试发送消息...")
                        message_data = {
                            "content": "这是一条测试消息",
                            "message_type": "text"
                        }
                        
                        async with session.post(
                            f"http://localhost:8000/api/modern-chat/rooms/{test_room['id']}/messages",
                            json=message_data,
                            headers=admin_headers
                        ) as response:
                            if response.status == 200:
                                message = await response.json()
                                print(f"✅ 消息发送成功")
                                print(f"   消息ID: {message.get('id')}")
                                print(f"   消息内容: {message.get('content')}")
                                print(f"   发送时间: {message.get('created_at')}")
                            else:
                                error_text = await response.text()
                                print(f"❌ 消息发送失败 ({response.status}): {error_text}")
                                
                                # 尝试解析错误详情
                                try:
                                    error_data = json.loads(error_text)
                                    print(f"   错误详情: {error_data}")
                                except:
                                    pass
                        
                        # 5. 获取聊天室消息
                        print("\n🔄 获取聊天室消息...")
                        async with session.get(
                            f"http://localhost:8000/api/modern-chat/rooms/{test_room['id']}/messages",
                            headers=admin_headers
                        ) as response:
                            if response.status == 200:
                                messages = await response.json()
                                print(f"✅ 消息列表获取成功，共 {len(messages)} 条消息")
                                
                                if messages:
                                    latest_message = messages[-1]
                                    print(f"   最新消息: {latest_message.get('content')}")
                                    print(f"   发送者: {latest_message.get('sender', {}).get('username')}")
                            else:
                                error_text = await response.text()
                                print(f"❌ 获取消息列表失败 ({response.status}): {error_text}")
                    else:
                        print("   没有可用的聊天室进行测试")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室列表失败 ({response.status}): {error_text}")
            
            print("\n🎉 聊天权限和消息发送测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_permissions())
