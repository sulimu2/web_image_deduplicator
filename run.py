#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级图片去重网页应用 - 启动脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_dependencies():
    """检查依赖包是否安装"""
    required_packages = [
        'flask',
        'flask_cors', 
        'PIL',
        'numpy',
        'imagehash',
        'tqdm'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'PIL':
                __import__('PIL.Image')
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("缺少必要的依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def create_necessary_directories():
    """创建必要的目录结构"""
    directories = [
        'uploads',
        'static/uploads',
        'logs'
    ]
    
    for dir_name in directories:
        dir_path = current_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"创建目录: {dir_path}")

def setup_logging():
    """设置日志配置"""
    log_dir = current_dir / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """主函数"""
    print("=" * 60)
    print("高级图片去重网页应用")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建目录
    create_necessary_directories()
    
    # 设置日志
    setup_logging()
    
    # 导入并启动应用
    try:
        # 直接导入app模块
        from app import app
        
        print("\n应用信息:")
        print(f"  访问地址: http://localhost:5010")
        print(f"  API文档: http://localhost:5010/health")
        print(f"  工作目录: {current_dir}")
        print("\n启动中...")
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=5010,
            debug=True,
            threaded=True
        )
        
    except ImportError as e:
        print(f"导入应用失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"启动应用失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()