#!/usr/bin/env python3
"""
测试新版本重启接口：验证详细日志输出
"""

import asyncio
import aiohttp
import json
from pathlib import Path

async def test_new_restart():
    """测试新版本重启接口"""
    
    print("🚀 测试新版本重启接口：验证详细日志输出...\n")
    
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
            print("⚠️  这将生成重启脚本并执行重启！")
            
            async with session.post(
                "http://192.168.3.139:8000/api/system/reboot",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    reboot_result = await response.json()
                    print(f"✅ 重启接口调用成功")
                    print(f"\n📋 重启响应详情:")
                    print(json.dumps(reboot_result, indent=2, ensure_ascii=False))
                    
                    # 检查是否生成了新的重启脚本
                    print(f"\n🔍 检查重启脚本生成...")
                    restart_script = Path("restart_temp.bat")
                    
                    # 等待脚本生成
                    for i in range(5):
                        if restart_script.exists():
                            print(f"✅ 重启脚本已生成: {restart_script.resolve()}")
                            break
                        await asyncio.sleep(0.5)
                    else:
                        print(f"❌ 重启脚本未生成")
                        return
                    
                    # 显示脚本内容
                    try:
                        script_content = restart_script.read_text(encoding='utf-8')
                        print(f"\n📋 新版本重启脚本内容:")
                        print("=" * 60)
                        print(script_content)
                        print("=" * 60)
                        
                        # 验证脚本内容
                        print(f"\n🔍 脚本内容验证:")
                        if "echo 重启脚本开始执行..." in script_content:
                            print(f"✅ 包含详细日志输出")
                        else:
                            print(f"❌ 缺少详细日志输出")
                        
                        if "main.py" in script_content:
                            print(f"✅ 包含main.py启动命令")
                        else:
                            print(f"❌ 缺少main.py启动命令")
                        
                        if "python.exe" in script_content:
                            print(f"✅ 包含Python可执行文件路径")
                        else:
                            print(f"❌ 缺少Python可执行文件路径")
                        
                    except Exception as e:
                        print(f"❌ 读取脚本内容失败: {e}")
                    
                    print(f"\n⏰ 系统将在 {reboot_result.get('restart_delay', 2)} 秒后重启")
                    print(f"🔧 重启方式: {reboot_result.get('restart_method')}")
                    
                    # 等待重启开始
                    print(f"\n🔄 等待重启开始...")
                    for i in range(5, 0, -1):
                        print(f"   倒计时: {i} 秒", end='\r')
                        await asyncio.sleep(1)
                    
                    print(f"\n\n🔄 检查系统状态...")
                    
                    # 尝试连接几次
                    for retry in range(3):
                        try:
                            print(f"   尝试连接 ({retry + 1}/3)...")
                            async with session.get(
                                "http://192.168.3.139:8000/api/system/config-status",
                                headers=admin_headers,
                                timeout=aiohttp.ClientTimeout(total=3)
                            ) as test_response:
                                if test_response.status == 200:
                                    print(f"✅ 系统仍在运行（可能重启失败或重启太快）")
                                    return
                                else:
                                    print(f"⚠️  系统响应异常: {test_response.status}")
                        except Exception as e:
                            print(f"   连接失败: {e}")
                        
                        await asyncio.sleep(2)
                    
                    print(f"⚠️  系统可能正在重启或重启失败")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 重启接口调用失败: HTTP {response.status}")
                    print(f"   错误信息: {error_text}")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
    
    print(f"\n🎉 新版本重启接口测试完成!")
    print(f"\n💡 测试结果说明:")
    print(f"1. 如果生成了包含详细日志的重启脚本，说明新版本正常")
    print(f"2. 重启脚本应该包含 'echo 重启脚本开始执行...' 等日志")
    print(f"3. 重启脚本会在新控制台窗口中执行，可以看到详细过程")
    print(f"4. 如果重启成功，应用会在几秒后重新启动")

if __name__ == "__main__":
    asyncio.run(test_new_restart())
