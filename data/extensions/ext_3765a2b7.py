"""
系统信息监控扩展
功能: 获取系统资源使用情况和基本信息
作者: System
版本: 1.0.0
依赖: psutil (可选，用于详细系统信息)
"""

import os
import platform
import subprocess
import json
from datetime import datetime

def get_query_form():
    """返回查询表单"""
    return """
    <div class="mb-3">
        <label for="info_type" class="form-label">监控信息类型</label>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="system_info" name="info_type" value="system" checked>
            <label class="form-check-label" for="system_info">系统基本信息</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="cpu_info" name="info_type" value="cpu">
            <label class="form-check-label" for="cpu_info">CPU信息</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="memory_info" name="info_type" value="memory">
            <label class="form-check-label" for="memory_info">内存信息</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="disk_info" name="info_type" value="disk">
            <label class="form-check-label" for="disk_info">磁盘信息</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="network_info" name="info_type" value="network">
            <label class="form-check-label" for="network_info">网络信息</label>
        </div>
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="process_info" name="info_type" value="process">
            <label class="form-check-label" for="process_info">进程信息</label>
        </div>
    </div>
    
    <div class="mb-3">
        <label for="process_limit" class="form-label">进程列表限制</label>
        <input type="number" class="form-control" id="process_limit" name="process_limit" 
               value="10" min="1" max="50">
        <div class="form-text">显示CPU使用率最高的进程数量</div>
    </div>
    
    <div class="mb-3 form-check">
        <input type="checkbox" class="form-check-input" id="detailed_info" name="detailed_info">
        <label class="form-check-label" for="detailed_info">
            显示详细信息 (需要psutil库)
        </label>
    </div>
    """

def get_basic_system_info():
    """获取基本系统信息"""
    try:
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 获取环境变量中的一些有用信息
        info["environment"] = {
            "user": os.environ.get("USER") or os.environ.get("USERNAME", "unknown"),
            "home": os.environ.get("HOME") or os.environ.get("USERPROFILE", "unknown"),
            "path_count": len(os.environ.get("PATH", "").split(os.pathsep))
        }
        
        return info
    except Exception as e:
        return {"error": f"获取系统信息失败: {str(e)}"}

def get_cpu_info_basic():
    """获取基本CPU信息"""
    try:
        info = {
            "cpu_count": os.cpu_count(),
            "processor": platform.processor()
        }
        
        # 尝试从/proc/cpuinfo获取更多信息 (Linux)
        if platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    
                # 提取CPU型号
                for line in cpuinfo.split("\n"):
                    if "model name" in line:
                        info["model_name"] = line.split(":")[1].strip()
                        break
                        
                # 提取CPU频率
                for line in cpuinfo.split("\n"):
                    if "cpu MHz" in line:
                        info["frequency_mhz"] = float(line.split(":")[1].strip())
                        break
            except:
                pass
        
        return info
    except Exception as e:
        return {"error": f"获取CPU信息失败: {str(e)}"}

def get_memory_info_basic():
    """获取基本内存信息"""
    try:
        info = {}
        
        if platform.system() == "Linux":
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                    
                for line in meminfo.split("\n"):
                    if "MemTotal:" in line:
                        info["total_kb"] = int(line.split()[1])
                        info["total_mb"] = info["total_kb"] // 1024
                        info["total_gb"] = info["total_mb"] / 1024
                    elif "MemAvailable:" in line:
                        info["available_kb"] = int(line.split()[1])
                        info["available_mb"] = info["available_kb"] // 1024
                        info["available_gb"] = info["available_mb"] / 1024
                    elif "MemFree:" in line:
                        info["free_kb"] = int(line.split()[1])
                        info["free_mb"] = info["free_kb"] // 1024
                
                if "total_kb" in info and "available_kb" in info:
                    info["used_kb"] = info["total_kb"] - info["available_kb"]
                    info["used_mb"] = info["used_kb"] // 1024
                    info["usage_percent"] = (info["used_kb"] / info["total_kb"]) * 100
                    
            except:
                pass
        
        # Windows系统使用wmic命令
        elif platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) >= 2:
                        data = lines[1].split(",")
                        if len(data) >= 3:
                            info["free_kb"] = int(data[1]) if data[1].isdigit() else 0
                            info["total_kb"] = int(data[2]) if data[2].isdigit() else 0
                            info["used_kb"] = info["total_kb"] - info["free_kb"]
                            info["total_mb"] = info["total_kb"] // 1024
                            info["used_mb"] = info["used_kb"] // 1024
                            info["usage_percent"] = (info["used_kb"] / info["total_kb"]) * 100 if info["total_kb"] > 0 else 0
            except:
                pass
        
        return info
    except Exception as e:
        return {"error": f"获取内存信息失败: {str(e)}"}

def get_disk_info_basic():
    """获取基本磁盘信息"""
    try:
        info = {"disks": []}
        
        if platform.system() == "Windows":
            # Windows系统
            for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive_path = f"{drive}:\\"
                if os.path.exists(drive_path):
                    try:
                        stat = os.statvfs(drive_path) if hasattr(os, 'statvfs') else None
                        if stat:
                            total = stat.f_blocks * stat.f_frsize
                            free = stat.f_bavail * stat.f_frsize
                            used = total - free
                            
                            info["disks"].append({
                                "drive": drive_path,
                                "total_bytes": total,
                                "used_bytes": used,
                                "free_bytes": free,
                                "usage_percent": (used / total) * 100 if total > 0 else 0
                            })
                    except:
                        pass
        else:
            # Unix-like系统
            try:
                stat = os.statvfs("/")
                total = stat.f_blocks * stat.f_frsize
                free = stat.f_bavail * stat.f_frsize
                used = total - free
                
                info["disks"].append({
                    "mount_point": "/",
                    "total_bytes": total,
                    "used_bytes": used,
                    "free_bytes": free,
                    "usage_percent": (used / total) * 100 if total > 0 else 0
                })
            except:
                pass
        
        return info
    except Exception as e:
        return {"error": f"获取磁盘信息失败: {str(e)}"}

def get_process_info_basic(limit=10):
    """获取基本进程信息"""
    try:
        info = {"processes": []}
        
        if platform.system() == "Windows":
            # Windows使用tasklist命令
            try:
                result = subprocess.run(
                    ["tasklist", "/fo", "csv"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")[1:]  # 跳过标题行
                    for i, line in enumerate(lines[:limit]):
                        parts = line.split('","')
                        if len(parts) >= 5:
                            info["processes"].append({
                                "name": parts[0].strip('"'),
                                "pid": parts[1].strip('"'),
                                "memory": parts[4].strip('"')
                            })
            except:
                pass
        else:
            # Unix-like系统使用ps命令
            try:
                result = subprocess.run(
                    ["ps", "aux", "--sort=-%cpu"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")[1:]  # 跳过标题行
                    for i, line in enumerate(lines[:limit]):
                        parts = line.split()
                        if len(parts) >= 11:
                            info["processes"].append({
                                "user": parts[0],
                                "pid": parts[1],
                                "cpu_percent": parts[2],
                                "memory_percent": parts[3],
                                "command": " ".join(parts[10:])
                            })
            except:
                pass
        
        return info
    except Exception as e:
        return {"error": f"获取进程信息失败: {str(e)}"}

def get_detailed_info_with_psutil():
    """使用psutil获取详细信息"""
    try:
        import psutil
        
        info = {
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count_logical": psutil.cpu_count(logical=True),
                "count_physical": psutil.cpu_count(logical=False),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": psutil.virtual_memory()._asdict(),
            "swap": psutil.swap_memory()._asdict(),
            "disk": {
                "usage": psutil.disk_usage('/')._asdict(),
                "io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
            },
            "network": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return info
    except ImportError:
        return {"error": "psutil库未安装"}
    except Exception as e:
        return {"error": f"获取详细信息失败: {str(e)}"}

def execute_query(params, config=None):
    """执行系统监控查询"""
    try:
        info_types = params.getlist("info_type") if hasattr(params, 'getlist') else [params.get("info_type", "system")]
        process_limit = int(params.get("process_limit", 10))
        detailed_info = params.get("detailed_info", False)
        
        result = {
            "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system_platform": platform.system()
        }
        
        # 如果启用详细信息且有psutil
        if detailed_info:
            detailed = get_detailed_info_with_psutil()
            if "error" not in detailed:
                result["detailed_info"] = detailed
            else:
                result["detailed_info_error"] = detailed["error"]
        
        # 根据选择的类型获取信息
        if "system" in info_types:
            result["system_info"] = get_basic_system_info()
        
        if "cpu" in info_types:
            result["cpu_info"] = get_cpu_info_basic()
        
        if "memory" in info_types:
            result["memory_info"] = get_memory_info_basic()
        
        if "disk" in info_types:
            result["disk_info"] = get_disk_info_basic()
        
        if "process" in info_types:
            result["process_info"] = get_process_info_basic(process_limit)
        
        if "network" in info_types:
            # 基本网络信息
            network_info = {"interfaces": []}
            try:
                if platform.system() == "Windows":
                    result_cmd = subprocess.run(
                        ["ipconfig"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result_cmd.returncode == 0:
                        network_info["ipconfig_output"] = result_cmd.stdout[:1000]  # 限制输出长度
                else:
                    result_cmd = subprocess.run(
                        ["ifconfig"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result_cmd.returncode == 0:
                        network_info["ifconfig_output"] = result_cmd.stdout[:1000]  # 限制输出长度
            except:
                network_info["error"] = "无法获取网络接口信息"
            
            result["network_info"] = network_info
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        return {"error": f"系统监控失败: {str(e)}"}
