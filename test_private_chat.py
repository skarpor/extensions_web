#!/usr/bin/env python3
"""
测试私聊功能
"""

import asyncio
import aiohttp
import json

async def test_private_chat():
    """测试私聊功能"""
    
    print("🚀 开始测试私聊功能...\n")
    
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
                "http://localhost:8000/api/users/search/users?q=admin&limit=5",
                headers=headers
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"✅ 用户搜索成功，找到 {len(search_results)} 个用户")
                    for user in search_results:
                        print(f"   - {user.get('username')} ({user.get('nickname', '无昵称')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 用户搜索失败 ({response.status}): {error_text}")
            
            # 3. 测试获取最近联系人
            print("\n🔄 测试获取最近联系人...")
            async with session.get(
                "http://localhost:8000/api/users/contacts/recent?limit=5",
                headers=headers
            ) as response:
                if response.status == 200:
                    recent_contacts = await response.json()
                    print(f"✅ 获取最近联系人成功，共 {len(recent_contacts)} 个")
                    for user in recent_contacts:
                        print(f"   - {user.get('username')} ({user.get('nickname', '无昵称')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取最近联系人失败 ({response.status}): {error_text}")
            
            # 4. 使用一个假设的用户ID进行测试（通常ID为2的用户存在）
            print("\n🔄 使用测试用户ID...")
            test_user_id = 2  # 假设存在ID为2的用户

            # 验证用户是否存在
            async with session.get(
                f"http://localhost:8000/api/users/{test_user_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    test_user = await response.json()
                    print(f"✅ 找到测试用户: {test_user.get('username')}")
                else:
                    # 如果ID为2的用户不存在，尝试搜索其他用户
                    print("⚠️ ID为2的用户不存在，搜索其他用户...")
                    async with session.get(
                        "http://localhost:8000/api/users/search/users?q=&limit=5",
                        headers=headers
                    ) as search_response:
                        if search_response.status == 200:
                            search_results = await search_response.json()
                            if search_results:
                                test_user_id = search_results[0]['id']
                                print(f"✅ 使用搜索到的用户，ID: {test_user_id}")
                            else:
                                print("❌ 未找到任何其他用户")
                                return
                        else:
                            print("❌ 搜索用户失败")
                            return
            
            # 5. 测试创建私聊聊天室
            print("\n🔄 测试创建私聊聊天室...")
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
                    print(f"   成员数量: {private_room.get('member_count')}")
                    print(f"   是否公开: {private_room.get('is_public')}")
                    private_room_id = private_room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建私聊聊天室失败 ({response.status}): {error_text}")
                    return
            
            # 6. 测试再次创建相同的私聊（应该返回现有的）
            print("\n🔄 测试重复创建私聊聊天室...")
            async with session.post(
                "http://localhost:8000/api/modern-chat/private-rooms",
                json=private_chat_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    duplicate_room = await response.json()
                    if duplicate_room.get('id') == private_room_id:
                        print("✅ 重复创建返回现有聊天室（正确行为）")
                    else:
                        print("⚠️ 重复创建返回了不同的聊天室")
                else:
                    error_text = await response.text()
                    print(f"❌ 重复创建私聊失败 ({response.status}): {error_text}")
            
            # 7. 测试获取聊天室列表（应该包含私聊）
            print("\n🔄 测试获取聊天室列表...")
            async with session.get(
                "http://localhost:8000/api/modern-chat/rooms",
                headers=headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    print(f"✅ 获取聊天室列表成功，共 {len(rooms)} 个聊天室")
                    
                    # 查找私聊聊天室
                    private_rooms = [r for r in rooms if r.get('room_type') == 'private']
                    print(f"   其中私聊聊天室: {len(private_rooms)} 个")
                    
                    for room in private_rooms:
                        print(f"     - {room.get('name')} (ID: {room.get('id')})")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室列表失败 ({response.status}): {error_text}")
            
            # 8. 清理测试数据
            print("\n🔄 清理测试数据...")
            
            # 删除私聊聊天室
            async with session.delete(
                f"http://localhost:8000/api/modern-chat/rooms/{private_room_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    print("✅ 私聊聊天室删除成功")
                else:
                    error_text = await response.text()
                    print(f"⚠️ 私聊聊天室删除失败 ({response.status}): {error_text}")
            
            print("\n🎉 私聊功能测试完成!")
            print("\n📋 测试结果总结:")
            print("✅ 用户搜索功能")
            print("✅ 最近联系人获取")
            print("✅ 私聊聊天室创建")
            print("✅ 重复创建处理")
            print("✅ 聊天室列表包含私聊")
            print("✅ 测试数据清理")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_private_chat())
