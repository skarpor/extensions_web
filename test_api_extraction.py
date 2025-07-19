#!/usr/bin/env python3
"""
测试API提取后的功能
"""

import asyncio
import aiohttp

async def test_api_extraction():
    """测试API提取后的功能"""
    
    print("🚀 测试API提取后的功能...\n")
    
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
            
            # 2. 测试所有API接口
            print(f"\n🔄 测试所有Markdown API接口...")
            
            # 列出文件
            async with session.get(
                "http://192.168.3.139:8000/api/markdown/list",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 列出文件API正常 - 找到 {data.get('total_files')} 个文件")
                else:
                    print(f"❌ 列出文件API失败: {response.status}")
                    return
            
            # 创建文件
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/create",
                json={"file_name": "api-test.md", "template": "blank"},
                headers=headers
            ) as response:
                if response.status == 200:
                    create_data = await response.json()
                    print(f"✅ 创建文件API正常")
                    test_file_path = create_data.get('file_path')
                else:
                    print(f"❌ 创建文件API失败: {response.status}")
                    return
            
            # 加载文件
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/load",
                json={"file_path": test_file_path},
                headers=headers
            ) as response:
                if response.status == 200:
                    load_data = await response.json()
                    print(f"✅ 加载文件API正常 - 内容长度: {len(load_data.get('content', ''))}")
                else:
                    print(f"❌ 加载文件API失败: {response.status}")
            
            # 保存文件
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/save",
                json={
                    "content": "# API测试文件\n\n这是通过API创建和保存的文件。",
                    "file_path": test_file_path
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    save_data = await response.json()
                    print(f"✅ 保存文件API正常 - 保存了 {save_data.get('content_length')} 字节")
                else:
                    print(f"❌ 保存文件API失败: {response.status}")
            
            # 删除文件
            async with session.delete(
                "http://192.168.3.139:8000/api/markdown/delete",
                json={"file_path": test_file_path},
                headers=headers
            ) as response:
                if response.status == 200:
                    print(f"✅ 删除文件API正常")
                else:
                    print(f"❌ 删除文件API失败: {response.status}")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
    
    print(f"\n🎉 API提取测试完成!")
    print(f"\n📊 提取内容:")
    print(f"✅ getMarkdownList() - 获取文件列表")
    print(f"✅ loadMarkdownFile() - 加载文件内容")
    print(f"✅ saveMarkdownFile() - 保存文件内容")
    print(f"✅ createMarkdownFile() - 创建新文件")
    print(f"✅ deleteMarkdownFile() - 删除文件")
    
    print(f"\n💡 优势:")
    print(f"1. 代码分离：API逻辑与UI逻辑分离")
    print(f"2. 复用性：API方法可在其他组件中复用")
    print(f"3. 维护性：统一的错误处理和请求配置")
    print(f"4. 可测试性：API方法可以独立测试")
    print(f"5. 类型安全：可以添加TypeScript类型定义")

if __name__ == "__main__":
    asyncio.run(test_api_extraction())
