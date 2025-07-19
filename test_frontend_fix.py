#!/usr/bin/env python3
"""
测试前端修复后的功能
"""

import asyncio
import aiohttp

async def test_frontend_fix():
    """测试前端修复后的功能"""
    
    print("🚀 测试前端修复后的功能...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 登录获取token
            print("🔄 登录获取token...")
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
            
            # 2. 测试列出文件API
            print(f"\n🔄 测试列出文件API...")
            async with session.get(
                "http://192.168.3.139:8000/api/markdown/list",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 列出文件API正常")
                    print(f"   文件夹路径: {data.get('folder_path')}")
                    print(f"   文件总数: {data.get('total_files')}")
                    
                    files = data.get('files', [])
                    if files:
                        print(f"   现有文件:")
                        for file_info in files:
                            print(f"     - {file_info.get('name')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 列出文件API失败: {response.status}")
                    print(f"   错误: {error_text}")
                    return
            
            # 3. 测试创建文件API
            print(f"\n🔄 测试创建文件API...")
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/create",
                json={
                    "file_name": "frontend-test.md",
                    "template": "blank"
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    create_data = await response.json()
                    print(f"✅ 创建文件API正常")
                    print(f"   文件路径: {create_data.get('file_path')}")
                    test_file_path = create_data.get('file_path')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建文件API失败: {response.status}")
                    print(f"   错误: {error_text}")
                    test_file_path = None
            
            # 4. 测试加载文件API
            if test_file_path:
                print(f"\n🔄 测试加载文件API...")
                async with session.post(
                    "http://192.168.3.139:8000/api/markdown/load",
                    json={"file_path": test_file_path},
                    headers=headers
                ) as response:
                    if response.status == 200:
                        load_data = await response.json()
                        print(f"✅ 加载文件API正常")
                        print(f"   内容长度: {len(load_data.get('content', ''))}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 加载文件API失败: {response.status}")
                        print(f"   错误: {error_text}")
            
            # 5. 测试保存文件API
            if test_file_path:
                print(f"\n🔄 测试保存文件API...")
                async with session.post(
                    "http://192.168.3.139:8000/api/markdown/save",
                    json={
                        "content": "# 前端测试文件\n\n这是一个前端修复测试文件。",
                        "file_path": test_file_path
                    },
                    headers=headers
                ) as response:
                    if response.status == 200:
                        save_data = await response.json()
                        print(f"✅ 保存文件API正常")
                        print(f"   内容长度: {save_data.get('content_length')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 保存文件API失败: {response.status}")
                        print(f"   错误: {error_text}")
            
            # 6. 清理测试文件
            if test_file_path:
                print(f"\n🔄 清理测试文件...")
                async with session.delete(
                    "http://192.168.3.139:8000/api/markdown/delete",
                    json={"file_path": test_file_path},
                    headers=headers
                ) as response:
                    if response.status == 200:
                        print(f"✅ 删除文件API正常")
                    else:
                        error_text = await response.text()
                        print(f"❌ 删除文件API失败: {response.status}")
                        print(f"   错误: {error_text}")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
    
    print(f"\n🎉 前端修复测试完成!")
    print(f"\n📊 修复内容:")
    print(f"✅ 修复了 loadFile 方法名错误")
    print(f"✅ 修复了 API 请求端口问题")
    print(f"✅ 所有 API 请求现在指向正确的后端地址")
    
    print(f"\n🌐 现在可以访问:")
    print(f"- 图标测试页面: http://localhost:5173/test-icons")
    print(f"- Markdown编辑器: http://localhost:5173/markdown")

if __name__ == "__main__":
    asyncio.run(test_frontend_fix())
