@echo off
chcp 65001 >nul
echo ========== 扩展Web系统 Docker配置测试 ==========

echo.
echo 1. 检查Docker...
docker --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Docker已安装
    docker --version
) else (
    echo ✗ Docker未安装
)

echo.
echo 2. 检查Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Docker Compose已安装
    docker-compose --version
) else (
    echo ✗ Docker Compose未安装
)

echo.
echo 3. 检查必要文件...
if exist "Dockerfile.backend" (echo ✓ Dockerfile.backend) else (echo ✗ Dockerfile.backend)
if exist "Dockerfile.frontend" (echo ✓ Dockerfile.frontend) else (echo ✗ Dockerfile.frontend)
if exist "docker-compose.prod.yml" (echo ✓ docker-compose.prod.yml) else (echo ✗ docker-compose.prod.yml)
if exist ".env.example" (echo ✓ .env.example) else (echo ✗ .env.example)

echo.
echo 4. 检查环境变量文件...
if exist ".env" (
    echo ✓ .env文件存在
) else (
    echo ⚠ 创建.env文件...
    copy ".env.example" ".env" >nul
    echo ✓ .env文件已创建
)

echo.
echo 5. 创建数据目录...
if not exist "docker-data" mkdir "docker-data"
if not exist "docker-data\data" mkdir "docker-data\data"
if not exist "docker-data\logs" mkdir "docker-data\logs"
if not exist "docker-data\extensions" mkdir "docker-data\extensions"
if not exist "docker-data\uploads" mkdir "docker-data\uploads"
if not exist "docker-data\db" mkdir "docker-data\db"
if not exist "docker-data\redis" mkdir "docker-data\redis"
echo ✓ 数据目录已创建

echo.
echo ========== 部署命令 ==========
echo 开发环境: powershell -File scripts\deploy.ps1 dev
echo 生产环境: powershell -File scripts\deploy.ps1 prod
echo 查看状态: powershell -File scripts\deploy.ps1 status
echo.
echo ========== 测试完成 ==========
pause
