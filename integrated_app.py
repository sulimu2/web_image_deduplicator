#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成应用启动脚本
同时运行图片去重和IP分类功能
"""

import os
import sys
import threading
import time
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('integrated_app')

def run_image_deduplicator(port=5010):
    """运行图片去重应用"""
    try:
        from app import app as deduplicator_app
        
        logger.info(f"启动图片去重应用 (端口: {port})")
        deduplicator_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
    except Exception as e:
        logger.error(f"图片去重应用启动失败: {e}")

def run_ip_classification():
    """运行IP分类应用（集成到主应用）"""
    try:
        # IP分类功能已集成到主应用中
        logger.info("✅ IP分类功能已集成到主应用")
        return True
        
    except Exception as e:
        logger.error(f"IP分类功能集成失败: {e}")
        return False

def check_service_health(port, endpoint='/health', service_name='服务'):
    """检查服务健康状态"""
    import requests
    try:
        response = requests.get(f'http://localhost:{port}{endpoint}', timeout=5)
        if response.status_code == 200:
            logger.info(f"{service_name}健康检查通过")
            return True
        else:
            logger.warning(f"{service_name}健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"{service_name}健康检查失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("智能图片处理集成系统")
    print("=" * 60)
    print("功能模块:")
    print("  1. 高级图片去重系统")
    print("  2. 智能IP表情分类系统")
    print("=" * 60)
    
    # 设置端口（单端口集成）
    deduplicator_port = int(os.environ.get('DEDUPLICATOR_PORT', 5010))
    ip_classification_port = deduplicator_port  # 使用同一个端口
    port = deduplicator_port
    
    # 启动主应用（集成所有功能）
    deduplicator_thread = threading.Thread(
        target=run_image_deduplicator, 
        args=(port,),
        daemon=True
    )
    
    deduplicator_thread.start()
    
    # 等待应用启动
    logger.info("等待应用启动...")
    time.sleep(5)
    
    # 检查服务健康状态
    deduplicator_healthy = check_service_health(
        port, '/health', '图片去重服务'
    )
    
    ip_classification_healthy = check_service_health(
        port, '/api/ip-classification/health', 'IP分类服务'
    )
    
    # 显示访问信息
    print("\n" + "=" * 60)
    print("应用访问地址:")
    print(f"🏠 主页面: http://localhost:{port}")
    print(f"📷 图片去重: http://localhost:{port}")
    print(f"🤖 IP分类: http://localhost:{port}/ip-classification")
    print("=" * 60)
    
    if deduplicator_healthy and ip_classification_healthy:
        print("✅ 所有服务启动成功!")
    else:
        print("⚠️  部分服务可能未正常启动，请检查日志")
    
    print("\n按 Ctrl+C 退出系统")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在关闭应用...")
        sys.exit(0)

if __name__ == '__main__':
    # 添加当前目录到Python路径
    sys.path.insert(0, str(Path(__file__).parent))
    
    main()