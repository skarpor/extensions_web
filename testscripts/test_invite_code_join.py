#!/usr/bin/env python3
"""
测试邀请码加入功能
"""

import asyncio
import aiohttp

async def test_invite_code_join():
    """测试邀请码加入功能"""
    
    print("🚀 测试邀请码加入功能...\n")
    
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
                    token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ tyy用户登录失败: {error_text}")
                    return
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 使用邀请码加入聊天室
            print("\n🔄 使用邀请码加入聊天室...")
            invite_code = "tfYr-kkwBb4KCR5x82R4lA"  # 从上面的测试中获取的邀请码
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms/join-by-invite",
                json={"invite_code": invite_code},
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 邀请码加入成功")
                    print(f"   消息: {result.get('message')}")
                    print(f"   聊天室ID: {result.get('room_id')}")
                    print(f"   聊天室名称: {result.get('room_name')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 邀请码加入失败 ({response.status}): {error_text}")
                    return
            
            # 3. 验证用户已成为聊天室成员
            print(f"\n🔄 验证用户已成为聊天室成员...")
            async with session.get(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                headers=headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    print(f"✅ 获取聊天室列表成功，共 {len(rooms)} 个聊天室")
                    
                    # 查找刚加入的聊天室
                    target_room = None
                    for room in rooms:
                        if room.get('name') == '测试私密聊天室':
                            target_room = room
                            break
                    
                    if target_room:
                        print(f"✅ 已成功加入聊天室")
                        print(f"   聊天室名称: {target_room.get('name')}")
                        print(f"   成员数: {target_room.get('member_count')}")
                    else:
                        print(f"❌ 未找到加入的聊天室")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室列表失败: {error_text}")
            
            # 4. 测试重复使用邀请码（应该失败）
            print(f"\n🔄 测试重复使用邀请码...")
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms/join-by-invite",
                json={"invite_code": invite_code},
                headers=headers
            ) as response:
                if response.status == 400:
                    error_data = await response.json()
                    print(f"✅ 重复使用邀请码正确被拒绝")
                    print(f"   错误信息: {error_data.get('detail')}")
                else:
                    print(f"❌ 重复使用邀请码处理异常 ({response.status})")
            
            # 5. 测试无效邀请码
            print(f"\n🔄 测试无效邀请码...")
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms/join-by-invite",
                json={"invite_code": "invalid_code_123"},
                headers=headers
            ) as response:
                if response.status == 404:
                    error_data = await response.json()
                    print(f"✅ 无效邀请码正确被拒绝")
                    print(f"   错误信息: {error_data.get('detail')}")
                else:
                    print(f"❌ 无效邀请码处理异常 ({response.status})")
            
            print("\n🎉 邀请码加入功能测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_invite_code_join())
