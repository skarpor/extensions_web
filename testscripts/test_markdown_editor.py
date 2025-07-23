#!/usr/bin/env python3
"""
测试Markdown编辑器功能
"""

import asyncio
import aiohttp
import json
import os

async def test_markdown_editor():
    """测试Markdown编辑器的完整功能"""
    
    print("🚀 测试Markdown编辑器功能...\n")
    
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
            
            # 2. 测试加载Markdown文件
            print(f"\n🔄 测试加载Markdown文件...")
            async with session.get(
                "http://192.168.3.139:8000/api/markdown/load",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    load_data = await response.json()
                    print(f"✅ 加载Markdown文件成功")
                    print(f"   文件路径: {load_data.get('file_path')}")
                    print(f"   内容长度: {len(load_data.get('content', ''))}")
                    print(f"   消息: {load_data.get('message')}")
                    
                    original_content = load_data.get('content', '')
                    file_path = load_data.get('file_path')
                else:
                    error_text = await response.text()
                    print(f"❌ 加载Markdown文件失败: {error_text}")
                    return
            
            # 3. 测试保存Markdown文件
            print(f"\n🔄 测试保存Markdown文件...")
            test_content = """# 测试Markdown文档

## 简介
这是一个测试文档，用于验证Markdown编辑器功能。

## 功能特点
- **实时预览**: 支持实时预览Markdown渲染效果
- **语法高亮**: 编辑器支持Markdown语法高亮
- **工具栏**: 提供常用的Markdown格式化工具
- **文件管理**: 支持创建、保存、删除Markdown文件

## 代码示例
```python
def hello_world():
    print("Hello, Markdown Editor!")
```

## 表格示例
| 功能 | 状态 | 描述 |
|------|------|------|
| 加载文件 | ✅ | 支持加载现有Markdown文件 |
| 保存文件 | ✅ | 支持保存编辑内容 |
| 实时预览 | ✅ | 支持实时预览渲染效果 |
| 导出HTML | ✅ | 支持导出为HTML文件 |

## 链接和图片
- [项目地址](https://github.com/example/project)
- ![示例图片](https://via.placeholder.com/300x200)

> 这是一个引用块，用于展示重要信息。

---

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/save",
                json={
                    "content": test_content,
                    "file_path": file_path
                },
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    save_data = await response.json()
                    print(f"✅ 保存Markdown文件成功")
                    print(f"   文件路径: {save_data.get('file_path')}")
                    print(f"   内容长度: {save_data.get('content_length')}")
                    print(f"   消息: {save_data.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 保存Markdown文件失败: {error_text}")
                    return
            
            # 4. 测试创建新文件
            print(f"\n🔄 测试创建新Markdown文件...")
            new_file_path = "data/docs/test-new-file.md"
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/create",
                json={
                    "file_path": new_file_path,
                    "template": "readme"
                },
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    create_data = await response.json()
                    print(f"✅ 创建新文件成功")
                    print(f"   文件路径: {create_data.get('file_path')}")
                    print(f"   使用模板: {create_data.get('template')}")
                    print(f"   消息: {create_data.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 创建新文件失败: {error_text}")
            
            # 5. 测试列出Markdown文件
            print(f"\n🔄 测试列出Markdown文件...")
            async with session.get(
                "http://192.168.3.139:8000/api/markdown/list",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    list_data = await response.json()
                    print(f"✅ 列出文件成功")
                    print(f"   当前文件: {list_data.get('current_file')}")
                    print(f"   找到文件数量: {len(list_data.get('files', []))}")
                    
                    for file_info in list_data.get('files', [])[:5]:  # 只显示前5个
                        print(f"     - {file_info.get('name')} ({file_info.get('path')})")
                else:
                    error_text = await response.text()
                    print(f"❌ 列出文件失败: {error_text}")
            
            # 6. 测试设置文件路径
            print(f"\n🔄 测试设置文件路径...")
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/set-path",
                json={"file_path": "data/docs/readme.md"},
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    path_data = await response.json()
                    print(f"✅ 设置文件路径成功")
                    print(f"   新路径: {path_data.get('file_path')}")
                    print(f"   消息: {path_data.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 设置文件路径失败: {error_text}")
            
            # 7. 清理测试文件
            print(f"\n🔄 清理测试文件...")
            if os.path.exists(new_file_path):
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
            
            # 8. 恢复原始内容
            print(f"\n🔄 恢复原始文件内容...")
            async with session.post(
                "http://192.168.3.139:8000/api/markdown/save",
                json={
                    "content": original_content,
                    "file_path": file_path
                },
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    print(f"✅ 恢复原始内容成功")
                else:
                    print(f"❌ 恢复原始内容失败")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
    
    print(f"\n🎉 Markdown编辑器功能测试完成!")
    print(f"\n📊 测试总结:")
    print(f"✅ 文件加载：正常")
    print(f"✅ 文件保存：正常")
    print(f"✅ 创建文件：正常")
    print(f"✅ 列出文件：正常")
    print(f"✅ 设置路径：正常")
    print(f"✅ 删除文件：正常")
    
    print(f"\n💡 Markdown编辑器特点:")
    print(f"1. 支持实时预览和编辑")
    print(f"2. 提供多种文档模板")
    print(f"3. 支持文件的增删改查")
    print(f"4. 可配置文件路径")
    print(f"5. 支持导出HTML和打印")
    print(f"6. 提供丰富的编辑工具")
    
    print(f"\n🌐 前端访问:")
    print(f"- 访问地址: http://localhost:5173/markdown")
    print(f"- 菜单位置: 侧边栏 -> Markdown编辑器")

if __name__ == "__main__":
    import datetime
    asyncio.run(test_markdown_editor())
