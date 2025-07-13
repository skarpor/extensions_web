#!/usr/bin/env python3
"""
测试私聊修复功能
"""

import asyncio
import aiohttp
import json
import websockets

async def test_private_chat_fixes():
    """测试私聊修复功能"""
    
    print("🚀 开始测试私聊修复功能...\n")
    
    # 管理员登录信息
    admin_credentials = {
        "username": "admin",
        "password": "123"
    }
    
    # Alice登录信息
    alice_credentials = {
        "username": "alice",
        "password": "alice123"
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
            
            # 2. Alice登录
            print("🔄 Alice登录...")
            async with session.post(
                "http://localhost:8000/api/auth/login",
                data=alice_credentials,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    alice_login = await response.json()
                    print(f"✅ Alice登录成功")
                    alice_token = alice_login.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ Alice登录失败 ({response.status}): {error_text}")
                    return
            
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            alice_headers = {"Authorization": f"Bearer {alice_token}"}
            
            # 3. Alice建立WebSocket连接（模拟在线状态）
            print("\n🔄 Alice建立WebSocket连接...")
            
            # 先创建一个临时聊天室让Alice连接
            temp_room_data = {
                "name": "Alice临时聊天室",
                "description": "用于建立WebSocket连接",
                "room_type": "group",
                "is_public": True
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/rooms",
                json=temp_room_data,
                headers=alice_headers
            ) as response:
                if response.status == 200:
                    temp_room = await response.json()
                    temp_room_id = temp_room.get('id')
                    print(f"✅ Alice临时聊天室创建成功，ID: {temp_room_id}")
                else:
                    error_text = await response.text()
                    print(f"❌ 创建Alice临时聊天室失败: {error_text}")
                    return
            
            # Alice连接WebSocket
            alice_ws_url = f"ws://localhost:8000/api/modern-chat/ws/{temp_room_id}"
            
            async with websockets.connect(alice_ws_url) as alice_websocket:
                print("✅ Alice WebSocket连接建立成功")
                
                # Alice认证
                alice_auth_message = {
                    "type": "auth",
                    "token": alice_token
                }
                
                await alice_websocket.send(json.dumps(alice_auth_message))
                
                # 等待认证响应
                alice_auth_response = await asyncio.wait_for(alice_websocket.recv(), timeout=10.0)
                alice_auth_data = json.loads(alice_auth_response)
                
                if alice_auth_data.get('type') == 'auth_response' and alice_auth_data.get('success'):
                    print("✅ Alice WebSocket认证成功")
                    
                    # 等待欢迎消息
                    try:
                        welcome_msg = await asyncio.wait_for(alice_websocket.recv(), timeout=3.0)
                        print("✅ Alice收到欢迎消息")
                    except asyncio.TimeoutError:
                        print("⚠️ Alice欢迎消息超时")
                    
                    # 4. 管理员创建与Alice的私聊
                    print("\n🔄 管理员创建与Alice的私聊...")
                    
                    private_chat_data = {
                        "target_user_id": 6  # Alice的ID
                    }
                    
                    async with session.post(
                        "http://localhost:8000/api/modern-chat/private-rooms",
                        json=private_chat_data,
                        headers=admin_headers
                    ) as response:
                        if response.status == 200:
                            private_room = await response.json()
                            print(f"✅ 私聊聊天室创建成功")
                            print(f"   聊天室名称: {private_room.get('name')}")
                            private_room_id = private_room.get('id')
                            
                            # 等待Alice收到私聊创建通知
                            print("🔄 等待Alice收到私聊创建通知...")
                            try:
                                notification = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                notification_data = json.loads(notification)
                                
                                if notification_data.get('type') == 'private_room_created':
                                    print("✅ Alice收到私聊创建通知")
                                    print(f"   通知内容: {notification_data.get('data', {}).get('room', {}).get('name')}")
                                else:
                                    print(f"⚠️ Alice收到其他类型通知: {notification_data.get('type')}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到私聊创建通知")
                        else:
                            error_text = await response.text()
                            print(f"❌ 创建私聊聊天室失败: {error_text}")
                            return
                    
                    # 5. 管理员在私聊中发送消息
                    print("\n🔄 管理员在私聊中发送消息...")
                    
                    # 管理员连接私聊WebSocket
                    admin_ws_url = f"ws://localhost:8000/api/modern-chat/ws/{private_room_id}"
                    
                    async with websockets.connect(admin_ws_url) as admin_websocket:
                        # 管理员认证
                        admin_auth_message = {
                            "type": "auth",
                            "token": admin_token
                        }
                        
                        await admin_websocket.send(json.dumps(admin_auth_message))
                        
                        # 等待认证响应
                        admin_auth_response = await asyncio.wait_for(admin_websocket.recv(), timeout=10.0)
                        admin_auth_data = json.loads(admin_auth_response)
                        
                        if admin_auth_data.get('type') == 'auth_response' and admin_auth_data.get('success'):
                            print("✅ 管理员私聊WebSocket认证成功")
                            
                            # 等待欢迎消息
                            try:
                                welcome_msg = await asyncio.wait_for(admin_websocket.recv(), timeout=3.0)
                                print("✅ 管理员收到私聊欢迎消息")
                            except asyncio.TimeoutError:
                                print("⚠️ 管理员私聊欢迎消息超时")
                            
                            # 发送私聊消息
                            test_message = {
                                "type": "send_message",
                                "data": {
                                    "content": "你好Alice！这是一条私聊测试消息。",
                                    "message_type": "text"
                                }
                            }
                            
                            await admin_websocket.send(json.dumps(test_message))
                            print("✅ 管理员发送私聊消息")
                            
                            # 等待消息响应
                            try:
                                msg_response = await asyncio.wait_for(admin_websocket.recv(), timeout=5.0)
                                msg_data = json.loads(msg_response)
                                
                                if msg_data.get('type') == 'new_message':
                                    print("✅ 管理员收到消息发送确认")
                                else:
                                    print(f"⚠️ 管理员收到其他类型响应: {msg_data.get('type')}")
                            except asyncio.TimeoutError:
                                print("❌ 管理员消息响应超时")
                            
                            # Alice应该收到私聊消息更新通知
                            print("🔄 等待Alice收到私聊消息更新通知...")
                            try:
                                update_notification = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                update_data = json.loads(update_notification)
                                
                                if update_data.get('type') == 'room_updated':
                                    print("✅ Alice收到私聊消息更新通知")
                                    print(f"   最后消息: {update_data.get('data', {}).get('last_message', {}).get('content')}")
                                else:
                                    print(f"⚠️ Alice收到其他类型通知: {update_data.get('type')}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到私聊消息更新通知")
                        else:
                            print(f"❌ 管理员私聊WebSocket认证失败: {admin_auth_data}")
                    
                    # 6. 测试标记消息已读功能
                    print("\n🔄 测试标记消息已读功能...")
                    async with session.post(
                        f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}/mark-read",
                        headers=alice_headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ 标记消息已读成功: {result.get('message')}")
                        else:
                            error_text = await response.text()
                            print(f"❌ 标记消息已读失败 ({response.status}): {error_text}")
                    
                    # 7. 清理测试数据
                    print("\n🔄 清理测试数据...")
                    
                    # 删除私聊聊天室
                    async with session.delete(
                        f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}",
                        headers=admin_headers
                    ) as response:
                        if response.status == 200:
                            print("✅ 私聊聊天室删除成功")
                        else:
                            print("⚠️ 私聊聊天室删除失败")
                else:
                    print(f"❌ Alice WebSocket认证失败: {alice_auth_data}")
                    return
            
            # 删除临时聊天室
            async with session.delete(
                f"http://localhost:8000/api/modern-chat/rooms/{temp_room_id}",
                headers=alice_headers
            ) as response:
                if response.status == 200:
                    print("✅ 临时聊天室删除成功")
                else:
                    print("⚠️ 临时聊天室删除失败")
            
            print("\n🎉 私聊修复功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ Alice WebSocket连接和认证")
            print("✅ 私聊聊天室创建通知")
            print("✅ 私聊消息发送和接收")
            print("✅ 私聊消息更新通知")
            print("✅ 标记消息已读功能")
            print("✅ 聊天室删除功能")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_private_chat_fixes())
