#!/usr/bin/env python3
"""
测试表情反应功能
"""

import asyncio
import aiohttp

async def test_emoji_reactions():
    """测试表情反应功能"""
    
    print("🚀 测试表情反应功能...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 管理员登录
            print("🔄 管理员登录...")
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login-json",
                json={"username": "admin", "password": "123"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    login_data = await response.json()
                    print(f"✅ 管理员登录成功")
                    admin_token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败: {error_text}")
                    return
            
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # 2. 创建测试聊天室
            print("\n🔄 创建测试聊天室...")
            room_data = {
                "name": "表情反应测试群",
                "description": "用于测试表情反应功能",
                "room_type": "group",
                "is_public": False,
                "max_members": 100
            }

            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 聊天室创建成功: {room.get('name')} (ID: {room.get('id')})")
                    room_id = room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败: {error_text}")
                    return

            # 3. 发送测试消息
            print(f"\n🔄 发送测试消息...")
            message_data = {
                "content": "这是一条用于测试表情反应的消息",
                "message_type": "text"
            }

            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages",
                json=message_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    message = await response.json()
                    print(f"✅ 消息发送成功")
                    message_id = message.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 消息发送失败: {error_text}")
                    return
            
            # 4. 测试添加表情反应
            print(f"\n🔄 测试添加表情反应...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/messages/{message_id}/reactions",
                json={"emoji": "👍"},
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 表情反应添加成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 表情反应失败: {error_text}")
            
            # 5. 测试获取表情反应
            print(f"\n🔄 测试获取表情反应...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/messages/{message_id}/reactions",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    reactions = await response.json()
                    print(f"✅ 表情反应获取成功，共 {len(reactions)} 种表情")
                    for reaction in reactions:
                        print(f"   - {reaction.get('emoji')}: {reaction.get('count')} 个用户")
                        print(f"     用户列表: {reaction.get('users')}")
                        print(f"     当前用户已反应: {reaction.get('user_reacted')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取表情反应失败: {error_text}")
            
            print("\n🎉 表情反应功能测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_emoji_reactions())
