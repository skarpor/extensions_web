import os
import json
from io import BytesIO
from typing import Dict, Optional, List

# from engineio.static_files import content_types
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, UploadFile, Request, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.routing import APIRoute
from sqlalchemy import select

from models.extension import Extension
from schemas.extension import ExtensionUpdate

from core.logger import get_logger
from core.sandbox import load_module_in_sandbox, execute_query_in_sandbox, SandboxException
from sqlalchemy.ext.asyncio import AsyncSession
from core.file_manager import FileManager
from core.config import settings
from api.v1.endpoints.database import db_manager
logger = get_logger("extension")
class ExtensionManager:
    """
    扩展管理器类
    
    负责扩展的加载、卸载、配置管理和查询执行
    """
    def __init__(self, app: FastAPI):
        """
        初始化扩展管理器
        
        Args:
            app: FastAPI应用实例
            extensions_dir: 扩展文件目录
            file_manager: 文件管理器实例（可选）
            db: 数据库实例，如果提供则使用数据库存储配置
        """
        self.app = app
        # self.db_session_maker = db_session_maker  # 传入会话工厂
        self.loaded_extensions: Dict[str, dict] = {}
        self.file_manager = None # 文件管理器、不使用了，太罗嗦
        # 额外的数据库，取决于api中的database
        self.db_manager = db_manager
        # 确保目录存在
        os.makedirs(settings.EXTENSIONS_DIR, exist_ok=True)
        logger.info(f"扩展管理器初始化完成。扩展目录: {settings.EXTENSIONS_DIR}")

    def get_route_by_path(self, path: str) -> Optional[APIRoute]:
        """
        获取指定路径的路由对象
        
        Args:
            path: API路径
            
        Returns:
            路由对象，如果不存在则返回None
        """
        for route in self.app.routes:
            if isinstance(route, APIRoute) and route.path == path:
                return route
        return None

    def route_exists(self, path: str) -> bool:
        """
        检查路由是否已存在
        
        Args:
            path: API路径
            
        Returns:
            如果路由存在返回True，否则返回False
        """
        return self.get_route_by_path(path) is not None

    async def load_extension(self, extension_id: str,db:AsyncSession):
        """
        加载单个扩展
        
        Args:
            extension_id: 扩展ID
        """
        filepath = os.path.join(settings.EXTENSIONS_DIR, f"{extension_id}.py")
        # 从数据库获取配置
        extension = await db.execute(select(Extension).where(Extension.id == extension_id))
        extension = extension.scalar_one_or_none()
        if not extension:
            logger.error(f"扩展配置不存在: {extension_id}")
            return 
        try:
            logger.info(f"开始加载扩展: {extension_id}")
            
            # 使用沙箱加载模块
            module = load_module_in_sandbox(filepath)

            # 记录扩展信息
            self.loaded_extensions[extension_id] = {
                "module": module,
                "extension": jsonable_encoder(extension),
                "has_config_form": hasattr(module, "get_config_form"),
                "has_query_form": hasattr(module, "get_query_form")
            }
            extension.has_config_form=hasattr(module, "get_config_form")
            extension.has_query_form=hasattr(module, "has_query_form")
            await db.commit()
            # 如果扩展启用，注册API路由
            if extension.enabled:
                logger.info(f"为扩展 {extension_id} 注册API端点: {extension.entry_point}")
                self.app.add_api_route(
                    path=extension.entry_point,
                    endpoint=self.create_query_endpoint(module, extension_id),
                    methods=["POST"],
                    response_model=Dict,
                    tags=["extensions"],
                    summary=f"Extension endpoint for {extension.name}",
                    response_description="Extension query result"
                )
                logger.debug(f"扩展 {extension_id} 的API端点注册成功")
            
            
            logger.info(f"扩展 {extension_id} 加载完成")
            return self.loaded_extensions[extension_id]

        except SandboxException as e:
            logger.error(f"扩展 {extension_id} 加载失败(沙箱错误): {str(e)}")
        except Exception as e:
            logger.error(f"扩展 {extension_id} 加载失败: {str(e)}")

    def create_query_endpoint(self, module, extension_id):
        """
        创建扩展的查询端点
        
        Args:
            module: 扩展模块
            extension_id: 扩展ID
            
        Returns:
            查询端点函数
        """
        # 修改路由接口，支持表单和文件上传
        async def query_endpoint(request: Request):
            logger.info(f"执行扩展查询: {extension_id}")
            
            try:
                config = self.loaded_extensions[extension_id]["extension"].get("config")
                # print(config)
                # print(json.dumps(config))
                # config=json.loads(json.dumps(config))
                try:
                    if config:
                        config = json.loads(config)  # 尝试解析 JSON 字符串
                    else:
                        config = {}
                except json.JSONDecodeError:
                    config = {}  # 如果解析失败，设为空字典

                print(config,type(config))
                # 使用表单接收数据，包括文件
                form = await request.form()
                # 打印所有字段和类型
                # for key, value in form.multi_items():
                #     print(f"字段: {key}, 类型: {type(value)}, 值: {value}")

                # 构建查询参数字典
                query_params = {}
                files={}
                # 统一处理所有表单字段
                for key, value in form.multi_items():
                    try:
                        is_file = value.filename
                    except AttributeError:
                        is_file = False
                    if is_file or isinstance(value, UploadFile):
                        # 处理文件上传
                        # print("检测到文件字段:", key, value.filename)

                        file_content = await value.read()
                        await value.seek(0)  # 重置文件指针
                        files[key] = {
                            "filename": value.filename,
                            "content_type": value.content_type,
                            "content": file_content
                        }
                    else:
                        # 处理普通表单字段
                        # print("普通字段:", key, value)
                        query_params[key] = value

                # 构建最终参数
                params = {
                    "query": query_params,
                    "files": files if files else None,  # 如果没有文件就设为None
                    "extension_id": extension_id
                }
                # print(params)
                # 如果有文件管理器，传递给沙箱环境
                if self.file_manager:
                    params["file_manager"] = self.file_manager
                    params["logger"] = get_logger("extension")

                logger.debug(f"查询参数: {str(params)[:1000]}...")  # 日志记录部分参数，避免过大
                if self.db_manager:
                    # 在沙箱中执行查询
                    result =await execute_query_in_sandbox(module, params, config,db_manager=self.db_manager)
                else:
                    # 在沙箱中执行查询
                    result =await execute_query_in_sandbox(module, params, config)
                logger.info(f"扩展 {extension_id} 查询成功完成")
                return result
                
            except SandboxException as e:
                raise
                logger.error(f"扩展 {extension_id} 查询执行失败(沙箱错误): {str(e)}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
            except Exception as e:
                raise
                logger.error(f"扩展 {extension_id} 查询执行失败: {str(e)}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        return query_endpoint

    async def load_all_extensions(self,db:AsyncSession):
        """加载所有扩展"""
        logger.info("开始加载所有扩展")
        count = 0
        for filename in os.listdir(settings.EXTENSIONS_DIR):
            if filename.endswith(".py"):
                extension_id = filename[:-3]
                if await self.load_extension(extension_id,db):
                    count += 1
        logger.info(f"完成加载所有扩展，共 {count} 个")

    def remove_route(self, path: str):
        """
        移除路由
        
        Args:
            path: 要移除的API路径
        """
        logger.info(f"移除API路由: {path}")
        for i, route in enumerate(self.app.routes):
            if hasattr(route, "path") and route.path == path:
                self.app.routes.pop(i)
                logger.debug(f"已从路由列表中移除: {path}")
                break

        # 清除FastAPI内部路由缓存
        self.app.openapi_schema = None
        self.app.setup()

    async def update_extension(self, extension_id: str, updateExtension: ExtensionUpdate,db:AsyncSession):
        """
        更新扩展
        
        Args:
            extension_id: 扩展ID
            updateExtension: 更新扩展模型
        """
        print(self.loaded_extensions)
        extension = await db.execute(select(Extension).where(Extension.id == extension_id))
        extension = extension.scalar_one_or_none()
        if not extension:
            logger.error(f"扩展配置不存在: {extension_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Extension not loaded")
            # 逐个更新字段
        # 更新字段
        update_data = updateExtension.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(extension, field, value)
        if update_data.get("enabled"):
            extension.entry_point=f"/query/{extension_id}"
            # 如果扩展启用，注册API路由
            logger.info(f"为扩展 {extension_id} 注册API端点: {extension.entry_point}")

            # 使用沙箱加载模块
            filepath = os.path.join(settings.EXTENSIONS_DIR, f"{extension_id}.py")
            module = load_module_in_sandbox(filepath)
            self.app.add_api_route(
                path=extension.entry_point,
                endpoint=self.create_query_endpoint(module, extension_id),
                methods=["POST"],
                response_model=Dict,
                tags=["extensions"],
                summary=f"Extension endpoint for {extension.name}",
                response_description="Extension query result"
            )
            logger.debug(f"扩展 {extension_id} 的API端点注册成功")
        else:
            try:
                self.remove_route(settings.EXTENSIONS_ENTRY_POINT_PREFIX+extension_id)
                self.loaded_extensions.pop(extension_id)
            except:
                pass

        extension.updated_at = datetime.now()
        await db.commit()
        await db.refresh(extension)
        logger.info(f"已保存扩展配置到数据库: {extension_id}")
        return extension
    async def list_extensions(self,db:AsyncSession):
        """
        获取所有扩展的列表
        
        Returns:
            扩展信息列表
        """
        extensions = await db.execute(select(Extension).where(Extension.deleted == False))
        return extensions.scalars().all()

    async def delete_extension(self, extension_id: str,db:AsyncSession):
        """
        删除扩展,修改deleted字段为True
        """
        try:
            print(self.loaded_extensions)
            extension = await db.execute(select(Extension).where(Extension.id == extension_id))
            extension = extension.scalar_one_or_none()
            if not extension:
                logger.error(f"扩展配置不存在: {extension_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Extension not loaded")
            extension.deleted = True
            await db.commit()
            print(self.loaded_extensions)
            self.remove_route(f"/query/{extension_id}")
            try:
                self.loaded_extensions.pop(extension_id)
            except:
                pass
            logger.info(f"数据库 删除扩展 {extension_id} 成功")
            return True
        except Exception as e:
            raise
            logger.error(f"数据库 删除扩展 {extension_id} 失败: {str(e)}")
            return False
    async def create_extension(self, extension_id: str, extension_data: dict, file: UploadFile,db:AsyncSession):
        """
        创建扩展
        """
        # 创建扩展文件
        extension_file = os.path.join(settings.EXTENSIONS_DIR, f"extension_{extension_id}.py")
        # 写入文件
        with open(extension_file, "wb") as f:
            f.write(file.file.read())
        # 写入数据库
        extension = Extension(
            id=extension_id,
            **extension_data,
            entry_point=settings.EXTENSIONS_ENTRY_POINT_PREFIX+extension_id
        )
        db.add(extension)
        await db.commit()
        await self.load_extension(extension_id,db)
        return True
    async def get_extension_document(self, extension_id: str) -> dict:
        """
        获取扩展文档
        """
        if extension_id not in self.loaded_extensions:
            logger.error(f"扩展配置不存在: {extension_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Extension not loaded")
        module = self.loaded_extensions[extension_id]["module"]
        # 获取module的get_document方法
        docstring = module.__doc__ or "无详细说明"
        function_docs = {
            "execute_query": module.execute_query.__doc__ or "无方法说明",
            "get_config_form": module.get_config_form.__doc__ if hasattr(module, "get_config_form") else None,
            "get_default_config": module.get_default_config.__doc__ if hasattr(module, "get_default_config") else None,
            "get_query_form": module.get_query_form.__doc__ if hasattr(module, "get_query_form") else None
        }

        return {  # 结构化文档信息
            "docs": docstring,
            "functions": function_docs
        }
    
