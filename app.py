import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, IntegerField, FloatField, SubmitField, TextAreaField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage
import requests
import csv
import io
import uuid
import pandas as pd
from PIL import Image

from config import Config
from models import db, Product, Order, User, SystemSetting, Category
from utils import send_email_notification, send_sms_notification, fetch_product_image, allowed_file, resize_image

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf.init_app(app)

    # 创建必要的目录
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'temp'), exist_ok=True)

    db.init_app(app)

    # 管理后台设置
    admin = Admin(app, name='后台管理', template_mode='bootstrap4', url='/admin')
    
    class ProductAdmin(ModelView):
        column_list = ('sku', 'name', 'barcode', 'spec', 'model', 'retail_price', 'wholesale_price', 'category', 'stock_quantity', 'image_filename', 'is_active', 'created_at')
        column_searchable_list = ('name', 'sku', 'barcode')
        column_filters = ('category', 'is_active', 'created_at')
        form_columns = ('sku', 'name', 'barcode', 'spec', 'model', 'retail_price', 'wholesale_price', 'category', 'stock_quantity', 'description', 'image_filename', 'is_active')
        form_excluded_columns = ('created_at', 'updated_at')
        
        def on_model_change(self, form, model, is_created):
            if is_created:
                model.created_at = datetime.utcnow()

    class OrderAdmin(ModelView):
        column_list = ('id', 'product', 'quantity', 'customer_name', 'customer_phone', 'status', 'total_amount', 'created_at')
        column_searchable_list = ('customer_name', 'customer_phone')
        column_filters = ('status', 'created_at')
        form_columns = ('product', 'quantity', 'customer_name', 'customer_phone', 'status', 'notes')
        
    class CategoryAdmin(ModelView):
        column_list = ('name', 'description', 'parent', 'sort_order', 'is_active')
        
    class UserAdmin(ModelView):
        column_list = ('username', 'email', 'role', 'is_active', 'created_at')
        form_columns = ('username', 'email', 'password', 'role', 'is_active')
        
        def on_model_change(self, form, model, is_created):
            if is_created and model.password:
                model.password = generate_password_hash(model.password)

    admin.add_view(ProductAdmin(Product, db.session))
    admin.add_view(OrderAdmin(Order, db.session))
    admin.add_view(CategoryAdmin(Category, db.session))
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(ModelView(SystemSetting, db.session))

    # 创建默认管理员账户
    @app.before_first_request
    def create_tables():
        db.create_all()
        
        # 创建默认管理员账户
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin_user)
            
        # 创建默认分类
        if not Category.query.first():
            default_category = Category(
                name='日用品',
                description='日用产品分类'
            )
            db.session.add(default_category)
            
        # 创建默认系统设置
        if not SystemSetting.query.first():
            default_settings = [
                SystemSetting(key='site_name', value='产品查询系统'),
                SystemSetting(key='smtp_server', value='smtp.example.com'),
                SystemSetting(key='smtp_port', value='587'),
                SystemSetting(key='notify_email', value='sales@example.com'),
                SystemSetting(key='enable_email', value='true'),
                SystemSetting(key='enable_sms', value='false')
            ]
            for setting in default_settings:
                db.session.add(setting)
                
        db.session.commit()

    @app.route('/')
    def index():
        return redirect(url_for('search'))

    @app.route('/search', methods=['GET', 'POST'])
    def search():
        q = request.args.get('q', '').strip() if request.method == 'GET' else request.form.get('q', '').strip()
        sku = request.args.get('sku', '').strip() if request.method == 'GET' else request.form.get('sku', '').strip()
        barcode = request.args.get('barcode', '').strip() if request.method == 'GET' else request.form.get('barcode', '').strip()
        category = request.args.get('category', '') if request.method == 'GET' else request.form.get('category', '')
        
        products = []
        categories = Category.query.filter_by(is_active=True).all()
        
        if q or sku or barcode or category:
            query = Product.query.filter_by(is_active=True)
            if q:
                query = query.filter(Product.name.ilike(f"%{q}%"))
            if sku:
                query = query.filter(Product.sku.ilike(f"%{sku}%"))
            if barcode:
                query = query.filter(Product.barcode == barcode)
            if category:
                query = query.filter(Product.category_id == category)
            
            products = query.order_by(Product.created_at.desc()).limit(100).all()
            
        return render_template('search.html', products=products, q=q, sku=sku, barcode=barcode, 
                             category=category, categories=categories)

    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        p = Product.query.get_or_404(product_id)
        if not p.is_active:
            flash('该产品已下架', 'error')
            return redirect(url_for('search'))
        return render_template('result.html', p=p)

    @app.route('/order/<int:product_id>', methods=['GET', 'POST'])
    def order(product_id):
        p = Product.query.get_or_404(product_id)
        if not p.is_active:
            flash('该产品已下架', 'error')
            return redirect(url_for('search'))
            
        form = OrderForm()
        
        if form.validate_on_submit():
            # 检查库存
            if p.stock_quantity and p.stock_quantity < form.quantity.data:
                flash('库存不足', 'error')
                return render_template('order_confirm.html', product=p, form=form)
                
            # 计算总金额
            unit_price = p.wholesale_price if form.quantity.data >= 10 else p.retail_price
            total_amount = unit_price * form.quantity.data
            
            order = Order(
                product_id=p.id,
                quantity=form.quantity.data,
                customer_name=form.customer_name.data,
                customer_phone=form.customer_phone.data,
                total_amount=total_amount,
                status='pending',
                notes=form.notes.data
            )
            
            db.session.add(order)
            
            # 更新库存
            if p.stock_quantity:
                p.stock_quantity -= form.quantity.data
                
            db.session.commit()
            
            # 发送通知
            send_notifications(order, p)
            
            return render_template('order_success.html', order=order, product=p)
            
        return render_template('order_confirm.html', product=p, form=form)

    @app.route('/upload_product', methods=['GET', 'POST'])
    def upload_product():
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('没有选择文件', 'error')
                return redirect(request.url)
                
            file = request.files['file']
            if file.filename == '':
                flash('没有选择文件', 'error')
                return redirect(request.url)
                
            if file and allowed_file(file.filename, ['csv', 'xlsx']):
                try:
                    if file.filename.endswith('.csv'):
                        # 处理CSV文件
                        stream = io.StringIO(file.read().decode('utf-8'))
                        csv_reader = csv.DictReader(stream)
                        
                        for row in csv_reader:
                            product = Product(
                                sku=row.get('sku', ''),
                                name=row.get('name', ''),
                                barcode=row.get('barcode', ''),
                                spec=row.get('spec', ''),
                                model=row.get('model', ''),
                                retail_price=float(row.get('retail_price', 0)),
                                wholesale_price=float(row.get('wholesale_price', 0)),
                                stock_quantity=int(row.get('stock_quantity', 0)),
                                description=row.get('description', '')
                            )
                            db.session.add(product)
                            
                    elif file.filename.endswith(('.xlsx', '.xls')):
                        # 处理Excel文件
                        try:
                            df = pd.read_excel(file)
                            # 重命名列以匹配标准格式
                            column_mapping = {
                                '货号': 'sku',
                                '产品名称': 'name',
                                '品名': 'name', 
                                '名称': 'name',
                                '条码': 'barcode',
                                '规格': 'spec',
                                '型号': 'model',
                                '零售价': 'retail_price',
                                '零售价格': 'retail_price',
                                '批发价': 'wholesale_price',
                                '批发价格': 'wholesale_price',
                                '库存': 'stock_quantity',
                                '库存数量': 'stock_quantity',
                                '描述': 'description',
                                '分类': 'category'
                            }
                            df = df.rename(columns=column_mapping)
                            
                            for index, row in df.iterrows():
                                product = Product(
                                    sku=str(row.get('sku', '')),
                                    name=str(row.get('name', '')),
                                    barcode=str(row.get('barcode', '')) if pd.notna(row.get('barcode')) else '',
                                    spec=str(row.get('spec', '')) if pd.notna(row.get('spec')) else '',
                                    model=str(row.get('model', '')) if pd.notna(row.get('model')) else '',
                                    retail_price=float(row.get('retail_price', 0)) if pd.notna(row.get('retail_price')) else 0,
                                    wholesale_price=float(row.get('wholesale_price', 0)) if pd.notna(row.get('wholesale_price')) else 0,
                                    stock_quantity=int(row.get('stock_quantity', 0)) if pd.notna(row.get('stock_quantity')) else 0,
                                    description=str(row.get('description', '')) if pd.notna(row.get('description')) else ''
                                )
                                db.session.add(product)
                        except Exception as e:
                            flash(f'Excel文件处理失败: {str(e)}', 'error')
                            return redirect(request.url)
                        
                    db.session.commit()
                    flash('产品导入成功', 'success')
                    return redirect(url_for('search'))
                    
                except Exception as e:
                    flash(f'导入失败: {str(e)}', 'error')
                    return redirect(request.url)
            else:
                flash('不支持的文件格式', 'error')
                return redirect(request.url)
                
        return render_template('upload_product.html')

    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        if request.method == 'POST':
            for key, value in request.form.items():
                setting = SystemSetting.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    setting = SystemSetting(key=key, value=value)
                    db.session.add(setting)
            db.session.commit()
            flash('设置保存成功', 'success')
            return redirect(url_for('settings'))
            
        settings = SystemSetting.query.all()
        settings_dict = {s.key: s.value for s in settings}
        return render_template('settings.html', settings=settings_dict)

    @app.route('/statistics')
    def statistics():
        total_products = Product.query.count()
        active_products = Product.query.filter_by(is_active=True).count()
        inactive_products = total_products - active_products
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        
        # 计算总销售额
        total_sales = db.session.query(db.func.sum(Order.total_amount)).filter(Order.status != 'cancelled').scalar() or 0
        
        # 获取最近订单
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        
        # 获取热门产品（按销量）
        top_products = Product.query.filter_by(is_active=True).limit(10).all()
        
        # 获取库存不足产品
        low_stock_products = Product.query.filter(
            Product.stock_quantity <= 10,
            Product.stock_quantity > 0,
            Product.is_active == True
        ).all()
        
        return render_template('statistics.html', 
                             total_products=total_products,
                             active_products=active_products,
                             inactive_products=inactive_products,
                             total_orders=total_orders,
                             pending_orders=pending_orders,
                             total_sales=total_sales,
                             recent_orders=recent_orders,
                             top_products=top_products,
                             low_stock_products=low_stock_products)

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    def send_notifications(order, product):
        settings = {s.key: s.value for s in SystemSetting.query.all()}
        
        # 发送邮件通知
        if settings.get('enable_email', 'false').lower() == 'true':
            send_email_notification(order, product, settings)
            
        # 发送短信通知
        if settings.get('enable_sms', 'false').lower() == 'true':
            send_sms_notification(order, product, settings)

    return app

# 表单类
class OrderForm(FlaskForm):
    quantity = IntegerField('数量', default=1, validators=[DataRequired(), NumberRange(min=1)])
    customer_name = StringField('姓名', validators=[DataRequired(), Length(min=2, max=50)])
    customer_phone = StringField('电话', validators=[DataRequired(), Length(min=11, max=11)])
    notes = TextAreaField('备注')
    submit = SubmitField('提交订单')

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)