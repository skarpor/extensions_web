#!/usr/bin/env python3
"""
系统设置API接口
"""
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

import psutil
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.permissions import manage_system, view_settings, update_settings
from core.config_manager import config_manager
from core.logger import get_logger
from db.session import get_db
from models.user import User as DBUser
from schemas.user import User

router = APIRouter()
logger = get_logger("settings")

def get_system_info():
    """获取系统信息"""
    try:
        # 获取系统基本信息
        system_info = {
            'os': f"{platform.system()} {platform.release()}",
            'platform': platform.system(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'python_executable': sys.executable,
            'current_directory': os.getcwd(),
            'script_path': os.path.abspath(__file__),
            'is_executable': getattr(sys, 'frozen', False),  # 是否为打包的exe文件
            'pid': str(os.getpid()),
            'uptime': '',
            'memory_usage': '',
            'cpu_usage': '',
            'hostname': platform.node(),
            'processor': platform.processor() or 'Unknown',
            'python_build': ' '.join(platform.python_build()),
            'python_compiler': platform.python_compiler()
        }

        # 检测运行环境
        environment_info = detect_environment()
        system_info.update(environment_info)

        # 生成默认重启命令
        restart_commands = generate_default_restart_commands(system_info)
        system_info['default_restart_commands'] = restart_commands

        # 获取进程信息
        try:
            process = psutil.Process()
            create_time = datetime.fromtimestamp(process.create_time())
            uptime = datetime.now() - create_time
            system_info['uptime'] = uptime.total_seconds()  # 返回秒数，前端格式化

            # 获取内存使用情况
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()

            system_info['memory_usage'] = {
                'used': memory_info.rss,
                'total': system_memory.total,
                'percent': (memory_info.rss / system_memory.total) * 100,
                'formatted': f"{memory_info.rss / 1024 / 1024:.1f} MB"
            }

            # 获取CPU使用率
            cpu_percent = process.cpu_percent(interval=0.1)
            system_cpu = psutil.cpu_percent(interval=0.1)

            system_info['cpu_usage'] = {
                'process': cpu_percent,
                'system': system_cpu,
                'cores': psutil.cpu_count(),
                'formatted': f"{cpu_percent:.1f}%"
            }

            # 获取系统负载信息
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
                system_info['load_average'] = {
                    '1min': load_avg[0],
                    '5min': load_avg[1],
                    '15min': load_avg[2]
                }

            # 获取磁盘使用情况
            disk_usage = psutil.disk_usage(os.getcwd())
            system_info['disk_usage'] = {
                'used': disk_usage.used,
                'total': disk_usage.total,
                'free': disk_usage.free,
                'percent': (disk_usage.used / disk_usage.total) * 100
            }

        except Exception as e:
            logger.warning(f"获取进程信息失败: {e}")
            system_info['uptime'] = 0
            system_info['memory_usage'] = {'formatted': 'Unknown'}
            system_info['cpu_usage'] = {'formatted': 'Unknown'}

        return system_info

    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return {
            'os': 'Unknown',
            'python_version': 'Unknown',
            'python_executable': 'Unknown',
            'current_directory': 'Unknown',
            'script_path': 'Unknown',
            'is_executable': False,
            'pid': 'Unknown',
            'uptime': 'Unknown',
            'memory_usage': 'Unknown',
            'cpu_usage': 'Unknown',
            'error': str(e)
        }

def detect_environment():
    """检测运行环境 - 增强版本，提供更多环境信息"""
    env_info = {
        'environment_type': 'unknown',
        'is_docker': False,
        'is_executable': False,
        'is_python_script': False,
        'is_service': False,
        'is_virtual_env': False,
        'is_conda_env': False,
        'restart_method': 'unknown',
        'executable_path': None,
        'working_python': None,
        'main_script': None,
        'platform': platform.system(),
        'architecture': platform.machine(),
        'python_implementation': platform.python_implementation(),
        'virtual_env_path': None,
        'conda_env_name': None,
        'package_manager': None
    }

    try:
        # 检测虚拟环境
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            env_info['is_virtual_env'] = True
            env_info['virtual_env_path'] = sys.prefix

        # 检测Conda环境
        if 'CONDA_DEFAULT_ENV' in os.environ:
            env_info['is_conda_env'] = True
            env_info['conda_env_name'] = os.environ.get('CONDA_DEFAULT_ENV')
            env_info['package_manager'] = 'conda'
        elif env_info['is_virtual_env']:
            env_info['package_manager'] = 'pip'
        else:
            env_info['package_manager'] = 'system'

        # 检查是否在Docker中运行
        if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
            env_info["is_docker"] = True
            env_info["restart_method"] = "docker"
            env_info['environment_type'] = 'docker'

        # 检查是否是打包的可执行文件（PyInstaller等）
        elif getattr(sys, 'frozen', False):
            env_info["is_executable"] = True
            env_info["restart_method"] = "executable"
            env_info["executable_path"] = sys.executable
            env_info['environment_type'] = 'executable'

        # 检查是否作为Windows服务运行
        elif platform.system().lower() == "windows" and os.environ.get("RUNNING_AS_SERVICE"):
            env_info["is_service"] = True
            env_info["restart_method"] = "service"
            env_info['environment_type'] = 'windows_service'

        # 检查是否有systemd服务
        elif platform.system().lower() == "linux" and os.environ.get("SYSTEMD_SERVICE"):
            env_info["is_service"] = True
            env_info["restart_method"] = "systemd"
            env_info['environment_type'] = 'systemd_service'

        # 默认Python脚本方式
        else:
            env_info["is_python_script"] = True
            env_info["restart_method"] = "python"
            env_info['environment_type'] = 'python_script'

            # 查找可用的Python命令
            python_commands = [
                sys.executable,  # 当前Python解释器
                "python",
                "python3",
                "py",
                "/usr/bin/python3",
                "/usr/bin/python",
                "/usr/local/bin/python3",
                "/opt/python/bin/python3"
            ]

            for cmd in python_commands:
                try:
                    result = subprocess.run([cmd, "--version"],
                                          capture_output=True,
                                          timeout=5)
                    if result.returncode == 0:
                        env_info["working_python"] = cmd
                        logger.info(f"找到可用的Python命令: {cmd}")
                        break
                except:
                    continue

            if not env_info["working_python"]:
                logger.warning("未找到可用的Python命令")
                env_info["restart_method"] = "exit_only"

        # 检测主脚本文件
        current_dir = os.getcwd()

        # 首先检查当前运行的脚本
        if hasattr(sys, 'argv') and len(sys.argv) > 0:
            current_script = os.path.basename(sys.argv[0])
            if current_script.endswith('.py'):
                script_path = os.path.join(current_dir, current_script)
                if os.path.exists(script_path):
                    env_info['main_script'] = script_path
                    logger.info(f"检测到当前运行脚本: {current_script}")

        # 如果没有找到，查找常见的主脚本
        if not env_info.get('main_script'):
            possible_scripts = ['main.py', 'app.py', 'server.py', 'run.py', 'wsgi.py', 'asgi.py']
            for script in possible_scripts:
                script_path = os.path.join(current_dir, script)
                if os.path.exists(script_path):
                    env_info['main_script'] = script_path
                    logger.info(f"找到主脚本: {script}")
                    break

        # 如果没找到，尝试从当前文件推断
        if not env_info['main_script']:
            # 从当前API文件路径推断主脚本位置
            from pathlib import Path
            main_script = Path(__file__).parent.parent.parent.parent / "main.py"
            if main_script.exists():
                env_info['main_script'] = str(main_script.resolve())
            else:
                # 尝试app.py
                app_script = Path(__file__).parent.parent.parent.parent / "app.py"
                if app_script.exists():
                    env_info['main_script'] = str(app_script.resolve())
                else:
                    env_info['main_script'] = os.path.join(current_dir, 'app.py')

        # 添加更多环境信息
        env_info['environment_variables'] = {
            'PATH': os.environ.get('PATH', ''),
            'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
            'VIRTUAL_ENV': os.environ.get('VIRTUAL_ENV', ''),
            'CONDA_DEFAULT_ENV': os.environ.get('CONDA_DEFAULT_ENV', ''),
            'HOME': os.environ.get('HOME', os.environ.get('USERPROFILE', '')),
            'USER': os.environ.get('USER', os.environ.get('USERNAME', '')),
            'SHELL': os.environ.get('SHELL', ''),
            'TERM': os.environ.get('TERM', ''),
        }

        # 检测开发/生产环境
        if any(env_var in os.environ for env_var in ['DEBUG', 'DEVELOPMENT', 'DEV']):
            env_info['deployment_env'] = 'development'
        elif any(env_var in os.environ for env_var in ['PRODUCTION', 'PROD']):
            env_info['deployment_env'] = 'production'
        else:
            env_info['deployment_env'] = 'unknown'

    except Exception as e:
        logger.error(f"环境检测失败: {e}")

    return env_info

def generate_process_manager_config(system_info, current_dir, python_exe):
    """生成进程管理器配置"""
    try:
        # 检测主脚本
        possible_scripts = ['main.py', 'app.py', 'server.py', 'run.py']
        main_script = None
        for script in possible_scripts:
            if os.path.exists(os.path.join(current_dir, script)):
                main_script = script
                break

        if not main_script:
            main_script = 'main.py'  # 默认

        # 检测端口 - 简化逻辑，直接使用8000
        check_port = 8000

        # 尝试从main.py中检测端口
        try:
            main_py_path = os.path.join(current_dir, 'main.py')
            if os.path.exists(main_py_path):
                with open(main_py_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 查找uvicorn运行配置
                    import re
                    port_match = re.search(r'port["\s]*[:=]["\s]*(\d+)', content, re.IGNORECASE)
                    if port_match:
                        check_port = int(port_match.group(1))
        except:
            pass

        # 生成检查URL
        check_url = f"http://localhost:{check_port}/"

        # 检测Python解释器
        working_python = system_info.get('working_python', python_exe)
        if not working_python or working_python == 'python':
            # 尝试使用当前Python解释器
            working_python = sys.executable

        # 生成配置
        config = {
            "command": working_python,
            "args": [main_script],
            "cwd": current_dir,
            "check_port": check_port,
            "check_url": check_url,
            "restart_delay": 3,
            "auto_restart": True,
            "max_restart_attempts": 10
        }

        # 只添加必要的环境变量
        config['env'] = {
            'PYTHONPATH': current_dir,
            'PYTHONUNBUFFERED': '1'
        }

        logger.info(f"生成进程管理器配置: {config}")
        return config

    except Exception as e:
        logger.error(f"生成进程管理器配置失败: {e}")
        # 返回默认配置
        return {
            "command": python_exe,
            "args": ["main.py"],
            "cwd": current_dir,
            "check_port": 8000,
            "check_url": "http://localhost:8000/",
            "restart_delay": 3,
            "auto_restart": True,
            "max_restart_attempts": 10
        }

def generate_default_restart_commands(system_info):
    """根据环境生成默认重启命令 - 基于reboot接口逻辑"""
    commands = []

    try:
        is_windows = platform.system().lower() == 'windows'
        restart_method = system_info.get('restart_method', 'unknown')
        executable_path = system_info.get('executable_path')
        working_python = system_info.get('working_python')
        main_script = system_info.get('main_script')
        pid = system_info.get('pid', '0')

        if restart_method == 'docker':
            # Docker环境
            commands.extend([
                {
                    'name': '重启Docker容器',
                    'command': 'docker restart $(hostname)' if not is_windows else 'docker restart %COMPUTERNAME%',
                    'description': '重启当前Docker容器'
                }
            ])

        elif restart_method == 'executable':
            # 打包的可执行文件
            if executable_path:
                exe_name = os.path.basename(executable_path)
                if is_windows:
                    commands.extend([
                        {
                            'name': '重启可执行文件(进程名)',
                            'command': f'TASKKILL /IM "{exe_name}" /F && "{executable_path}"',
                            'description': '通过进程名重启可执行文件'
                        },
                        {
                            'name': '重启可执行文件(PID)',
                            'command': f'TASKKILL /PID {pid} /F && "{executable_path}"',
                            'description': '通过进程ID重启可执行文件'
                        }
                    ])
                else:
                    commands.extend([
                        {
                            'name': '重启可执行文件',
                            'command': f'kill {pid} && "{executable_path}" &',
                            'description': '重启可执行文件'
                        }
                    ])

        elif restart_method == 'service':
            # 服务环境
            if is_windows:
                commands.extend([
                    {
                        'name': '重启Windows服务',
                        'command': 'net stop YourServiceName && net start YourServiceName',
                        'description': '重启Windows服务（需要修改服务名）'
                    }
                ])
            else:
                commands.extend([
                    {
                        'name': '重启systemd服务',
                        'command': 'sudo systemctl restart your-service-name',
                        'description': '重启systemd服务（需要修改服务名）'
                    }
                ])

        elif restart_method == 'python' and working_python and main_script:
            # Python脚本环境
            if is_windows:
                commands.extend([
                    {
                        'name': '重启Python服务(进程名)',
                        'command': f'TASKKILL /IM python.exe /F && "{working_python}" "{main_script}"',
                        'description': '通过进程名重启Python服务'
                    },
                    {
                        'name': '重启Python服务(PID)',
                        'command': f'TASKKILL /PID {pid} /F && "{working_python}" "{main_script}"',
                        'description': '通过进程ID重启Python服务'
                    },
                    {
                        'name': '温和重启',
                        'command': f'TASKKILL /PID {pid} && "{working_python}" "{main_script}"',
                        'description': '温和方式重启服务'
                    }
                ])
            else:
                script_name = os.path.basename(main_script)
                commands.extend([
                    {
                        'name': '重启Python服务(进程名)',
                        'command': f'pkill -f "python.*{script_name}" && nohup "{working_python}" "{main_script}" &',
                        'description': '通过进程名重启Python服务'
                    },
                    {
                        'name': '重启Python服务(PID)',
                        'command': f'kill {pid} && nohup "{working_python}" "{main_script}" &',
                        'description': '通过进程ID重启Python服务'
                    }
                ])
        else:
            # 无法确定重启方式或exit_only
            if is_windows:
                commands.extend([
                    {
                        'name': '强制退出进程',
                        'command': f'TASKKILL /PID {pid} /F',
                        'description': '强制退出当前进程（需要手动重启）'
                    }
                ])
            else:
                commands.extend([
                    {
                        'name': '强制退出进程',
                        'command': f'kill -9 {pid}',
                        'description': '强制退出当前进程（需要手动重启）'
                    }
                ])

        # 添加脚本重启方式（如果有可用的重启方法）
        if restart_method not in ['exit_only', 'unknown']:
            if is_windows:
                commands.append({
                    'name': '脚本重启(推荐)',
                    'command': 'data\\restart_service.bat',
                    'description': '使用独立脚本重启，避免API中断'
                })
            else:
                commands.append({
                    'name': '脚本重启(推荐)',
                    'command': 'bash data/restart_service.sh',
                    'description': '使用独立脚本重启，避免API中断'
                })

    except Exception as e:
        logger.error(f"生成默认重启命令失败: {e}")
        # 提供基本的退出命令
        pid = system_info.get('pid', '0')
        if platform.system().lower() == 'windows':
            commands = [{
                'name': '退出进程',
                'command': f'TASKKILL /PID {pid} /F',
                'description': '退出当前进程（需要手动重启）'
            }]
        else:
            commands = [{
                'name': '退出进程',
                'command': f'kill {pid}',
                'description': '退出当前进程（需要手动重启）'
            }]

    return commands

def safe_execute_command(command, timeout=30):
    """安全执行系统命令"""
    try:
        # 安全检查：禁止一些危险命令
        dangerous_commands = [
            'rm -rf /', 'format c:', 'del /f /s /q c:', 'shutdown -s',
            'mkfs', 'fdisk', 'dd if=', 'chmod 777 /', 'chown root /'
        ]

        command_lower = command.lower()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                return {
                    'success': False,
                    'error': f'危险命令被禁止执行: {dangerous}',
                    'output': ''
                }

        # 特殊处理重启命令
        if 'taskkill' in command_lower and '&&' in command:
            return handle_restart_command(command, timeout)

        # 检查是否是重启命令，如果是则使用独立进程执行
        if 'restart_service.bat' in command.lower():
            # 重启命令需要独立进程执行，避免API进程被杀死后无法继续
            if platform.system().lower() == 'windows':
                # 使用独立的cmd进程执行，不等待结果
                subprocess.Popen(
                    f'cmd /c "{command}"',
                    shell=True,
                    cwd=os.getcwd()
                )
                # 立即返回成功，因为重启脚本会在独立进程中执行
                return {
                    'success': True,
                    'output': '重启脚本已在独立进程中启动执行',
                    'error': None,
                    'return_code': 0
                }
            else:
                # Linux使用nohup在后台执行
                subprocess.Popen(
                    f'nohup {command} &',
                    shell=True,
                    cwd=os.getcwd()
                )
                return {
                    'success': True,
                    'output': '重启脚本已在后台启动执行',
                    'error': None,
                    'return_code': 0
                }

        # 普通命令正常执行
        if platform.system().lower() == 'windows':
            # 在Windows上使用cmd执行
            cmd_command = f'cmd /c "{command}"'
            result = subprocess.run(
                cmd_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
        else:
            # Linux/Mac使用默认shell
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )

        return {
            'success': result.returncode == 0,
            'output': result.stdout if result.stdout else result.stderr,
            'error': result.stderr if result.returncode != 0 else None,
            'return_code': result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f'命令执行超时 ({timeout}秒)',
            'output': ''
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'命令执行失败: {str(e)}',
            'output': ''
        }

def handle_restart_command(command, timeout=30):
    """特殊处理重启命令"""
    try:
        # 分解重启命令
        if '&&' in command:
            parts = command.split('&&')
            kill_cmd = parts[0].strip()
            start_cmd = parts[1].strip()
        else:
            return {
                'success': False,
                'error': '重启命令格式错误，应使用 && 分隔停止和启动命令',
                'output': ''
            }

        output_lines = []
        current_pid = os.getpid()

        # 检查是否要杀死当前进程
        is_killing_self = False
        if '/IM python.exe' in kill_cmd or f'/PID {current_pid}' in kill_cmd:
            is_killing_self = True
            output_lines.append(f"检测到重启当前进程 (PID: {current_pid})")

        if is_killing_self:
            # 如果要杀死当前进程，使用延迟执行
            return handle_self_restart(kill_cmd, start_cmd, output_lines)
        else:
            # 如果不是杀死当前进程，正常执行
            return execute_normal_restart(kill_cmd, start_cmd, output_lines, timeout)

    except Exception as e:
        return {
            'success': False,
            'error': f'重启命令执行失败: {str(e)}',
            'output': '\n'.join(output_lines) if 'output_lines' in locals() else ''
        }

def handle_self_restart(kill_cmd, start_cmd, output_lines):
    """处理重启当前进程的情况 - 使用独立脚本"""
    try:
        # 生成重启脚本
        script_path = create_restart_script(kill_cmd, start_cmd)

        if not script_path:
            return {
                'success': False,
                'error': '无法创建重启脚本',
                'output': '\n'.join(output_lines)
            }

        # 异步执行重启脚本
        if platform.system().lower() == 'windows':
            # Windows: 使用start /B在后台执行，不创建新窗口
            subprocess.Popen(f'start /B "" "{script_path}"', shell=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Linux: 后台执行脚本
            subprocess.Popen(['bash', script_path], start_new_session=True)

        output_lines.append("重启脚本已创建并启动")
        output_lines.append(f"脚本路径: {script_path}")
        output_lines.append("服务将在3秒后重启")

        return {
            'success': True,
            'output': '\n'.join(output_lines),
            'error': None,
            'return_code': 0
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'创建重启脚本失败: {str(e)}',
            'output': '\n'.join(output_lines)
        }

def create_restart_script(kill_cmd, start_cmd):
    """创建动态重启脚本"""
    try:
        import tempfile
        from pathlib import Path

        # 确保data目录存在
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)

        if platform.system().lower() == 'windows':
            script_path = data_dir / 'restart_service_temp.bat'
            script_content = f'''@echo off
REM 动态生成的服务重启脚本
echo [%date% %time%] 开始重启服务...

REM 等待3秒，确保API响应已返回
timeout /t 3 /nobreak >nul

REM 执行停止命令
echo [%date% %time%] 正在停止进程...
{kill_cmd} >nul 2>&1

REM 等待进程完全停止
timeout /t 2 /nobreak >nul

REM 执行启动命令
echo [%date% %time%] 正在启动后台服务...
start "" {start_cmd}

echo [%date% %time%] 后台服务启动完成
timeout /t 3 /nobreak >nul

REM 检查进程状态
tasklist | findstr python.exe >nul
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 服务启动成功
) else (
    echo [%date% %time%] 警告：未检测到Python进程
)

REM 清理临时脚本
del "%~f0"
'''
        else:
            script_path = data_dir / 'restart_service_temp.sh'
            script_content = f'''#!/bin/bash
# 动态生成的服务重启脚本
echo "[$(date)] 开始重启服务..."

# 等待3秒，确保API响应已返回
sleep 3

# 执行停止命令
echo "[$(date)] 正在停止进程..."
{kill_cmd} 2>/dev/null || true

# 等待进程完全停止
sleep 2

# 执行启动命令
echo "[$(date)] 正在启动新进程..."
{start_cmd} &

echo "[$(date)] 重启完成"
# 清理临时脚本
rm "$0"
'''

        # 写入脚本文件
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # Linux下设置执行权限
        if platform.system().lower() != 'windows':
            import stat
            script_path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

        logger.info(f"重启脚本已创建: {script_path}")
        return str(script_path)

    except Exception as e:
        logger.error(f"创建重启脚本失败: {e}")
        return None

def execute_normal_restart(kill_cmd, start_cmd, output_lines, timeout):
    """执行普通的重启命令（不涉及当前进程）"""
    try:
        # 执行停止命令
        logger.info(f"执行停止命令: {kill_cmd}")
        kill_result = subprocess.run(
            kill_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if kill_result.stdout:
            output_lines.append(f"停止命令输出: {kill_result.stdout}")
        if kill_result.stderr:
            output_lines.append(f"停止命令错误: {kill_result.stderr}")

        # 等待一下
        import time
        time.sleep(2)

        # 执行启动命令
        logger.info(f"执行启动命令: {start_cmd}")
        if platform.system().lower() == 'windows':
            async_start_cmd = f'start "" {start_cmd}'
        else:
            async_start_cmd = f'{start_cmd} &'

        start_result = subprocess.run(
            async_start_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )

        output_lines.append("重启命令已执行")
        if start_result.stdout:
            output_lines.append(f"启动命令输出: {start_result.stdout}")

        return {
            'success': True,
            'output': '\n'.join(output_lines),
            'error': None,
            'return_code': 0
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f'重启命令执行超时',
            'output': '\n'.join(output_lines)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'重启命令执行失败: {str(e)}',
            'output': '\n'.join(output_lines)
        }

class SystemSettings(BaseModel):
    """系统设置模型"""
    # 基础配置
    APP_NAME: str = Field(..., description="应用名称")
    DEBUG: bool = Field(False, description="调试模式")
    HOST: str = Field("0.0.0.0", description="监听地址")
    PORT: int = Field(8000, description="监听端口")
    
    # 安全配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="访问令牌过期时间(分钟)")
    ALGORITHM: str = Field("HS256", description="加密算法")
    SECRET_KEY_SET: bool = Field(False, description="密钥是否已设置")
    
    # 数据库配置
    EXT_DB_DIR: str = Field("data/db", description="数据库目录")
    EXT_DB_TYPE: str = Field("sqlite", description="数据库类型")
    EXT_DB_CONFIG: Dict[str, Dict[str, str]] = Field({
        "sqlite": {"db_url": "sqlite+aiosqlite:///./database.sqlite"},
        "postgresql": {"db_url": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"},
        "mysql": {"db_url": "mysql+aiomysql://root:root@localhost:3306/mysql"},
        "mssql": {"db_url": "mssql+pyodbc://sa:123456@localhost:1433/test?driver=ODBC+Driver+17+for+SQL+Server"}
    }, description="数据库配置")
    
    # 应用配置
    FILE_ENABLE: bool= Field(False, description="是否启用文件管理")
    CHAT_ENABLE: bool= Field(False, description="是否启用聊天")
    QR_ENABLE: bool= Field(False, description="是否启用二维码文件传输")
    SCHEDULER_ENABLE: bool= Field(False, description="是否启用定时器")
    LOG_ENABLE: bool = Field(False, description="是否启用日志功能")
    DATABASE_ENABLE: bool = Field(False, description="是否启用数据库")
    HELP_ENABLE: bool = Field( False,description="是否启用帮助文档")
    MARKDOWN_ENABLE: bool = Field(False,description="是否启用Markdown文档")
    DANMU_ENABLE: bool = Field(False,description="是否启用弹幕")
    DASHBOARD_ENABLE: bool = Field(False,description="是否启用控制面板")

    # 文件配置
    UPLOAD_DIR: str = Field("data/uploads", description="上传目录")
    MAX_FILE_SIZE: int = Field(104857600, description="最大文件大小(字节)")
    ALLOWED_EXTENSIONS: list = Field(default_factory=list, description="允许的文件扩展名")

    MARKDOWN_FOLDER_PATH:str = Field("data/docs", description="Markdown文件目录")
    # 扩展配置
    EXTENSIONS_DIR: str = Field("data/extensions", description="扩展目录")
    ALLOW_EXTENSION_UPLOAD: bool = Field(True, description="允许上传扩展")
    
    # 用户配置
    ALLOW_REGISTER: bool = Field(True, description="允许用户注册")
    DEFAULT_USER_ROLE: str = Field("user", description="默认用户角色")
    
    # 日志配置
    LOG_LEVEL: str = Field("INFO", description="日志级别")
    LOG_DIR: str = Field("data/logs", description="日志目录")
    
    # 邮件配置
    SMTP_HOST: str = Field("", description="SMTP服务器地址")
    SMTP_PORT: int = Field(587, description="SMTP端口")
    SMTP_USER: str = Field("", description="SMTP用户名")
    SMTP_PASSWORD: str = Field("", description="SMTP密码")
    SMTP_TLS: bool = Field(True, description="启用TLS")
    
    # 系统配置
    TIMEZONE: str = Field("Asia/Shanghai", description="时区")
    LANGUAGE: str = Field("zh-CN", description="语言")

class SecretKeyUpdate(BaseModel):
    """密钥更新模型"""
    secret_key: str = Field(..., min_length=32, description="新的密钥(至少32位)")

class ExpiryInfo(BaseModel):
    """过期信息模型"""
    expired: bool = Field(..., description="是否已过期")
    expiry_date: Optional[str] = Field(None, description="过期日期")
    initialized_at: Optional[str] = Field(None, description="初始化时间")
    days_left: int = Field(0, description="剩余天数")

class CommandRequest(BaseModel):
    """命令执行请求模型"""
    command: str = Field(..., description="要执行的命令")
    name: str = Field(..., description="命令名称")

class MemoryUsage(BaseModel):
    """内存使用信息"""
    used: int
    total: int
    percent: float
    formatted: str

class CpuUsage(BaseModel):
    """CPU使用信息"""
    process: float
    system: float
    cores: int
    formatted: str

class DiskUsage(BaseModel):
    """磁盘使用信息"""
    used: int
    total: int
    free: int
    percent: float

class LoadAverage(BaseModel):
    """系统负载信息"""
    min1: float = Field(alias="1min")
    min5: float = Field(alias="5min")
    min15: float = Field(alias="15min")

class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""
    os: str
    platform: str
    architecture: str
    python_version: str
    python_implementation: str
    python_executable: str
    current_directory: str
    script_path: str
    is_executable: bool
    pid: str
    uptime: Union[float, str]
    memory_usage: Union[MemoryUsage, str]
    cpu_usage: Union[CpuUsage, str]
    hostname: str
    processor: str
    python_build: str
    python_compiler: str
    disk_usage: Optional[DiskUsage] = None
    load_average: Optional[LoadAverage] = None

    # 环境信息
    environment_type: Optional[str] = None
    is_docker: Optional[bool] = None
    is_virtual_env: Optional[bool] = None
    is_conda_env: Optional[bool] = None
    virtual_env_path: Optional[str] = None
    conda_env_name: Optional[str] = None
    package_manager: Optional[str] = None
    deployment_env: Optional[str] = None
    restart_method: Optional[str] = None
    main_script: Optional[str] = None

    class Config:
        allow_population_by_field_name = True

@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user:User=Depends(view_settings)
):
    """获取系统设置"""
    try:
        config = config_manager.get_editable_config()
        logger.info(f"用户 {current_user.username} 获取系统设置")
        return SystemSettings(**config)
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统设置失败"
        )

@router.put("/settings", response_model=Dict[str, str])
async def update_system_settings(
    settings: SystemSettings,
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user:User=Depends(update_settings)
):
    """更新系统设置"""
    try:
        # 转换为字典，排除不需要保存的字段
        settings_dict = settings.dict()
        settings_dict.pop("SECRET_KEY_SET", None)  # 移除密钥设置状态字段
        
        # 保存配置
        success = config_manager.save_config(settings_dict)
        
        if success:
            logger.info(f"用户 {current_user.username} 更新系统设置成功")
            return {"message": "系统设置更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存系统设置失败"
            )
            
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新系统设置失败"
        )

@router.put("/settings/secret-key", response_model=Dict[str, str])
async def update_secret_key(
    key_update: SecretKeyUpdate,
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user:User=Depends(update_settings)
):
    """更新系统密钥"""
    try:
        success = config_manager.set_config_value("SECRET_KEY", key_update.secret_key)
        
        if success:
            logger.info(f"用户 {current_user.username} 更新系统密钥成功")
            return {"message": "系统密钥更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存系统密钥失败"
            )
            
    except Exception as e:
        logger.error(f"更新系统密钥失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新系统密钥失败"
        )

@router.get("/expiry-info", response_model=ExpiryInfo)
async def get_expiry_info():
    """获取系统过期信息（无需认证）"""
    try:
        expiry_info = config_manager.get_expiry_info()
        return ExpiryInfo(**expiry_info)
    except Exception as e:
        logger.error(f"获取过期信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取过期信息失败"
        )

@router.get("/config-status", response_model=Dict[str, Any])
async def get_config_status(
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user:User=Depends(view_settings)
):
    """获取配置状态信息"""
    try:
        config = config_manager.load_config()
        expiry_info = config_manager.get_expiry_info()
        
        status_info = {
            "config_file_exists": config_manager.config_file.exists(),
            "config_dir": str(config_manager.config_dir),
            "initialized_at": config.get("INITIALIZED_AT"),
            "updated_at": config.get("UPDATED_AT"),
            "expiry_info": expiry_info,
            "total_config_items": len(config)
        }
        
        logger.info(f"用户 {current_user.username} 获取配置状态")
        return status_info
        
    except Exception as e:
        logger.error(f"获取配置状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置状态失败"
        )


@router.get("/system/info", response_model=SystemInfoResponse)
async def get_system_info_api(
    current_user: User = Depends(view_settings)
):
    """获取系统信息"""
    try:
        info = get_system_info()
        return info
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统信息失败: {str(e)}"
        )

@router.post("/system/execute-command")
async def execute_command_api(
    request: CommandRequest,
    current_user: User = Depends(manage_system)  # 临时禁用
):
    """执行系统命令"""
    try:
        command = request.command.strip()
        name = request.name

        if not command:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='命令不能为空'
            )

        # 记录命令执行
        logger.info(f"{current_user.username} 执行命令: {name} - {command}")  # 临时修改

        # 执行命令
        result = safe_execute_command(command)

        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'return_code': result['return_code']
            }
        else:
            return {
                'success': False,
                'error': result['error'],
                'output': result['output']
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'执行命令失败: {str(e)}'
        )

@router.post("/system/create-restart-script")
async def create_restart_script_api(
    current_user: User = Depends(manage_system)  # 临时禁用
):
    """创建或更新重启脚本模板"""
    try:
        from pathlib import Path

        # 获取系统信息
        sys_info = get_system_info()
        python_exe = sys_info.get('python_executable', 'python')
        current_dir = sys_info.get('current_directory', '.')
        script_path = sys_info.get('script_path', 'app.py')

        # 确保data目录存在
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)

        # 生成进程管理器配置
        config = generate_process_manager_config(sys_info, current_dir, python_exe)

        # 保存配置文件
        config_file = os.path.join(current_dir, "process_config.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"进程管理器配置已保存到: {config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

        # 重启命令统一使用进程管理器
        start_command = f'"{python_exe}" parent_process.py restart'

        scripts_created = []

        # 创建Windows重启脚本
        windows_script = data_dir / 'restart_service.bat'
        windows_content = f'''@echo off
REM 服务重启脚本 - 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
echo [%date% %time%] 开始重启服务... >> restart.log
echo [%date% %time%] 开始重启服务...

REM 等待3秒，确保API响应已返回
timeout /t 3 /nobreak >nul

REM 通过进程管理器重启
echo [%date% %time%] 通过进程管理器请求重启... >> restart.log
echo [%date% %time%] 通过进程管理器请求重启...
cd /d "{current_dir}"
"{python_exe}" parent_process.py restart

echo [%date% %time%] 后台服务启动完成 >> restart.log
echo [%date% %time%] 后台服务启动完成
timeout /t 5 /nobreak >nul

REM 检查服务状态
tasklist | findstr python.exe >nul
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 服务启动成功 >> restart.log
    echo [%date% %time%] 服务启动成功
) else (
    echo [%date% %time%] 警告：未检测到Python进程 >> restart.log
    echo [%date% %time%] 警告：未检测到Python进程
)

REM 检查端口监听
netstat -ano | findstr :8000 >nul
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 服务端口正常监听 >> restart.log
    echo [%date% %time%] 服务端口正常监听
) else (
    echo [%date% %time%] 提示：服务可能需要更多时间启动 >> restart.log
    echo [%date% %time%] 提示：服务可能需要更多时间启动
)
'''

        with open(windows_script, 'w', encoding='utf-8') as f:
            f.write(windows_content)
        scripts_created.append(str(windows_script))

        # 创建Linux重启脚本
        linux_script = data_dir / 'restart_service.sh'
        linux_content = f'''#!/bin/bash
# 服务重启脚本 - 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
echo "[$(date)] 开始重启服务..."

# 等待3秒，确保API响应已返回
sleep 3

# 强制结束Python进程
echo "[$(date)] 正在停止Python进程..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true

# 等待进程完全停止
sleep 2

# 启动新的Python进程
echo "[$(date)] 正在启动新进程..."
cd "{current_dir}"
nohup {start_command} > /dev/null 2>&1 &

echo "[$(date)] 重启完成"
sleep 2
'''

        with open(linux_script, 'w', encoding='utf-8') as f:
            f.write(linux_content)

        # 设置Linux脚本执行权限
        import stat
        linux_script.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        scripts_created.append(str(linux_script))

        return {
            'success': True,
            'message': '重启脚本已创建',
            'scripts': scripts_created,
            'python_executable': python_exe,
            'script_path': script_path,
            'start_command': start_command,
            'process_config': config,
            'config_file': config_file
        }

    except Exception as e:
        logger.error(f"创建重启脚本失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'创建重启脚本失败: {str(e)}'
        )

@router.post("/system/process-restart")
async def process_restart_api(
    current_user: User = Depends(manage_system)
):
    """通过进程管理器重启服务"""
    try:
        # 记录操作
        logger.info(f"用户 {current_user.username} 请求通过进程管理器重启服务")

        # 发送重启命令给进程管理器
        command_file = Path("process_command.txt")
        command_file.write_text("restart")

        return {
            'success': True,
            'message': '重启命令已发送给进程管理器',
            'command': 'restart'
        }

    except Exception as e:
        logger.error(f"进程管理器重启失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'进程管理器重启失败: {str(e)}'
        )

@router.post("/system/process-stop")
async def process_stop_api(
    current_user: User = Depends(manage_system)
):
    """通过进程管理器停止服务"""
    try:
        # 记录操作
        logger.info(f"用户 {current_user.username} 请求通过进程管理器停止服务")

        # 发送停止命令给进程管理器
        command_file = Path("process_command.txt")
        command_file.write_text("stop")

        return {
            'success': True,
            'message': '停止命令已发送给进程管理器',
            'command': 'stop'
        }

    except Exception as e:
        logger.error(f"进程管理器停止失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'进程管理器停止失败: {str(e)}'
        )

@router.post("/system/process-force-restart")
async def process_force_restart_api(
    current_user: User = Depends(manage_system)
):
    """通过进程管理器强制重启服务"""
    try:
        # 记录操作
        logger.info(f"用户 {current_user.username} 请求通过进程管理器强制重启服务")

        # 发送强制重启命令给进程管理器
        command_file = Path("process_command.txt")
        command_file.write_text("force_restart")

        return {
            'success': True,
            'message': '强制重启命令已发送给进程管理器',
            'command': 'force_restart'
        }

    except Exception as e:
        logger.error(f"进程管理器强制重启失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'进程管理器强制重启失败: {str(e)}'
        )

@router.get("/system/process-config")
async def get_process_config_api(
    current_user: User = Depends(manage_system)
):
    """获取进程管理器配置"""
    try:
        config_file = Path("process_config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return {
                'success': True,
                'config': config,
                'config_file': str(config_file)
            }
        else:
            return {
                'success': False,
                'message': '配置文件不存在'
            }

    except Exception as e:
        logger.error(f"获取进程管理器配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'获取进程管理器配置失败: {str(e)}'
        )

@router.post("/system/process-config")
async def update_process_config_api(
    config_data: dict,
    current_user: User = Depends(manage_system)
):
    """更新进程管理器配置"""
    try:
        # 记录操作
        logger.info(f"用户 {current_user.username} 更新进程管理器配置")

        # 保存配置文件
        config_file = Path("process_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        # 发送配置更新命令给进程管理器
        command_file = Path("process_command.txt")
        command_file.write_text(f"config:{json.dumps(config_data)}")

        return {
            'success': True,
            'message': '配置已更新并发送给进程管理器',
            'config': config_data
        }

    except Exception as e:
        logger.error(f"更新进程管理器配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'更新进程管理器配置失败: {str(e)}'
        )

