"""
简单示例扩展

这是一个基础的扩展示例，展示了如何创建一个简单的数据查询扩展。
该扩展接收几个基本参数，并返回格式化的结果。
"""

def get_config():
    """
    获取扩展配置
    
    定义扩展的基本信息、参数和UI显示选项
    
    Returns:
        扩展配置字典
    """
    return {
        # 基本信息
        "name": "简单示例扩展",
        "description": "这是一个基础的示例扩展，展示了扩展的基本结构和用法",
        "version": "1.0.0",
        "author": "系统开发团队",
        
        # 参数定义
        "parameters": [
            {
                "name": "name",
                "description": "您的姓名",
                "type": "string",
                "required": True,
                "default": ""
            },
            {
                "name": "age",
                "description": "您的年龄",
                "type": "integer",
                "required": False,
                "default": 0,
                "minimum": 0,
                "maximum": 120
            },
            {
                "name": "interests",
                "description": "您的兴趣爱好",
                "type": "array",
                "items": {
                    "type": "string"
                },
                "required": False,
                "default": []
            },
            {
                "name": "education_level",
                "description": "教育程度",
                "type": "string",
                "enum": ["小学", "初中", "高中", "大学", "研究生", "博士"],
                "required": False,
                "default": "大学"
            }
        ],
        
        # UI配置
        "ui": {
            "group": "示例",
            "icon": "example",
            "primary_color": "#4e73df",
            "secondary_color": "#f8f9fc"
        }
    }


def query(params):
    """
    执行查询逻辑
    
    根据输入的参数，生成一个简单的个人信息摘要
    
    Args:
        params: 查询参数字典
        
    Returns:
        查询结果字典
    """
    try:
        # 获取参数值
        name = params.get("name", "")
        age = params.get("age", 0)
        interests = params.get("interests", [])
        education_level = params.get("education_level", "大学")
        
        # 数据验证
        if not name:
            return {
                "success": False,
                "message": "姓名不能为空",
                "data": None
            }
        
        # 处理兴趣爱好列表
        interests_text = "没有填写兴趣爱好"
        if interests and len(interests) > 0:
            interests_text = "、".join(interests)
        
        # 构建结果
        summary = f"{name}，{age}岁，教育程度为{education_level}，兴趣爱好包括：{interests_text}。"
        
        # 构建额外数据
        details = {
            "name": name,
            "age": age,
            "education": education_level,
            "interests": interests,
            "summary": summary
        }
        
        # 返回成功结果
        return {
            "success": True,
            "message": "查询成功",
            "data": {
                "summary": summary,
                "details": details
            }
        }
        
    except Exception as e:
        # 异常处理
        return {
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": None
        }


# 测试代码 - 仅在直接运行文件时执行
if __name__ == "__main__":
    # 打印配置信息
    import json
    print("扩展配置:")
    print(json.dumps(get_config(), indent=2, ensure_ascii=False))
    
    # 测试查询函数
    test_params = {
        "name": "张三",
        "age": 30,
        "interests": ["编程", "阅读", "旅行"],
        "education_level": "研究生"
    }
    
    print("\n测试查询:")
    result = query(test_params)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 