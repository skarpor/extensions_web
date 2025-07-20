# Docker配置测试脚本

Write-Host "========== 扩展Web系统 Docker配置测试 ==========" -ForegroundColor Green

# 检查Docker环境
Write-Host "`n1. 检查Docker环境..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker版本: $dockerVersion" -ForegroundColor Green

    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose版本: $composeVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ Docker未安装或未启动" -ForegroundColor Red
    exit 1
}

# 检查必要文件
Write-Host "`n2. 检查必要文件..." -ForegroundColor Yellow

$requiredFiles = @(
    "Dockerfile.backend",
    "Dockerfile.frontend", 
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.prod.yml",
    ".env.example",
    "requirements.txt",
    "fr\package.json"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file 存在" -ForegroundColor Green
    } else {
        Write-Host "✗ $file 不存在" -ForegroundColor Red
    }
}

# 检查环境变量文件
Write-Host "`n3. 检查环境变量配置..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env 文件存在" -ForegroundColor Green
    
    # 检查关键环境变量
    $envContent = Get-Content ".env" -Raw
    $keyVars = @("SECRET_KEY", "VITE_API_BASE_URL", "DATABASE_URL")
    
    foreach ($var in $keyVars) {
        if ($envContent -match "$var=") {
            Write-Host "✓ $var 已配置" -ForegroundColor Green
        } else {
            Write-Host "✗ $var 未配置" -ForegroundColor Red
        }
    }
} else {
    Write-Host "⚠ .env 文件不存在，将从 .env.example 复制" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ 已创建 .env 文件" -ForegroundColor Green
}

# 检查目录结构
Write-Host "`n4. 检查目录结构..." -ForegroundColor Yellow
$requiredDirs = @(
    "api",
    "core", 
    "fr\src",
    "docker-config",
    "scripts"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✓ $dir 目录存在" -ForegroundColor Green
    } else {
        Write-Host "✗ $dir 目录不存在" -ForegroundColor Red
    }
}

# 创建Docker数据目录
Write-Host "`n5. 创建Docker数据目录..." -ForegroundColor Yellow
$dataDirs = @(
    "docker-data\data",
    "docker-data\logs", 
    "docker-data\extensions",
    "docker-data\uploads",
    "docker-data\db",
    "docker-data\redis",
    "docker-data\ssl"
)

foreach ($dir in $dataDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ 创建目录: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ 目录已存在: $dir" -ForegroundColor Green
    }
}

# 测试Docker Compose配置
Write-Host "`n6. 验证Docker Compose配置..." -ForegroundColor Yellow
try {
    Write-Host "检查开发环境配置..." -ForegroundColor Cyan
    docker-compose -f docker-compose.dev.yml config | Out-Null
    Write-Host "✓ 开发环境配置有效" -ForegroundColor Green
    
    Write-Host "检查生产环境配置..." -ForegroundColor Cyan
    docker-compose -f docker-compose.prod.yml config | Out-Null
    Write-Host "✓ 生产环境配置有效" -ForegroundColor Green
}
catch {
    Write-Host "✗ Docker Compose配置有误: $($_.Exception.Message)" -ForegroundColor Red
}

# 显示部署命令
Write-Host "`n========== 部署命令 ==========" -ForegroundColor Green
Write-Host "开发环境部署:" -ForegroundColor Yellow
Write-Host "  .\scripts\deploy.ps1 dev" -ForegroundColor White
Write-Host ""
Write-Host "生产环境部署:" -ForegroundColor Yellow  
Write-Host "  .\scripts\deploy.ps1 prod -Build" -ForegroundColor White
Write-Host ""
Write-Host "查看服务状态:" -ForegroundColor Yellow
Write-Host "  .\scripts\deploy.ps1 status" -ForegroundColor White
Write-Host ""
Write-Host "停止所有服务:" -ForegroundColor Yellow
Write-Host "  .\scripts\deploy.ps1 stop" -ForegroundColor White

Write-Host "`n========== 测试完成 ==========" -ForegroundColor Green
