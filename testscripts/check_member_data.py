#!/usr/bin/env python3
"""
检查成员数据
"""

import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def check_member_data():
    """检查成员数据"""
    
    print("🚀 检查成员数据...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查成员数据
            print("🔄 检查成员数据...")
            result = await db.execute(text("""
                SELECT * FROM chat_room_members_new
            """))
            members = result.fetchall()
            
            print(f"✅ 成员数据，共 {len(members)} 条:")
            for member in members:
                print(f"   {dict(member._mapping)}")
            
            # 检查聊天室数据
            print(f"\n🔄 检查聊天室数据...")
            result = await db.execute(text("""
                SELECT id, name, created_by FROM chat_rooms
            """))
            rooms = result.fetchall()
            
            print(f"✅ 聊天室数据，共 {len(rooms)} 条:")
            for room in rooms:
                print(f"   {dict(room._mapping)}")
            
            # 如果没有成员数据，添加创建者为成员
            if len(members) == 0 and len(rooms) > 0:
                print(f"\n🔄 添加聊天室创建者为成员...")
                for room in rooms:
                    room_id = room.id
                    created_by = room.created_by
                    
                    await db.execute(text("""
                        INSERT INTO chat_room_members_new (room_id, user_id, role, joined_at)
                        VALUES (:room_id, :user_id, 'creator', datetime('now'))
                    """), {"room_id": room_id, "user_id": created_by})
                
                await db.commit()
                print(f"✅ 已添加创建者为成员")
            
            print("\n🎉 检查完成!")
            
        except Exception as e:
            print(f"❌ 检查过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_member_data())
