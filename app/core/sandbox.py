import importlib.util
import sys
import os
import builtins
import types
import threading
import time
import platform
if platform.system() == "Windows":
    resource = None
else:
    import resource
from typing import Dict, Any, Optional
from .logger import extension_logger as logger

class SandboxException(Exception):
    """沙箱执行过程中的异常"""
    pass

class Timeout(Exception):
    """执行超时异常"""
    pass

# 文件管理器API接口
class FileManagerAPI:
    """
    安全的文件管理器API接口
    
    提供限制性的文件管理功能，只允许特定操作
    """
    
    def __init__(self, file_manager, extension_id):
        """
        初始化文件管理器API
        
        Args:
            file_manager: 原始文件管理器
            extension_id: 扩展ID
        """
        self._file_manager = file_manager
        self._extension_id = extension_id
    
    def save_file(self, file_content, filename, content_type=None, description=None):
        """
        安全地保存文件
        
        Args:
            file_content: 文件内容（二进制数据）
            filename: 原始文件名
            content_type: 文件MIME类型
            description: 文件描述
            
        Returns:
            文件元数据字典，包含文件ID、名称等信息
        """
        try:
            # 确保文件内容是二进制
            if not isinstance(file_content, bytes):
                raise SandboxException("文件内容必须是字节类型(bytes)")
            
            # 限制文件大小
            max_size = 50 * 1024 * 1024  # 50MB
            if len(file_content) > max_size:
                raise SandboxException(f"文件大小超过限制: {len(file_content)/1024/1024:.2f}MB > 50MB")
            
            # 保存文件
            file_meta = self._file_manager.save_file(
                file_content=file_content,
                filename=filename,
                content_type=content_type,
                extension_id=self._extension_id,
                description=description
            )
            
            # 返回安全的文件元数据（移除敏感信息）
            safe_meta = {
                "id": file_meta["id"],
                "filename": file_meta["filename"],
                "content_type": file_meta["content_type"],
                "size": file_meta["size"],
                "created_at": file_meta["created_at"],
                "description": file_meta["description"]
            }
            
            return safe_meta
        
        except Exception as e:
            raise SandboxException(f"保存文件失败: {str(e)}")
    
    def list_files(self, limit=50, offset=0):
        """
        列出当前扩展的文件
        
        Args:
            limit: 返回的最大文件数
            offset: 结果起始位置
            
        Returns:
            文件元数据列表
        """
        try:
            # 只列出当前扩展的文件
            files = self._file_manager.list_files(
                extension_id=self._extension_id,
                limit=min(limit, 100),  # 限制最大返回数量
                offset=offset
            )
            
            # 移除敏感信息
            safe_files = []
            for file in files:
                safe_files.append({
                    "id": file["id"],
                    "filename": file["filename"],
                    "content_type": file.get("content_type"),
                    "size": file["size"],
                    "created_at": file["created_at"],
                    "description": file.get("description")
                })
            
            return safe_files
        
        except Exception as e:
            raise SandboxException(f"列出文件失败: {str(e)}")
    
    def get_file_url(self, file_id):
        """
        获取文件下载URL
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件下载URL
        """
        try:
            # 检查文件是否存在且属于当前扩展
            file = self._file_manager.get_file(file_id)
            
            if not file:
                raise SandboxException(f"文件不存在: {file_id}")
            
            if file.get("extension_id") != self._extension_id:
                raise SandboxException(f"无权访问此文件: {file_id}")
            
            # 返回文件下载URL
            return f"/api/files/{file_id}"
        
        except Exception as e:
            raise SandboxException(f"获取文件URL失败: {str(e)}")

# 安全的内置函数白名单
SAFE_BUILTINS = {
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
    'chr', 'complex', 'dict', 'dir', 'divmod', 'enumerate', 'filter',
    'float', 'format', 'frozenset', 'hash', 'hex', 'id', 'int', 'isinstance',
    'issubclass', 'iter', 'len', 'list', 'map', 'max', 'min', 'next',
    'object', 'oct', 'ord', 'pow', 'print', 'range', 'repr', 'reversed',
    'round', 'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip'
}

# 危险的模块黑名单
DANGEROUS_MODULES = {
    'os', 'sys', 'subprocess', 'multiprocessing', 'threading', 'socket',
    'pickle', 'marshal', 'builtins', 'ctypes', 'msvcrt', 'winreg',
    'platform', 'posix', 'pty', 'fcntl', 'pipes'
}

# 允许的模块白名单
ALLOWED_MODULES = {
    'datetime', 'json', 'math', 're', 'random', 'collections',
    'functools', 'itertools', 'decimal', 'string', 'time', 'uuid',
    'hashlib', 'base64', 'urllib.parse', 'csv', 'xml.etree.ElementTree','paramiko','requests',
    'xlsxwriter','openpyxl','apscheduler','pytz','pyquery','lxml','bs4','pyyaml','pyodbc',
    'pymysql','pymssql','psycopg2','sqlalchemy','cx_Oracle','pymongo','redis','elasticsearch',
    'pandas','numpy','scipy','matplotlib','seaborn','plotly','bokeh','altair','pyecharts',
    'pygal'

}

def timeout_handler(signum, frame):
    """超时信号处理函数"""
    raise Timeout("代码执行超时")

def run_with_timeout(func, args=(), kwargs={}, timeout_sec=5):
    """
    在限定时间内运行函数
    
    Args:
        func: 要执行的函数
        args: 函数参数
        kwargs: 函数关键字参数
        timeout_sec: 超时时间（秒）
        
    Returns:
        函数执行结果
        
    Raises:
        Timeout: 如果执行超时
    """
    result = [None]
    exception = [None]
    
    def worker():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout_sec)
    
    if thread.is_alive():
        # 线程仍在运行，表示超时
        raise Timeout(f"代码执行超过了 {timeout_sec} 秒限制")
    
    if exception[0]:
        raise exception[0]
        
    return result[0]

def create_restricted_environment():
    """
    创建一个受限的执行环境字典
    
    Returns:
        包含安全内置函数的环境字典
    """
    # 创建一个只包含安全内置函数的字典
    safe_builtins = {}
    for name in SAFE_BUILTINS:
        if hasattr(builtins, name):
            safe_builtins[name] = getattr(builtins, name)
    
    # 创建执行环境
    restricted_env = {
        '__builtins__': safe_builtins,
    }
    
    return restricted_env

def load_module_in_sandbox(extension_id, filepath):
    """
    在沙箱中加载模块
    
    Args:
        extension_id: 扩展ID
        filepath: 扩展文件路径
        
    Returns:
        加载的模块对象
        
    Raises:
        SandboxException: 如果加载失败或模块不安全
    """
    try:
        logger.info(f"尝试在沙箱中加载扩展: {extension_id}")
        
        # 读取文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 检查危险导入
        for module_name in DANGEROUS_MODULES:
            if f"import {module_name}" in code or f"from {module_name}" in code:
                logger.warning(f"扩展 {extension_id} 尝试导入危险模块: {module_name}")
                raise SandboxException(f"禁止导入不安全的模块: {module_name}")
        
        # 创建模块
        # print(extension_id,filepath)
        spec = importlib.util.spec_from_file_location(extension_id, filepath)
        module = importlib.util.module_from_spec(spec)
        
        # 限制模块访问
        for attr in list(module.__dict__.keys()):
            if attr not in ['__name__', '__doc__']:
                module.__dict__[attr] = None
        
        # 加载模块
        spec.loader.exec_module(module)
        
        # 验证模块接口
        if not hasattr(module, 'execute_query'):
            raise SandboxException("扩展必须实现 execute_query 函数")
        
        logger.info(f"扩展 {extension_id} 加载成功")
        return module
        
    except SandboxException as e:
        logger.error(f"沙箱加载错误 ({extension_id}): {str(e)}")
        raise
    except Exception as e:
        logger.error(f"扩展加载失败 ({extension_id}): {str(e)}")
        raise SandboxException(f"扩展加载失败: {str(e)}")

def execute_query_in_sandbox(module, params, config, timeout_sec=120):
    """
    在沙箱中执行查询
    
    Args:
        module: 扩展模块
        params: 查询参数
        config: 扩展配置
        timeout_sec: 超时时间（秒）
        
    Returns:
        查询结果
        
    Raises:
        SandboxException: 如果执行失败或不安全
    """
    try:
        # 设置资源限制 (仅在Unix系统上生效)
        if resource:
            try:
                resource.setrlimit(resource.RLIMIT_CPU, (timeout_sec, timeout_sec))
                resource.setrlimit(resource.RLIMIT_DATA, (100 * 1024 * 1024, 100 * 1024 * 1024))  # 100MB内存限制
            except (ImportError, AttributeError):
            # Windows下不支持资源限制
              pass
        
        # 检查是否有文件管理器，如果有则创建安全API
        file_manager = params.get("file_manager")
        extension_id = params.get("extension_id")
        
        if file_manager and extension_id:
            # 创建安全的文件管理器API
            params["file_manager"] = FileManagerAPI(file_manager, extension_id)
        else:
            # 移除不安全的参数
            params.pop("file_manager", None)
        
        # 使用超时机制执行查询
        result = run_with_timeout(
            module.execute_query, 
            args=(params, config), 
            timeout_sec=timeout_sec
        )
        
        return result
        
    except Timeout as e:
        logger.error(f"扩展执行超时: {str(e)}")
        raise SandboxException(f"执行超时: {str(e)}")
    except Exception as e:
        logger.error(f"扩展执行错误: {str(e)}")
        raise SandboxException(f"执行错误: {str(e)}") 