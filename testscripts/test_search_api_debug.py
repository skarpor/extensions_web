#!/usr/bin/env python3
"""
调试搜索API问题
"""

import asyncio
import aiohttp

async def test_search_api_debug():
    """调试搜索API问题"""
    
    print("🚀 调试搜索API问题...\n")
    
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
            
            # 2. 获取所有聊天室
            print("\n🔄 获取所有聊天室...")
            async with session.get(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    all_rooms = await response.json()
                    print(f"✅ 获取到 {len(all_rooms)} 个聊天室:")
                    for room in all_rooms:
                        print(f"   - ID: {room.get('id')}, 名称: {room.get('name')}")
                        print(f"     类型: {room.get('room_type')}, 公开: {room.get('is_public')}")
                        print(f"     允许搜索: {room.get('allow_search')}")
                        print()
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室失败: {error_text}")
                    return
            
            # 3. 测试搜索API
            print("🔄 测试搜索API...")
            
            search_terms = ["可搜索", "不可搜索", "公开", "私密", "群"]
            
            for term in search_terms:
                print(f"\n🔍 搜索: '{term}'")
                async with session.get(
                    f"http://192.168.3.139:8000/api/modern-chat/search-rooms?q={term}",
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        search_results = await response.json()
                        print(f"✅ 找到 {len(search_results)} 个结果:")
                        for result in search_results:
                            print(f"   - ID: {result.get('id')}, 名称: {result.get('name')}")
                            print(f"     类型: {result.get('room_type')}, 公开: {result.get('is_public')}")
                            print(f"     允许搜索: {result.get('allow_search')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 搜索失败: {error_text}")
            
            # 4. 测试具体的搜索逻辑
            print(f"\n🔄 测试搜索逻辑验证...")
            
            # 应该能搜索到的：
            # - ID: 1, 可搜索私密群（已编辑）, allow_search: 1, room_type: group
            # - ID: 3, 公开聊天室, allow_search: 0, room_type: public (公开聊天室应该都能搜索)
            
            # 不应该搜索到的：
            # - ID: 2, 不可搜索私密群, allow_search: 0, room_type: group
            
            print("📋 预期搜索结果分析:")
            print("✅ 应该能搜索到:")
            print("   - 可搜索私密群（已编辑）: allow_search=1, room_type=group")
            print("   - 公开聊天室: room_type=public (所有公开聊天室)")
            print("❌ 不应该搜索到:")
            print("   - 不可搜索私密群: allow_search=0, room_type=group")
            
            # 5. 创建一个新的测试聊天室来验证
            print(f"\n🔄 创建新的测试聊天室...")
            test_room_data = {
                "name": "搜索测试专用群",
                "description": "专门用于测试搜索功能",
                "room_type": "group",
                "is_public": False,
                "max_members": 100,
                "allow_search": True,  # 明确设置为可搜索
                "enable_invite_code": True,
                "allow_member_invite": True
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=test_room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    new_room = await response.json()
                    print(f"✅ 创建新聊天室成功:")
                    print(f"   - ID: {new_room.get('id')}, 名称: {new_room.get('name')}")
                    print(f"   - 允许搜索: {new_room.get('allow_search')}")
                    
                    # 立即搜索这个新创建的聊天室
                    print(f"\n🔍 搜索新创建的聊天室...")
                    async with session.get(
                        f"http://192.168.3.139:8000/api/modern-chat/search-rooms?q=搜索测试",
                        headers=admin_headers
                    ) as search_response:
                        if search_response.status == 200:
                            search_results = await search_response.json()
                            print(f"✅ 搜索结果: {len(search_results)} 个")
                            for result in search_results:
                                print(f"   - {result.get('name')} (allow_search: {result.get('allow_search')})")
                        else:
                            error_text = await search_response.text()
                            print(f"❌ 搜索新聊天室失败: {error_text}")
                    
                    # 清理测试数据
                    print(f"\n🔄 清理测试数据...")
                    async with session.delete(
                        f"http://192.168.3.139:8000/api/modern-chat/rooms/{new_room.get('id')}",
                        headers=admin_headers
                    ) as delete_response:
                        if delete_response.status == 200:
                            print(f"✅ 测试聊天室已删除")
                        else:
                            print(f"❌ 删除测试聊天室失败")
                else:
                    error_text = await response.text()
                    print(f"❌ 创建测试聊天室失败: {error_text}")
            
            print("\n🎉 搜索API调试完成!")
            
        except Exception as e:
            print(f"❌ 调试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_search_api_debug())
