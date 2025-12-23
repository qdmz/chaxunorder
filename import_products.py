import csv
import os
import requests
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

from config import Config
from models import db, Product
from app import create_app

app = create_app()

def download_image(url, dest_folder):
    try:
        os.makedirs(dest_folder, exist_ok=True)
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            filename = secure_filename(url.split('/')[-1]) or 'image'
            path = os.path.join(dest_folder, filename)
            with open(path, 'wb') as f:
                f.write(r.content)
            return filename
    except Exception as e:
        print('图片下载失败', e)
    return None

def import_from_csv(csv_path):
    with app.app_context():
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = row.get('sku') or row.get('货号')
                if not sku:
                    continue
                product = Product.query.filter_by(sku=sku).first()
                if not product:
                    product = Product(sku=sku)
                product.name = row.get('name') or row.get('名称') or product.name
                product.barcode = row.get('barcode') or row.get('条码') or product.barcode
                product.spec = row.get('spec') or row.get('规格') or product.spec
                product.model = row.get('model') or row.get('型号') or product.model
                try:
                    if row.get('retail_price'):
                        product.retail_price = float(row.get('retail_price'))
                    if row.get('wholesale_price'):
                        product.wholesale_price = float(row.get('wholesale_price'))
                except Exception:
                    pass
                image_url = row.get('image_url') or row.get('图片')
                if image_url:
                    fn = download_image(image_url, app.config['UPLOAD_FOLDER'])
                    if fn:
                        product.image_filename = fn
                db.session.add(product)
            db.session.commit()

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('用法: python import_products.py products.csv')
    else:
        import_from_csv(sys.argv[1])
