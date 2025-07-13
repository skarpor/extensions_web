#!/usr/bin/env python3
"""
手动初始化数据库
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.session import init_models, AsyncSessionLocal

# 显式导入所有模型以确保它们被注册到Base.metadata
import models.user
import models.chat
import models.file
import models.extension
import models.setting
import models.log
import models.qrfile

async def init_database():
    """手动初始化数据库"""
    
    print("🚀 手动初始化数据库...\n")
    
    try:
        # 创建所有表
        print("🔄 创建数据库表...")
        await init_models()
        print("✅ 数据库表创建完成")
        
        # 检查创建的表
        print("\n🔄 检查创建的表...")
        import sqlite3
        from pathlib import Path
        
        db_path = Path("data/db/app.db")
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print("✅ 创建的表:")
            for table in tables:
                print(f"   - {table[0]}")
            
            # 检查聊天室表结构
            chat_tables = [table[0] for table in tables if 'chat' in table[0].lower()]
            for table_name in chat_tables:
                print(f"\n🔄 表 {table_name} 的结构:")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    print(f"   - {col[1]} ({col[2]})")
            
            conn.close()
        else:
            print("❌ 数据库文件不存在")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(init_database())
