#!/usr/bin/env python3
"""
Table类型扩展 - 进程监控器
返回类型: table
"""

import psutil
import datetime

def get_default_config():
    return {"max_processes": 20, "sort_by": "cpu_percent"}

def get_config_form(current_config=None):
    config = current_config or get_default_config()
    return f"""
    <div class="form-group">
        <label for="config.max_processes">最大进程数:</label>
        <input type="number" name="config.max_processes" value="{config.get('max_processes', 20)}" min="5" max="100" class="form-control">
    </div>
    <div class="form-group">
        <label for="config.sort_by">排序方式:</label>
        <select name="config.sort_by" class="form-control">
            <option value="cpu_percent" {"selected" if config.get('sort_by') == 'cpu_percent' else ""}>CPU使用率</option>
            <option value="memory_percent" {"selected" if config.get('sort_by') == 'memory_percent' else ""}>内存使用率</option>
        </select>
    </div>
    """

def get_query_form(config=None):
    return """
    <div class="form-group">
        <label for="filter_name">进程名称过滤:</label>
        <input type="text" name="filter_name" placeholder="输入进程名称" class="form-control">
    </div>
    <div class="form-group">
        <label for="min_memory_mb">最小内存(MB):</label>
        <input type="number" name="min_memory_mb" value="0" min="0" class="form-control">
    </div>
    """

def execute_query(params, config=None):
    try:
        filter_name = params.get("filter_name", "").lower()
        min_memory_mb = float(params.get("min_memory_mb", 0))
        config = config or get_default_config()
        max_processes = config.get("max_processes", 20)
        sort_by = config.get("sort_by", "cpu_percent")
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status']):
            try:
                pinfo = proc.info
                if filter_name and filter_name not in pinfo['name'].lower():
                    continue
                    
                memory_mb = pinfo['memory_info'].rss / (1024 * 1024) if pinfo['memory_info'] else 0
                if memory_mb < min_memory_mb:
                    continue
                
                processes.append({
                    "PID": pinfo['pid'],
                    "进程名": pinfo['name'][:30],
                    "CPU(%)": f"{pinfo['cpu_percent']:.1f}" if pinfo['cpu_percent'] else "0.0",
                    "内存(%)": f"{pinfo['memory_percent']:.1f}" if pinfo['memory_percent'] else "0.0",
                    "内存(MB)": f"{memory_mb:.1f}",
                    "状态": pinfo['status']
                })
            except:
                continue
        
        if sort_by == "cpu_percent":
            processes.sort(key=lambda x: float(x["CPU(%)"]), reverse=True)
        elif sort_by == "memory_percent":
            processes.sort(key=lambda x: float(x["内存(%)"]), reverse=True)
        
        processes = processes[:max_processes]
        
        return {
            "data": processes,
            "meta": {
                "查询时间": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "总进程数": len(processes),
                "过滤条件": f"名称包含: {filter_name or '无'}, 最小内存: {min_memory_mb}MB"
            }
        }
    except Exception as e:
        return {
            "data": [],
            "meta": {"错误": f"获取进程信息失败: {str(e)}"}
        }
