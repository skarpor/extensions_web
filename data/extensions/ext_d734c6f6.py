#!/usr/bin/env python3
"""
Chart类型扩展 - 性能图表
返回类型: chart
返回图表配置数据，由前端渲染
"""

import datetime
import random

def get_default_config():
    return {
        "chart_type": "line",
        "data_points": 20,
        "update_interval": 5
    }

def get_config_form(current_config=None):
    config = current_config or get_default_config()
    return f"""
    <div class="form-group">
        <label for="config.chart_type">图表类型:</label>
        <select name="config.chart_type" class="form-control">
            <option value="line" {"selected" if config.get('chart_type') == 'line' else ""}>折线图</option>
            <option value="bar" {"selected" if config.get('chart_type') == 'bar' else ""}>柱状图</option>
            <option value="pie" {"selected" if config.get('chart_type') == 'pie' else ""}>饼图</option>
            <option value="area" {"selected" if config.get('chart_type') == 'area' else ""}>面积图</option>
        </select>
    </div>
    <div class="form-group">
        <label for="config.data_points">数据点数量:</label>
        <input type="number" name="config.data_points" value="{config.get('data_points', 20)}" min="5" max="100" class="form-control">
    </div>
    <div class="form-group">
        <label for="config.update_interval">更新间隔(秒):</label>
        <input type="number" name="config.update_interval" value="{config.get('update_interval', 5)}" min="1" max="60" class="form-control">
    </div>
    """

def get_query_form(config=None):
    return """
    <div class="form-group">
        <label for="metric_type">性能指标:</label>
        <select name="metric_type" class="form-control">
            <option value="cpu_memory">CPU和内存</option>
            <option value="disk_io">磁盘IO</option>
            <option value="network_io">网络IO</option>
            <option value="process_count">进程统计</option>
        </select>
    </div>
    <div class="form-group">
        <label for="time_range">时间范围:</label>
        <select name="time_range" class="form-control">
            <option value="5min">最近5分钟</option>
            <option value="15min">最近15分钟</option>
            <option value="1hour">最近1小时</option>
            <option value="6hour">最近6小时</option>
        </select>
    </div>
    <div class="form-group">
        <label>
            <input type="checkbox" name="show_legend" checked>
            显示图例
        </label>
    </div>
    <div class="form-group">
        <label>
            <input type="checkbox" name="animate" checked>
            动画效果
        </label>
    </div>
    """

def execute_query(params, config=None):
    try:
        metric_type = params.get("metric_type", "cpu_memory")
        time_range = params.get("time_range", "5min")
        show_legend = params.get("show_legend", False)
        animate = params.get("animate", False)
        
        config = config or get_default_config()
        chart_type = config.get("chart_type", "line")
        data_points = config.get("data_points", 20)
        
        # 生成图表数据
        chart_data = generate_chart_data(metric_type, time_range, data_points, chart_type)
        
        # 返回图表配置
        return {
            "type": chart_type,
            "data": chart_data,
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "animation": {
                    "duration": 1000 if animate else 0
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": get_chart_title(metric_type, time_range)
                    },
                    "legend": {
                        "display": show_legend,
                        "position": "top"
                    }
                },
                "scales": get_chart_scales(chart_type, metric_type)
            },
            "meta": {
                "metric_type": metric_type,
                "time_range": time_range,
                "data_points": data_points,
                "generated_at": datetime.datetime.now().isoformat(),
                "chart_type": chart_type
            }
        }
        
    except Exception as e:
        return {
            "type": "bar",
            "data": {
                "labels": ["错误"],
                "datasets": [{
                    "label": "错误信息",
                    "data": [1],
                    "backgroundColor": ["#ff6b6b"]
                }]
            },
            "options": {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"图表生成失败: {str(e)}"
                    }
                }
            }
        }

def generate_chart_data(metric_type, time_range, data_points, chart_type):
    """生成图表数据"""
    
    # 生成时间标签
    labels = generate_time_labels(time_range, data_points)
    
    if metric_type == "cpu_memory":
        return generate_cpu_memory_data(labels, chart_type)
    elif metric_type == "disk_io":
        return generate_disk_io_data(labels, chart_type)
    elif metric_type == "network_io":
        return generate_network_io_data(labels, chart_type)
    elif metric_type == "process_count":
        return generate_process_count_data(labels, chart_type)
    else:
        return generate_default_data(labels, chart_type)

def generate_time_labels(time_range, data_points):
    """生成时间标签"""
    now = datetime.datetime.now()
    
    if time_range == "5min":
        interval = 300 // data_points  # 5分钟 = 300秒
    elif time_range == "15min":
        interval = 900 // data_points  # 15分钟 = 900秒
    elif time_range == "1hour":
        interval = 3600 // data_points  # 1小时 = 3600秒
    else:  # 6hour
        interval = 21600 // data_points  # 6小时 = 21600秒
    
    labels = []
    for i in range(data_points):
        time_point = now - datetime.timedelta(seconds=interval * (data_points - 1 - i))
        labels.append(time_point.strftime("%H:%M"))
    
    return labels

def generate_cpu_memory_data(labels, chart_type):
    """生成CPU和内存数据"""
    try:
        import psutil
        current_cpu = psutil.cpu_percent(interval=0.1)
        current_memory = psutil.virtual_memory().percent
    except ImportError:
        current_cpu = 50
        current_memory = 60
    
    # 生成模拟的历史数据
    cpu_data = []
    memory_data = []
    
    for i in range(len(labels)):
        # 在当前值附近波动
        cpu_variation = random.uniform(-10, 10)
        memory_variation = random.uniform(-5, 5)
        
        cpu_value = max(0, min(100, current_cpu + cpu_variation))
        memory_value = max(0, min(100, current_memory + memory_variation))
        
        cpu_data.append(round(cpu_value, 1))
        memory_data.append(round(memory_value, 1))
    
    if chart_type == "pie":
        # 饼图显示当前状态
        return {
            "labels": ["CPU使用", "CPU空闲", "内存使用", "内存空闲"],
            "datasets": [{
                "data": [current_cpu, 100-current_cpu, current_memory, 100-current_memory],
                "backgroundColor": ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4"]
            }]
        }
    else:
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "CPU使用率 (%)",
                    "data": cpu_data,
                    "borderColor": "#ff6b6b",
                    "backgroundColor": "rgba(255, 107, 107, 0.1)",
                    "fill": chart_type == "area"
                },
                {
                    "label": "内存使用率 (%)",
                    "data": memory_data,
                    "borderColor": "#4ecdc4",
                    "backgroundColor": "rgba(78, 205, 196, 0.1)",
                    "fill": chart_type == "area"
                }
            ]
        }

def generate_disk_io_data(labels, chart_type):
    """生成磁盘IO数据"""
    try:
        import psutil
        disk_io = psutil.disk_io_counters()
        base_read = disk_io.read_bytes / (1024*1024)  # MB
        base_write = disk_io.write_bytes / (1024*1024)  # MB
    except ImportError:
        base_read = 100
        base_write = 50
    
    read_data = []
    write_data = []
    
    for i in range(len(labels)):
        read_variation = random.uniform(-20, 30)
        write_variation = random.uniform(-10, 20)
        
        read_value = max(0, base_read + read_variation)
        write_value = max(0, base_write + write_variation)
        
        read_data.append(round(read_value, 1))
        write_data.append(round(write_value, 1))
    
    return {
        "labels": labels,
        "datasets": [
            {
                "label": "磁盘读取 (MB)",
                "data": read_data,
                "borderColor": "#45b7d1",
                "backgroundColor": "rgba(69, 183, 209, 0.1)",
                "fill": chart_type == "area"
            },
            {
                "label": "磁盘写入 (MB)",
                "data": write_data,
                "borderColor": "#96ceb4",
                "backgroundColor": "rgba(150, 206, 180, 0.1)",
                "fill": chart_type == "area"
            }
        ]
    }

def generate_network_io_data(labels, chart_type):
    """生成网络IO数据"""
    try:
        import psutil
        net_io = psutil.net_io_counters()
        base_sent = net_io.bytes_sent / (1024*1024)  # MB
        base_recv = net_io.bytes_recv / (1024*1024)  # MB
    except ImportError:
        base_sent = 200
        base_recv = 500
    
    sent_data = []
    recv_data = []
    
    for i in range(len(labels)):
        sent_variation = random.uniform(-50, 100)
        recv_variation = random.uniform(-100, 200)
        
        sent_value = max(0, base_sent + sent_variation)
        recv_value = max(0, base_recv + recv_variation)
        
        sent_data.append(round(sent_value, 1))
        recv_data.append(round(recv_value, 1))
    
    return {
        "labels": labels,
        "datasets": [
            {
                "label": "网络发送 (MB)",
                "data": sent_data,
                "borderColor": "#feca57",
                "backgroundColor": "rgba(254, 202, 87, 0.1)",
                "fill": chart_type == "area"
            },
            {
                "label": "网络接收 (MB)",
                "data": recv_data,
                "borderColor": "#ff9ff3",
                "backgroundColor": "rgba(255, 159, 243, 0.1)",
                "fill": chart_type == "area"
            }
        ]
    }

def generate_process_count_data(labels, chart_type):
    """生成进程统计数据"""
    try:
        import psutil
        current_processes = len(psutil.pids())
    except ImportError:
        current_processes = 150
    
    process_data = []
    
    for i in range(len(labels)):
        variation = random.randint(-20, 20)
        process_count = max(50, current_processes + variation)
        process_data.append(process_count)
    
    return {
        "labels": labels,
        "datasets": [{
            "label": "进程数量",
            "data": process_data,
            "borderColor": "#a55eea",
            "backgroundColor": "rgba(165, 94, 234, 0.1)",
            "fill": chart_type == "area"
        }]
    }

def generate_default_data(labels, chart_type):
    """生成默认数据"""
    data = [random.randint(10, 100) for _ in labels]
    
    return {
        "labels": labels,
        "datasets": [{
            "label": "示例数据",
            "data": data,
            "borderColor": "#3742fa",
            "backgroundColor": "rgba(55, 66, 250, 0.1)",
            "fill": chart_type == "area"
        }]
    }

def get_chart_title(metric_type, time_range):
    """获取图表标题"""
    titles = {
        "cpu_memory": "CPU和内存使用率",
        "disk_io": "磁盘IO统计",
        "network_io": "网络IO统计",
        "process_count": "进程数量统计"
    }
    
    time_labels = {
        "5min": "最近5分钟",
        "15min": "最近15分钟",
        "1hour": "最近1小时",
        "6hour": "最近6小时"
    }
    
    return f"{titles.get(metric_type, '性能监控')} - {time_labels.get(time_range, '')}"

def get_chart_scales(chart_type, metric_type):
    """获取图表坐标轴配置"""
    if chart_type == "pie":
        return {}
    
    scales = {
        "x": {
            "display": True,
            "title": {
                "display": True,
                "text": "时间"
            }
        },
        "y": {
            "display": True,
            "title": {
                "display": True,
                "text": get_y_axis_label(metric_type)
            },
            "beginAtZero": True
        }
    }
    
    if metric_type in ["cpu_memory"]:
        scales["y"]["max"] = 100
    
    return scales

def get_y_axis_label(metric_type):
    """获取Y轴标签"""
    labels = {
        "cpu_memory": "使用率 (%)",
        "disk_io": "数据量 (MB)",
        "network_io": "数据量 (MB)",
        "process_count": "进程数量"
    }
    return labels.get(metric_type, "数值")
