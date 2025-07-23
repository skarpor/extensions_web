#!/usr/bin/env python3
"""
测试重启接口的日志输出：验证重启脚本是否正确生成和执行
"""

import asyncio
import aiohttp
import json

async def test_reboot_logs():
    """测试重启接口的日志输出"""
    
    print("🚀 测试重启接口的日志输出：验证重启脚本是否正确生成和执行...\n")
    
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
            
            # 2. 调用重启接口
            print(f"\n🔄 调用重启接口...")
            print("⚠️  注意：这将真正重启系统！")
            
            user_input = input("确认要重启系统吗？(yes/N): ").strip().lower()
            if user_input != 'yes':
                print("❌ 用户取消重启")
                return
            
            print(f"\n🚀 开始重启系统...")
            
            async with session.post(
                "http://192.168.3.139:8000/api/system/reboot",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    reboot_result = await response.json()
                    print(f"✅ 重启接口调用成功")
                    print(f"📋 重启响应:")
                    print(json.dumps(reboot_result, indent=2, ensure_ascii=False))
                    
                    print(f"\n⏰ 系统将在 {reboot_result.get('restart_delay', 2)} 秒后重启")
                    print(f"🔧 重启方式: {reboot_result.get('restart_method')}")
                    print(f"📝 说明: {reboot_result.get('instructions')}")
                    
                    # 等待重启
                    print(f"\n🔄 等待系统重启...")
                    for i in range(15, 0, -1):
                        print(f"   等待重启: {i} 秒", end='\r')
                        await asyncio.sleep(1)
                    
                    print(f"\n\n🔄 检查系统是否重启成功...")
                    
                    # 尝试重新连接
                    max_retries = 10
                    for retry in range(max_retries):
                        try:
                            print(f"   尝试连接 ({retry + 1}/{max_retries})...")
                            async with session.get(
                                "http://192.168.3.139:8000/api/system/config-status",
                                headers=admin_headers,
                                timeout=aiohttp.ClientTimeout(total=5)
                            ) as test_response:
                                if test_response.status == 200:
                                    status_data = await test_response.json()
                                    print(f"✅ 系统重启成功！")
                                    print(f"   配置文件存在: {status_data.get('config_file_exists')}")
                                    print(f"   配置项总数: {status_data.get('total_config_items')}")
                                    return
                                else:
                                    print(f"⚠️  系统响应异常: {test_response.status}")
                        except asyncio.TimeoutError:
                            print(f"   连接超时，继续等待...")
                        except Exception as e:
                            print(f"   连接失败: {e}")
                        
                        await asyncio.sleep(3)
                    
                    print(f"❌ 系统重启可能失败，无法重新连接")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 重启接口调用失败: HTTP {response.status}")
                    print(f"   错误信息: {error_text}")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
    
    print(f"\n🎉 重启接口测试完成!")
    print(f"\n💡 测试说明:")
    print(f"1. 如果系统成功重启，应该能重新连接到API")
    print(f"2. 如果无法重新连接，可能是重启脚本有问题")
    print(f"3. 检查是否生成了 restart_temp.bat 文件")
    print(f"4. 查看后端日志了解重启过程")

if __name__ == "__main__":
    asyncio.run(test_reboot_logs())
