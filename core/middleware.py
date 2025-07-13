#!/usr/bin/env python3
"""
中间件 - HTTP拦截器
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time

from core.config_manager import config_manager
from core.logger import get_logger

logger = get_logger("middleware")

class ExpiryCheckMiddleware(BaseHTTPMiddleware):
    """过期检查中间件"""
    
    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        # 排除的路径（这些路径不检查过期）
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/system/expiry-info",
            "/api/system/settings",  # 允许访问设置页面来续期
            "/static",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()
        
        # 检查是否为排除路径
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            response = await call_next(request)
            return response
        
        # 检查系统是否过期
        try:
            if config_manager.is_expired():
                expiry_info = config_manager.get_expiry_info()
                logger.warning(f"系统已过期，拒绝访问: {path}")
                
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "SYSTEM_EXPIRED",
                        "message": "系统使用期限已过期，请联系管理员",
                        "expiry_info": expiry_info
                    }
                )
        except Exception as e:
            logger.error(f"检查过期状态失败: {e}")
            # 如果检查失败，允许继续访问，避免系统完全不可用
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加处理时间头
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 如果是HTTPS，添加HSTS头
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # start_time = time.time()
        
        # 记录请求开始
        # client_ip = request.client.host if request.client else "unknown"
        # logger.info(f"请求开始: {request.method} {request.url.path} - IP: {client_ip}")
        
        # 处理请求
        response = await call_next(request)
        
        # 记录请求结束
        # process_time = time.time() - start_time
        # logger.info(
        #     f"请求完成: {request.method} {request.url.path} - "
        #     f"状态: {response.status_code} - 耗时: {process_time:.3f}s"
        # )

        return response
