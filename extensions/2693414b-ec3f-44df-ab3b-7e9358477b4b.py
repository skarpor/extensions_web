import pandas as pd
import numpy as np

def execute_query(params: dict, config: dict):
    """
    示例查询函数，执行一些数据处理并返回结果
    
    参数:
        params (dict): 查询参数
        config (dict): 扩展配置
        
    返回:
        dict: 查询结果
    """
    # 从配置获取数据库连接信息等
    db_config = config.get("database", {})
    
    # 示例1: 生成随机数据
    if params.get("type") == "random":
        size = params.get("size", 10)
        return {
            "data": np.random.rand(size).tolist(),
            "message": f"Generated {size} random numbers"
        }
    
    # 示例2: 模拟数据库查询
    elif params.get("type") == "simulate_db":
        # 这里应该是实际的数据库查询代码
        # 示例使用pandas生成模拟数据
        data = {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "score": [85.5, 92.0, 78.5]
        }
        df = pd.DataFrame(data)
        
        # 应用简单过滤
        if "min_age" in params:
            df = df[df["age"] >= params["min_age"]]
        
        return {
            "columns": list(df.columns),
            "data": df.to_dict("records"),
            "count": len(df)
        }
    
    else:
        raise ValueError("Unknown query type")

# 可选: 扩展配置表单
def get_config_form():
    """
    返回扩展配置的HTML表单
    
    返回:
        str: HTML表单字符串
    """
    return """
    <div class="mb-3">
        <label class="form-label">数据库连接字符串</label>
        <input type="text" class="form-control" name="database.connection_string">
    </div>
    <div class="mb-3">
        <label class="form-label">缓存时间(秒)</label>
        <input type="number" class="form-control" name="database.cache_ttl" value="300">
    </div>
    """