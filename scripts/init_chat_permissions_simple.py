#!/usr/bin/env python3
"""
简单的聊天室权限初始化脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from database import async_session_maker

async def init_chat_permissions():
    """初始化聊天室权限"""
    
    print("🚀 开始初始化聊天室权限...\n")
    
    async with async_session_maker() as db:
        try:
            # 1. 创建聊天室权限分组
            print("🔄 创建聊天室权限分组...")
            
            # 检查是否已存在聊天室权限分组
            group_check = await db.execute(
                text("SELECT id FROM permission_groups WHERE code = 'chat_management'")
            )
            existing_group = group_check.fetchone()
            
            if not existing_group:
                # 创建权限分组
                await db.execute(text("""
                    INSERT INTO permission_groups (code, name, description, sort_order, icon)
                    VALUES ('chat_management', '聊天室管理', '聊天室相关权限管理', 3, 'ChatDotRound')
                """))
                print("✅ 聊天室权限分组创建成功")
            else:
                print("✅ 聊天室权限分组已存在")
            
            # 获取分组ID
            group_result = await db.execute(
                text("SELECT id FROM permission_groups WHERE code = 'chat_management'")
            )
            group_id = group_result.fetchone()[0]
            
            # 2. 创建聊天室权限
            print("\n🔄 创建聊天室权限...")
            
            chat_permissions = [
                ("chat:room:view_all", "查看所有聊天室", "/api/modern-chat/rooms", "可以查看所有聊天室，包括不属于自己的聊天室"),
                ("chat:room:create", "创建聊天室", "/api/modern-chat/rooms", "可以创建新的聊天室"),
                ("chat:room:edit_all", "编辑所有聊天室", "/api/modern-chat/rooms/*", "可以编辑所有聊天室，包括不属于自己的聊天室"),
                ("chat:room:delete_all", "删除所有聊天室", "/api/modern-chat/rooms/*", "可以删除所有聊天室，包括不属于自己的聊天室"),
                ("chat:room:manage_members", "管理聊天室成员", "/api/modern-chat/rooms/*/members", "可以管理聊天室成员，添加或移除成员"),
                ("chat:message:view_all", "查看所有消息", "/api/modern-chat/rooms/*/messages", "可以查看所有聊天室的消息"),
                ("chat:message:delete_all", "删除所有消息", "/api/modern-chat/messages/*", "可以删除任何用户的消息"),
                ("chat:private:access_all", "访问所有私聊", "/api/modern-chat/private-rooms", "可以访问和查看所有用户的私聊")
            ]
            
            permission_ids = []
            for code, name, url, description in chat_permissions:
                # 检查权限是否已存在
                perm_check = await db.execute(
                    text("SELECT id FROM permissions WHERE code = :code"),
                    {"code": code}
                )
                existing_perm = perm_check.fetchone()
                
                if not existing_perm:
                    # 创建权限
                    result = await db.execute(text("""
                        INSERT INTO permissions (code, name, url, description, group_id)
                        VALUES (:code, :name, :url, :description, :group_id)
                        RETURNING id
                    """), {
                        "code": code,
                        "name": name,
                        "url": url,
                        "description": description,
                        "group_id": group_id
                    })
                    perm_id = result.fetchone()[0]
                    permission_ids.append(perm_id)
                    print(f"✅ 权限创建: {name}")
                else:
                    permission_ids.append(existing_perm[0])
                    print(f"✅ 权限已存在: {name}")
            
            # 3. 创建聊天室管理员角色
            print("\n🔄 创建聊天室管理员角色...")
            
            # 检查是否已存在聊天室管理员角色
            role_check = await db.execute(
                text("SELECT id FROM roles WHERE name = 'chat_admin'")
            )
            existing_role = role_check.fetchone()
            
            if not existing_role:
                # 创建角色
                result = await db.execute(text("""
                    INSERT INTO roles (name, description)
                    VALUES ('chat_admin', '聊天室管理员，拥有所有聊天室管理权限')
                    RETURNING id
                """))
                role_id = result.fetchone()[0]
                print("✅ 聊天室管理员角色创建成功")
            else:
                role_id = existing_role[0]
                print("✅ 聊天室管理员角色已存在")
            
            # 4. 为聊天室管理员角色分配权限
            print("\n🔄 为聊天室管理员角色分配权限...")
            
            permissions_added = 0
            for perm_id in permission_ids:
                # 检查权限是否已分配
                check_result = await db.execute(text("""
                    SELECT 1 FROM role_permission 
                    WHERE role_id = :role_id AND permission_id = :permission_id
                """), {"role_id": role_id, "permission_id": perm_id})
                
                if not check_result.fetchone():
                    # 分配权限
                    await db.execute(text("""
                        INSERT INTO role_permission (role_id, permission_id)
                        VALUES (:role_id, :permission_id)
                    """), {"role_id": role_id, "permission_id": perm_id})
                    permissions_added += 1
            
            if permissions_added > 0:
                print(f"✅ 共分配了 {permissions_added} 个权限")
            else:
                print("✅ 所有权限已分配")
            
            # 5. 为admin用户分配聊天室管理员角色
            print("\n🔄 为admin用户分配聊天室管理员角色...")
            
            # 查找admin用户
            admin_result = await db.execute(
                text("SELECT id FROM users WHERE username = 'admin'")
            )
            admin_user = admin_result.fetchone()
            
            if admin_user:
                admin_user_id = admin_user[0]
                
                # 检查admin用户是否已有聊天室管理员角色
                role_check = await db.execute(text("""
                    SELECT 1 FROM user_role 
                    WHERE user_id = :user_id AND role_id = :role_id
                """), {"user_id": admin_user_id, "role_id": role_id})
                
                if not role_check.fetchone():
                    # 分配角色
                    await db.execute(text("""
                        INSERT INTO user_role (user_id, role_id)
                        VALUES (:user_id, :role_id)
                    """), {"user_id": admin_user_id, "role_id": role_id})
                    print("✅ admin用户已分配聊天室管理员角色")
                else:
                    print("✅ admin用户已有聊天室管理员角色")
            else:
                print("⚠️ 未找到admin用户")
            
            # 提交所有更改
            await db.commit()
            
            print("\n🎉 聊天室权限初始化完成!")
            print("\n📋 权限总结:")
            print("✅ 聊天室权限分组")
            print("✅ 8个聊天室相关权限")
            print("✅ 聊天室管理员角色")
            print("✅ admin用户权限分配")
            
            # 6. 显示权限列表
            print("\n📋 聊天室权限列表:")
            for code, name, _, _ in chat_permissions:
                print(f"   - {code}: {name}")
            
        except Exception as e:
            print(f"❌ 初始化过程中发生错误: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(init_chat_permissions())
