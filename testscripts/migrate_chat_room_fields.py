#!/usr/bin/env python3
"""
数据库迁移脚本：为聊天室表添加新字段
"""

import asyncio
import sqlite3
from pathlib import Path

async def migrate_chat_room_fields():
    """为聊天室表添加新字段"""
    
    print("🚀 开始数据库迁移：为聊天室表添加新字段...\n")
    
    # 数据库文件路径
    db_path = Path("data/db/app.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查表结构
        print("🔄 检查当前表结构...")
        cursor.execute("PRAGMA table_info(chat_rooms)")
        columns = cursor.fetchall()
        
        existing_columns = [col[1] for col in columns]
        print(f"✅ 当前字段: {existing_columns}")
        
        # 需要添加的新字段
        new_fields = [
            ("auto_delete_messages", "BOOLEAN DEFAULT 0"),
            ("message_retention_days", "INTEGER DEFAULT 30"),
            ("allow_file_upload", "BOOLEAN DEFAULT 1"),
            ("max_file_size", "INTEGER DEFAULT 10"),
            ("welcome_message", "TEXT"),
            ("rules", "TEXT")
        ]
        
        # 添加缺失的字段
        for field_name, field_type in new_fields:
            if field_name not in existing_columns:
                print(f"🔄 添加字段: {field_name}")
                try:
                    cursor.execute(f"ALTER TABLE chat_rooms ADD COLUMN {field_name} {field_type}")
                    print(f"✅ 成功添加字段: {field_name}")
                except sqlite3.Error as e:
                    print(f"❌ 添加字段 {field_name} 失败: {e}")
            else:
                print(f"✅ 字段已存在: {field_name}")
        
        # 检查更新后的表结构
        print("\n🔄 检查更新后的表结构...")
        cursor.execute("PRAGMA table_info(chat_rooms)")
        columns = cursor.fetchall()
        
        print("✅ 更新后的字段:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # 提交更改
        conn.commit()
        print("\n✅ 数据库迁移完成!")
        
        # 测试查询
        print("\n🔄 测试查询现有聊天室...")
        cursor.execute("SELECT id, name, allow_search, auto_delete_messages FROM chat_rooms LIMIT 5")
        rooms = cursor.fetchall()
        
        if rooms:
            print("✅ 现有聊天室:")
            for room in rooms:
                print(f"   - ID: {room[0]}, 名称: {room[1]}, 允许搜索: {room[2]}, 自动删除: {room[3]}")
        else:
            print("✅ 暂无聊天室数据")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_chat_room_fields())
