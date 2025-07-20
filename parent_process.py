#!/usr/bin/env python3
"""
通用进程管理器 - 管理任何程序的启动、重启和关闭
支持自定义命令、参数、端口检测等
"""
import subprocess
import sys
import time
import os
import signal
import threading
import json
import socket
import psutil
import platform
from pathlib import Path
import argparse
import shlex

class ProcessManager:
    def __init__(self, config=None):
        """
        初始化进程管理器
        config: 配置字典，包含以下字段：
        - command: 要执行的命令 (必需)
        - args: 命令参数列表 (可选)
        - cwd: 工作目录 (可选)
        - env: 环境变量 (可选)
        - check_port: 要检查的端口 (可选)
        - check_url: 要检查的URL (可选)
        - restart_delay: 重启延迟秒数 (默认2)
        - auto_restart: 是否自动重启 (默认True)
        - max_restart_attempts: 最大重启尝试次数 (默认-1无限制)
        """
        if config is None:
            config = {"command": "python", "args": ["main.py"]}

        self.config = config
        self.command = config.get("command", "python")
        self.args = config.get("args", [])
        self.cwd = config.get("cwd", os.getcwd())
        # 确保环境变量包含系统环境变量
        base_env = os.environ.copy()
        custom_env = config.get("env", {})
        if custom_env:
            base_env.update(custom_env)
        self.env = base_env
        self.check_port = config.get("check_port")
        self.check_url = config.get("check_url")
        self.restart_delay = config.get("restart_delay", 2)
        self.auto_restart = config.get("auto_restart", True)
        self.max_restart_attempts = config.get("max_restart_attempts", -1)

        self.process = None
        self.should_restart = True
        self.restart_requested = False
        self.restart_attempts = 0
        self.process_name = f"{self.command} {' '.join(self.args)}"
        
    def start_child_process(self):
        """启动子进程"""
        try:
            # 构建完整命令
            full_command = [self.command] + self.args
            print(f"[父进程] 启动子进程: {' '.join(full_command)}")
            print(f"[父进程] 工作目录: {self.cwd}")

            # 在Windows下，Python子进程通常使用GBK编码输出中文
            # 我们需要根据系统来选择合适的编码
            if platform.system().lower() == 'windows':
                # Windows下使用GBK编码
                process_encoding = 'gbk'
            else:
                # Linux/Mac使用UTF-8编码
                process_encoding = 'utf-8'

            self.process = subprocess.Popen(
                full_command,
                cwd=self.cwd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并stderr到stdout
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True,
                encoding=process_encoding,  # 根据系统选择编码
                errors='replace'    # 替换无法解码的字符
            )
            print(f"[父进程] 子进程已启动，PID: {self.process.pid}")

            # 启动输出监控线程
            output_thread = threading.Thread(target=self.monitor_output, daemon=True)
            output_thread.start()

            # 如果配置了端口检查，等待端口可用
            if self.check_port:
                self.wait_for_port()

            # 如果配置了URL检查，等待URL可访问
            if self.check_url:
                self.wait_for_url()

            self.restart_attempts = 0  # 重置重启计数
            return True
        except Exception as e:
            print(f"[父进程] 启动子进程失败: {e}")
            return False

    def monitor_output(self):
        """监控子进程输出"""
        if self.process and self.process.stdout:
            try:
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        print(f"[子进程] {line.rstrip()}")
                    if self.process.poll() is not None:
                        break
            except Exception as e:
                print(f"[父进程] 监控输出异常: {e}")

    def wait_for_port(self, timeout=30):
        """等待端口可用"""
        print(f"[父进程] 等待端口 {self.check_port} 可用...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', self.check_port))
                sock.close()
                if result == 0:
                    print(f"[父进程] 端口 {self.check_port} 已可用")
                    return True
            except:
                pass
            time.sleep(1)
        print(f"[父进程] 等待端口 {self.check_port} 超时")
        return False

    def wait_for_url(self, timeout=30):
        """等待URL可访问"""
        print(f"[父进程] 等待URL {self.check_url} 可访问...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                import requests
                response = requests.get(self.check_url, timeout=2)
                if response.status_code < 500:
                    print(f"[父进程] URL {self.check_url} 已可访问")
                    return True
            except:
                pass
            time.sleep(1)
        print(f"[父进程] 等待URL {self.check_url} 超时")
        return False
    
    def stop_child_process(self, force=False):
        """停止子进程"""
        if self.process and self.process.poll() is None:
            print(f"[父进程] 停止子进程 PID: {self.process.pid}")
            try:
                if force:
                    # 强制杀死
                    self.process.kill()
                    self.process.wait()
                    print(f"[父进程] 子进程已强制停止")
                else:
                    # 温和地终止进程
                    self.process.terminate()
                    # 等待3秒
                    try:
                        self.process.wait(timeout=3)
                        print(f"[父进程] 子进程已停止")
                    except subprocess.TimeoutExpired:
                        # 如果3秒后还没退出，强制杀死
                        print(f"[父进程] 温和停止超时，强制杀死子进程")
                        self.process.kill()
                        self.process.wait()
                        print(f"[父进程] 子进程已强制停止")
                return True
            except Exception as e:
                print(f"[父进程] 停止子进程失败: {e}")
                return False
        return True

    def kill_all_related_processes(self):
        """杀死所有相关进程（根据命令名称）"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and len(cmdline) > 0:
                        # 检查是否包含我们的命令
                        if self.command in ' '.join(cmdline):
                            print(f"[父进程] 杀死相关进程 PID: {proc.info['pid']}, 命令: {' '.join(cmdline)}")
                            proc.kill()
                            killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            print(f"[父进程] 已杀死 {killed_count} 个相关进程")
            return killed_count > 0
        except Exception as e:
            print(f"[父进程] 杀死相关进程失败: {e}")
            return False
    
    def restart_child_process(self, force=False):
        """重启子进程"""
        print(f"[父进程] 开始重启子进程...")
        self.restart_requested = True
        self.restart_attempts += 1

        # 检查重启次数限制
        if self.max_restart_attempts > 0 and self.restart_attempts > self.max_restart_attempts:
            print(f"[父进程] 已达到最大重启次数限制 ({self.max_restart_attempts})")
            self.restart_requested = False
            return False

        # 停止当前进程
        if self.stop_child_process(force):
            print(f"[父进程] 等待 {self.restart_delay} 秒后重启...")
            time.sleep(self.restart_delay)

            # 启动新进程
            if self.start_child_process():
                print(f"[父进程] 子进程重启成功 (第 {self.restart_attempts} 次)")
                self.restart_requested = False
                return True

        print(f"[父进程] 子进程重启失败 (第 {self.restart_attempts} 次)")
        self.restart_requested = False
        return False

    def force_restart(self):
        """强制重启（杀死所有相关进程）"""
        print(f"[父进程] 开始强制重启...")
        self.kill_all_related_processes()
        time.sleep(self.restart_delay)
        return self.start_child_process()
    
    def monitor_child_process(self):
        """监控子进程"""
        while self.should_restart:
            if self.process is None and not self.restart_requested:
                # 如果没有进程且不是重启中，启动一个
                if not self.start_child_process():
                    print(f"[父进程] 启动失败，{self.restart_delay}秒后重试...")
                    time.sleep(self.restart_delay)
                    continue

            # 检查进程状态
            if self.process and self.process.poll() is not None:
                # 进程已退出
                exit_code = self.process.returncode
                print(f"[父进程] 子进程已退出，退出码: {exit_code}")

                if not self.restart_requested and self.auto_restart:
                    # 如果不是主动重启且允许自动重启
                    if self.max_restart_attempts > 0 and self.restart_attempts >= self.max_restart_attempts:
                        print(f"[父进程] 已达到最大重启次数限制，停止自动重启")
                        self.should_restart = False
                        break

                    print(f"[父进程] {self.restart_delay}秒后自动重启子进程...")
                    time.sleep(self.restart_delay)

                self.process = None
            else:
                # 进程正在运行或重启中，等待1秒后再检查
                time.sleep(1)
    
    def handle_commands(self):
        """处理命令文件"""
        command_file = Path("process_command.txt")

        while self.should_restart:
            if command_file.exists():
                try:
                    command_data = command_file.read_text().strip()
                    command_file.unlink()  # 删除命令文件

                    if command_data == "restart":
                        print(f"[父进程] 检测到重启请求")
                        self.restart_child_process()
                    elif command_data == "force_restart":
                        print(f"[父进程] 检测到强制重启请求")
                        self.force_restart()
                    elif command_data == "stop":
                        print(f"[父进程] 检测到停止请求")
                        self.should_restart = False
                        self.stop_child_process()
                    elif command_data == "force_stop":
                        print(f"[父进程] 检测到强制停止请求")
                        self.should_restart = False
                        self.kill_all_related_processes()
                    elif command_data.startswith("config:"):
                        # 动态更新配置
                        try:
                            config_json = command_data[7:]  # 去掉 "config:" 前缀
                            new_config = json.loads(config_json)
                            self.update_config(new_config)
                            print(f"[父进程] 配置已更新")
                        except Exception as e:
                            print(f"[父进程] 配置更新失败: {e}")
                    else:
                        print(f"[父进程] 未知命令: {command_data}")
                except Exception as e:
                    print(f"[父进程] 处理命令失败: {e}")
            time.sleep(1)

    def update_config(self, new_config):
        """动态更新配置"""
        for key, value in new_config.items():
            if hasattr(self, key):
                setattr(self, key, value)
                print(f"[父进程] 更新配置 {key} = {value}")
        self.config.update(new_config)
    
    def run(self):
        """运行父进程管理器"""
        print(f"[父进程] 进程管理器启动，PID: {os.getpid()}")
        print(f"[父进程] 管理命令: {self.process_name}")
        print(f"[父进程] 工作目录: {self.cwd}")
        print(f"[父进程] 配置: {json.dumps(self.config, indent=2)}")

        # 启动监控线程
        monitor_thread = threading.Thread(target=self.monitor_child_process, daemon=True)
        monitor_thread.start()

        # 启动命令监听线程
        command_thread = threading.Thread(target=self.handle_commands, daemon=True)
        command_thread.start()

        try:
            # 主线程等待
            while self.should_restart:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"[父进程] 收到中断信号，正在关闭...")
            self.should_restart = False
            self.stop_child_process()
            print(f"[父进程] 已关闭")

    def save_config(self, config_file="process_config.json"):
        """保存配置到文件"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[父进程] 配置已保存到 {config_file}")
            return True
        except Exception as e:
            print(f"[父进程] 保存配置失败: {e}")
            return False

    @staticmethod
    def load_config(config_file="process_config.json"):
        """从文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"[父进程] 配置已从 {config_file} 加载")
            return config
        except Exception as e:
            print(f"[父进程] 加载配置失败: {e}")
            return None

def send_command(command):
    """发送命令给进程管理器"""
    command_file = Path("process_command.txt")
    command_file.write_text(command)
    print(f"命令已发送: {command}")

def create_config_from_args(args):
    """从命令行参数创建配置"""
    config = {
        "command": args.command,
        "args": args.args if args.args else [],
        "cwd": args.cwd if args.cwd else os.getcwd(),
        "restart_delay": args.restart_delay,
        "auto_restart": args.auto_restart,
        "max_restart_attempts": args.max_restart_attempts
    }

    if args.port:
        config["check_port"] = args.port
    if args.url:
        config["check_url"] = args.url
    if args.env:
        env_dict = {}
        for env_pair in args.env:
            if '=' in env_pair:
                key, value = env_pair.split('=', 1)
                env_dict[key] = value
        if env_dict:
            config["env"] = {**os.environ, **env_dict}

    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='通用进程管理器')
    subparsers = parser.add_subparsers(dest='action', help='操作命令')

    # start 命令
    start_parser = subparsers.add_parser('start', help='启动进程管理器')
    start_parser.add_argument('command', nargs='?', help='要执行的命令')
    start_parser.add_argument('args', nargs='*', help='命令参数')
    start_parser.add_argument('--cwd', help='工作目录')
    start_parser.add_argument('--port', type=int, help='检查的端口')
    start_parser.add_argument('--url', help='检查的URL')
    start_parser.add_argument('--restart-delay', type=int, default=2, help='重启延迟秒数')
    start_parser.add_argument('--no-auto-restart', dest='auto_restart', action='store_false', help='禁用自动重启')
    start_parser.add_argument('--max-restart', type=int, default=-1, dest='max_restart_attempts', help='最大重启次数')
    start_parser.add_argument('--env', action='append', help='环境变量 (格式: KEY=VALUE)')
    start_parser.add_argument('--config', help='配置文件路径')
    start_parser.add_argument('--save-config', help='保存配置到文件')

    # 控制命令
    subparsers.add_parser('restart', help='重启进程')
    subparsers.add_parser('force-restart', help='强制重启进程')
    subparsers.add_parser('stop', help='停止进程')
    subparsers.add_parser('force-stop', help='强制停止进程')

    # config 命令
    config_parser = subparsers.add_parser('config', help='更新配置')
    config_parser.add_argument('config_json', help='JSON格式的配置')

    args = parser.parse_args()

    if args.action == 'start':
        # 启动进程管理器
        if args.config:
            # 从配置文件加载
            config = ProcessManager.load_config(args.config)
            if config is None:
                print(f"无法加载配置文件: {args.config}")
                sys.exit(1)
        elif args.command:
            # 从命令行参数创建配置
            config = create_config_from_args(args)
        else:
            print("错误: 必须指定命令或配置文件")
            sys.exit(1)

        manager = ProcessManager(config)

        # 保存配置（如果指定）
        if args.save_config:
            manager.save_config(args.save_config)

        manager.run()

    elif args.action == 'restart':
        send_command('restart')
    elif args.action == 'force-restart':
        send_command('force_restart')
    elif args.action == 'stop':
        send_command('stop')
    elif args.action == 'force-stop':
        send_command('force_stop')
    elif args.action == 'config':
        send_command(f'config:{args.config_json}')
    else:
        # 默认行为：如果没有参数，尝试加载默认配置或使用默认设置
        config = ProcessManager.load_config()
        if config is None:
            config = {"command": "python", "args": ["main.py"]}

        manager = ProcessManager(config)
        manager.run()
