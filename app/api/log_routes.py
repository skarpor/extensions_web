"""
日志管理路由

"""

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import List, Dict, Optional
import os
from datetime import datetime
import re

from app.core.log_manager import LogManager
from app.core.logger import get_logger
from app.core.auth import get_current_user
from app.models.user import User
from config import LOG_DIR

router = APIRouter(prefix="/api/logs", tags=["logs"])
log_manager = LogManager(LOG_DIR)
logger = get_logger("log_api")

@router.get("/list")
async def list_logs(
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """获取所有日志文件列表"""
    try:
        log_files = log_manager.get_all_logs()
        logs = []
        
        for log_file in log_files:
            file_path = os.path.join(LOG_DIR, log_file)
            if os.path.exists(file_path):
                # 获取文件信息
                file_stats = os.stat(file_path)
                file_size = file_stats.st_size
                modified_time = datetime.fromtimestamp(file_stats.st_mtime)
                
                # 从文件名中提取日期 (假设格式为app_YYYY-MM-DD.log)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', log_file)
                date = date_match.group(1) if date_match else "Unknown"
                
                logs.append({
                    "filename": log_file,
                    "date": date,
                    "size": file_size,
                    "size_formatted": f"{file_size / 1024:.2f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.2f} MB",
                    "modified": modified_time.strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # 按日期排序（最新的在前）
        logs.sort(key=lambda x: x["date"], reverse=True)
        return logs
        
    except Exception as e:
        logger.error(f"获取日志列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取日志列表失败: {str(e)}")

@router.get("/content/{filename}")
async def get_log_content(
    filename: str,
    module: Optional[str] = None,
    level: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """获取指定日志文件的内容，支持按模块、级别、日期范围和关键字筛选"""
    try:
        file_path = os.path.join(LOG_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"日志文件 {filename} 不存在")
        
        # 读取日志
        with open(file_path, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
        
        # 应用筛选
        filtered_lines = []
        for line in log_lines:
            # 检查每个筛选条件
            if module and f" - {module} - " not in line:
                continue
                
            if level and f" - {level.upper()} - " not in line:
                continue
                
            if keyword and keyword not in line:
                continue
                
            # 日期筛选
            try:
                if start_date or end_date:
                    # 提取日志中的时间戳
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        line_date = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                        
                        if start_date:
                            start = datetime.strptime(start_date, "%Y-%m-%d")
                            if line_date < start:
                                continue
                                
                        if end_date:
                            end = datetime.strptime(end_date, "%Y-%m-%d")
                            # 将结束日期设为当天的结束
                            end = end.replace(hour=23, minute=59, second=59)
                            if line_date > end:
                                continue
                    else:
                        # 如果无法提取时间戳，则在筛选模式下跳过此行
                        if start_date or end_date:
                            continue
            except Exception as e:
                logger.warning(f"日期过滤错误: {str(e)}")
                # 出错时不过滤
                pass
                
            filtered_lines.append(line)
        
        # 分页
        total = len(filtered_lines)
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total)
        
        paginated_lines = filtered_lines[start_idx:end_idx]
        
        # 提取所有日志模块和级别，用于前端筛选
        modules = set()
        levels = set()
        
        for line in log_lines:
            parts = line.split(" - ")
            if len(parts) >= 3:
                try:
                    modules.add(parts[1].strip())
                    levels.add(parts[2].strip())
                except:
                    pass
        
        return {
            "filename": filename,
            "total_lines": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "lines": paginated_lines,
            "available_modules": sorted(list(modules)),
            "available_levels": sorted(list(levels))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日志内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取日志内容失败: {str(e)}")

@router.delete("/{filename}")
async def delete_log(
    filename: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """删除指定日志文件（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以删除日志文件")
        
    try:
        file_path = os.path.join(LOG_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"日志文件 {filename} 不存在")
            
        os.remove(file_path)
        logger.info(f"日志文件 {filename} 已被用户 {current_user.username} 删除")
        
        return {"success": True, "message": f"日志文件 {filename} 已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除日志文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除日志文件失败: {str(e)}")

@router.get("/modules")
async def get_log_modules(
    current_user: User = Depends(get_current_user)
) -> List[str]:
    """获取所有日志模块列表"""
    # 从最新的日志文件中提取模块名
    try:
        log_files = log_manager.get_all_logs()
        if not log_files:
            return []
            
        # 获取最新的日志文件
        log_files.sort(reverse=True)
        latest_log = log_files[0]
        
        modules = set()
        with open(os.path.join(LOG_DIR, latest_log), "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split(" - ")
                if len(parts) >= 3:
                    try:
                        modules.add(parts[1].strip())
                    except:
                        pass
        
        return sorted(list(modules))
        
    except Exception as e:
        logger.error(f"获取日志模块列表失败: {str(e)}")
        return []









