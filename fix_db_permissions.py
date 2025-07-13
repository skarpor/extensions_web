#!/usr/bin/env python3
"""
直接通过数据库修复权限问题
"""

import asyncio
from sqlalchemy import select, text
from db.session import AsyncSessionLocal

async def fix_database_permissions():
    """直接修复数据库权限"""
    
    print("🚀 开始修复数据库权限...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 检查用户
            print("🔄 检查用户...")
            result = await db.execute(text("SELECT id, username FROM users WHERE username = 'admin'"))
            admin_user = result.fetchone()
            
            if admin_user:
                admin_id = admin_user[0]
                print(f"✅ 找到admin用户，ID: {admin_id}")
            else:
                print("❌ 未找到admin用户")
                return
            
            # 2. 检查聊天权限组
            print("\n🔄 检查聊天权限组...")
            result = await db.execute(text("SELECT id, name FROM permission_groups WHERE name LIKE '%聊天%'"))
            chat_groups = result.fetchall()
            
            if chat_groups:
                for group in chat_groups:
                    print(f"   找到聊天权限组: {group[1]} (ID: {group[0]})")
                
                chat_group_id = chat_groups[0][0]  # 使用第一个聊天权限组
                
                # 3. 检查用户是否已有此权限组
                print(f"\n🔄 检查用户权限组关联...")
                result = await db.execute(text("""
                    SELECT * FROM user_permission_groups 
                    WHERE user_id = :user_id AND permission_group_id = :group_id
                """), {"user_id": admin_id, "group_id": chat_group_id})
                
                existing = result.fetchone()
                
                if existing:
                    print("✅ 用户已有聊天权限组")
                else:
                    print("🔄 分配聊天权限组...")
                    await db.execute(text("""
                        INSERT INTO user_permission_groups (user_id, permission_group_id)
                        VALUES (:user_id, :group_id)
                    """), {"user_id": admin_id, "group_id": chat_group_id})
                    
                    await db.commit()
                    print("✅ 聊天权限组分配成功")
            else:
                print("❌ 未找到聊天权限组")
            
            # 4. 检查聊天室
            print("\n🔄 检查聊天室...")
            result = await db.execute(text("SELECT id, name, creator_id FROM chat_rooms"))
            rooms = result.fetchall()
            
            if rooms:
                print(f"✅ 找到 {len(rooms)} 个聊天室")
                
                for room in rooms:
                    room_id, room_name, creator_id = room
                    print(f"\n🔄 处理聊天室: {room_name} (ID: {room_id})")
                    
                    # 检查admin是否是成员
                    result = await db.execute(text("""
                        SELECT * FROM chat_room_members 
                        WHERE room_id = :room_id AND user_id = :user_id
                    """), {"room_id": room_id, "user_id": admin_id})
                    
                    existing_member = result.fetchone()
                    
                    if existing_member:
                        print("   ✅ admin已是成员")
                    else:
                        print("   🔄 添加admin为成员...")
                        await db.execute(text("""
                            INSERT INTO chat_room_members (room_id, user_id, joined_at)
                            VALUES (:room_id, :user_id, NOW())
                        """), {"room_id": room_id, "user_id": admin_id})
                        
                        print("   ✅ 成功添加为成员")
                
                await db.commit()
                print("\n✅ 聊天室成员关系更新完成")
            else:
                print("❌ 未找到聊天室")
            
            # 5. 验证权限
            print("\n🔄 验证最终权限...")
            result = await db.execute(text("""
                SELECT DISTINCT p.name 
                FROM permissions p
                JOIN permission_group_permissions pgp ON p.id = pgp.permission_id
                JOIN user_permission_groups upg ON pgp.permission_group_id = upg.permission_group_id
                WHERE upg.user_id = :user_id AND p.name LIKE 'chat:%'
            """), {"user_id": admin_id})
            
            chat_permissions = result.fetchall()
            
            if chat_permissions:
                print("✅ 用户聊天权限:")
                for perm in chat_permissions:
                    print(f"   - {perm[0]}")
            else:
                print("❌ 用户没有聊天权限")
            
            print("\n🎉 数据库权限修复完成!")
            
        except Exception as e:
            print(f"❌ 修复过程中发生错误: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(fix_database_permissions())
