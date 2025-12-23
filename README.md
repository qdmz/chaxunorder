# 产品查询系统

一个基于Flask的销售和批发日用产品价格查询系统，支持产品查询、订单管理、批量导入等功能。

## 功能特性

### 🔍 产品查询
- 多条件搜索（名称、货号、条码、分类）
- 产品详情展示（图片、价格、库存等）
- 响应式设计，支持移动端访问

### 🛒 订单管理
- 在线下单功能
- 自动价格计算（零售/批发）
- 订单状态跟踪
- 库存实时更新

### 📦 产品管理
- 后台管理系统
- 批量导入产品数据
- 产品分类管理
- 图片上传和管理

### 🔔 通知系统
- 邮件通知
- 短信通知（阿里云短信服务）
- 库存预警
- 系统警报

### 📊 统计分析
- 销售统计图表
- 产品概况分析
- 订单数据导出
- 实时数据更新

## 技术栈

- **后端**: Flask, Flask-SQLAlchemy, Flask-Admin
- **前端**: Bootstrap 5, jQuery, Chart.js
- **数据库**: PostgreSQL / SQLite
- **缓存**: Redis
- **部署**: Docker, Docker Compose, Nginx

## 快速开始

### 环境要求

- Docker 20.0+
- Docker Compose 2.0+
- Python 3.8+ (如果不用Docker)

### 使用Docker部署（推荐）

1. **克隆项目**
```bash
git clone https://github.com/qdmz/chaxunorder.git
cd chaxunorder
```

2. **运行部署脚本**
```bash
chmod +x deploy.sh
./deploy.sh
```

3. **访问系统**
- Web应用: http://localhost:5000
- 管理后台: http://localhost:5000/admin

### 手动部署

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，配置数据库连接等信息
```

3. **初始化数据库**
```bash
python -c "
from app import create_app
from models import db
app = create_app()
app.app_context().push()
db.create_all()
"
```

4. **启动应用**
```bash
python app.py
```

## 配置说明

### 环境变量

主要配置项：

```bash
# Flask配置
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname

# 邮件配置
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password
NOTIFY_EMAIL=sales@example.com

# 短信配置（阿里云）
SMS_ACCESS_KEY=your-access-key
SMS_SECRET_KEY=your-secret-key
SMS_SIGN_NAME=产品查询系统
SMS_TEMPLATE_CODE=SMS_123456789
```

### 数据库配置

系统支持PostgreSQL和SQLite数据库：

- **生产环境**: 推荐使用PostgreSQL
- **开发环境**: 可以使用SQLite（默认）

### 文件上传

- 上传目录: `static/uploads/`
- 支持格式: JPG, PNG, GIF, CSV, Excel
- 最大文件大小: 16MB

## 使用指南

### 管理员登录

默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`

**重要**: 首次登录后请立即修改密码！

### 产品导入

支持批量导入产品数据：

1. **下载模板**
```bash
python import_products.py --sample
```

2. **准备数据**
按照模板格式填写产品信息

3. **执行导入**
```bash
python import_products.py your_data.csv
```

### 分类管理

在管理后台可以：
- 创建产品分类
- 设置分类层级
- 管理分类显示

### 订单处理

1. 客户在前台下单
2. 系统自动发送通知给销售人员
3. 销售人员在后台确认订单
4. 更新订单状态

## API接口

### 产品查询

```http
GET /search?q=关键词&sku=货号&barcode=条码&category=分类ID
```

### 产品详情

```http
GET /product/<产品ID>
```

### 创建订单

```http
POST /order/<产品ID>
Content-Type: application/x-www-form-urlencoded

quantity=数量&customer_name=姓名&customer_phone=电话
```

## 部署到生产环境

### 服务器要求

- **操作系统**: Linux (推荐Ubuntu 20.04+)
- **内存**: 最少2GB，推荐4GB+
- **存储**: 最少20GB可用空间
- **网络**: 稳定的互联网连接

### 安全配置

1. **修改默认密码**
2. **配置HTTPS**
3. **设置防火墙**
4. **定期备份数据**

### 性能优化

1. **数据库优化**
   - 添加索引
   - 配置连接池
   - 定期清理日志

2. **缓存配置**
   - Redis缓存
   - 静态文件缓存
   - CDN加速

3. **负载均衡**
   - 多实例部署
   - Nginx负载均衡
   - 数据库读写分离

## 监控和维护

### 日志管理

- 应用日志: `logs/`
- Nginx日志: `/var/log/nginx/`
- 数据库日志: Docker容器内

### 备份策略

1. **数据库备份**
```bash
# 导出数据
docker-compose exec db pg_dump -U chaxunuser chaxunorder > backup.sql

# 恢复数据
docker-compose exec -T db psql -U chaxunuser chaxunorder < backup.sql
```

2. **文件备份**
```bash
# 备份上传文件
tar -czf uploads_backup.tar.gz static/uploads/
```

### 监控指标

- 系统资源使用率
- 应用响应时间
- 数据库连接数
- 错误率统计

## 故障排除

### 常见问题

1. **应用无法启动**
   - 检查端口是否被占用
   - 确认环境变量配置
   - 查看应用日志

2. **数据库连接失败**
   - 检查数据库服务状态
   - 确认连接字符串
   - 验证用户权限

3. **文件上传失败**
   - 检查目录权限
   - 确认文件大小限制
   - 验证文件格式

### 调试模式

启用调试模式查看详细错误信息：

```bash
export FLASK_ENV=development
python app.py
```

## 开发指南

### 项目结构

```
chaxunorder/
├── app.py              # 主应用文件
├── models.py           # 数据模型
├── config.py           # 配置文件
├── utils.py            # 工具函数
├── templates/          # HTML模板
├── static/             # 静态文件
├── Dockerfile          # Docker镜像构建
├── docker-compose.yml  # Docker编排
└── requirements.txt    # Python依赖
```

### 添加新功能

1. 在`models.py`中定义数据模型
2. 在`app.py`中添加路由和视图
3. 在`templates/`中创建HTML模板
4. 更新依赖包（如需要）

### 代码规范

- 遵循PEP 8规范
- 使用类型提示
- 编写单元测试
- 添加必要的注释

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

## 支持

如有问题，请通过以下方式联系：

- 提交Issue: [GitHub Issues](https://github.com/qdmz/chaxunorder/issues)
- 邮件联系: admin@example.com

## 更新日志

### v1.0.0 (2024-12-23)
- 初始版本发布
- 完整的产品查询功能
- 订单管理系统
- 后台管理界面
- Docker部署支持

---

**注意**: 本系统仅供学习和参考使用，生产环境部署请确保充分测试和安全配置。