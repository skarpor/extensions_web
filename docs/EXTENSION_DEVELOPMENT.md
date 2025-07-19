# 扩展开发文档

## 概述

扩展工作台支持多种返回值类型的扩展开发，提供统一的数据格式和丰富的前端显示功能。本文档详细介绍如何开发兼容的扩展程序。

## 支持的返回值类型

### 1. HTML类型 (`html`)
**用途**: 返回HTML内容，直接在页面中渲染
**特性**: 支持样式、脚本、交互元素

```python
def execute_query(params, config=None):
    return {
        "type": "html",
        "data": "<div><h1>系统状态</h1><p>CPU: 50%</p></div>",
        "meta": {
            "generated_at": "2025-07-19 21:30:00",
            "theme": "dark"
        }
    }
```

### 2. Table类型 (`table`)
**用途**: 返回表格数据，支持排序、分页、导出
**特性**: 自动列类型识别、数据导出、全屏显示

```python
def execute_query(params, config=None):
    return {
        "type": "table",
        "data": [
            {"PID": 1234, "进程名": "python.exe", "CPU": 15.5, "状态": "运行"},
            {"PID": 5678, "进程名": "chrome.exe", "CPU": 25.2, "状态": "运行"}
        ],
        "meta": {
            "查询时间": "2025-07-19 21:30:00",
            "总进程数": 150
        }
    }
```

### 3. Text类型 (`text`)
**用途**: 返回纯文本内容，支持搜索、复制、统计
**特性**: 文本搜索、字符统计、全屏模式

```python
def execute_query(params, config=None):
    return {
        "type": "text",
        "data": "系统信息报告\n=============\nCPU: Intel i7\n内存: 16GB",
        "meta": {
            "report_format": "detailed",
            "line_count": 4,
            "character_count": 45
        }
    }
```

### 4. File类型 (`file`)
**用途**: 生成文件供用户下载
**特性**: 文件预览、下载进度、格式识别

```python
def execute_query(params, config=None):
    return {
        "type": "file",
        "data": {
            "file_path": "/tmp/report.csv",
            "filename": "system_report.csv",
            "content_type": "text/csv",
            "size": 1024
        },
        "meta": {
            "generated_at": "2025-07-19 21:30:00",
            "compressed": False
        }
    }
```

### 5. Chart类型 (`chart`)
**用途**: 返回图表配置，使用Chart.js渲染
**特性**: 多种图表类型、交互功能、数据导出

```python
def execute_query(params, config=None):
    return {
        "type": "chart",
        "data": {
            "chart_type": "line",
            "chart_data": {
                "labels": ["1月", "2月", "3月", "4月"],
                "datasets": [{
                    "label": "销售额",
                    "data": [100, 150, 120, 180],
                    "borderColor": "#ff6b6b",
                    "backgroundColor": "rgba(255, 107, 107, 0.1)"
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "月度销售趋势"
                    }
                }
            }
        },
        "meta": {
            "chart_type": "line",
            "data_points": 4
        }
    }
```

### 6. Image类型 (`image`)
**用途**: 返回图片数据或URL
**特性**: 缩放、全屏、下载

```python
def execute_query(params, config=None):
    return {
        "type": "image",
        "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
        "meta": {
            "width": 800,
            "height": 600,
            "format": "png"
        }
    }
```

## 标准返回格式

所有扩展都应该返回以下标准格式：

```python
{
    "type": "html|table|text|file|chart|image",  # 必需：返回值类型
    "data": "具体的数据内容",                      # 必需：实际数据
    "meta": {                                    # 可选：元数据
        "generated_at": "2025-07-19 21:30:00",  # 生成时间
        "其他元数据": "..."                       # 其他相关信息
    }
}
```

## 兼容性适配

### 自动适配机制
扩展工作台提供自动适配功能，即使扩展返回非标准格式，也会尝试适配：

1. **类型推断**: 根据扩展的`render_type`配置推断显示类型
2. **数据转换**: 自动将数据转换为对应类型的格式
3. **元数据生成**: 自动生成基础元数据信息

### 数据转换规则

| 原始数据类型 | 目标类型 | 转换规则 |
|-------------|---------|----------|
| 字符串 | html/text | 直接使用 |
| 数组 | table | 直接使用 |
| 对象 | table | 转换为键值对表格 |
| 数组/对象 | chart | 自动生成图表配置 |
| 任意类型 | text | JSON序列化 |

## 前端显示特性

### HTML类型
- ✅ 直接渲染HTML内容
- ✅ 支持CSS样式
- ✅ 支持JavaScript（受限）
- ✅ 响应式布局

### Table类型
- ✅ 自动列类型识别（数字、状态、文本）
- ✅ 排序功能
- ✅ 分页显示
- ✅ 数据导出（CSV、JSON）
- ✅ 全屏模式
- ✅ 搜索过滤

### Text类型
- ✅ 语法高亮
- ✅ 全文搜索
- ✅ 文本统计
- ✅ 复制功能
- ✅ 全屏模式
- ✅ 自动换行

### File类型
- ✅ 文件信息显示
- ✅ 下载进度
- ✅ 文件预览（支持多种格式）
- ✅ 格式识别
- ✅ 大小格式化

### Chart类型
- ✅ 多种图表类型（line、bar、pie、doughnut等）
- ✅ 交互功能（缩放、悬停）
- ✅ 图表导出（PNG、SVG）
- ✅ 数据表格查看
- ✅ 全屏模式
- ✅ 动画效果

### Image类型
- ✅ 图片缩放
- ✅ 全屏预览
- ✅ 图片下载
- ✅ 格式支持（PNG、JPG、SVG等）
- ✅ 尺寸信息显示

## 最佳实践

### 1. 错误处理
```python
def execute_query(params, config=None):
    try:
        # 扩展逻辑
        result = process_data()
        return {
            "type": "table",
            "data": result,
            "meta": {"success": True}
        }
    except Exception as e:
        return {
            "type": "text",
            "data": f"执行失败: {str(e)}",
            "meta": {
                "error": True,
                "error_message": str(e)
            }
        }
```

### 2. 配置表单
```python
def get_config_form(current_config=None):
    config = current_config or get_default_config()
    return f"""
    <div class="form-group">
        <label for="config.max_items">最大条目数:</label>
        <input type="number" name="config.max_items" 
               value="{config.get('max_items', 100)}" 
               min="1" max="1000" class="form-control">
    </div>
    """

def get_query_form(config=None):
    return """
    <div class="form-group">
        <label for="search_term">搜索关键词:</label>
        <input type="text" name="search_term" class="form-control">
    </div>
    """
```

### 3. 性能优化
- 限制数据量大小
- 使用分页机制
- 缓存计算结果
- 异步处理长时间操作

### 4. 用户体验
- 提供有意义的错误信息
- 添加加载状态提示
- 支持参数验证
- 提供使用说明

## 调试和测试

### 1. 本地测试
```python
# 测试扩展函数
if __name__ == "__main__":
    result = execute_query({}, {})
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 2. 格式验证
使用提供的验证工具检查返回格式：
```javascript
import { validateExtensionResult } from '@/utils/extensionAdapter'

const validation = validateExtensionResult(result)
if (!validation.valid) {
    console.error('格式错误:', validation.errors)
}
```

### 3. 兼容性测试
确保扩展在不同配置下都能正常工作：
- 不同的参数组合
- 空数据情况
- 错误情况处理
- 大数据量测试

## 部署和发布

### 1. 文件结构
```
extension_name.py
├── get_default_config()    # 默认配置
├── get_config_form()       # 配置表单
├── get_query_form()        # 查询表单
└── execute_query()         # 主执行函数
```

### 2. 安装步骤
1. 将扩展文件放入 `data/extensions/` 目录
2. 在扩展管理页面安装
3. 配置扩展参数
4. 测试扩展功能

### 3. 版本管理
- 在扩展文件中添加版本信息
- 记录变更日志
- 保持向后兼容性

## 常见问题

### Q: 如何处理大量数据？
A: 使用分页机制，限制单次返回的数据量，考虑使用流式处理。

### Q: 图表不显示怎么办？
A: 检查chart_data格式是否正确，确保Chart.js库已加载。

### Q: 如何自定义样式？
A: 在HTML类型中可以包含CSS样式，其他类型通过主题配置调整。

### Q: 扩展执行超时怎么办？
A: 优化算法性能，使用异步处理，设置合理的超时时间。

## 示例扩展

完整的示例扩展可以在以下文件中找到：
- `extension_html_dashboard.py` - HTML仪表板
- `extension_table_processes.py` - 进程表格
- `extension_text_sysinfo.py` - 系统信息
- `extension_file_logger.py` - 日志文件
- `extension_chart_performance.py` - 性能图表
