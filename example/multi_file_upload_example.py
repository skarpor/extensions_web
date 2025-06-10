"""
多文件上传处理示例扩展

本扩展展示了如何在同一个表单中处理多种不同类型的文件上传，
并对每种文件类型进行专门的处理。这是一个学习示例，
可以作为开发者学习文件上传处理的参考。

作者: System Administrator
版本: 1.0.0
日期: 2025-05-20
"""
import json
import base64
import hashlib
import datetime
from typing import Dict, Any, List, Optional
import io

def get_default_config() -> Dict[str, Any]:
    """
    返回扩展的默认配置
    
    Returns:
        包含默认配置的字典
    """
    return {
        "图片文件类型": "jpg,jpeg,png,gif",
        "文本文件类型": "txt,csv,json,xml,md",
        "Excel文件类型": "xls,xlsx",
        "最大文件大小(MB)": 10,
        "启用图像处理": True,
        "启用文本分析": True,
        "启用Excel分析": True,
        "保存处理后的文件": False,
        "文件保存路径": "./processed_files",
    }

def get_config_form() -> str:
    """
    返回配置表单的HTML
    
    Returns:
        HTML表单代码
    """
    return """
    <div class="card mb-4">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">文件类型设置</h5>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label for="config.图片文件类型" class="form-label">图片文件类型</label>
                <input type="text" class="form-control" id="config.图片文件类型" name="config.图片文件类型" 
                       value="{{ config.图片文件类型 }}">
                <div class="form-text">以逗号分隔的图片文件扩展名列表</div>
            </div>
            
            <div class="mb-3">
                <label for="config.文本文件类型" class="form-label">文本文件类型</label>
                <input type="text" class="form-control" id="config.文本文件类型" name="config.文本文件类型" 
                       value="{{ config.文本文件类型 }}">
                <div class="form-text">以逗号分隔的文本文件扩展名列表</div>
            </div>
            
            <div class="mb-3">
                <label for="config.Excel文件类型" class="form-label">Excel文件类型</label>
                <input type="text" class="form-control" id="config.Excel文件类型" name="config.Excel文件类型" 
                       value="{{ config.Excel文件类型 }}">
                <div class="form-text">以逗号分隔的Excel文件扩展名列表</div>
            </div>
            
            <div class="mb-3">
                <label for="config.最大文件大小(MB)" class="form-label">最大文件大小(MB)</label>
                <input type="number" class="form-control" id="config.最大文件大小(MB)" name="config.最大文件大小(MB)" 
                       value="{{ config.最大文件大小(MB) }}" min="1" max="100">
            </div>
        </div>
    </div>
    
    <div class="card mb-4">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">处理选项</h5>
        </div>
        <div class="card-body">
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.启用图像处理" name="config.启用图像处理" 
                       {% if config.启用图像处理 %}checked{% endif %}>
                <label class="form-check-label" for="config.启用图像处理">启用图像处理</label>
                <div class="form-text">启用后将处理图像文件的基本信息</div>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.启用文本分析" name="config.启用文本分析" 
                       {% if config.启用文本分析 %}checked{% endif %}>
                <label class="form-check-label" for="config.启用文本分析">启用文本分析</label>
                <div class="form-text">启用后将分析文本文件的内容</div>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.启用Excel分析" name="config.启用Excel分析" 
                       {% if config.启用Excel分析 %}checked{% endif %}>
                <label class="form-check-label" for="config.启用Excel分析">启用Excel分析</label>
                <div class="form-text">启用后将分析Excel文件的结构</div>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.保存处理后的文件" name="config.保存处理后的文件" 
                       {% if config.保存处理后的文件 %}checked{% endif %}>
                <label class="form-check-label" for="config.保存处理后的文件">保存处理后的文件</label>
                <div class="form-text">启用后将保存处理后的文件（演示用，实际沙箱环境中可能无法保存）</div>
            </div>
            
            <div class="mb-3">
                <label for="config.文件保存路径" class="form-label">文件保存路径</label>
                <input type="text" class="form-control" id="config.文件保存路径" name="config.文件保存路径" 
                       value="{{ config.文件保存路径 }}">
                <div class="form-text">处理后文件的保存目录</div>
            </div>
        </div>
    </div>
    """

def get_query_form() -> str:
    """
    返回查询表单的HTML
    
    包含多种类型的文件上传控件和处理选项
    
    Returns:
        HTML表单代码
    """
    return """
    <div class="card mb-4">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">文件上传</h5>
            <p class="text-white-50 mb-0">本示例展示如何处理多种类型的文件上传</p>
        </div>
        <div class="card-body">
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                这是一个学习示例，展示如何同时处理多种类型的文件上传。
                您可以选择上传图片、文本文件或Excel文件，系统将对每种文件类型进行相应的处理。
            </div>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-header bg-success text-white">
                            <h6 class="mb-0">图片文件</h6>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label for="query.image_file" class="form-label">上传图片</label>
                                <input type="file" class="form-control" id="query.image_file" name="query.image_file" accept="image/*">
                                <div class="form-text">支持JPG、PNG、GIF等图片格式</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="query.image_process_type" class="form-label">处理类型</label>
                                <select class="form-select" id="query.image_process_type" name="query.image_process_type">
                                    <option value="info">基本信息</option>
                                    <option value="thumbnail">生成缩略图</option>
                                    <option value="metadata">提取元数据</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0">文本文件</h6>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label for="query.text_file" class="form-label">上传文本</label>
                                <input type="file" class="form-control" id="query.text_file" name="query.text_file" accept=".txt,.csv,.json,.xml,.md">
                                <div class="form-text">支持TXT、CSV、JSON、XML等文本格式</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="query.text_process_type" class="form-label">分析类型</label>
                                <select class="form-select" id="query.text_process_type" name="query.text_process_type">
                                    <option value="stats">统计信息</option>
                                    <option value="keywords">关键词提取</option>
                                    <option value="summary">内容摘要</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-header bg-warning text-dark">
                            <h6 class="mb-0">Excel文件</h6>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label for="query.excel_file" class="form-label">上传Excel</label>
                                <input type="file" class="form-control" id="query.excel_file" name="query.excel_file" accept=".xls,.xlsx">
                                <div class="form-text">支持XLS、XLSX格式</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="query.excel_process_type" class="form-label">分析类型</label>
                                <select class="form-select" id="query.excel_process_type" name="query.excel_process_type">
                                    <option value="structure">结构分析</option>
                                    <option value="preview">数据预览</option>
                                    <option value="stats">数据统计</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <h6 class="mb-0">全局处理选项</h6>
                    </div>
                    <div class="card-body">
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="query.calculate_hash" name="query.calculate_hash" checked>
                            <label class="form-check-label" for="query.calculate_hash">计算文件哈希值</label>
                        </div>
                        
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="query.extract_metadata" name="query.extract_metadata">
                            <label class="form-check-label" for="query.extract_metadata">提取文件元数据</label>
                        </div>
                        
                        <div class="mb-3">
                            <label for="query.output_format" class="form-label">输出格式</label>
                            <select class="form-select" id="query.output_format" name="query.output_format">
                                <option value="simple">简单格式</option>
                                <option value="detailed">详细格式</option>
                                <option value="visual">可视化格式</option>
                            </select>
                        </div>
                    </div>
                </div>
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
        calculate_hash = query.get("calculate_hash", True)
        extract_metadata = query.get("extract_metadata", False)
        output_format = query.get("output_format", "simple")
        
        # 图片处理选项
        image_process_type = query.get("image_process_type", "info")
        
        # 文本处理选项
        text_process_type = query.get("text_process_type", "stats")
        
        # Excel处理选项
        excel_process_type = query.get("excel_process_type", "structure")
        
        # 获取配置
        image_extensions = config.get("图片文件类型", "").lower().split(",")
        text_extensions = config.get("文本文件类型", "").lower().split(",")
        excel_extensions = config.get("Excel文件类型", "").lower().split(",")
        max_size_mb = config.get("最大文件大小(MB)", 10)
        enable_image_processing = config.get("启用图像处理", True)
        enable_text_analysis = config.get("启用文本分析", True)
        enable_excel_analysis = config.get("启用Excel分析", True)
        
        # 获取上传的文件
        files = params.get("files", {})
        
        # 如果没有上传文件
        if not files:
            return {
                "success": False,
                "error": "未上传任何文件",
                "help": "请选择至少一个文件上传"
            }
        
        results = {
            "image_results": [],
            "text_results": [],
            "excel_results": [],
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
                
                # 根据文件类型添加到相应的结果列表
                if "image" in file_key:
                    results["image_results"].append(error_result)
                elif "text" in file_key:
                    results["text_results"].append(error_result)
                elif "excel" in file_key:
                    results["excel_results"].append(error_result)
                    
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
                file_info["sha256"] = hashlib.sha256(content).hexdigest()
            
            # 处理图片文件
            if "image_file" in file_key and enable_image_processing:
                if file_ext in image_extensions:
                    image_result = process_image(content, file_ext, image_process_type)
                    file_info.update(image_result)
                    results["image_results"].append(file_info)
                else:
                    file_info["status"] = "错误"
                    file_info["message"] = f"不支持的图片格式: {file_ext}"
                    results["image_results"].append(file_info)
            
            # 处理文本文件
            elif "text_file" in file_key and enable_text_analysis:
                if file_ext in text_extensions:
                    text_result = process_text(content, file_ext, text_process_type)
                    file_info.update(text_result)
                    results["text_results"].append(file_info)
                else:
                    file_info["status"] = "错误"
                    file_info["message"] = f"不支持的文本格式: {file_ext}"
                    results["text_results"].append(file_info)
            
            # 处理Excel文件
            elif "excel_file" in file_key and enable_excel_analysis:
                if file_ext in excel_extensions:
                    excel_result = process_excel(content, file_ext, excel_process_type)
                    file_info.update(excel_result)
                    results["excel_results"].append(file_info)
                else:
                    file_info["status"] = "错误"
                    file_info["message"] = f"不支持的Excel格式: {file_ext}"
                    results["excel_results"].append(file_info)
        
        # 格式化汇总信息
        results["summary"]["total_size_formatted"] = format_size(results["summary"]["total_size"])
        results["summary"]["image_files_count"] = len(results["image_results"])
        results["summary"]["text_files_count"] = len(results["text_results"])
        results["summary"]["excel_files_count"] = len(results["excel_results"])
        
        # 根据输出格式调整结果
        if output_format == "simple":
            # 简化输出，移除一些详细信息
            for result_list in [results["image_results"], results["text_results"], results["excel_results"]]:
                for item in result_list:
                    for key in list(item.keys()):
                        if key in ["md5", "sha1", "content_preview", "detailed_analysis"]:
                            item.pop(key, None)
        
        elif output_format == "visual":
            # 添加可视化标记
            results["visualization_ready"] = True
            results["visualization_type"] = "multi_file_analysis"
        
        return {
            "success": True,
            "output_format": output_format,
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

def process_image(content: bytes, file_ext: str, process_type: str) -> Dict[str, Any]:
    """
    处理图像文件
    
    Args:
        content: 文件内容
        file_ext: 文件扩展名
        process_type: 处理类型
        
    Returns:
        处理结果
    """
    result = {
        "image_info": {
            "mime_type": guess_mime_type(file_ext),
            "file_type": "图像文件",
            "process_type": process_type,
        }
    }
    
    # 模拟图像处理，实际应用中可以使用PIL等库进行处理
    if process_type == "info":
        # 返回基本信息
        result["image_info"]["width"] = "模拟值：1920 px"
        result["image_info"]["height"] = "模拟值：1080 px"
        result["image_info"]["color_mode"] = "模拟值：RGB"
        
    elif process_type == "thumbnail":
        # 模拟缩略图生成
        result["image_info"]["thumbnail_created"] = True
        result["image_info"]["thumbnail_size"] = "模拟值：200x112 px"
        result["thumbnail_base64"] = "模拟的Base64编码缩略图数据"
        
    elif process_type == "metadata":
        # 模拟元数据提取
        result["image_info"]["metadata"] = {
            "camera": "模拟值：Canon EOS R5",
            "exposure": "模拟值：1/125 sec",
            "aperture": "模拟值：f/2.8",
            "iso": "模拟值：100",
            "date_taken": "模拟值：2025-01-15 14:30:45"
        }
    
    return result

def process_text(content: bytes, file_ext: str, process_type: str) -> Dict[str, Any]:
    """
    处理文本文件
    
    Args:
        content: 文件内容
        file_ext: 文件扩展名
        process_type: 处理类型
        
    Returns:
        处理结果
    """
    result = {
        "text_info": {
            "mime_type": guess_mime_type(file_ext),
            "file_type": "文本文件",
            "process_type": process_type
        }
    }
    
    try:
        # 尝试将内容解码为文本
        text = content.decode("utf-8")
        
        # 文本统计信息
        char_count = len(text)
        line_count = text.count("\n") + 1
        word_count = len(text.split())
        
        result["text_info"]["character_count"] = char_count
        result["text_info"]["line_count"] = line_count
        result["text_info"]["word_count"] = word_count
        
        # 内容预览
        preview_length = min(len(text), 1000)
        result["content_preview"] = text[:preview_length] + ("..." if len(text) > preview_length else "")
        
        if process_type == "stats":
            # 添加更多统计信息
            result["text_info"]["avg_chars_per_line"] = char_count / max(line_count, 1)
            result["text_info"]["avg_words_per_line"] = word_count / max(line_count, 1)
            
        elif process_type == "keywords":
            # 模拟关键词提取
            result["text_info"]["keywords"] = ["模拟关键词1", "模拟关键词2", "模拟关键词3"]
            result["text_info"]["keyword_extraction_method"] = "模拟TF-IDF算法"
            
        elif process_type == "summary":
            # 模拟内容摘要
            result["text_info"]["summary"] = "这是一个模拟的文本摘要，实际应用中可以使用NLP库生成真实的摘要。"
            result["text_info"]["summary_method"] = "模拟提取式摘要算法"
    
    except UnicodeDecodeError:
        result["text_info"]["error"] = "无法解码为文本，可能是二进制文件"
        result["status"] = "部分失败"
    
    return result

def process_excel(content: bytes, file_ext: str, process_type: str) -> Dict[str, Any]:
    """
    处理Excel文件
    
    Args:
        content: 文件内容
        file_ext: 文件扩展名
        process_type: 处理类型
        
    Returns:
        处理结果
    """
    result = {
        "excel_info": {
            "mime_type": guess_mime_type(file_ext),
            "file_type": "Excel文件",
            "process_type": process_type
        }
    }
    
    # 模拟Excel处理，实际应用中可以使用pandas、openpyxl等库进行处理
    
    if process_type == "structure":
        # 模拟Excel结构分析
        result["excel_info"]["sheets"] = ["模拟工作表1", "模拟工作表2", "模拟工作表3"]
        result["excel_info"]["sheet_count"] = 3
        result["excel_info"]["named_ranges"] = ["模拟命名范围1", "模拟命名范围2"]
        
    elif process_type == "preview":
        # 模拟数据预览
        result["excel_info"]["preview"] = [
            ["姓名", "年龄", "职位"],
            ["张三", "28", "工程师"],
            ["李四", "35", "经理"],
            ["王五", "42", "总监"]
        ]
        result["excel_info"]["rows_count"] = "模拟值：1000行"
        result["excel_info"]["columns_count"] = "模拟值：15列"
        
    elif process_type == "stats":
        # 模拟数据统计
        result["excel_info"]["stats"] = {
            "sheet1": {
                "rows": "模拟值：500行",
                "columns": "模拟值：8列",
                "numeric_columns": "模拟值：5列",
                "text_columns": "模拟值：3列"
            },
            "sheet2": {
                "rows": "模拟值：300行",
                "columns": "模拟值：12列",
                "numeric_columns": "模拟值：7列",
                "text_columns": "模拟值：5列"
            }
        }
    
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
        # 文本文件
        "txt": "text/plain",
        "html": "text/html",
        "css": "text/css",
        "csv": "text/csv",
        "md": "text/markdown",
        "xml": "application/xml",
        "json": "application/json",
        
        # 图像文件
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "svg": "image/svg+xml",
        "webp": "image/webp",
        
        # Excel文件
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        
        # 其他常见文件
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "zip": "application/zip",
    }
    
    return mime_types.get(file_ext.lower(), "application/octet-stream") 