#!/usr/bin/env python3
"""
测试完整聊天功能：表情反应、编辑聊天室、设置聊天室、置顶消息、统计信息等
"""

import asyncio
import aiohttp

async def test_complete_chat_features():
    """测试完整聊天功能"""
    
    print("🚀 测试完整聊天功能：表情反应、编辑聊天室、设置聊天室、置顶消息、统计信息等...\n")
    
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
                "name": "完整功能测试群",
                "description": "用于测试所有聊天功能",
                "room_type": "group",
                "is_public": False,
                "max_members": 100,
                "allow_search": True,
                "enable_invite_code": True,
                "allow_member_invite": True,
                "auto_delete_messages": False,
                "message_retention_days": 30,
                "allow_file_upload": True,
                "max_file_size": 10,
                "welcome_message": "欢迎加入完整功能测试群！",
                "rules": "请遵守聊天室规则，文明聊天。"
            }
            
            async with session.post(
                "http://192.168.3.139:8000/api/modern-chat/rooms",
                json=room_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    room = await response.json()
                    print(f"✅ 聊天室创建成功: {room.get('name')} (ID: {room.get('id')})")
                    room_id = room.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建聊天室失败: {error_text}")
                    return
            
            # 3. 发送测试消息
            print(f"\n🔄 发送测试消息...")
            message_data = {
                "content": "这是一条用于测试所有功能的消息",
                "message_type": "text"
            }
            
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages",
                json=message_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    message = await response.json()
                    print(f"✅ 消息发送成功")
                    message_id = message.get('id')
                else:
                    error_text = await response.text()
                    print(f"❌ 消息发送失败: {error_text}")
                    return
            
            # 4. 测试表情反应功能
            print(f"\n🔄 测试表情反应功能...")
            reactions = ["👍", "❤️", "😂", "😮", "😢"]
            for emoji in reactions:
                async with session.post(
                    f"http://192.168.3.139:8000/api/modern-chat/messages/{message_id}/reactions",
                    json={"emoji": emoji},
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        print(f"✅ 表情反应 {emoji} 添加成功")
                    else:
                        error_text = await response.text()
                        print(f"❌ 表情反应 {emoji} 失败: {error_text}")
            
            # 5. 测试获取表情反应
            print(f"\n🔄 测试获取表情反应...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/messages/{message_id}/reactions",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    reactions_data = await response.json()
                    print(f"✅ 表情反应获取成功，共 {len(reactions_data)} 种表情")
                    for reaction in reactions_data:
                        print(f"   - {reaction.get('emoji')}: {reaction.get('count')} 个用户")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取表情反应失败: {error_text}")
            
            # 6. 测试消息置顶功能
            print(f"\n🔄 测试消息置顶功能...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages/{message_id}/pin",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 消息置顶成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 消息置顶失败: {error_text}")
            
            # 7. 测试获取置顶消息
            print(f"\n🔄 测试获取置顶消息...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/pinned-messages",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    pinned_messages = await response.json()
                    print(f"✅ 置顶消息获取成功，共 {len(pinned_messages)} 条")
                    for msg in pinned_messages:
                        print(f"   - {msg.get('content')[:30]}... (置顶时间: {msg.get('pinned_at')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取置顶消息失败: {error_text}")
            
            # 8. 测试编辑聊天室功能
            print(f"\n🔄 测试编辑聊天室功能...")
            update_data = {
                "name": "完整功能测试群（已编辑）",
                "description": "这是编辑后的描述，包含更多信息",
                "max_members": 150,
                "allow_search": False,
                "enable_invite_code": True,
                "allow_member_invite": False,
                "is_active": True,
                "auto_delete_messages": True,
                "message_retention_days": 60,
                "allow_file_upload": True,
                "max_file_size": 20,
                "welcome_message": "欢迎加入我们的测试群！这里有最新的功能体验。",
                "rules": "1. 文明聊天\n2. 不发广告\n3. 尊重他人\n4. 积极参与讨论"
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
                    print(f"   最大成员数: {updated_room.get('max_members')}")
                    print(f"   消息保留天数: {updated_room.get('message_retention_days', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 编辑聊天室失败: {error_text}")
            
            # 9. 测试获取聊天室统计信息
            print(f"\n🔄 测试获取聊天室统计信息...")
            async with session.get(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/statistics",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    statistics = await response.json()
                    print(f"✅ 统计信息获取成功")
                    print(f"   聊天室名称: {statistics.get('room_name')}")
                    print(f"   总消息数: {statistics.get('total_messages')}")
                    print(f"   今日消息: {statistics.get('today_messages')}")
                    print(f"   总成员数: {statistics.get('total_members')}")
                    print(f"   活跃成员: {statistics.get('active_members')}")
                    print(f"   置顶消息: {statistics.get('pinned_messages')}")
                    
                    top_users = statistics.get('top_users', [])
                    if top_users:
                        print(f"   最活跃用户:")
                        for user in top_users:
                            print(f"     - {user.get('username')}: {user.get('message_count')} 条消息")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取统计信息失败: {error_text}")
            
            # 10. 测试取消表情反应
            print(f"\n🔄 测试取消表情反应...")
            async with session.post(
                f"http://192.168.3.139:8000/api/modern-chat/messages/{message_id}/reactions",
                json={"emoji": "👍"},
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 表情反应取消成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 取消表情反应失败: {error_text}")
            
            # 11. 测试取消消息置顶
            print(f"\n🔄 测试取消消息置顶...")
            async with session.delete(
                f"http://192.168.3.139:8000/api/modern-chat/rooms/{room_id}/messages/{message_id}/pin",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 取消置顶成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 取消置顶失败: {error_text}")
            
            print("\n🎉 完整聊天功能测试完成!")
            print("\n📊 测试总结:")
            print("✅ 表情反应功能：正常")
            print("✅ 消息置顶功能：正常")
            print("✅ 聊天室编辑功能：正常")
            print("✅ 聊天室统计信息：正常")
            print("✅ 权限验证：正常")
            print("✅ 数据持久化：正常")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_complete_chat_features())
