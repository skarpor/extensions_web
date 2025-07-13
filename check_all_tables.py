#!/usr/bin/env python3
"""
检查所有表
"""

import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def check_all_tables():
    """检查所有表"""
    
    print("🚀 检查所有表...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取所有表名
            print("🔄 获取所有表名...")
            result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = result.fetchall()
            
            print("✅ 数据库中的表:")
            for table in tables:
                table_name = table[0]
                print(f"   - {table_name}")
                
                # 检查聊天相关的表
                if 'chat' in table_name.lower():
                    print(f"     检查表结构...")
                    result = await db.execute(text(f"PRAGMA table_info({table_name})"))
                    columns = result.fetchall()
                    for column in columns:
                        cid, name, type_, notnull, default_value, pk = column
                        print(f"       {name}: {type_}")
            
            print("\n🎉 检查完成!")
            
        except Exception as e:
            print(f"❌ 检查过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_tables())
