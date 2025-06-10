"""
数据库使用示例扩展

这个示例展示了如何在扩展中使用数据库功能，包括创建表、插入数据和查询数据。
"""

def get_config():
    """
    获取扩展配置
    
    定义扩展的基本信息、参数和数据库表结构
    
    Returns:
        扩展配置字典
    """
    return {
        # 基本信息
        "name": "数据库示例扩展",
        "description": "演示如何在扩展中使用数据库功能",
        "version": "1.0.0",
        "author": "系统开发团队",
        
        # 参数定义
        "parameters": [
            {
                "name": "action",
                "description": "操作类型",
                "type": "string",
                "enum": ["add", "search", "list", "delete"],
                "required": True,
                "default": "list"
            },
            {
                "name": "name",
                "description": "联系人姓名",
                "type": "string",
                "required": False,
                "default": ""
            },
            {
                "name": "phone",
                "description": "联系人电话",
                "type": "string",
                "required": False,
                "default": ""
            },
            {
                "name": "email",
                "description": "联系人邮箱",
                "type": "string",
                "required": False,
                "default": ""
            },
            {
                "name": "search_term",
                "description": "搜索关键词",
                "type": "string",
                "required": False,
                "default": ""
            },
            {
                "name": "contact_id",
                "description": "联系人ID",
                "type": "integer",
                "required": False,
                "default": 0
            }
        ],
        
        # 数据库表结构定义
        "database": {
            "tables": [
                {
                    "name": "contacts",
                    "schema": """
                        CREATE TABLE IF NOT EXISTS contacts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            phone TEXT,
                            email TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """
                }
            ]
        },
        
        # UI配置
        "ui": {
            "group": "示例",
            "icon": "database",
            "primary_color": "#36b9cc",
            "secondary_color": "#f8f9fc"
        }
    }


def query(params, db=None):
    """
    执行查询逻辑
    
    根据操作类型执行不同的数据库操作
    
    Args:
        params: 查询参数字典
        db: 数据库实例
        
    Returns:
        查询结果字典
    """
    try:
        # 如果数据库实例不可用，返回错误
        if db is None:
            return {
                "success": False,
                "message": "数据库连接不可用",
                "data": None
            }
        
        # 获取操作类型
        action = params.get("action", "list")
        
        # 根据操作类型执行不同的数据库操作
        if action == "add":
            return add_contact(params, db)
        elif action == "search":
            return search_contacts(params, db)
        elif action == "list":
            return list_contacts(params, db)
        elif action == "delete":
            return delete_contact(params, db)
        else:
            return {
                "success": False,
                "message": f"不支持的操作类型: {action}",
                "data": None
            }
        
    except Exception as e:
        # 异常处理
        return {
            "success": False,
            "message": f"操作失败: {str(e)}",
            "data": None
        }


def add_contact(params, db):
    """添加联系人"""
    name = params.get("name")
    phone = params.get("phone", "")
    email = params.get("email", "")
    
    # 验证必填字段
    if not name:
        return {
            "success": False,
            "message": "联系人姓名不能为空",
            "data": None
        }
    
    # 执行插入操作
    query = """
        INSERT INTO contacts (name, phone, email)
        VALUES (?, ?, ?)
    """
    cursor = db.execute(query, (name, phone, email))
    db.commit()
    
    # 获取新增的联系人ID
    contact_id = cursor.lastrowid
    
    return {
        "success": True,
        "message": f"联系人 {name} 添加成功",
        "data": {
            "contact_id": contact_id,
            "name": name,
            "phone": phone,
            "email": email
        }
    }


def search_contacts(params, db):
    """搜索联系人"""
    search_term = params.get("search_term", "")
    
    if not search_term:
        return {
            "success": False,
            "message": "请输入搜索关键词",
            "data": None
        }
    
    # 执行搜索
    query = """
        SELECT id, name, phone, email, created_at
        FROM contacts
        WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
        ORDER BY name
    """
    search_param = f"%{search_term}%"
    result = db.query(query, (search_param, search_param, search_param))
    
    return {
        "success": True,
        "message": f"找到 {len(result)} 个匹配的联系人",
        "data": {
            "contacts": result
        }
    }


def list_contacts(params, db):
    """列出所有联系人"""
    # 执行查询
    query = """
        SELECT id, name, phone, email, created_at
        FROM contacts
        ORDER BY name
    """
    result = db.query(query)
    
    return {
        "success": True,
        "message": f"共有 {len(result)} 个联系人",
        "data": {
            "contacts": result
        }
    }


def delete_contact(params, db):
    """删除联系人"""
    contact_id = params.get("contact_id", 0)
    
    if not contact_id:
        return {
            "success": False,
            "message": "请指定要删除的联系人ID",
            "data": None
        }
    
    # 先查询联系人是否存在
    query = "SELECT name FROM contacts WHERE id = ?"
    result = db.query(query, (contact_id,))
    
    if not result:
        return {
            "success": False,
            "message": f"联系人ID {contact_id} 不存在",
            "data": None
        }
    
    name = result[0]["name"]
    
    # 执行删除
    query = "DELETE FROM contacts WHERE id = ?"
    db.execute(query, (contact_id,))
    db.commit()
    
    return {
        "success": True,
        "message": f"联系人 {name} (ID: {contact_id}) 已删除",
        "data": {
            "contact_id": contact_id,
            "name": name
        }
    }


# 测试代码 - 仅在直接运行文件时执行
if __name__ == "__main__":
    # 打印配置信息
    import json
    print("扩展配置:")
    print(json.dumps(get_config(), indent=2, ensure_ascii=False))
    
    # 模拟数据库
    class MockDB:
        def __init__(self):
            self.data = []
            self.last_id = 0
        
        def execute(self, query, params=None):
            print(f"执行SQL: {query}")
            print(f"参数: {params}")
            self.last_id += 1
            return self
        
        def commit(self):
            print("提交事务")
        
        def query(self, query, params=None):
            print(f"查询SQL: {query}")
            print(f"参数: {params}")
            
            if "SELECT id, name" in query and params and "张三" in params[0]:
                return [{"id": 1, "name": "张三", "phone": "13800138000", "email": "zhangsan@example.com", "created_at": "2023-01-01 12:00:00"}]
            
            return [
                {"id": 1, "name": "张三", "phone": "13800138000", "email": "zhangsan@example.com", "created_at": "2023-01-01 12:00:00"},
                {"id": 2, "name": "李四", "phone": "13900139000", "email": "lisi@example.com", "created_at": "2023-01-02 12:00:00"}
            ]
        
        @property
        def lastrowid(self):
            return self.last_id
    
    # 测试查询函数
    mock_db = MockDB()
    
    print("\n测试添加联系人:")
    add_params = {
        "action": "add",
        "name": "王五",
        "phone": "13700137000",
        "email": "wangwu@example.com"
    }
    result = query(add_params, mock_db)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n测试列出联系人:")
    list_params = {
        "action": "list"
    }
    result = query(list_params, mock_db)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n测试搜索联系人:")
    search_params = {
        "action": "search",
        "search_term": "张三"
    }
    result = query(search_params, mock_db)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 