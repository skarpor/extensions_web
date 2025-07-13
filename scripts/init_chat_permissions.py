#!/usr/bin/env python3
"""
初始化聊天室权限
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from models.user import PermissionGroup, Permission, Role, role_permission

async def init_chat_permissions():
    """初始化聊天室权限"""
    
    print("🚀 开始初始化聊天室权限...\n")
    
    async for db in get_db():
        try:
            # 1. 创建聊天室权限分组
            print("🔄 创建聊天室权限分组...")
            
            # 检查是否已存在聊天室权限分组
            group_query = select(PermissionGroup).where(PermissionGroup.code == "chat_management")
            group_result = await db.execute(group_query)
            chat_group = group_result.scalar_one_or_none()
            
            if not chat_group:
                chat_group = PermissionGroup(
                    code="chat_management",
                    name="聊天室管理",
                    description="聊天室相关权限管理",
                    sort_order=3,
                    icon="ChatDotRound"
                )
                db.add(chat_group)
                await db.commit()
                await db.refresh(chat_group)
                print("✅ 聊天室权限分组创建成功")
            else:
                print("✅ 聊天室权限分组已存在")
            
            # 2. 创建聊天室权限
            print("\n🔄 创建聊天室权限...")
            
            chat_permissions = [
                {
                    "code": "chat:room:view_all",
                    "name": "查看所有聊天室",
                    "url": "/api/modern-chat/rooms",
                    "description": "可以查看所有聊天室，包括不属于自己的聊天室"
                },
                {
                    "code": "chat:room:create",
                    "name": "创建聊天室",
                    "url": "/api/modern-chat/rooms",
                    "description": "可以创建新的聊天室"
                },
                {
                    "code": "chat:room:edit_all",
                    "name": "编辑所有聊天室",
                    "url": "/api/modern-chat/rooms/*",
                    "description": "可以编辑所有聊天室，包括不属于自己的聊天室"
                },
                {
                    "code": "chat:room:delete_all",
                    "name": "删除所有聊天室",
                    "url": "/api/modern-chat/rooms/*",
                    "description": "可以删除所有聊天室，包括不属于自己的聊天室"
                },
                {
                    "code": "chat:room:manage_members",
                    "name": "管理聊天室成员",
                    "url": "/api/modern-chat/rooms/*/members",
                    "description": "可以管理聊天室成员，添加或移除成员"
                },
                {
                    "code": "chat:message:view_all",
                    "name": "查看所有消息",
                    "url": "/api/modern-chat/rooms/*/messages",
                    "description": "可以查看所有聊天室的消息"
                },
                {
                    "code": "chat:message:delete_all",
                    "name": "删除所有消息",
                    "url": "/api/modern-chat/messages/*",
                    "description": "可以删除任何用户的消息"
                },
                {
                    "code": "chat:private:access_all",
                    "name": "访问所有私聊",
                    "url": "/api/modern-chat/private-rooms",
                    "description": "可以访问和查看所有用户的私聊"
                }
            ]
            
            created_permissions = []
            for perm_data in chat_permissions:
                # 检查权限是否已存在
                perm_query = select(Permission).where(Permission.code == perm_data["code"])
                perm_result = await db.execute(perm_query)
                existing_perm = perm_result.scalar_one_or_none()
                
                if not existing_perm:
                    permission = Permission(
                        code=perm_data["code"],
                        name=perm_data["name"],
                        url=perm_data["url"],
                        description=perm_data["description"],
                        group_id=chat_group.id
                    )
                    db.add(permission)
                    created_permissions.append(permission)
                    print(f"✅ 权限创建: {perm_data['name']}")
                else:
                    created_permissions.append(existing_perm)
                    print(f"✅ 权限已存在: {perm_data['name']}")
            
            await db.commit()
            
            # 刷新权限对象
            for perm in created_permissions:
                await db.refresh(perm)
            
            # 3. 创建聊天室管理员角色
            print("\n🔄 创建聊天室管理员角色...")
            
            # 检查是否已存在聊天室管理员角色
            role_query = select(Role).where(Role.name == "chat_admin")
            role_result = await db.execute(role_query)
            chat_admin_role = role_result.scalar_one_or_none()
            
            if not chat_admin_role:
                chat_admin_role = Role(
                    name="chat_admin",
                    description="聊天室管理员，拥有所有聊天室管理权限"
                )
                db.add(chat_admin_role)
                await db.commit()
                await db.refresh(chat_admin_role)
                print("✅ 聊天室管理员角色创建成功")
            else:
                print("✅ 聊天室管理员角色已存在")
            
            # 4. 为聊天室管理员角色分配权限
            print("\n🔄 为聊天室管理员角色分配权限...")
            
            # 获取当前角色的权限
            await db.refresh(chat_admin_role, ['permissions'])
            current_permission_codes = {perm.code for perm in chat_admin_role.permissions}
            
            # 添加缺失的权限
            permissions_added = 0
            for permission in created_permissions:
                if permission.code not in current_permission_codes:
                    # 使用原生SQL插入关联关系
                    from sqlalchemy import text
                    insert_stmt = text(
                        "INSERT INTO role_permission (role_id, permission_id) VALUES (:role_id, :permission_id)"
                    )
                    await db.execute(insert_stmt, {
                        "role_id": chat_admin_role.id,
                        "permission_id": permission.id
                    })
                    permissions_added += 1
                    print(f"✅ 权限分配: {permission.name}")
            
            if permissions_added > 0:
                await db.commit()
                print(f"✅ 共分配了 {permissions_added} 个权限")
            else:
                print("✅ 所有权限已分配")
            
            # 5. 为admin用户分配聊天室管理员角色
            print("\n🔄 为admin用户分配聊天室管理员角色...")
            
            from models.user import User, user_role
            
            # 查找admin用户
            admin_query = select(User).where(User.username == "admin")
            admin_result = await db.execute(admin_query)
            admin_user = admin_result.scalar_one_or_none()
            
            if admin_user:
                # 检查admin用户是否已有聊天室管理员角色
                await db.refresh(admin_user, ['roles'])
                has_chat_admin_role = any(role.name == "chat_admin" for role in admin_user.roles)
                
                if not has_chat_admin_role:
                    # 使用原生SQL插入用户角色关联
                    from sqlalchemy import text
                    insert_stmt = text(
                        "INSERT INTO user_role (user_id, role_id) VALUES (:user_id, :role_id)"
                    )
                    await db.execute(insert_stmt, {
                        "user_id": admin_user.id,
                        "role_id": chat_admin_role.id
                    })
                    await db.commit()
                    print("✅ admin用户已分配聊天室管理员角色")
                else:
                    print("✅ admin用户已有聊天室管理员角色")
            else:
                print("⚠️ 未找到admin用户")
            
            print("\n🎉 聊天室权限初始化完成!")
            print("\n📋 权限总结:")
            print("✅ 聊天室权限分组")
            print("✅ 8个聊天室相关权限")
            print("✅ 聊天室管理员角色")
            print("✅ admin用户权限分配")
            
            # 6. 显示权限列表
            print("\n📋 聊天室权限列表:")
            for perm in created_permissions:
                print(f"   - {perm.code}: {perm.name}")
            
        except Exception as e:
            print(f"❌ 初始化过程中发生错误: {e}")
            await db.rollback()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(init_chat_permissions())
