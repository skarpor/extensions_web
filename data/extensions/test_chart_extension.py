#!/usr/bin/env python3
"""
测试图表扩展 - 验证Chart.js渲染功能
返回类型: chart
"""

import datetime
import random

def get_default_config():
    return {
        "chart_type": "line",
        "data_points": 10,
        "theme": "default"
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
            <option value="doughnut" {"selected" if config.get('chart_type') == 'doughnut' else ""}>环形图</option>
        </select>
    </div>
    <div class="form-group">
        <label for="config.data_points">数据点数量:</label>
        <input type="number" name="config.data_points" value="{config.get('data_points', 10)}" min="5" max="50" class="form-control">
    </div>
    """

def get_query_form(config=None):
    return """
    <div class="form-group">
        <label for="chart_title">图表标题:</label>
        <input type="text" name="chart_title" value="测试图表" class="form-control">
    </div>
    <div class="form-group">
        <label for="data_type">数据类型:</label>
        <select name="data_type" class="form-control">
            <option value="random">随机数据</option>
            <option value="trend">趋势数据</option>
            <option value="seasonal">季节性数据</option>
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
        chart_title = params.get("chart_title", "测试图表")
        data_type = params.get("data_type", "random")
        show_legend = params.get("show_legend", False)
        animate = params.get("animate", False)
        
        config = config or get_default_config()
        chart_type = config.get("chart_type", "line")
        data_points = config.get("data_points", 10)
        
        # 生成图表数据
        chart_data = generate_chart_data(chart_type, data_type, data_points)
        
        # 返回标准格式
        return {
            "type": "chart",
            "data": {
                "chart_type": chart_type,
                "chart_data": chart_data,
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "animation": {
                        "duration": 1000 if animate else 0
                    },
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": chart_title,
                            "font": {
                                "size": 16,
                                "weight": "bold"
                            }
                        },
                        "legend": {
                            "display": show_legend,
                            "position": "top"
                        }
                    },
                    "scales": get_chart_scales(chart_type)
                }
            },
            "meta": {
                "chart_type": chart_type,
                "data_type": data_type,
                "data_points": data_points,
                "generated_at": datetime.datetime.now().isoformat(),
                "show_legend": show_legend,
                "animate": animate
            }
        }
        
    except Exception as e:
        return {
            "type": "chart",
            "data": {
                "chart_type": "bar",
                "chart_data": {
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
            },
            "meta": {
                "error": True,
                "error_message": str(e),
                "generated_at": datetime.datetime.now().isoformat()
            }
        }

def generate_chart_data(chart_type, data_type, data_points):
    """生成图表数据"""
    
    if chart_type in ["pie", "doughnut"]:
        # 饼图数据
        labels = ["数据A", "数据B", "数据C", "数据D", "数据E"]
        data = [random.randint(10, 100) for _ in labels]
        colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57"]
        
        return {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": colors,
                "borderWidth": 2,
                "borderColor": "#fff"
            }]
        }
    else:
        # 线图/柱图数据
        labels = [f"点{i+1}" for i in range(data_points)]
        
        if data_type == "random":
            dataset1_data = [random.randint(10, 100) for _ in range(data_points)]
            dataset2_data = [random.randint(20, 80) for _ in range(data_points)]
        elif data_type == "trend":
            base = 50
            dataset1_data = [base + i * 5 + random.randint(-10, 10) for i in range(data_points)]
            dataset2_data = [base - i * 3 + random.randint(-8, 8) for i in range(data_points)]
        else:  # seasonal
            import math
            dataset1_data = [50 + 30 * math.sin(i * 0.5) + random.randint(-5, 5) for i in range(data_points)]
            dataset2_data = [40 + 25 * math.cos(i * 0.4) + random.randint(-5, 5) for i in range(data_points)]
        
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "数据系列1",
                    "data": dataset1_data,
                    "borderColor": "#ff6b6b",
                    "backgroundColor": "rgba(255, 107, 107, 0.1)",
                    "fill": chart_type == "area",
                    "tension": 0.4 if chart_type == "line" else 0
                },
                {
                    "label": "数据系列2", 
                    "data": dataset2_data,
                    "borderColor": "#4ecdc4",
                    "backgroundColor": "rgba(78, 205, 196, 0.1)",
                    "fill": chart_type == "area",
                    "tension": 0.4 if chart_type == "line" else 0
                }
            ]
        }

def get_chart_scales(chart_type):
    """获取图表坐标轴配置"""
    if chart_type in ["pie", "doughnut"]:
        return {}
    
    return {
        "x": {
            "display": True,
            "title": {
                "display": True,
                "text": "X轴"
            }
        },
        "y": {
            "display": True,
            "title": {
                "display": True,
                "text": "Y轴"
            },
            "beginAtZero": True
        }
    }
