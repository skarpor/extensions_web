# Windows 重启命令使用指南

## 🎯 重启命令格式

### 基本语法
```bash
TASKKILL /参数 目标 && 启动命令
```

### 常用参数
- `/IM` - 按进程名结束进程
- `/PID` - 按进程ID结束进程  
- `/F` - 强制结束进程
- `&&` - 命令连接符，前一个命令成功后执行下一个

## 📋 推荐的重启命令

### 方法1：按进程名重启（推荐）
```bash
TASKKILL /IM python.exe /F && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
```

### 方法2：按进程ID重启
```bash
TASKKILL /PID 9608 /F && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
```

### 方法3：温和重启（不强制）
```bash
TASKKILL /PID 9608 && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
```

## ⚠️ 常见错误及解决方案

### 错误1：语法错误
```
错误: 无效参数/选项 - 'G:\cursor_projects\extensions_web\app.py'
```
**原因**：TASKKILL命令语法错误，缺少 `/F` 参数或路径格式问题

**解决**：
- 确保使用正确的参数格式
- 路径用双引号包围
- 使用 `&&` 而不是 `;` 连接命令

### 错误2：JSON解析错误
```
Failed to execute 'json' on 'Response': Unexpected end of JSON input
```
**原因**：服务器响应不完整或连接中断

**解决**：
- 检查网络连接
- 确认服务器正常运行
- 重试命令执行

### 错误3：进程未找到
```
错误: 找不到进程 "python.exe"
```
**解决**：
- 使用 `tasklist | findstr python` 查找正确的进程名
- 使用具体的进程ID而不是进程名

## 🔧 实用命令示例

### 查找Python进程
```bash
tasklist | findstr python
```

### 查找特定端口的进程
```bash
netstat -ano | findstr :8000
```

### 结束特定端口的进程
```bash
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8000') do taskkill /pid %a /f
```

### 检查进程是否存在
```bash
tasklist /FI "IMAGENAME eq python.exe"
```

## 📊 命令执行流程

1. **停止当前进程**
   - 使用TASKKILL命令结束Python进程
   - 等待进程完全停止

2. **启动新进程**
   - 使用完整Python路径
   - 指定完整脚本路径
   - 异步启动新进程

3. **验证重启**
   - 检查新进程是否启动成功
   - 验证服务是否正常响应

## 🎯 最佳实践

### 1. 使用完整路径
```bash
# 好的做法
"D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"

# 避免的做法
python app.py
```

### 2. 路径包含空格时使用引号
```bash
# 正确
"C:\Program Files\Python\python.exe" "C:\My App\app.py"

# 错误
C:\Program Files\Python\python.exe C:\My App\app.py
```

### 3. 优先使用进程名而不是PID
```bash
# 推荐（进程名相对稳定）
TASKKILL /IM python.exe /F

# 次选（PID会变化）
TASKKILL /PID 9608 /F
```

### 4. 添加错误处理
```bash
# 带错误检查的重启命令
TASKKILL /IM python.exe /F >nul 2>&1 && "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
```

## 🚀 自动化脚本

### 创建重启批处理文件
```batch
@echo off
echo 正在重启服务...
TASKKILL /IM python.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul
start "" "D:\develop\python396\python.exe" "G:\cursor_projects\extensions_web\app.py"
echo 服务重启完成
```

### PowerShell重启脚本
```powershell
# restart-service.ps1
Write-Host "正在停止Python进程..."
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "正在启动新进程..."
Start-Process -FilePath "D:\develop\python396\python.exe" -ArgumentList "G:\cursor_projects\extensions_web\app.py"
Write-Host "服务重启完成"
```

## 📋 故障排除清单

- [ ] 确认Python路径正确
- [ ] 确认脚本路径正确
- [ ] 检查路径中是否有特殊字符
- [ ] 验证进程名或PID是否正确
- [ ] 确认有足够的权限执行命令
- [ ] 检查防火墙或安全软件是否阻止
- [ ] 验证端口是否被占用
- [ ] 检查系统资源是否充足

使用这些指南，你应该能够成功执行重启命令并避免常见的错误！
