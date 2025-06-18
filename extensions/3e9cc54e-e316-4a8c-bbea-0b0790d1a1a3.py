"""
示例扩展，展示如何实现配置表单和查询表单
"""

def get_default_config():
    """返回扩展的默认配置"""
    return {
        "api_key": "",
        "base_url": "https://api.example.com/v1",
        "timeout": 30
    }

def get_config_form():
    """返回扩展配置表单的HTML"""
    return """
    <div class="mb-3">
        <label for="config.api_key" class="form-label">API密钥</label>
        <input type="password" class="form-control" id="config.api_key" name="config.api_key" 
               value="{{ config.api_key }}" placeholder="输入您的API密钥">
        <div class="form-text">在Example服务申请的API密钥</div>
    </div>
    
    <div class="mb-3">
        <label for="config.base_url" class="form-label">API基础URL</label>
        <input type="text" class="form-control" id="config.base_url" name="config.base_url" 
               value="{{ config.base_url }}">
    </div>
    
    <div class="mb-3">
        <label for="config.timeout" class="form-label">请求超时(秒)</label>
        <input type="number" class="form-control" id="config.timeout" name="config.timeout" 
               value="{{ config.timeout }}" min="1" max="120">
    </div>
    """

def get_query_form():
    """返回查询表单的HTML"""
    return """
    <div class="mb-3">
        <label for="params.keyword" class="form-label">搜索关键词</label>
        <input type="text" class="form-control" id="params.keyword" name="params.keyword" 
               placeholder="输入搜索关键词">
    </div>
    
    <div class="row">
        <div class="col-md-6 mb-3">
            <label for="params.start_date" class="form-label">开始日期</label>
            <input type="date" class="form-control" id="params.start_date" name="params.start_date">
        </div>
        <div class="col-md-6 mb-3">
            <label for="params.end_date" class="form-label">结束日期</label>
            <input type="date" class="form-control" id="params.end_date" name="params.end_date">
        </div>
    </div>
    
    <div class="mb-3">
        <label for="params.limit" class="form-label">最大结果数</label>
        <input type="number" class="form-control" id="params.limit" name="params.limit" 
               value="10" min="1" max="100">
    </div>
    """

def validate_config(config):
    """验证配置有效性"""
    if not config.get("api_key"):
        return False, "API密钥不能为空"
    
    if not config.get("base_url"):
        return False, "API基础URL不能为空"
    
    return True, ""

def execute_query(params, config):
    """执行查询
    
    Args:
        params: 查询参数，从查询表单收集
        config: 扩展配置，从配置表单保存
    """
    # 在实际应用中，这里会使用config中的API密钥等信息调用外部API
    # 这里仅作演示
    result = {
        "query_params": params,
        "config_used": {
            "base_url": config.get("base_url"),
            "timeout": config.get("timeout"),
            # 不要返回敏感信息如API密钥
        },
        "results": [
            {"id": 1, "name": "结果1", "timestamp": "2023-05-01"},
            {"id": 2, "name": "结果2", "timestamp": "2023-05-02"},
            {"id": 3, "name": "结果3", "timestamp": "2023-05-03"}
        ]
    }
    return result