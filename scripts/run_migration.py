"""
迁移运行脚本
用于执行数据迁移和测试
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.migrate_data import main as migrate_main
from scripts.test_migration import main as test_main

async def main():
    """主函数"""
    try:
        print("=== 开始数据迁移 ===")
        await migrate_main()
        
        print("\n=== 开始迁移测试 ===")
        await test_main()
        
        print("\n迁移过程完成！")
        
    except Exception as e:
        print(f"迁移过程中出错：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 