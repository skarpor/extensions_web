#!/usr/bin/env python3
"""
File类型扩展 - 日志文件生成器
返回类型: file
生成系统日志文件供下载
"""

import datetime
import tempfile
import os
import json

def get_default_config():
    return {
        "log_format": "csv",
        "include_system_info": True,
        "max_entries": 1000
    }

def get_config_form(current_config=None):
    config = current_config or get_default_config()
    return f"""
    <div class="form-group">
        <label for="config.log_format">日志格式:</label>
        <select name="config.log_format" class="form-control">
            <option value="csv" {"selected" if config.get('log_format') == 'csv' else ""}>CSV格式</option>
            <option value="json" {"selected" if config.get('log_format') == 'json' else ""}>JSON格式</option>
            <option value="txt" {"selected" if config.get('log_format') == 'txt' else ""}>文本格式</option>
        </select>
    </div>
    <div class="form-group">
        <label for="config.max_entries">最大条目数:</label>
        <input type="number" name="config.max_entries" value="{config.get('max_entries', 1000)}" min="10" max="10000" class="form-control">
    </div>
    <div class="form-group">
        <label>
            <input type="checkbox" name="config.include_system_info" {"checked" if config.get('include_system_info', True) else ""}>
            包含系统信息
        </label>
    </div>
    """

def get_query_form(config=None):
    return """
    <div class="form-group">
        <label for="log_type">日志类型:</label>
        <select name="log_type" class="form-control">
            <option value="system_status">系统状态日志</option>
            <option value="process_list">进程列表日志</option>
            <option value="network_stats">网络统计日志</option>
            <option value="disk_usage">磁盘使用日志</option>
        </select>
    </div>
    <div class="form-group">
        <label for="time_period">时间周期:</label>
        <select name="time_period" class="form-control">
            <option value="current">当前状态</option>
            <option value="last_hour">最近1小时</option>
            <option value="last_day">最近24小时</option>
            <option value="last_week">最近7天</option>
        </select>
    </div>
    <div class="form-group">
        <label>
            <input type="checkbox" name="compress_file" value="true">
            压缩文件
        </label>
    </div>
    """

def execute_query(params, config=None):
    try:
        log_type = params.get("log_type", "system_status")
        time_period = params.get("time_period", "current")
        compress_file = params.get("compress_file", False)
        
        config = config or get_default_config()
        log_format = config.get("log_format", "csv")
        max_entries = config.get("max_entries", 1000)
        include_system_info = config.get("include_system_info", True)
        
        # 生成日志数据
        log_data = generate_log_data(log_type, time_period, max_entries, include_system_info)
        
        # 创建临时文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{log_type}_{timestamp}.{log_format}"
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                              suffix=f'.{log_format}', 
                                              prefix=f'{log_type}_')
        
        # 写入数据
        if log_format == "csv":
            write_csv_log(temp_file, log_data)
        elif log_format == "json":
            write_json_log(temp_file, log_data)
        else:  # txt
            write_txt_log(temp_file, log_data)
        
        temp_file.close()
        
        # 如果需要压缩
        if compress_file:
            compressed_file = compress_log_file(temp_file.name)
            os.unlink(temp_file.name)  # 删除原文件
            return {
                "type": "file",
                "data": {
                    "file_path": compressed_file,
                    "filename": filename.replace(f'.{log_format}', '.zip'),
                    "content_type": "application/zip",
                    "compressed": True
                },
                "meta": {
                    "log_type": log_type,
                    "time_period": time_period,
                    "log_format": log_format,
                    "compressed": True,
                    "generated_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        else:
            return {
                "type": "file",
                "data": {
                    "file_path": temp_file.name,
                    "filename": filename,
                    "content_type": get_content_type(log_format),
                    "compressed": False
                },
                "meta": {
                    "log_type": log_type,
                    "time_period": time_period,
                    "log_format": log_format,
                    "compressed": False,
                    "generated_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
    except Exception as e:
        # 创建错误日志文件
        error_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        error_file.write(f"日志生成失败\n")
        error_file.write(f"错误时间: {datetime.datetime.now()}\n")
        error_file.write(f"错误信息: {str(e)}\n")
        error_file.write(f"参数: {params}\n")
        error_file.write(f"配置: {config}\n")
        error_file.close()
        
        return {
            "type": "file",
            "data": {
                "file_path": error_file.name,
                "filename": f"error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "content_type": "text/plain"
            },
            "meta": {
                "error": True,
                "error_message": str(e),
                "generated_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

def generate_log_data(log_type, time_period, max_entries, include_system_info):
    """生成日志数据"""
    import platform
    
    log_data = {
        "metadata": {
            "log_type": log_type,
            "time_period": time_period,
            "generated_at": datetime.datetime.now().isoformat(),
            "max_entries": max_entries
        },
        "entries": []
    }
    
    if include_system_info:
        log_data["system_info"] = {
            "platform": platform.system(),
            "hostname": platform.node(),
            "python_version": platform.python_version()
        }
    
    try:
        import psutil
        
        if log_type == "system_status":
            log_data["entries"] = generate_system_status_entries(max_entries)
        elif log_type == "process_list":
            log_data["entries"] = generate_process_entries(max_entries)
        elif log_type == "network_stats":
            log_data["entries"] = generate_network_entries(max_entries)
        elif log_type == "disk_usage":
            log_data["entries"] = generate_disk_entries(max_entries)
            
    except ImportError:
        log_data["entries"] = [{
            "timestamp": datetime.datetime.now().isoformat(),
            "level": "ERROR",
            "message": "psutil库未安装，无法获取系统信息"
        }]
    
    return log_data

def generate_system_status_entries(max_entries):
    """生成系统状态日志条目"""
    import psutil
    import random
    
    entries = []
    now = datetime.datetime.now()
    
    for i in range(min(max_entries, 100)):  # 限制实际生成数量
        timestamp = now - datetime.timedelta(minutes=i*5)
        
        # 模拟一些变化的数据
        cpu_base = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        entry = {
            "timestamp": timestamp.isoformat(),
            "level": "INFO",
            "cpu_percent": round(cpu_base + random.uniform(-5, 5), 2),
            "memory_percent": round(memory.percent + random.uniform(-2, 2), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "load_avg": round(random.uniform(0.5, 2.0), 2),
            "status": "normal" if cpu_base < 80 else "high_load"
        }
        entries.append(entry)
    
    return entries

def generate_process_entries(max_entries):
    """生成进程日志条目"""
    import psutil
    
    entries = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            pinfo = proc.info
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "level": "INFO",
                "pid": pinfo['pid'],
                "name": pinfo['name'],
                "cpu_percent": pinfo['cpu_percent'] or 0,
                "memory_percent": pinfo['memory_percent'] or 0,
                "status": pinfo['status']
            }
            entries.append(entry)
            
            if len(entries) >= max_entries:
                break
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return entries

def generate_network_entries(max_entries):
    """生成网络统计日志条目"""
    import psutil
    
    entries = []
    net_io = psutil.net_io_counters()
    
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "level": "INFO",
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv,
        "errin": net_io.errin,
        "errout": net_io.errout,
        "dropin": net_io.dropin,
        "dropout": net_io.dropout
    }
    entries.append(entry)
    
    return entries

def generate_disk_entries(max_entries):
    """生成磁盘使用日志条目"""
    import psutil
    
    entries = []
    
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "level": "INFO",
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": round((usage.used / usage.total) * 100, 2)
            }
            entries.append(entry)
        except:
            continue
    
    return entries

def write_csv_log(file_obj, log_data):
    """写入CSV格式日志"""
    import csv
    
    if not log_data["entries"]:
        file_obj.write("timestamp,level,message\n")
        file_obj.write(f"{datetime.datetime.now().isoformat()},ERROR,无数据\n")
        return
    
    # 获取所有字段名
    fieldnames = set()
    for entry in log_data["entries"]:
        fieldnames.update(entry.keys())
    fieldnames = sorted(list(fieldnames))
    
    writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
    writer.writeheader()
    
    for entry in log_data["entries"]:
        writer.writerow(entry)

def write_json_log(file_obj, log_data):
    """写入JSON格式日志"""
    json.dump(log_data, file_obj, indent=2, ensure_ascii=False)

def write_txt_log(file_obj, log_data):
    """写入文本格式日志"""
    file_obj.write(f"日志类型: {log_data['metadata']['log_type']}\n")
    file_obj.write(f"生成时间: {log_data['metadata']['generated_at']}\n")
    file_obj.write(f"条目数量: {len(log_data['entries'])}\n")
    file_obj.write("=" * 50 + "\n\n")
    
    for entry in log_data["entries"]:
        file_obj.write(f"时间: {entry.get('timestamp', 'N/A')}\n")
        file_obj.write(f"级别: {entry.get('level', 'INFO')}\n")
        
        for key, value in entry.items():
            if key not in ['timestamp', 'level']:
                file_obj.write(f"{key}: {value}\n")
        
        file_obj.write("-" * 30 + "\n")

def compress_log_file(file_path):
    """压缩日志文件"""
    import zipfile
    
    zip_path = file_path + '.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, os.path.basename(file_path))
    
    return zip_path

def get_content_type(log_format):
    """获取内容类型"""
    content_types = {
        "csv": "text/csv",
        "json": "application/json",
        "txt": "text/plain"
    }
    return content_types.get(log_format, "text/plain")
