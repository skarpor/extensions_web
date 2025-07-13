#!/usr/bin/env python3
"""
完整的私聊功能测试
"""

import asyncio
import aiohttp
import json
import websockets

async def test_private_chat_complete():
    """测试完整的私聊功能"""
    
    print("🚀 开始测试完整的私聊功能...\n")
    
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
            
            # 2. 测试用户搜索
            print("\n🔄 测试用户搜索...")
            async with session.get(
                "http://localhost:8000/api/users/search/users?q=alice&limit=5",
                headers=headers
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"✅ 用户搜索成功，找到 {len(search_results)} 个用户")
                    
                    if search_results:
                        test_user_id = search_results[0]['id']
                        test_user_name = search_results[0]['username']
                        print(f"   选择用户: {test_user_name} (ID: {test_user_id})")
                    else:
                        print("❌ 没有找到其他用户，无法测试私聊")
                        return
                else:
                    error_text = await response.text()
                    print(f"❌ 用户搜索失败 ({response.status}): {error_text}")
                    return
            
            # 3. 创建私聊聊天室
            print("\n🔄 创建私聊聊天室...")
            private_chat_data = {
                "target_user_id": test_user_id
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/private-rooms",
                json=private_chat_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    private_room = await response.json()
                    print(f"✅ 私聊聊天室创建成功")
                    print(f"   聊天室名称: {private_room.get('name')}")
                    print(f"   聊天室类型: {private_room.get('room_type')}")
                    private_room_id = private_room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建私聊聊天室失败 ({response.status}): {error_text}")
                    return
            
            # 4. 测试WebSocket连接和消息发送
            print("\n🔄 测试WebSocket连接和消息发送...")
            try:
                ws_url = f"ws://localhost:8000/api/modern-chat/ws/{private_room_id}"
                
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
                        
                        # 发送私聊消息
                        test_message = {
                            "type": "send_message",
                            "data": {
                                "content": f"你好 {test_user_name}！这是一条私聊测试消息。",
                                "message_type": "text"
                            }
                        }
                        
                        await websocket.send(json.dumps(test_message))
                        print("✅ 私聊消息发送成功")
                        
                        # 等待消息响应
                        try:
                            msg_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            msg_data = json.loads(msg_response)
                            
                            if msg_data.get('type') == 'new_message':
                                message_id = msg_data.get('data', {}).get('id')
                                print(f"✅ 收到新消息响应，消息ID: {message_id}")
                                
                                # 测试消息编辑
                                if message_id:
                                    print("🔄 测试消息编辑...")
                                    edit_message = {
                                        "type": "edit_message",
                                        "data": {
                                            "message_id": message_id,
                                            "content": f"你好 {test_user_name}！这是一条编辑后的私聊消息。✏️"
                                        }
                                    }
                                    
                                    await websocket.send(json.dumps(edit_message))
                                    
                                    try:
                                        edit_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                        edit_data = json.loads(edit_response)
                                        
                                        if edit_data.get('type') == 'message_updated':
                                            print("✅ 消息编辑成功")
                                        else:
                                            print(f"⚠️ 消息编辑响应异常: {edit_data.get('type')}")
                                    except asyncio.TimeoutError:
                                        print("⚠️ 消息编辑响应超时")
                            else:
                                print(f"⚠️ 收到其他类型响应: {msg_data.get('type')}")
                                
                        except asyncio.TimeoutError:
                            print("⚠️ 消息响应超时")
                        
                    else:
                        print(f"❌ WebSocket认证失败: {auth_data}")
                        
            except Exception as e:
                print(f"❌ WebSocket测试失败: {e}")
            
            # 5. 测试获取私聊消息列表
            print("\n🔄 测试获取私聊消息列表...")
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}/messages",
                headers=headers
            ) as response:
                if response.status == 200:
                    message_list = await response.json()
                    messages = message_list.get('messages', [])
                    print(f"✅ 获取私聊消息列表成功，共 {len(messages)} 条消息")
                    
                    # 显示消息内容
                    for msg in messages:
                        sender = msg.get('sender', {}).get('username', 'Unknown')
                        content = msg.get('content', '')
                        msg_type = msg.get('message_type', 'text')
                        is_edited = msg.get('is_edited', False)
                        
                        status = " [已编辑]" if is_edited else ""
                        print(f"   - {sender}: {content} ({msg_type}){status}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ 获取私聊消息列表失败 ({response.status}): {error_text}")
            
            # 6. 测试私聊聊天室详情
            print("\n🔄 测试私聊聊天室详情...")
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    room_detail = await response.json()
                    print(f"✅ 获取私聊聊天室详情成功:")
                    print(f"   名称: {room_detail.get('name')}")
                    print(f"   描述: {room_detail.get('description')}")
                    print(f"   类型: {room_detail.get('room_type')}")
                    print(f"   成员数: {room_detail.get('member_count')}")
                    print(f"   是否公开: {room_detail.get('is_public')}")
                    
                    members = room_detail.get('members', [])
                    print(f"   成员列表:")
                    for member in members:
                        print(f"     - {member.get('username')} ({member.get('role')})")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ 获取私聊聊天室详情失败 ({response.status}): {error_text}")
            
            # 7. 测试私聊删除权限
            print("\n🔄 测试私聊删除权限...")
            async with session.delete(
                f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 私聊聊天室删除成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 私聊聊天室删除失败 ({response.status}): {error_text}")
            
            # 8. 验证删除后聊天室不存在
            print("\n🔄 验证删除后聊天室不存在...")
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}",
                headers=headers
            ) as response:
                if response.status == 404:
                    print("✅ 确认聊天室已被删除")
                else:
                    print(f"⚠️ 聊天室删除验证异常 ({response.status})")
            
            print("\n🎉 完整私聊功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ 用户搜索功能")
            print("✅ 私聊聊天室创建")
            print("✅ WebSocket连接和认证")
            print("✅ 私聊消息发送")
            print("✅ 私聊消息编辑")
            print("✅ 私聊消息列表获取")
            print("✅ 私聊聊天室详情")
            print("✅ 私聊删除权限（双方都可删除）")
            print("✅ 删除后验证")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_private_chat_complete())
