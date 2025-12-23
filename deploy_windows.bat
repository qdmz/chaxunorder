@echo off
setlocal enabledelayedexpansion

REM 产品查询系统远程部署脚本 (Windows版本)
REM 目标服务器: 42.194.226.146
REM 用户: root
REM 密码: password

echo ==========================================
echo     产品查询系统远程部署脚本
echo ==========================================
echo.

REM 配置参数
set SERVER_IP=42.194.226.146
set SERVER_USER=root
set SERVER_PASS=password
set SERVER_PATH=/opt/chaxunorder
set PROJECT_NAME=chaxunorder

echo [INFO] 准备部署到服务器: %SERVER_IP%

REM 检查必要文件
if not exist "app.py" (
    echo [ERROR] 请在项目根目录下运行此脚本
    pause
    exit /b 1
)

if not exist "docker-compose.yml" (
    echo [ERROR] 找不到docker-compose.yml文件
    pause
    exit /b 1
)

REM 创建临时压缩包
echo [INFO] 创建项目压缩包...
tar -a -c -f %PROJECT_NAME%.zip --exclude=.git --exclude=__pycache__ --exclude=*.pyc --exclude=data.db --exclude=static/uploads\* --exclude=logs\* .

REM 使用PowerShell上传文件
echo [INFO] 上传项目文件到服务器...

powershell -Command "& {
    \$secpass = ConvertTo-SecureString '%SERVER_PASS%' -AsPlainText -Force
    \$cred = New-Object System.Management.Automation.PSCredential('%SERVER_USER%', \$secpass)
    
    Write-Host '[INFO] 连接到服务器...'
    New-PSDrive -Name 'RemoteServer' -PSProvider FileSystem -Root '\\%SERVER_IP%\c$' -Credential \$cred
    
    Write-Host '[INFO] 创建远程目录...'
    if (!(Test-Path '\\RemoteServer\opt\chaxunorder')) {
        New-Item -ItemType Directory -Path '\\RemoteServer\opt\chaxunorder' -Force
    }
    
    Write-Host '[INFO] 复制项目文件...'
    Expand-Archive -Path '%PROJECT_NAME%.zip' -DestinationPath '\\RemoteServer\opt\chaxunorder' -Force
    
    Remove-PSDrive -Name 'RemoteServer'
}"

if %errorlevel% neq 0 (
    echo [ERROR] 文件上传失败
    pause
    exit /b 1
)

REM 清理本地临时文件
del %PROJECT_NAME%.zip

echo [INFO] 项目文件上传完成

REM 使用SSH在远程服务器上执行部署命令
echo [INFO] 在远程服务器上执行部署...

REM 这里需要用户手动执行，因为Windows环境下的SSH配置复杂
echo.
echo ==========================================
echo         请手动执行以下步骤
echo ==========================================
echo.
echo 1. SSH登录到服务器:
echo    ssh root@%SERVER_IP%
echo.
echo 2. 进入项目目录:
echo    cd %SERVER_PATH%
echo.
echo 3. 设置执行权限并运行部署:
echo    chmod +x deploy.sh
echo    ./deploy.sh
echo.
echo 4. 检查部署状态:
echo    docker-compose ps
echo.
echo 5. 访问应用:
echo    http://%SERVER_IP%:5000
echo.
echo ==========================================
echo.

pause
