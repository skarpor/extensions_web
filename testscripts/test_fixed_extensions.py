#!/usr/bin/env python3
"""
测试修复后的扩展脚本
验证所有扩展都返回正确的字典格式
"""

import asyncio
import aiohttp
import json

async def test_fixed_extensions():
    """测试修复后的扩展脚本"""
    
    print("🚀 测试修复后的扩展脚本...\n")
    
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
                    
                    # 找到我们创建的扩展
                    test_extensions = []
                    for ext in extensions:
                        if any(keyword in ext.get('name', '').lower() for keyword in 
                              ['dashboard', 'processes', 'sysinfo', 'logger', 'performance']):
                            test_extensions.append(ext)
                    
                    print(f"📋 找到 {len(test_extensions)} 个测试扩展")
                    
                    # 测试每个扩展
                    for ext in test_extensions:
                        await test_extension(session, headers, ext)
                        
                else:
                    print(f"❌ 获取扩展列表失败: {response.status}")
                    return
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

async def test_extension(session, headers, extension):
    """测试单个扩展"""
    
    ext_name = extension.get('name', 'Unknown')
    ext_id = extension.get('id')
    render_type = extension.get('render_type', 'unknown')
    
    print(f"\n🧪 测试扩展: {ext_name} (类型: {render_type})")
    
    try:
        # 执行扩展查询
        async with session.post(
            f"http://192.168.3.139:8000/query/{ext_id}",
            json={},  # 空参数
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                
                # 验证返回格式
                if validate_response_format(result, render_type):
                    print(f"  ✅ 返回格式正确")
                    print(f"  📊 数据类型: {result.get('type', 'unknown')}")
                    
                    # 显示元数据信息
                    meta = result.get('meta', {})
                    if meta:
                        print(f"  📋 元数据: {len(meta)} 个字段")
                        if 'generated_at' in meta:
                            print(f"     生成时间: {meta['generated_at']}")
                        if 'error' in meta:
                            print(f"     错误状态: {meta['error']}")
                    
                    # 显示数据信息
                    data = result.get('data')
                    if isinstance(data, str):
                        print(f"  📝 内容长度: {len(data)} 字符")
                    elif isinstance(data, list):
                        print(f"  📊 数据条目: {len(data)} 条")
                    elif isinstance(data, dict):
                        print(f"  🗂️ 数据字段: {len(data)} 个")
                    
                else:
                    print(f"  ❌ 返回格式不正确")
                    print(f"     期望类型: {render_type}")
                    print(f"     实际类型: {result.get('type', 'missing')}")
                    
            else:
                error_text = await response.text()
                print(f"  ❌ 执行失败: {response.status}")
                print(f"     错误信息: {error_text[:200]}...")
                
    except Exception as e:
        print(f"  ❌ 测试失败: {str(e)}")

def validate_response_format(result, expected_type):
    """验证响应格式是否正确"""
    
    # 检查基本结构
    if not isinstance(result, dict):
        print(f"    ❌ 响应不是字典格式")
        return False
    
    # 检查必需字段
    if 'type' not in result:
        print(f"    ❌ 缺少 'type' 字段")
        return False
    
    if 'data' not in result:
        print(f"    ❌ 缺少 'data' 字段")
        return False
    
    # 检查类型匹配
    actual_type = result.get('type')
    if actual_type != expected_type:
        print(f"    ⚠️ 类型不匹配: 期望 {expected_type}, 实际 {actual_type}")
        # 不算错误，因为扩展可能返回不同类型
    
    # 检查数据格式
    data = result.get('data')
    if actual_type == 'html' and not isinstance(data, str):
        print(f"    ❌ HTML类型数据应该是字符串")
        return False
    
    if actual_type == 'table' and not isinstance(data, list):
        print(f"    ❌ Table类型数据应该是列表")
        return False
    
    if actual_type == 'text' and not isinstance(data, str):
        print(f"    ❌ Text类型数据应该是字符串")
        return False
    
    if actual_type == 'file' and not isinstance(data, dict):
        print(f"    ❌ File类型数据应该是字典")
        return False
    
    if actual_type == 'chart' and not isinstance(data, dict):
        print(f"    ❌ Chart类型数据应该是字典")
        return False
    
    # 检查元数据
    meta = result.get('meta')
    if meta is not None and not isinstance(meta, dict):
        print(f"    ❌ meta字段应该是字典或null")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_fixed_extensions())
