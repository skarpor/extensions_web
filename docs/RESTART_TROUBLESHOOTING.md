# 重启问题排查指南

## 🎯 问题现象

执行重启脚本后，通过 `tasklist | findstr python` 没有找到Python进程，说明新进程没有成功启动。

## 🔍 可能的原因

### 1. 脚本路径问题
- **问题**：脚本中的文件路径不正确
- **检查**：确认 `app.py` 文件是否存在
- **解决**：使用正确的脚本文件名

### 2. Python路径问题
- **问题**：Python可执行文件路径错误
- **检查**：确认Python路径是否正确
- **解决**：使用完整的绝对路径

### 3. 工作目录问题
- **问题**：启动时的工作目录不正确
- **检查**：确认 `cd` 命令是否正确
- **解决**：使用正确的项目目录

### 4. 权限问题
- **问题**：没有足够的权限启动进程
- **检查**：是否有执行权限
- **解决**：以管理员身份运行

### 5. 依赖问题
- **问题**：Python环境或依赖包缺失
- **检查**：手动运行Python命令是否正常
- **解决**：安装缺失的依赖

## 🔧 排查步骤

### 步骤1：检查当前进程
```bash
# 检查是否有Python进程在运行
tasklist | findstr python

# 如果有进程，记录PID
tasklist /fi "imagename eq python.exe"
```

### 步骤2：手动测试启动命令
```bash
# 切换到项目目录
cd /d "G:\cursor_projects\extensions_web"

# 手动启动应用
"D:\develop\python396\python.exe" "app.py"
```

### 步骤3：检查文件是否存在
```bash
# 检查Python可执行文件
dir "D:\develop\python396\python.exe"

# 检查应用脚本文件
dir "G:\cursor_projects\extensions_web\app.py"

# 检查当前目录
cd
```

### 步骤4：使用测试脚本
```bash
# 运行测试脚本
data\test_restart.bat

# 或运行简单重启脚本
data\simple_restart.bat
```

## 🛠️ 修复方案

### 方案1：修复脚本路径
```batch
@echo off
echo 修复版重启脚本...

REM 显示当前状态
echo 当前目录: %CD%
echo Python路径检查:
if exist "D:\develop\python396\python.exe" (
    echo Python路径正确
) else (
    echo Python路径错误，请检查
    pause
    exit
)

echo 脚本文件检查:
if exist "G:\cursor_projects\extensions_web\app.py" (
    echo 脚本文件存在
) else (
    echo 脚本文件不存在，请检查
    pause
    exit
)

REM 停止进程
echo 停止Python进程...
TASKKILL /IM python.exe /F >nul 2>&1

REM 等待
timeout /t 3 /nobreak >nul

REM 启动新进程
echo 启动新进程...
cd /d "G:\cursor_projects\extensions_web"
start "" "D:\develop\python396\python.exe" "app.py"

echo 重启完成
```

### 方案2：使用相对路径
```batch
@echo off
REM 获取当前脚本所在目录的上级目录
set "APP_DIR=%~dp0.."

echo 应用目录: %APP_DIR%
cd /d "%APP_DIR%"

REM 停止进程
TASKKILL /IM python.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

REM 启动新进程
start "" "D:\develop\python396\python.exe" "app.py"
```

### 方案3：添加错误检查
```batch
@echo off
echo 带错误检查的重启脚本...

REM 停止进程
echo 停止Python进程...
TASKKILL /IM python.exe /F
if %ERRORLEVEL% EQU 0 (
    echo 进程停止成功
) else (
    echo 没有找到Python进程或停止失败
)

REM 等待
timeout /t 3 /nobreak >nul

REM 启动新进程
echo 启动新进程...
cd /d "G:\cursor_projects\extensions_web"
start "" "D:\develop\python396\python.exe" "app.py"

REM 检查启动结果
timeout /t 3 /nobreak >nul
tasklist | findstr python
if %ERRORLEVEL% EQU 0 (
    echo 新进程启动成功
) else (
    echo 新进程启动失败
)
```

## 📋 调试命令

### 检查系统状态
```bash
# 检查Python版本
"D:\develop\python396\python.exe" --version

# 检查当前目录
cd

# 检查文件权限
icacls "G:\cursor_projects\extensions_web\app.py"

# 检查端口占用
netstat -ano | findstr :8000
```

### 手动重启流程
```bash
# 1. 查看当前进程
tasklist | findstr python

# 2. 停止进程（记录PID）
TASKKILL /PID <PID> /F

# 3. 确认停止
tasklist | findstr python

# 4. 切换目录
cd /d "G:\cursor_projects\extensions_web"

# 5. 启动新进程
start "" "D:\develop\python396\python.exe" "app.py"

# 6. 检查启动结果
timeout /t 5 /nobreak >nul
tasklist | findstr python
```

## ⚠️ 常见错误

### 错误1：文件路径包含空格
```bash
# 错误
D:\Program Files\Python\python.exe

# 正确
"D:\Program Files\Python\python.exe"
```

### 错误2：使用了错误的脚本名
```bash
# 检查实际的脚本文件名
dir *.py

# 常见的脚本名
app.py, main.py, server.py, run.py
```

### 错误3：工作目录不正确
```bash
# 确保在正确的目录启动
cd /d "G:\cursor_projects\extensions_web"
```

### 错误4：Python环境问题
```bash
# 检查Python是否正常
"D:\develop\python396\python.exe" -c "print('Python OK')"

# 检查依赖包
"D:\develop\python396\python.exe" -m pip list
```

## 🎯 最终解决方案

基于你的环境，推荐使用以下重启命令：

```bash
# 方法1：简单重启（推荐先试这个）
data\simple_restart.bat

# 方法2：手动命令
TASKKILL /IM python.exe /F && cd /d "G:\cursor_projects\extensions_web" && start "" "D:\develop\python396\python.exe" "app.py"

# 方法3：分步执行
TASKKILL /IM python.exe /F
# 等待3秒
cd /d "G:\cursor_projects\extensions_web"
start "" "D:\develop\python396\python.exe" "app.py"
```

## 📊 验证重启成功

```bash
# 等待5秒后检查
timeout /t 5 /nobreak >nul
tasklist | findstr python

# 检查端口是否监听
netstat -ano | findstr :8000

# 测试API是否响应
curl http://localhost:8000/api/health
```

按照这个指南逐步排查，应该能找到并解决重启问题！
