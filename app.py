import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import smtplib
from email.message import EmailMessage
import requests

from config import Config
from models import db, Product, Order

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    admin = Admin(app, name='后台管理', template_mode='bootstrap4')
    class ProductAdmin(ModelView):
        column_list = ('sku','name','barcode','spec','model','retail_price','wholesale_price','image_filename')
        form_excluded_columns = ('created_at',)

        def on_model_change(self, form, model, is_created):
            # handle file upload field if present in form
            pass

    admin.add_view(ProductAdmin(Product, db.session))
    admin.add_view(ModelView(Order, db.session))

    @app.before_first_request
    def create_tables():
        db.create_all()

    @app.route('/')
    def index():
        return redirect(url_for('search'))

    @app.route('/search', methods=['GET','POST'])
    def search():
        q = ''
        products = []
        if request.method == 'POST':
            q = request.form.get('q','').strip()
            sku = request.form.get('sku','').strip()
            barcode = request.form.get('barcode','').strip()
            query = Product.query
            if q:
                query = query.filter(Product.name.ilike(f"%{q}%"))
            if sku:
                query = query.filter(Product.sku==sku)
            if barcode:
                query = query.filter(Product.barcode==barcode)
            products = query.all()
        return render_template('search.html', products=products, q=q)

    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        p = Product.query.get_or_404(product_id)
        return render_template('result.html', p=p)

    class OrderForm(FlaskForm):
        quantity = IntegerField('数量', default=1, validators=[DataRequired()])
        customer_name = StringField('姓名')
        customer_phone = StringField('电话')
        submit = SubmitField('下单')

    def send_order_notification(order, product):
        cfg = app.config
        try:
            msg = EmailMessage()
            msg['Subject'] = f'新订单: {product.name} x{order.quantity}'
            msg['From'] = cfg['SMTP_USERNAME'] or 'noreply@example.com'
            msg['To'] = cfg['NOTIFY_EMAIL']
            body = f"订单ID: {order.id}\n产品: {product.name}\n数量: {order.quantity}\n客户: {order.customer_name} {order.customer_phone}"
            msg.set_content(body)
            if cfg['SMTP_USERNAME'] and cfg['SMTP_PASSWORD']:
                with smtplib.SMTP(cfg['SMTP_SERVER'], cfg['SMTP_PORT']) as s:
                    s.starttls()
                    s.login(cfg['SMTP_USERNAME'], cfg['SMTP_PASSWORD'])
                    s.send_message(msg)
            else:
                print('SMTP 未配置，订单通知已打印：')
                print(body)
        except Exception as e:
            print('发送通知失败', e)

    @app.route('/order/<int:product_id>', methods=['GET','POST'])
    def order(product_id):
        p = Product.query.get_or_404(product_id)
        form = OrderForm()
        if form.validate_on_submit():
            o = Order(product_id=p.id, quantity=form.quantity.data,
                      customer_name=form.customer_name.data,
                      customer_phone=form.customer_phone.data)
            db.session.add(o)
            db.session.commit()
            send_order_notification(o, p)
            return render_template('order_confirm.html', order=o, product=p)
        return render_template('order_confirm.html', order=None, product=p, form=form)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
