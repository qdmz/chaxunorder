import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-prod-2024")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件配置
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / 'static' / 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'csv', 'xlsx'}
    
    # 邮件配置
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.example.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "sales@example.com")
    
    # 短信配置（示例使用阿里云短信）
    SMS_ACCESS_KEY = os.environ.get("SMS_ACCESS_KEY", "")
    SMS_SECRET_KEY = os.environ.get("SMS_SECRET_KEY", "")
    SMS_SIGN_NAME = os.environ.get("SMS_SIGN_NAME", "产品查询系统")
    SMS_TEMPLATE_CODE = os.environ.get("SMS_TEMPLATE_CODE", "SMS_123456789")
    
    # 分页配置
    PRODUCTS_PER_PAGE = 20
    ORDERS_PER_PAGE = 50
    
    # 系统配置
    SITE_NAME = os.environ.get("SITE_NAME", "产品查询系统")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")