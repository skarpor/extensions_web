# 简单的Docker配置测试脚本

Write-Host "========== 扩展Web系统 Docker配置测试 ==========" -ForegroundColor Green

# 检查Docker
Write-Host "`n1. 检查Docker..." -ForegroundColor Yellow
$dockerCheck = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCheck) {
    Write-Host "✓ Docker已安装" -ForegroundColor Green
} else {
    Write-Host "✗ Docker未安装" -ForegroundColor Red
}

# 检查Docker Compose
Write-Host "`n2. 检查Docker Compose..." -ForegroundColor Yellow
$composeCheck = Get-Command docker-compose -ErrorAction SilentlyContinue
if ($composeCheck) {
    Write-Host "✓ Docker Compose已安装" -ForegroundColor Green
} else {
    Write-Host "✗ Docker Compose未安装" -ForegroundColor Red
}

# 检查必要文件
Write-Host "`n3. 检查必要文件..." -ForegroundColor Yellow
$files = @(
    "Dockerfile.backend",
    "Dockerfile.frontend", 
    "docker-compose.prod.yml",
    ".env.example"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file" -ForegroundColor Red
    }
}

# 检查.env文件
Write-Host "`n4. 检查环境变量..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env文件存在" -ForegroundColor Green
} else {
    Write-Host "⚠ 创建.env文件..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env文件已创建" -ForegroundColor Green
}

# 创建数据目录
Write-Host "`n5. 创建数据目录..." -ForegroundColor Yellow
$dirs = @("docker-data", "docker-data\data", "docker-data\logs")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ 创建: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ 存在: $dir" -ForegroundColor Green
    }
}

Write-Host "`n========== 部署命令 ==========" -ForegroundColor Green
Write-Host "开发环境: .\scripts\deploy.ps1 dev" -ForegroundColor White
Write-Host "生产环境: .\scripts\deploy.ps1 prod" -ForegroundColor White
Write-Host "查看状态: .\scripts\deploy.ps1 status" -ForegroundColor White

Write-Host "`n========== 测试完成 ==========" -ForegroundColor Green
