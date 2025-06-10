import os
import json
from io import BytesIO
from typing import Dict, Optional, List

# from engineio.static_files import content_types
from fastapi import FastAPI, HTTPException, status, UploadFile, Request
from fastapi.routing import APIRoute

from app.models.extension import UpdateExtension

from .logger import extension_logger as logger
from .sandbox import load_module_in_sandbox, execute_query_in_sandbox, SandboxException
from .file_manager import FileManager
from .database import Database

# from app.models.extension import DynamicForm


class ExtensionManager:
    """
    扩展管理器类
    
    负责扩展的加载、卸载、配置管理和查询执行
    """
    def __init__(self, app: FastAPI, db: Database, extensions_dir: str,config_dir: str, file_manager: Optional[FileManager] = None):
        """
        初始化扩展管理器
        
        Args:
            app: FastAPI应用实例
            extensions_dir: 扩展文件目录
            file_manager: 文件管理器实例（可选）
            db: 数据库实例，如果提供则使用数据库存储配置
        """
        self.app = app
        self.extensions_dir = extensions_dir
        self.loaded_extensions: Dict[str, dict] = {}
        self.file_manager = file_manager
        self.db = db
        self.config_dir = config_dir
        # 确保目录存在
        os.makedirs(extensions_dir, exist_ok=True)
        os.makedirs(config_dir, exist_ok=True)
        logger.info(f"扩展管理器初始化完成。扩展目录: {extensions_dir}")
        if db:
            logger.info("使用数据库存储扩展配置")
        else:
            logger.info("使用JSON文件存储扩展配置")

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

    def load_extension(self, extension_id: str):
        """
        加载单个扩展
        
        Args:
            extension_id: 扩展ID
        """
        filepath = os.path.join(self.extensions_dir, f"{extension_id}.py")
        config_path = os.path.join(self.config_dir, f"{extension_id}.json")
        # 从数据库获取配置
        config = self.db.get_extension_config(extension_id)
        try:
            logger.info(f"开始加载扩展: {extension_id}")
            
            # 使用沙箱加载模块
            module = load_module_in_sandbox(extension_id, filepath)

            # 加载配置
            # config = None
            
            if self.db:
                # 从数据库加载配置
                config = self.db.get_extension_config(extension_id)
            else:
                # 从文件加载配置
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                    logger.debug(f"已加载扩展配置: {extension_id}")
                except FileNotFoundError:
                    logger.warning(f"扩展配置文件不存在: {config_path}，将使用默认配置")
            if not config:
                print(f"{filepath}，数据库信息不存在，加载失败")
                return
            # 如果配置不存在，创建默认配置
            # if not config:
            #     config = {
            #         "id": extension_id,
            #         "name": extension_id,
            #         "description": "无描述",
            #         "endpoint": f"/query/{extension_id}",
            #         "enabled": False,
            #         "config": {}
            #     }
            #     self.save_extension_config(extension_id, config)

            # 记录扩展信息
            self.loaded_extensions[extension_id] = {
                "module": module,
                "config": config,
                "has_config_form": hasattr(module, "get_config_form"),
                "has_query_form": hasattr(module, "get_query_form")
            }

            # 如果扩展启用，注册API路由
            if config.get("enabled", True):
                logger.info(f"为扩展 {extension_id} 注册API端点: {config['endpoint']}")
                self.app.add_api_route(
                    path=config["endpoint"],
                    endpoint=self.create_query_endpoint(module, extension_id),
                    methods=["POST"],
                    response_model=Dict,
                    tags=["extensions"],
                    summary=f"Extension endpoint for {extension_id}",
                    response_description="Extension query result"
                )
                logger.debug(f"扩展 {extension_id} 的API端点注册成功")
            
            # 尝试设置应用实例（如果扩展支持）
            if hasattr(module, 'set_app'):
                try:
                    module.set_app(self.app)
                    logger.info(f"已为扩展 {extension_id} 设置应用实例")
                except Exception as e:
                    logger.warning(f"为扩展 {extension_id} 设置应用实例失败: {str(e)}")

            logger.info(f"扩展 {extension_id} 加载完成")

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
                config = self.loaded_extensions[extension_id]["config"].get("config", {})
                
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
                        print("普通字段:", key, value)
                        query_params[key] = value
                # # 处理常规表单字段
                # for key, value in form.items():
                #     # 判断是否为文件
                #     if not isinstance(value, UploadFile):
                #         # 所有非文件字段都作为查询参数
                #         query_params[key] = value
                #         print("not file",key,value)
                #
                # # 处理文件上传
                # files = {}
                # for key, value in form.items():
                #     if isinstance(value, UploadFile):
                #         # 读取文件内容
                #         file_content = await value.read()
                #         # 重置文件指针，以便后续可能的读取
                #         await value.seek(0)
                #         print("file",key,value)
                #         # 将文件信息添加到files字典
                #         files[key] = {
                #             "filename": value.filename,
                #             "content_type": value.content_type,
                #             "content": file_content
                #         }
                
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
                
                logger.debug(f"查询参数: {str(params)[:1000]}...")  # 日志记录部分参数，避免过大
                
                # 在沙箱中执行查询
                result = execute_query_in_sandbox(module, params, config)
                logger.info(f"扩展 {extension_id} 查询成功完成")
                return result
                
            except SandboxException as e:
                logger.error(f"扩展 {extension_id} 查询执行失败(沙箱错误): {str(e)}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
            except Exception as e:
                logger.error(f"扩展 {extension_id} 查询执行失败: {str(e)}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        return query_endpoint

    def load_all_extensions(self):
        """加载所有扩展"""
        logger.info("开始加载所有扩展")
        count = 0
        for filename in os.listdir(self.extensions_dir):
            if filename.endswith(".py"):
                extension_id = filename[:-3]
                if self.load_extension(extension_id):
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

    def get_extension_config(self, extension_id: str) -> dict:
        """
        获取扩展配置
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            扩展配置字典
            
        Raises:
            HTTPException: 如果扩展未加载或配置文件不存在
        """
        if self.db:
            # 从数据库获取配置
            config = self.db.get_extension_config(extension_id)
            if not config:
                logger.error(f"扩展配置不存在: {extension_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Extension not loaded")
            return config
        else:
            # 从文件获取配置
            config_path = os.path.join(self.config_dir, f"{extension_id}.json")
            try:
                with open(config_path) as f:
                    return json.load(f)
            except FileNotFoundError as e:
                logger.error(f"扩展配置不存在: {extension_id}, {str(e)}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Extension not loaded,{e}")

    def save_extension_config(self, extension_id: str, updateExtension: UpdateExtension):
        """
        保存扩展配置
        
        Args:
            extension_id: 扩展ID
            config: 配置字典
        """
        if self.db:
            # 保存到数据库
            success = self.db.save_extension_config(extension_id, updateExtension)
            if not success:
                logger.error(f"保存扩展配置到数据库失败: {extension_id}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save extension config")
            logger.info(f"已保存扩展配置到数据库: {extension_id}")
        else:
            # 保存到文件
            config_path = os.path.join(self.config_dir, f"{extension_id}.json")
            try:
                with open(config_path, "w") as f:
                    json.dump(updateExtension.get('config', {}), f, indent=2)
                logger.info(f"已保存扩展配置: {extension_id}")
            except Exception as e:
                logger.error(f"保存扩展配置失败: {extension_id}, {str(e)}")
                raise
                
    def list_extensions(self) -> List[Dict]:
        """
        获取所有扩展的列表
        
        Returns:
            扩展信息列表
        """
        if self.db:
            # 从数据库获取所有扩展配置
            return self.db.list_extension_configs()
        else:
            # 从文件获取所有扩展配置
            extensions = []
            for filename in os.listdir(self.config_dir):
                if filename.endswith(".json"):
                    extension_id = filename[:-5]
                    try:
                        config = self.get_extension_config(extension_id)
                        extensions.append(config)
                    except Exception as e:
                        logger.error(f"获取扩展配置失败: {extension_id}, {str(e)}")
            return extensions

    def delete_extension(self, extension_id: str):
        """
        删除扩展
        """
        try:
            self.db.delete_extension_config(extension_id)
            self.remove_route(f"/query/{extension_id}")
            self.loaded_extensions.pop(extension_id)
            # logger.info(f"数据库 删除扩展 {extension_id} 成功")
            return True
        except Exception as e:
            # logger.error(f"数据库 删除扩展 {extension_id} 失败: {str(e)}")
            return False