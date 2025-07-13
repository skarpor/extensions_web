#!/usr/bin/env python3
"""
检查数据库表结构
"""

import asyncio
import sqlite3
from pathlib import Path

async def check_database_tables():
    """检查数据库表结构"""
    
    print("🚀 检查数据库表结构...\n")
    
    # 数据库文件路径
    db_path = Path("data/db/app.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取所有表名
        print("🔄 获取所有表名...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("✅ 数据库中的表:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # 查找聊天室相关的表
        chat_tables = [table[0] for table in tables if 'chat' in table[0].lower() or 'room' in table[0].lower()]
        
        if chat_tables:
            print(f"\n✅ 聊天室相关的表: {chat_tables}")
            
            for table_name in chat_tables:
                print(f"\n🔄 检查表 {table_name} 的结构:")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
                
                # 查看表中的数据
                print(f"\n🔄 查看表 {table_name} 的数据:")
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   记录数: {count}")
                
                if count > 0 and count <= 5:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()
                    for row in rows:
                        print(f"   - {row}")
        else:
            print("\n❌ 未找到聊天室相关的表")
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    asyncio.run(check_database_tables())
