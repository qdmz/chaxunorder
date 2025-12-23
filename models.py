from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(120), unique=True, nullable=False)
    barcode = db.Column(db.String(120), unique=True, nullable=True)
    name = db.Column(db.String(256), nullable=False)
    spec = db.Column(db.String(256), nullable=True)
    model = db.Column(db.String(256), nullable=True)
    retail_price = db.Column(db.Float, nullable=True)
    wholesale_price = db.Column(db.Float, nullable=True)
    image_filename = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            'image_filename': self.image_filename,
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    customer_name = db.Column(db.String(256), nullable=True)
    customer_phone = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
