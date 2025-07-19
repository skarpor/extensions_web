#!/usr/bin/env python3
"""
测试查询表单功能
"""

import asyncio
import aiohttp

async def test_query_form():
    """测试查询表单功能"""
    
    print("🚀 测试查询表单功能...\n")
    
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
            
            # 2. 获取扩展列表
            print(f"\n🔄 获取扩展列表...")
            async with session.get(
                "http://192.168.3.139:8000/api/extensions",
                headers=headers
            ) as response:
                if response.status == 200:
                    extensions_data = await response.json()
                    # 处理可能的不同响应格式
                    if isinstance(extensions_data, dict):
                        extensions = extensions_data.get('data', [])
                    else:
                        extensions = extensions_data if isinstance(extensions_data, list) else []
                    print(f"✅ 找到 {len(extensions)} 个扩展")
                    
                    # 测试每个有查询表单的扩展
                    for ext in extensions:
                        if ext.get('has_query_form', False):
                            await test_extension_query_form(session, headers, ext)
                        
                else:
                    print(f"❌ 获取扩展列表失败: {response.status}")
                    return
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

async def test_extension_query_form(session, headers, extension):
    """测试单个扩展的查询表单"""
    
    ext_name = extension.get('name', 'Unknown')
    ext_id = extension.get('id')
    
    print(f"\n🧪 测试扩展查询表单: {ext_name}")
    
    try:
        # 获取查询表单
        async with session.get(
            f"http://192.168.3.139:8000/api/extensions/{ext_id}/query",
            headers=headers
        ) as response:
            if response.status == 200:
                form_data = await response.json()
                print(f"  ✅ 查询表单获取成功")
                
                # 检查返回的数据结构
                if 'query_form' in form_data:
                    form_html = form_data['query_form']
                    print(f"  📋 表单HTML长度: {len(form_html)} 字符")
                    
                    # 显示表单HTML的前100个字符
                    preview = form_html[:100].replace('\n', ' ').strip()
                    print(f"  👀 表单预览: {preview}...")
                    
                    # 检查表单中是否包含输入元素
                    input_count = form_html.count('<input')
                    select_count = form_html.count('<select')
                    textarea_count = form_html.count('<textarea')
                    
                    print(f"  🔍 表单元素统计:")
                    print(f"     输入框: {input_count} 个")
                    print(f"     下拉框: {select_count} 个") 
                    print(f"     文本域: {textarea_count} 个")
                    
                else:
                    print(f"  ❌ 响应中没有query_form字段")
                    print(f"     可用字段: {list(form_data.keys())}")
                    
            else:
                error_text = await response.text()
                print(f"  ❌ 获取查询表单失败: {response.status}")
                print(f"     错误信息: {error_text[:200]}...")
                
    except Exception as e:
        print(f"  ❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_query_form())
