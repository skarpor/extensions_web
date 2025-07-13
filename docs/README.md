# 环境

> python3.9+,vue3

```powershell
# 安装依赖
pip install -r requirements.txt

# 启动后端
python main.py

# 启动前端
cd frontend;npm i;npm run dev
```





# Data Query System 2.0

这是一个基于FastAPI的数据查询系统，支持文件管理、用户管理、扩展管理等功能。

## 项目结构

```
.
├── new_app/                    # 新版本应用目录
│   ├── api/                   # API路由
│   ├── core/                  # 核心功能
│   ├── db/                    # 数据库相关
│   ├── models/               # 数据模型
│   ├── schemas/              # Pydantic模型
│   └── utils/                # 工具函数
├── migrations/               # 数据库迁移文件
├── scripts/                 # 脚本文件
│   ├── migrate_data.py     # 数据迁移脚本
│   ├── test_migration.py   # 迁移测试脚本
│   └── run_migration.py    # 迁移运行脚本
├── static/                 # 静态文件
├── templates/              # 模板文件
├── uploads/               # 上传文件目录
├── alembic.ini            # Alembic配置文件
├── main.py               # 应用入口
├── config.py             # 配置文件
└── requirements.txt      # 依赖文件
```

## 迁移步骤

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 创建新数据库：
```bash
alembic upgrade head
```

3. 运行数据迁移：
```bash
python scripts/run_migration.py
```

4. 启动应用：
```bash
python main.py
```

## 主要功能

- 用户管理：注册、登录、权限控制
- 文件管理：上传、下载、删除文件
- 扩展管理：安装、启用、禁用扩展
- 设置管理：系统设置、用户设置
- 聊天功能：实时聊天、消息历史
- 日志管理：系统日志记录和查看

## API文档

启动应用后，访问 http://localhost:8000/docs 查看API文档。

## 开发说明

1. 数据库迁移：
```bash
# 创建迁移
alembic revision --autogenerate -m "migration message"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

2. 运行测试：
```bash
pytest
```

## 注意事项

1. 确保已备份原数据库
2. 迁移前检查数据一致性
3. 迁移后验证数据完整性
4. 保持日志记录完整

## 许可证

MIT License 