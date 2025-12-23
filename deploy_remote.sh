#!/bin/bash

# 远程服务器部署脚本
# 目标服务器: 42.194.226.146
# 用户: root
# 密码: password

set -e

# 服务器配置
SERVER_IP="42.194.226.146"
SERVER_USER="root"
SERVER_PASS="password"
SERVER_PATH="/opt/chaxunorder"
PROJECT_NAME="chaxunorder"

# 本地项目路径
LOCAL_PATH=$(pwd)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查SSH连接
check_ssh_connection() {
    log_info "检查SSH连接..."
    if ! sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'SSH连接成功'"; then
        log_error "无法连接到服务器 $SERVER_IP"
        exit 1
    fi
    log_info "SSH连接正常"
}

# 准备服务器环境
prepare_server() {
    log_info "准备服务器环境..."
    
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << 'EOF'
# 更新系统包
apt update && apt upgrade -y

# 安装Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    usermod -aG docker root
else
    echo "Docker已安装"
fi

# 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose已安装"
fi

# 安装其他必要工具
apt install -y sshpass curl wget git unzip

# 创建项目目录
mkdir -p /opt/chaxunorder
mkdir -p /opt/chaxunorder/static/uploads
mkdir -p /opt/chaxunorder/logs
mkdir -p /opt/chaxunorder/ssl

# 设置防火墙
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw --force enable

echo "服务器环境准备完成"
EOF
    
    log_info "服务器环境准备完成"
}

# 上传项目文件
upload_project() {
    log_info "上传项目文件到服务器..."
    
    # 创建临时压缩包
    tar -czf /tmp/$PROJECT_NAME.tar.gz \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='data.db' \
        --exclude='static/uploads/*' \
        --exclude='logs/*' \
        .
    
    # 上传到服务器
    sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no /tmp/$PROJECT_NAME.tar.gz $SERVER_USER@$SERVER_IP:/tmp/
    
    # 在服务器上解压
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
cd /opt/chaxunorder
rm -rf *
tar -xzf /tmp/$PROJECT_NAME.tar.gz -C /opt/chaxunorder
rm /tmp/$PROJECT_NAME.tar.gz
EOF
    
    # 清理本地临时文件
    rm /tmp/$PROJECT_NAME.tar.gz
    
    log_info "项目文件上传完成"
}

# 部署应用
deploy_application() {
    log_info "部署应用到服务器..."
    
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
cd /opt/chaxunorder

# 设置执行权限
chmod +x deploy.sh

# 创建环境配置文件
cat > .env << 'ENVEOF'
# 数据库配置
POSTGRES_DB=chaxunorder
POSTGRES_USER=chaxunuser
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Flask配置
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
DATABASE_URL=postgresql://chaxunuser:\$POSTGRES_PASSWORD@db:5432/chaxunorder

# 邮件配置
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
NOTIFY_EMAIL=sales@example.com

# 短信配置
SMS_ACCESS_KEY=
SMS_SECRET_KEY=
SMS_SIGN_NAME=产品查询系统
SMS_TEMPLATE_CODE=SMS_123456789
NOTIFY_PHONE=

# 其他配置
SITE_NAME=产品查询系统
ADMIN_EMAIL=admin@example.com
UPLOAD_FOLDER=/app/static/uploads
ENVEOF

# 创建开机自启动服务
cat > /etc/systemd/system/chaxunorder.service << 'EOFSERVICE'
[Unit]
Description=ChaxunOrder Web Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/chaxunorder
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOFSERVICE

# 启用服务
systemctl daemon-reload
systemctl enable chaxunorder.service

# 构建并启动应用
./deploy.sh

echo "应用部署完成"
EOF
    
    log_info "应用部署完成"
}

# 检查部署状态
check_deployment() {
    log_info "检查部署状态..."
    
    sleep 20  # 等待服务启动
    
    # 检查容器状态
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
cd /opt/chaxunorder
docker-compose ps

echo ""
echo "检查服务访问..."
if curl -f http://localhost:5000 > /dev/null 2>&1; then
    echo "✓ Web服务运行正常"
else
    echo "✗ Web服务访问异常"
fi

if curl -f http://localhost > /dev/null 2>&1; then
    echo "✓ Nginx代理运行正常"
else
    echo "⚠ Nginx代理访问异常"
fi

# 显示日志
echo ""
echo "=== 应用日志 ==="
docker-compose logs --tail=20 web

echo ""
echo "=== 数据库日志 ==="
docker-compose logs --tail=10 db
EOF
}

# 显示部署信息
show_deployment_info() {
    log_info "部署完成！"
    echo ""
    echo "🌍 访问地址:"
    echo "  - Web应用: http://$SERVER_IP:5000"
    echo "  - Nginx代理: http://$SERVER_IP"
    echo "  - 管理后台: http://$SERVER_IP:5000/admin"
    echo ""
    echo "👤 默认管理员账户:"
    echo "  - 用户名: admin"
    echo "  - 密码: admin123"
    echo ""
    echo "🔧 服务器管理命令:"
    echo "  - SSH登录: ssh root@$SERVER_IP"
    echo "  - 查看状态: cd /opt/chaxunorder && docker-compose ps"
    echo "  - 查看日志: cd /opt/chaxunorder && docker-compose logs -f"
    echo "  - 重启服务: cd /opt/chaxunorder && docker-compose restart"
    echo "  - 停止服务: cd /opt/chaxunorder && docker-compose down"
    echo ""
    echo "📁 重要目录:"
    echo "  - 项目路径: /opt/chaxunorder"
    echo "  - 上传文件: /opt/chaxunorder/static/uploads"
    echo "  - 日志文件: /opt/chaxunorder/logs"
    echo "  - SSL证书: /opt/chaxunorder/ssl"
    echo ""
    echo "🔒 安全建议:"
    echo "  - 1. 首次登录后立即修改管理员密码"
    echo "  - 2. 配置HTTPS证书"
    echo "  - 3. 设置防火墙规则"
    echo "  - 4. 定期备份数据"
    echo "  - 5. 更新系统和Docker镜像"
    echo ""
}

# 安装本地依赖
install_local_dependencies() {
    log_info "检查本地依赖..."
    
    if ! command -v sshpass &> /dev/null; then
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y sshpass
        elif command -v brew &> /dev/null; then
            brew install sshpass
        elif command -v yum &> /dev/null; then
            sudo yum install -y sshpass
        else
            log_error "请手动安装sshpass工具"
            exit 1
        fi
    fi
    
    log_info "本地依赖检查完成"
}

# 主函数
main() {
    log_info "开始远程部署到服务器 $SERVER_IP..."
    
    # 检查本地是否在项目根目录
    if [ ! -f "app.py" ] || [ ! -f "docker-compose.yml" ]; then
        log_error "请在项目根目录下运行此脚本"
        exit 1
    fi
    
    install_local_dependencies
    check_ssh_connection
    prepare_server
    upload_project
    deploy_application
    check_deployment
    show_deployment_info
    
    log_info "远程部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误"; exit 1' ERR

# 执行主函数
main "$@"
