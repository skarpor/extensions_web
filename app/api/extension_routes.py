from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import PlainTextResponse
from typing import List, Optional
import uuid
import os

from app.models.user import User
from ..models.extension import ExtensionConfig
from ..core.extension_manager import ExtensionManager
from ..core.logger import extension_logger as logger
from ..core.sandbox import load_module_in_sandbox, SandboxException
from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user
router = APIRouter()
extension_manager: ExtensionManager = None

from config import templates

def init_router(manager: ExtensionManager):
    """
    初始化路由器
    
    Args:
        manager: 扩展管理器实例
    """
    global extension_manager
    extension_manager = manager
    logger.info("扩展路由初始化完成")


@router.post("/api/extensions/upload")
async def upload_extension(
        file: UploadFile = File(...),
        name: str = Form(...),
        description: str = Form(...),
        return_type: Optional[str] = Form(None),
        showinindex: bool = Form(True),
        current_user: User = Depends(get_current_user)
):
    """
    处理扩展上传
    
    Args:
        file: 上传的扩展文件
        name: 扩展名称
        description: 扩展描述
        return_type: 返回类型
        showinindex: 是否在首页显示
        current_user: 当前用户
        
    Returns:
        上传结果
        
    Raises:
        HTTPException: 如果上传失败或权限不足
    """
    logger.info(f"用户 {current_user.username} 尝试上传扩展: {name}")

    if current_user.role != "admin":
        logger.warning(f"非管理员用户 {current_user.username} 尝试上传扩展")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Only admin can upload extensions")

    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=500, detail="Extension manager not initialized")

    try:
        # 验证文件类型
        if not file.filename.endswith('.py'):
            logger.warning(f"尝试上传非Python文件: {file.filename}")
            raise HTTPException(status_code=400, detail="只能上传 Python (.py) 文件")

        extension_id = "extension_"+str(uuid.uuid4()).replace('-','_')
        filename = f"{extension_id}.py"
        filepath = os.path.join(extension_manager.extensions_dir, filename)

        try:
            # 重置文件指针位置并读取内容
            await file.seek(0)
            contents = await file.read()
            
            # 写入文件
            with open(filepath, "wb") as f:
                f.write(contents)
            logger.debug(f"扩展文件已保存: {filepath}")
            
            try:
                # 尝试在沙箱中加载模块以验证其有效性
                module = load_module_in_sandbox(extension_id, filepath)
                logger.info(f"扩展 {name} ({extension_id}) 成功加载测试")
            except SandboxException as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                logger.error(f"扩展加载测试失败(沙箱错误): {str(e)}")
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"加载失败，文件内容有问题！-> {str(e)}")
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                logger.error(f"扩展加载测试失败: {str(e)}")
                return HTTPException(status.HTTP_403_FORBIDDEN, f"加载失败，文件内容有问题！-> {str(e)}")
            
            # 如果没有指定返回类型，尝试从函数注解获取
            if not return_type:
                if hasattr(module.execute_query, "__annotations__"):
                    return_type = module.execute_query.__annotations__.get("return", None)
            
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

            config["documentation"] = {  # 结构化文档信息
                "module": docstring,
                "functions": function_docs
            }

            # 保存配置并加载扩展
            extension_manager.save_extension_config(extension_id, config)
            extension_manager.load_extension(extension_id)
            
            logger.info(f"扩展 {name} ({extension_id}) 上传成功")
            return {"success": True, "id": extension_id, "config": config}

        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            logger.error(f"扩展上传处理过程中出错: {str(e)}")
            raise e

    except Exception as e:
        logger.error(f"扩展上传失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/api/extensions", response_model=List[ExtensionConfig])
async def get_extensions():
    """
    获取所有扩展列表
    
    Returns:
        扩展配置列表
        
    Raises:
        HTTPException: 如果扩展管理器未初始化
    """
    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=500, detail="Extension manager not initialized")
    
    try:
        # 使用扩展管理器的list_extensions方法获取所有扩展配置
        extensions = extension_manager.list_extensions()
        return extensions
    except Exception as e:
        logger.error(f"获取扩展列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get extensions: {str(e)}")


@router.get("/config/{extension_id}/form", response_class=PlainTextResponse)
async def get_extension_config_form(extension_id: str):
    """
    获取扩展的配置表单HTML
    
    Args:
        extension_id: 扩展ID
        
    Returns:
        配置表单HTML
        
    Raises:
        HTTPException: 如果扩展未加载或不存在配置表单
    """
    logger.info(f"获取扩展配置表单: {extension_id}")
    
    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=500, detail="Extension manager not initialized")

    if extension_id not in extension_manager.loaded_extensions:
        logger.warning(f"尝试获取未加载扩展的配置表单: {extension_id}")
        raise HTTPException(status_code=404, detail="Extension not loaded")

    module = extension_manager.loaded_extensions[extension_id]["module"]
    if not hasattr(module, "get_config_form"):
        logger.debug(f"扩展 {extension_id} 没有配置表单")
        return "该扩展没有可配置选项"

    try:
        config_data = await get_extension(extension_id)
        config_data = config_data.get("config")
        form_html = module.get_config_form()
        
        # 如果表单包含模板标记，则渲染模板
        if "{{ config." in form_html:
            from jinja2 import Template
            template = Template(form_html)
            form_html = template.render(config=config_data)
            
        logger.debug(f"成功获取扩展 {extension_id} 的配置表单")
        return form_html
    except Exception as e:
        logger.error(f"生成扩展 {extension_id} 配置表单时出错: {str(e)}")
        return f"生成配置表单时出错: {str(e)}"


# 获取扩展的查询表单HTML
@router.get("/api/extensions/{extension_id}/query_form", response_class=PlainTextResponse)
async def get_extension_query_form(extension_id: str):
    """
    获取扩展的查询表单HTML
    
    Args:
        extension_id: 扩展ID
        
    Returns:
        查询表单HTML
        
    Raises:
        HTTPException: 如果扩展未加载或不存在查询表单
    """
    logger.info(f"获取扩展查询表单: {extension_id}")
    
    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=500, detail="Extension manager not initialized")
    
    if extension_id not in extension_manager.loaded_extensions:
        logger.warning(f"尝试获取未加载扩展的查询表单: {extension_id}")
        raise HTTPException(status_code=404, detail="Extension not loaded")
        
    module = extension_manager.loaded_extensions[extension_id]["module"]
    if not hasattr(module, "get_query_form"):
        logger.debug(f"扩展 {extension_id} 没有查询表单")
        return "该扩展没有可配置选项"
        
    try:
        form_html = module.get_query_form()
        logger.debug(f"成功获取扩展 {extension_id} 的查询表单")
        return form_html
    except Exception as e:
        logger.error(f"生成扩展 {extension_id} 查询表单时出错: {str(e)}")
        return f"生成查询表单时出错: {str(e)}"


@router.get("/api/extensions/{extension_id}")
async def get_extension(extension_id: str):
    """
    获取扩展配置
    
    Args:
        extension_id: 扩展ID
        
    Returns:
        扩展配置
        
    Raises:
        HTTPException: 如果扩展管理器未初始化或扩展不存在
    """
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

        config["documentation"] = {  # 结构化文档信息
            "module": docstring,
            "functions": function_docs
        }

        logger.debug(f"成功获取扩展配置: {extension_id}")
        return config
    except HTTPException as e:
        # 已经是HTTPException，直接抛出
        raise
    except Exception as e:
        logger.error(f"获取扩展 {extension_id} 配置时出错: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"获取扩展配置失败: {str(e)}")


@router.put("/api/extensions/{extension_id}")
async def update_extension_config(
    config: ExtensionConfig, 
    current_user: User = Depends(get_current_user),
):
    """
    更新扩展配置
    
    Args:
        config: 扩展配置
        current_user: 当前用户
        
    Returns:
        更新结果
        
    Raises:
        HTTPException: 如果更新失败或权限不足
    """
    logger.info(f"用户 {current_user.username} 尝试更新扩展配置: {config.id}")

    if current_user.role != "admin":
        logger.warning(f"非管理员用户 {current_user.username} 尝试更新扩展配置")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Only admin can update extensions")

    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension manager not initialized")
    
    logger.debug(f"更新扩展配置: {config.dict()}")
    config_dict = config.dict()
    extension_id = config_dict["id"]

    try:
        # 保留原有配置中的某些字段
        fconfig = extension_manager.get_extension_config(extension_id)
        config_dict['documentation'] = fconfig.get("documentation")
        config_dict['has_config_form'] = fconfig.get("has_config_form")
        config_dict['has_query_form'] = fconfig.get("has_query_form")
        
        # 保存配置并重新加载扩展
        extension_manager.save_extension_config(extension_id, config_dict)
        
        # 如果扩展已经加载，先从加载列表中移除
        if extension_id in extension_manager.loaded_extensions:
            del extension_manager.loaded_extensions[extension_id]
            
        # 重新加载扩展
        extension_manager.load_extension(extension_id)
        
        logger.info(f"扩展 {extension_id} 配置更新成功")
        return {"success": True}
    except Exception as e:
        logger.error(f"更新扩展 {extension_id} 配置时出错: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"更新扩展配置失败: {str(e)}")


@router.delete("/api/extensions/{extension_id}")
async def delete_extension(extension_id: str, current_user: User = Depends(get_current_user)):
    """
    删除扩展
    
    Args:
        extension_id: 扩展ID
        current_user: 当前用户
        
    Returns:
        删除结果
        
    Raises:
        HTTPException: 如果删除失败或权限不足
    """
    logger.info(f"用户 {current_user.username} 尝试删除扩展: {extension_id}")

    if current_user.role != "admin":
        logger.warning(f"非管理员用户 {current_user.username} 尝试删除扩展")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Only admin can delete extensions")
        
    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Extension manager not initialized")

    try:
        # 获取扩展配置
        config = extension_manager.get_extension_config(extension_id)
        
        # 移除API路由
        extension_manager.remove_route(config["endpoint"])
        
        # 从加载列表中移除
        if extension_id in extension_manager.loaded_extensions:
            del extension_manager.loaded_extensions[extension_id]

        # 删除文件
        # extension_file = os.path.join(extension_manager.extensions_dir, f"{extension_id}.py")
        # config_file = os.path.join(extension_manager.config_dir, f"{extension_id}.json")
        # if os.path.exists(extension_file):
        #     os.remove(extension_file)
        #     
        # if os.path.exists(config_file):
        #     os.remove(config_file)
        # 删除数据库中的数据
        extension_manager.delete_extension(extension_id)

        logger.info(f"扩展 {extension_id} 删除成功")
        return {"success": True}
    except Exception as e:
        logger.error(f"删除扩展 {extension_id} 时出错: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/api/extensions/view/{extension_id}")
async def view_extension(request: Request, extension_id: str, current_user: Optional[User] = None):
    """
    查看扩展详情页面
    
    Args:
        request: 请求对象
        extension_id: 扩展ID
        current_user: 当前用户(可选)
        
    Returns:
        扩展详情页面
    """
    if not extension_manager:
        logger.error("扩展管理器未初始化")
        raise HTTPException(status_code=500, detail="Extension manager not initialized")
    
    try:
        # 获取扩展配置
        extension = extension_manager.get_extension_config(extension_id)
        if not extension:
            logger.warning(f"尝试查看不存在的扩展: {extension_id}")
            raise HTTPException(status_code=404, detail="Extension not found")
        
        return templates.TemplateResponse(
            "extension_view.html",
            {
                "request": request,
                "extension": extension,
                "user": current_user
            }
        )
    except Exception as e:
        logger.error(f"查看扩展详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to view extension: {str(e)}")



