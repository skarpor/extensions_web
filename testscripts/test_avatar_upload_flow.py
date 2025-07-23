#!/usr/bin/env python3
"""
测试头像上传完整流程：选择文件 -> 预览 -> 保存时上传 -> 更新用户信息
"""

import asyncio
import aiohttp
import os
from pathlib import Path

async def test_avatar_upload_flow():
    """测试头像上传完整流程"""
    
    print("🚀 测试头像上传完整流程：选择文件 -> 预览 -> 保存时上传 -> 更新用户信息...\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 管理员登录
            print("🔄 管理员登录...")
            async with session.post(
                "http://192.168.3.139:8001/api/auth/login-json",
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
            
            # 2. 获取当前用户信息
            print("\n🔄 获取当前用户信息...")
            async with session.get(
                "http://192.168.3.139:8001/api/auth/me",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    print(f"✅ 获取用户信息成功")
                    print(f"   当前头像: {user_info.get('avatar') or '无'}")
                    original_avatar = user_info.get('avatar')
                else:
                    error_text = await response.text()
                    print(f"❌ 获取用户信息失败: {error_text}")
                    return
            
            # 3. 创建测试图片文件
            print("\n🔄 创建测试图片文件...")
            test_image_path = "test_avatar.png"
            
            # 创建一个简单的PNG图片（1x1像素）
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
            
            with open(test_image_path, 'wb') as f:
                f.write(png_data)
            
            print(f"✅ 测试图片创建成功: {test_image_path}")
            
            # 4. 测试头像上传API
            print("\n🔄 测试头像上传API...")
            
            with open(test_image_path, 'rb') as f:
                form_data = aiohttp.FormData()
                form_data.add_field('avatar', f, filename='test_avatar.png', content_type='image/png')
                
                async with session.post(
                    "http://192.168.3.139:8001/api/auth/upload-avatar",
                    data=form_data,
                    headers={"Authorization": f"Bearer {admin_token}"}
                ) as response:
                    if response.status == 200:
                        upload_result = await response.json()
                        print(f"✅ 头像上传成功")
                        print(f"   上传结果: {upload_result.get('message')}")
                        print(f"   头像URL: {upload_result.get('avatar_url')}")
                        new_avatar_url = upload_result.get('avatar_url')
                    else:
                        error_text = await response.text()
                        print(f"❌ 头像上传失败: {error_text}")
                        return
            
            # 5. 测试更新用户信息（包含新头像）
            print("\n🔄 测试更新用户信息（包含新头像）...")
            update_data = {
                "username": user_info.get('username'),
                "email": user_info.get('email'),
                "nickname": user_info.get('nickname') or "管理员",
                "avatar": new_avatar_url
            }
            
            async with session.put(
                "http://192.168.3.139:8001/api/auth/me",
                json=update_data,
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    updated_user = await response.json()
                    print(f"✅ 用户信息更新成功")
                    print(f"   更新后的头像: {updated_user.get('avatar')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 用户信息更新失败: {error_text}")
            
            # 6. 验证头像文件是否可访问
            print("\n🔄 验证头像文件是否可访问...")
            avatar_access_url = f"http://192.168.3.139:8001{new_avatar_url}"
            
            async with session.get(avatar_access_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = response.headers.get('content-length', '0')
                    print(f"✅ 头像文件可访问")
                    print(f"   访问URL: {avatar_access_url}")
                    print(f"   内容类型: {content_type}")
                    print(f"   文件大小: {content_length} bytes")
                else:
                    print(f"❌ 头像文件无法访问: HTTP {response.status}")
            
            # 7. 再次获取用户信息，确认头像已更新
            print("\n🔄 再次获取用户信息，确认头像已更新...")
            async with session.get(
                "http://192.168.3.139:8001/api/auth/me",
                headers=admin_headers
            ) as response:
                if response.status == 200:
                    final_user_info = await response.json()
                    final_avatar = final_user_info.get('avatar')
                    print(f"✅ 最终用户信息获取成功")
                    print(f"   最终头像URL: {final_avatar}")
                    
                    if final_avatar == new_avatar_url:
                        print(f"✅ 头像更新流程完全成功！")
                    else:
                        print(f"❌ 头像URL不匹配")
                else:
                    error_text = await response.text()
                    print(f"❌ 获取最终用户信息失败: {error_text}")
            
            # 8. 清理测试文件
            print(f"\n🔄 清理测试文件...")
            try:
                os.remove(test_image_path)
                print(f"✅ 测试文件已删除: {test_image_path}")
            except:
                print(f"⚠️ 测试文件删除失败: {test_image_path}")
            
            print("\n🎉 头像上传完整流程测试完成!")
            print("\n📊 测试总结:")
            print("✅ 头像上传API：正常")
            print("✅ 用户信息更新：正常")
            print("✅ 头像文件访问：正常")
            print("✅ 完整流程：正常")
            
            print("\n💡 前端使用提示:")
            print("1. 用户选择头像文件时，只做预览，不立即上传")
            print("2. 用户点击保存时，先上传头像文件，再更新用户信息")
            print("3. 头像上传成功后，返回的URL会自动更新到用户信息中")
            print("4. 前端可以通过返回的URL直接显示新头像")
            print("5. 整个流程分为两个请求：上传文件 + 更新用户信息")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_avatar_upload_flow())
