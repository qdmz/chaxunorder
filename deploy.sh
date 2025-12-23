#!/bin/bash

# 产品查询系统部署脚本
# 作者: AI Assistant
# 日期: $(date +%Y-%m-%d)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查端口占用
    if netstat -tuln | grep -q ":80 "; then
        log_warn "端口80已被占用"
    fi
    
    if netstat -tuln | grep -q ":5000 "; then
        log_warn "端口5000已被占用"
    fi
    
    log_info "系统要求检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p static/uploads/products
    mkdir -p static/uploads/temp
    mkdir -p logs
    mkdir -p ssl
    
    # 创建占位文件
    touch static/uploads/.gitkeep
    touch logs/.gitkeep
    
    log_info "目录创建完成"
}

# 设置环境变量
setup_environment() {
    log_info "设置环境变量..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# 数据库配置
POSTGRES_DB=chaxunorder
POSTGRES_USER=chaxunuser
POSTGRES_PASSWORD=chaxunpass

# Flask配置
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
DATABASE_URL=postgresql://chaxunuser:chaxunpass@db:5432/chaxunorder

# 邮件配置
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
NOTIFY_EMAIL=sales@example.com

# 短信配置（阿里云）
SMS_ACCESS_KEY=
SMS_SECRET_KEY=
SMS_SIGN_NAME=产品查询系统
SMS_TEMPLATE_CODE=SMS_123456789
NOTIFY_PHONE=

# 文件上传配置
UPLOAD_FOLDER=/app/static/uploads
MAX_CONTENT_LENGTH=16777216

# 其他配置
SITE_NAME=产品查询系统
ADMIN_EMAIL=admin@example.com
EOF
        log_info "已创建.env文件，请根据需要修改配置"
    else
        log_warn ".env文件已存在，跳过创建"
    fi
}

# 构建和启动服务
build_and_start() {
    log_info "构建Docker镜像..."
    docker-compose build
    
    log_info "启动服务..."
    docker-compose up -d
    
    log_info "等待服务启动..."
    sleep 10
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    until docker-compose exec -T db pg_isready -U chaxunuser -d chaxunorder; do
        echo "等待PostgreSQL启动..."
        sleep 2
    done
    
    # 创建表
    log_info "创建数据表..."
    docker-compose exec -T web python -c "
from app import create_app
from models import db
app = create_app()
app.app_context().push()
db.create_all()
print('数据表创建完成')
"
    
    log_info "数据库初始化完成"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    # 检查容器状态
    if docker-compose ps | grep -q "Up"; then
        log_info "服务运行正常"
        docker-compose ps
    else
        log_error "部分服务启动失败"
        docker-compose ps
        exit 1
    fi
    
    # 检查web服务
    if curl -f http://localhost:5000 > /dev/null 2>&1; then
        log_info "Web服务访问正常: http://localhost:5000"
    else
        log_error "Web服务访问异常"
    fi
    
    # 检查nginx
    if curl -f http://localhost > /dev/null 2>&1; then
        log_info "Nginx服务访问正常: http://localhost"
    else
        log_warn "Nginx服务访问异常或未配置"
    fi
}

# 显示部署信息
show_info() {
    log_info "部署完成！"
    echo ""
    echo "访问地址:"
    echo "  - Web应用: http://localhost:5000"
    echo "  - Nginx代理: http://localhost"
    echo "  - 管理后台: http://localhost:5000/admin"
    echo ""
    echo "默认管理员账户:"
    echo "  - 用户名: admin"
    echo "  - 密码: admin123"
    echo ""
    echo "常用命令:"
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 停止服务: docker-compose down"
    echo "  - 重启服务: docker-compose restart"
    echo "  - 更新服务: docker-compose pull && docker-compose up -d"
    echo ""
    echo "数据目录:"
    echo "  - 上传文件: ./static/uploads/"
    echo "  - 日志文件: ./logs/"
    echo "  - 数据库: Docker volume (postgres_data)"
    echo ""
}

# 主函数
main() {
    log_info "开始部署产品查询系统..."
    
    check_requirements
    create_directories
    setup_environment
    build_and_start
    init_database
    check_services
    show_info
    
    log_info "部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"