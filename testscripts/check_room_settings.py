#!/usr/bin/env python3
"""
检查聊天室设置
"""

import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def check_room_settings():
    """检查聊天室设置"""
    
    print("🚀 开始检查聊天室设置...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查聊天室设置
            print("🔄 检查聊天室设置...")
            result = await db.execute(text("""
                SELECT id, name, room_type, allow_search, enable_invite_code, invite_code
                FROM chat_rooms 
                ORDER BY id
            """))
            rooms = result.fetchall()
            
            print("✅ 聊天室设置:")
            for room in rooms:
                room_id, name, room_type, allow_search, enable_invite_code, invite_code = room
                print(f"   ID: {room_id}, 名称: {name}, 类型: {room_type}")
                print(f"      允许搜索: {allow_search}, 启用邀请码: {enable_invite_code}")
                print(f"      邀请码: {invite_code or '无'}")
                print()
            
            print("🎉 检查完成!")
            
        except Exception as e:
            print(f"❌ 检查过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_room_settings())
