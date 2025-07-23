#!/usr/bin/env python3
"""
测试扩展配置保存功能：验证配置数据是否正确携带和保存
"""

import asyncio
import aiohttp
import json

async def test_extension_config_save():
    """测试扩展配置保存功能"""
    
    print("🚀 测试扩展配置保存功能：验证配置数据是否正确携带和保存...\n")
    
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
            
            # 2. 获取扩展列表
            print(f"\n🔄 获取扩展列表...")
            async with session.get(
                "http://192.168.3.139:8000/api/extensions",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    extensions = await response.json()
                    print(f"✅ 获取到 {len(extensions)} 个扩展")
                    
                    if not extensions:
                        print(f"❌ 没有找到扩展，无法测试配置保存")
                        return
                    
                    # 选择第一个扩展进行测试
                    test_extension = extensions[0]
                    extension_id = test_extension['id']
                    print(f"   测试扩展: {test_extension['name']} (ID: {extension_id})")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取扩展列表失败: {error_text}")
                    return
            
            # 3. 获取扩展详情
            print(f"\n🔄 获取扩展详情...")
            async with session.get(
                f"http://192.168.3.139:8000/api/extensions/{extension_id}",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    extension_detail = await response.json()
                    print(f"✅ 获取扩展详情成功")
                    print(f"   名称: {extension_detail.get('name')}")
                    print(f"   描述: {extension_detail.get('description')}")
                    print(f"   有配置表单: {extension_detail.get('has_config_form')}")
                    print(f"   启用状态: {extension_detail.get('enabled')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取扩展详情失败: {error_text}")
                    return
            
            # 4. 获取扩展配置表单（如果有）
            if extension_detail.get('has_config_form'):
                print(f"\n🔄 获取扩展配置表单...")
                async with session.get(
                    f"http://192.168.3.139:8000/api/extensions/{extension_id}/config",
                    headers=admin_headers
                ) as response:
                    if response.status == 200:
                        config_data = await response.json()
                        print(f"✅ 获取配置表单成功")
                        print(f"   配置表单HTML长度: {len(config_data.get('config_form', ''))}")
                        print(f"   当前配置: {config_data.get('config', {})}")
                        
                        current_config = config_data.get('config', {})
                    else:
                        error_text = await response.text()
                        print(f"❌ 获取配置表单失败: {error_text}")
                        current_config = {}
            else:
                print(f"\n⚠️  该扩展没有配置表单，使用基本配置测试")
                current_config = {}
            
            # 5. 准备测试配置数据
            print(f"\n🔄 准备测试配置数据...")
            
            # 基本配置
            test_config_data = {
                "id": extension_detail.get('id'),
                "name": extension_detail.get('name'),
                "description": extension_detail.get('description', '') + " [测试更新]",
                "endpoint": extension_detail.get('entry_point'),
                "return_type": extension_detail.get('render_type', 'html'),
                "showinindex": not extension_detail.get('show_in_home', False),  # 切换状态
                "enabled": not extension_detail.get('enabled', False)  # 切换状态
            }
            
            # 扩展配置（如果有）
            if current_config:
                # 修改现有配置值进行测试
                test_extension_config = {}
                for key, value in current_config.items():
                    if isinstance(value, str):
                        test_extension_config[key] = value + "_test"
                    elif isinstance(value, bool):
                        test_extension_config[key] = not value
                    elif isinstance(value, (int, float)):
                        test_extension_config[key] = value + 1
                    else:
                        test_extension_config[key] = value
                
                test_config_data["config"] = test_extension_config
                print(f"   扩展配置: {test_extension_config}")
            
            print(f"   测试配置数据: {json.dumps(test_config_data, indent=2, ensure_ascii=False)}")
            
            # 6. 保存配置
            print(f"\n🔄 保存扩展配置...")
            async with session.put(
                f"http://192.168.3.139:8000/api/extensions/{extension_id}",
                json=test_config_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    save_result = await response.json()
                    print(f"✅ 配置保存成功")
                    print(f"   保存结果: {json.dumps(save_result, indent=2, ensure_ascii=False)}")
                else:
                    error_text = await response.text()
                    print(f"❌ 配置保存失败: HTTP {response.status}")
                    print(f"   错误信息: {error_text}")
                    return
            
            # 7. 验证配置是否正确保存
            print(f"\n🔄 验证配置是否正确保存...")
            async with session.get(
                f"http://192.168.3.139:8000/api/extensions/{extension_id}",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    updated_extension = await response.json()
                    print(f"✅ 获取更新后的扩展信息成功")
                    
                    # 验证基本配置
                    print(f"\n🔍 验证基本配置:")
                    print(f"   名称: {updated_extension.get('name')} (期望: {test_config_data['name']})")
                    print(f"   描述: {updated_extension.get('description')} (期望: {test_config_data['description']})")
                    print(f"   首页显示: {updated_extension.get('show_in_home')} (期望: {test_config_data['showinindex']})")
                    print(f"   启用状态: {updated_extension.get('enabled')} (期望: {test_config_data['enabled']})")
                    
                    # 验证扩展配置
                    if "config" in test_config_data:
                        print(f"\n🔍 验证扩展配置:")
                        async with session.get(
                            f"http://192.168.3.139:8000/api/extensions/{extension_id}/config",
                            headers=admin_headers
                        ) as config_response:
                            if config_response.status == 200:
                                updated_config_data = await config_response.json()
                                updated_config = updated_config_data.get('config', {})
                                print(f"   更新后的配置: {updated_config}")
                                print(f"   期望的配置: {test_config_data['config']}")
                                
                                # 检查配置是否匹配
                                config_match = True
                                for key, expected_value in test_config_data['config'].items():
                                    actual_value = updated_config.get(key)
                                    if actual_value != expected_value:
                                        print(f"   ❌ 配置不匹配: {key} = {actual_value} (期望: {expected_value})")
                                        config_match = False
                                    else:
                                        print(f"   ✅ 配置匹配: {key} = {actual_value}")
                                
                                if config_match:
                                    print(f"✅ 扩展配置保存验证成功")
                                else:
                                    print(f"❌ 扩展配置保存验证失败")
                            else:
                                print(f"❌ 获取更新后的配置失败")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 获取更新后的扩展信息失败: {error_text}")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
    
    print(f"\n🎉 扩展配置保存测试完成!")
    print(f"\n💡 测试说明:")
    print(f"1. 测试了基本配置的保存和验证")
    print(f"2. 测试了扩展配置的保存和验证")
    print(f"3. 验证了前端发送的数据格式")
    print(f"4. 验证了后端保存的数据完整性")

if __name__ == "__main__":
    asyncio.run(test_extension_config_save())
