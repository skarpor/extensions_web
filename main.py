"""
应用程序入口文件
"""
from contextlib import asynccontextmanager

from core.app_scheduler import AppScheduler
from core.aps import stop_scheduler, start_scheduler

"""
主应用入口模块
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.auth import init_permissions, init_users, init_default_roles
from api.v1.api import api_router
from core.logger import get_logger
from core.extension_manager import ExtensionManager
from db.session import init_models, AsyncSessionLocal
from api.v1.endpoints.extensions import init_manager
from core.middleware import ExpiryCheckMiddleware, SecurityHeadersMiddleware, RequestLoggingMiddleware
from core.config_manager import config_manager
# from core.chat_manager import start_cleanup_task  # 已移除
import uvicorn
import asyncio
from config import settings

logger = get_logger("main")


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_version="3.0.0",  # 明确指定OpenAPI版本
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/api/docs",
        lifespan=lifespan
    )

    # 设置CORS
    # 开发环境允许所有来源，避免代理IP变化导致的问题
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源（开发环境）
        allow_credentials=False,  # 当allow_origins=["*"]时，必须设置为False
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 添加自定义中间件
    # app.add_middleware(RequestLoggingMiddleware)
    # app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ExpiryCheckMiddleware)

    # 挂载静态文件
    app.mount("/api/static", StaticFiles(directory="static"), name="static")

    # 设置模板引擎
    # app.state.templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

    # async def get_extension_manager():
    #     async with get_db() as db:
    #         yield ExtensionManager(app,db)
    #
    # extension_manager = get_extension_manager()
    #

    # 注册数据库API路由 - 直接使用前端需要的路径
    # app.include_router(database.router, prefix=settings.API_V1_STR + "/db")
    app.include_router(api_router, prefix="/api")
    # 初始化文件管理器
    # file_manager = FileManager()

    # 初始化扩展管理器
    # 初始化扩展管理器（不依赖db）
    # extension_manager = ExtensionManager(app)
    # app.state.extension_manager = extension_manager



    # @app.on_event("startup")
    # async def startup_event():
    #     """应用启动时的初始化操作"""
    #     logger.info("应用启动...")
    #     await init_models()  # 创建表
    #     async with AsyncSessionLocal() as db:
    #         # 现在db是真正的AsyncSession实例
    #         await init_users(db)
    #         await init_permissions(db)
    #         # extension_manager = ExtensionManager(app)
    #         init_manager(app.state.extension_manager)
    #
    #         # 加载所有扩展
    #         await extension_manager.load_all_extensions(db=db)

        # 添加依赖项
        # def get_extension_manager():
        #     return app.state.extension_manager
        #
        # logger.info("应用启动完成")

    # @app.on_event("shutdown")
    # async def shutdown_event():
    #     """应用关闭时的清理操作"""
    #     logger.info("应用关闭...")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """自定义Swagger UI页面"""
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - API文档",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger/swagger-ui-bundle.min.js",
            swagger_css_url="/static/swagger/swagger-ui.min.css",
        )

    return app

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("应用启动...")
    extension_manager = ExtensionManager(app)
    app.state.extension_manager = extension_manager
    if settings.SCHEDULER_ENABLE:
        await start_scheduler()
        # 创建一个简化的接口供应用使用
        app.state.scheduler =AppScheduler()
        logger.info("应用调度器已初始化")

    await init_models()  # 创建表
    async with AsyncSessionLocal() as db:
        # 现在db是真正的AsyncSession实例
        await init_users(db)
        await init_permissions(db)
        await init_default_roles(db)
        # extension_manager = ExtensionManager(app)
        init_manager(app.state.extension_manager)

        # 加载所有扩展
        await extension_manager.load_all_extensions(db=db)
    logger.info("应用启动完成")

    # 启动聊天室清理任务 (已移除)
    yield
    # Clean up the ML models and release the resources
    if settings.SCHEDULER_ENABLE:
        await stop_scheduler()
        logger.info("应用调度器已关闭")
    logger.info("应用关闭...")



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


if __name__ == "__main__":
    # 删除数据库
    uvicorn.run(
        app,
        host='0.0.0.0',# settings.HOST,
        port=8000,# settings.PORT,
        reload=False,
        workers=1
    )