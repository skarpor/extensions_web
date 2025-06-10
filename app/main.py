"""
主应用入口模块
"""
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from fastapi.openapi.docs import get_swagger_ui_html
from config import TEMPLATE_DIR, title, version
from .core.extension_manager import ExtensionManager
from .core.file_manager import FileManager
from .core.database import Database
from .api import extension_routes, auth_routes, file_routes, page_routes, example_routes, scheduler_routes, \
    settings_routes, packages_routes, log_routes, user_routes, ws_routes, chat_routes
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db
# from config import files_dir,db_path
import sys
import json
import uvicorn
from datetime import datetime


# 设置日志记录
from app.core.logger import app_logger as logger


# 配置文件路径
config_dir = os.path.join(os.path.expanduser("~"), ".config", "data_query_system")
os.makedirs(config_dir, exist_ok=True)
config_file = os.path.join(config_dir, "config.dat")

# 定义系统过期时间（如果需要）
EXPIRY_DATE = datetime(2099, 12, 31)

# 加载或创建配置文件
def load_or_create_config():
    try:
        if not os.path.exists(config_file):
            # 创建新配置
            config = {
                "installation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_access": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "access_count": 0
            }
            
            # 保存配置
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info("已创建新配置文件")
        else:
            # 加载现有配置
            with open(config_file, "r") as f:
                config = json.load(f)
            
            # 更新最后访问时间和访问计数
            config["last_access"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config["access_count"] = config.get("access_count", 0) + 1
            
            # 保存更新后的配置
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"已加载配置文件，访问计数: {config['access_count']}")
        
        return config
    
    except Exception as e:
        logger.error(f"加载配置文件时出错: {str(e)}")
        return {
            "installation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_access": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "access_count": 0
        }

# 创建FastAPI应用

def create_app():
    app = FastAPI(title=title, version=version, docs_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应更严格
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]  # 如果需要客户端访问特定响应头
)

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # 设置模板引擎
    templates = Jinja2Templates(directory=TEMPLATE_DIR)

    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行的操作"""
        try:
            # 初始化数据库
            await init_db()

            # 获取根目录
            root_dir = os.path.dirname(os.path.abspath(__file__))

            # 设置路径
            data_dir = os.environ.get("DATA_DIR", "data")
            config_dir = os.path.join(data_dir, "config")
            extensions_dir = os.path.join(data_dir, "extensions")
            files_dir = os.path.abspath("files")
            db_path = os.path.abspath("database.sqlite")

            # 确保目录存在
            os.makedirs(config_dir, exist_ok=True)
            os.makedirs(extensions_dir, exist_ok=True)
            os.makedirs(files_dir, exist_ok=True)

            # 初始化数据库
            db = Database(db_path)
            # from app.db.database import get_db
            app.state.db = db

            # 初始化文件管理器
            file_manager = FileManager(files_dir, db=db)
            app.state.file_manager = file_manager
            file_routes.init_router(file_manager)

            # 初始化扩展管理器
            extension_manager = ExtensionManager(app, config_dir=config_dir, extensions_dir=extensions_dir,
                                                 file_manager=file_manager, db=db)
            extension_routes.init_router(extension_manager)

            # 初始化路由
            auth_routes.init_router(db)
            page_routes.init_router(db)
            user_routes.init_router(db)
            chat_routes.init_router(db, file_manager)
            settings_routes.init_router(db)

            # 加载所有扩展
            extension_manager.load_all_extensions()

            logger.info("应用初始化成功")
        except Exception as e:
            logger.error(f"应用初始化失败: {str(e)}")
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时执行的操作"""
        if hasattr(app.state, 'db'):
            app.state.db.close()
        logger.info("应用已关闭")

    # 包括路由
    app.include_router(extension_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(file_routes.router)
    app.include_router(page_routes.router)
    app.include_router(example_routes.router)
    app.include_router(scheduler_routes.router)
    app.include_router(settings_routes.router)
    app.include_router(packages_routes.router)
#     app.include_router(trans_routes.router)
    app.include_router(log_routes.router)
    app.include_router(user_routes.router)
    app.include_router(ws_routes.router)
    app.include_router(chat_routes.router)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """返回网站图标"""
        return RedirectResponse(url="/static/favicon.ico")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """自定义Swagger UI页面"""
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - API文档",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )

    return app
app = create_app()

