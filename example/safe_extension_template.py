"""
安全扩展模板示例

这是一个遵循沙箱安全规则的扩展模板，可以作为开发新扩展的基础。
该模板展示了如何实现配置表单、查询表单和安全的查询执行。

配置参数与查询参数：
- 配置参数：管理员设置的长期稳定参数，如数据库连接信息、API密钥等
- 查询参数：用户每次查询时输入的可变参数，如搜索关键词、日期范围等

作者: System Administrator
版本: 1.1.0
日期: 2025-05-10
"""
import json
import math
import random
import datetime
import uuid
import hashlib
import base64
from typing import Dict, List, Any, Optional


def get_default_config() -> Dict[str, Any]:
    """
    返回扩展的默认配置
    
    配置参数是管理员设置的长期稳定参数，通常包括：
    - 连接信息（数据库地址、API端点）
    - 认证信息（用户名、API密钥）
    - 全局限制（分页大小、缓存时间）
    - 功能开关（启用特定功能）
    
    Returns:
        包含默认配置的字典
    """
    return {
        # 数据连接和认证相关配置
        "api_endpoint": "https://api.example.com/v1",
        "api_key": "",  # 安全考虑，默认为空
        
        # 全局限制和控制
        "items_per_page": 10,
        "max_results": 100,
        "default_sort": "name",
        
        # 缓存设置
        "cache_results": True,
        "cache_ttl": 300,  # 秒
        
        # 功能开关
        "enable_advanced_search": False,
        "enable_export": True
    }


def get_config_form() -> str:
    """
    返回扩展配置表单的HTML
    
    配置表单用于管理员配置扩展参数，这些参数通常是稳定的，不经常变更。
    每个配置项应使用 'config.' 前缀，并使用 Jinja2 模板语法引用当前值。
    
    Returns:
        HTML表单代码
    """
    return """
    <div class="card mb-4">
        <div class="card-header">
            <h5>API连接设置</h5>
            <p class="card-text text-muted">设置外部API的连接参数</p>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label for="config.api_endpoint" class="form-label">API端点</label>
                <input type="text" class="form-control" id="config.api_endpoint" name="config.api_endpoint" 
                       value="{{ config.api_endpoint }}">
                <div class="form-text">外部API的基础URL地址</div>
            </div>
            
            <div class="mb-3">
                <label for="config.api_key" class="form-label">API密钥</label>
                <input type="password" class="form-control" id="config.api_key" name="config.api_key" 
                       value="{{ config.api_key }}">
                <div class="form-text">访问API所需的密钥，留空表示不使用认证</div>
            </div>
        </div>
    </div>
    
    <div class="card mb-4">
        <div class="card-header">
            <h5>数据控制设置</h5>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label for="config.items_per_page" class="form-label">每页显示项目数</label>
                <input type="number" class="form-control" id="config.items_per_page" name="config.items_per_page" 
                       value="{{ config.items_per_page }}" min="1" max="100">
                <div class="form-text">设置每页显示的结果数量</div>
            </div>
            
            <div class="mb-3">
                <label for="config.max_results" class="form-label">最大结果数</label>
                <input type="number" class="form-control" id="config.max_results" name="config.max_results" 
                       value="{{ config.max_results }}" min="1" max="1000">
                <div class="form-text">单次查询返回的最大结果数量</div>
            </div>
            
            <div class="mb-3">
                <label for="config.default_sort" class="form-label">默认排序字段</label>
                <select class="form-select" id="config.default_sort" name="config.default_sort">
                    <option value="name" {% if config.default_sort == "name" %}selected{% endif %}>名称</option>
                    <option value="date" {% if config.default_sort == "date" %}selected{% endif %}>日期</option>
                    <option value="priority" {% if config.default_sort == "priority" %}selected{% endif %}>优先级</option>
                </select>
                <div class="form-text">未指定排序时的默认排序字段</div>
            </div>
        </div>
    </div>
    
    <div class="card mb-4">
        <div class="card-header">
            <h5>缓存和性能设置</h5>
        </div>
        <div class="card-body">
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.cache_results" name="config.cache_results" 
                       {% if config.cache_results %}checked{% endif %}>
                <label class="form-check-label" for="config.cache_results">启用结果缓存</label>
                <div class="form-text">缓存查询结果以提高性能</div>
            </div>
            
            <div class="mb-3">
                <label for="config.cache_ttl" class="form-label">缓存时间 (秒)</label>
                <input type="number" class="form-control" id="config.cache_ttl" name="config.cache_ttl" 
                       value="{{ config.cache_ttl }}" min="0" max="3600">
                <div class="form-text">结果缓存的有效时间</div>
            </div>
        </div>
    </div>
    
    <div class="card mb-4">
        <div class="card-header">
            <h5>功能开关</h5>
        </div>
        <div class="card-body">
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.enable_advanced_search" name="config.enable_advanced_search" 
                       {% if config.enable_advanced_search %}checked{% endif %}>
                <label class="form-check-label" for="config.enable_advanced_search">启用高级搜索</label>
                <div class="form-text">允许用户使用高级搜索功能</div>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="config.enable_export" name="config.enable_export" 
                       {% if config.enable_export %}checked{% endif %}>
                <label class="form-check-label" for="config.enable_export">启用导出功能</label>
                <div class="form-text">允许用户导出查询结果</div>
            </div>
        </div>
    </div>
    """


def get_query_form() -> str:
    """
    返回查询表单的HTML
    
    查询表单用于用户输入查询参数，这些参数在每次查询时可能不同。
    包括：搜索关键词、日期范围、筛选条件、上传文件等。
    
    Returns:
        HTML表单代码
    """
    return """
    <div class="card mb-4">
        <div class="card-header">
            <h5>基本搜索</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="keyword" class="form-label">关键词</label>
                    <input type="text" class="form-control" id="keyword" name="keyword" placeholder="输入搜索关键词">
                    <div class="form-text">在名称和描述中搜索</div>
                </div>
                
                <div class="col-md-6 mb-3">
                    <label for="category" class="form-label">类别</label>
                    <select class="form-select" id="category" name="category">
                        <option value="">-- 全部类别 --</option>
                        <option value="technology">技术</option>
                        <option value="business">商业</option>
                        <option value="health">健康</option>
                        <option value="education">教育</option>
                    </select>
                </div>
            </div>
        </div>
    </div>
    
    <div class="card mb-4">
        <div class="card-header">
            <h5>时间筛选</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="start_date" class="form-label">开始日期</label>
                    <input type="date" class="form-control" id="start_date" name="start_date">
                </div>
                
                <div class="col-md-6 mb-3">
                    <label for="end_date" class="form-label">结束日期</label>
                    <input type="date" class="form-control" id="end_date" name="end_date">
                </div>
            </div>
        </div>
    </div>
    
    <div class="card mb-4">
        <div class="card-header">
            <h5>高级选项</h5>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label for="sort_by" class="form-label">排序方式</label>
                <select class="form-select" id="sort_by" name="sort_by">
                    <option value="">-- 使用默认排序 --</option>
                    <option value="name">按名称</option>
                    <option value="date">按日期</option>
                    <option value="priority">按优先级</option>
                </select>
            </div>
            
            <div class="mb-3 form-check">
                <input type="checkbox" class="form-check-input" id="include_archived" name="include_archived">
                <label class="form-check-label" for="include_archived">包含归档项</label>
            </div>
            
            <div class="mb-3">
                <label for="file" class="form-label">上传文件（可选）</label>
                <input type="file" class="form-control" id="file" name="file">
                <div class="form-text">上传文件进行处理或分析</div>
            </div>
        </div>
    </div>
    """


def validate_params(params: Dict[str, Any]) -> tuple:
    """
    验证查询参数
    
    Args:
        params: 查询参数字典
        
    Returns:
        (bool, str) 元组，包含验证结果和错误消息
    """
    # 示例验证逻辑
    try:
        if isinstance(params, str):
            params = json.loads(params)
            
        # 检查必填参数
        if "query" not in params:
            return False, "缺少查询参数"
            
        # 验证日期格式
        if "start_date" in params["query"] and params["query"]["start_date"]:
            try:
                datetime.datetime.strptime(params["query"]["start_date"], "%Y-%m-%d")
            except ValueError:
                return False, "开始日期格式无效"
                
        if "end_date" in params["query"] and params["query"]["end_date"]:
            try:
                datetime.datetime.strptime(params["query"]["end_date"], "%Y-%m-%d")
            except ValueError:
                return False, "结束日期格式无效"
                
        # 验证日期范围
        if (params["query"].get("start_date") and params["query"].get("end_date") and
                params["query"]["start_date"] > params["query"]["end_date"]):
            return False, "开始日期不能晚于结束日期"
            
        return True, ""
    except Exception as e:
        return False, f"参数验证错误: {str(e)}"


def execute_query(params: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行查询逻辑
    
    这个函数实现了扩展的主要业务逻辑，处理查询请求并返回结果。
    它接收两类参数：
    - params: 用户每次查询时提供的查询参数（搜索条件、过滤器等）和上传的文件
    - config: 管理员配置的长期稳定参数（连接信息、API密钥等）
    
    Args:
        params: 查询参数，从查询表单收集，每次查询可能不同
        config: 扩展配置，从配置表单保存，相对稳定
        
    Returns:
        查询结果字典
    """
    try:
        # 参数处理和验证
        if isinstance(params, str):
            params = json.loads(params)
            
        valid, error_msg = validate_params(params)
        if not valid:
            return {
                "success": False,
                "error": error_msg
            }
            
        # 获取查询参数（用户输入的可变参数）
        query = params.get("query", {})
        keyword = query.get("keyword", "")
        category = query.get("category", "")
        start_date = query.get("start_date", "")
        end_date = query.get("end_date", "")
        include_archived = query.get("include_archived", False)
        sort_by = query.get("sort_by", "")
        
        # 处理上传的文件
        files = params.get("files", {})
        file_info = []
        
        # 遍历所有上传的文件
        for file_key, file_data in files.items():
            if file_data:
                filename = file_data.get("filename", "未知文件")
                content_type = file_data.get("content_type", "unknown")
                content = file_data.get("content", b"")
                file_size = len(content) if content else 0
                
                # 添加文件信息到结果
                file_info.append({
                    "key": file_key,
                    "filename": filename,
                    "content_type": content_type,
                    "size": file_size,
                    # 此处可以添加文件处理逻辑，如：
                    # 1. 保存文件到临时目录
                    # 2. 解析文件内容（如CSV、XML等）
                    # 3. 分析文件（图像处理、文本提取等）
                })
        
        # 获取配置参数（管理员设置的稳定参数）
        api_endpoint = config.get("api_endpoint", "")
        api_key = config.get("api_key", "")
        items_per_page = config.get("items_per_page", 10)
        max_results = config.get("max_results", 100)
        default_sort = config.get("default_sort", "name")
        cache_results = config.get("cache_results", True)
        enable_advanced_search = config.get("enable_advanced_search", False)
        
        # 使用有效的排序方式
        effective_sort = sort_by if sort_by else default_sort
        
        # 模拟API调用或数据库查询
        # 这里只是示例，实际应用中可能需要调用外部API或查询数据库
        print(f"模拟API调用: {api_endpoint}")
        if api_key:
            print(f"使用API密钥进行认证")
            
        # 如果启用了缓存，可以先检查缓存
        if cache_results:
            print(f"检查缓存...")
            
        # 高级搜索功能的示例条件处理
        if enable_advanced_search and keyword:
            print(f"使用高级搜索处理关键词: {keyword}")
            
        # 模拟数据库查询，生成结果
        results = generate_sample_data(
            keyword=keyword,
            category=category,
            start_date=start_date,
            end_date=end_date,
            include_archived=include_archived,
            limit=max_results,
            sort_by=effective_sort
        )
        
        # 构建响应
        response = {
            "success": True,
            "query": {
                "keyword": keyword,
                "category": category,
                "start_date": start_date,
                "end_date": end_date,
                "include_archived": include_archived,
                "sort_by": effective_sort
            },
            "config": {
                "items_per_page": items_per_page,
                "max_results": max_results,
                "api_endpoint": api_endpoint,
                # 不返回敏感信息如API密钥
            },
            "files_processed": file_info,  # 添加文件处理信息
            "stats": {
                "total_results": len(results),
                "page_count": math.ceil(len(results) / items_per_page),
                "execution_time": random.uniform(0.05, 0.5)
            },
            "results": results[:items_per_page]  # 仅返回第一页结果
        }
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": f"查询执行错误: {str(e)}"
        }


def generate_sample_data(keyword="", category="", start_date="", end_date="", 
                         include_archived=False, limit=100, sort_by="name") -> List[Dict[str, Any]]:
    """
    生成示例数据
    
    这个函数用于生成模拟数据，在实际应用中应替换为真实的数据查询
    
    Args:
        keyword: 搜索关键词
        category: 过滤类别
        start_date: 开始日期
        end_date: 结束日期
        include_archived: 是否包含归档项
        limit: 结果数量限制
        sort_by: 排序字段
        
    Returns:
        数据项列表
    """
    categories = ["technology", "business", "health", "education"]
    
    # 生成随机数据
    data = []
    for i in range(min(limit, 100)):  # 最多生成100条记录
        today = datetime.datetime.now()
        days_ago = random.randint(0, 365)
        created_date = (today - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        item = {
            "id": str(uuid.uuid4()),
            "name": f"项目 {i+1}",
            "description": f"这是项目 {i+1} 的详细说明。包含一些相关信息和描述。",
            "category": random.choice(categories),
            "created_date": created_date,
            "priority": random.randint(1, 5),
            "status": "active" if random.random() > 0.2 else "archived",
            "tags": random.sample(["标签A", "标签B", "标签C", "标签D", "标签E"], k=random.randint(1, 3))
        }
        data.append(item)
    
    # 应用过滤条件
    filtered_data = []
    for item in data:
        # 关键词过滤
        if keyword and keyword.lower() not in item["name"].lower() and keyword.lower() not in item["description"].lower():
            continue
            
        # 类别过滤
        if category and item["category"] != category:
            continue
            
        # 日期过滤
        if start_date and item["created_date"] < start_date:
            continue
            
        if end_date and item["created_date"] > end_date:
            continue
            
        # 归档状态过滤
        if not include_archived and item["status"] == "archived":
            continue
            
        filtered_data.append(item)
    
    # 排序
    if sort_by == "name":
        filtered_data.sort(key=lambda x: x["name"])
    elif sort_by == "date":
        filtered_data.sort(key=lambda x: x["created_date"], reverse=True)
    elif sort_by == "priority":
        filtered_data.sort(key=lambda x: x["priority"], reverse=True)
    
    return filtered_data 