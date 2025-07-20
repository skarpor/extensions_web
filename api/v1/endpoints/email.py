"""
邮件相关API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
import os
import tempfile
from core.logger import get_logger
from core import auth
from db.session import get_db
from core.email import email_service, send_notification_email, test_email_service
from models.user import User as UserModel
logger = get_logger('email')

router = APIRouter()


class EmailRequest(BaseModel):
    """发送邮件请求模型"""
    to_emails: List[EmailStr] = Field(..., description="收件人邮箱列表")
    subject: str = Field(..., min_length=1, max_length=200, description="邮件主题")
    content: str = Field(..., min_length=1, description="邮件内容")
    content_type: str = Field(default="plain", description="内容类型: plain 或 html")
    cc_emails: Optional[List[EmailStr]] = Field(default=None, description="抄送邮箱列表")
    bcc_emails: Optional[List[EmailStr]] = Field(default=None, description="密送邮箱列表")


class NotificationEmailRequest(BaseModel):
    """通知邮件请求模型"""
    to_emails: List[EmailStr] = Field(..., description="收件人邮箱列表")
    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    message: str = Field(..., min_length=1, description="通知消息")


class EmailResponse(BaseModel):
    """邮件发送响应模型"""
    success: bool = Field(..., description="发送是否成功")
    message: str = Field(..., description="响应消息")


class EmailConfigResponse(BaseModel):
    """邮件配置响应模型"""
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from: str
    use_tls: bool
    use_ssl: bool
    is_configured: bool


@router.post("/send", response_model=EmailResponse)
async def send_email(
    email_request: EmailRequest,
    current_user: UserModel = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送邮件
    """
    try:
        # 检查用户权限（可以添加特定的邮件发送权限检查）
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户未激活"
            )
        
        # 发送邮件
        success = await email_service.send_email(
            recipients=email_request.to_emails,
            subject=email_request.subject,
            body=email_request.content,
            html=email_request.content if email_request.content_type == "html" else None,
            cc=email_request.cc_emails,
            bcc=email_request.bcc_emails
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 发送邮件成功: {email_request.subject}")
            return EmailResponse(
                success=True,
                message="邮件发送成功"
            )
        else:
            logger.error(f"用户 {current_user.username} 发送邮件失败: {email_request.subject}")
            return EmailResponse(
                success=False,
                message="邮件发送失败，请检查邮件服务器配置"
            )
    
    except Exception as e:
        logger.error(f"发送邮件异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送邮件失败: {str(e)}"
        )


@router.post("/send-notification", response_model=EmailResponse)
async def send_notification(
    notification_request: NotificationEmailRequest,
    current_user: UserModel = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送通知邮件（带样式的HTML邮件）
    """
    try:
        # 检查用户权限
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户未激活"
            )
        
        # 发送通知邮件
        success = await send_notification_email(
            recipients=notification_request.to_emails,
            title=notification_request.title,
            message=notification_request.message
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 发送通知邮件成功: {notification_request.title}")
            return EmailResponse(
                success=True,
                message="通知邮件发送成功"
            )
        else:
            logger.error(f"用户 {current_user.username} 发送通知邮件失败: {notification_request.title}")
            return EmailResponse(
                success=False,
                message="通知邮件发送失败，请检查邮件服务器配置"
            )
    
    except Exception as e:
        logger.error(f"发送通知邮件异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送通知邮件失败: {str(e)}"
        )


@router.post("/send-with-attachments", response_model=EmailResponse)
async def send_email_with_attachments(
    to_emails: str,
    subject: str,
    content: str,
    content_type: str = "plain",
    files: List[UploadFile] = File(...),
    current_user: UserModel = Depends(auth.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送带附件的邮件
    """
    try:
        # 检查用户权限
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户未激活"
            )
        
        # 解析收件人邮箱
        to_email_list = [email.strip() for email in to_emails.split(',')]
        
        # 保存临时附件文件
        temp_files = []
        try:
            for file in files:
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
                content_data = await file.read()
                temp_file.write(content_data)
                temp_file.close()
                temp_files.append(temp_file.name)
            
            # 发送邮件
            success = await email_service.send_email(
                recipients=to_email_list,
                subject=subject,
                body=content,
                html=content if content_type == "html" else None,
                attachments=temp_files
            )
            
            if success:
                logger.info(f"用户 {current_user.username} 发送带附件邮件成功: {subject}")
                return EmailResponse(
                    success=True,
                    message="带附件邮件发送成功"
                )
            else:
                logger.error(f"用户 {current_user.username} 发送带附件邮件失败: {subject}")
                return EmailResponse(
                    success=False,
                    message="带附件邮件发送失败"
                )
        
        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"清理临时文件失败 {temp_file}: {e}")
    
    except Exception as e:
        logger.error(f"发送带附件邮件异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送带附件邮件失败: {str(e)}"
        )


@router.get("/config", response_model=EmailConfigResponse)
async def get_email_config(
    current_user: UserModel = Depends(auth.get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    获取邮件配置信息（仅超级管理员）
    """
    try:
        config_info = email_service.get_config_info()
        return EmailConfigResponse(
            smtp_host=config_info["smtp_host"],
            smtp_port=config_info["smtp_port"],
            smtp_user=config_info["smtp_user"],
            smtp_from=config_info["smtp_from"],
            use_tls=config_info["use_tls"],
            use_ssl=config_info["use_ssl"],
            is_configured=config_info["is_configured"]
        )
    except Exception as e:
        logger.error(f"获取邮件配置异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取邮件配置失败"
        )


@router.post("/test-connection", response_model=EmailResponse)
async def test_email_connection(
    current_user: UserModel = Depends(auth.get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    测试邮件服务器连接（仅超级管理员）
    """
    try:
        success = await test_email_service()

        if success:
            return EmailResponse(
                success=True,
                message="邮件服务器连接测试成功"
            )
        else:
            return EmailResponse(
                success=False,
                message="邮件服务器连接测试失败，请检查配置"
            )
    
    except Exception as e:
        logger.error(f"测试邮件连接异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试邮件连接失败: {str(e)}"
        )


@router.post("/send-test", response_model=EmailResponse)
async def send_test_email(
    test_email: EmailStr,
    current_user: UserModel = Depends(auth.get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    发送测试邮件（仅超级管理员）
    """
    try:
        success = await send_notification_email(
            recipients=[test_email],
            title="邮件服务测试",
            message=f"""
            <p>这是一封测试邮件。</p>
            <p><strong>发送时间:</strong> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>发送用户:</strong> {current_user.username}</p>
            <p>如果您收到这封邮件，说明邮件服务配置正确。</p>
            """,
            user_name=current_user.username
        )
        
        if success:
            return EmailResponse(
                success=True,
                message=f"测试邮件已发送到 {test_email}"
            )
        else:
            return EmailResponse(
                success=False,
                message="测试邮件发送失败"
            )
    
    except Exception as e:
        logger.error(f"发送测试邮件异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送测试邮件失败: {str(e)}"
        )
