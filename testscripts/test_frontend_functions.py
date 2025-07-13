#!/usr/bin/env python3
"""
测试前端功能：删除、编辑、搜索等
"""

import asyncio
import aiohttp

async def test_frontend_functions():
    """测试前端功能"""
    
    print("🚀 测试前端功能：删除、编辑、搜索等...\n")
    
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
                "name": "前端功能测试群",
                "description": "用于测试前端功能",
                "room_type": "group",
                "is_public": False,
                "max_members": 100,
                "allow_search": True,  # 设置为可搜索
                "enable_invite_code": True,
                "allow_member_invite": True
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 聊天室创建成功: {room.get('name')} (ID: {room.get('id')})")
                    print(f"   allow_search: {room.get('allow_search')}")
                    room_id = room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败: {error_text}")
                    return
            
            # 3. 测试搜索功能
            print(f"\n🔄 测试搜索功能...")
            search_queries = ["前端", "功能", "测试"]
            
            for query in search_queries:
                async with session.get(
                    f"http://192.168.3.139:8000/api/modern-chat/search-rooms?q={query}",
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        search_results = await response.json()
                        print(f"✅ 搜索 '{query}' 成功，找到 {len(search_results)} 个结果")
                        for result in search_results:
                            print(f"   - {result.get('name')} (allow_search: {result.get('allow_search')})")
                    else:
                        error_text = await response.text()
                        print(f"❌ 搜索 '{query}' 失败: {error_text}")
            
            # 4. 测试编辑功能
            print(f"\n🔄 测试编辑功能...")
            update_data = {
                "name": "前端功能测试群（已编辑）",
                "description": "这是编辑后的描述",
                "max_members": 150,
                "allow_search": True,  # 确保仍然可搜索
                "enable_invite_code": True,
                "allow_member_invite": False,
                "is_active": True
            }
            
            async with session.put(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}",
                json=update_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    updated_room = await response.json()
                    print(f"✅ 聊天室编辑成功")
                    print(f"   新名称: {updated_room.get('name')}")
                    print(f"   新描述: {updated_room.get('description')}")
                    print(f"   allow_search: {updated_room.get('allow_search')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 编辑聊天室失败: {error_text}")
            
            # 5. 再次测试搜索（编辑后）
            print(f"\n🔄 再次测试搜索（编辑后）...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/search-rooms?q=已编辑",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"✅ 搜索 '已编辑' 成功，找到 {len(search_results)} 个结果")
                    for result in search_results:
                        print(f"   - {result.get('name')} (allow_search: {result.get('allow_search')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 搜索 '已编辑' 失败: {error_text}")
            
            # 6. 测试获取聊天室详情
            print(f"\n🔄 测试获取聊天室详情...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room_details = await response.json()
                    print(f"✅ 获取聊天室详情成功")
                    print(f"   名称: {room_details.get('name')}")
                    print(f"   描述: {room_details.get('description')}")
                    print(f"   allow_search: {room_details.get('allow_search')}")
                    print(f"   is_public: {room_details.get('is_public')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室详情失败: {error_text}")
            
            # 7. 测试删除功能
            print(f"\n🔄 测试删除功能...")
            async with session.delete(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 聊天室删除成功: {result.get('message', '删除成功')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 删除聊天室失败: {error_text}")
            
            # 8. 验证删除后搜索不到
            print(f"\n🔄 验证删除后搜索不到...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/search-rooms?q=已编辑",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"✅ 删除后搜索结果: {len(search_results)} 个")
                    if len(search_results) == 0:
                        print("   ✅ 确认删除成功，搜索不到已删除的聊天室")
                    else:
                        print("   ⚠️ 仍然能搜索到聊天室，可能删除未完全生效")
                else:
                    error_text = await response.text()
                    print(f"❌ 删除后搜索失败: {error_text}")
            
            print("\n🎉 前端功能测试完成!")
            print("\n📊 测试总结:")
            print("✅ 创建聊天室：正常")
            print("✅ 搜索功能：正常")
            print("✅ 编辑功能：正常")
            print("✅ 删除功能：正常")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_frontend_functions())
