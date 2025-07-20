# Data Query System 2.0 - API接口文档

## 接口概览

本系统提供RESTful API接口，所有接口都基于HTTP协议，使用JSON格式进行数据交换。API遵循OpenAPI 3.0规范，支持Swagger UI在线文档。

### 基础信息
- **基础URL**: `http://localhost:8000/api`
- **API版本**: v1
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`
- **在线文档**: `http://localhost:8000/docs`

### 通用响应格式

#### 成功响应
```json
{
  "status": "success",
  "data": {},
  "message": "操作成功"
}
```

#### 错误响应
```json
{
  "status": "error",
  "detail": "错误详细信息",
  "code": "ERROR_CODE"
}
```

### 状态码说明
- `200` - 请求成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未授权
- `403` - 权限不足
- `404` - 资源不存在
- `422` - 数据验证失败
- `500` - 服务器内部错误

## 认证接口 (/api/auth)

### 用户登录
**POST** `/api/auth/login`

用户登录获取访问令牌。

#### 请求参数
```json
{
  "username": "admin",
  "password": "admin123"
}
```

#### 响应示例
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "nickname": "管理员",
    "is_active": true,
    "is_superuser": true
  }
}
```

### 获取令牌
**POST** `/api/auth/token`

OAuth2标准令牌获取接口。

#### 请求参数 (form-data)
- `username`: 用户名
- `password`: 密码
- `grant_type`: password

#### 响应示例
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "admin",
  "email": "admin@example.com",
  "nickname": "管理员"
}
```

### 用户登出
**POST** `/api/auth/logout`

用户登出，清除令牌。

#### 响应示例
```json
{
  "status_code": 200,
  "detail": "登出成功"
}
```

### 验证令牌
**POST** `/api/auth/test-token`

验证当前令牌有效性。

#### Headers
```
Authorization: Bearer <token>
```

#### 响应示例
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true
}
```

## 用户管理接口 (/api/users)

### 获取用户列表
**GET** `/api/users/`

获取系统中的用户列表（需要管理员权限）。

#### 查询参数
- `skip`: 跳过记录数 (默认: 0)
- `limit`: 返回记录数 (默认: 100)

#### 响应示例
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "nickname": "管理员",
    "is_active": true,
    "is_superuser": true,
    "created_at": "2023-01-01T00:00:00Z"
  }
]
```

### 创建用户
**POST** `/api/users/`

创建新用户（需要管理员权限）。

#### 请求参数
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "nickname": "新用户",
  "is_active": true,
  "is_superuser": false
}
```

### 获取当前用户信息
**GET** `/api/users/me`

获取当前登录用户的详细信息。

#### Headers
```
Authorization: Bearer <token>
```

#### 响应示例
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "nickname": "管理员",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2023-01-01T00:00:00Z",
  "last_login": "2023-01-01T12:00:00Z"
}
```

### 更新用户信息
**PUT** `/api/users/{user_id}`

更新指定用户信息。

#### 请求参数
```json
{
  "nickname": "新昵称",
  "email": "newemail@example.com",
  "is_active": true
}
```

## 扩展管理接口 (/api/extensions)

### 获取扩展列表
**GET** `/api/extensions/`

获取所有扩展的列表。

#### 查询参数
- `skip`: 跳过记录数
- `limit`: 返回记录数
- `enabled`: 是否启用 (true/false)

#### 响应示例
```json
[
  {
    "id": "example-extension",
    "name": "示例扩展",
    "description": "这是一个示例扩展",
    "enabled": true,
    "execution_mode": "manual",
    "has_config_form": true,
    "has_query_form": true,
    "show_in_home": false,
    "entry_point": "/query/example-extension",
    "creator_id": 1,
    "created_at": "2023-01-01T00:00:00Z"
  }
]
```

### 获取扩展详情
**GET** `/api/extensions/{extension_id}`

获取指定扩展的详细信息。

#### 响应示例
```json
{
  "id": "example-extension",
  "name": "示例扩展",
  "description": "这是一个示例扩展",
  "enabled": true,
  "config": {
    "api_key": "***",
    "base_url": "https://api.example.com",
    "timeout": 30
  },
  "document": {
    "docs": "扩展模块说明",
    "functions": {
      "execute_query": "执行查询的方法说明",
      "get_config_form": "获取配置表单的方法说明"
    }
  }
}
```

### 创建扩展
**POST** `/api/extensions/`

创建新的扩展。

#### 请求参数 (multipart/form-data)
- `name`: 扩展名称
- `description`: 扩展描述
- `file`: 扩展脚本文件 (.py)

#### 响应示例
```json
{
  "id": "new-extension-id",
  "name": "新扩展",
  "message": "扩展创建成功"
}
```

### 更新扩展
**PUT** `/api/extensions/{extension_id}`

更新扩展配置。

#### 请求参数
```json
{
  "name": "更新后的扩展名",
  "description": "更新后的描述",
  "enabled": true,
  "config": {
    "api_key": "new-api-key",
    "timeout": 60
  }
}
```

### 删除扩展
**DELETE** `/api/extensions/{extension_id}`

删除指定扩展。

#### 响应示例
```json
{
  "message": "扩展删除成功"
}
```

### 获取扩展配置表单
**GET** `/api/extensions/{extension_id}/config`

获取扩展的配置表单HTML。

#### 响应示例
```json
{
  "config_form": "<div class=\"mb-3\">...</div>",
  "config": {
    "api_key": "current-value",
    "timeout": 30
  }
}
```

### 获取扩展查询表单
**GET** `/api/extensions/{extension_id}/query`

获取扩展的查询表单HTML。

#### 响应示例
```json
{
  "query_form": "<div class=\"mb-3\">...</div>"
}
```

### 执行扩展查询
**POST** `/query/{extension_id}`

执行指定扩展的查询功能。

#### 请求参数 (multipart/form-data)
- 查询表单中定义的参数
- 可选的文件上传

#### 响应示例
```json
{
  "query_params": {
    "keyword": "test",
    "limit": 10
  },
  "config_used": {
    "base_url": "https://api.example.com",
    "timeout": 30
  },
  "data": [
    {"id": 1, "name": "结果1"},
    {"id": 2, "name": "结果2"}
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "page_size": 10
  }
}
```

## 文件管理接口 (/api/files)

### 上传文件
**POST** `/api/files/upload`

上传文件到系统。

#### 请求参数 (multipart/form-data)
- `file`: 要上传的文件
- `path`: 存储路径 (可选，默认为根目录)

#### 响应示例
```json
{
  "id": 1,
  "filename": "document.pdf",
  "filepath": "/uploads/",
  "filetype": "application/pdf",
  "filesize": 1024000,
  "hash": "sha256hash",
  "owner_id": 1,
  "created_at": "2023-01-01T00:00:00Z"
}
```

### 获取文件列表
**GET** `/api/files/`

获取用户的文件列表。

#### 查询参数
- `path`: 目录路径 (默认: "/")
- `skip`: 跳过记录数
- `limit`: 返回记录数

#### 响应示例
```json
{
  "files": [
    {
      "id": 1,
      "filename": "document.pdf",
      "filepath": "/uploads/",
      "filetype": "application/pdf",
      "filesize": 1024000,
      "created_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### 下载文件
**GET** `/api/files/{file_id}/download`

下载指定文件。

#### 响应
返回文件的二进制内容，Content-Type根据文件类型设置。

### 删除文件
**DELETE** `/api/files/{file_id}`

删除指定文件。

#### 查询参数
- `path`: 文件路径

#### 响应示例
```json
{
  "message": "文件删除成功"
}
```

### 创建目录
**POST** `/api/files/mkdir`

创建新目录。

#### 请求参数
```json
{
  "path": "/documents",
  "name": "new-folder"
}
```

## 聊天接口 (/api/chat)

### 获取聊天列表
**GET** `/api/chat/`

获取用户的聊天列表。

#### 响应示例
```json
[
  {
    "id": 1,
    "title": "聊天室1",
    "chat_type": "private",
    "created_at": "2023-01-01T00:00:00Z",
    "last_message": {
      "content": "最后一条消息",
      "created_at": "2023-01-01T12:00:00Z"
    }
  }
]
```

### 创建聊天
**POST** `/api/chat/`

创建新的聊天。

#### 请求参数
```json
{
  "title": "新聊天",
  "chat_type": "private"
}
```

### 获取聊天消息
**GET** `/api/chat/{chat_id}/messages`

获取指定聊天的消息历史。

#### 查询参数
- `skip`: 跳过消息数
- `limit`: 返回消息数

#### 响应示例
```json
[
  {
    "id": 1,
    "content": "消息内容",
    "message_type": "text",
    "sender_id": 1,
    "chat_id": 1,
    "created_at": "2023-01-01T00:00:00Z"
  }
]
```

### 发送消息
**POST** `/api/chat/{chat_id}/messages`

发送新消息到聊天。

#### 请求参数
```json
{
  "content": "消息内容",
  "message_type": "text"
}
```

## 数据库管理接口 (/api/db)

### 获取数据库列表
**GET** `/api/db/databases`

获取可用的数据库列表。

#### 响应示例
```json
[
  {
    "name": "main",
    "type": "sqlite",
    "status": "connected"
  }
]
```

### 获取表列表
**GET** `/api/db/tables`

获取数据库中的表列表。

#### 响应示例
```json
[
  {
    "name": "users",
    "row_count": 10,
    "columns": 8
  },
  {
    "name": "extensions",
    "row_count": 5,
    "columns": 12
  }
]
```

### 获取表结构
**GET** `/api/db/tables/{table_name}/schema`

获取指定表的结构定义。

#### 响应示例
```json
{
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "INTEGER",
      "nullable": false,
      "primary_key": true
    },
    {
      "name": "username",
      "type": "VARCHAR(50)",
      "nullable": false,
      "unique": true
    }
  ]
}
```

### 执行SQL查询
**POST** `/api/db/query`

执行SQL查询语句。

#### 请求参数
```json
{
  "sql": "SELECT * FROM users LIMIT 10",
  "params": {}
}
```

#### 响应示例
```json
{
  "columns": ["id", "username", "email"],
  "data": [
    [1, "admin", "admin@example.com"],
    [2, "user", "user@example.com"]
  ],
  "row_count": 2,
  "execution_time": 0.001
}
```

## 调度器接口 (/api/scheduler)

### 获取任务列表
**GET** `/api/scheduler/jobs`

获取所有调度任务。

#### 响应示例
```json
[
  {
    "id": "job_1",
    "name": "定时任务1",
    "func": "my_function",
    "trigger": "cron",
    "next_run_time": "2023-01-01T12:00:00Z",
    "status": "running"
  }
]
```

### 创建任务
**POST** `/api/scheduler/jobs`

创建新的调度任务。

#### 请求参数
```json
{
  "name": "新任务",
  "func": "function_name",
  "trigger": "cron",
  "cron_expression": "0 12 * * *",
  "args": [],
  "kwargs": {}
}
```

### 暂停/恢复任务
**POST** `/api/scheduler/jobs/{job_id}/pause`
**POST** `/api/scheduler/jobs/{job_id}/resume`

暂停或恢复指定任务。

### 删除任务
**DELETE** `/api/scheduler/jobs/{job_id}`

删除指定任务。

## WebSocket接口 (/api/ws)

### 聊天WebSocket
**WebSocket** `/api/ws/chat/{chat_id}`

实时聊天WebSocket连接。

#### 连接参数
- `token`: JWT令牌 (查询参数)

#### 消息格式
```json
{
  "type": "message",
  "data": {
    "content": "消息内容",
    "message_type": "text"
  }
}
```

### 系统通知WebSocket
**WebSocket** `/api/ws/notifications`

系统通知WebSocket连接。

#### 通知类型
- `extension_status`: 扩展状态变更
- `file_upload`: 文件上传完成
- `task_complete`: 任务执行完成

## 错误处理

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `INVALID_CREDENTIALS` | 无效的登录凭证 | 检查用户名和密码 |
| `TOKEN_EXPIRED` | 令牌已过期 | 重新登录获取新令牌 |
| `PERMISSION_DENIED` | 权限不足 | 联系管理员获取权限 |
| `EXTENSION_NOT_FOUND` | 扩展不存在 | 检查扩展ID是否正确 |
| `FILE_TOO_LARGE` | 文件过大 | 减小文件大小或联系管理员 |
| `INVALID_FILE_TYPE` | 不支持的文件类型 | 使用支持的文件格式 |

### 调试技巧

1. **查看详细错误信息**: 检查响应中的 `detail` 字段
2. **验证请求格式**: 确保Content-Type和请求体格式正确
3. **检查认证状态**: 验证令牌是否有效且未过期
4. **查看API文档**: 访问 `/docs` 获取最新的接口文档
5. **检查日志**: 查看服务器日志获取更多错误信息

## 版本更新

### v2.0.0 (当前版本)
- 重构扩展系统架构
- 新增WebSocket实时通信
- 优化文件管理功能
- 增强安全性和性能

### 向后兼容性
- API接口保持向后兼容
- 数据库结构自动迁移
- 扩展脚本格式兼容v1.x

---

*API文档最后更新: 2025-07-09*
