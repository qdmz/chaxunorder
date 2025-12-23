# 远程部署指南

## 服务器信息
- **IP地址**: 42.194.226.146
- **用户名**: root  
- **密码**: Thanks12A#
- **系统**: Debian Linux

## 快速部署步骤

### 1. 连接到服务器

```bash
ssh root@42.194.226.146
# 输入密码: Thanks12A#
```

### 2. 安装Docker环境

```bash
# 更新系统包
apt update && apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# 安装Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 3. 创建项目目录

```bash
mkdir -p /opt/chaxunorder
cd /opt/chaxunorder
mkdir -p static/uploads products
mkdir -p logs
mkdir -p ssl
```

### 4. 下载项目代码

```bash
# 使用Git克隆（推荐）
git clone https://github.com/qdmz/chaxunorder.git /opt/chaxunorder

# 或者手动下载
wget https://github.com/qdmz/chaxunorder/archive/main.zip
unzip main.zip
mv chaxunorder-main/* .
rm -rf chaxunorder-main main.zip
```

### 5. 配置环境变量

```bash
# 创建环境文件
cat > .env << 'EOF'
# 数据库配置
POSTGRES_DB=chaxunorder
POSTGRES_USER=chaxunuser
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Flask配置
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
DATABASE_URL=postgresql://chaxunuser:$POSTGRES_PASSWORD@db:5432/chaxunorder

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
EOF
```

### 6. 构建并启动应用

```bash
# 设置执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 7. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查服务访问
curl http://localhost:5000
curl http://localhost

# 查看日志
docker-compose logs -f web
```

## 访问应用

部署成功后，可通过以下地址访问：

- **Web应用**: http://42.194.226.146:5000
- **Nginx代理**: http://42.194.226.146
- **管理后台**: http://42.194.226.146:5000/admin

默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`

## 常用管理命令

### 查看服务状态
```bash
cd /opt/chaxunorder
docker-compose ps
```

### 查看日志
```bash
cd /opt/chaxunorder
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

### 重启服务
```bash
cd /opt/chaxunorder
docker-compose restart
```

### 停止服务
```bash
cd /opt/chaxunorder
docker-compose down
```

### 更新应用
```bash
cd /opt/chaxunorder
git pull
docker-compose down
docker-compose up -d --build
```

### 备份数据
```bash
# 备份数据库
docker-compose exec db pg_dump -U chaxunuser chaxunorder > backup_$(date +%Y%m%d).sql

# 备份文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz static/uploads/
```

### 恢复数据
```bash
# 恢复数据库
docker-compose exec -T db psql -U chaxunuser chaxunorder < backup_20241223.sql

# 恢复文件
tar -xzf uploads_backup_20241223.tar.gz
```

## 安全配置

### 设置防火墙
```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 5000/tcp  # 应用端口
ufw enable
```

### 配置HTTPS（可选）
```bash
# 使用Let's Encrypt获取SSL证书
apt install certbot
certbot certonly --standalone -d yourdomain.com

# 更新nginx配置使用HTTPS
# 编辑 /opt/chaxunorder/nginx.conf
```

### 修改默认密码
```bash
# 登录管理后台修改admin密码
# 或通过命令行修改
docker-compose exec web python -c "
from app import create_app
from models import User, db
app = create_app()
app.app_context().push()
user = User.query.filter_by(username='admin').first()
user.set_password('your_new_password')
db.session.commit()
"
```

## 监控和维护

### 设置定时任务
```bash
# 编辑crontab
crontab -e

# 添加定时备份（每天凌晨3点）
0 3 * * * cd /opt/chaxunorder && docker-compose exec db pg_dump -U chaxunuser chaxunorder > /backup/backup_$(date +\%Y\%m\%d).sql

# 添加日志清理（每周日凌晨4点）
0 4 * * 0 find /opt/chaxunorder/logs -name "*.log" -mtime +30 -delete
```

### 监控磁盘空间
```bash
# 查看磁盘使用情况
df -h

# 查看容器大小
docker system df

# 清理未使用的镜像
docker system prune -a
```

## 故障排除

### 应用无法访问
1. 检查容器状态：`docker-compose ps`
2. 查看应用日志：`docker-compose logs web`
3. 检查端口占用：`netstat -tlnp | grep 5000`

### 数据库连接失败
1. 检查数据库容器：`docker-compose logs db`
2. 验证数据库配置：检查.env文件
3. 重启数据库：`docker-compose restart db`

### 文件上传失败
1. 检查目录权限：`ls -la static/uploads/`
2. 修改权限：`chmod 755 static/uploads/`
3. 检查磁盘空间：`df -h`

## 联系支持

如遇到问题，请：
1. 查看GitHub Issues: https://github.com/qdmz/chaxunorder/issues
2. 检查项目文档: https://github.com/qdmz/chaxunorder
3. 查看系统日志排查问题

---

**注意**: 首次部署后请立即修改默认密码，并定期备份数据！