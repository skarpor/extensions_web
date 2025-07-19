"""
API路由主入口
"""
from fastapi import APIRouter
from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.users import router as users_router
from api.v1.endpoints.extensions import router as extensions_router
from api.v1.endpoints.files import router as files_router
# from api.v1.endpoints.chats import router as chat_router  # 旧版聊天路由已移除
from api.v1.endpoints.settings import router as settings_router
from api.v1.endpoints.database import router as database_router
# from api.v1.endpoints.ws import router as ws_router  # 已移除，使用chat_websocket
from api.v1.endpoints.dashboard import router as dashboard_router
from api.v1.endpoints.scheduler import router as scheduler_router
from api.v1.endpoints.logger import router as log_router
from api.v1.endpoints.qrfile import router as qrfile_router  # 导入二维码处理路由
from api.v1.endpoints.danmu import router as danmu_router  # 导入弹幕路由
from api.v1.endpoints.help import router as help_router  # 导入帮助路由
from api.v1.endpoints.system import router as system_router  # 导入系统设置路由
from api.v1.endpoints.modern_chat import router as modern_chat_router  # 导入现代化聊天路由
from api.v1.endpoints.global_websocket import router as global_ws_router  # 导入全局WebSocket路由
from api.v1.endpoints.markdown import router as markdown_router  # 导入Markdown编辑器路由
from config import settings
api_router = APIRouter()

# 注册所有子路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户"])
api_router.include_router(extensions_router, prefix="/extensions", tags=["扩展"])
if settings.FILE_ENABLE:
   api_router.include_router(files_router, prefix="/files", tags=["文件管理"])  # 添加文件管理路由
# api_router.include_router(chat_router, prefix="/chat", tags=["聊天"])  # 旧版聊天路由已移除
# api_router.include_router(settings_router, prefix="/settings", tags=["设置"])
if settings.DATABASE_ENABLE:
   api_router.include_router(database_router, prefix="/db", tags=["数据库"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["控制面板"])
# api_router.include_router(ws_router, prefix="/ws", tags=["websocket"])  # 已移除，使用chat_websocket
api_router.include_router(scheduler_router, prefix="/scheduler", tags=["scheduler"])
if settings.LOG_ENABLE:
   api_router.include_router(log_router, prefix="/log", tags=["log"])
if settings.QR_ENABLE:
   api_router.include_router(qrfile_router, prefix="/qrfile", tags=["qrfile"])  # 添加二维码路由
api_router.include_router(danmu_router, prefix="/danmu", tags=["弹幕"])  # 添加二维码路由
api_router.include_router(help_router, prefix="/help", tags=["帮助"])  # 添加帮助路由
api_router.include_router(system_router, prefix="/system", tags=["系统设置"])  # 添加系统设置路由
api_router.include_router(markdown_router, prefix="/markdown", tags=["Markdown编辑器"])  # 添加Markdown编辑器路由
if settings.CHAT_ENABLE:
   api_router.include_router(modern_chat_router, prefix="/modern-chat", tags=["聊天"])  # 添加现代化聊天路由
   api_router.include_router(global_ws_router, prefix="", tags=["全局WebSocket"])  # 添加全局WebSocket路由
