#!/usr/bin/env python3
"""
更新现有聊天室的设置
"""

import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def update_room_settings():
    """更新现有聊天室的设置"""
    
    print("🚀 开始更新现有聊天室的设置...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 更新所有聊天室的默认设置
            print("🔄 更新聊天室默认设置...")
            
            # 为私密聊天室设置默认值
            await db.execute(text("""
                UPDATE chat_rooms 
                SET 
                    allow_search = CASE 
                        WHEN room_type = 'group' THEN 0 
                        ELSE 0 
                    END,
                    enable_invite_code = CASE 
                        WHEN room_type = 'group' THEN 1 
                        ELSE 0 
                    END
                WHERE allow_search IS NULL OR enable_invite_code IS NULL
            """))
            
            await db.commit()
            print("✅ 默认设置更新完成")
            
            # 2. 特别设置：让"私密测试聊天室"允许被搜索
            print("\n🔄 设置私密测试聊天室允许被搜索...")
            await db.execute(text("""
                UPDATE chat_rooms 
                SET allow_search = 1 
                WHERE name = '私密测试聊天室'
            """))
            
            await db.commit()
            print("✅ 私密测试聊天室设置完成")
            
            # 3. 检查更新结果
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
            
            print("\n🎉 聊天室设置更新完成!")
            
        except Exception as e:
            print(f"❌ 更新过程中发生错误: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(update_room_settings())
