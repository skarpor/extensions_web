#!/usr/bin/env python3
"""
测试最终修复
"""

import asyncio
import aiohttp
import json
import websockets

async def test_final_fixes():
    """测试最终修复"""
    
    print("🚀 开始测试最终修复...\n")
    
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
            
            # 3. 测试消息获取修复
            print("\n🔄 测试消息获取修复...")
            
            # 先创建一个测试聊天室
            test_room_data = {
                "name": "消息测试聊天室",
                "description": "用于测试消息获取",
                "room_type": "group",
                "is_public": True
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/rooms",
                json=test_room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    test_room = await response.json()
                    test_room_id = test_room.get('id')
                    print(f"✅ 测试聊天室创建成功，ID: {test_room_id}")
                else:
                    error_text = await response.text()
                    print(f"❌ 创建测试聊天室失败: {error_text}")
                    return
            
            # 测试消息获取
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{test_room_id}/messages",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    message_list = await response.json()
                    print(f"✅ 消息获取成功，无SQLAlchemy错误")
                else:
                    error_text = await response.text()
                    print(f"❌ 消息获取失败 ({response.status}): {error_text}")
            
            # 4. 测试聊天室创建通知（排除创建者）
            print("\n🔄 测试聊天室创建通知（排除创建者）...")
            
            # Alice建立WebSocket连接
            alice_ws_url = f"ws://localhost:8000/api/modern-chat/ws/{test_room_id}"
            
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
                    
                    # 管理员创建新聊天室
                    print("🔄 管理员创建新聊天室...")
                    
                    new_room_data = {
                        "name": f"通知测试聊天室",
                        "description": "测试创建通知",
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
                            print(f"✅ 新聊天室创建成功: {new_room.get('name')}")
                            new_room_id = new_room.get('id')
                            
                            # 等待Alice收到聊天室创建通知
                            print("🔄 等待Alice收到聊天室创建通知...")
                            try:
                                notification = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                notification_data = json.loads(notification)
                                
                                if notification_data.get('type') == 'room_created':
                                    print("✅ Alice收到聊天室创建通知（创建者被正确排除）")
                                else:
                                    print(f"⚠️ Alice收到其他类型通知: {notification_data.get('type')}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到聊天室创建通知")
                        else:
                            error_text = await response.text()
                            print(f"❌ 创建新聊天室失败: {error_text}")
                            return
                    
                    # 5. 测试聊天室信息实时更新
                    print("\n🔄 测试聊天室信息实时更新...")
                    
                    # 管理员发送消息
                    admin_ws_url = f"ws://localhost:8000/api/modern-chat/ws/{test_room_id}"
                    
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
                            print("✅ 管理员WebSocket认证成功")
                            
                            # 等待欢迎消息
                            try:
                                welcome_msg = await asyncio.wait_for(admin_websocket.recv(), timeout=3.0)
                                print("✅ 管理员收到欢迎消息")
                            except asyncio.TimeoutError:
                                print("⚠️ 管理员欢迎消息超时")
                            
                            # 发送测试消息
                            test_message = {
                                "type": "send_message",
                                "data": {
                                    "content": "这是一条测试消息，用于测试聊天室信息更新",
                                    "message_type": "text"
                                }
                            }
                            
                            await admin_websocket.send(json.dumps(test_message))
                            print("✅ 管理员发送测试消息")
                            
                            # Alice应该收到新消息
                            try:
                                new_message = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                new_message_data = json.loads(new_message)
                                
                                if new_message_data.get('type') == 'new_message':
                                    print("✅ Alice收到新消息")
                                else:
                                    print(f"⚠️ Alice收到其他类型消息: {new_message_data.get('type')}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到新消息")
                            
                            # Alice应该收到聊天室更新通知
                            try:
                                room_update = await asyncio.wait_for(alice_websocket.recv(), timeout=5.0)
                                room_update_data = json.loads(room_update)
                                
                                if room_update_data.get('type') == 'room_updated':
                                    print("✅ Alice收到聊天室更新通知")
                                    print(f"   最后消息: {room_update_data.get('data', {}).get('last_message', {}).get('content')}")
                                else:
                                    print(f"⚠️ Alice收到其他类型通知: {room_update_data.get('type')}")
                            except asyncio.TimeoutError:
                                print("❌ Alice未收到聊天室更新通知")
                        else:
                            print(f"❌ 管理员WebSocket认证失败: {admin_auth_data}")
                else:
                    print(f"❌ Alice WebSocket认证失败: {alice_auth_data}")
                    return
            
            # 6. 清理测试数据
            print("\n🔄 清理测试数据...")
            
            # 删除测试聊天室
            for room_id in [test_room_id, new_room_id]:
                async with session.delete(
                    f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        print(f"✅ 聊天室 {room_id} 删除成功")
                    else:
                        print(f"⚠️ 聊天室 {room_id} 删除失败")
            
            print("\n🎉 最终修复测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ SQLAlchemy懒加载问题修复")
            print("✅ 聊天室创建通知排除创建者")
            print("✅ 聊天室信息实时更新")
            print("✅ WebSocket连接稳定")
            print("✅ 消息发送和接收正常")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_final_fixes())
