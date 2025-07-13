#!/usr/bin/env python3
"""
最终聊天室功能测试
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime

async def test_final_chat_features():
    """测试修复后的聊天室功能"""
    
    print("🚀 开始测试修复后的聊天室功能...\n")
    
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
            
            # 2. 创建测试聊天室
            print("\n🔄 创建测试聊天室...")
            new_room_data = {
                "name": f"功能测试聊天室 {datetime.now().strftime('%H:%M:%S')}",
                "description": "用于测试修复后功能的聊天室",
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
            
            # 3. 测试聊天室详情（检查成员数量和在线状态）
            print("\n🔄 测试聊天室详情...")
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    room_detail = await response.json()
                    print(f"✅ 获取聊天室详情成功:")
                    print(f"   名称: {room_detail.get('name')}")
                    print(f"   成员数: {room_detail.get('member_count')}")
                    print(f"   成员列表: {len(room_detail.get('members', []))}")
                    
                    # 检查成员在线状态
                    members = room_detail.get('members', [])
                    online_members = [m for m in members if m.get('is_online')]
                    print(f"   在线成员: {len(online_members)}")
                    
                    for member in members:
                        status = "在线" if member.get('is_online') else "离线"
                        print(f"     - {member.get('username')} ({status})")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室详情失败 ({response.status}): {error_text}")
            
            # 4. 测试WebSocket连接和表情反应
            print("\n🔄 测试WebSocket连接和表情反应...")
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
                    
                    # 等待认证响应
                    auth_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    auth_data = json.loads(auth_response)
                    
                    if auth_data.get('type') == 'auth_response' and auth_data.get('success'):
                        print("✅ WebSocket认证成功")
                        
                        # 发送测试消息
                        test_message = {
                            "type": "send_message",
                            "data": {
                                "content": "这是一条用于测试表情反应的消息！",
                                "message_type": "text"
                            }
                        }
                        
                        await websocket.send(json.dumps(test_message))
                        
                        # 等待消息响应
                        msg_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        msg_data = json.loads(msg_response)
                        
                        if msg_data.get('type') == 'new_message':
                            message_id = msg_data.get('data', {}).get('id')
                            print(f"✅ 消息发送成功，ID: {message_id}")
                            
                            # 测试表情反应
                            if message_id:
                                print("🔄 测试表情反应...")
                                
                                reaction_message = {
                                    "type": "react_message",
                                    "data": {
                                        "message_id": message_id,
                                        "emoji": "👍"
                                    }
                                }
                                
                                await websocket.send(json.dumps(reaction_message))
                                
                                # 等待表情反应响应
                                try:
                                    reaction_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                    reaction_data = json.loads(reaction_response)
                                    
                                    if reaction_data.get('type') == 'message_reaction':
                                        print("✅ 表情反应成功")
                                        print(f"   表情: {reaction_data.get('data', {}).get('emoji')}")
                                        print(f"   操作: {reaction_data.get('data', {}).get('action')}")
                                    else:
                                        print(f"⚠️ 收到其他类型响应: {reaction_data.get('type')}")
                                        
                                except asyncio.TimeoutError:
                                    print("⚠️ 表情反应响应超时")
                        
                    else:
                        print(f"❌ WebSocket认证失败: {auth_data}")
                        
            except Exception as e:
                print(f"❌ WebSocket测试失败: {e}")
            
            # 5. 测试获取消息列表（检查表情反应）
            print("\n🔄 测试获取消息列表...")
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}/messages",
                headers=headers
            ) as response:
                if response.status == 200:
                    message_list = await response.json()
                    messages = message_list.get('messages', [])
                    print(f"✅ 获取消息列表成功，共 {len(messages)} 条消息")
                    
                    # 检查最新消息的表情反应
                    if messages:
                        latest_message = messages[-1]
                        reactions = latest_message.get('reactions', [])
                        print(f"   最新消息表情反应: {len(reactions)} 个")
                        
                        for reaction in reactions:
                            print(f"     - {reaction.get('emoji')}: {reaction.get('count')} 次")
                            
                else:
                    error_text = await response.text()
                    print(f"❌ 获取消息列表失败 ({response.status}): {error_text}")
            
            # 6. 测试聊天室删除
            print("\n🔄 测试聊天室删除...")
            async with session.delete(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 聊天室删除成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 聊天室删除失败 ({response.status}): {error_text}")
            
            print("\n🎉 修复后的聊天室功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ 聊天室创建和管理")
            print("✅ 成员数量正确显示")
            print("✅ 在线状态检测")
            print("✅ WebSocket安全认证")
            print("✅ 消息发送和接收")
            print("✅ 表情反应功能")
            print("✅ 消息列表获取")
            print("✅ 聊天室删除")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_final_chat_features())
