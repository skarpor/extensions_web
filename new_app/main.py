"""
主应用入口模块
"""

import os
from fastapi import FastAPI, Request, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from new_app.core.auth import init_permissions, init_users
from new_app.core.config import settings
from new_app.api.v1.api import api_router
# from new_app.api import (
#     auth,
#     users,
#     files,
#     extensions,
#     settings as settings_router,
#     chat,
#     websocket,
#     database,
# )
from new_app.core.logger import get_logger
from new_app.core.extension_manager import ExtensionManager
from new_app.core.file_manager import FileManager
from new_app.db.session import init_models, get_db, AsyncSessionLocal

logger = get_logger("main")

def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json", docs_url=None,
    )

    # 设置CORS
    # if settings.BACKEND_CORS_ORIGINS:
    # 允许 WebSocket 和跨域请求
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源（生产环境应限制）
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # 设置模板引擎
    app.state.templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

    # 注册路由
    # app.include_router(auth.router, prefix=settings.API_V1_STR)
    # app.include_router(users.router, prefix=settings.API_V1_STR)
    # app.include_router(files.router, prefix=settings.API_V1_STR)
    # app.include_router(extensions.router, prefix=settings.API_V1_STR)
    # app.include_router(settings_router.router, prefix=settings.API_V1_STR)
    # app.include_router(chat.router, prefix=settings.API_V1_STR)
    # app.include_router(websocket.router, prefix=settings.API_V1_STR)
    
    # 注册数据库API路由 - 直接使用前端需要的路径
    # app.include_router(database.router, prefix=settings.API_V1_STR + "/db")
    app.include_router(api_router,prefix="/api")
    # 初始化文件管理器
    file_manager = FileManager()

    # 初始化扩展管理器
    extension_manager = ExtensionManager(
        app=app,
        extensions_dir=settings.EXTENSIONS_DIR,
    )

    @app.on_event("startup")
    async def startup_event():
        """应用启动时的初始化操作"""
        logger.info("应用启动...")
        await init_models() # 创建表
        async with AsyncSessionLocal() as db:
            # 现在db是真正的AsyncSession实例
            await init_users(db)
            await init_permissions(db)
        # 加载所有扩展
        extension_manager.load_all_extensions()
        
        logger.info("应用启动完成")

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时的清理操作"""
        logger.info("应用关闭...")
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """自定义Swagger UI页面"""
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - API文档",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.min.css",
        )

    return app

app = create_app() 

@app.get("/")
async def root():
    """根路由"""
    return {"message": "Welcome to Data Query System API"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": settings.VERSION}

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
    ) 