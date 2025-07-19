#!/usr/bin/env python3
"""
简单测试Markdown API接口
"""

import asyncio
import aiohttp
import json

async def test_markdown_api():
    """简单测试Markdown API接口"""
    
    print("🚀 简单测试Markdown API接口...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 管理员登录
            print("🔄 管理员登录...")
            async with session.post(
                "http://192.168.3.139:8000/api/auth/login-json",
                json={"username": "admin", "password": "123"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    login_data = await response.json()
                    print(f"✅ 管理员登录成功")
                    admin_token = login_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败: {error_text}")
                    return
            
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # 2. 测试列出文件
            print(f"\n🔄 测试列出Markdown文件...")
            async with session.get(
                "http://192.168.3.139:8000/api/markdown/list",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    list_data = await response.json()
                    print(f"✅ 列出文件成功")
                    print(f"   文件夹路径: {list_data.get('folder_path')}")
                    print(f"   文件总数: {list_data.get('total_files')}")
                    
                    files = list_data.get('files', [])
                    if files:
                        print(f"   文件列表:")
                        for file_info in files:
                            print(f"     - {file_info.get('name')}")
                    else:
                        print(f"   文件夹为空")
                else:
                    error_text = await response.text()
                    print(f"❌ 列出文件失败: {error_text}")
            
            # 3. 测试创建文件
            print(f"\n🔄 测试创建文件...")
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/create",
                json={
                    "file_name": "test-api.md",
                    "template": "blank"
                },
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    create_data = await response.json()
                    print(f"✅ 创建文件成功")
                    print(f"   文件路径: {create_data.get('file_path')}")
                    test_file_path = create_data.get('file_path')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建文件失败: {error_text}")
                    test_file_path = None
            
            # 4. 测试加载文件
            if test_file_path:
                print(f"\n🔄 测试加载文件...")
                async with session.post(
                    "http://192.168.3.139:8000/api/markdown/load",
                    json={"file_path": test_file_path},
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        load_data = await response.json()
                        print(f"✅ 加载文件成功")
                        print(f"   内容长度: {len(load_data.get('content', ''))}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 加载文件失败: {error_text}")
            
            # 5. 测试保存文件
            if test_file_path:
                print(f"\n🔄 测试保存文件...")
                async with session.post(
                    "http://192.168.3.139:8000/api/markdown/save",
                    json={
                        "content": "# 测试文件\n\n这是一个API测试文件。",
                        "file_path": test_file_path
                    },
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        save_data = await response.json()
                        print(f"✅ 保存文件成功")
                        print(f"   内容长度: {save_data.get('content_length')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 保存文件失败: {error_text}")
            
            # 6. 清理测试文件
            if test_file_path:
                print(f"\n🔄 清理测试文件...")
                async with session.delete(
                    "http://192.168.3.139:8000/api/markdown/delete",
                    json={"file_path": test_file_path},
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        print(f"✅ 删除文件成功")
                    else:
                        error_text = await response.text()
                        print(f"❌ 删除文件失败: {error_text}")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
    
    print(f"\n🎉 Markdown API测试完成!")

if __name__ == "__main__":
    asyncio.run(test_markdown_api())
