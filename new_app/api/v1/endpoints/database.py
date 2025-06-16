"""
统一数据库API路由模块

提供用于管理统一数据库的RESTful API端点，包括表管理和数据操作。
这些API允许前端对数据库进行CRUD操作，同时确保安全和权限控制。
"""

import json
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from new_app.core.auth import get_current_active_user, RoleChecker, PermissionChecker
from new_app.core.db_manager import DBManager
from new_app.schemas.database import (
    TableSchema, 
    TableInfo, 
    ColumnInfo, 
    TableDataResponse,
    TableDataCreate,
    TableDataUpdate
)
from new_app.models.user import User

router = APIRouter()

# 初始化数据库管理器
db_manager = DBManager()

# 权限检查器
manage_database = PermissionChecker(["manage_database"])
view_database = PermissionChecker(["view_database"])

# --------------
# 表管理API
# --------------

@router.post("/initialize")
async def initialize_database(
    request: Request,
    # current_user: User = Depends(get_current_active_user)
):
    """
    初始化数据库连接
    
    参数:
        db_type: 数据库类型 (sqlite, postgres, mysql)
        db_path: 数据库路径 (对于sqlite是文件路径，对于其他数据库可选)
    
    返回:
        初始化状态消息
    """
    try:
        global db_manager
        # db_type和db_path从params中获取
        db_type = request.query_params.get("db_type")
        db_path = request.query_params.get("db_path")
        db_manager = DBManager(db_type=db_type, db_path=db_path)
        result = await db_manager.initialize()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库初始化失败: {str(e)}")

@router.get("/tables", response_model=List[TableInfo])
async def list_tables(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有表的列表
    """
    try:
        tables = await db_manager.list_all_tables()
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")


@router.post("/tables", status_code=201)
async def create_table(
    table_name: str = Body(..., description="表名"),
    schema: TableSchema = Body(..., description="表结构定义"),
    # current_user: User = Depends(manage_database)
):
    """
    创建新表
    """
    try:
        await db_manager.create_table(table_name, schema.columns, schema.description)
        return {"message": f"表 {table_name} 创建成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建表失败: {str(e)}")


@router.get("/tables/{table_name}/schema", response_model=Dict[str, Any])
async def get_table_schema(
    table_name: str = Path(..., description="表名"),
    # current_user: User = Depends(get_current_active_user)
):
    """
    获取指定表的结构定义
    """
    try:
        schema = await db_manager.get_table_schema(table_name)
        return schema
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表结构失败: {str(e)}")


@router.put("/tables/{table_name}", status_code=200)
async def update_table(
    table_name: str = Path(..., description="表名"),
    schema: TableSchema = Body(..., description="表结构定义"),
    # current_user: User = Depends(manage_database)
):
    """
    更新表结构
    """
    try:
        await db_manager.alter_table(table_name, schema.columns, schema.description)
        return {"message": f"表 {table_name} 更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新表失败: {str(e)}")


@router.delete("/tables/{table_name}", status_code=200)
async def delete_table(
    table_name: str = Path(..., description="表名"),
    # current_user: User = Depends(manage_database)
):
    """
    删除指定表
    """
    try:
        await db_manager.drop_table(table_name)
        return {"message": f"表 {table_name} 删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除表失败: {str(e)}")


# --------------
# 数据操作API
# --------------

@router.get("/tables/{table_name}/data", response_model=TableDataResponse)
async def get_table_data(
    table_name: str = Path(..., description="表名"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=100, description="每页记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    sort_desc: bool = Query(False, description="是否降序排序"),
    # current_user: User = Depends(get_current_active_user)
):
    """
    获取表数据，支持分页、搜索和排序
    """
    try:
        # 计算偏移量
        offset = (page - 1) * per_page
        
        # 准备条件
        condition = {}
        if search:
            # 这里需要实现搜索逻辑，但需要根据具体数据库实现
            # 简化处理
            pass
            
        # 执行查询
        query_result = await db_manager.execute_query(
            operation="select",
            table_name=table_name,
            condition=condition,
            limit=per_page,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        
        # 获取总记录数
        count_query = await db_manager.execute_query(
            operation="raw",
            sql=f"SELECT COUNT(*) as total FROM {table_name}"
        )
        
        total = count_query[0]["total"] if count_query else 0
        
        # 构建响应
        result = {
            "items": query_result,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise #HTTPException(status_code=500, detail=f"获取表数据失败: {str(e)}")


@router.post("/tables/{table_name}/data", status_code=201, response_model=Dict[str, Any])
async def create_table_record(
    table_name: str = Path(..., description="表名"),
    data: Dict[str, Any] = Body(..., description="记录数据"),
    # current_user: User = Depends(manage_database)
):
    """
    在表中创建新记录,如果主键存在，则更新，否则插入
    """
    try:
        # 获取表结构，找出主键
        schema = await db_manager.get_table_schema(table_name)
        primary_key = next((col["name"] for col in schema["columns"] if col["primary_key"]), None)
        
        if not primary_key:
            raise ValueError(f"表 {table_name} 没有主键，无法创建记录")
        
        # 构建条件
        condition = {primary_key: data.get(primary_key)}
        
        # 执行查询
        result = await db_manager.execute_query(
            operation="select",
            table_name=table_name,
            condition=condition
        )
        if result:
            # 更新
            await db_manager.execute_query(
                operation="update",
                table_name=table_name,
                data=data.get("data")
            )
        else:
            # 插入
            await db_manager.execute_query(
                operation="insert",
                table_name=table_name,
                data=data.get("data")
            )
        return {"message": f"记录 {data.get(primary_key)} 创建成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建记录失败: {str(e)}")


@router.get("/tables/{table_name}/data/{record_id}", response_model=Dict[str, Any])
async def get_table_record(
    table_name: str = Path(..., description="表名"),
    record_id: Union[int, str] = Path(..., description="记录ID"),
    # current_user: User = Depends(view_database)
):
    """
    获取表中特定记录
    """
    try:
        # 获取表结构，找出主键
        schema = await db_manager.get_table_schema(table_name)
        primary_key = next((col["name"] for col in schema["columns"] if col["primary_key"]), None)
        
        if not primary_key:
            raise ValueError(f"表 {table_name} 没有主键，无法按ID查询")
        
        # 构建条件
        condition = {primary_key: record_id}
        
        # 执行查询
        result = await db_manager.execute_query(
            operation="select",
            table_name=table_name,
            condition=condition
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"记录 {record_id} 不存在")
            
        return result[0]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")


@router.put("/tables/{table_name}/data/{record_id}", response_model=Dict[str, Any])
async def update_table_record(
    table_name: str = Path(..., description="表名"),
    record_id: Union[int, str] = Path(..., description="记录ID"),
    data: Dict[str, Any] = Body(..., description="更新数据"),
    # current_user: User = Depends(manage_database)
):
    """
    更新表中特定记录
    """
    try:
        # 获取表结构，找出主键
        schema = await db_manager.get_table_schema(table_name)
        primary_key = next((col["name"] for col in schema["columns"] if col["primary_key"]), None)
        
        if not primary_key:
            raise ValueError(f"表 {table_name} 没有主键，无法按ID更新")
        
        # 构建条件
        condition = {primary_key: record_id}
        
        # 执行更新
        result = await db_manager.execute_query(
            operation="update",
            table_name=table_name,
            data=data,
            condition=condition
        )
        
        if result.get("affected_rows", 0) == 0:
            raise HTTPException(status_code=404, detail=f"记录 {record_id} 不存在或未更改")
            
        # 获取更新后的记录
        updated = await db_manager.execute_query(
            operation="select",
            table_name=table_name,
            condition=condition
        )
        
        return {"message": f"记录 {record_id} 更新成功", "record": updated[0] if updated else None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新记录失败: {str(e)}")


@router.delete("/tables/{table_name}/data/{record_id}", status_code=200)
async def delete_table_record(
    table_name: str = Path(..., description="表名"),
    record_id: Union[int, str] = Path(..., description="记录ID"),
    # current_user: User = Depends(manage_database)
):
    """
    删除表中特定记录
    """
    try:
        # 获取表结构，找出主键
        schema = await db_manager.get_table_schema(table_name)
        primary_key = next((col["name"] for col in schema["columns"] if col["primary_key"]), None)
        
        if not primary_key:
            raise ValueError(f"表 {table_name} 没有主键，无法按ID删除")
        
        # 构建条件
        condition = {primary_key: record_id}
        
        # 执行删除
        result = await db_manager.execute_query(
            operation="delete",
            table_name=table_name,
            condition=condition
        )
        
        if result.get("affected_rows", 0) == 0:
            raise HTTPException(status_code=404, detail=f"记录 {record_id} 不存在")
            
        return {"message": f"记录 {record_id} 删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除记录失败: {str(e)}")


# --------------
# 高级查询API
# --------------

@router.post("/tables/{table_name}/query", response_model=Dict[str, Any])
async def execute_custom_query(
    table_name: str = Path(..., description="表名"),
    query: Dict[str, Any] = Body(..., description="自定义查询条件"),
    # current_user: User = Depends(view_database)
):
    """
    执行自定义查询，支持复杂条件和聚合操作
    """
    try:
        result = await db_manager.execute_query(
            operation="raw",
            table_name=table_name,
            sql=query.get("sql"),
            params=query.get("params")
        )
        return {"data": result, "count": len(result) if isinstance(result, list) else 0}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行查询失败: {str(e)}")


@router.post("/tables/{table_name}/bulk", status_code=201)
async def bulk_insert_data(
    table_name: str = Path(..., description="表名"),
    data: List[Dict[str, Any]] = Body(..., description="批量插入的数据列表"),
    # current_user: User = Depends(manage_database)
):
    """
    批量插入数据到指定表
    查询主键，如果主键存在，则更新，否则插入
    """
    try:
        # 获取表结构，找出主键
        schema = await db_manager.get_table_schema(table_name)
        primary_key = next((col["name"] for col in schema["columns"] if col["primary_key"]), None)
        
        if not primary_key:
            raise ValueError(f"表 {table_name} 没有主键，无法批量插入")
        
        inserted_count = 0
        for item in data:
            # 构建条件
            condition = {primary_key: item[primary_key]}
            
            # 执行查询
            result = await db_manager.execute_query(
                operation="select",
                table_name=table_name,
                condition=condition
            )
            
            if result:
                # 更新
                await db_manager.execute_query(
                    operation="update",
                    table_name=table_name,
                    data=item,
                    condition=condition
                )
            else:
                # 插入
                await db_manager.execute_query(
                    operation="insert",
                    table_name=table_name,
                    data=item
                )
            inserted_count += 1
            
        return {"message": f"成功插入 {inserted_count} 条记录"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量插入失败: {str(e)}")


@router.post("/tables/{table_name}/import", status_code=201)
async def import_table_data(
    table_name: str = Path(..., description="表名"),
    file: UploadFile = File(..., description="要导入的CSV或JSON文件"),
    # current_user: User = Depends(manage_database)
):
    """
    从CSV或JSON文件导入数据到表
    """
    try:
        file_content = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == 'json':
            data = json.loads(file_content)
            if not isinstance(data, list):
                raise HTTPException(status_code=400, detail="JSON文件必须包含数据对象的数组")
        elif file_extension == 'csv':
            # 处理CSV导入
            import csv
            import io
            
            content = file_content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            data = [row for row in csv_reader]
        else:
            raise HTTPException(status_code=400, detail="只支持CSV或JSON文件")
        
        if not data:
            raise HTTPException(status_code=400, detail="文件不包含有效数据")
        
        # 批量插入数据，查询主键，如果主键存在，则更新，否则插入
        inserted_count = 0
        for item in data:
            # 获取表结构，找出主键
            schema = await db_manager.get_table_schema(table_name)
            primary_key = next((col["name"] for col in schema["columns"] if col["primary_key"]), None)
            
            if not primary_key:
                raise ValueError(f"表 {table_name} 没有主键，无法批量插入")
            
            # 构建条件
            condition = {primary_key: item[primary_key]}
            
            # 执行查询
            result = await db_manager.execute_query(
                operation="select",
                table_name=table_name,
                condition=condition
            )
            
            if result:
                # 更新
                await db_manager.execute_query(
                    operation="update",
                    table_name=table_name,
                    data=item,
                    condition=condition
                )
            else:
                # 插入
                await db_manager.execute_query(
                    operation="insert",
                    table_name=table_name,
                    data=item
                )
            inserted_count += 1
            
        return {"message": f"成功导入 {inserted_count} 条记录"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON格式无效")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码无效，请使用UTF-8编码")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入数据失败: {str(e)}")


@router.get("/tables/{table_name}/export")
async def export_table_data(
    table_name: str = Path(..., description="表名"),
    format: str = Query("json", description="导出格式，支持json或csv"),
    # current_user: User = Depends(view_database)
):
    """
    导出表数据为JSON或CSV格式
    """
    try:
        if format.lower() not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="只支持json或csv格式")
        
        # 获取所有数据
        data = await db_manager.execute_query(
            operation="select",
            table_name=table_name
        )
        
        if format.lower() == "json":
            return JSONResponse(content=data)
        else:
            import csv
            import io
            
            if not data:
                return JSONResponse(content={"message": "表中没有数据"})
                
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            response = JSONResponse(content={"csv_data": output.getvalue()})
            response.headers["Content-Disposition"] = f"attachment; filename={table_name}.csv"
            return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}") 