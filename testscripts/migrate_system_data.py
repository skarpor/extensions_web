#!/usr/bin/env python3
"""
数据库迁移脚本：为chat_messages表添加system_data字段
"""

import asyncio
import sqlite3
from pathlib import Path

async def migrate_system_data():
    """为chat_messages表添加system_data字段"""
    
    print("🚀 开始数据库迁移：为chat_messages表添加system_data字段...\n")
    
    # 数据库文件路径
    db_path = Path("database.sqlite")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查表结构
        print("🔄 检查当前表结构...")
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = cursor.fetchall()
        
        existing_columns = [col[1] for col in columns]
        print(f"✅ 当前字段: {existing_columns}")
        
        # 检查system_data字段是否存在
        if 'system_data' not in existing_columns:
            print("🔄 添加system_data字段...")
            try:
                cursor.execute("ALTER TABLE chat_messages ADD COLUMN system_data TEXT")
                print("✅ 成功添加system_data字段")
            except sqlite3.Error as e:
                print(f"❌ 添加字段失败: {e}")
        else:
            print("✅ system_data字段已存在")
        
        # 检查更新后的表结构
        print("\n🔄 检查更新后的表结构...")
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = cursor.fetchall()
        
        print("✅ 更新后的字段:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # 提交更改
        conn.commit()
        print("\n✅ 数据库迁移完成!")
        
        # 测试查询
        print("\n🔄 测试查询现有消息...")
        cursor.execute("SELECT id, content, message_type, system_data FROM chat_messages LIMIT 5")
        messages = cursor.fetchall()
        
        if messages:
            print("✅ 现有消息:")
            for msg in messages:
                print(f"   - ID: {msg[0]}, 内容: {msg[1][:30]}..., 类型: {msg[2]}, 系统数据: {msg[3]}")
        else:
            print("✅ 暂无消息数据")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_system_data())
