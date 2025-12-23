#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
产品数据批量导入脚本
支持从CSV、Excel文件导入产品数据
"""

import os
import sys
import csv
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import requests
import io

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Product, Category
from utils import allowed_file, resize_image, fetch_product_image

def import_from_csv(file_path):
    """从CSV文件导入产品"""
    app = create_app()
    with app.app_context():
        try:
            # 使用pandas读取CSV，支持更好的编码处理
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 检查必要的列
            required_columns = ['sku', 'name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"错误: 缺少必要的列: {missing_columns}")
                return False
            
            success_count = 0
            error_count = 0
            error_messages = []
            
            for index, row in df.iterrows():
                try:
                    # 检查SKU是否已存在
                    existing_product = Product.query.filter_by(sku=str(row['sku'])).first()
                    if existing_product:
                        print(f"跳过已存在的SKU: {row['sku']}")
                        continue
                    
                    # 创建产品对象
                    product = Product(
                        sku=str(row['sku']),
                        name=str(row['name']),
                        barcode=str(row.get('barcode', '')) if pd.notna(row.get('barcode')) else '',
                        spec=str(row.get('spec', '')) if pd.notna(row.get('spec')) else '',
                        model=str(row.get('model', '')) if pd.notna(row.get('model')) else '',
                        retail_price=float(row.get('retail_price', 0)) if pd.notna(row.get('retail_price')) else None,
                        wholesale_price=float(row.get('wholesale_price', 0)) if pd.notna(row.get('wholesale_price')) else None,
                        stock_quantity=int(row.get('stock_quantity', 0)) if pd.notna(row.get('stock_quantity')) else 0,
                        description=str(row.get('description', '')) if pd.notna(row.get('description')) else ''
                    )
                    
                    # 如果有分类，尝试查找或创建分类
                    category_name = row.get('category', '')
                    if pd.notna(category_name) and category_name:
                        category = Category.query.filter_by(name=str(category_name)).first()
                        if not category:
                            category = Category(name=str(category_name))
                            db.session.add(category)
                            db.session.flush()
                        product.category_id = category.id
                    
                    db.session.add(product)
                    db.session.commit()
                    
                    # 尝试获取产品图片
                    try:
                        image_url = fetch_product_image(product.name)
                        if image_url:
                            # 下载并保存图片
                            response = requests.get(image_url, timeout=10)
                            if response.status_code == 200:
                                image_data = response.content
                                # 生成文件名
                                filename = secure_filename(f"{product.sku}.jpg")
                                image_path = os.path.join('static/uploads', filename)
                                
                                # 保存图片
                                with open(image_path, 'wb') as f:
                                    f.write(image_data)
                                
                                # 调整图片大小
                                resize_image(image_path)
                                
                                # 更新产品记录
                                product.image_filename = filename
                                db.session.commit()
                    except Exception as e:
                        print(f"获取产品图片失败 {product.name}: {e}")
                    
                    success_count += 1
                    print(f"成功导入: {product.name} (SKU: {product.sku})")
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"第 {index + 2} 行导入失败: {e}"
                    error_messages.append(error_msg)
                    print(error_msg)
                    db.session.rollback()
            
            print(f"\n导入完成!")
            print(f"成功: {success_count} 个")
            print(f"失败: {error_count} 个")
            
            if error_messages:
                print("\n错误详情:")
                for msg in error_messages[:10]:  # 只显示前10个错误
                    print(f"  - {msg}")
                if len(error_messages) > 10:
                    print(f"  ... 还有 {len(error_messages) - 10} 个错误")
            
            return True
            
        except Exception as e:
            print(f"导入CSV文件失败: {e}")
            return False

def import_from_excel(file_path):
    """从Excel文件导入产品"""
    app = create_app()
    with app.app_context():
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, sheet_name=0)
            
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
            
            # 重命名列
            df = df.rename(columns=column_mapping)
            
            # 转换为CSV格式进行处理
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_buffer.seek(0)
            
            # 保存为临时CSV文件
            temp_csv_path = 'temp_import.csv'
            with open(temp_csv_path, 'w', encoding='utf-8') as f:
                f.write(csv_buffer.getvalue())
            
            # 调用CSV导入函数
            result = import_from_csv(temp_csv_path)
            
            # 清理临时文件
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
            
            return result
            
        except Exception as e:
            print(f"导入Excel文件失败: {e}")
            return False

def create_sample_csv():
    """创建示例CSV文件"""
    sample_data = [
        {
            'sku': 'PRD001',
            'name': '洗衣液',
            'barcode': '1234567890123',
            'spec': '2L/瓶',
            'model': 'LX-2000',
            'retail_price': 25.50,
            'wholesale_price': 20.00,
            'stock_quantity': 100,
            'description': '强力去污洗衣液，适用于各种织物',
            'category': '清洁用品'
        },
        {
            'sku': 'PRD002',
            'name': '洗洁精',
            'barcode': '2345678901234',
            'spec': '500ml/瓶',
            'model': 'XJ-001',
            'retail_price': 12.00,
            'wholesale_price': 9.50,
            'stock_quantity': 200,
            'description': '食品级洗洁精，去油效果好',
            'category': '清洁用品'
        },
        {
            'sku': 'PRD003',
            'name': '纸巾',
            'barcode': '3456789012345',
            'spec': '6包装',
            'model': 'ZJ-100',
            'retail_price': 18.00,
            'wholesale_price': 15.00,
            'stock_quantity': 150,
            'description': '原生木浆纸巾，柔软舒适',
            'category': '日用品'
        }
    ]
    
    filename = 'sample_products.csv'
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['sku', 'name', 'barcode', 'spec', 'model', 'retail_price', 'wholesale_price', 'stock_quantity', 'description', 'category']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(sample_data)
    
    print(f"已创建示例文件: {filename}")
    return filename

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python import_products.py <文件路径>    # 导入文件")
        print("  python import_products.py --sample     # 创建示例文件")
        print("  python import_products.py --help       # 显示帮助")
        return
    
    if sys.argv[1] == '--help':
        print("产品数据导入工具")
        print("支持的文件格式: CSV (.csv), Excel (.xlsx, .xls)")
        print("\n必需字段:")
        print("  - sku: 产品货号 (必填)")
        print("  - name: 产品名称 (必填)")
        print("\n可选字段:")
        print("  - barcode: 条码")
        print("  - spec: 规格")
        print("  - model: 型号")
        print("  - retail_price: 零售价格")
        print("  - wholesale_price: 批发价格")
        print("  - stock_quantity: 库存数量")
        print("  - description: 产品描述")
        print("  - category: 产品分类")
        return
    
    if sys.argv[1] == '--sample':
        create_sample_csv()
        return
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return
    
    # 检查文件格式
    if not allowed_file(file_path, ['csv', 'xlsx', 'xls']):
        print("错误: 不支持的文件格式")
        print("支持的格式: CSV (.csv), Excel (.xlsx, .xls)")
        return
    
    print(f"开始导入文件: {file_path}")
    
    # 根据文件类型选择导入方法
    if file_path.lower().endswith('.csv'):
        success = import_from_csv(file_path)
    elif file_path.lower().endswith(('.xlsx', '.xls')):
        success = import_from_excel(file_path)
    else:
        print("错误: 不支持的文件格式")
        return
    
    if success:
        print("导入完成!")
    else:
        print("导入失败!")

if __name__ == '__main__':
    main()