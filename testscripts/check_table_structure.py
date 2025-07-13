#!/usr/bin/env python3
"""
检查数据库表结构
"""

import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def check_table_structure():
    """检查数据库表结构"""
    
    print("🚀 开始检查数据库表结构...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查chat_rooms表结构
            print("🔄 检查chat_rooms表结构...")
            result = await db.execute(text("PRAGMA table_info(chat_rooms)"))
            columns = result.fetchall()
            
            print("✅ chat_rooms表字段:")
            for column in columns:
                cid, name, type_, notnull, default_value, pk = column
                print(f"   {name}: {type_} (默认值: {default_value}, 非空: {bool(notnull)}, 主键: {bool(pk)})")
            
            # 检查是否有allow_search字段
            has_allow_search = any(col[1] == 'allow_search' for col in columns)
            has_enable_invite_code = any(col[1] == 'enable_invite_code' for col in columns)
            has_invite_code = any(col[1] == 'invite_code' for col in columns)
            
            print(f"\n字段检查:")
            print(f"   allow_search: {'✅ 存在' if has_allow_search else '❌ 不存在'}")
            print(f"   enable_invite_code: {'✅ 存在' if has_enable_invite_code else '❌ 不存在'}")
            print(f"   invite_code: {'✅ 存在' if has_invite_code else '❌ 不存在'}")
            
            # 如果字段不存在，显示如何添加
            if not has_allow_search:
                print("\n需要添加allow_search字段:")
                print("   ALTER TABLE chat_rooms ADD COLUMN allow_search BOOLEAN DEFAULT 0;")
            
            if not has_enable_invite_code:
                print("\n需要添加enable_invite_code字段:")
                print("   ALTER TABLE chat_rooms ADD COLUMN enable_invite_code BOOLEAN DEFAULT 1;")
            
            if not has_invite_code:
                print("\n需要添加invite_code字段:")
                print("   ALTER TABLE chat_rooms ADD COLUMN invite_code VARCHAR(32);")
                print("   ALTER TABLE chat_rooms ADD COLUMN invite_code_expires_at DATETIME;")
            
            print("\n🎉 表结构检查完成!")
            
        except Exception as e:
            print(f"❌ 检查过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())
