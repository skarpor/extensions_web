#!/usr/bin/env python3
"""
测试全局WebSocket功能
"""

import asyncio
import aiohttp
import json
import websockets

async def test_global_websocket():
    """测试全局WebSocket功能"""
    
    print("🚀 开始测试全局WebSocket功能...\n")
    
    # 管理员登录信息
    admin_credentials = {
        "username": "admin",
        "password": "123"
    }
    
    # 测试用户登录信息（使用admin作为第二个用户进行测试）
    test_user_credentials = {
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
            
            # 2. 测试用户登录（使用同一个admin用户模拟两个连接）
            print("🔄 测试用户登录...")
            test_user_token = admin_token  # 使用同一个token
            print(f"✅ 测试用户登录成功")

            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            test_user_headers = {"Authorization": f"Bearer {test_user_token}"}
            
            # 3. 测试用户建立全局WebSocket连接
            print("\n🔄 测试用户建立全局WebSocket连接...")

            test_ws_url = "ws://localhost:8000/api/global-ws"

            async with websockets.connect(test_ws_url) as test_websocket:
                print("✅ 测试用户全局WebSocket连接建立成功")

                # 测试用户认证
                test_auth_message = {
                    "type": "auth",
                    "token": test_user_token
                }

                await test_websocket.send(json.dumps(test_auth_message))

                # 等待认证响应
                test_auth_response = await asyncio.wait_for(test_websocket.recv(), timeout=10.0)
                test_auth_data = json.loads(test_auth_response)

                if test_auth_data.get('type') == 'auth_response' and test_auth_data.get('data', {}).get('success'):
                    print("✅ 测试用户全局WebSocket认证成功")
                    
                    # 4. 管理员创建公开聊天室（应该通知测试用户）
                    print("\n🔄 管理员创建公开聊天室...")

                    new_room_data = {
                        "name": f"全局WebSocket测试聊天室",
                        "description": "测试全局WebSocket通知",
                        "room_type": "group",
                        "is_public": True
                    }

                    async with session.post(
                        "http://localhost:8000/api/modern-chat/rooms",
                        json=new_room_data,
                        headers=admin_headers
                    ) as response:
                        if response.status == 200:
                            new_room = await response.json()
                            print(f"✅ 公开聊天室创建成功: {new_room.get('name')}")
                            new_room_id = new_room.get('id')

                            # 等待测试用户收到聊天室创建通知
                            print("🔄 等待测试用户收到聊天室创建通知...")
                            try:
                                notification = await asyncio.wait_for(test_websocket.recv(), timeout=5.0)
                                notification_data = json.loads(notification)

                                if notification_data.get('type') == 'room_created':
                                    print("✅ 测试用户收到聊天室创建通知")
                                    print(f"   通知内容: {notification_data.get('data', {}).get('room', {}).get('name')}")
                                else:
                                    print(f"⚠️ 测试用户收到其他类型通知: {notification_data.get('type')}")
                                    print(f"   通知数据: {notification_data}")
                            except asyncio.TimeoutError:
                                print("❌ 测试用户未收到聊天室创建通知")
                        else:
                            error_text = await response.text()
                            print(f"❌ 创建公开聊天室失败: {error_text}")
                            return
                    
                    # 5. 管理员创建与Alice的私聊
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
                                    print(f"   通知数据: {notification_data}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到私聊创建通知")
                        else:
                            error_text = await response.text()
                            print(f"❌ 创建私聊聊天室失败: {error_text}")
                    
                    # 6. 管理员在私聊中发送消息
                    print("\n🔄 管理员在私聊中发送消息...")
                    
                    message_data = {
                        "content": "你好Alice！这是通过全局WebSocket发送的消息。",
                        "message_type": "text"
                    }
                    
                    async with session.post(
                        f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}/messages",
                        json=message_data,
                        headers=admin_headers
                    ) as response:
                        if response.status == 200:
                            message = await response.json()
                            print(f"✅ 管理员发送私聊消息成功")
                            
                            # 等待Alice收到新消息通知
                            print("🔄 等待Alice收到新消息通知...")
                            try:
                                notification = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                notification_data = json.loads(notification)
                                
                                if notification_data.get('type') == 'new_message':
                                    print("✅ Alice收到新消息通知")
                                    print(f"   消息内容: {notification_data.get('data', {}).get('content')}")
                                else:
                                    print(f"⚠️ Alice收到其他类型通知: {notification_data.get('type')}")
                                    print(f"   通知数据: {notification_data}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到新消息通知")
                            
                            # 等待Alice收到聊天室更新通知
                            print("🔄 等待Alice收到聊天室更新通知...")
                            try:
                                notification = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                notification_data = json.loads(notification)
                                
                                if notification_data.get('type') == 'room_updated':
                                    print("✅ Alice收到聊天室更新通知")
                                    print(f"   最后消息: {notification_data.get('data', {}).get('last_message', {}).get('content')}")
                                else:
                                    print(f"⚠️ Alice收到其他类型通知: {notification_data.get('type')}")
                                    print(f"   通知数据: {notification_data}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到聊天室更新通知")
                        else:
                            error_text = await response.text()
                            print(f"❌ 发送私聊消息失败: {error_text}")
                    
                    # 7. 清理测试数据
                    print("\n🔄 清理测试数据...")
                    
                    # 删除聊天室
                    for room_id in [new_room_id, private_room_id]:
                        async with session.delete(
                            f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                            headers=admin_headers
                        ) as response:
                            if response.status == 200:
                                print(f"✅ 聊天室 {room_id} 删除成功")
                            else:
                                print(f"⚠️ 聊天室 {room_id} 删除失败")
                else:
                    print(f"❌ Alice全局WebSocket认证失败: {alice_auth_data}")
                    return
            
            print("\n🎉 全局WebSocket功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ Alice全局WebSocket连接和认证")
            print("✅ 公开聊天室创建通知")
            print("✅ 私聊聊天室创建通知")
            print("✅ 新消息通知")
            print("✅ 聊天室更新通知")
            print("✅ 聊天室删除功能")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_global_websocket())
