"""
扩展管理API路由
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import PlainTextResponse
from typing import List, Optional
import uuid
import os

from new_app.models.user import User
from new_app.models.extension import ExtensionConfig
from new_app.core.extension_manager import ExtensionManager
from new_app.core.logger import get_logger
from new_app.core.sandbox import load_module_in_sandbox, SandboxException
from new_app.core.auth import get_current_user

router = APIRouter(prefix="/api/v1/extensions", tags=["extensions"])
extension_manager: ExtensionManager = None
logger = get_logger("extension_routes")

def init_router(manager: ExtensionManager):
    """初始化路由器"""
    global extension_manager
    extension_manager = manager
    logger.info("扩展路由初始化完成")

@router.post("/upload")
async def upload_extension(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(...),
    return_type: Optional[str] = Form(None),
    showinindex: bool = Form(True),
    current_user: User = Depends(get_current_user)
):
    """上传扩展"""
    if not extension_manager:
        raise HTTPException(status_code=500, detail="Extension manager not initialized")
    
    try:
        # 生成扩展ID
        extension_id = str(uuid.uuid4())
        
        # 读取文件内容
        content = await file.read()
        
        # 保存扩展文件
        extension_path = os.path.join(extension_manager.extensions_dir, f"{extension_id}.py")
        with open(extension_path, "wb") as f:
            f.write(content)
            
        # 尝试在沙箱中加载模块
        try:
            module = load_module_in_sandbox(extension_path)
        except SandboxException as e:
            # 清理文件
            os.remove(extension_path)
            raise HTTPException(status_code=400, detail=f"Invalid extension: {str(e)}")
            
        # 准备扩展配置
        config = {
            "id": extension_id,
            "name": name,
            "description": description,
            "endpoint": f"/query/{extension_id}",
            "enabled": False,
            "config": {},
            "has_config_form": hasattr(module, "get_config_form"),
            "has_query_form": hasattr(module, "get_query_form"),
            "documentation": "",
            "return_type": return_type,
            "showinindex": showinindex,
        }
        
        # 如果模块有默认配置生成逻辑，获取默认配置
        if hasattr(module, "get_default_config"):
            config["config"] = module.get_default_config()
        
        # 提取文档信息
        docstring = module.__doc__ or "无详细说明"
        function_docs = {
            "execute_query": module.execute_query.__doc__ or "无方法说明",
            "get_config_form": module.get_config_form.__doc__ if hasattr(module, "get_config_form") else None,
            "get_default_config": module.get_default_config.__doc__ if hasattr(module, "get_default_config") else None,
            "get_query_form": module.get_query_form.__doc__ if hasattr(module, "get_query_form") else None
        }

        config["documentation"] = {
            "module": docstring,
            "functions": function_docs
        }

        # 保存配置并加载扩展
        extension_manager.save_extension_config(extension_id, config)
        extension_manager.load_extension(extension_id)
        
        logger.info(f"扩展 {name} ({extension_id}) 上传成功")
        return {"success": True, "id": extension_id, "config": config}
        
    except Exception as e:
        logger.error(f"上传扩展失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ExtensionConfig])
async def get_extensions():
    """获取所有扩展列表"""
    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=500, detail="Extension manager not initialized")
    
    try:
        extensions = extension_manager.list_extensions()
        return extensions
    except Exception as e:
        logger.error(f"获取扩展列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{extension_id}")
async def get_extension(extension_id: str):
    """获取扩展配置"""
    logger.info(f"获取扩展配置: {extension_id}")
    
    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=500, detail="Extension manager not initialized")

    try:
        module = extension_manager.loaded_extensions[extension_id]["module"]
        config = extension_manager.get_extension_config(extension_id)

        # 提取文档信息
        docstring = module.__doc__ or "无详细说明"
        function_docs = {
            "execute_query": module.execute_query.__doc__ or "无方法说明",
            "get_config_form": module.get_config_form.__doc__ if hasattr(module, "get_config_form") else None,
            "get_default_config": module.get_default_config.__doc__ if hasattr(module, "get_default_config") else None,
            "get_query_form": module.get_query_form.__doc__ if hasattr(module, "get_query_form") else None
        }

        config["documentation"] = {
            "module": docstring,
            "functions": function_docs
        }

        logger.debug(f"成功获取扩展配置: {extension_id}")
        return config
    except Exception as e:
        logger.error(f"获取扩展 {extension_id} 配置时出错: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{extension_id}")
async def delete_extension(extension_id: str, current_user: User = Depends(get_current_user)):
    """删除扩展"""
    logger.info(f"用户 {current_user.username} 尝试删除扩展: {extension_id}")

    if current_user.role != "admin":
        logger.warning(f"非管理员用户 {current_user.username} 尝试删除扩展")
        raise HTTPException(status_code=401, detail="Only admin can delete extensions")
        
    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=501, detail="Extension manager not initialized")

    try:
        # 获取扩展配置
        config = extension_manager.get_extension_config(extension_id)
        
        # 移除API路由
        extension_manager.remove_route(config["endpoint"])
        
        # 从加载列表中移除
        if extension_id in extension_manager.loaded_extensions:
            del extension_manager.loaded_extensions[extension_id]

        # 删除数据库中的数据
        extension_manager.delete_extension(extension_id)

        logger.info(f"扩展 {extension_id} 删除成功")
        return {"success": True}
    except Exception as e:
        logger.error(f"删除扩展 {extension_id} 时出错: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 