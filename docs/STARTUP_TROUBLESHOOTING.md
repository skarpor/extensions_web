# 启动问题排查指南

## 🎯 问题现象

重启脚本执行后，通过 `tasklist | findstr python` 找不到进程，说明应用没有成功启动。

## 🔍 常见原因

### 1. Python环境问题
- Python路径不正确
- Python版本不兼容
- Python环境变量未设置

### 2. 脚本路径问题
- 主脚本文件不存在
- 工作目录不正确
- 文件路径包含特殊字符

### 3. 依赖包问题
- 缺少必要的Python包
- 包版本不兼容
- 虚拟环境未激活

### 4. 端口占用问题
- 8000端口被其他进程占用
- 防火墙阻止端口访问

### 5. 权限问题
- 没有执行权限
- 文件被占用或锁定

## 🛠️ 解决方案

### 方案1: 使用启动诊断
```bash
# 点击"启动诊断"按钮，或手动运行
data\startup_diagnosis.bat
```

**诊断内容：**
- 检查Python环境
- 验证项目文件
- 测试依赖包
- 检查端口占用
- 尝试启动测试

### 方案2: 使用可靠重启
```bash
# 点击"可靠重启"按钮，或手动运行
data\reliable_restart.bat
```

**重启流程：**
- 清理所有Python进程
- 释放端口占用
- 智能查找Python和脚本
- 尝试多种启动方式
- 验证启动结果

### 方案3: 手动排查

#### 步骤1: 检查Python
```bash
# 测试Python是否可用
python --version
python3 --version
D:\develop\python396\python.exe --version
```

#### 步骤2: 检查脚本文件
```bash
# 切换到项目目录
cd /d "G:\cursor_projects\extensions_web"

# 查看Python文件
dir *.py

# 检查主脚本是否存在
if exist app.py echo app.py存在
if exist main.py echo main.py存在
```

#### 步骤3: 检查依赖
```bash
# 检查关键依赖包
python -c "import fastapi; print('FastAPI OK')"
python -c "import uvicorn; print('Uvicorn OK')"
python -c "import sqlalchemy; print('SQLAlchemy OK')"
```

#### 步骤4: 检查端口
```bash
# 查看端口占用
netstat -ano | findstr :8000

# 如果端口被占用，杀死占用进程
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8000') do taskkill /pid %a /f
```

#### 步骤5: 手动启动
```bash
# 前台启动（用于调试）
cd /d "G:\cursor_projects\extensions_web"
python app.py

# 后台启动
start /B "" python app.py
```

## 📋 具体解决步骤

### 如果Python路径错误
1. 找到正确的Python路径：
   ```bash
   where python
   where python3
   ```

2. 更新脚本中的Python路径

3. 或者添加Python到PATH环境变量

### 如果脚本文件不存在
1. 确认主脚本文件名：
   ```bash
   dir *.py
   ```

2. 更新脚本中的文件名

3. 确保在正确的工作目录

### 如果依赖包缺失
1. 安装缺失的包：
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic
   ```

2. 或者从requirements.txt安装：
   ```bash
   pip install -r requirements.txt
   ```

### 如果端口被占用
1. 查找占用进程：
   ```bash
   netstat -ano | findstr :8000
   ```

2. 杀死占用进程：
   ```bash
   taskkill /pid <PID> /f
   ```

3. 或者修改应用端口配置

## 🎯 推荐的重启命令

### 基于你的环境
```bash
# 最简单的重启命令
TASKKILL /IM python.exe /F && cd /d "G:\cursor_projects\extensions_web" && python app.py

# 使用完整路径的重启命令
TASKKILL /IM python.exe /F && cd /d "G:\cursor_projects\extensions_web" && "D:\develop\python396\python.exe" app.py

# 后台启动的重启命令
TASKKILL /IM python.exe /F && cd /d "G:\cursor_projects\extensions_web" && start /B "" "D:\develop\python396\python.exe" app.py
```

### 分步执行（推荐）
```bash
# 第1步：停止进程
TASKKILL /IM python.exe /F

# 第2步：等待3秒
timeout /t 3 /nobreak

# 第3步：切换目录
cd /d "G:\cursor_projects\extensions_web"

# 第4步：启动应用
"D:\develop\python396\python.exe" app.py
```

## ⚠️ 注意事项

### 1. 路径问题
- 使用双引号包围包含空格的路径
- 使用绝对路径避免相对路径问题
- 确保路径分隔符正确（Windows使用反斜杠）

### 2. 启动方式
- 前台启动：直接运行，可以看到输出和错误
- 后台启动：使用 `start /B`，不阻塞命令行
- 服务启动：使用Windows服务或systemd

### 3. 调试技巧
- 先用前台启动调试问题
- 查看错误输出确定问题原因
- 使用日志文件记录启动过程

## 🚀 最佳实践

### 1. 创建启动脚本
```bash
# 创建 start_app.bat
@echo off
cd /d "G:\cursor_projects\extensions_web"
"D:\develop\python396\python.exe" app.py
pause
```

### 2. 创建重启脚本
```bash
# 创建 restart_app.bat
@echo off
TASKKILL /IM python.exe /F
timeout /t 3 /nobreak
cd /d "G:\cursor_projects\extensions_web"
start /B "" "D:\develop\python396\python.exe" app.py
echo 应用已重启
```

### 3. 设置环境变量
```bash
# 添加Python到PATH
set PATH=%PATH%;D:\develop\python396

# 设置项目目录
set PROJECT_DIR=G:\cursor_projects\extensions_web
```

现在你可以：
1. 使用"启动诊断"找出具体问题
2. 使用"可靠重启"尝试自动解决
3. 根据诊断结果手动修复问题
4. 使用推荐的重启命令

这样应该能解决启动问题！
