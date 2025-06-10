import sqlite3
import os

print("Current directory:", os.getcwd())
print("Database exists:", os.path.exists("database.sqlite"))

try:
    conn = sqlite3.connect("database.sqlite")
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    # 获取每个表的结构
    for table in [t[0] for t in tables]:
        print(f"\nTable: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print("Columns:", [col[1] for col in columns])
        
        # 获取表中的记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Records count: {count}")
        
        # 如果是扩展配置表，显示所有扩展名称
        if table == "extension_configs":
            cursor.execute("SELECT id, name, enabled FROM extension_configs")
            extensions = cursor.fetchall()
            print("Extensions:", [(ext[0], ext[1], bool(ext[2])) for ext in extensions])
    
    conn.close()
except Exception as e:
    print(f"Error: {str(e)}") 