"""
扩展基类模块
"""

class ExtensionBase:
    """扩展基类，定义所有扩展必须实现的接口"""
    
    @classmethod
    def get_default_config(cls):
        """返回扩展的默认配置"""
        return {}
    
    @classmethod
    def get_config_form(cls, current_config=None):
        """返回扩展配置表单的HTML
        
        Args:
            current_config: 当前配置值
        """
        return "<p>此扩展没有配置选项</p>"
    
    @classmethod
    def get_query_form(cls, config=None):
        """返回查询表单的HTML
        
        Args:
            config: 扩展当前的配置
        """
        return "<p>此扩展不需要查询参数</p>"
    
    @classmethod
    def execute_query(cls, params, config=None):
        """执行查询
        
        Args:
            params: 查询参数
            config: 扩展配置
        """
        raise NotImplementedError("扩展必须实现execute_query方法")
    
    @classmethod
    def validate_config(cls, config):
        """验证配置有效性
        
        Args:
            config: 要验证的配置
        
        Returns:
            (bool, str): (是否有效, 错误信息)
        """
        return True, "" 