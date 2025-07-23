#!/usr/bin/env python3
"""
测试增强后的系统信息API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.v1.endpoints.system import get_system_info, detect_environment

def test_system_info():
    """测试系统信息获取"""
    print("========== 测试增强后的系统信息 ==========")
    
    # 测试环境检测
    print("\n1. 环境检测信息:")
    env_info = detect_environment()
    
    print(f"  环境类型: {env_info.get('environment_type')}")
    print(f"  平台: {env_info.get('platform')}")
    print(f"  架构: {env_info.get('architecture')}")
    print(f"  Python实现: {env_info.get('python_implementation')}")
    print(f"  是否Docker: {env_info.get('is_docker')}")
    print(f"  是否虚拟环境: {env_info.get('is_virtual_env')}")
    print(f"  是否Conda环境: {env_info.get('is_conda_env')}")
    print(f"  虚拟环境路径: {env_info.get('virtual_env_path')}")
    print(f"  Conda环境名: {env_info.get('conda_env_name')}")
    print(f"  包管理器: {env_info.get('package_manager')}")
    print(f"  部署环境: {env_info.get('deployment_env')}")
    print(f"  主脚本: {env_info.get('main_script')}")
    print(f"  重启方法: {env_info.get('restart_method')}")
    
    # 测试系统信息
    print("\n2. 系统信息:")
    try:
        system_info = get_system_info()
        
        print(f"  操作系统: {system_info.get('os')}")
        print(f"  主机名: {system_info.get('hostname')}")
        print(f"  处理器: {system_info.get('processor')}")
        print(f"  Python版本: {system_info.get('python_version')}")
        print(f"  Python构建: {system_info.get('python_build')}")
        print(f"  Python编译器: {system_info.get('python_compiler')}")
        print(f"  Python路径: {system_info.get('python_executable')}")
        print(f"  当前目录: {system_info.get('current_directory')}")
        print(f"  进程ID: {system_info.get('pid')}")
        
        # 内存信息
        memory = system_info.get('memory_usage', {})
        if isinstance(memory, dict):
            print(f"  内存使用: {memory.get('formatted')}")
            if 'used' in memory and 'total' in memory:
                print(f"    详细: {memory['used']/1024/1024:.1f}MB / {memory['total']/1024/1024:.1f}MB ({memory.get('percent', 0):.1f}%)")
        
        # CPU信息
        cpu = system_info.get('cpu_usage', {})
        if isinstance(cpu, dict):
            print(f"  CPU使用: {cpu.get('formatted')}")
            print(f"  CPU核心数: {cpu.get('cores')}")
            print(f"  系统CPU: {cpu.get('system', 0):.1f}%")
        
        # 磁盘信息
        disk = system_info.get('disk_usage', {})
        if isinstance(disk, dict):
            print(f"  磁盘使用: {disk['used']/1024/1024/1024:.1f}GB / {disk['total']/1024/1024/1024:.1f}GB ({disk.get('percent', 0):.1f}%)")
        
        # 运行时间
        uptime = system_info.get('uptime', 0)
        if isinstance(uptime, (int, float)) and uptime > 0:
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            print(f"  运行时间: {hours}小时 {minutes}分钟 {seconds}秒")
        
        print("\n3. 环境变量 (部分):")
        env_vars = system_info.get('environment_variables', {})
        for key, value in env_vars.items():
            if value:
                # 截断长路径
                display_value = value[:80] + "..." if len(value) > 80 else value
                print(f"  {key}: {display_value}")
        
    except Exception as e:
        print(f"  获取系统信息失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n========== 测试完成 ==========")

if __name__ == "__main__":
    test_system_info()
