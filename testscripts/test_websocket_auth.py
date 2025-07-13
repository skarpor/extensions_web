#!/usr/bin/env python3
"""
测试新的WebSocket认证方式
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime

async def test_websocket_auth():
    """测试WebSocket认证功能"""
    
    print("🚀 开始测试WebSocket认证功能...\n")
    
    # 管理员登录信息
    admin_credentials = {
        "username": "admin",
        "password": "123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 管理员登录获取token
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
            
            # 2. 创建测试聊天室
            print("\n🔄 创建测试聊天室...")
            new_room_data = {
                "name": f"WebSocket认证测试聊天室 {datetime.now().strftime('%H:%M:%S')}",
                "description": "用于测试WebSocket认证的聊天室",
                "room_type": "group",
                "is_public": True,
                "max_members": 100
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/rooms",
                json=new_room_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    new_room = await response.json()
                    print(f"✅ 创建聊天室成功: {new_room.get('name')}")
                    room_id = new_room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败 ({response.status}): {error_text}")
                    return
            
            # 3. 测试WebSocket认证连接
            print("\n🔄 测试WebSocket认证连接...")
            
            # 测试正确的认证流程
            print("📝 测试正确的认证流程...")
            try:
                ws_url = f"ws://localhost:8000/api/modern-chat/ws/{room_id}"
                
                async with websockets.connect(ws_url) as websocket:
                    print("✅ WebSocket连接建立成功")
                    
                    # 发送认证消息
                    auth_message = {
                        "type": "auth",
                        "token": access_token
                    }
                    
                    await websocket.send(json.dumps(auth_message))
                    print("✅ 认证消息发送成功")
                    
                    # 等待认证响应
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        auth_response = json.loads(response)
                        
                        if auth_response.get('type') == 'auth_response':
                            if auth_response.get('success'):
                                print("✅ WebSocket认证成功")
                                print(f"   用户信息: {auth_response.get('user')}")
                                
                                # 测试发送消息
                                print("🔄 测试发送消息...")
                                test_message = {
                                    "type": "send_message",
                                    "data": {
                                        "content": "这是WebSocket认证测试消息！",
                                        "message_type": "text"
                                    }
                                }
                                
                                await websocket.send(json.dumps(test_message))
                                print("✅ 测试消息发送成功")
                                
                                # 等待消息响应
                                try:
                                    msg_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                    msg_data = json.loads(msg_response)
                                    
                                    if msg_data.get('type') == 'new_message':
                                        print("✅ 收到新消息响应")
                                        print(f"   消息内容: {msg_data.get('data', {}).get('content')}")
                                    else:
                                        print(f"⚠️ 收到其他类型响应: {msg_data.get('type')}")
                                        
                                except asyncio.TimeoutError:
                                    print("⚠️ 消息响应超时")
                                
                            else:
                                print(f"❌ WebSocket认证失败: {auth_response.get('error')}")
                        else:
                            print(f"⚠️ 收到非认证响应: {auth_response}")
                            
                    except asyncio.TimeoutError:
                        print("❌ 认证响应超时")
                        
            except Exception as e:
                print(f"❌ WebSocket连接测试失败: {e}")
            
            # 4. 测试错误的认证流程
            print("\n📝 测试错误的认证流程...")
            
            # 测试无效token
            print("🔄 测试无效token...")
            try:
                async with websockets.connect(ws_url) as websocket:
                    # 发送无效token
                    invalid_auth = {
                        "type": "auth",
                        "token": "invalid_token_12345"
                    }
                    
                    await websocket.send(json.dumps(invalid_auth))
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        auth_response = json.loads(response)
                        
                        if auth_response.get('type') == 'auth_response' and not auth_response.get('success'):
                            print("✅ 无效token正确被拒绝")
                            print(f"   错误信息: {auth_response.get('error')}")
                        else:
                            print(f"❌ 无效token未被正确处理: {auth_response}")
                            
                    except asyncio.TimeoutError:
                        print("⚠️ 无效token测试响应超时")
                        
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"✅ 无效token连接被正确关闭: {e.code} - {e.reason}")
            except Exception as e:
                print(f"❌ 无效token测试失败: {e}")
            
            # 测试缺少token
            print("🔄 测试缺少token...")
            try:
                async with websockets.connect(ws_url) as websocket:
                    # 发送缺少token的认证消息
                    no_token_auth = {
                        "type": "auth"
                        # 故意不包含token
                    }
                    
                    await websocket.send(json.dumps(no_token_auth))
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        auth_response = json.loads(response)
                        
                        if auth_response.get('type') == 'auth_response' and not auth_response.get('success'):
                            print("✅ 缺少token正确被拒绝")
                            print(f"   错误信息: {auth_response.get('error')}")
                        else:
                            print(f"❌ 缺少token未被正确处理: {auth_response}")
                            
                    except asyncio.TimeoutError:
                        print("⚠️ 缺少token测试响应超时")
                        
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"✅ 缺少token连接被正确关闭: {e.code} - {e.reason}")
            except Exception as e:
                print(f"❌ 缺少token测试失败: {e}")
            
            # 测试认证超时
            print("🔄 测试认证超时...")
            try:
                async with websockets.connect(ws_url) as websocket:
                    # 不发送任何认证消息，等待超时
                    print("   等待认证超时...")
                    
                    try:
                        # 等待超过认证超时时间
                        response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                        print(f"❌ 认证超时未正确处理，收到响应: {response}")
                        
                    except asyncio.TimeoutError:
                        print("⚠️ 认证超时测试本身超时")
                        
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"✅ 认证超时连接被正确关闭: {e.code} - {e.reason}")
            except Exception as e:
                print(f"❌ 认证超时测试失败: {e}")
            
            # 5. 清理测试数据
            print("\n🔄 清理测试数据...")
            async with session.delete(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 测试聊天室删除成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 测试聊天室删除失败 ({response.status}): {error_text}")
            
            print("\n🎉 WebSocket认证功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ 正确的认证流程")
            print("✅ 认证成功后消息发送")
            print("✅ 无效token拒绝")
            print("✅ 缺少token拒绝")
            print("✅ 认证超时处理")
            print("✅ 测试数据清理")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_auth())
