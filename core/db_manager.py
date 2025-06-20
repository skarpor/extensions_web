"""
数据库管理器

提供动态管理数据库表的功能，允许创建、修改、删除表和数据。
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy import MetaData, Table, Column, Integer, String, Float, Boolean, Text, DateTime, func
from sqlalchemy import select, insert, update, delete
from sqlalchemy.schema import CreateTable, DropTable
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from config import settings
from core.logger import get_logger

logger = get_logger("db_manager")

# 支持的数据库类型
DB_TYPES = {
    "sqlite": {
        "sync_url": "sqlite:///{path}",
        "async_url": "sqlite+aiosqlite:///{path}",
    },
    "postgres": {
        "sync_url": "postgresql://{user}:{password}@{host}:{port}/{database}",
        "async_url": "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
    },
    "mysql": {
        "sync_url": "mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
        "async_url": "mysql+aiomysql://{user}:{password}@{host}:{port}/{database}",
    }
}

# 默认数据库配置
DEFAULT_DB_CONFIG = {
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
    "database": "postgres"
}

# 支持的列类型映射
COLUMN_TYPES = {
    "integer": Integer,
    "string": String,
    "varchar": String,
    "text": Text,
    "float": Float,
    "boolean": Boolean,
    "datetime": DateTime,
}

class DBManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = f"{settings.EXT_DB_DIR}/app.db", db_type: str = "sqlite"):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径或数据库名称
            db_type: 数据库类型，支持 sqlite, postgres, mysql
        """
        self.db_path = db_path
        self.db_type = db_type
        self.engine = None
        self.metadata = MetaData()
        self.tables = {}
        
        # 确保目录存在
        if db_type == "sqlite":
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        logger.info(f"数据库管理器初始化完成，数据库路径：{db_path}，数据库类型：{db_type}")
    
    def _get_connection_url(self, async_mode: bool = True) -> str:
        """获取数据库连接URL
        
        Args:
            async_mode: 是否使用异步模式
            
        Returns:
            数据库连接URL
        """
        if self.db_type == "sqlite":
            url_template = DB_TYPES[self.db_type]["async_url"] if async_mode else DB_TYPES[self.db_type]["sync_url"]
            return url_template.format(path=self.db_path)
        else:
            # 对于其他数据库类型，尝试从 settings 获取配置
            config = DEFAULT_DB_CONFIG
            
            # 尝试从 settings 获取配置
            if hasattr(settings, "DB_USER"):
                config["user"] = settings.DB_USER
            if hasattr(settings, "DB_PASSWORD"):
                config["password"] = settings.DB_PASSWORD
            if hasattr(settings, "DB_HOST"):
                config["host"] = settings.DB_HOST
            if hasattr(settings, "DB_PORT"):
                config["port"] = settings.DB_PORT
            if hasattr(settings, "DB_NAME"):
                config["database"] = settings.DB_NAME
                
            url_template = DB_TYPES[self.db_type]["async_url"] if async_mode else DB_TYPES[self.db_type]["sync_url"]
            return url_template.format(**config)
    
    async def initialize(self):
        """初始化数据库连接并加载现有表信息"""
        if not self.engine:
            url = self._get_connection_url()
            self.engine = create_async_engine(url, echo=True)
            
            # 加载现有表信息
            async with self.engine.begin() as conn:
                # await self.metadata.reflect(bind=conn)
                # 使用run_sync执行同步反射
                await conn.run_sync(self.metadata.reflect)

            # 缓存表对象
            for table_name, table in self.metadata.tables.items():
                self.tables[table_name] = table
                
            logger.info(f"数据库初始化完成，加载了 {len(self.tables)} 个表")
        return {"status": "success", "message": f"数据库初始化成功，类型：{self.db_type}，路径：{self.db_path}"}
    
    def _get_column_type(self, column_def: Dict) -> Any:
        """根据列定义获取列类型
        
        Args:
            column_def: 列定义字典
            
        Returns:
            SQLAlchemy列类型
        """
        type_name = column_def.get("type", "varchar")
        
        # 处理带长度的类型字符串，如"varchar(255)"
        length = None
        if isinstance(type_name, str) and "(" in type_name:
            import re
            match = re.match(r"(\w+)\((\d+)\)", type_name)
            if match:
                type_name = match.group(1)
                length = int(match.group(2))
        
        if type_name not in COLUMN_TYPES:
            raise ValueError(f"不支持的列类型: {type_name}")
        
        column_type = COLUMN_TYPES[type_name]
        
        # 处理特殊类型参数
        if type_name == "varchar":
            # 优先使用从类型字符串中提取的长度，其次使用单独提供的length属性
            if length:
                return column_type(length)
            elif "length" in column_def:
                return column_type(column_def["length"])
            else:
                return column_type(255)  # 默认长度
        
        return column_type()
    
    async def list_all_tables(self) -> List[Dict]:
        """获取所有表信息
        
        Returns:
            表信息列表，每个元素包含表名、表结构等基本信息
        """
        if not self.engine:
            await self.initialize()
            
        result = []
        for table_name, table in self.tables.items():
            # 获取记录数
            count = 0
            async with self.engine.connect() as conn:
                count_query = select(func.count()).select_from(table)
                count_result = await conn.execute(count_query)
                count = count_result.scalar()
            
            # 获取创建时间（可能需要从表中的特定字段获取）
            created_at = datetime.now()  # 默认使用当前时间
            
            result.append({
                "name": table_name,
                "display_name": table_name,
                "description": getattr(table, "comment", None),
                "record_count": count,
                "created_at": created_at,
                "updated_at": created_at
            })
        
        return result
    
    async def get_table_schema(self, table_name: str) -> Dict:
        """获取表结构
        
        Args:
            table_name: 表名
            
        Returns:
            表结构信息
        """
        if not self.engine:
            await self.initialize()
            
        if table_name not in self.tables:
            raise ValueError(f"表 {table_name} 不存在")
        
        table = self.tables[table_name]
        columns = []
        
        for column in table.columns:
            # 解析列类型
            column_type = str(column.type)
            type_name = column_type.lower()
            
            # 保留完整的类型信息（包括长度）
            if "varchar" in type_name:
                # 例如 "VARCHAR(255)" -> "varchar(255)"
                match = column_type.lower().replace(" ", "")
                type_name = match
            else:
                # 推断数据类型
                for known_type in COLUMN_TYPES.keys():
                    if known_type in type_name:
                        type_name = known_type
                        break
            
            # 获取额外属性
            columns.append({
                "name": column.name,
                "type": type_name,
                "primary_key": column.primary_key,
                "nullable": column.nullable,
                "unique": any(constraint.name and constraint.name.startswith("uq_") for constraint in column.constraints if hasattr(constraint, "name")),
                "default": str(column.default.arg) if column.default and column.default.arg else None,
                "comment": getattr(column, "comment", None)
            })
        
        # 创建SQL语句（用于展示）
        sql = str(CreateTable(table).compile(dialect=self.engine.dialect))
        
        return {
            "name": table_name,
            "columns": columns,
            "description": getattr(table, "comment", None),
            "sql": sql
        }
    
    async def table_exists(self, table_name: str) -> bool:
        """检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            表是否存在
        """
        if not self.engine:
            await self.initialize()
            
        return table_name in self.tables
    
    async def create_table(self, table_name: str, columns: List[Dict], description: Optional[str] = None) -> str:
        """创建表
        
        Args:
            table_name: 表名
            columns: 列定义列表
            description: 表描述
            
        Returns:
            创建的表名
        """
        if not self.engine:
            await self.initialize()
            
        # 检查表是否已存在
        if table_name in self.tables:
            raise ValueError(f"表 {table_name} 已存在")
        
        # 构建列对象
        table_columns = []
        for col in columns:
            col = dict(col)
            column_type = self._get_column_type(col)
            column_args = {
                "primary_key": col.get("primary_key", False),
                "nullable": col.get("nullable", True)
            }
            
            # 添加额外属性
            if col.get("unique", False):
                column_args["unique"] = True
            
            if "default" in col:
                column_args["default"] = col["default"]
                
            if "comment" in col:
                column_args["comment"] = col["comment"]
            
            table_columns.append(Column(col["name"], column_type, **column_args))
        
        # 创建表对象
        table_args = {}
        if description:
            table_args["comment"] = description
            
        table = Table(table_name, self.metadata, *table_columns, **table_args)
        
        # 在数据库中创建表
        async with self.engine.begin() as conn:
            await conn.execute(CreateTable(table))
        
        # 更新缓存
        self.tables[table_name] = table
        
        logger.info(f"创建表 {table_name} 成功")
        return table_name
    
    async def drop_table(self, table_name: str) -> bool:
        """删除表
        
        Args:
            table_name: 表名
            
        Returns:
            是否成功删除
        """
        if not self.engine:
            await self.initialize()
            
        if table_name not in self.tables:
            logger.warning(f"表 {table_name} 不存在，无法删除")
            return False
        
        table = self.tables[table_name]
        
        # 在数据库中删除表
        async with self.engine.begin() as conn:
            await conn.execute(DropTable(table))
        
        # 从缓存中删除表
        del self.tables[table_name]
        self.metadata.remove(table)
        
        logger.info(f"删除表 {table_name} 成功")
        return True
    
    async def alter_table1(self, table_name: str, columns: List[Dict], description: Optional[str] = None) -> bool:
        """修改表结构
        
        由于SQLAlchemy核心不直接支持ALTER TABLE，我们通过重新创建表来实现
        
        Args:
            table_name: 表名
            columns: 新的列定义列表
            description: 新的表描述
            
        Returns:
            是否成功修改
        """
        if not self.engine:
            await self.initialize()
            
        if table_name not in self.tables:
            logger.warning(f"表 {table_name} 不存在，无法修改")
            return False
        
        # 获取表的所有数据
        data = await self.execute_query(
            operation="select",
            table_name=table_name
        )
        
        # 创建临时表名
        temp_table_name = f"{table_name}_temp_{int(datetime.now().timestamp())}"
        
        try:
            # 创建新表
            async with self.engine.begin() as conn:
                # 构建列对象
                table_columns = []
                for col in columns:
                    col = dict(col)
                    column_type = self._get_column_type(col)
                    column_args = {
                        "primary_key": col.get("primary_key", False),
                        "nullable": col.get("nullable", True)
                    }
                    
                    # 添加额外属性
                    if col.get("unique", False):
                        column_args["unique"] = True
                    
                    if "default" in col:
                        column_args["default"] = col["default"]
                        
                    if "comment" in col:
                        column_args["comment"] = col["comment"]
                    
                    table_columns.append(Column(col["name"], column_type, **column_args))
                
                # 创建临时表对象
                table_args = {}
                if description:
                    table_args["comment"] = description
                    
                temp_table = Table(temp_table_name, MetaData(), *table_columns, **table_args)
                
                # 创建临时表
                await conn.execute(CreateTable(temp_table))
                
                # 复制数据到临时表
                column_names = [col["name"] for col in columns]
                existing_column_names = set([c.name for c in self.tables[table_name].columns])

                # 插入符合新表结构的数据
                for row in data:
                    filtered_row = {k: v for k, v in row.items() if k in column_names}
                    if filtered_row:
                        insert_stmt = insert(temp_table).values(**filtered_row)
                        await conn.execute(insert_stmt)
                
                # 删除原表
                await conn.execute(DropTable(self.tables[table_name]))
                
                # 重命名临时表为原表名
                if self.db_type == "sqlite":
                    # SQLite 不支持重命名表操作，需要创建新表并复制数据
                    final_table = Table(table_name, MetaData(), *table_columns, **table_args)
                    await conn.execute(CreateTable(final_table))
                    
                    # 查询临时表数据
                    select_stmt = select(temp_table)
                    result = await conn.execute(select_stmt)
                    temp_data = [dict(row._mapping) for row in result.fetchall()]
                    
                    # 复制到最终表
                    for row in temp_data:
                        insert_stmt = insert(final_table).values(**row)
                        await conn.execute(insert_stmt)
                    
                    # 删除临时表
                    await conn.execute(DropTable(temp_table))
                    
                    # 更新缓存
                    self.tables[table_name] = final_table
                    self.metadata.remove(self.tables[table_name])
                    self.metadata.add(final_table)
                else:
                    # 其他数据库可以直接重命名
                    rename_sql = f"ALTER TABLE {temp_table_name} RENAME TO {table_name}"
                    await conn.execute(text(rename_sql))
                    
                    # 更新缓存
                    self.tables[table_name] = temp_table
                    temp_table.name = table_name
                    self.metadata.remove(self.tables[table_name])
                    self.metadata.add(temp_table)
        
        except Exception as e:
            logger.error(f"修改表 {table_name} 结构失败: {str(e)}")
            raise
            # 尝试清理临时表
            try:
                async with self.engine.begin() as conn:
                    await conn.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))
            except:
                pass
            raise
        
        logger.info(f"修改表 {table_name} 结构成功")
        return True

    async def alter_table(self, table_name: str, columns: List[Dict], description: Optional[str] = None) -> bool:
        """修改表结构"""
        if not self.engine:
            await self.initialize()

        if table_name not in self.tables:
            logger.warning(f"表 {table_name} 不存在，无法修改")
            return False

        # 获取表的所有数据
        data = await self.execute_query(
            operation="select",
            table_name=table_name
        )

        # 创建临时表名
        temp_table_name = f"{table_name}_temp_{int(datetime.now().timestamp())}"

        try:
            # 创建列对象的函数
            def create_columns(col_definitions):
                new_columns = []
                for col in col_definitions:
                    col = dict(col)
                    column_type = self._get_column_type(col)
                    column_args = {
                        "primary_key": col.get("primary_key", False),
                        "nullable": col.get("nullable", True)
                    }

                    if col.get("unique", False):
                        column_args["unique"] = True

                    if "default" in col:
                        column_args["default"] = col["default"]

                    if "comment" in col:
                        column_args["comment"] = col["comment"]

                    new_columns.append(Column(col["name"], column_type, **column_args))
                return new_columns

            async with self.engine.begin() as conn:
                # 创建临时表的列
                temp_table_columns = create_columns(columns)

                # 创建临时表对象
                table_args = {}
                if description:
                    table_args["comment"] = description

                temp_table = Table(temp_table_name, MetaData(), *temp_table_columns, **table_args)

                # 创建临时表
                await conn.execute(CreateTable(temp_table))

                # 复制数据到临时表
                column_names = [dict(col)["name"] for col in columns]
                existing_column_names = set([c.name for c in self.tables[table_name].columns])

                for row in data:
                    filtered_row = {k: v for k, v in row.items() if k in column_names}
                    if filtered_row:
                        insert_stmt = insert(temp_table).values(**filtered_row)
                        await conn.execute(insert_stmt)

                # 删除原表
                await conn.execute(DropTable(self.tables[table_name]))

                if self.db_type == "sqlite":
                    # 为最终表创建全新的列对象
                    final_table_columns = create_columns(columns)
                    final_table = Table(table_name, MetaData(), *final_table_columns, **table_args)
                    await conn.execute(CreateTable(final_table))

                    # 查询临时表数据
                    select_stmt = select(temp_table)
                    result = await conn.execute(select_stmt)
                    temp_data = [dict(row._mapping) for row in result.fetchall()]

                    # 复制到最终表
                    for row in temp_data:
                        insert_stmt = insert(final_table).values(**row)
                        await conn.execute(insert_stmt)

                    # 删除临时表
                    await conn.execute(DropTable(temp_table))

                    # 更新缓存
                    # self.tables[table_name] = final_table
                    # self.metadata.remove(self.tables[table_name])
                    # self.metadata.add(final_table)
                    # 更新缓存 - 修正后的方式
                    self.tables[table_name] = final_table
                    # 移除旧的表引用（如果存在）
                    if table_name in self.metadata.tables:
                        self.metadata.remove(self.metadata.tables[table_name])
                    # 添加新表到元数据
                    final_table.metadata = self.metadata

                else:
                    # 其他数据库可以直接重命名
                    rename_sql = f"ALTER TABLE {temp_table_name} RENAME TO {table_name}"
                    await conn.execute(text(rename_sql))

                    # 更新缓存
                    self.tables[table_name] = temp_table
                    temp_table.name = table_name
                    if table_name in self.metadata.tables:
                        self.metadata.remove(self.metadata.tables[table_name])
                    temp_table.metadata = self.metadata

        except Exception as e:
            logger.error(f"修改表 {table_name} 结构失败: {str(e)}")
            # 尝试清理临时表
            try:
                async with self.engine.begin() as conn:
                    await conn.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))
            except:
                pass
            raise

        logger.info(f"修改表 {table_name} 结构成功")
        return True
    async def execute_query(self, operation: str, table_name: Optional[str] = None, 
                           data: Optional[Dict] = None, condition: Optional[Dict] = None,
                           sql: Optional[str] = None, params: Optional[Dict] = None,
                           limit: Optional[int] = None, offset: Optional[int] = None,
                           sort_by: Optional[str] = None, sort_desc: bool = False) -> Any:
        """执行统一查询
        
        Args:
            operation: 操作类型 (select/insert/update/delete/raw)
            table_name: 表名
            data: 数据字典 (用于insert/update)
            condition: 条件字典 (用于select/update/delete)
            sql: 原始SQL语句 (用于raw查询)
            params: SQL参数
            limit: 限制返回的行数
            offset: 跳过的行数
            sort_by: 排序字段
            sort_desc: 是否降序排序
            
        Returns:
            查询结果或影响的行数
        """
        if not self.engine:
            await self.initialize()
        
        result = None
        data = data or {}
        condition = condition or {}
        params = params or {}
        
        try:
            if operation == "raw" and sql:
                # 执行原始SQL
                async with self.engine.begin() as conn:
                    result = await conn.execute(text(sql), params)
                    if result.returns_rows:
                        return [dict(row._mapping) for row in result]
                    return {"affected_rows": result.rowcount}
            
            elif table_name and table_name in self.tables:
                table = self.tables[table_name]
                
                if operation == "select":
                    # 构建查询
                    query = select(table)
                    
                    # 添加条件
                    for key, value in condition.items():
                        if hasattr(table.c, key):
                            query = query.where(getattr(table.c, key) == value)
                    
                    # 添加排序
                    if sort_by and hasattr(table.c, sort_by):
                        if sort_desc:
                            query = query.order_by(getattr(table.c, sort_by).desc())
                        else:
                            query = query.order_by(getattr(table.c, sort_by))
                    
                    # 应用分页
                    if limit is not None:
                        query = query.limit(limit)
                    if offset is not None:
                        query = query.offset(offset)
                    
                    # 执行查询,
                    async with self.engine.connect() as conn:
                        result = await conn.execute(query)
                        print('result',result)
                        print('query',query)
                        return [dict(row._mapping) for row in result]
                
                elif operation == "insert" and data:
                    # 执行插入
                    async with self.engine.begin() as conn:
                        print(data)
                        # print(**data['data'])
                        result = await conn.execute(insert(table).values(**data))
                        return {"id": result.inserted_primary_key[0] if result.inserted_primary_key else None}
                
                elif operation == "update" and data:
                    # 构建更新
                    query = update(table).values(**data)
                    
                    # 添加条件
                    for key, value in condition.items():
                        if hasattr(table.c, key):
                            query = query.where(getattr(table.c, key) == value)
                    
                    # 执行更新
                    async with self.engine.begin() as conn:
                        result = await conn.execute(query)
                        return {"affected_rows": result.rowcount}
                
                elif operation == "delete":
                    # 构建删除
                    query = delete(table)
                    
                    # 添加条件
                    for key, value in condition.items():
                        if hasattr(table.c, key):
                            query = query.where(getattr(table.c, key) == value)
                    
                    # 执行删除
                    async with self.engine.begin() as conn:
                        result = await conn.execute(query)
                        return {"affected_rows": result.rowcount}
            
            raise ValueError(f"无法执行操作: {operation}, 表: {table_name}")
        
        except Exception as e:
            # 记录错误并重新抛出
            logger.error(f"数据库操作失败: {str(e)}")
            raise

    async def refresh(self):
        """
        刷新表
        :return:
        """
        self.engine=None
        await self.initialize()
        return {"status": "success", "message": f"数据库表刷新成功，类型：{self.db_type}"}

    async def shutdown(self):
        """
        :return:
        """
        self.engine=None

