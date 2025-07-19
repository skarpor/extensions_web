#!/usr/bin/env python3
"""
简单测试Markdown API
"""

import asyncio
import aiohttp

async def test_markdown_api():
    """测试Markdown API"""
    
    print("🚀 测试Markdown API...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 登录
            print("🔄 登录...")
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login-json",
                json={"username": "admin", "password": "123"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    login_data = await response.json()
                    print(f"✅ 登录成功")
                    token = login_data.get('access_token')
                else:
                    print(f"❌ 登录失败")
                    return
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. 测试列出文件
            print(f"\n🔄 测试列出文件...")
            async with session.get(
                "http://192.168.3.139:8000/api/markdown/list",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 列出文件成功")
                    print(f"   文件夹: {data.get('folder_path')}")
                    print(f"   文件数: {data.get('total_files')}")
                else:
                    print(f"❌ 列出文件失败: {response.status}")
            
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_markdown_api())
