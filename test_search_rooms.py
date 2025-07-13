#!/usr/bin/env python3
"""
测试搜索聊天室功能
"""

import asyncio
import aiohttp

async def test_search_rooms():
    """测试搜索聊天室功能"""
    
    print("🚀 测试搜索聊天室功能...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 用户登录
            print("🔄 用户登录...")
            async with session.post(
                "http://localhost:8000/api/auth/login",
                data={"username": "tyy", "password": "123"},
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
            
            # 2. 搜索聊天室
            search_queries = ["公开", "测试", "聊天"]
            
            for query in search_queries:
                print(f"\n🔄 搜索关键词: '{query}'")
                async with session.get(
                    f"http://localhost:8000/api/modern-chat/search-rooms?q={query}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        rooms = await response.json()
                        print(f"✅ 搜索成功，找到 {len(rooms)} 个聊天室:")
                        for room in rooms:
                            print(f"   - {room.get('name')} ({room.get('room_type')}) - {room.get('member_count')} 成员")
                            print(f"     描述: {room.get('description', '无')}")
                            print(f"     是否成员: {room.get('is_member', False)}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 搜索失败: {error_text}")
            
            print("\n🎉 搜索测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_search_rooms())
