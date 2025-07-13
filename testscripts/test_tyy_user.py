#!/usr/bin/env python3
"""
测试tyy用户发送消息
"""

import asyncio
import aiohttp

async def test_tyy_user():
    """测试tyy用户发送消息"""
    
    print("🚀 测试tyy用户发送消息...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. tyy用户登录
            print("🔄 tyy用户登录...")
            async with session.post(
                "http://localhost:8000/api/auth/login",
                data={"username": "tyy", "password": "123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    login_data = await response.json()
                    print(f"✅ tyy用户登录成功")
                    token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ tyy用户登录失败: {error_text}")
                    return
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 发送消息到公开聊天室
            print("\n🔄 发送消息到公开聊天室...")
            message_data = {
                "content": "这是tyy用户的测试消息，测试自动加入功能",
                "message_type": "text"
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/rooms/1/messages",
                json=message_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    message = await response.json()
                    print(f"✅ 消息发送成功: {message.get('content')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 消息发送失败 ({response.status}): {error_text}")
            
            print("\n🎉 测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_tyy_user())
