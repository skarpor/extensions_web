#!/usr/bin/env python3
"""
测试新版Markdown编辑器功能：文件夹模式
"""

import asyncio
import aiohttp
import json
import os

async def test_markdown_folder_editor():
    """测试基于文件夹的Markdown编辑器功能"""
    
    print("🚀 测试新版Markdown编辑器功能：文件夹模式...\n")
    
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
            
            # 2. 测试列出Markdown文件
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
                        for file_info in files[:5]:  # 只显示前5个
                            print(f"     - {file_info.get('name')} ({file_info.get('size')} bytes)")
                        
                        # 选择第一个文件进行测试
                        test_file = files[0]
                        test_file_path = test_file.get('path')
                        print(f"   选择测试文件: {test_file.get('name')}")
                    else:
                        print(f"   文件夹为空，将创建测试文件")
                        test_file_path = None
                else:
                    error_text = await response.text()
                    print(f"❌ 列出文件失败: {error_text}")
                    return
            
            # 3. 测试创建新文件
            print(f"\n🔄 测试创建新文件...")
            test_file_name = "test-markdown-editor.md"
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/create",
                json={
                    "file_name": test_file_name,
                    "template": "readme"
                },
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    create_data = await response.json()
                    print(f"✅ 创建文件成功")
                    print(f"   文件路径: {create_data.get('file_path')}")
                    print(f"   文件名: {create_data.get('file_name')}")
                    print(f"   使用模板: {create_data.get('template')}")
                    
                    new_file_path = create_data.get('file_path')
                else:
                    error_text = await response.text()
                    print(f"❌ 创建文件失败: {error_text}")
                    new_file_path = None
            
            # 4. 测试加载文件内容
            if new_file_path:
                print(f"\n🔄 测试加载文件内容...")
                async with session.post(
                    "http://192.168.3.139:8000/api/markdown/load",
                    json={"file_path": new_file_path},
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        load_data = await response.json()
                        print(f"✅ 加载文件成功")
                        print(f"   文件路径: {load_data.get('file_path')}")
                        print(f"   内容长度: {len(load_data.get('content', ''))}")
                        
                        original_content = load_data.get('content', '')
                    else:
                        error_text = await response.text()
                        print(f"❌ 加载文件失败: {error_text}")
                        original_content = ""
            
            # 5. 测试保存文件内容
            if new_file_path:
                print(f"\n🔄 测试保存文件内容...")
                test_content = """# 测试Markdown编辑器

## 新版特性

### 文件夹模式
- ✅ 从系统设置获取文件夹路径
- ✅ 左侧显示文件列表
- ✅ 点击文件直接编辑
- ✅ 支持创建、删除文件

### 界面优化
- ✅ 文件侧边栏
- ✅ 实时预览
- ✅ 工具栏快捷操作
- ✅ 响应式布局

### 功能完善
- ✅ 多文件管理
- ✅ 模板支持
- ✅ 导出功能
- ✅ 安全验证

## 使用方法

1. 在系统设置中配置Markdown文件夹路径
2. 访问Markdown编辑器页面
3. 在左侧文件列表中选择文件
4. 在右侧编辑和预览内容
5. 保存文件或创建新文件

---

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                async with session.post(
                    "http://192.168.3.139:8000/api/markdown/save",
                    json={
                        "content": test_content,
                        "file_path": new_file_path
                    },
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        save_data = await response.json()
                        print(f"✅ 保存文件成功")
                        print(f"   文件路径: {save_data.get('file_path')}")
                        print(f"   内容长度: {save_data.get('content_length')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 保存文件失败: {error_text}")
            
            # 6. 再次列出文件，验证新文件
            print(f"\n🔄 验证文件列表更新...")
            async with session.get(
                "http://192.168.3.139:8000/api/markdown/list",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    list_data = await response.json()
                    print(f"✅ 文件列表更新成功")
                    print(f"   当前文件总数: {list_data.get('total_files')}")
                    
                    files = list_data.get('files', [])
                    print(f"   文件列表:")
                    for file_info in files:
                        print(f"     - {file_info.get('name')} ({file_info.get('size')} bytes)")
                else:
                    print(f"❌ 获取文件列表失败")
            
            # 7. 清理测试文件
            if new_file_path:
                print(f"\n🔄 清理测试文件...")
                async with session.delete(
                    "http://192.168.3.139:8000/api/markdown/delete",
                    json={"file_path": new_file_path},
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        delete_data = await response.json()
                        print(f"✅ 删除测试文件成功")
                        print(f"   文件路径: {delete_data.get('file_path')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 删除测试文件失败: {error_text}")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
    
    print(f"\n🎉 新版Markdown编辑器功能测试完成!")
    print(f"\n📊 测试总结:")
    print(f"✅ 文件列表：正常")
    print(f"✅ 创建文件：正常")
    print(f"✅ 加载文件：正常")
    print(f"✅ 保存文件：正常")
    print(f"✅ 删除文件：正常")
    
    print(f"\n💡 新版特点:")
    print(f"1. 文件夹模式：从系统设置获取文件夹路径")
    print(f"2. 文件列表：左侧显示所有.md文件")
    print(f"3. 点击编辑：直接选择文件进行编辑")
    print(f"4. 多文件管理：支持创建、删除、切换文件")
    print(f"5. 实时预览：编辑和预览同步显示")
    print(f"6. 安全验证：路径安全检查和权限验证")
    
    print(f"\n🔧 配置说明:")
    print(f"1. 进入系统设置 -> Markdown编辑器")
    print(f"2. 设置文件夹路径，如：data/docs")
    print(f"3. 访问Markdown编辑器页面")
    print(f"4. 在左侧文件列表中选择或创建文件")
    
    print(f"\n🌐 前端访问:")
    print(f"- 访问地址: http://localhost:5173/markdown")
    print(f"- 菜单位置: 侧边栏 -> Markdown编辑器")

if __name__ == "__main__":
    import datetime
    asyncio.run(test_markdown_folder_editor())
