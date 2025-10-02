#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示测试脚本 - 验证网页应用功能
"""

import sys
import os
import json
from pathlib import Path

def test_imports():
    """测试模块导入"""
    print("=" * 50)
    print("测试模块导入")
    print("=" * 50)
    
    try:
        from app import app
        print("✅ Flask应用导入成功")
        print(f"   应用名称: {app.name}")
        print(f"   调试模式: {app.debug}")
    except Exception as e:
        print(f"❌ Flask应用导入失败: {e}")
        return False
    
    try:
        from flask import Flask, render_template, request, jsonify
        print("✅ Flask组件导入成功")
    except Exception as e:
        print(f"❌ Flask组件导入失败: {e}")
        return False
    
    return True

def test_templates():
    """测试模板文件"""
    print("\n" + "=" * 50)
    print("测试模板文件")
    print("=" * 50)
    
    template_path = Path("templates/index.html")
    if template_path.exists():
        print("✅ 主模板文件存在")
        content = template_path.read_text(encoding='utf-8')
        if "图片去重" in content:
            print("✅ 模板内容包含中文标题")
        else:
            print("⚠️  模板内容可能有问题")
    else:
        print("❌ 主模板文件不存在")
        return False
    
    return True

def test_static_files():
    """测试静态文件"""
    print("\n" + "=" * 50)
    print("测试静态文件")
    print("=" * 50)
    
    static_files = [
        "static/css/style.css",
        "static/js/app.js"
    ]
    
    all_exists = True
    for file_path in static_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            all_exists = False
    
    return all_exists

def test_configuration():
    """测试应用配置"""
    print("\n" + "=" * 50)
    print("测试应用配置")
    print("=" * 50)
    
    try:
        from app import app
        
        # 检查关键配置
        config_checks = [
            ('SECRET_KEY', bool),
            ('DEBUG', bool),
            ('UPLOAD_FOLDER', str)
        ]
        
        for key, expected_type in config_checks:
            value = app.config.get(key)
            if value is not None:
                if isinstance(value, expected_type):
                    print(f"✅ 配置 {key}: {type(value).__name__} = {value if len(str(value)) < 20 else str(value)[:20] + '...'}")
                else:
                    print(f"⚠️  配置 {key} 类型不匹配: 期望 {expected_type.__name__}, 实际 {type(value).__name__}")
            else:
                print(f"⚠️  配置 {key} 未设置")
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 50)
    print("测试API端点")
    print("=" * 50)
    
    try:
        from app import app
        
        # 获取所有路由
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'path': str(rule)
                })
        
        print(f"✅ 发现 {len(routes)} 个路由端点")
        
        # 检查关键端点
        required_endpoints = [
            ('index', '/'),
            ('scan_directory', '/api/scan'),
            ('get_groups', '/api/groups'),
            ('health_check', '/health')
        ]
        
        found_endpoints = []
        for endpoint, path in required_endpoints:
            for route in routes:
                if route['path'] == path:
                    found_endpoints.append((endpoint, path))
                    print(f"✅ 端点 {endpoint}: {path}")
                    break
            else:
                print(f"❌ 端点 {endpoint} ({path}) 未找到")
        
        return len(found_endpoints) >= len(required_endpoints) * 0.8  # 允许部分缺失
    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("高级图片去重网页应用 - 功能测试")
    print("=" * 60)
    
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"工作目录: {os.getcwd()}")
    
    # 运行测试
    tests = [
        test_imports,
        test_templates,
        test_static_files,
        test_configuration,
        test_api_endpoints
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
            results.append(False)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！应用可以正常运行。")
        print("\n启动命令:")
        print("  python run.py")
        print("  ./start.sh")
        print("\n访问地址: http://localhost:5010")
    elif passed >= total * 0.7:
        print("⚠️  大部分测试通过，应用基本可用。")
    else:
        print("❌ 测试失败较多，需要修复问题。")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)