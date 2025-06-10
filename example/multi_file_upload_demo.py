"""
多文件上传示例扩展

本扩展展示了如何处理多种不同类型的文件上传并进行处理。
可以用作开发者学习的参考。

作者: System Administrator
版本: 1.0.0
日期: 2025-05-20
"""
from typing import Dict, Any
import hashlib
import datetime

def get_default_config() -> Dict[str, Any]:
    """返回扩展的默认配置"""
    return {
        "允许的图片类型": "jpg,jpeg,png,gif",
        "允许的文档类型": "txt,pdf,doc,docx",
        "最大文件大小(MB)": 5
    }

def get_config_form() -> str:
    """返回配置表单的HTML"""
    return """
    <div class="card mb-4">
        <div class="card-header">
            <h5>文件处理设置</h5>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label for="config.允许的图片类型" class="form-label">允许的图片类型</label>
                <input type="text" class="form-control" id="config.允许的图片类型" 
                       name="config.允许的图片类型" value="{{ config.允许的图片类型 }}">
            </div>
            <div class="mb-3">
                <label for="config.允许的文档类型" class="form-label">允许的文档类型</label>
                <input type="text" class="form-control" id="config.允许的文档类型" 
                       name="config.允许的文档类型" value="{{ config.允许的文档类型 }}">
            </div>
            <div class="mb-3">
                <label for="config.最大文件大小(MB)" class="form-label">最大文件大小(MB)</label>
                <input type="number" class="form-control" id="config.最大文件大小(MB)" 
                       name="config.最大文件大小(MB)" value="{{ config.最大文件大小(MB) }}" min="1" max="50">
            </div>
        </div>
    </div>
    """

def get_query_form() -> str:
    """返回查询表单的HTML"""
    return """
    <div class="card mb-4">
        <div class="card-header">
            <h5>多文件上传</h5>
            <p class="text-muted">本示例展示如何处理多种类型的文件上传</p>
        </div>
        <div class="card-body">
            <div class="row">
                <!-- 图片上传 -->
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h6 class="mb-0">图片文件</h6>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label for="image_file" class="form-label">上传图片</label>
                                <input type="file" class="form-control" id="image_file" 
                                       name="image_file" accept="image/*">
                                <div class="form-text">支持JPG、PNG、GIF等图片格式</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 文档上传 -->
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h6 class="mb-0">文档文件</h6>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label for="document_file" class="form-label">上传文档</label>
                                <input type="file" class="form-control" id="document_file" 
                                       name="document_file" accept=".txt,.pdf,.doc,.docx">
                                <div class="form-text">支持TXT、PDF、DOC等文档格式</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 处理选项 -->
            <div class="mt-3">
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <h6 class="mb-0">处理选项</h6>
                    </div>
                    <div class="card-body">
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="calculate_hash" 
                                   name="calculate_hash" checked>
                            <label class="form-check-label" for="calculate_hash">计算文件哈希值</label>
                        </div>
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="extract_info" 
                                   name="extract_info" checked>
                            <label class="form-check-label" for="extract_info">提取文件信息</label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

def execute_query(params: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """执行查询逻辑"""
    try:
        # 获取查询参数
        query = params.get("query", {})
        calculate_hash = query.get("calculate_hash", True)
        extract_info = query.get("extract_info", True)
        
        # 获取配置
        allowed_image_types = config.get("允许的图片类型", "").lower().split(",")
        allowed_doc_types = config.get("允许的文档类型", "").lower().split(",")
        max_size_mb = config.get("最大文件大小(MB)", 5)
        
        # 获取上传的文件
        files = params.get("files", {})
        
        # 如果没有上传文件
        if not files:
            return {
                "success": False,
                "error": "未上传任何文件"
            }
        
        results = {
            "image_results": [],
            "document_results": [],
            "summary": {
                "total_files": len(files),
                "total_size": 0,
                "processed_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
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
            results["summary"]["total_size"] += file_size
            
            if file_size_mb > max_size_mb:
                error_result = {
                    "filename": filename,
                    "status": "错误",
                    "message": f"文件大小超过限制({file_size_mb:.2f}MB > {max_size_mb}MB)"
                }
                
                if "image_file" in file_key:
                    results["image_results"].append(error_result)
                elif "document_file" in file_key:
                    results["document_results"].append(error_result)
                continue
            
            # 检查文件类型
            file_ext = filename.split(".")[-1].lower() if "." in filename else ""
            
            # 基本文件信息
            file_info = {
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
                file_info["md5"] = hashlib.md5(content).hexdigest()
                file_info["sha1"] = hashlib.sha1(content).hexdigest()
            
            # 图片文件处理
            if "image_file" in file_key:
                if file_ext in allowed_image_types:
                    if extract_info:
                        file_info["image_info"] = {
                            "file_type": "图像文件",
                            "mime_type": guess_mime_type(file_ext)
                        }
                    results["image_results"].append(file_info)
                else:
                    file_info["status"] = "错误"
                    file_info["message"] = f"不支持的图片格式: {file_ext}"
                    results["image_results"].append(file_info)
            
            # 文档文件处理
            elif "document_file" in file_key:
                if file_ext in allowed_doc_types:
                    if extract_info:
                        file_info["document_info"] = {
                            "file_type": "文档文件",
                            "mime_type": guess_mime_type(file_ext)
                        }
                        
                        # 文本文件处理
                        if file_ext == "txt":
                            try:
                                text = content.decode("utf-8")
                                preview_length = min(len(text), 200)
                                file_info["document_info"]["preview"] = text[:preview_length] + ("..." if len(text) > preview_length else "")
                                file_info["document_info"]["character_count"] = len(text)
                                file_info["document_info"]["line_count"] = text.count("\n") + 1
                            except UnicodeDecodeError:
                                file_info["document_info"]["preview"] = "无法解码文本内容"
                    
                    results["document_results"].append(file_info)
                else:
                    file_info["status"] = "错误"
                    file_info["message"] = f"不支持的文档格式: {file_ext}"
                    results["document_results"].append(file_info)
        
        # 格式化汇总信息
        results["summary"]["total_size_formatted"] = format_size(results["summary"]["total_size"])
        results["summary"]["image_files_count"] = len(results["image_results"])
        results["summary"]["document_files_count"] = len(results["document_results"])
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"文件处理错误: {str(e)}"
        }

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def guess_mime_type(file_ext: str) -> str:
    """根据文件扩展名猜测MIME类型"""
    mime_types = {
        "txt": "text/plain",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif"
    }
    return mime_types.get(file_ext.lower(), "application/octet-stream") 