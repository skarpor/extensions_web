#!/usr/bin/env python3
"""
修复用户权限问题
"""

import asyncio
import aiohttp
import json

async def fix_user_permissions():
    """修复用户权限"""
    
    print("🚀 开始修复用户权限...\n")
    
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
            
            # 2. 检查权限组
            print("\n🔄 检查权限组...")
            async with session.get(
                "http://localhost:8000/api/auth/permission-groups",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    groups = await response.json()
                    print(f"✅ 权限组获取成功，共 {len(groups)} 个权限组")
                    
                    for group in groups:
                        print(f"   - {group.get('name')} (ID: {group.get('id')})")
                        
                    # 找到管理员权限组
                    admin_group = None
                    for group in groups:
                        if 'admin' in group.get('name', '').lower() or '管理员' in group.get('name', ''):
                            admin_group = group
                            break
                    
                    if admin_group:
                        print(f"\n🔄 找到管理员权限组: {admin_group.get('name')}")
                        
                        # 3. 给admin用户分配管理员权限组
                        print("🔄 给admin用户分配管理员权限组...")
                        assign_data = {
                            "permission_group_ids": [admin_group.get('id')]
                        }
                        
                        async with session.put(
                            "http://localhost:8000/api/auth/users/admin/permission-groups",
                            json=assign_data,
                            headers=admin_headers
                        ) as response:
                            if response.status == 200:
                                print("✅ 权限组分配成功")
                            else:
                                error_text = await response.text()
                                print(f"❌ 权限组分配失败 ({response.status}): {error_text}")
                    else:
                        print("❌ 未找到管理员权限组")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取权限组失败 ({response.status}): {error_text}")
            
            # 4. 检查聊天室成员资格
            print("\n🔄 检查聊天室成员资格...")
            async with session.get(
                "http://localhost:8000/api/modern-chat/rooms",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    rooms = await response.json()
                    print(f"✅ 聊天室列表获取成功，共 {len(rooms)} 个聊天室")
                    
                    for room in rooms:
                        room_id = room.get('id')
                        room_name = room.get('name')
                        print(f"\n🔄 检查聊天室 '{room_name}' (ID: {room_id}) 的成员...")
                        
                        # 获取聊天室详情
                        async with session.get(
                            f"http://localhost:8000/api/modern-chat/rooms/{room_id}",
                            headers=admin_headers
                        ) as detail_response:
                            if detail_response.status == 200:
                                room_detail = await detail_response.json()
                                members = room_detail.get('members', [])
                                print(f"   当前成员数: {len(members)}")
                                
                                # 检查admin是否是成员
                                admin_is_member = any(m.get('username') == 'admin' for m in members)
                                
                                if not admin_is_member:
                                    print(f"   admin不是成员，尝试加入...")
                                    
                                    # 尝试加入聊天室
                                    join_data = {
                                        "user_ids": [3]  # admin的ID通常是3
                                    }
                                    
                                    async with session.post(
                                        f"http://localhost:8000/api/modern-chat/rooms/{room_id}/members",
                                        json=join_data,
                                        headers=admin_headers
                                    ) as join_response:
                                        if join_response.status == 200:
                                            print("   ✅ 成功加入聊天室")
                                        else:
                                            error_text = await join_response.text()
                                            print(f"   ❌ 加入聊天室失败: {error_text}")
                                else:
                                    print("   ✅ admin已经是成员")
                            else:
                                error_text = await detail_response.text()
                                print(f"   ❌ 获取聊天室详情失败: {error_text}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取聊天室列表失败 ({response.status}): {error_text}")
            
            print("\n🎉 权限修复完成!")
            
        except Exception as e:
            print(f"❌ 修复过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(fix_user_permissions())
