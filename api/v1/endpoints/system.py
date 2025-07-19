#!/usr/bin/env python3
"""
系统设置API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from api.v1.endpoints.danmu import send_danmu
from core.config_manager import config_manager
from core.auth import manage_system,view_settings,update_settings
from core.logger import get_logger
from db.session import get_db
from models.user import User as DBUser
from schemas.user import User

router = APIRouter()
logger = get_logger("settings")

class SystemSettings(BaseModel):
    """系统设置模型"""
    # 基础配置
    APP_NAME: str = Field(..., description="应用名称")
    DEBUG: bool = Field(False, description="调试模式")
    HOST: str = Field("0.0.0.0", description="监听地址")
    PORT: int = Field(8000, description="监听端口")
    
    # 安全配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="访问令牌过期时间(分钟)")
    ALGORITHM: str = Field("HS256", description="加密算法")
    SECRET_KEY_SET: bool = Field(False, description="密钥是否已设置")
    
    # 数据库配置
    EXT_DB_DIR: str = Field("data/db", description="数据库目录")
    EXT_DB_TYPE: str = Field("sqlite", description="数据库类型")
    EXT_DB_CONFIG: Dict[str, Dict[str, str]] = Field({
        "sqlite": {"db_url": "sqlite+aiosqlite:///./database.sqlite"},
        "postgresql": {"db_url": "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"},
        "mysql": {"db_url": "mysql+aiomysql://root:root@localhost:3306/mysql"},
        "mssql": {"db_url": "mssql+pyodbc://sa:123456@localhost:1433/test?driver=ODBC+Driver+17+for+SQL+Server"}
    }, description="数据库配置")
    
    # 应用配置
    FILE_ENABLE: bool= Field(False, description="是否启用文件管理")
    CHAT_ENABLE: bool= Field(False, description="是否启用聊天")
    QR_ENABLE: bool= Field(False, description="是否启用二维码文件传输")
    SCHEDULER_ENABLE: bool= Field(False, description="是否启用定时器")
    LOG_ENABLE: bool = Field(False, description="是否启用日志功能")
    DATABASE_ENABLE: bool = Field(False, description="是否启用数据库")

    # 文件配置
    UPLOAD_DIR: str = Field("data/uploads", description="上传目录")
    MAX_FILE_SIZE: int = Field(104857600, description="最大文件大小(字节)")
    ALLOWED_EXTENSIONS: list = Field(default_factory=list, description="允许的文件扩展名")

    MARKDOWN_FOLDER_PATH:str = Field("data/docs", description="Markdown文件目录")
    # 扩展配置
    EXTENSIONS_DIR: str = Field("data/extensions", description="扩展目录")
    ALLOW_EXTENSION_UPLOAD: bool = Field(True, description="允许上传扩展")
    
    # 用户配置
    ALLOW_REGISTER: bool = Field(True, description="允许用户注册")
    DEFAULT_USER_ROLE: str = Field("user", description="默认用户角色")
    
    # 日志配置
    LOG_LEVEL: str = Field("INFO", description="日志级别")
    LOG_DIR: str = Field("data/logs", description="日志目录")
    
    # 邮件配置
    SMTP_HOST: str = Field("", description="SMTP服务器地址")
    SMTP_PORT: int = Field(587, description="SMTP端口")
    SMTP_USER: str = Field("", description="SMTP用户名")
    SMTP_PASSWORD: str = Field("", description="SMTP密码")
    SMTP_TLS: bool = Field(True, description="启用TLS")
    
    # 系统配置
    TIMEZONE: str = Field("Asia/Shanghai", description="时区")
    LANGUAGE: str = Field("zh-CN", description="语言")

class SecretKeyUpdate(BaseModel):
    """密钥更新模型"""
    secret_key: str = Field(..., min_length=32, description="新的密钥(至少32位)")

class ExpiryInfo(BaseModel):
    """过期信息模型"""
    expired: bool = Field(..., description="是否已过期")
    expiry_date: Optional[str] = Field(None, description="过期日期")
    initialized_at: Optional[str] = Field(None, description="初始化时间")
    days_left: int = Field(0, description="剩余天数")

@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user:User=Depends(view_settings)
):
    """获取系统设置"""
    try:
        config = config_manager.get_editable_config()
        logger.info(f"用户 {current_user.username} 获取系统设置")
        return SystemSettings(**config)
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统设置失败"
        )

@router.put("/settings", response_model=Dict[str, str])
async def update_system_settings(
    settings: SystemSettings,
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user:User=Depends(update_settings)
):
    """更新系统设置"""
    try:
        # 转换为字典，排除不需要保存的字段
        settings_dict = settings.dict()
        settings_dict.pop("SECRET_KEY_SET", None)  # 移除密钥设置状态字段
        
        # 保存配置
        success = config_manager.save_config(settings_dict)
        
        if success:
            logger.info(f"用户 {current_user.username} 更新系统设置成功")
            return {"message": "系统设置更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存系统设置失败"
            )
            
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新系统设置失败"
        )

@router.put("/settings/secret-key", response_model=Dict[str, str])
async def update_secret_key(
    key_update: SecretKeyUpdate,
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user:User=Depends(update_settings)
):
    """更新系统密钥"""
    try:
        success = config_manager.set_config_value("SECRET_KEY", key_update.secret_key)
        
        if success:
            logger.info(f"用户 {current_user.username} 更新系统密钥成功")
            return {"message": "系统密钥更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存系统密钥失败"
            )
            
    except Exception as e:
        logger.error(f"更新系统密钥失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新系统密钥失败"
        )

@router.get("/expiry-info", response_model=ExpiryInfo)
async def get_expiry_info():
    """获取系统过期信息（无需认证）"""
    try:
        expiry_info = config_manager.get_expiry_info()
        return ExpiryInfo(**expiry_info)
    except Exception as e:
        logger.error(f"获取过期信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取过期信息失败"
        )

@router.get("/config-status", response_model=Dict[str, Any])
async def get_config_status(
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user:User=Depends(view_settings)
):
    """获取配置状态信息"""
    try:
        config = config_manager.load_config()
        expiry_info = config_manager.get_expiry_info()
        
        status_info = {
            "config_file_exists": config_manager.config_file.exists(),
            "config_dir": str(config_manager.config_dir),
            "initialized_at": config.get("INITIALIZED_AT"),
            "updated_at": config.get("UPDATED_AT"),
            "expiry_info": expiry_info,
            "total_config_items": len(config)
        }
        
        logger.info(f"用户 {current_user.username} 获取配置状态")
        return status_info
        
    except Exception as e:
        logger.error(f"获取配置状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置状态失败"
        )

@router.post("/reboot")
async def reboot_system(
    current_user: DBUser = Depends(manage_system),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(update_settings)
):
    """重启业务系统"""
    try:
        logger.info(f"用户 {current_user.username} 请求重启系统")

        import platform
        import os
        import sys
        import signal
        import subprocess
        from pathlib import Path

        system_os = platform.system().lower()
        current_pid = os.getpid()

        logger.info(f"当前操作系统: {system_os}")
        logger.info(f"当前进程PID: {current_pid}")
        logger.info(f"Python可执行文件: {sys.executable}")

        # 检测运行环境
        def detect_runtime_environment():
            """检测当前运行环境"""
            env_info = {
                "is_docker": False,
                "is_executable": False,
                "is_python_script": False,
                "is_service": False,
                "restart_method": "unknown",
                "executable_path": None,
                "working_python": None
            }

            # 检查是否在Docker中运行
            if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
                env_info["is_docker"] = True
                env_info["restart_method"] = "docker"

            # 检查是否是打包的可执行文件（PyInstaller等）
            elif getattr(sys, 'frozen', False):
                env_info["is_executable"] = True
                env_info["restart_method"] = "executable"
                env_info["executable_path"] = sys.executable

            # 检查是否作为Windows服务运行
            elif system_os == "windows" and os.environ.get("RUNNING_AS_SERVICE"):
                env_info["is_service"] = True
                env_info["restart_method"] = "service"

            # 检查是否有systemd服务
            elif system_os == "linux" and os.environ.get("SYSTEMD_SERVICE"):
                env_info["is_service"] = True
                env_info["restart_method"] = "systemd"

            # 默认Python脚本方式
            else:
                env_info["is_python_script"] = True
                env_info["restart_method"] = "python"

                # 查找可用的Python命令
                python_commands = [
                    sys.executable,  # 当前Python解释器
                    "python",
                    "python3",
                    "py",
                    "/usr/bin/python3",
                    "/usr/bin/python",
                    "/usr/local/bin/python3",
                    "/opt/python/bin/python3"
                ]

                for cmd in python_commands:
                    try:
                        result = subprocess.run([cmd, "--version"],
                                              capture_output=True,
                                              timeout=5)
                        if result.returncode == 0:
                            env_info["working_python"] = cmd
                            logger.info(f"找到可用的Python命令: {cmd}")
                            break
                    except:
                        continue

                if not env_info["working_python"]:
                    logger.warning("未找到可用的Python命令")
                    env_info["restart_method"] = "exit_only"

            return env_info

        env_info = detect_runtime_environment()
        logger.info(f"运行环境检测结果: {env_info}")

        # 延迟重启函数
        async def delayed_restart(delay_seconds: int = 2):
            import asyncio
            await asyncio.sleep(delay_seconds)  # 等待响应返回

            try:
                if env_info["restart_method"] == "docker":
                    # Docker环境：退出容器，让Docker重启
                    logger.info("Docker环境：退出进程，依赖容器重启策略")
                    os.kill(current_pid, signal.SIGTERM)

                elif env_info["restart_method"] == "executable":
                    # 可执行文件环境
                    logger.info("可执行文件环境：重启可执行文件")
                    executable_path = env_info["executable_path"]

                    logger.info(f"可执行文件路径: {executable_path}")

                    # 验证可执行文件存在
                    if not Path(executable_path).exists():
                        logger.error(f"可执行文件不存在: {executable_path}")
                        raise Exception(f"可执行文件不存在: {executable_path}")

                    if system_os == "windows":
                        # Windows可执行文件重启
                        restart_bat = f'''@echo off
echo 重启可执行文件...
echo 等待3秒...
timeout /t 3 /nobreak >nul

echo 终止当前进程 PID: {current_pid}
taskkill /PID {current_pid} /F >nul 2>&1

echo 等待2秒...
timeout /t 2 /nobreak >nul

echo 启动可执行文件: {executable_path}
start "" "{executable_path}"

echo 重启完成，删除临时脚本
del "%~f0"
'''
                        restart_file = Path("restart_temp.bat")
                        restart_file.write_text(restart_bat, encoding='utf-8')
                        logger.info(f"生成Windows可执行文件重启脚本: {restart_file.resolve()}")

                        subprocess.Popen([str(restart_file)], shell=True,
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
                    else:
                        # Linux/macOS可执行文件重启
                        restart_sh = f'''#!/bin/bash
echo "重启可执行文件..."
echo "等待3秒..."
sleep 3

echo "终止当前进程 PID: {current_pid}"
kill {current_pid} 2>/dev/null

echo "等待2秒..."
sleep 2

echo "启动可执行文件: {executable_path}"
"{executable_path}" &

echo "重启完成，删除临时脚本"
rm "$0"
'''
                        restart_file = Path("restart_temp.sh")
                        restart_file.write_text(restart_sh, encoding='utf-8')
                        restart_file.chmod(0o755)
                        logger.info(f"生成Unix可执行文件重启脚本: {restart_file.resolve()}")

                        subprocess.Popen(["/bin/bash", str(restart_file)])

                elif env_info["restart_method"] == "service":
                    # 服务环境：退出进程，让服务管理器重启
                    logger.info("服务环境：退出进程，依赖服务管理器重启")
                    os.kill(current_pid, signal.SIGTERM)

                elif env_info["restart_method"] == "python" and env_info["working_python"]:
                    # Python脚本环境
                    logger.info(f"Python脚本环境：使用 {env_info['working_python']} 重启")

                    # 获取main.py的绝对路径
                    main_script = Path(__file__).parent.parent.parent.parent / "main.py"
                    main_script = main_script.resolve()  # 转换为绝对路径
                    working_python = env_info["working_python"]

                    logger.info(f"主脚本路径: {main_script}")
                    logger.info(f"工作目录: {main_script.parent}")
                    logger.info(f"Python命令: {working_python}")

                    # 验证文件存在
                    if not main_script.exists():
                        logger.error(f"主脚本不存在: {main_script}")
                        raise Exception(f"主脚本不存在: {main_script}")

                    if system_os == "windows":
                        # Windows Python重启
                        restart_bat = f'''@echo off
echo 重启脚本开始执行...
echo 等待3秒...
timeout /t 3 /nobreak >nul

echo 终止当前进程 PID: {current_pid}
taskkill /PID {current_pid} /F >nul 2>&1

echo 等待2秒...
timeout /t 2 /nobreak >nul

echo 切换到工作目录: {main_script.parent}
cd /d "{main_script.parent}"

echo 启动新进程...
echo Python: {working_python}
echo 脚本: {main_script}
"{working_python}" "{main_script}"

echo 重启完成，删除临时脚本
del "%~f0"
'''
                        restart_file = Path("restart_temp.bat")
                        restart_file.write_text(restart_bat, encoding='utf-8')
                        logger.info(f"生成Windows重启脚本: {restart_file.resolve()}")

                        # 启动重启脚本
                        subprocess.Popen([str(restart_file)], shell=True,
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
                    else:
                        # Linux/macOS Python重启
                        restart_sh = f'''#!/bin/bash
echo "重启脚本开始执行..."
echo "等待3秒..."
sleep 3

echo "终止当前进程 PID: {current_pid}"
kill {current_pid} 2>/dev/null

echo "等待2秒..."
sleep 2

echo "切换到工作目录: {main_script.parent}"
cd "{main_script.parent}"

echo "启动新进程..."
echo "Python: {working_python}"
echo "脚本: {main_script}"
"{working_python}" "{main_script}" &

echo "重启完成，删除临时脚本"
rm "$0"
'''
                        restart_file = Path("restart_temp.sh")
                        restart_file.write_text(restart_sh, encoding='utf-8')
                        restart_file.chmod(0o755)
                        logger.info(f"生成Unix重启脚本: {restart_file.resolve()}")

                        # 启动重启脚本
                        subprocess.Popen(["/bin/bash", str(restart_file)])

                else:
                    # 无法重启，只能退出进程
                    logger.warning("无法确定重启方式，只能退出当前进程")
                    logger.warning("请手动重启应用程序")
                    os.kill(current_pid, signal.SIGTERM)

            except Exception as restart_error:
                logger.error(f"重启过程中发生错误: {restart_error}")
                # 最后的手段：强制退出
                try:
                    os.kill(current_pid, signal.SIGKILL)
                except:
                    pass

        # 设置重启延迟时间
        restart_delay = 2  # 2秒延迟

        # 在后台执行延迟重启
        import asyncio
        asyncio.create_task(delayed_restart(restart_delay))
        from api.v1.endpoints.danmu import send_data
        danmu_data = {
            "id": "66666666666666",
            "text": f"系统重启请求已接受，将在{restart_delay}秒后执行重启。请及时保存数据",
            "color": "red",
            "timestamp": int(asyncio.get_event_loop().time() * 1000)
        }
        await send_data(danmu_data)
        logger.info(f"系统重启请求已接受，将在{restart_delay}秒后执行重启")
        return {
            "message": f"系统重启请求已接受，系统将在{restart_delay}秒后重启",
            "status": "accepted",
            "restart_delay": restart_delay,
            "environment": env_info,
            "system_os": system_os,
            "current_pid": current_pid,
            "restart_method": env_info["restart_method"],
            "instructions": {
                "docker": "容器将退出，依赖Docker重启策略重新启动",
                "executable": "将重启可执行文件",
                "service": "将退出进程，依赖服务管理器重启",
                "python": f"将使用 {env_info.get('working_python', 'python')} 重启应用",
                "exit_only": "无法自动重启，将退出进程，请手动重启应用"
            }.get(env_info["restart_method"], "未知重启方式")
        }

    except Exception as e:
        logger.error(f"重启系统失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重启系统失败: {str(e)}"
        )

