#!/usr/bin/env python3
"""
检查前端用户权限
"""

import asyncio
import aiohttp
import json

async def check_frontend_user_permissions():
    """检查前端用户权限"""
    
    print("🚀 开始检查前端用户权限...\n")
    
    # 测试不同用户的权限
    test_users = [
        {"username": "admin", "password": "123"},
        {"username": "tyy", "password": "123"}  # 如果有其他测试用户
    ]
    
    async with aiohttp.ClientSession() as session:
        for user_creds in test_users:
            try:
                print(f"🔄 检查用户 {user_creds['username']} 的权限...")
                
                # 1. 用户登录
                async with session.post(
                    "http://localhost:8000/api/auth/login",
                    data=user_creds,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    if response.status == 200:
                        login_data = await response.json()
                        print(f"✅ 用户 {user_creds['username']} 登录成功")
                        token = login_data.get('access_token')
                    else:
                        error_text = await response.text()
                        print(f"❌ 用户 {user_creds['username']} 登录失败: {error_text}")
                        continue
                
                headers = {"Authorization": f"Bearer {token}"}
                
                # 2. 检查用户信息和权限
                async with session.get(
                    "http://localhost:8000/api/auth/me",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        user_info = await response.json()
                        print(f"   用户ID: {user_info.get('id')}")
                        print(f"   用户名: {user_info.get('username')}")
                        print(f"   权限组: {user_info.get('permission_groups', [])}")
                        
                        permissions = user_info.get('permissions', [])
                        chat_permissions = [p for p in permissions if 'chat:' in p]
                        print(f"   聊天权限: {chat_permissions}")
                        
                        if not chat_permissions:
                            print(f"   ⚠️  用户 {user_creds['username']} 没有聊天权限！")
                    else:
                        error_text = await response.text()
                        print(f"❌ 获取用户信息失败: {error_text}")
                        continue
                
                # 3. 测试获取聊天室列表
                async with session.get(
                    "http://localhost:8000/api/modern-chat/rooms",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        rooms = await response.json()
                        print(f"   ✅ 可以获取聊天室列表，共 {len(rooms)} 个聊天室")
                        
                        # 找到公开聊天室
                        public_rooms = [r for r in rooms if r.get('room_type') == 'public']
                        if public_rooms:
                            public_room = public_rooms[0]
                            print(f"   找到公开聊天室: {public_room.get('name')} (ID: {public_room.get('id')})")
                            
                            # 4. 测试发送消息到公开聊天室
                            message_data = {
                                "content": f"来自用户 {user_creds['username']} 的测试消息",
                                "message_type": "text"
                            }
                            
                            async with session.post(
                                f"http://localhost:8000/api/modern-chat/rooms/{public_room['id']}/messages",
                                json=message_data,
                                headers=headers
                            ) as response:
                                if response.status == 200:
                                    message = await response.json()
                                    print(f"   ✅ 消息发送成功: {message.get('content')}")
                                else:
                                    error_text = await response.text()
                                    print(f"   ❌ 消息发送失败 ({response.status}): {error_text}")
                                    
                                    # 尝试解析错误详情
                                    try:
                                        error_data = json.loads(error_text)
                                        print(f"   错误详情: {error_data}")
                                    except:
                                        pass
                        else:
                            print("   ⚠️  没有找到公开聊天室")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ 获取聊天室列表失败 ({response.status}): {error_text}")
                
                print()  # 空行分隔
                
            except Exception as e:
                print(f"❌ 检查用户 {user_creds['username']} 时发生错误: {e}")
                print()
    
    print("🎉 前端用户权限检查完成!")

if __name__ == "__main__":
    asyncio.run(check_frontend_user_permissions())
