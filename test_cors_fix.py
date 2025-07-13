#!/usr/bin/env python3
"""
测试CORS修复是否有效
"""

import asyncio
import aiohttp

async def test_cors_fix():
    """测试CORS修复"""
    
    print("🚀 测试CORS修复...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 用户登录
            print("🔄 用户登录...")
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login",
                data={"username": "admin", "password": "123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    login_data = await response.json()
                    print(f"✅ 用户登录成功")
                    token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 用户登录失败: {error_text}")
                    return
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 创建聊天室
            print("\n🔄 创建测试聊天室...")
            room_data = {
                "name": "CORS测试聊天室",
                "description": "用于测试CORS修复的聊天室",
                "room_type": "public",
                "is_public": True,
                "max_members": 100
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=room_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 聊天室创建成功: {room.get('name')} (ID: {room.get('id')})")
                    room_id = room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败: {error_text}")
                    return
            
            # 3. 测试发送消息（模拟前端请求）
            print(f"\n🔄 测试发送消息...")
            message_data = {
                "content": "这是一条CORS测试消息",
                "message_type": "text"
            }
            
            # 添加Origin头部模拟浏览器跨域请求
            test_headers = headers.copy()
            test_headers["Origin"] = "http://192.168.3.139:5173"
            test_headers["Content-Type"] = "application/json"
            
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages",
                json=message_data,
                headers=test_headers
            ) as response:
                if response.status == 200:
                    message = await response.json()
                    print(f"✅ 消息发送成功: {message.get('content')}")
                    
                    # 检查CORS头部
                    cors_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                        'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                    }
                    print(f"   CORS头部: {cors_headers}")
                else:
                    error_text = await response.text()
                    print(f"❌ 消息发送失败 ({response.status}): {error_text}")
            
            # 4. 测试OPTIONS预检请求
            print(f"\n🔄 测试OPTIONS预检请求...")
            options_headers = {
                "Origin": "http://192.168.3.139:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type"
            }
            
            async with session.options(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages",
                headers=options_headers
            ) as response:
                if response.status == 200:
                    print(f"✅ OPTIONS预检请求成功")
                    cors_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                    }
                    print(f"   CORS头部: {cors_headers}")
                else:
                    error_text = await response.text()
                    print(f"❌ OPTIONS预检请求失败 ({response.status}): {error_text}")
            
            print("\n🎉 CORS测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_cors_fix())
