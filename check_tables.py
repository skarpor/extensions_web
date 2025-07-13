import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal

async def check_tables():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = result.fetchall()
        print('数据库表:')
        for table in tables:
            print(f'  {table[0]}')

asyncio.run(check_tables())
