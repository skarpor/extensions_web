#!/usr/bin/env python3
"""
HTML类型扩展 - 系统状态仪表板
返回类型: html
显示系统状态的HTML仪表板
"""

import os
import platform
import datetime
import psutil

def get_default_config():
    """返回扩展的默认配置"""
    return {
        "refresh_interval": 30,
        "show_processes": True,
        "show_network": True,
        "theme": "dark"
    }

def get_config_form(current_config=None):
    """返回扩展配置表单的HTML"""
    config = current_config or get_default_config()
    
    return f"""
    <div class="config-form">
        <div class="form-group">
            <label for="config.refresh_interval">刷新间隔(秒):</label>
            <input type="number" name="config.refresh_interval" value="{config.get('refresh_interval', 30)}" min="5" max="300" class="form-control">
        </div>
        
        <div class="form-group">
            <label>
                <input type="checkbox" name="config.show_processes" {"checked" if config.get('show_processes', True) else ""}>
                显示进程信息
            </label>
        </div>
        
        <div class="form-group">
            <label>
                <input type="checkbox" name="config.show_network" {"checked" if config.get('show_network', True) else ""}>
                显示网络信息
            </label>
        </div>
        
        <div class="form-group">
            <label for="config.theme">主题:</label>
            <select name="config.theme" class="form-control">
                <option value="light" {"selected" if config.get('theme') == 'light' else ""}>浅色</option>
                <option value="dark" {"selected" if config.get('theme') == 'dark' else ""}>深色</option>
            </select>
        </div>
    </div>
    """

def get_query_form(config=None):
    """返回查询表单的HTML"""
    return """
    <div class="query-form">
        <div class="form-group">
            <label for="detail_level">详细级别:</label>
            <select name="detail_level" class="form-control">
                <option value="basic">基础信息</option>
                <option value="detailed" selected>详细信息</option>
                <option value="full">完整信息</option>
            </select>
        </div>
        
        <div class="form-group">
            <label>
                <input type="checkbox" name="include_disk" checked>
                包含磁盘信息
            </label>
        </div>
        
        <div class="form-group">
            <label>
                <input type="checkbox" name="include_memory" checked>
                包含内存信息
            </label>
        </div>
    </div>
    """

def execute_query(params, config=None):
    """执行查询并返回HTML仪表板"""
    try:
        # 获取参数
        detail_level = params.get("detail_level", "detailed")
        include_disk = params.get("include_disk", False)
        include_memory = params.get("include_memory", False)
        
        # 获取配置
        config = config or get_default_config()
        theme = config.get("theme", "dark")
        show_processes = config.get("show_processes", True)
        show_network = config.get("show_network", True)
        
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        
        # 构建HTML
        theme_class = "dashboard-dark" if theme == "dark" else "dashboard-light"
        
        html = f"""
        <div class="system-dashboard {theme_class}">
            <style>
                .system-dashboard {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding: 20px;
                    border-radius: 10px;
                }}
                .dashboard-dark {{
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                }}
                .dashboard-light {{
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    color: #333;
                }}
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .dashboard-card {{
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    padding: 20px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .dashboard-light .dashboard-card {{
                    background: rgba(255, 255, 255, 0.8);
                    border: 1px solid rgba(0, 0, 0, 0.1);
                }}
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .metric-label {{
                    font-size: 0.9em;
                    opacity: 0.8;
                }}
                .progress-bar {{
                    width: 100%;
                    height: 10px;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 5px;
                    overflow: hidden;
                    margin: 10px 0;
                }}
                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #4CAF50, #45a049);
                    transition: width 0.3s ease;
                }}
                .system-info {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    margin-top: 15px;
                }}
                .info-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 5px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }}
                .dashboard-light .info-item {{
                    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                }}
            </style>
            
            <h2>🖥️ 系统状态仪表板</h2>
            <p>更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="dashboard-grid">
                <!-- CPU信息 -->
                <div class="dashboard-card">
                    <h3>🔥 CPU使用率</h3>
                    <div class="metric-value">{cpu_percent:.1f}%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {cpu_percent}%"></div>
                    </div>
                    <div class="metric-label">处理器: {platform.processor()}</div>
                </div>
                
                <!-- 内存信息 -->
                <div class="dashboard-card">
                    <h3>💾 内存使用</h3>
                    <div class="metric-value">{memory.percent:.1f}%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {memory.percent}%"></div>
                    </div>
                    <div class="metric-label">
                        已用: {memory.used // (1024**3):.1f}GB / 
                        总计: {memory.total // (1024**3):.1f}GB
                    </div>
                </div>
                
                <!-- 系统信息 -->
                <div class="dashboard-card">
                    <h3>ℹ️ 系统信息</h3>
                    <div class="system-info">
                        <div class="info-item">
                            <span>系统:</span>
                            <span>{platform.system()} {platform.release()}</span>
                        </div>
                        <div class="info-item">
                            <span>主机名:</span>
                            <span>{platform.node()}</span>
                        </div>
                        <div class="info-item">
                            <span>启动时间:</span>
                            <span>{boot_time.strftime('%m-%d %H:%M')}</span>
                        </div>
                        <div class="info-item">
                            <span>运行时间:</span>
                            <span>{str(uptime).split('.')[0]}</span>
                        </div>
                    </div>
                </div>
        """
        
        # 添加磁盘信息
        if include_disk:
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            html += f"""
                <div class="dashboard-card">
                    <h3>💿 磁盘使用</h3>
                    <div class="metric-value">{disk_percent:.1f}%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {disk_percent}%"></div>
                    </div>
                    <div class="metric-label">
                        已用: {disk_usage.used // (1024**3):.1f}GB / 
                        总计: {disk_usage.total // (1024**3):.1f}GB
                    </div>
                </div>
            """
        
        # 添加网络信息
        if show_network:
            net_io = psutil.net_io_counters()
            html += f"""
                <div class="dashboard-card">
                    <h3>🌐 网络统计</h3>
                    <div class="system-info">
                        <div class="info-item">
                            <span>发送:</span>
                            <span>{net_io.bytes_sent // (1024**2):.1f}MB</span>
                        </div>
                        <div class="info-item">
                            <span>接收:</span>
                            <span>{net_io.bytes_recv // (1024**2):.1f}MB</span>
                        </div>
                        <div class="info-item">
                            <span>发送包:</span>
                            <span>{net_io.packets_sent:,}</span>
                        </div>
                        <div class="info-item">
                            <span>接收包:</span>
                            <span>{net_io.packets_recv:,}</span>
                        </div>
                    </div>
                </div>
            """
        
        # 添加进程信息
        if show_processes and detail_level in ["detailed", "full"]:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按CPU使用率排序，取前5个
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            top_processes = processes[:5]
            
            html += """
                <div class="dashboard-card">
                    <h3>⚡ 热门进程</h3>
                    <div style="font-size: 0.9em;">
            """
            
            for proc in top_processes:
                html += f"""
                        <div class="info-item">
                            <span>{proc['name'][:20]}...</span>
                            <span>CPU: {proc['cpu_percent'] or 0:.1f}%</span>
                        </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        html += """
            </div>
            
            <div style="margin-top: 20px; text-align: center; opacity: 0.7;">
                <small>🔄 自动刷新间隔: """ + str(config.get('refresh_interval', 30)) + """秒</small>
            </div>
        </div>
        """
        
        return html
        
    except Exception as e:
        return f"""
        <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px;">
            <h3>❌ 错误</h3>
            <p>获取系统信息时发生错误: {str(e)}</p>
            <p>请确保已安装psutil库: pip install psutil</p>
        </div>
        """
