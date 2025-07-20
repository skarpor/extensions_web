# 自动重启命令生成说明

## 🎯 功能概述

系统会自动检测运行环境，并生成适合当前环境的默认重启命令，支持多种部署场景。

## 🔍 环境检测

### 支持的环境类型
1. **Docker容器** - 检测 `/.dockerenv` 文件或 `/proc/1/cgroup` 内容
2. **Windows服务** - 检测 `win32serviceutil` 模块
3. **Systemd服务** - 检测 `SYSTEMD_EXEC_PID` 环境变量
4. **可执行文件** - 检测 `sys.frozen` 属性（PyInstaller打包）
5. **Python脚本** - 普通Python脚本运行
6. **无Python环境** - 检测系统是否有Python命令

### 检测信息
- **操作系统类型**：Windows/Linux
- **Python版本和路径**：完整的Python可执行文件路径
- **主脚本文件**：自动查找 app.py、main.py、server.py、run.py
- **当前目录**：应用程序运行目录
- **进程信息**：PID、运行时间、内存使用等

## 📋 默认重启命令

### Windows环境

#### 1. 可执行文件 (exe)
```batch
# 重启服务(exe)
TASKKILL /IM "app.exe" /F && "C:\path\to\app.exe"
```

#### 2. Python脚本
```batch
# 重启服务(进程名) - 推荐
TASKKILL /IM python.exe /F && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"

# 重启服务(PID)
TASKKILL /PID 1234 /F && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"

# 温和重启
TASKKILL /PID 1234 && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
```

#### 3. Docker环境
```batch
# 重启Docker容器
docker restart $(hostname)
```

#### 4. 独立脚本 (推荐)
```batch
# 脚本重启(推荐)
data\restart_service.bat
```

### Linux环境

#### 1. Python脚本
```bash
# 重启服务(进程名)
pkill -f "python.*app.py" && nohup "/usr/bin/python3" "/path/to/app.py" &

# 重启服务(PID)
kill 1234 && nohup "/usr/bin/python3" "/path/to/app.py" &
```

#### 2. Systemd服务
```bash
# 重启systemd服务
sudo systemctl restart your-service-name
```

#### 3. Docker环境
```bash
# 重启Docker容器
docker restart $(hostname)
```

#### 4. 独立脚本 (推荐)
```bash
# 脚本重启(推荐)
bash data/restart_service.sh
```

## 🚀 自动化流程

### 1. 系统启动时
```
加载系统设置页面 → 获取系统信息 → 检测运行环境 → 生成默认命令 → 自动添加到自定义命令
```

### 2. 命令生成逻辑
```python
def generate_default_restart_commands(system_info):
    # 检测环境类型
    env_type = system_info.get('environment_type')
    
    # 根据环境生成相应命令
    if env_type == 'docker':
        return docker_restart_commands()
    elif env_type == 'executable':
        return exe_restart_commands()
    else:
        return python_script_commands()
```

### 3. 自动添加机制
- 检查是否已存在重启命令
- 如果没有，自动添加适合当前环境的命令
- 自动保存到本地存储
- 显示添加成功提示

## 📊 环境适配示例

### 场景1：Windows + Python脚本
```
检测结果：
- OS: Windows 10
- Environment: python_script
- Python: D:\develop\python396\python.exe
- Script: G:\cursor_projects\extensions_web\app.py

生成命令：
1. TASKKILL /IM python.exe /F && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
2. TASKKILL /PID 1234 /F && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
3. data\restart_service.bat
```

### 场景2：Docker容器
```
检测结果：
- OS: Linux
- Environment: docker
- Is_Docker: true

生成命令：
1. docker restart $(hostname)
2. bash data/restart_service.sh
```

### 场景3：打包的exe文件
```
检测结果：
- OS: Windows 10
- Environment: executable
- Is_Executable: true
- Exe_Path: C:\MyApp\app.exe

生成命令：
1. TASKKILL /IM "app.exe" /F && "C:\MyApp\app.exe"
2. data\restart_service.bat
```

## ⚠️ 注意事项

### 1. 权限要求
- **Windows**：需要结束进程的权限
- **Linux**：可能需要sudo权限
- **Docker**：需要Docker命令权限

### 2. 路径处理
- 自动使用绝对路径
- 路径包含空格时自动添加引号
- 支持中文路径

### 3. 错误处理
- 环境检测失败时提供基本命令
- 路径获取失败时使用默认值
- 命令生成失败时显示错误信息

## 🔧 手动调整

### 1. 修改生成的命令
- 在自定义命令中编辑生成的命令
- 根据实际情况调整路径和参数
- 保存修改后的命令

### 2. 添加自定义命令
- 点击"添加命令"按钮
- 输入适合你环境的命令
- 测试命令是否正常工作

### 3. 重新生成
- 如果环境发生变化
- 点击"生成重启脚本"重新创建
- 系统会更新脚本内容

## 📋 最佳实践

### 1. 优先使用独立脚本
```bash
# 推荐方式
data\restart_service.bat  # Windows
bash data/restart_service.sh  # Linux
```

### 2. 测试重启命令
```bash
# 先测试停止命令
TASKKILL /IM python.exe /F

# 再测试启动命令
"D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
```

### 3. 监控重启过程
- 查看命令执行结果
- 检查新进程是否启动成功
- 验证服务是否正常响应

## 🎉 总结

自动重启命令生成功能让系统能够：
- ✅ 自动适配不同的运行环境
- ✅ 生成正确的重启命令
- ✅ 提供多种重启方式选择
- ✅ 简化系统管理操作

无论你的应用运行在什么环境下，系统都会自动为你准备好合适的重启命令！
