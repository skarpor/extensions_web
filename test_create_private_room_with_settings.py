#!/usr/bin/env python3
"""
测试创建带设置的私密聊天室
"""

import asyncio
import aiohttp

async def test_create_private_room_with_settings():
    """测试创建带设置的私密聊天室"""
    
    print("🚀 测试创建带设置的私密聊天室...\n")
    
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
                    token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败: {error_text}")
                    return
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 创建私密聊天室（允许搜索，启用邀请码）
            print("\n🔄 创建私密聊天室（允许搜索，启用邀请码）...")
            room_data = {
                "name": "测试私密聊天室",
                "description": "这是一个测试私密聊天室，允许搜索和邀请码",
                "room_type": "group",
                "is_public": False,
                "max_members": 100,
                "allow_member_invite": True,
                "allow_member_modify_info": False,
                "message_history_visible": True,
                "allow_search": True,  # 允许搜索
                "enable_invite_code": True  # 启用邀请码
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=room_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 私密聊天室创建成功")
                    print(f"   聊天室名称: {room.get('name')}")
                    print(f"   聊天室ID: {room.get('id')}")
                    print(f"   聊天室类型: {room.get('room_type')}")
                    print(f"   是否公开: {room.get('is_public')}")
                    room_id = room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败 ({response.status}): {error_text}")
                    return
            
            # 3. 检查数据库中的设置
            print(f"\n🔄 检查聊天室设置...")
            # 这里我们通过搜索API来验证设置是否生效
            
            # 4. 测试搜索功能
            print(f"\n🔄 测试搜索功能...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/search-rooms?q=测试",
                headers=headers
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"✅ 搜索成功，找到 {len(search_results)} 个聊天室")
                    
                    # 检查是否包含我们刚创建的聊天室
                    found_room = None
                    for room in search_results:
                        if room.get('id') == room_id:
                            found_room = room
                            break
                    
                    if found_room:
                        print(f"✅ 新创建的聊天室可以被搜索到")
                        print(f"   名称: {found_room.get('name')}")
                        print(f"   描述: {found_room.get('description')}")
                        print(f"   成员数: {found_room.get('member_count')}")
                        print(f"   是否成员: {found_room.get('is_member')}")
                    else:
                        print(f"❌ 新创建的聊天室无法被搜索到")
                else:
                    error_text = await response.text()
                    print(f"❌ 搜索失败: {error_text}")
            
            # 5. 测试邀请码功能
            if room_id:
                print(f"\n🔄 测试邀请码功能...")
                async with session.get(
                    f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/invite-code",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        invite_info = await response.json()
                        print(f"✅ 邀请码获取成功")
                        print(f"   邀请码: {invite_info.get('invite_code')}")
                        print(f"   过期时间: {invite_info.get('expires_at')}")
                        print(f"   是否过期: {invite_info.get('is_expired')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 获取邀请码失败: {error_text}")
            
            print("\n🎉 测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_create_private_room_with_settings())
