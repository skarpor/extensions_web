#!/usr/bin/env python3
"""
测试系统设置功能
"""

import asyncio
import aiohttp
import json
from pathlib import Path

async def test_system_settings():
    """测试系统设置功能"""
    
    # 管理员登录信息
    admin_credentials = {
        "username": "admin",
        "password": "123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 管理员登录
            print("🔄 管理员登录...")
            async with session.post(
                "http://localhost:8000/api/auth/login",
                data=admin_credentials,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    print(f"✅ 管理员登录成功")
                    access_token = login_result.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ 管理员登录失败 ({response.status}): {error_text}")
                    return
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 2. 测试获取过期信息
            print("\n🔄 测试获取过期信息...")
            async with session.get(
                "http://localhost:8000/api/system/expiry-info"
            ) as response:
                if response.status == 200:
                    expiry_info = await response.json()
                    print(f"✅ 获取过期信息成功:")
                    print(f"   是否过期: {expiry_info.get('expired')}")
                    print(f"   剩余天数: {expiry_info.get('days_left')}")
                    print(f"   过期日期: {expiry_info.get('expiry_date')}")
                else:
                    print(f"❌ 获取过期信息失败 ({response.status})")
            
            # 3. 测试获取配置状态
            print("\n🔄 测试获取配置状态...")
            async with session.get(
                "http://localhost:8000/api/system/config-status",
                headers=headers
            ) as response:
                if response.status == 200:
                    config_status = await response.json()
                    print(f"✅ 获取配置状态成功:")
                    print(f"   配置文件存在: {config_status.get('config_file_exists')}")
                    print(f"   配置目录: {config_status.get('config_dir')}")
                    print(f"   配置项数量: {config_status.get('total_config_items')}")
                else:
                    print(f"❌ 获取配置状态失败 ({response.status})")
            
            # 4. 测试获取系统设置
            print("\n🔄 测试获取系统设置...")
            async with session.get(
                "http://localhost:8000/api/system/settings",
                headers=headers
            ) as response:
                if response.status == 200:
                    settings = await response.json()
                    print(f"✅ 获取系统设置成功:")
                    print(f"   应用名称: {settings.get('APP_NAME')}")
                    print(f"   调试模式: {settings.get('DEBUG')}")
                    print(f"   监听端口: {settings.get('PORT')}")
                    print(f"   密钥已设置: {settings.get('SECRET_KEY_SET')}")
                    print(f"   允许注册: {settings.get('ALLOW_REGISTER')}")
                    original_settings = settings.copy()
                else:
                    error_text = await response.text()
                    print(f"❌ 获取系统设置失败 ({response.status}): {error_text}")
                    return
            
            # 5. 测试更新系统设置
            print("\n🔄 测试更新系统设置...")
            updated_settings = original_settings.copy()
            updated_settings['APP_NAME'] = 'Extensions Web - 测试更新'
            updated_settings['DEBUG'] = not updated_settings['DEBUG']
            
            async with session.put(
                "http://localhost:8000/api/system/settings",
                json=updated_settings,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 更新系统设置成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 更新系统设置失败 ({response.status}): {error_text}")
            
            # 6. 验证设置是否已更新
            print("\n🔄 验证设置更新...")
            async with session.get(
                "http://localhost:8000/api/system/settings",
                headers=headers
            ) as response:
                if response.status == 200:
                    settings = await response.json()
                    if settings.get('APP_NAME') == 'Extensions Web - 测试更新':
                        print(f"✅ 设置更新验证成功")
                    else:
                        print(f"❌ 设置更新验证失败")
                else:
                    print(f"❌ 验证设置更新失败 ({response.status})")
            
            # 7. 测试密钥更新
            print("\n🔄 测试密钥更新...")
            new_secret_key = "test_secret_key_1234567890abcdef1234567890abcdef"
            
            async with session.put(
                "http://localhost:8000/api/system/settings/secret-key",
                json={"secret_key": new_secret_key},
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 密钥更新成功: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 密钥更新失败 ({response.status}): {error_text}")
            
            # 8. 验证密钥设置状态
            print("\n🔄 验证密钥设置状态...")
            async with session.get(
                "http://localhost:8000/api/system/settings",
                headers=headers
            ) as response:
                if response.status == 200:
                    settings = await response.json()
                    if settings.get('SECRET_KEY_SET'):
                        print(f"✅ 密钥设置状态验证成功")
                    else:
                        print(f"❌ 密钥设置状态验证失败")
                else:
                    print(f"❌ 验证密钥设置状态失败 ({response.status})")
            
            # 9. 恢复原始设置
            print("\n🔄 恢复原始设置...")
            async with session.put(
                "http://localhost:8000/api/system/settings",
                json=original_settings,
                headers=headers
            ) as response:
                if response.status == 200:
                    print(f"✅ 原始设置恢复成功")
                else:
                    print(f"❌ 原始设置恢复失败 ({response.status})")
            
            # 10. 检查配置文件
            print("\n🔄 检查配置文件...")
            config_dir = Path.home() / ".extensions_web"
            config_file = config_dir / "app_config.enc"
            key_file = config_dir / ".key"
            
            print(f"   配置目录: {config_dir}")
            print(f"   配置文件存在: {config_file.exists()}")
            print(f"   密钥文件存在: {key_file.exists()}")
            
            if config_file.exists():
                file_size = config_file.stat().st_size
                print(f"   配置文件大小: {file_size} 字节")
            
            print("\n🎉 系统设置功能测试完成!")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    print("🚀 开始测试系统设置功能...\n")
    asyncio.run(test_system_settings())
