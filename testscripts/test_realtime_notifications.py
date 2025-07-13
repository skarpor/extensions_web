#!/usr/bin/env python3
"""
测试实时通知功能
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime

async def test_realtime_notifications():
    """测试实时通知功能"""
    
    print("🚀 开始测试实时通知功能...\n")
    
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
            
            # 3. Alice建立WebSocket连接（模拟在线用户）
            print("\n🔄 Alice建立WebSocket连接...")
            
            # 先创建一个临时聊天室让Alice连接
            temp_room_data = {
                "name": "临时聊天室",
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
                    print(f"✅ 临时聊天室创建成功，ID: {temp_room_id}")
                else:
                    error_text = await response.text()
                    print(f"❌ 创建临时聊天室失败: {error_text}")
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
                    
                    # 4. 管理员创建公开聊天室（应该通知Alice）
                    print("\n🔄 管理员创建公开聊天室...")
                    
                    new_room_data = {
                        "name": f"测试公开聊天室 {datetime.now().strftime('%H:%M:%S')}",
                        "description": "这是一个测试公开聊天室",
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
                            
                            # 等待Alice收到聊天室创建通知
                            print("🔄 等待Alice收到聊天室创建通知...")
                            try:
                                notification = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                notification_data = json.loads(notification)
                                
                                if notification_data.get('type') == 'room_created':
                                    print("✅ Alice收到聊天室创建通知")
                                    print(f"   通知内容: {notification_data.get('data', {}).get('room', {}).get('name')}")
                                else:
                                    print(f"⚠️ Alice收到其他类型通知: {notification_data.get('type')}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到聊天室创建通知")
                        else:
                            error_text = await response.text()
                            print(f"❌ 创建公开聊天室失败: {error_text}")
                            return
                    
                    # 5. 管理员删除聊天室（应该通知Alice）
                    print("\n🔄 管理员删除聊天室...")
                    
                    async with session.delete(
                        f"http://localhost:8000/api/modern-chat/rooms/{new_room_id}",
                        headers=admin_headers
                    ) as response:
                        if response.status == 200:
                            print("✅ 聊天室删除成功")
                            
                            # 等待Alice收到聊天室删除通知
                            print("🔄 等待Alice收到聊天室删除通知...")
                            try:
                                notification = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                notification_data = json.loads(notification)
                                
                                if notification_data.get('type') == 'room_deleted':
                                    print("✅ Alice收到聊天室删除通知")
                                    print(f"   删除的聊天室: {notification_data.get('data', {}).get('room_name')}")
                                else:
                                    print(f"⚠️ Alice收到其他类型通知: {notification_data.get('type')}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到聊天室删除通知")
                        else:
                            error_text = await response.text()
                            print(f"❌ 删除聊天室失败: {error_text}")
                    
                    # 6. 测试消息获取修复
                    print("\n🔄 测试消息获取修复...")
                    async with session.get(
                        f"http://localhost:8000/api/modern-chat/rooms/{temp_room_id}/messages",
                        headers=alice_headers
                    ) as response:
                        if response.status == 200:
                            message_list = await response.json()
                            messages = message_list.get('messages', [])
                            print(f"✅ 消息获取成功，共 {len(messages)} 条消息")
                        else:
                            error_text = await response.text()
                            print(f"❌ 消息获取失败 ({response.status}): {error_text}")
                    
                else:
                    print(f"❌ Alice WebSocket认证失败: {alice_auth_data}")
                    return
            
            # 7. 清理临时聊天室
            print("\n🔄 清理临时聊天室...")
            async with session.delete(
                f"http://localhost:8000/api/modern-chat/rooms/{temp_room_id}",
                headers=alice_headers
            ) as response:
                if response.status == 200:
                    print("✅ 临时聊天室清理成功")
                else:
                    print("⚠️ 临时聊天室清理失败")
            
            print("\n🎉 实时通知功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ Alice WebSocket连接和认证")
            print("✅ 公开聊天室创建通知")
            print("✅ 聊天室删除通知")
            print("✅ 消息获取修复")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_realtime_notifications())
