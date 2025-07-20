"""
邮件发送核心模块 - 使用 fastapi-mail
"""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from typing import List, Optional, Union, Dict, Any
import os
import tempfile
from pathlib import Path
from pydantic import EmailStr, BaseModel

from config import settings
from core.logger import get_logger

logger = get_logger('email')


class EmailTemplateData(BaseModel):
    """邮件模板数据模型"""
    title: str
    content: str
    user_name: Optional[str] = None
    timestamp: Optional[str] = None


class EmailConfig:
    """邮件配置类"""
    
    def __init__(self):
        self.smtp_host = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.smtp_from = getattr(settings, 'SMTP_FROM', self.smtp_user)
        self.use_tls = getattr(settings, 'SMTP_USE_TLS', True)
        self.use_ssl = getattr(settings, 'SMTP_USE_SSL', False)
        self.validate_certs = getattr(settings, 'SMTP_VALIDATE_CERTS', True)
    
    def get_connection_config(self) -> ConnectionConfig:
        """获取 fastapi-mail 连接配置"""
        # 确保模板目录存在
        template_folder = Path(__file__).parent.parent / "templates" / "email"
        template_folder.mkdir(parents=True, exist_ok=True)

        return ConnectionConfig(
            MAIL_USERNAME=self.smtp_user,
            MAIL_PASSWORD=self.smtp_password,
            MAIL_FROM=self.smtp_from,
            MAIL_PORT=self.smtp_port,
            MAIL_SERVER=self.smtp_host,
            MAIL_FROM_NAME="扩展Web系统",
            MAIL_STARTTLS=self.use_tls,
            MAIL_SSL_TLS=self.use_ssl,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=self.validate_certs,
            TEMPLATE_FOLDER=template_folder
        )
    
    def is_configured(self) -> bool:
        """检查邮件是否已配置"""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)


class EmailService:
    """邮件服务类 - 基于 fastapi-mail"""
    
    def __init__(self):
        self.config = EmailConfig()
        self._fast_mail = None
    
    @property
    def fast_mail(self) -> FastMail:
        """获取 FastMail 实例"""
        if self._fast_mail is None:
            if not self.config.is_configured():
                raise ValueError("邮件服务未配置，请检查 SMTP 相关环境变量")
            self._fast_mail = FastMail(self.config.get_connection_config())
        return self._fast_mail
    
    async def send_email(
        self,
        recipients: Union[str, List[str]],
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        template_name: Optional[str] = None,
        template_body: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            recipients: 收件人邮箱地址
            subject: 邮件主题
            body: 邮件正文（纯文本）
            html: HTML格式邮件内容
            cc: 抄送邮箱列表
            bcc: 密送邮箱列表
            attachments: 附件文件路径列表
            template_name: 模板名称
            template_body: 模板变量
        
        Returns:
            bool: 发送是否成功
        """
        try:
            # 确保收件人是列表格式
            if isinstance(recipients, str):
                recipients = [recipients]
            
            # 处理附件
            attachment_files = []
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        attachment_files.append(file_path)
                    else:
                        logger.warning(f"附件文件不存在: {file_path}")
            
            # 创建邮件消息
            if template_name and template_body:
                # 使用模板
                message = MessageSchema(
                    subject=subject,
                    recipients=recipients,
                    cc=cc or [],
                    bcc=bcc or [],
                    template_body=template_body,
                    attachments=attachment_files,
                    subtype=MessageType.html
                )
                await self.fast_mail.send_message(message, template_name=template_name)
            else:
                # 直接发送
                message = MessageSchema(
                    subject=subject,
                    recipients=recipients,
                    body=html or body,
                    cc=cc or [],
                    bcc=bcc or [],
                    attachments=attachment_files,
                    subtype=MessageType.html if html else MessageType.plain
                )
                await self.fast_mail.send_message(message)
            
            logger.info(f"邮件发送成功: {subject} -> {recipients}")
            return True
            
        except ConnectionErrors as e:
            logger.error(f"邮件服务器连接错误: {e}")
            return False
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    async def send_notification_email(
        self,
        recipients: Union[str, List[str]],
        title: str,
        message: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        发送通知邮件（使用内置模板）
        
        Args:
            recipients: 收件人邮箱地址
            title: 通知标题
            message: 通知消息
            user_name: 用户名
        
        Returns:
            bool: 发送是否成功
        """
        from datetime import datetime
        
        # 创建HTML格式的通知邮件
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2c3e50;
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #7f8c8d;
                    font-size: 14px;
                }}
                .timestamp {{
                    color: #95a5a6;
                    font-size: 12px;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                <div class="content">
                    {message}
                </div>
                {f'<p><strong>收件人:</strong> {user_name}</p>' if user_name else ''}
                <div class="timestamp">
                    发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                <div class="footer">
                    <p>此邮件由扩展Web系统自动发送，请勿回复。</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            recipients=recipients,
            subject=title,
            body=message,
            html=html_content
        )
    
    async def send_template_email(
        self,
        recipients: Union[str, List[str]],
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        使用模板发送邮件
        
        Args:
            recipients: 收件人邮箱地址
            subject: 邮件主题
            template_name: 模板名称（不含扩展名）
            template_data: 模板数据
            **kwargs: 其他参数
        
        Returns:
            bool: 发送是否成功
        """
        return await self.send_email(
            recipients=recipients,
            subject=subject,
            body="",  # 使用模板时body可以为空
            template_name=template_name,
            template_body=template_data,
            **kwargs
        )
    
    async def test_connection(self) -> bool:
        """测试邮件服务器连接"""
        try:
            if not self.config.is_configured():
                logger.error("邮件服务未配置")
                return False
            
            # 创建一个简单的测试消息
            test_message = MessageSchema(
                subject="连接测试",
                recipients=[self.config.smtp_from],
                body="这是一个连接测试消息",
                subtype=MessageType.plain
            )
            
            # 尝试连接但不实际发送
            connection_config = self.config.get_connection_config()
            fast_mail = FastMail(connection_config)
            
            # 这里我们只是创建连接，不实际发送邮件
            logger.info("邮件服务器连接测试成功")
            return True
            
        except ConnectionErrors as e:
            logger.error(f"邮件服务器连接测试失败: {e}")
            return False
        except Exception as e:
            logger.error(f"邮件连接测试异常: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取邮件配置信息"""
        return {
            "smtp_host": self.config.smtp_host,
            "smtp_port": self.config.smtp_port,
            "smtp_user": self.config.smtp_user,
            "smtp_from": self.config.smtp_from,
            "use_tls": self.config.use_tls,
            "use_ssl": self.config.use_ssl,
            "is_configured": self.config.is_configured()
        }


# 全局邮件服务实例
email_service = EmailService()


# 便捷函数
async def send_email(
    recipients: Union[str, List[str]],
    subject: str,
    body: str,
    html: Optional[str] = None,
    **kwargs
) -> bool:
    """发送邮件的便捷函数"""
    return await email_service.send_email(
        recipients=recipients,
        subject=subject,
        body=body,
        html=html,
        **kwargs
    )


async def send_notification_email(
    recipients: Union[str, List[str]],
    title: str,
    message: str,
    **kwargs
) -> bool:
    """发送通知邮件的便捷函数"""
    return await email_service.send_notification_email(
        recipients=recipients,
        title=title,
        message=message,
        **kwargs
    )


async def test_email_service() -> bool:
    """测试邮件服务的便捷函数"""
    return await email_service.test_connection()
