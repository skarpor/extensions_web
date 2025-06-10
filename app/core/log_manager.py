"""
日志管理
负责日志的读取、写入、删除、清理等操作
"""

import os
import datetime


class LogManager:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir

    def get_logs(self, day: str):
        """获取指定日期的日志文件"""
        log_file = os.path.join(self.log_dir, day)
        if os.path.exists(log_file):
            return log_file
        return None

    def get_all_logs(self):
        """获取所有日志文件"""
        return [f for f in os.listdir(self.log_dir) if f.endswith(".log")]

    def get_log_content(self, day: str):
        """获取指定日期的日志文件内容"""
        log_file = self.get_logs(day)
        if log_file:
            with open(log_file, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def delete_log(self, day: str):
        """删除指定日期的日志文件"""
        log_file = self.get_logs(day)
        if log_file:
            os.remove(log_file)
            return True
        return False

    def clear_logs(self):
        """清空所有日志文件"""
        for log_file in self.get_all_logs():
            self.delete_log(log_file)

    def get_log_file_list(self):
        """获取日志文件列表"""
        return self.get_all_logs()
    
    def get_log_file_content(self, day: str):
        """获取指定日期的日志文件内容"""
        return self.get_log_content(day)
    
    def delete_log_file(self, day: str):
        """删除指定日期的日志文件"""
        return self.delete_log(day)
    # 获取日志中指定关键字的内容
    def get_log_content_by_keyword(self, keyword: str):
        """获取日志中指定关键字的内容"""
        for log_file in self.get_all_logs():
            content = self.get_log_content(log_file)
            if content:
                if keyword in content:
                    return content
        return None








