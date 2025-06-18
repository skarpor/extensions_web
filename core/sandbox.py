"""
扩展沙箱模块

提供安全的扩展执行环境，限制扩展的权限和资源访问。
"""
import os
import sys
import importlib.util
from typing import Any, Dict, Optional
from io import BytesIO
import inspect

from core.db_manager import DBManager
from core.file_manager import FileManager
class SandboxException(Exception):
    """沙箱异常"""
    pass

class FileManagerAPI:
    """安全的文件管理器API接口"""
    
    def __init__(self, file_manager: FileManager, extension_id: str):
        """初始化文件管理器API"""
        self._file_manager = file_manager
        self._extension_id = extension_id
    
    def save_file(self, file_content: bytes, filename: str, content_type: Optional[str] = None, description: Optional[str] = None) -> Dict:
        """安全地保存文件"""
        try:
            # 创建文件对象
            file_obj = BytesIO(file_content)
            file_obj.name = filename
            
            # 保存文件
            result = self._file_manager.save_file(
                file=file_obj,
                filename=filename,
                content_type=content_type,
                description=description,
                owner_id=self._extension_id
            )
            
            return result
        except Exception as e:
            raise SandboxException(f"保存文件失败: {str(e)}")

def load_module_in_sandbox(filepath: str) -> Any:
    """在沙箱环境中加载模块"""
    try:
        # 检查文件是否存在
        if not os.path.exists(filepath):
            raise SandboxException(f"模块文件不存在: {filepath}")
        
        # 获取模块名
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        
        # 加载模块
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if not spec or not spec.loader:
            raise SandboxException(f"无法加载模块: {filepath}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        
        # 验证模块接口
        if not hasattr(module, "execute_query"):
            raise SandboxException("模块必须实现execute_query方法")
        
        return module
        
    except SandboxException:
        raise
    except Exception as e:
        raise SandboxException(f"加载模块失败: {str(e)}")
from sqlalchemy.ext.asyncio import AsyncSession
async def execute_query_in_sandbox(module: Any, params: Dict, config: Dict, files: Optional[Dict] = None, file_manager: Optional[FileManager] = None,db_manager:Optional[DBManager]=None) -> Any:
    """在沙箱环境中执行查询"""
    try:
        # 如果有文件管理器，创建API接口
        if file_manager and files:
            file_api = FileManagerAPI(file_manager, module.__name__)
            params["files"] = files
            params["file_manager"] = file_api
        parameters=[]
        # 执行查询,根据参数名称注入所需的参数
        # 获取execute_query方法的参数
        sig = inspect.signature(module.execute_query)
        # 根据参数名称注入所需的参数
        for param in sig.parameters.values():
            if param.name == "params":
                parameters.append(params)
            elif param.name == "config":
                parameters.append(config)
            elif param.name == "db_manager":
                parameters.append(db_manager)
            else:
                parameters.append(param.default)
        print(config,params,db_manager)
        result = await module.execute_query(*parameters)
        return result
        
    except Exception as e:
        raise
        raise SandboxException(f"执行查询失败: {str(e)}") 