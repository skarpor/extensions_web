# 扩展Web系统 - Docker部署脚本 (PowerShell版本)
# 使用方法: .\scripts\deploy.ps1 [dev|prod] [-Build]

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "prod", "stop", "cleanup", "status", "help")]
    [string]$Action = "help",
    
    [switch]$Build
)

# 颜色定义
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

# 日志函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

# 显示帮助信息
function Show-Help {
    Write-Host "扩展Web系统 - Docker部署脚本" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "使用方法:"
    Write-Host "  .\scripts\deploy.ps1 [dev|prod] [-Build]"
    Write-Host ""
    Write-Host "参数:"
    Write-Host "  dev     启动开发环境"
    Write-Host "  prod    启动生产环境"
    Write-Host "  stop    停止所有服务"
    Write-Host "  cleanup 清理Docker资源"
    Write-Host "  status  查看服务状态"
    Write-Host "  -Build  强制重新构建镜像"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\scripts\deploy.ps1 dev          # 启动开发环境"
    Write-Host "  .\scripts\deploy.ps1 prod -Build  # 重新构建并启动生产环境"
    Write-Host ""
}

# 检查Docker是否安装
function Test-Docker {
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            throw "Docker not found"
        }
        
        $composeVersion = docker-compose --version 2>$null
        if (-not $composeVersion) {
            throw "Docker Compose not found"
        }
        
        Write-Info "Docker 环境检查通过"
        return $true
    }
    catch {
        Write-Error "Docker 或 Docker Compose 未安装，请先安装 Docker Desktop"
        return $false
    }
}

# 检查环境变量文件
function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Warning ".env 文件不存在，从 .env.example 复制"
        Copy-Item ".env.example" ".env"
        Write-Warning "请编辑 .env 文件并设置正确的环境变量"
        Write-Warning "特别注意修改 SECRET_KEY 和数据库密码"
    }
}

# 创建必要的目录
function New-Directories {
    Write-Info "创建必要的目录..."
    
    $directories = @(
        "docker-data\data",
        "docker-data\logs",
        "docker-data\extensions",
        "docker-data\uploads",
        "docker-data\db",
        "docker-data\redis",
        "docker-data\ssl"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Info "创建目录: $dir"
        }
    }
}

# 部署开发环境
function Start-DevEnvironment {
    param([bool]$BuildFlag)
    
    Write-Info "部署开发环境..."
    
    $buildParam = if ($BuildFlag) { "--build" } else { "" }
    if ($BuildFlag) {
        Write-Info "将重新构建镜像"
    }
    
    try {
        if ($buildParam) {
            docker-compose -f docker-compose.dev.yml up -d --build
        } else {
            docker-compose -f docker-compose.dev.yml up -d
        }
        
        Write-Success "开发环境启动成功!"
        Write-Info "前端地址: http://localhost:5173"
        Write-Info "后端地址: http://localhost:8000"
        Write-Info "API文档: http://localhost:8000/docs"
        Write-Info "数据库管理: http://localhost:8080"
    }
    catch {
        Write-Error "开发环境启动失败: $($_.Exception.Message)"
    }
}

# 部署生产环境
function Start-ProdEnvironment {
    param([bool]$BuildFlag)
    
    Write-Info "部署生产环境..."
    
    $buildParam = if ($BuildFlag) { "--build" } else { "" }
    if ($BuildFlag) {
        Write-Info "将重新构建镜像"
    }
    
    try {
        # 构建前端
        Write-Info "构建前端应用..."
        Set-Location "fr"
        npm ci
        npm run build
        Set-Location ".."
        
        if ($buildParam) {
            docker-compose -f docker-compose.prod.yml up -d --build
        } else {
            docker-compose -f docker-compose.prod.yml up -d
        }
        
        Write-Success "生产环境启动成功!"
        Write-Info "应用地址: http://localhost"
        Write-Info "后端API: http://localhost:8000"
        Write-Info "Redis: localhost:6379"
    }
    catch {
        Write-Error "生产环境启动失败: $($_.Exception.Message)"
    }
}

# 停止服务
function Stop-Services {
    Write-Info "停止所有服务..."
    
    try {
        if (Test-Path "docker-compose.dev.yml") {
            docker-compose -f docker-compose.dev.yml down 2>$null
        }
        
        if (Test-Path "docker-compose.prod.yml") {
            docker-compose -f docker-compose.prod.yml down 2>$null
        }
        
        Write-Success "所有服务已停止"
    }
    catch {
        Write-Error "停止服务失败: $($_.Exception.Message)"
    }
}

# 清理资源
function Clear-Resources {
    Write-Info "清理Docker资源..."
    
    try {
        # 停止服务
        Stop-Services
        
        # 删除未使用的镜像
        docker image prune -f
        
        # 删除未使用的卷
        docker volume prune -f
        
        Write-Success "清理完成"
    }
    catch {
        Write-Error "清理失败: $($_.Exception.Message)"
    }
}

# 显示状态
function Show-Status {
    Write-Info "服务状态:"
    
    try {
        Write-Host "开发环境:" -ForegroundColor $Colors.Yellow
        docker-compose -f docker-compose.dev.yml ps 2>$null
        
        Write-Host "生产环境:" -ForegroundColor $Colors.Yellow
        docker-compose -f docker-compose.prod.yml ps 2>$null
    }
    catch {
        Write-Warning "无法获取服务状态"
    }
}

# 主函数
function Main {
    switch ($Action) {
        "dev" {
            if (-not (Test-Docker)) { return }
            Test-EnvFile
            New-Directories
            Start-DevEnvironment -BuildFlag $Build
        }
        "prod" {
            if (-not (Test-Docker)) { return }
            Test-EnvFile
            New-Directories
            Start-ProdEnvironment -BuildFlag $Build
        }
        "stop" {
            Stop-Services
        }
        "cleanup" {
            Clear-Resources
        }
        "status" {
            Show-Status
        }
        "help" {
            Show-Help
        }
        default {
            Write-Error "无效的参数: $Action"
            Show-Help
        }
    }
}

# 执行主函数
Main
