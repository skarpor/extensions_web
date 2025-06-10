# config.py
import os
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import passlib.handlers.bcrypt  # 显式导入，确保 PyInstaller 能检测到

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
# 从环境变量获取密钥，如果没有则使用默认值（不推荐用于生产环境）
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "123")
# if JWT_SECRET_KEY == "SECRET_KEY":
#     logger.warning("使用默认JWT密钥，这在生产环境中不安全。请设置环境变量JWT_SECRET_KEY")

# 设置令牌过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "600"))

# 示例文件目录
EXAMPLE_DIR = "example"
TEMPLATE_DIR = "templates"
token_name="access_token"
LOG_DIR = "logs"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
title="数据查询服务"
version="1.0.0"
root_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.environ.get("EXT_DATA_DIR", "data")
db_path = os.path.join(root_dir, "database.sqlite")
files_dir = os.path.join(root_dir, "files")

class Settings:
    DATABASE_PATH=db_path
    DEBUG=True
settings=Settings()
