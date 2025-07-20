# 通用进程管理器使用示例

## 基本用法

### 1. 启动Python应用
```bash
# 启动main.py，检查8000端口
python parent_process.py start python main.py --port 8000

# 启动FastAPI应用，检查URL
python parent_process.py start uvicorn main:app --host 0.0.0.0 --port 8000 --url http://localhost:8000/

# 启动Django应用
python parent_process.py start python manage.py runserver 0.0.0.0:8000 --port 8000
```

### 2. 启动Node.js应用
```bash
# 启动Express应用
python parent_process.py start node server.js --port 3000

# 启动Next.js应用
python parent_process.py start npm run start --port 3000
```

### 3. 启动其他应用
```bash
# 启动Nginx
python parent_process.py start nginx -g "daemon off;" --port 80

# 启动Redis
python parent_process.py start redis-server --port 6379

# 启动自定义脚本
python parent_process.py start ./my_script.sh --cwd /path/to/script
```

## 高级用法

### 1. 自定义配置
```bash
# 设置工作目录和环境变量
python parent_process.py start python app.py \
  --cwd /path/to/app \
  --env DEBUG=1 \
  --env PORT=8080 \
  --port 8080

# 设置重启参数
python parent_process.py start python app.py \
  --restart-delay 5 \
  --max-restart 10 \
  --no-auto-restart
```

### 2. 使用配置文件
```bash
# 保存配置
python parent_process.py start python main.py --port 8000 --save-config my_app.json

# 从配置文件启动
python parent_process.py start --config my_app.json
```

### 3. 进程控制
```bash
# 重启进程
python parent_process.py restart

# 强制重启（杀死所有相关进程）
python parent_process.py force-restart

# 停止进程
python parent_process.py stop

# 强制停止
python parent_process.py force-stop

# 动态更新配置
python parent_process.py config '{"restart_delay": 10, "max_restart_attempts": 5}'
```

## 配置文件示例

### FastAPI应用配置 (fastapi_config.json)
```json
{
  "command": "uvicorn",
  "args": ["main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
  "cwd": "/path/to/fastapi/app",
  "check_port": 8000,
  "check_url": "http://localhost:8000/health",
  "restart_delay": 3,
  "auto_restart": true,
  "max_restart_attempts": 10,
  "env": {
    "DEBUG": "1",
    "DATABASE_URL": "sqlite:///./app.db"
  }
}
```

### Node.js应用配置 (nodejs_config.json)
```json
{
  "command": "node",
  "args": ["server.js"],
  "cwd": "/path/to/nodejs/app",
  "check_port": 3000,
  "restart_delay": 2,
  "auto_restart": true,
  "max_restart_attempts": -1,
  "env": {
    "NODE_ENV": "production",
    "PORT": "3000"
  }
}
```

### Docker应用配置 (docker_config.json)
```json
{
  "command": "docker",
  "args": ["run", "--rm", "-p", "8080:80", "nginx:alpine"],
  "check_port": 8080,
  "restart_delay": 5,
  "auto_restart": true,
  "max_restart_attempts": 5
}
```

## 集成到现有项目

### 1. 修改重启脚本
将原来的重启脚本改为：
```batch
@echo off
echo 通过父进程重启...
python parent_process.py restart
```

### 2. 修改启动脚本
```batch
@echo off
echo 启动应用管理器...
python parent_process.py start python main.py --port 8000 --save-config app_config.json
```

### 3. API集成
在你的API中添加重启端点：
```python
@app.post("/api/system/restart")
async def restart_app():
    import subprocess
    subprocess.run(["python", "parent_process.py", "restart"])
    return {"message": "重启请求已发送"}
```

## 监控和日志

进程管理器会输出详细的日志信息：
- `[父进程]` - 管理器本身的日志
- `[子进程]` - 被管理进程的输出

你可以将输出重定向到文件：
```bash
python parent_process.py start python main.py --port 8000 > app.log 2>&1 &
```

## 故障排除

### 1. 进程启动失败
- 检查命令和参数是否正确
- 检查工作目录是否存在
- 检查环境变量是否正确设置

### 2. 端口检查失败
- 确认端口号正确
- 检查防火墙设置
- 确认应用确实在监听该端口

### 3. 重启循环
- 检查应用日志找出崩溃原因
- 调整 `max_restart_attempts` 限制重启次数
- 使用 `--no-auto-restart` 禁用自动重启进行调试

这个增强版的进程管理器现在可以管理任何类型的应用程序，提供了丰富的配置选项和控制命令！
