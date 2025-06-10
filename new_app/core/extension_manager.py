"""
扩展管理器模块
"""
import os
import json
from io import BytesIO
from typing import Dict, Optional, List

from fastapi import FastAPI, HTTPException, status, UploadFile, Request
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

from new_app.core.logger import get_logger
from new_app.core.sandbox import load_module_in_sandbox, execute_query_in_sandbox, SandboxException
from new_app.core.file_manager import FileManager
from new_app.core.extension_file_manager import ExtensionFileManager

logger = get_logger("extension_manager")

class ExtensionManager:
    """扩展管理器类"""
    
    def __init__(self, extensions_dir: str, config_dir: str, file_manager: Optional[FileManager] = None):
        """初始化扩展管理器"""
        self.extensions_dir = extensions_dir
        self.loaded_extensions: Dict[str, dict] = {}
        self.file_manager = file_manager
        self.config_dir = config_dir
        
        # 初始化扩展程序文件管理器
        self.extension_file_manager = ExtensionFileManager(os.path.join(extensions_dir, "files"))
        
        # 确保目录存在
        os.makedirs(extensions_dir, exist_ok=True)
        os.makedirs(config_dir, exist_ok=True)
        logger.info(f"扩展管理器初始化完成。扩展目录: {extensions_dir}")
        # if db:
        #     logger.info("使用数据库存储扩展配置")
        # else:
        #     logger.info("使用JSON文件存储扩展配置")

    def get_route_by_path(self, path: str) -> Optional[APIRoute]:
        """获取指定路径的路由对象"""
        for route in self.app.routes:
            if isinstance(route, APIRoute) and route.path == path:
                return route
        return None

    def route_exists(self, path: str) -> bool:
        """检查路由是否已存在"""
        return self.get_route_by_path(path) is not None

    def load_extension(self, extension_id: str,db:AsyncSession):
        """加载单个扩展"""
        filepath = os.path.join(self.extensions_dir, f"{extension_id}.py")
        config_path = os.path.join(self.config_dir, f"{extension_id}.json")
        
        try:
            # 从数据库获取配置
            config = db.get_extension_config(extension_id)
            
            # 加载模块
            module = load_module_in_sandbox(filepath)
            
            # 保存到已加载扩展字典
            self.loaded_extensions[extension_id] = {
                "module": module,
                "config": config
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
            return True

        except SandboxException as e:
            logger.error(f"扩展 {extension_id} 加载失败(沙箱错误): {str(e)}")
            return False
        except Exception as e:
            logger.error(f"扩展 {extension_id} 加载失败: {str(e)}")
            return False

    def create_query_endpoint(self, module, extension_id):
        """创建扩展的查询端点"""
        async def query_endpoint(request: Request):
            logger.info(f"执行扩展查询: {extension_id}")
            
            try:
                config = self.loaded_extensions[extension_id]["config"].get("config", {})
                
                # 使用表单接收数据，包括文件
                form = await request.form()
                
                # 构建查询参数字典
                query_params = {}
                files = {}
                
                # 统一处理所有表单字段
                for key, value in form.multi_items():
                    try:
                        is_file = value.filename
                    except AttributeError:
                        is_file = False
                    if is_file or isinstance(value, UploadFile):
                        # 处理文件上传
                        file_content = await value.read()
                        await value.seek(0)  # 重置文件指针
                        
                        # 使用扩展程序文件管理器保存文件
                        file_info = await self.extension_file_manager.save_file(
                            extension_id=extension_id,
                            file=value,
                            description=f"Uploaded via query endpoint"
                        )
                        
                        files[key] = file_info
                    else:
                        # 处理普通表单字段
                        query_params[key] = value

                # 执行查询
                result = await execute_query_in_sandbox(
                    module,
                    query_params,
                    config,
                    files=files,
                    file_manager=self.extension_file_manager
                )
                
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
        """移除路由"""
        logger.info(f"移除API路由: {path}")
        for i, route in enumerate(self.app.routes):
            if hasattr(route, "path") and route.path == path:
                self.app.routes.pop(i)
                logger.debug(f"已从路由列表中移除: {path}")
                break

        # 清除FastAPI内部路由缓存
        self.app.openapi_schema = None
        self.app.setup()

    def get_extension_config(self, extension_id: str,db:AsyncSession) -> Dict:
        """获取扩展配置"""
        if db:
            return db.get_extension_config(extension_id)
        else:
            config_path = os.path.join(self.config_dir, f"{extension_id}.json")
            if not os.path.exists(config_path):
                raise HTTPException(status_code=404, detail=f"Extension {extension_id} not found")
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def save_extension_config(self, extension_id: str, config: Dict,db:AsyncSession):
        """保存扩展配置"""
        if db:
            db.save_extension_config(extension_id, config)
        else:
            config_path = os.path.join(self.config_dir, f"{extension_id}.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

    def list_extensions(self,db:AsyncSession) -> List[Dict]:
        """获取所有扩展的列表"""
        if db:
            return db.list_extension_configs()
        else:
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

    def delete_extension(self, extension_id: str,db:AsyncSession):
        """删除扩展"""
        try:
            # 删除扩展配置
            db.delete_extension_config(extension_id)
            
            # 移除路由
            self.remove_route(f"/query/{extension_id}")
            
            # 从加载列表中移除
            self.loaded_extensions.pop(extension_id)
            
            # 清理扩展程序文件
            self.extension_file_manager.clean_files(extension_id)
            
            return True
        except Exception as e:
            return False 