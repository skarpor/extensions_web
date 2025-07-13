#!/usr/bin/env python3
"""
创建私密聊天室进行测试
"""

import asyncio
import aiohttp

async def create_private_room():
    """创建私密聊天室"""
    
    print("🚀 开始创建私密聊天室...\n")
    
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
                    admin_login = await response.json()
                    print(f"✅ 管理员登录成功")
                    admin_token = admin_login.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败 ({response.status}): {error_text}")
                    return
            
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # 2. 创建私密聊天室（允许搜索）
            print("\n🔄 创建私密聊天室（允许搜索）...")
            room_data = {
                "name": "私密测试聊天室",
                "description": "这是一个私密的测试聊天室，需要申请加入",
                "room_type": "group",
                "is_public": False,
                "max_members": 100,
                "allow_search": True,
                "enable_invite_code": True
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/rooms",
                json=room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 私密聊天室创建成功")
                    print(f"   聊天室名称: {room.get('name')}")
                    print(f"   聊天室ID: {room.get('id')}")
                    print(f"   聊天室类型: {room.get('room_type')}")
                    print(f"   是否公开: {room.get('is_public')}")
                    print(f"   允许搜索: {room.get('allow_search', 'N/A')}")
                    print(f"   启用邀请码: {room.get('enable_invite_code', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败 ({response.status}): {error_text}")
                    try:
                        error_data = json.loads(error_text)
                        print(f"   错误详情: {error_data}")
                    except:
                        pass
                    return
            
            # 3. 创建私密聊天室（不允许搜索）
            print("\n🔄 创建私密聊天室（不允许搜索）...")
            room_data2 = {
                "name": "秘密聊天室",
                "description": "这是一个秘密聊天室，不允许被搜索",
                "room_type": "group",
                "is_public": False,
                "max_members": 50,
                "allow_search": False,
                "enable_invite_code": True
            }
            
            async with session.post(
                "http://localhost:8000/api/modern-chat/rooms",
                json=room_data2,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room2 = await response.json()
                    print(f"✅ 秘密聊天室创建成功")
                    print(f"   聊天室名称: {room2.get('name')}")
                    print(f"   聊天室ID: {room2.get('id')}")
                    print(f"   聊天室类型: {room2.get('room_type')}")
                    print(f"   允许搜索: {room2.get('allow_search', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 创建秘密聊天室失败 ({response.status}): {error_text}")
            
            print("\n🎉 私密聊天室创建完成!")
            
        except Exception as e:
            print(f"❌ 创建过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(create_private_room())
