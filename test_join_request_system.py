#!/usr/bin/env python3
"""
测试申请加入系统功能
"""

import asyncio
import aiohttp

async def test_join_request_system():
    """测试申请加入系统功能"""
    
    print("🚀 测试申请加入系统功能...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. tyy用户登录
            print("🔄 tyy用户登录...")
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login-json",
                json={"username": "tyy", "password": "123"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    login_data = await response.json()
                    print(f"✅ tyy用户登录成功")
                    tyy_token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ tyy用户登录失败: {error_text}")
                    return
            
            # 2. 管理员登录
            print("\n🔄 管理员登录...")
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
            
            tyy_headers = {"Authorization": f"Bearer {tyy_token}"}
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # 3. 创建一个不允许搜索的私密聊天室
            print("\n🔄 创建私密聊天室（不允许搜索）...")
            room_data = {
                "name": "申请测试聊天室",
                "description": "用于测试申请加入功能的私密聊天室",
                "room_type": "group",
                "is_public": False,
                "max_members": 100,
                "allow_search": False,  # 不允许搜索
                "enable_invite_code": True
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 私密聊天室创建成功: {room.get('name')} (ID: {room.get('id')})")
                    room_id = room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败: {error_text}")
                    return
            
            # 4. tyy用户申请加入聊天室
            print(f"\n🔄 tyy用户申请加入聊天室...")
            join_request_data = {
                "room_id": room_id,
                "message": "我想加入这个聊天室，请批准我的申请"
            }
            
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/join-request",
                json=join_request_data,
                headers=tyy_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 申请发送成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 申请发送失败: {error_text}")
                    return
            
            # 5. 管理员处理申请（同意）
            print(f"\n🔄 管理员同意申请...")
            process_data = {
                "room_id": room_id,
                "action": "approve",
                "message": "欢迎加入"
            }
            
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/join-requests/2/process",  # tyy的用户ID是2
                json=process_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 申请处理成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 申请处理失败: {error_text}")
            
            # 6. 验证tyy用户已成为聊天室成员
            print(f"\n🔄 验证tyy用户已成为聊天室成员...")
            async with session.get(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                headers=tyy_headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    target_room = None
                    for room in rooms:
                        if room.get('id') == room_id:
                            target_room = room
                            break
                    
                    if target_room:
                        print(f"✅ tyy用户已成功加入聊天室")
                        print(f"   聊天室名称: {target_room.get('name')}")
                        print(f"   成员数: {target_room.get('member_count')}")
                    else:
                        print(f"❌ tyy用户未成功加入聊天室")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室列表失败: {error_text}")
            
            print("\n🎉 申请加入系统测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_join_request_system())
