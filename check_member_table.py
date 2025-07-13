#!/usr/bin/env python3
"""
检查成员表结构
"""

import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def check_member_table():
    """检查成员表结构"""
    
    print("🚀 检查成员表结构...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查chat_room_members表结构
            print("🔄 检查chat_room_members表结构...")
            result = await db.execute(text("PRAGMA table_info(chat_room_members)"))
            columns = result.fetchall()
            
            print("✅ chat_room_members表字段:")
            for column in columns:
                cid, name, type_, notnull, default_value, pk = column
                print(f"   {name}: {type_} (默认值: {default_value}, 非空: {bool(notnull)}, 主键: {bool(pk)})")
            
            # 检查实际数据
            print(f"\n🔄 检查实际成员数据...")
            result = await db.execute(text("""
                SELECT cm.*, u.username, u.nickname, u.avatar, u.email
                FROM chat_room_members cm
                JOIN users u ON cm.user_id = u.id
                LIMIT 5
            """))
            members = result.fetchall()
            
            print("✅ 成员数据样例:")
            for member in members:
                print(f"   {dict(member._mapping)}")
            
            print("\n🎉 检查完成!")
            
        except Exception as e:
            print(f"❌ 检查过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_member_table())
