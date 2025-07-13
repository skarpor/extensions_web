#!/usr/bin/env python3
"""
更新聊天室搜索设置
"""

import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def update_room_search():
    """更新聊天室搜索设置"""
    
    print("🚀 开始更新聊天室搜索设置...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 设置第一个聊天室允许搜索
            print("🔄 设置聊天室1允许搜索...")
            await db.execute(text("""
                UPDATE chat_rooms 
                SET allow_search = 1 
                WHERE id = 1
            """))
            
            await db.commit()
            print("✅ 聊天室1设置完成")
            
            # 检查更新结果
            print("\n🔄 检查更新结果...")
            result = await db.execute(text("""
                SELECT id, name, room_type, allow_search, enable_invite_code
                FROM chat_rooms 
                ORDER BY id
            """))
            rooms = result.fetchall()
            
            print("✅ 聊天室设置:")
            for room in rooms:
                room_id, name, room_type, allow_search, enable_invite_code = room
                print(f"   ID: {room_id}, 名称: {name}, 类型: {room_type}")
                print(f"      允许搜索: {bool(allow_search)}, 启用邀请码: {bool(enable_invite_code)}")
            
            print("\n🎉 更新完成!")
            
        except Exception as e:
            print(f"❌ 更新过程中发生错误: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(update_room_search())
