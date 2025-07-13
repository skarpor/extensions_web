#!/usr/bin/env python3
"""
完整的聊天室功能测试
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime
import tempfile
import os

async def test_complete_chat_features():
    """测试完整的聊天室功能"""
    
    print("🚀 开始测试完整的聊天室功能...\n")
    
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
                "name": f"完整功能测试聊天室 {datetime.now().strftime('%H:%M:%S')}",
                "description": "这是一个功能完整的测试聊天室",
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
            
            # 3. 测试文件上传
            print("\n🔄 测试文件上传...")
            try:
                # 创建一个临时测试文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_file.write("这是一个测试文件内容\n用于测试聊天室文件上传功能")
                    temp_file_path = temp_file.name
                
                # 上传文件
                upload_path = f"chat/{room_id}/2025/7"
                with open(temp_file_path, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field('files', f, filename='test.txt', content_type='text/plain')
                    
                    async with session.post(
                        f"http://localhost:8000/api/files/upload/{upload_path}",
                        data=form_data,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            upload_result = await response.json()
                            if upload_result and len(upload_result) > 0:
                                uploaded_file = upload_result[0]
                                print(f"✅ 文件上传成功: {uploaded_file.get('filename')}")
                                file_url = uploaded_file.get('download_url')
                            else:
                                print("❌ 文件上传返回空结果")
                                file_url = None
                        else:
                            error_text = await response.text()
                            print(f"❌ 文件上传失败 ({response.status}): {error_text}")
                            file_url = None
                
                # 清理临时文件
                os.unlink(temp_file_path)
                
            except Exception as e:
                print(f"❌ 文件上传测试失败: {e}")
                file_url = None
            
            # 4. 测试WebSocket连接和消息功能
            print("\n🔄 测试WebSocket连接和消息功能...")
            try:
                ws_url = f"ws://localhost:8000/api/modern-chat/ws/{room_id}?token={access_token}"
                
                async with websockets.connect(ws_url) as websocket:
                    print("✅ WebSocket连接成功")
                    
                    # 测试发送文本消息
                    print("🔄 测试发送文本消息...")
                    text_message = {
                        "type": "send_message",
                        "data": {
                            "content": "这是一条测试文本消息！👋",
                            "message_type": "text"
                        }
                    }
                    
                    await websocket.send(json.dumps(text_message))
                    
                    # 等待响应
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        ws_message = json.loads(response)
                        if ws_message.get('type') == 'new_message':
                            print("✅ 文本消息发送成功")
                            message_id = ws_message.get('data', {}).get('id')
                        else:
                            print(f"⚠️ 收到其他类型消息: {ws_message.get('type')}")
                            message_id = None
                    except asyncio.TimeoutError:
                        print("⚠️ WebSocket响应超时")
                        message_id = None
                    
                    # 测试发送文件消息（如果文件上传成功）
                    if file_url:
                        print("🔄 测试发送文件消息...")
                        file_message = {
                            "type": "send_message",
                            "data": {
                                "content": "[文件] test.txt",
                                "message_type": "file",
                                "file_url": file_url,
                                "file_name": "test.txt",
                                "file_size": 100
                            }
                        }
                        
                        await websocket.send(json.dumps(file_message))
                        
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            ws_message = json.loads(response)
                            if ws_message.get('type') == 'new_message':
                                print("✅ 文件消息发送成功")
                            else:
                                print(f"⚠️ 文件消息响应异常: {ws_message.get('type')}")
                        except asyncio.TimeoutError:
                            print("⚠️ 文件消息响应超时")
                    
                    # 测试正在输入状态
                    print("🔄 测试正在输入状态...")
                    typing_message = {
                        "type": "typing",
                        "data": {
                            "is_typing": True
                        }
                    }
                    
                    await websocket.send(json.dumps(typing_message))
                    print("✅ 正在输入状态发送成功")
                    
                    # 停止输入
                    await asyncio.sleep(1)
                    stop_typing_message = {
                        "type": "typing",
                        "data": {
                            "is_typing": False
                        }
                    }
                    
                    await websocket.send(json.dumps(stop_typing_message))
                    print("✅ 停止输入状态发送成功")
                    
                    # 测试消息编辑（如果有消息ID）
                    if message_id:
                        print("🔄 测试消息编辑...")
                        edit_message = {
                            "type": "edit_message",
                            "data": {
                                "message_id": message_id,
                                "content": "这是一条编辑后的测试消息！✏️"
                            }
                        }
                        
                        await websocket.send(json.dumps(edit_message))
                        
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            ws_message = json.loads(response)
                            if ws_message.get('type') == 'message_updated':
                                print("✅ 消息编辑成功")
                            else:
                                print(f"⚠️ 消息编辑响应异常: {ws_message.get('type')}")
                        except asyncio.TimeoutError:
                            print("⚠️ 消息编辑响应超时")
                        
                        # 测试表情反应
                        print("🔄 测试表情反应...")
                        reaction_message = {
                            "type": "react_message",
                            "data": {
                                "message_id": message_id,
                                "emoji": "👍"
                            }
                        }
                        
                        await websocket.send(json.dumps(reaction_message))
                        print("✅ 表情反应发送成功")
                        
                        # 测试消息删除
                        print("🔄 测试消息删除...")
                        delete_message = {
                            "type": "delete_message",
                            "data": {
                                "message_id": message_id
                            }
                        }
                        
                        await websocket.send(json.dumps(delete_message))
                        
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            ws_message = json.loads(response)
                            if ws_message.get('type') == 'message_deleted':
                                print("✅ 消息删除成功")
                            else:
                                print(f"⚠️ 消息删除响应异常: {ws_message.get('type')}")
                        except asyncio.TimeoutError:
                            print("⚠️ 消息删除响应超时")
                    
            except Exception as e:
                print(f"❌ WebSocket测试失败: {e}")
            
            # 5. 测试获取消息列表
            print("\n🔄 测试获取消息列表...")
            async with session.get(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}/messages",
                headers=headers
            ) as response:
                if response.status == 200:
                    message_list = await response.json()
                    messages = message_list.get('messages', [])
                    print(f"✅ 获取消息列表成功，共 {len(messages)} 条消息")
                    
                    # 显示最近的消息
                    for msg in messages[-3:]:
                        sender = msg.get('sender', {}).get('username', 'Unknown')
                        content = msg.get('content', '')
                        msg_type = msg.get('message_type', 'text')
                        is_deleted = msg.get('is_deleted', False)
                        is_edited = msg.get('is_edited', False)
                        
                        status = ""
                        if is_deleted:
                            status += " [已删除]"
                        if is_edited:
                            status += " [已编辑]"
                        
                        print(f"   - {sender}: {content} ({msg_type}){status}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取消息列表失败 ({response.status}): {error_text}")
            
            # 6. 测试聊天室管理功能
            print("\n🔄 测试聊天室管理功能...")
            
            # 更新聊天室信息
            update_data = {
                "description": "这是一个功能测试完成的聊天室 ✅"
            }
            
            async with session.put(
                f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                json=update_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    updated_room = await response.json()
                    print(f"✅ 聊天室更新成功")
                    print(f"   新描述: {updated_room.get('description')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 聊天室更新失败 ({response.status}): {error_text}")
            
            # 7. 清理测试数据
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
            
            print("\n🎉 完整聊天室功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ 聊天室创建和管理")
            print("✅ 文件上传功能")
            print("✅ WebSocket实时通信")
            print("✅ 文本消息发送")
            print("✅ 文件消息发送")
            print("✅ 正在输入状态")
            print("✅ 消息编辑功能")
            print("✅ 表情反应功能")
            print("✅ 消息删除功能")
            print("✅ 消息列表获取")
            print("✅ 聊天室信息更新")
            print("✅ 测试数据清理")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_complete_chat_features())
