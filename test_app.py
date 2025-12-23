#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用测试脚本
验证应用是否能正常启动
"""

import os
import sys

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        from flask import Flask
        print("✓ Flask导入成功")
    except ImportError as e:
        print(f"✗ Flask导入失败: {e}")
        return False
    
    try:
        from flask_sqlalchemy import SQLAlchemy
        print("✓ Flask-SQLAlchemy导入成功")
    except ImportError as e:
        print(f"✗ Flask-SQLAlchemy导入失败: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ Pandas导入成功")
    except ImportError as e:
        print(f"✗ Pandas导入失败: {e}")
        return False
    
    return True

def test_config():
    """测试配置文件"""
    print("\n测试配置文件...")
    
    try:
        from config import Config
        config = Config()
        print("✓ 配置文件加载成功")
        
        # 检查必要的配置项
        if hasattr(config, 'SECRET_KEY'):
            print("✓ SECRET_KEY配置存在")
        else:
            print("✗ SECRET_KEY配置缺失")
            return False
            
        if hasattr(config, 'SQLALCHEMY_DATABASE_URI'):
            print("✓ 数据库配置存在")
        else:
            print("✗ 数据库配置缺失")
            return False
            
        return True
    except ImportError as e:
        print(f"✗ 配置文件导入失败: {e}")
        return False

def test_models():
    """测试模型文件"""
    print("\n测试数据模型...")
    
    try:
        from models import Product, Order, User, SystemSetting, Category
        print("✓ 数据模型导入成功")
        
        # 检查模型是否有必要的属性
        product = Product()
        if hasattr(product, 'id') and hasattr(product, 'name'):
            print("✓ Product模型正常")
        else:
            print("✗ Product模型异常")
            return False
            
        order = Order()
        if hasattr(order, 'id') and hasattr(order, 'product_id'):
            print("✓ Order模型正常")
        else:
            print("✗ Order模型异常")
            return False
            
        return True
    except ImportError as e:
        print(f"✗ 数据模型导入失败: {e}")
        return False

def test_app_creation():
    """测试应用创建"""
    print("\n测试应用创建...")
    
    try:
        # 设置测试环境
        os.environ['FLASK_ENV'] = 'development'
        
        from app import create_app
        app = create_app()
        
        print("✓ 应用创建成功")
        print(f"✓ 应用名称: {app.name}")
        print(f"✓ 调试模式: {app.debug}")
        
        return True
    except Exception as e:
        print(f"✗ 应用创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("     产品查询系统 - 应用测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置文件", test_config),
        ("数据模型", test_models),
        ("应用创建", test_app_creation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n【{test_name}】")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:12} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！应用可以正常运行。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项测试失败，请检查问题。")
        return 1

if __name__ == '__main__':
    sys.exit(main())