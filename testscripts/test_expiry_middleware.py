#!/usr/bin/env python3
"""
测试过期中间件功能
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from core.config_manager import config_manager

async def test_expiry_middleware():
    """测试过期中间件功能"""
    
    print("🚀 开始测试过期中间件功能...\n")
    
    # 1. 测试正常访问（未过期）
    print("🔄 测试正常访问（未过期）...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/api/system/expiry-info") as response:
                if response.status == 200:
                    expiry_info = await response.json()
                    print(f"✅ 正常访问成功，剩余天数: {expiry_info.get('days_left')}")
                else:
                    print(f"❌ 正常访问失败 ({response.status})")
        except Exception as e:
            print(f"❌ 访问失败: {e}")
    
    # 2. 模拟过期状态
    print("\n🔄 模拟系统过期状态...")
    try:
        # 临时设置过期时间为昨天
        yesterday = datetime.now() - timedelta(days=1)
        config_manager.set_config_value("EXPIRY_DATE", yesterday.isoformat())
        print("✅ 已设置系统为过期状态")
        
        # 测试访问受保护的接口
        print("\n🔄 测试访问受保护接口（应该被拒绝）...")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8000/api/auth/roles") as response:
                    if response.status == 403:
                        result = await response.json()
                        if result.get('error') == 'SYSTEM_EXPIRED':
                            print("✅ 过期检查正常工作，访问被正确拒绝")
                            print(f"   错误信息: {result.get('message')}")
                        else:
                            print("❌ 返回403但错误类型不正确")
                    else:
                        print(f"❌ 过期检查失败，访问未被拒绝 ({response.status})")
            except Exception as e:
                print(f"❌ 测试访问失败: {e}")
        
        # 测试排除路径（应该可以访问）
        print("\n🔄 测试排除路径访问（应该允许）...")
        excluded_paths = [
            "/api/system/expiry-info",
            "/docs",
            "/api/auth/login"
        ]
        
        async with aiohttp.ClientSession() as session:
            for path in excluded_paths:
                try:
                    async with session.get(f"http://localhost:8000{path}") as response:
                        if response.status in [200, 422]:  # 422 for login without data
                            print(f"✅ 排除路径 {path} 访问正常")
                        else:
                            print(f"❌ 排除路径 {path} 访问失败 ({response.status})")
                except Exception as e:
                    print(f"❌ 访问排除路径 {path} 失败: {e}")
        
    finally:
        # 3. 恢复正常状态
        print("\n🔄 恢复系统正常状态...")
        try:
            # 设置过期时间为3个月后
            future_date = datetime.now() + timedelta(days=90)
            config_manager.set_config_value("EXPIRY_DATE", future_date.isoformat())
            print("✅ 已恢复系统正常状态")
            
            # 验证恢复
            print("\n🔄 验证系统恢复...")
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get("http://localhost:8000/api/system/expiry-info") as response:
                        if response.status == 200:
                            expiry_info = await response.json()
                            if not expiry_info.get('expired'):
                                print(f"✅ 系统恢复验证成功，剩余天数: {expiry_info.get('days_left')}")
                            else:
                                print("❌ 系统恢复验证失败，仍显示过期")
                        else:
                            print(f"❌ 验证系统恢复失败 ({response.status})")
                except Exception as e:
                    print(f"❌ 验证系统恢复失败: {e}")
                    
        except Exception as e:
            print(f"❌ 恢复系统状态失败: {e}")
    
    print("\n🎉 过期中间件功能测试完成!")

if __name__ == "__main__":
    asyncio.run(test_expiry_middleware())
