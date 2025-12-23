from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(120), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(120), unique=True, nullable=True, index=True)
    name = db.Column(db.String(256), nullable=False, index=True)
    spec = db.Column(db.String(256), nullable=True)
    model = db.Column(db.String(256), nullable=True)
    retail_price = db.Column(db.Float, nullable=True)
    wholesale_price = db.Column(db.Float, nullable=True)
    stock_quantity = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(512), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    category = db.relationship('Category', backref=db.backref('products', lazy=True))
    orders = db.relationship('Order', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'barcode': self.barcode,
            'name': self.name,
            'spec': self.spec,
            'model': self.model,
            'retail_price': self.retail_price,
            'wholesale_price': self.wholesale_price,
            'stock_quantity': self.stock_quantity,
            'description': self.description,
            'image_filename': self.image_filename,
            'is_active': self.is_active,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=True)
    total_amount = db.Column(db.Float, nullable=True)
    customer_name = db.Column(db.String(256), nullable=True)
    customer_phone = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_amount': self.total_amount,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='user')  # admin, manager, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 自关联
    parent = db.relationship('Category', remote_side=[id], backref='children')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'parent_name': self.parent.name if self.parent else None,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }