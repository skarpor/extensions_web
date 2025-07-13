#!/usr/bin/env python3
"""
检查正确的数据库文件：database.sqlite
"""

import asyncio
import sqlite3
from pathlib import Path

async def check_correct_database():
    """检查正确的数据库文件"""
    
    print("🚀 检查正确的数据库文件：database.sqlite...\n")
    
    # 正确的数据库文件路径
    db_path = Path("database.sqlite")
    
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
        
        # 特别检查chat_rooms表
        print(f"\n🔄 特别检查chat_rooms表...")
        try:
            cursor.execute("PRAGMA table_info(chat_rooms)")
            columns = cursor.fetchall()
            
            if columns:
                print("✅ chat_rooms表结构:")
                for col in columns:
                    print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
                
                # 检查是否有allow_search字段
                column_names = [col[1] for col in columns]
                if 'allow_search' in column_names:
                    print("✅ allow_search字段存在")
                else:
                    print("❌ allow_search字段不存在")
                
                # 查看现有数据
                cursor.execute("SELECT id, name, allow_search, room_type, is_public FROM chat_rooms LIMIT 10")
                rooms = cursor.fetchall()
                
                if rooms:
                    print("\n✅ 现有聊天室数据:")
                    for room in rooms:
                        print(f"   - ID: {room[0]}, 名称: {room[1]}, 允许搜索: {room[2]}, 类型: {room[3]}, 公开: {room[4]}")
                else:
                    print("\n✅ 暂无聊天室数据")
            else:
                print("❌ chat_rooms表不存在")
        except sqlite3.Error as e:
            print(f"❌ 检查chat_rooms表失败: {e}")
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    asyncio.run(check_correct_database())
