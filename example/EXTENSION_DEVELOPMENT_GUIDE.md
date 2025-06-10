# 扩展开发指南

本文档提供了如何为扩展数据查询系统开发安全、高效扩展的指南。扩展是实现新功能和连接外部数据源的推荐方式。

## 目录

1. [扩展系统概述](#扩展系统概述)
2. [扩展文件结构](#扩展文件结构)
3. [必需和可选函数](#必需和可选函数)
4. [配置参数与查询参数](#配置参数与查询参数)
5. [文件上传处理](#文件上传处理)
6. [沙箱安全规则](#沙箱安全规则)
7. [表单开发指南](#表单开发指南)
8. [最佳实践](#最佳实践)
9. [示例扩展](#示例扩展)

## 扩展系统概述

扩展系统允许开发者创建新的查询功能，而无需修改核心应用代码。每个扩展都是一个独立的Python模块，通过标准接口与主应用交互。

扩展在沙箱环境中执行，以确保系统安全和稳定运行。系统自动为每个启用的扩展创建一个API端点，可通过前端界面或直接调用API使用。

## 扩展文件结构

一个标准的扩展模块应包含以下元素：

1. **模块文档字符串**：描述扩展的功能、作者和版本信息
2. **配置管理函数**：定义和处理扩展配置
3. **查询表单函数**：定义用户输入界面
4. **查询执行函数**：实现核心业务逻辑

### 基本模板

```python
"""
扩展名称和简要描述

详细描述扩展的功能和用途

作者: 您的姓名
版本: 1.0.0
日期: YYYY-MM-DD
"""
from typing import Dict, Any

def get_default_config() -> Dict[str, Any]:
    """返回扩展的默认配置"""
    return {
        "数据库地址": "localhost:3306",
        "用户名": "admin",
        "连接超时": 30
    }

def get_config_form() -> str:
    """返回配置表单的HTML"""
    return """
    <div class="mb-3">
        <label for="config.数据库地址" class="form-label">数据库地址</label>
        <input type="text" class="form-control" id="config.数据库地址" name="config.数据库地址" 
               value="{{ config.数据库地址 }}">
    </div>
    """

def get_query_form() -> str:
    """返回查询表单的HTML"""
    return """
    <div class="mb-3">
        <label for="关键词" class="form-label">搜索关键词</label>
        <input type="text" class="form-control" id="关键词" name="关键词">
    </div>
    """

def execute_query(params: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行查询逻辑
    
    Args:
        params: 查询参数
        config: 扩展配置
        
    Returns:
        查询结果字典
    """
    # 实现查询逻辑
    return {
        "success": True,
        "results": []
    }
```

## 必需和可选函数

### 必需函数

* **execute_query(params, config)** - 执行查询的主函数，必须实现

### 可选函数

* **get_default_config()** - 返回默认配置
* **get_config_form()** - 返回配置表单的HTML
* **get_query_form()** - 返回查询表单的HTML

## 配置参数与查询参数

扩展系统中的参数分为两类：**配置参数**和**查询参数**。理解这两者的区别对于正确设计扩展非常重要。

### 配置参数 (Config)

配置参数是**长期稳定**的设置，通常由管理员设置，不经常变更，例如：

- 数据库连接信息（地址、用户名、密码）
- API密钥和认证信息
- 全局限制和阈值（超时时间、最大结果数、分页大小）
- 功能开关和处理模式

配置参数通过`get_default_config()`函数提供默认值，并通过`get_config_form()`函数提供配置界面。管理员可以在系统管理界面中修改这些配置，修改后的配置会被保存并在所有查询中使用。

### 查询参数 (Params)

查询参数是**每次查询可能变动**的输入，由用户在每次查询时提供，例如：

- 搜索关键词
- 日期范围
- 筛选条件
- 排序方式
- 上传的文件（用于处理和分析）

查询参数通过`get_query_form()`函数定义输入界面，用户每次执行查询时都需要填写或修改这些参数。这些参数不会被长期保存，仅用于当前查询。

### 区别和最佳实践

|              | 配置参数 (Config)              | 查询参数 (Params)            |
|--------------|------------------------------|----------------------------|
| **变更频率**   | 低频，稳定                     | 高频，每次查询可能不同         |
| **设置者**    | 管理员                        | 最终用户                     |
| **保存方式**   | 持久化存储                     | 临时使用，不持久保存           |
| **适用场景**   | 连接信息、认证信息、系统限制       | 搜索条件、过滤条件、上传文件      |
| **定义函数**   | `get_default_config()`      | `get_query_form()`         |
| **表单前缀**   | `config.参数名`               | 直接使用参数名                |

设计扩展时，请合理划分参数类型，避免将经常变动的查询条件放在配置中，也避免将敏感的连接信息放在查询参数中。

## 文件上传处理

扩展系统支持文件上传和处理功能，允许用户上传文件进行分析、处理或导入数据。

### 文件上传表单

要启用文件上传，在`get_query_form()`函数中添加文件输入控件：

```html
<div class="mb-3">
    <label for="my_file" class="form-label">上传文件</label>
    <input type="file" class="form-control" id="my_file" name="my_file">
    <div class="form-text">选择要上传的文件</div>
</div>
```

<!-- 仅接受图片 -->
<input type="file" class="form-control" id="image" name="image" accept="image/*">

<!-- 仅接受特定类型 -->
<input type="file" class="form-control" id="document" name="document" accept=".pdf,.doc,.docx,.txt">

### 文件处理

在`execute_query()`函数中，上传的文件可以通过`params["files"]`字典访问：

```python
def execute_query(params, config):
    # 获取上传的文件
    files = params.get("files", {})
    
    # 处理文件
    results = []
    for file_key, file_data in files.items():
        filename = file_data.get("filename")
        content_type = file_data.get("content_type")
        content = file_data.get("content")  # 文件内容(bytes)
        
        # 处理文件内容...
        
    return {
        "success": True,
        "results": results
    }
```

### 文件数据结构

上传的文件在`params["files"]`字典中的结构如下：

```python
{
    "query.myfile": {
        "filename": "example.txt",
        "content_type": "text/plain",
        "content": b"文件内容（二进制数据）" 
    }
}
```

### 文件处理最佳实践

1. **文件大小限制**：验证文件大小是否在合理范围内，避免处理过大的文件导致性能问题
2. **文件类型验证**：检查文件扩展名和MIME类型，只接受预期的文件类型
3. **安全处理**：注意文件内容的安全性，防止恶意文件
4. **内存管理**：处理大文件时注意内存使用，避免占用过多资源
5. **错误处理**：妥善处理文件读取和处理过程中的异常

### 示例：文本文件分析

```python
def execute_query(params, config):
    files = params.get("files", {})
    results = []
    
    for file_key, file_data in files.items():
        filename = file_data.get("filename", "未知文件")
        content = file_data.get("content", b"")
        
        try:
            # 尝试将文件内容解码为文本
            text = content.decode("utf-8")
            
            # 文本分析
            word_count = len(text.split())
            line_count = text.count("\n") + 1
            char_count = len(text)
            
            results.append({
                "filename": filename,
                "word_count": word_count,
                "line_count": line_count,
                "char_count": char_count,
                "excerpt": text[:100] + "..." if len(text) > 100 else text
            })
        except UnicodeDecodeError:
            results.append({
                "filename": filename,
                "error": "无法解码为文本，可能是二进制文件"
            })
    
    return {
        "success": True,
        "results": results
    }
```

### 完整示例

系统提供了一个完整的文件处理示例扩展`file_upload_extension_example.py`，展示了如何：

1. 设计文件上传表单
2. 处理不同类型的文件
3. 进行文件内容分析
4. 计算文件哈希值
5. 安全检查文件

参考该示例可以快速实现自己的文件处理功能。

## 沙箱安全规则

为确保系统安全，扩展在受限的沙箱环境中执行。以下限制适用于所有扩展：

### 禁止导入的模块

出于安全考虑，以下模块不能在扩展中使用：

* `os` - 操作系统接口
* `sys` - 系统特定参数和函数
* `subprocess` - 子进程管理
* `multiprocessing` - 基于进程的并行处理
* `threading` - 线程相关功能
* `socket` - 低级网络接口
* `pickle` - Python对象序列化
* `marshal` - Python内部对象序列化
* `builtins` - 内置命名空间
* `ctypes` - 外部函数库接口
* 其他系统和平台相关模块

### 允许使用的模块

扩展可以安全使用以下模块：

* `datetime` - 日期和时间处理
* `json` - JSON编码和解码
* `math` - 数学函数
* `re` - 正则表达式
* `random` - 随机数生成
* `collections` - 容器数据类型
* `functools` - 高阶函数工具
* `itertools` - 迭代器函数
* `decimal` - 十进制固定和浮点运算
* `string` - 字符串操作
* `time` - 时间访问和转换
* `uuid` - UUID对象
* `hashlib` - 安全哈希和消息摘要
* `base64` - Base16/32/64数据编码
* `urllib.parse` - URL解析
* `csv` - CSV文件读写
* `xml.etree.ElementTree` - XML处理

### 资源限制

扩展代码的执行受到以下限制：

* **执行时间**：每次查询最长执行30秒
* **内存使用**：最多使用100MB内存
* **CPU使用**：有限制

## 表单开发指南

### 配置表单

配置表单用于管理员设置扩展参数。以下是开发配置表单的指南：

1. 使用Bootstrap 5样式和组件
2. 使用`config.参数名`格式命名表单元素
3. 可以使用Jinja2模板语法`{{ config.参数名 }}`引用当前配置值
4. 添加适当的验证和帮助文本
5. 适合放置**不经常变更**的参数，如连接信息、认证信息
6. 注意敏感信息（如密码）的处理，使用password类型输入框

### 查询表单

查询表单是用户与扩展交互的界面。开发查询表单时：

1. 使用Bootstrap 5样式和组件
2. 使用参数的直接名称作为表单元素的name属性（不再需要query.前缀）
3. 保持表单结构清晰，使用恰当的标签和描述
4. 考虑响应式设计，使用栅格系统
5. 适合放置**经常变更**的参数，如搜索条件、日期范围、上传文件等
6. 提供直观的用户体验，考虑不同类型数据的适当输入控件（日期选择器、下拉列表等）

## 最佳实践

开发扩展时，请遵循以下最佳实践：

1. **异常处理**：妥善处理所有可能的异常，提供清晰的错误消息
2. **参数验证**：在执行查询前验证所有参数
3. **性能优化**：
   - 最小化外部API调用
   - 合理使用缓存
   - 分页处理大量数据
4. **安全性**：
   - 不存储敏感信息
   - 使用参数化查询防止注入攻击
   - 验证和净化用户输入
5. **文档**：
   - 提供全面的模块和函数文档字符串
   - 详细说明参数和返回值
   - 添加使用示例
6. **参数设计**：
   - 明确区分配置参数和查询参数
   - 配置参数适合存放连接信息、API密钥等稳定的设置
   - 查询参数适合存放搜索关键词、过滤条件等变化的输入

## 示例扩展

我们提供了一个示例扩展模板`safe_extension_template.py`，它演示了如何实现一个完整、安全的扩展。该示例包括：

1. 完整的文档
2. 配置和查询表单
3. 参数验证
4. 错误处理
5. 模拟数据生成和过滤
6. 合理的参数分类（配置参数与查询参数）

请参考该示例作为开发自己扩展的起点。

---

如有任何问题，请联系系统管理员。祝您开发愉快！ 