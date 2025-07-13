#!/usr/bin/env python3
"""
测试加入页面相关的API功能
"""

import asyncio
import aiohttp

async def test_join_page_apis():
    """测试加入页面相关的API功能"""
    
    print("🚀 测试加入页面相关API功能...\n")
    
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
            
            # 2. 测试搜索API
            print("\n🔄 测试搜索API...")
            async with session.get(
                "http://localhost:8000/api/modern-chat/search-rooms?q=测试",
                headers=headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    print(f"✅ 搜索API正常，找到 {len(rooms)} 个聊天室")
                    
                    if rooms:
                        test_room = rooms[0]
                        print(f"   测试聊天室: {test_room.get('name')}")
                        print(f"   聊天室ID: {test_room.get('id')}")
                        print(f"   是否成员: {test_room.get('is_member')}")
                        
                        # 3. 测试申请加入API
                        if not test_room.get('is_member'):
                            print(f"\n🔄 测试申请加入API...")
                            join_data = {
                                "room_id": test_room.get('id'),
                                "message": "这是一个测试申请消息"
                            }
                            
                            async with session.post(
                                f"http://localhost:8000/api/modern-chat/rooms/{test_room.get('id')}/join-request",
                                json=join_data,
                                headers=headers
                            ) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    print(f"✅ 申请加入API正常: {result.get('message')}")
                                elif response.status == 429:
                                    error_data = await response.json()
                                    print(f"⚠️  申请冷却中: {error_data.get('detail')}")
                                else:
                                    error_text = await response.text()
                                    print(f"❌ 申请加入失败: {error_text}")
                        else:
                            print(f"   用户已经是成员，跳过申请测试")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 搜索API失败: {error_text}")
            
            # 4. 测试邀请码加入API（使用无效邀请码）
            print(f"\n🔄 测试邀请码加入API...")
            invite_data = {
                "invite_code": "invalid_code_test"
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/rooms/join-by-invite",
                json=invite_data,
                headers=headers
            ) as response:
                if response.status == 404:
                    print(f"✅ 邀请码API正常（预期的404错误：邀请码无效）")
                elif response.status == 200:
                    result = await response.json()
                    print(f"✅ 邀请码加入成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 邀请码API异常: {error_text}")
            
            print("\n🎉 加入页面API测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_join_page_apis())
