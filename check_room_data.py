#!/usr/bin/env python3
"""
检查数据库中的聊天室数据
"""

import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def check_room_data():
    """检查数据库中的聊天室数据"""
    
    print("🚀 开始检查数据库中的聊天室数据...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 检查所有聊天室
            print("🔄 检查所有聊天室...")
            result = await db.execute(text("""
                SELECT id, name, room_type, is_public, created_by 
                FROM chat_rooms 
                ORDER BY id
            """))
            rooms = result.fetchall()
            
            if rooms:
                print(f"✅ 找到 {len(rooms)} 个聊天室:")
                for room in rooms:
                    room_id, name, room_type, is_public, created_by = room
                    print(f"   ID: {room_id}, 名称: {name}, 类型: {room_type}, 公开: {is_public}, 创建者: {created_by}")
            else:
                print("❌ 没有找到聊天室")
                return
            
            # 2. 检查聊天室成员
            print(f"\n🔄 检查聊天室成员...")
            for room in rooms:
                room_id, name, room_type, is_public, created_by = room
                print(f"\n聊天室: {name} (ID: {room_id}, 类型: {room_type})")
                
                result = await db.execute(text("""
                    SELECT crm.user_id, u.username, crm.role, crm.joined_at
                    FROM chat_room_members_new crm
                    JOIN users u ON crm.user_id = u.id
                    WHERE crm.room_id = :room_id
                    ORDER BY crm.joined_at
                """), {"room_id": room_id})
                
                members = result.fetchall()
                
                if members:
                    print(f"   成员 ({len(members)} 人):")
                    for member in members:
                        user_id, username, role, joined_at = member
                        print(f"     - {username} (ID: {user_id}, 角色: {role}, 加入时间: {joined_at})")
                else:
                    print(f"   无成员")
            
            # 3. 检查消息
            print(f"\n🔄 检查最近的消息...")
            result = await db.execute(text("""
                SELECT m.id, m.room_id, m.content, m.message_type, u.username, m.created_at
                FROM chat_messages m
                JOIN users u ON m.sender_id = u.id
                ORDER BY m.created_at DESC
                LIMIT 10
            """))
            
            messages = result.fetchall()
            
            if messages:
                print(f"✅ 最近 {len(messages)} 条消息:")
                for message in messages:
                    msg_id, room_id, content, msg_type, username, created_at = message
                    print(f"   [{created_at}] {username} 在聊天室{room_id}: {content}")
            else:
                print("❌ 没有找到消息")
            
            print("\n🎉 数据库检查完成!")
            
        except Exception as e:
            print(f"❌ 检查过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_room_data())
