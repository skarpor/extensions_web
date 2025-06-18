import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler  # 关键修改点

from config import LOG_DIR

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name, level=logging.INFO):
    """
    创建并配置一个日志记录器（支持按天轮转日志文件）
    
    Args:
        name: 日志记录器名称
        level: 日志级别，默认为INFO
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 日志文件名格式（不带日期，由TimedRotatingFileHandler自动处理）
    log_file = os.path.join(LOG_DIR, f"app.log")  # 基础文件名

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 文件处理器（按天轮转，午夜切换，保留7天日志）
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",  # 每天午夜轮转
        interval=1,       # 每天一个文件
        backupCount=30,    # 保留30天日志
        encoding="gbk"    # 编码
    )
    file_handler.setLevel(level)

    # 统一格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# 预配置日志记录器
app_logger = setup_logger("app")
# extension_logger = setup_logger("extension")
auth_logger = setup_logger("auth")

# file_logger = setup_logger("file")
# db_logger = setup_logger("db")

def get_logger(name,level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    log_file = os.path.join(LOG_DIR, f"{name}.log")  # 基础文件名
    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=30, encoding="gbk"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    file_handler.encoding = 'gbk'

    return logger

