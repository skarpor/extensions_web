"""
文件上传演示扩展

此扩展演示如何在扩展中处理和保存用户上传的文件。
支持多种文件类型上传，并展示如何安全地保存和管理这些文件。
"""
import base64
import json
import datetime
import hashlib
from typing import Dict, Any, List

# 扩展信息
VERSION = "1.0.0"
AUTHOR = "系统管理员"
DESCRIPTION = "文件上传与管理演示扩展，展示如何在扩展中处理多种文件类型的上传"
TAGS = ["演示", "文件上传", "文件管理"]

def get_default_config():
    """
    获取默认配置
    
    Returns:
        默认配置字典
    """
    return {
        "max_file_size_mb": 10,
        "allowed_file_types": [
            "image/jpeg", "image/png", "image/gif", 
            "application/pdf", "text/plain", 
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ],
        "store_file_metadata": True
    }

def get_config_form():
    """
    获取配置表单
    
    Returns:
        配置表单HTML
    """
    return """
    <div class="mb-3">
        <label for="max_file_size_mb" class="form-label">最大文件大小 (MB)</label>
        <input type="number" class="form-control" id="max_file_size_mb" name="max_file_size_mb" 
               value="{{ config.max_file_size_mb }}" min="1" max="50">
        <div class="form-text">允许上传的最大文件大小，单位为MB</div>
    </div>
    
    <div class="mb-3">
        <label for="allowed_file_types" class="form-label">允许的文件类型</label>
        <textarea class="form-control" id="allowed_file_types" name="allowed_file_types" rows="4">{{ config.allowed_file_types | join('\n') }}</textarea>
        <div class="form-text">允许上传的MIME类型，每行一个</div>
    </div>
    
    <div class="mb-3 form-check">
        <input type="checkbox" class="form-check-input" id="store_file_metadata" name="store_file_metadata" 
               {% if config.store_file_metadata %}checked{% endif %}>
        <label class="form-check-label" for="store_file_metadata">保存文件元数据</label>
        <div class="form-text">是否保存上传文件的元数据，如文件哈希、大小等</div>
    </div>
    """

def get_query_form():
    """
    获取查询表单
    
    Returns:
        查询表单HTML
    """
    return """
    <div class="mb-3">
        <label for="main_file" class="form-label">上传主文件</label>
        <input type="file" class="form-control" id="main_file" name="main_file" required>
        <div class="form-text">支持图片、PDF、文本、Excel和Word文档</div>
    </div>
    
    <div class="mb-3">
        <label for="image_file" class="form-label">上传图片（可选）</label>
        <input type="file" class="form-control" id="image_file" name="image_file" accept="image/*">
        <div class="form-text">可选的图片文件</div>
    </div>
    
    <div class="mb-3">
        <label for="file_description" class="form-label">文件描述</label>
        <textarea class="form-control" id="file_description" name="file_description" rows="2"></textarea>
        <div class="form-text">请输入文件的描述信息</div>
    </div>
    
    <div class="mb-3">
        <label for="file_tags" class="form-label">文件标签</label>
        <input type="text" class="form-control" id="file_tags" name="file_tags" placeholder="逗号分隔的标签">
        <div class="form-text">用逗号分隔的文件标签</div>
    </div>
    """

def execute_query(params, config):
    """
    执行查询
    
    Args:
        params: 查询参数
        config: 扩展配置
        
    Returns:
        查询结果
    """
    result = {
        "status": "success",
        "message": "文件处理成功",
        "files": [],
        "metadata": {}
    }
    
    try:
        # 获取文件管理器
        file_manager = params.get("file_manager")
        if not file_manager:
            return {"status": "error", "message": "文件管理器不可用"}
        
        # 获取查询参数
        query = params.get("query", {})
        files = params.get("files", {})
        
        # 获取文件描述和标签
        file_description = query.get("file_description", "")
        file_tags = [tag.strip() for tag in query.get("file_tags", "").split(",") if tag.strip()]
        
        # 解析配置
        max_file_size = config.get("max_file_size_mb", 10) * 1024 * 1024  # 转换为字节
        allowed_types = config.get("allowed_file_types", [])
        store_metadata = config.get("store_file_metadata", True)
        
        # 处理上传的文件
        for file_key, file_data in files.items():
            filename = file_data.get("filename", "未命名文件")
            content_type = file_data.get("content_type", "application/octet-stream")
            content = file_data.get("content", b"")
            
            # 文件大小检查
            file_size = len(content)
            if file_size > max_file_size:
                result["files"].append({
                    "name": filename,
                    "status": "error",
                    "message": f"文件大小超过限制 ({file_size/1024/1024:.2f}MB > {max_file_size/1024/1024}MB)"
                })
                continue
            
            # 文件类型检查
            if allowed_types and content_type not in allowed_types:
                result["files"].append({
                    "name": filename,
                    "status": "error",
                    "message": f"不支持的文件类型: {content_type}"
                })
                continue
            
            # 计算文件元数据
            file_meta = {}
            if store_metadata:
                file_meta = {
                    "size": file_size,
                    "size_readable": f"{file_size/1024:.2f} KB" if file_size < 1024*1024 else f"{file_size/1024/1024:.2f} MB",
                    "content_type": content_type,
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "processed_at": datetime.datetime.now().isoformat(),
                    "tags": file_tags
                }
            
            # 构建完整的文件描述
            full_description = file_description
            if file_tags:
                full_description += f" [标签: {', '.join(file_tags)}]"
            
            # 保存文件
            saved_file = file_manager.save_file(
                file_content=content,
                filename=filename,
                content_type=content_type,
                description=full_description
            )
            
            # 生成缩略图（如果是图片）
            thumbnail_url = None
            if content_type.startswith("image/") and len(content) < 5*1024*1024:  # 小于5MB的图片
                try:
                    # 使用base64编码图片内容作为缩略图
                    base64_image = base64.b64encode(content).decode('utf-8')
                    thumbnail_url = f"data:{content_type};base64,{base64_image}"
                except:
                    pass
            
            # 添加到结果
            result["files"].append({
                "name": filename,
                "status": "success",
                "file_id": saved_file.get("id"),
                "size": file_size,
                "size_readable": f"{file_size/1024:.2f} KB" if file_size < 1024*1024 else f"{file_size/1024/1024:.2f} MB",
                "content_type": content_type,
                "description": full_description,
                "download_url": file_manager.get_file_url(saved_file.get("id")),
                "thumbnail_url": thumbnail_url
            })
        
        # 更新结果元数据
        result["metadata"] = {
            "total_files": len(result["files"]),
            "success_count": sum(1 for f in result["files"] if f.get("status") == "success"),
            "error_count": sum(1 for f in result["files"] if f.get("status") == "error"),
            "total_size": sum(f.get("size", 0) for f in result["files"]),
            "tags": file_tags
        }
        
        # 生成人性化的总大小
        total_size = result["metadata"]["total_size"]
        if total_size < 1024:
            result["metadata"]["total_size_readable"] = f"{total_size} B"
        elif total_size < 1024*1024:
            result["metadata"]["total_size_readable"] = f"{total_size/1024:.2f} KB"
        else:
            result["metadata"]["total_size_readable"] = f"{total_size/1024/1024:.2f} MB"
        
        # 如果没有文件被处理，更新状态
        if not result["files"]:
            result["status"] = "warning"
            result["message"] = "没有处理任何文件"
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"处理文件时出错: {str(e)}"
    
    return result 