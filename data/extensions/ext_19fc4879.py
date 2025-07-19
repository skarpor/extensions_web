#!/usr/bin/env python3
"""
Text类型扩展 - 系统信息报告
返回类型: text
生成纯文本格式的系统信息报告
"""

import platform
import datetime
import os

def get_default_config():
    return {
        "report_format": "detailed",
        "include_env": False,
        "include_network": True
    }

def get_config_form(current_config=None):
    config = current_config or get_default_config()
    return f"""
    <div class="form-group">
        <label for="config.report_format">报告格式:</label>
        <select name="config.report_format" class="form-control">
            <option value="brief" {"selected" if config.get('report_format') == 'brief' else ""}>简要</option>
            <option value="detailed" {"selected" if config.get('report_format') == 'detailed' else ""}>详细</option>
            <option value="full" {"selected" if config.get('report_format') == 'full' else ""}>完整</option>
        </select>
    </div>
    <div class="form-group">
        <label>
            <input type="checkbox" name="config.include_env" {"checked" if config.get('include_env', False) else ""}>
            包含环境变量
        </label>
    </div>
    <div class="form-group">
        <label>
            <input type="checkbox" name="config.include_network" {"checked" if config.get('include_network', True) else ""}>
            包含网络信息
        </label>
    </div>
    """

def get_query_form(config=None):
    return """
    <div class="form-group">
        <label for="section">信息类别:</label>
        <select name="section" class="form-control">
            <option value="all">所有信息</option>
            <option value="system">系统信息</option>
            <option value="hardware">硬件信息</option>
            <option value="software">软件信息</option>
            <option value="network">网络信息</option>
        </select>
    </div>
    <div class="form-group">
        <label>
            <input type="checkbox" name="show_timestamps" checked>
            显示时间戳
        </label>
    </div>
    """

def execute_query(params, config=None):
    try:
        section = params.get("section", "all")
        show_timestamps = params.get("show_timestamps", False)
        config = config or get_default_config()
        
        report_format = config.get("report_format", "detailed")
        include_env = config.get("include_env", False)
        include_network = config.get("include_network", True)
        
        report = []
        
        # 标题和时间戳
        report.append("=" * 60)
        report.append("系统信息报告")
        report.append("=" * 60)
        
        if show_timestamps:
            report.append(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
        
        # 系统信息
        if section in ["all", "system"]:
            report.append("【系统信息】")
            report.append(f"操作系统: {platform.system()} {platform.release()}")
            report.append(f"系统版本: {platform.version()}")
            report.append(f"主机名: {platform.node()}")
            report.append(f"架构: {platform.architecture()[0]}")
            report.append(f"处理器: {platform.processor()}")
            
            if report_format in ["detailed", "full"]:
                report.append(f"Python版本: {platform.python_version()}")
                report.append(f"Python实现: {platform.python_implementation()}")
                
            try:
                import psutil
                boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.datetime.now() - boot_time
                report.append(f"启动时间: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
                report.append(f"运行时间: {str(uptime).split('.')[0]}")
            except ImportError:
                report.append("运行时间: 需要psutil库")
            
            report.append("")
        
        # 硬件信息
        if section in ["all", "hardware"]:
            report.append("【硬件信息】")
            
            try:
                import psutil
                
                # CPU信息
                cpu_count = psutil.cpu_count()
                cpu_count_logical = psutil.cpu_count(logical=True)
                cpu_freq = psutil.cpu_freq()
                
                report.append(f"CPU核心数: {cpu_count} 物理核心, {cpu_count_logical} 逻辑核心")
                if cpu_freq:
                    report.append(f"CPU频率: {cpu_freq.current:.2f}MHz (最大: {cpu_freq.max:.2f}MHz)")
                
                if report_format in ["detailed", "full"]:
                    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
                    report.append(f"CPU使用率: {psutil.cpu_percent(interval=1):.1f}%")
                    if report_format == "full":
                        for i, percent in enumerate(cpu_percent):
                            report.append(f"  核心{i}: {percent:.1f}%")
                
                # 内存信息
                memory = psutil.virtual_memory()
                report.append(f"内存总量: {memory.total / (1024**3):.2f}GB")
                report.append(f"内存使用: {memory.used / (1024**3):.2f}GB ({memory.percent:.1f}%)")
                report.append(f"内存可用: {memory.available / (1024**3):.2f}GB")
                
                if report_format in ["detailed", "full"]:
                    swap = psutil.swap_memory()
                    report.append(f"交换分区: {swap.total / (1024**3):.2f}GB (使用: {swap.percent:.1f}%)")
                
                # 磁盘信息
                if report_format in ["detailed", "full"]:
                    report.append("\n磁盘分区:")
                    for partition in psutil.disk_partitions():
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            report.append(f"  {partition.device}: {usage.total / (1024**3):.1f}GB "
                                        f"(使用: {usage.percent:.1f}%)")
                        except:
                            continue
                            
            except ImportError:
                report.append("详细硬件信息需要psutil库")
            
            report.append("")
        
        # 软件信息
        if section in ["all", "software"]:
            report.append("【软件信息】")
            report.append(f"Python路径: {os.sys.executable}")
            report.append(f"当前工作目录: {os.getcwd()}")
            
            if report_format in ["detailed", "full"]:
                report.append(f"PATH环境变量: {os.environ.get('PATH', 'N/A')[:100]}...")
                
                # 已安装的Python包（如果可用）
                try:
                    import pkg_resources
                    installed_packages = [d.project_name for d in pkg_resources.working_set]
                    report.append(f"已安装Python包数量: {len(installed_packages)}")
                    if report_format == "full":
                        report.append("主要包:")
                        important_packages = ['psutil', 'requests', 'numpy', 'pandas', 'matplotlib']
                        for pkg in important_packages:
                            if pkg in installed_packages:
                                try:
                                    version = pkg_resources.get_distribution(pkg).version
                                    report.append(f"  {pkg}: {version}")
                                except:
                                    report.append(f"  {pkg}: 已安装")
                except ImportError:
                    pass
            
            report.append("")
        
        # 网络信息
        if section in ["all", "network"] and include_network:
            report.append("【网络信息】")
            
            try:
                import socket
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                report.append(f"主机名: {hostname}")
                report.append(f"本地IP: {local_ip}")
                
                if report_format in ["detailed", "full"]:
                    import psutil
                    net_io = psutil.net_io_counters()
                    report.append(f"网络发送: {net_io.bytes_sent / (1024**2):.1f}MB")
                    report.append(f"网络接收: {net_io.bytes_recv / (1024**2):.1f}MB")
                    
                    if report_format == "full":
                        net_if = psutil.net_if_addrs()
                        report.append("\n网络接口:")
                        for interface, addresses in net_if.items():
                            report.append(f"  {interface}:")
                            for addr in addresses:
                                if addr.family == socket.AF_INET:
                                    report.append(f"    IPv4: {addr.address}")
                                elif addr.family == socket.AF_INET6:
                                    report.append(f"    IPv6: {addr.address}")
                                    
            except ImportError:
                report.append("详细网络信息需要psutil库")
            except Exception as e:
                report.append(f"获取网络信息失败: {str(e)}")
            
            report.append("")
        
        # 环境变量
        if include_env and report_format == "full":
            report.append("【环境变量】")
            important_env_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'PYTHONPATH']
            for var in important_env_vars:
                value = os.environ.get(var, 'N/A')
                if len(value) > 100:
                    value = value[:100] + "..."
                report.append(f"{var}: {value}")
            report.append("")
        
        # 结尾
        report.append("=" * 60)
        report.append(f"报告生成完成 - 格式: {report_format}")
        if show_timestamps:
            report.append(f"完成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        return "\n".join(report)
        
    except Exception as e:
        return f"""
系统信息报告生成失败
========================

错误信息: {str(e)}

建议:
1. 安装psutil库获取详细信息: pip install psutil
2. 检查系统权限
3. 确保Python环境正常

生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
