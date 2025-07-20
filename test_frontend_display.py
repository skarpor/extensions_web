#!/usr/bin/env python3
"""
测试前端显示效果
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.v1.endpoints.system import get_system_info

def test_frontend_display():
    """测试前端显示数据"""
    print("========== 测试前端显示数据格式 ==========")
    
    try:
        # 获取系统信息
        system_info = get_system_info()
        
        print("✅ 系统信息获取成功")
        print(f"操作系统: {system_info.get('os')}")
        print(f"平台: {system_info.get('platform')}")
        print(f"架构: {system_info.get('architecture')}")
        print(f"Python版本: {system_info.get('python_version')}")
        print(f"Python实现: {system_info.get('python_implementation')}")
        print(f"主机名: {system_info.get('hostname')}")
        print(f"处理器: {system_info.get('processor')}")
        
        # 环境信息
        print(f"\n环境信息:")
        print(f"环境类型: {system_info.get('environment_type')}")
        print(f"虚拟环境: {system_info.get('is_virtual_env')}")
        print(f"Conda环境: {system_info.get('is_conda_env')}")
        print(f"包管理器: {system_info.get('package_manager')}")
        print(f"部署环境: {system_info.get('deployment_env')}")
        print(f"重启方法: {system_info.get('restart_method')}")
        
        # 性能信息
        print(f"\n性能信息:")
        memory = system_info.get('memory_usage')
        if isinstance(memory, dict):
            print(f"内存使用: {memory.get('formatted')} ({memory.get('percent', 0):.1f}%)")
        else:
            print(f"内存使用: {memory}")
        
        cpu = system_info.get('cpu_usage')
        if isinstance(cpu, dict):
            print(f"CPU使用: {cpu.get('formatted')} (系统: {cpu.get('system', 0):.1f}%)")
            print(f"CPU核心数: {cpu.get('cores')}")
        else:
            print(f"CPU使用: {cpu}")
        
        disk = system_info.get('disk_usage')
        if isinstance(disk, dict):
            print(f"磁盘使用: {disk['used']/1024/1024/1024:.1f}GB / {disk['total']/1024/1024/1024:.1f}GB ({disk.get('percent', 0):.1f}%)")
        
        uptime = system_info.get('uptime', 0)
        if isinstance(uptime, (int, float)) and uptime > 0:
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            print(f"运行时间: {hours}小时 {minutes}分钟 {seconds}秒")
        
        print(f"\n✅ 数据格式正确，前端应该能正常显示")
        
        # 检查前端需要的关键字段
        required_fields = [
            'platform', 'architecture', 'python_version', 'python_implementation',
            'hostname', 'processor', 'environment_type', 'is_virtual_env', 
            'is_conda_env', 'package_manager', 'deployment_env'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in system_info or system_info[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"\n⚠️  缺少字段: {missing_fields}")
        else:
            print(f"\n✅ 所有必需字段都存在")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_display()
