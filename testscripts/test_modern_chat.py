#!/usr/bin/env python3
"""
测试现代化聊天室功能
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime

async def test_modern_chat():
    """测试现代化聊天室功能"""
    
    print("🚀 开始测试现代化聊天室功能...\n")
    
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
            
            # 2. 测试获取聊天室列表
            print("\n🔄 测试获取聊天室列表...")
            async with session.get(
                "http://localhost:8000/api/modern-chat/rooms",
                headers=headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    print(f"✅ 获取聊天室列表成功，共 {len(rooms)} 个聊天室")
                    for room in rooms[:3]:  # 只显示前3个
                        print(f"   - {room.get('name')} ({room.get('room_type')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室列表失败 ({response.status}): {error_text}")
            
            # 3. 测试创建聊天室
            print("\n🔄 测试创建聊天室...")
            new_room_data = {
                "name": f"测试聊天室 {datetime.now().strftime('%H:%M:%S')}",
                "description": "这是一个测试聊天室",
                "room_type": "group",
                "is_public": True,
                "max_members": 100,
                "allow_member_invite": True,
                "allow_member_modify_info": False,
                "message_history_visible": True
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
            
            # 4. 测试获取聊天室详情
            print("\n🔄 测试获取聊天室详情...")
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    room_detail = await response.json()
                    print(f"✅ 获取聊天室详情成功:")
                    print(f"   名称: {room_detail.get('name')}")
                    print(f"   类型: {room_detail.get('room_type')}")
                    print(f"   成员数: {room_detail.get('member_count')}")
                    print(f"   创建者: {room_detail.get('creator', {}).get('username')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室详情失败 ({response.status}): {error_text}")
            
            # 5. 测试发送消息
            print("\n🔄 测试发送消息...")
            message_data = {
                "room_id": room_id,
                "content": "这是一条测试消息！",
                "message_type": "text"
            }
            
            async with session.post(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}/messages",
                json=message_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    message = await response.json()
                    print(f"✅ 发送消息成功:")
                    print(f"   内容: {message.get('content')}")
                    print(f"   发送者: {message.get('sender', {}).get('username')}")
                    print(f"   时间: {message.get('created_at')}")
                    message_id = message.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 发送消息失败 ({response.status}): {error_text}")
                    return
            
            # 6. 测试获取消息列表
            print("\n🔄 测试获取消息列表...")
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}/messages",
                headers=headers
            ) as response:
                if response.status == 200:
                    message_list = await response.json()
                    messages = message_list.get('messages', [])
                    print(f"✅ 获取消息列表成功，共 {len(messages)} 条消息")
                    for msg in messages[-3:]:  # 显示最后3条消息
                        print(f"   - {msg.get('sender', {}).get('username')}: {msg.get('content')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取消息列表失败 ({response.status}): {error_text}")
            
            # 7. 测试WebSocket连接（简单测试）
            print("\n🔄 测试WebSocket连接...")
            try:
                ws_url = f"ws://localhost:8000/api/modern-chat/ws/{room_id}?token={access_token}"
                
                async with websockets.connect(ws_url) as websocket:
                    print("✅ WebSocket连接成功")
                    
                    # 发送一条测试消息
                    test_message = {
                        "type": "send_message",
                        "data": {
                            "content": "这是通过WebSocket发送的消息！",
                            "message_type": "text"
                        }
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    print("✅ 通过WebSocket发送消息成功")
                    
                    # 等待响应
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        ws_message = json.loads(response)
                        print(f"✅ 收到WebSocket响应: {ws_message.get('type')}")
                    except asyncio.TimeoutError:
                        print("⚠️ WebSocket响应超时（这是正常的）")
                    
            except Exception as e:
                print(f"❌ WebSocket连接失败: {e}")
            
            # 8. 测试更新聊天室
            print("\n🔄 测试更新聊天室...")
            update_data = {
                "description": "这是一个更新后的测试聊天室描述"
            }
            
            async with session.put(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                json=update_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    updated_room = await response.json()
                    print(f"✅ 更新聊天室成功")
                    print(f"   新描述: {updated_room.get('description')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 更新聊天室失败 ({response.status}): {error_text}")
            
            # 9. 测试删除聊天室
            print("\n🔄 测试删除聊天室...")
            async with session.delete(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 删除聊天室成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 删除聊天室失败 ({response.status}): {error_text}")
            
            print("\n🎉 现代化聊天室功能测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_modern_chat())
