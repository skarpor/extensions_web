# 文件上传功能开发指南

本指南将详细介绍如何在扩展中使用文件上传功能，包括表单设计、后端处理、安全检查和最佳实践。

## 目录

1. [概述](#概述)
2. [文件上传表单设计](#文件上传表单设计)
3. [后端文件处理](#后端文件处理)
4. [安全检查与验证](#安全检查与验证)
5. [文件管理器API](#文件管理器API)
6. [常见问题与解决方案](#常见问题与解决方案)
7. [最佳实践](#最佳实践)
8. [示例代码](#示例代码)

## 概述

文件上传功能允许扩展接收用户上传的文件，对其进行处理，并将结果返回给用户。系统提供了安全的文件管理API，使扩展可以：

- 接收用户上传的单个或多个文件
- 验证文件类型和大小
- 安全地存储文件
- 生成下载链接
- 管理文件元数据

文件上传和处理在沙箱环境中执行，具有严格的安全限制，保护系统免受潜在的恶意文件和代码的影响。

## 文件上传表单设计

### HTML表单元素

在`get_query_form`函数中，使用`<input type="file">`元素创建文件上传字段：

```html
<div class="mb-3">
    <label for="document_file" class="form-label">上传文档</label>
    <input type="file" class="form-control" id="document_file" name="document_file" required>
    <div class="form-text">支持PDF、Word和Excel文档</div>
</div>
```

### 多文件上传

要允许多个文件上传，可以设置`multiple`属性并调整`name`属性：

```html
<input type="file" class="form-control" id="images" name="images" multiple accept="image/*">
```

> **注意**：当使用`multiple`属性时，后端接收到的将是一个文件列表，而不是单个文件。

### 文件类型限制

使用`accept`属性限制可上传的文件类型：

```html
<!-- 仅接受图片 -->
<input type="file" accept="image/*">

<!-- 仅接受特定文件类型 -->
<input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx">
```

## 后端文件处理

在`execute_query`函数中，可以通过以下方式访问上传的文件：

```python
def execute_query(params, config):
    # 获取文件管理器
    file_manager = params.get("file_manager")
    
    # 获取查询参数和文件
    query = params.get("query", {})
    files = params.get("files", {})
    
    # 处理单个文件
    if "document_file" in files:
        file_data = files["document_file"]
        filename = file_data.get("filename")
        content_type = file_data.get("content_type")
        content = file_data.get("content")  # 二进制内容
        
        # 处理文件...
```

### 文件信息结构

上传的文件在`params["files"]`字典中，每个文件包含以下信息：

```python
{
    "filename": "example.pdf",      # 原始文件名
    "content_type": "application/pdf", # MIME类型
    "content": b"..."               # 文件二进制内容
}
```

## 安全检查与验证

在处理上传的文件前，应进行以下安全检查：

### 1. 文件大小验证

```python
# 限制文件大小（例如10MB）
max_size = 10 * 1024 * 1024
if len(file_content) > max_size:
    return {"error": f"文件大小超过限制: {len(file_content)/1024/1024:.2f}MB > 10MB"}
```

### 2. 文件类型验证

```python
# 允许的MIME类型列表
allowed_types = ["application/pdf", "image/jpeg", "image/png"]
if content_type not in allowed_types:
    return {"error": f"不支持的文件类型: {content_type}"}
```

### 3. 文件内容验证

对于特定文件类型，可以验证文件内容是否合法：

```python
# 检查PDF文件头
if content_type == "application/pdf" and not content.startswith(b"%PDF-"):
    return {"error": "无效的PDF文件"}
```

## 文件管理器API

系统提供的`file_manager`对象有以下主要方法：

### 保存文件

```python
file_meta = file_manager.save_file(
    file_content=content,      # 文件二进制内容
    filename="report.pdf",     # 原始文件名
    content_type="application/pdf", # MIME类型
    description="月度报告"     # 文件描述
)
```

返回的`file_meta`包含文件的元数据，如ID、名称、大小等信息。

### 列出文件

```python
# 列出当前扩展的文件，最多50个，从第0个开始
files = file_manager.list_files(limit=50, offset=0)
```

### 获取文件下载URL

```python
download_url = file_manager.get_file_url(file_id)
```

此URL可以返回给前端，用于下载文件。

## 常见问题与解决方案

### 问题1：文件上传后无法访问

确保在扩展配置中启用了文件上传功能，并检查`execute_query`函数是否正确处理了文件数据。

### 问题2：文件类型不被接受

检查HTML表单中的`accept`属性和后端的类型验证逻辑是否一致。

### 问题3：上传大文件时超时

系统对文件大小有限制（默认50MB），确保上传的文件在限制范围内，并在表单中告知用户这些限制。

## 最佳实践

1. **始终验证文件**：检查大小、类型和内容。
2. **提供清晰的错误信息**：当文件验证失败时，告诉用户具体原因。
3. **限制文件大小**：根据用例设置合理的文件大小限制。
4. **安全处理文件名**：避免直接使用用户提供的文件名，以防路径遍历攻击。
5. **优化用户体验**：在表单中明确说明支持的文件类型和大小限制。
6. **实现适当的错误处理**：捕获并处理所有可能的异常。

## 示例代码

以下是一个完整的文件上传处理示例：

```python
def execute_query(params, config):
    result = {"status": "success", "files": []}
    
    try:
        # 获取文件管理器
        file_manager = params.get("file_manager")
        if not file_manager:
            return {"status": "error", "message": "文件管理器不可用"}
        
        # 获取查询参数和文件
        query = params.get("query", {})
        files = params.get("files", {})
        
        # 获取配置参数
        max_size = config.get("max_file_size", 10) * 1024 * 1024
        allowed_types = config.get("allowed_types", [])
        
        # 处理上传的文件
        for file_key, file_data in files.items():
            filename = file_data.get("filename", "未命名文件")
            content_type = file_data.get("content_type", "application/octet-stream")
            content = file_data.get("content", b"")
            
            # 验证文件大小
            if len(content) > max_size:
                result["files"].append({
                    "name": filename,
                    "status": "error",
                    "message": f"文件太大: {len(content)/1024/1024:.2f}MB > {max_size/1024/1024}MB"
                })
                continue
            
            # 验证文件类型
            if allowed_types and content_type not in allowed_types:
                result["files"].append({
                    "name": filename,
                    "status": "error",
                    "message": f"不支持的文件类型: {content_type}"
                })
                continue
            
            # 保存文件
            saved_file = file_manager.save_file(
                file_content=content,
                filename=filename,
                content_type=content_type,
                description=query.get("description", "")
            )
            
            # 添加到结果
            result["files"].append({
                "name": filename,
                "status": "success",
                "file_id": saved_file.get("id"),
                "download_url": file_manager.get_file_url(saved_file.get("id"))
            })
            
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"文件处理失败: {str(e)}"
        }
```

查看完整的文件上传示例扩展代码：[file_upload_demo.py](file_upload_demo.py)

---

本指南涵盖了文件上传功能的基本概念和实现方法。随着您对系统的深入了解，可以开发更复杂的文件处理功能，如图像处理、文档解析等。

请记住，安全永远是首要考虑因素，特别是在处理用户上传的文件时。始终验证文件类型和内容，限制文件大小，并在沙箱环境中安全地处理文件。 