import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from config import LOG_DIR

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 获取当前日期作为日志文件名的一部分
current_date = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, f"app_{current_date}.log")

# 创建和配置日志记录器
def setup_logger(name, level=logging.INFO):
    """
    创建并配置一个日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别，默认为INFO
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果已经有处理器，不再添加新的处理器
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建文件处理器 (最大 10MB, 最多保留 5 个备份)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 设置日志文件编码格式
    file_handler.encoding = 'gbk'

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)



    return logger

# 预配置的日志记录器
app_logger = setup_logger("app")
extension_logger = setup_logger("extension")
auth_logger = setup_logger("auth")
# file_logger = setup_logger("file")
# db_logger = setup_logger("db")

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    file_handler.encoding = 'gbk'

    return logger

