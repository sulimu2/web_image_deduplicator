#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能IP表情图片分类系统 - 独立启动脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('ip_classification')

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 智能IP表情图片分类系统")
    print("=" * 60)
    print("功能特性:")
    print("  ✅ 基于深度学习的智能图片识别")
    print("  ✅ 特定IP表情自动分类")
    print("  ✅ 可视化分类结果展示")
    print("  ✅ 批量处理与文件整理")
    print("=" * 60)
    
    # 检查依赖
    try:
        import flask
        import torch
        import transformers
        import cv2
        logger.info("✅ 核心依赖检查通过")
    except ImportError as e:
        logger.error(f"❌ 依赖缺失: {e}")
        print("\n请安装必要依赖:")
        print("pip install -r requirements.txt")
        return
    
    # 设置端口
    port = int(os.environ.get('IP_CLASSIFICATION_PORT', 5020))
    
    try:
        from app import app
        
        logger.info(f"🚀 启动IP分类服务 (端口: {port})")
        print(f"\n📱 访问地址: http://localhost:{port}/ip-classification")
        print("🔧 API文档: http://localhost:{port}/api/ip-classification/health")
        print("⏹️  按 Ctrl+C 停止服务")
        print("=" * 60)
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )
        
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()