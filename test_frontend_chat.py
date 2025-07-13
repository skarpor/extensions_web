#!/usr/bin/env python3
"""
测试前端聊天室页面访问
"""

import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

async def test_frontend_access():
    """测试前端页面访问"""
    
    print("🚀 开始测试前端聊天室页面访问...\n")
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # 启动浏览器
        print("🔄 启动浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # 访问登录页面
        print("🔄 访问登录页面...")
        driver.get("http://localhost:5173/login")
        time.sleep(2)
        
        # 检查页面是否加载
        if "登录" in driver.title or "login" in driver.current_url.lower():
            print("✅ 登录页面加载成功")
        else:
            print(f"❌ 登录页面加载失败，当前URL: {driver.current_url}")
            return
        
        # 尝试登录
        print("🔄 尝试管理员登录...")
        try:
            # 查找用户名输入框
            username_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[placeholder*='用户名'], input[placeholder*='username']"))
            )
            username_input.clear()
            username_input.send_keys("admin")
            
            # 查找密码输入框
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_input.clear()
            password_input.send_keys("123")
            
            # 查找登录按钮
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button:contains('登录'), .el-button--primary")
            login_button.click()
            
            # 等待登录完成
            time.sleep(3)
            
            # 检查是否登录成功（URL变化或页面内容变化）
            if "login" not in driver.current_url.lower():
                print("✅ 登录成功")
            else:
                print("❌ 登录失败，仍在登录页面")
                return
                
        except Exception as e:
            print(f"❌ 登录过程出错: {e}")
            return
        
        # 尝试访问现代聊天室页面
        print("🔄 访问现代聊天室页面...")
        driver.get("http://localhost:5173/modern-chat")
        time.sleep(3)
        
        # 检查聊天室页面是否加载
        if "modern-chat" in driver.current_url:
            print("✅ 现代聊天室页面访问成功")
            
            # 检查页面元素
            try:
                # 检查聊天室列表
                sidebar = driver.find_element(By.CSS_SELECTOR, ".chat-sidebar, .sidebar")
                if sidebar:
                    print("✅ 聊天室侧边栏加载成功")
                
                # 检查主聊天区域
                main_area = driver.find_element(By.CSS_SELECTOR, ".chat-main, .main-area")
                if main_area:
                    print("✅ 主聊天区域加载成功")
                
                # 检查是否有聊天室列表
                room_items = driver.find_elements(By.CSS_SELECTOR, ".room-item, .chat-room")
                print(f"✅ 发现 {len(room_items)} 个聊天室")
                
            except Exception as e:
                print(f"⚠️ 页面元素检查出错: {e}")
        else:
            print(f"❌ 现代聊天室页面访问失败，当前URL: {driver.current_url}")
        
        # 截图保存
        print("🔄 保存页面截图...")
        driver.save_screenshot("modern_chat_page.png")
        print("✅ 截图已保存为 modern_chat_page.png")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    
    finally:
        # 关闭浏览器
        try:
            driver.quit()
            print("✅ 浏览器已关闭")
        except:
            pass
    
    print("\n🎉 前端页面访问测试完成!")

async def test_api_endpoints():
    """测试API端点可访问性"""
    
    print("\n🔄 测试API端点可访问性...")
    
    endpoints = [
        ("GET", "http://localhost:8000/docs", "API文档"),
        ("GET", "http://localhost:8000/api/system/expiry-info", "系统过期信息"),
        ("GET", "http://localhost:5173", "前端首页"),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, url, name in endpoints:
            try:
                async with session.request(method, url) as response:
                    if response.status < 400:
                        print(f"✅ {name} 访问正常 ({response.status})")
                    else:
                        print(f"⚠️ {name} 返回错误 ({response.status})")
            except Exception as e:
                print(f"❌ {name} 访问失败: {e}")

if __name__ == "__main__":
    # 首先测试API端点
    asyncio.run(test_api_endpoints())
    
    # 然后测试前端页面（需要安装selenium和chromedriver）
    try:
        asyncio.run(test_frontend_access())
    except ImportError:
        print("\n⚠️ 未安装selenium，跳过前端页面测试")
        print("   如需测试前端页面，请安装: pip install selenium")
        print("   并下载ChromeDriver: https://chromedriver.chromium.org/")
    except Exception as e:
        print(f"\n⚠️ 前端页面测试失败: {e}")
        print("   请确保Chrome浏览器和ChromeDriver已正确安装")
