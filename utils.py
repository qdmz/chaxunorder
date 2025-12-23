import os
import smtplib
import requests
import uuid
from email.message import EmailMessage
from PIL import Image
from werkzeug.utils import secure_filename
from io import BytesIO
import re

def allowed_file(filename, allowed_extensions=None):
    """检查文件扩展名是否允许"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def resize_image(image_path, max_size=(800, 600)):
    """调整图片尺寸"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(image_path, optimize=True, quality=85)
        return True
    except Exception as e:
        print(f"图片压缩失败: {e}")
        return False

def send_email_notification(order, product, settings):
    """发送邮件通知"""
    try:
        msg = EmailMessage()
        msg['Subject'] = f'新订单通知 - {product.name} x{order.quantity}'
        msg['From'] = settings.get('smtp_username', 'noreply@example.com')
        msg['To'] = settings.get('notify_email', 'sales@example.com')
        
        body = f"""
订单详情:
=================
订单ID: {order.id}
产品名称: {product.name}
产品货号: {product.sku}
订购数量: {order.quantity}
单价: {order.unit_price}
总金额: {order.total_amount}
客户姓名: {order.customer_name}
客户电话: {order.customer_phone}
下单时间: {order.created_at}
备注: {order.notes or '无'}

请及时处理订单！
        """
        
        msg.set_content(body)
        
        smtp_server = settings.get('smtp_server', 'smtp.example.com')
        smtp_port = int(settings.get('smtp_port', '587'))
        smtp_username = settings.get('smtp_username', '')
        smtp_password = settings.get('smtp_password', '')
        
        if smtp_username and smtp_password:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            print("邮件通知发送成功")
        else:
            print("SMTP未配置，邮件通知内容:")
            print(body)
            
    except Exception as e:
        print(f"发送邮件通知失败: {e}")

def send_sms_notification(order, product, settings):
    """发送短信通知"""
    try:
        # 这里使用阿里云短信服务示例
        # 需要先安装: pip install aliyun-python-sdk-core
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcore.acs_exception.exceptions import ServerException
        from aliyunsdkdysmsapi.request.v20170525.SendSmsRequest import SendSmsRequest
        
        access_key = settings.get('sms_access_key', '')
        secret_key = settings.get('sms_secret_key', '')
        sign_name = settings.get('sms_sign_name', '产品查询系统')
        template_code = settings.get('sms_template_code', 'SMS_123456789')
        
        if not access_key or not secret_key:
            print("短信服务未配置")
            return
            
        client = AcsClient(access_key, secret_key, 'cn-hangzhou')
        request = SendSmsRequest()
        
        # 接收短信的手机号码
        phone_numbers = settings.get('notify_phone', '')
        if not phone_numbers:
            print("未配置通知手机号")
            return
            
        request.set_PhoneNumbers(phone_numbers)
        request.set_SignName(sign_name)
        request.set_TemplateCode(template_code)
        
        # 短信模板参数
        template_param = {
            "product": product.name,
            "quantity": str(order.quantity),
            "customer": order.customer_name
        }
        request.set_TemplateParam(str(template_param))
        
        response = client.do_action_with_exception(request)
        print("短信通知发送成功")
        
    except ImportError:
        print("未安装阿里云短信SDK，请运行: pip install aliyun-python-sdk-core")
    except Exception as e:
        print(f"发送短信通知失败: {e}")

def fetch_product_image(product_name):
    """从网络获取产品图片"""
    try:
        # 这里使用百度图片搜索API示例
        # 实际使用时需要申请相应的API密钥
        search_url = f"https://image.baidu.com/search/index?tn=baiduimage&word={product_name}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # 这里需要解析HTML获取图片URL
            # 实际应用中可以使用更专业的图片API
            print(f"正在搜索 {product_name} 的图片...")
            return None
            
    except Exception as e:
        print(f"获取产品图片失败: {e}")
        return None

def generate_barcode_image(barcode_data):
    """生成条码图片"""
    try:
        import barcode
        from barcode.writer import ImageWriter
        
        # 创建条码对象
        code128 = barcode.get_barcode_class('code128')
        barcode_img = code128(barcode_data, writer=ImageWriter())
        
        # 保存条码图片
        filename = f"barcode_{barcode_data}.png"
        filepath = os.path.join('/tmp', filename)
        barcode_img.save(filepath)
        
        return filepath
        
    except ImportError:
        print("未安装条码生成库，请运行: pip install python-barcode")
        return None
    except Exception as e:
        print(f"生成条码失败: {e}")
        return None

def validate_phone(phone):
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_price(price):
    """格式化价格显示"""
    if price is None:
        return "0.00"
    return f"{price:.2f}"

def generate_unique_filename(filename):
    """生成唯一的文件名"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}" if ext else unique_id

def create_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """创建缩略图"""
    try:
        with Image.open(image_path) as img:
            # 创建缩略图，保持宽高比
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 创建一个新的白色背景图片
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', size, (255, 255, 255))
                # 将原始图片居中粘贴到背景上
                offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
                background.paste(img, offset)
                background.save(thumbnail_path, 'JPEG', quality=90)
            else:
                img.save(thumbnail_path, 'JPEG', quality=90)
                
        return True
    except Exception as e:
        print(f"创建缩略图失败: {e}")
        return False