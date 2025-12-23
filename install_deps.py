#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖安装脚本
"""

import subprocess
import sys

def install_package(package):
    """安装Python包"""
    try:
        print(f"正在安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {package} 安装失败")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("     安装产品查询系统依赖")
    print("=" * 50)
    
    # 基础依赖
    packages = [
        "flask>=2.3.0",
        "flask-sqlalchemy>=3.0.0",
        "flask-admin>=1.6.0",
        "flask-wtf>=1.1.0",
        "wtforms>=3.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "Pillow>=10.0.0",
        "Werkzeug>=2.3.0",
        "Jinja2>=3.1.0",
        "email-validator>=2.0.0",
        "SQLAlchemy>=2.0.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
    ]
    
    # 可选依赖
    optional_packages = [
        "aliyun-python-sdk-core>=2.13.36",
        "python-barcode>=0.15.0",
        "opencv-python>=4.8.0",
    ]
    
    print("\n【安装基础依赖】")
    success_count = 0
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n基础依赖安装完成: {success_count}/{len(packages)}")
    
    print("\n【安装可选依赖】")
    optional_success = 0
    
    for package in optional_packages:
        if install_package(package):
            optional_success += 1
    
    print(f"\n可选依赖安装完成: {optional_success}/{len(optional_packages)}")
    
    print("\n【验证安装】")
    try:
        import flask
        import flask_sqlalchemy
        import pandas
        import werkzeug
        import jinja2
        print("✓ 核心依赖验证成功")
        
        if optional_success > 0:
            try:
                import aliyunsdkcore
                print("✓ 阿里云SDK安装成功")
            except ImportError:
                pass
                
        print("\n🎉 依赖安装完成！")
        return 0
        
    except ImportError as e:
        print(f"✗ 依赖验证失败: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())