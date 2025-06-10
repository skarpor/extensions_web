"""
文件上传处理示例扩展

这个扩展展示了如何处理用户上传的文件，包括文件信息提取、内容分析等功能。
适合用作文件处理和分析的起点。

作者: System Administrator
版本: 1.0.0
日期: 2025-05-15
"""
import json
import base64
import hashlib
import datetime
from typing import Dict, Any, List, Optional

def get_default_config() -> Dict[str, Any]:
    """
    返回扩展的默认配置
    
    Returns:
        包含默认配置的字典
    """
    return {
        "允许的文件类型": "txt,csv,json,xml,pdf,jpg,png,xlsx",
        "最大文件大小(MB)": 10,
        "保存上传文件": False,
        "文件保存路径": "./uploads",
        "启用文件分析": True
    }

def get_config_form() -> str:
    """
    返回配置表单的HTML
    
    Returns:
        HTML表单代码
    """
    return """
    <div class="card mb-4">
        <div class="card-header">
            <h5>文件处理设置</h5>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label for="config.允许的文件类型" class="form-label">允许的文件类型</label>
                <input type="text" class="form-control" id="config.允许的文件类型" name="config.允许的文件类型" 
                       value="{{ config.允许的文件类型 }}">
                <div class="form-text">以逗号分隔的文件扩展名列表</div>
            </div>
            
            <div class="mb-3">
                <label for="config.最大文件大小(MB)" class="form-label">最大文件大小(MB)</label>
                <input type="number" class="form-control" id="config.最大文件大小(MB)" name="config.最大文件大小(MB)" 
                       value="{{ config.最大文件大小(MB) }}" min="1" max="100">
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.保存上传文件" name="config.保存上传文件" 
                       {% if config.保存上传文件 %}checked{% endif %}>
                <label class="form-check-label" for="config.保存上传文件">保存上传文件</label>
            </div>
            
            <div class="mb-3">
                <label for="config.文件保存路径" class="form-label">文件保存路径</label>
                <input type="text" class="form-control" id="config.文件保存路径" name="config.文件保存路径" 
                       value="{{ config.文件保存路径 }}">
                <div class="form-text">上传文件的保存目录</div>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.启用文件分析" name="config.启用文件分析" 
                       {% if config.启用文件分析 %}checked{% endif %}>
                <label class="form-check-label" for="config.启用文件分析">启用文件分析</label>
            </div>
        </div>
    </div>
    """

def get_query_form() -> str:
    """
    返回查询表单的HTML
    
    这个表单允许用户上传文件并设置处理选项
    
    Returns:
        HTML表单代码
    """
    return """
    <div class="card mb-4">
        <div class="card-header">
            <h5>文件上传</h5>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label for="query.file" class="form-label">选择文件</label>
                <input type="file" class="form-control" id="query.file" name="query.file">
                <div class="form-text">选择要上传和分析的文件</div>
            </div>
            
            <div class="mb-3">
                <label for="query.analysis_type" class="form-label">分析类型</label>
                <select class="form-select" id="query.analysis_type" name="query.analysis_type">
                    <option value="basic">基本信息分析</option>
                    <option value="content">内容分析</option>
                    <option value="security">安全检查</option>
                    <option value="full">完整分析</option>
                </select>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="query.extract_text" name="query.extract_text">
                <label class="form-check-label" for="query.extract_text">提取文本内容</label>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="query.calculate_hash" name="query.calculate_hash" checked>
                <label class="form-check-label" for="query.calculate_hash">计算文件哈希值</label>
            </div>
        </div>
    </div>
    """

def execute_query(params: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行文件处理和分析
    
    Args:
        params: 查询参数，包括上传的文件和处理选项
        config: 扩展配置
        
    Returns:
        处理结果字典
    """
    try:
        # 获取查询参数
        query = params.get("query", {})
        analysis_type = query.get("analysis_type", "basic")
        extract_text = query.get("extract_text", False)
        calculate_hash = query.get("calculate_hash", True)
        
        # 获取配置
        allowed_extensions = config.get("允许的文件类型", "").split(",")
        max_size_mb = config.get("最大文件大小(MB)", 10)
        save_files = config.get("保存上传文件", False)
        enable_analysis = config.get("启用文件分析", True)
        
        # 获取上传的文件
        files = params.get("files", {})
        
        # 如果没有上传文件
        if not files:
            return {
                "success": False,
                "error": "未上传任何文件"
            }
        
        results = []
        
        # 处理每个上传的文件
        for file_key, file_data in files.items():
            if not file_data:
                continue
                
            filename = file_data.get("filename", "未知文件")
            content_type = file_data.get("content_type", "unknown")
            content = file_data.get("content", b"")
            
            # 检查文件大小
            file_size = len(content) if content else 0
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > max_size_mb:
                results.append({
                    "filename": filename,
                    "status": "错误",
                    "message": f"文件大小超过限制({file_size_mb:.2f}MB > {max_size_mb}MB)"
                })
                continue
            
            # 检查文件类型
            file_ext = filename.split(".")[-1].lower() if "." in filename else ""
            if allowed_extensions and file_ext not in allowed_extensions:
                results.append({
                    "filename": filename,
                    "status": "错误",
                    "message": f"不支持的文件类型: {file_ext}"
                })
                continue
            
            # 文件分析结果
            file_result = {
                "filename": filename,
                "content_type": content_type,
                "size": file_size,
                "size_formatted": format_size(file_size),
                "extension": file_ext,
                "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "成功"
            }
            
            # 计算哈希值
            if calculate_hash and content:
                file_result["md5"] = hashlib.md5(content).hexdigest()
                file_result["sha1"] = hashlib.sha1(content).hexdigest()
                file_result["sha256"] = hashlib.sha256(content).hexdigest()
            
            # 提取文本内容（仅适用于文本文件）
            if extract_text and content and file_ext in ["txt", "csv", "json", "xml"]:
                try:
                    text_content = content.decode("utf-8")
                    # 限制文本长度，避免返回过大的内容
                    if len(text_content) > 1000:
                        text_content = text_content[:1000] + "... (内容已截断)"
                    file_result["text_content"] = text_content
                except UnicodeDecodeError:
                    file_result["text_content"] = "(无法解码为文本内容)"
            
            # 根据分析类型执行额外处理
            if enable_analysis:
                if analysis_type in ["content", "full"]:
                    # 这里可以添加内容分析逻辑
                    file_result["content_analysis"] = analyze_content(content, file_ext)
                
                if analysis_type in ["security", "full"]:
                    # 这里可以添加安全检查逻辑
                    file_result["security_check"] = security_check(content, file_ext)
            
            results.append(file_result)
        
        return {
            "success": True,
            "analysis_type": analysis_type,
            "config_summary": {
                "allowed_extensions": allowed_extensions,
                "max_size_mb": max_size_mb,
                "save_files": save_files,
                "enable_analysis": enable_analysis
            },
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"文件处理错误: {str(e)}"
        }

def format_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化后的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def analyze_content(content: bytes, file_ext: str) -> Dict[str, Any]:
    """
    分析文件内容
    
    Args:
        content: 文件内容
        file_ext: 文件扩展名
        
    Returns:
        分析结果
    """
    result = {
        "mime_type": guess_mime_type(file_ext),
        "character_count": 0,
        "line_count": 0,
    }
    
    # 文本文件分析
    if file_ext in ["txt", "csv", "json", "xml"]:
        try:
            text = content.decode("utf-8")
            result["character_count"] = len(text)
            result["line_count"] = text.count("\n") + 1
            
            # 添加更多文本分析
            if len(text) > 0:
                result["first_line"] = text.split("\n")[0][:100]
                result["is_binary"] = False
        except:
            result["is_binary"] = True
    else:
        result["is_binary"] = True
    
    return result

def security_check(content: bytes, file_ext: str) -> Dict[str, Any]:
    """
    执行安全检查
    
    Args:
        content: 文件内容
        file_ext: 文件扩展名
        
    Returns:
        安全检查结果
    """
    # 这里是简单的安全检查示例
    # 实际应用中可以添加更复杂的检测逻辑
    
    result = {
        "risk_level": "低",
        "warnings": []
    }
    
    # 检查可执行文件
    if file_ext in ["exe", "dll", "bat", "sh"]:
        result["risk_level"] = "高"
        result["warnings"].append("可执行文件可能包含恶意代码")
    
    # 检查脚本文件
    if file_ext in ["js", "py", "php", "vbs"]:
        result["risk_level"] = "中"
        result["warnings"].append("脚本文件可能包含恶意代码")
    
    # 检查二进制文件中的可疑字符串
    if len(content) > 0:
        suspicious_strings = ["virus", "trojan", "exploit", "hack", "inject"]
        for s in suspicious_strings:
            if s.encode() in content.lower():
                result["risk_level"] = "中" if result["risk_level"] == "低" else result["risk_level"]
                result["warnings"].append(f"发现可疑字符串: {s}")
    
    return result

def guess_mime_type(file_ext: str) -> str:
    """
    根据文件扩展名猜测MIME类型
    
    Args:
        file_ext: 文件扩展名
        
    Returns:
        MIME类型
    """
    mime_types = {
        "txt": "text/plain",
        "html": "text/html",
        "css": "text/css",
        "js": "application/javascript",
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "svg": "image/svg+xml",
        "zip": "application/zip",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    
    return mime_types.get(file_ext.lower(), "application/octet-stream") 