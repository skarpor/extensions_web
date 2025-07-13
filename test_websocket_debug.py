#!/usr/bin/env python3
"""
WebSocket调试测试
"""

import asyncio
import aiohttp
import json
import websockets

async def test_websocket_debug():
    """调试WebSocket连接问题"""
    
    print("🚀 开始调试WebSocket连接...\n")
    
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
                    login_result = await response.json()
                    print(f"✅ 管理员登录成功")
                    access_token = login_result.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败 ({response.status}): {error_text}")
                    return
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 2. 创建私聊聊天室
            print("\n🔄 创建私聊聊天室...")
            private_chat_data = {
                "target_user_id": 6  # alice的ID
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/private-rooms",
                json=private_chat_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    private_room = await response.json()
                    print(f"✅ 私聊聊天室创建成功")
                    print(f"   聊天室ID: {private_room.get('id')}")
                    private_room_id = private_room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建私聊聊天室失败 ({response.status}): {error_text}")
                    return
            
            # 3. 测试WebSocket连接
            print("\n🔄 测试WebSocket连接...")
            try:
                ws_url = f"ws://localhost:8000/api/modern-chat/ws/{private_room_id}"
                print(f"连接URL: {ws_url}")
                
                async with websockets.connect(ws_url) as websocket:
                    print("✅ WebSocket连接建立成功")
                    
                    # 发送认证消息
                    auth_message = {
                        "type": "auth",
                        "token": access_token
                    }
                    
                    print("🔄 发送认证消息...")
                    await websocket.send(json.dumps(auth_message))
                    print("✅ 认证消息发送成功")
                    
                    # 等待认证响应
                    print("🔄 等待认证响应...")
                    try:
                        auth_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        auth_data = json.loads(auth_response)
                        print(f"✅ 收到认证响应: {auth_data}")
                        
                        if auth_data.get('type') == 'auth_response' and auth_data.get('success'):
                            print("✅ WebSocket认证成功")
                            
                            # 等待欢迎消息
                            print("🔄 等待欢迎消息...")
                            try:
                                welcome_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                welcome_data = json.loads(welcome_response)
                                print(f"✅ 收到欢迎消息: {welcome_data}")
                            except asyncio.TimeoutError:
                                print("⚠️ 欢迎消息超时")
                            
                            # 发送测试消息
                            print("🔄 发送测试消息...")
                            test_message = {
                                "type": "send_message",
                                "data": {
                                    "content": "这是一条调试测试消息",
                                    "message_type": "text"
                                }
                            }
                            
                            await websocket.send(json.dumps(test_message))
                            print("✅ 测试消息发送成功")
                            
                            # 等待消息响应
                            print("🔄 等待消息响应...")
                            try:
                                msg_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                msg_data = json.loads(msg_response)
                                print(f"✅ 收到消息响应: {msg_data}")
                            except asyncio.TimeoutError:
                                print("⚠️ 消息响应超时")
                            
                            # 保持连接一段时间
                            print("🔄 保持连接5秒...")
                            await asyncio.sleep(5)
                            print("✅ 连接保持成功")
                            
                        else:
                            print(f"❌ WebSocket认证失败: {auth_data}")
                            
                    except asyncio.TimeoutError:
                        print("❌ 认证响应超时")
                        
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"❌ WebSocket连接被关闭: {e.code} - {e.reason}")
            except Exception as e:
                print(f"❌ WebSocket测试失败: {e}")
            
            # 4. 清理测试数据
            print("\n🔄 清理测试数据...")
            async with session.delete(
                f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 测试聊天室删除成功")
                else:
                    error_text = await response.text()
                    print(f"❌ 测试聊天室删除失败 ({response.status}): {error_text}")
            
            print("\n🎉 WebSocket调试测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_debug())
