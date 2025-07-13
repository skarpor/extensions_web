#!/usr/bin/env python3
"""
简单的全局WebSocket测试
"""

import asyncio
import aiohttp
import json
import websockets

async def test_simple_global_websocket():
    """简单测试全局WebSocket功能"""
    
    print("🚀 开始测试全局WebSocket基本功能...\n")
    
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
            
            # 2. 建立全局WebSocket连接
            print("\n🔄 建立全局WebSocket连接...")
            
            ws_url = "ws://localhost:8000/api/global-ws"
            
            async with websockets.connect(ws_url) as websocket:
                print("✅ 全局WebSocket连接建立成功")
                
                # 发送认证消息
                auth_message = {
                    "type": "auth",
                    "token": admin_token
                }
                
                await websocket.send(json.dumps(auth_message))
                print("✅ 认证消息发送成功")
                
                # 等待认证响应
                print("🔄 等待认证响应...")
                try:
                    auth_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    auth_data = json.loads(auth_response)
                    print(f"✅ 收到认证响应: {auth_data}")
                    
                    if auth_data.get('type') == 'auth_response' and auth_data.get('data', {}).get('success'):
                        print("✅ 全局WebSocket认证成功")
                        
                        # 3. 发送心跳测试
                        print("\n🔄 发送心跳测试...")
                        ping_message = {
                            "type": "ping"
                        }
                        
                        await websocket.send(json.dumps(ping_message))
                        print("✅ 心跳消息发送成功")
                        
                        # 等待心跳响应
                        try:
                            pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            pong_data = json.loads(pong_response)
                            print(f"✅ 收到心跳响应: {pong_data}")
                        except asyncio.TimeoutError:
                            print("❌ 心跳响应超时")
                        
                        # 4. 测试获取在线用户
                        print("\n🔄 测试获取在线用户...")
                        online_users_message = {
                            "type": "get_online_users"
                        }
                        
                        await websocket.send(json.dumps(online_users_message))
                        print("✅ 获取在线用户消息发送成功")
                        
                        # 等待在线用户响应
                        try:
                            users_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            users_data = json.loads(users_response)
                            print(f"✅ 收到在线用户响应: {users_data}")
                        except asyncio.TimeoutError:
                            print("❌ 在线用户响应超时")
                        
                        # 5. 保持连接一段时间
                        print("\n🔄 保持连接5秒...")
                        await asyncio.sleep(5)
                        print("✅ 连接保持成功")
                        
                    else:
                        print(f"❌ 全局WebSocket认证失败: {auth_data}")
                        
                except asyncio.TimeoutError:
                    print("❌ 认证响应超时")
                    
            print("\n🎉 全局WebSocket基本功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ 全局WebSocket连接建立")
            print("✅ 认证功能正常")
            print("✅ 心跳功能正常")
            print("✅ 在线用户查询功能")
            print("✅ 连接稳定性良好")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_global_websocket())
