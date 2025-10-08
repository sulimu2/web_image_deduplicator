#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP表情图片分类Web应用
集成到现有的图片去重系统中
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

from ip_image_classifier import IPImageClassifier

class IPClassificationApp:
    """IP分类Web应用"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app)
        
        # 配置
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
        self.app.config['UPLOAD_FOLDER'] = 'uploads'
        self.app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
        
        # 创建必要的目录
        Path(self.app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
        
        # 分类器实例
        self.classifier = None
        self.current_results = {}
        self.processing_status = {'status': 'idle', 'progress': 0}
        
        # 设置路由
        self.setup_routes()
        
        self.logger = self.setup_logging()
    
    def setup_logging(self) -> logging.Logger:
        """设置日志配置"""
        logger = logging.getLogger('ip_classification_app')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def setup_routes(self):
        """设置Flask路由"""
        
        @self.app.route('/ip-classification')
        def ip_classification_index():
            """IP分类主页面"""
            return render_template('ip_classification.html')
        
        @self.app.route('/api/ip-classification/scan', methods=['POST'])
        def api_ip_classification_scan():
            """API: IP分类扫描"""
            try:
                data = request.get_json()
                target_dir = data.get('target_dir')
                target_ip = data.get('target_ip', 'default')
                similarity_threshold = float(data.get('similarity_threshold', 0.7))
                
                if not target_dir:
                    return jsonify({'success': False, 'error': '请提供目录路径'})
                
                # 处理路径
                target_path = Path(target_dir)
                if not target_path.is_absolute():
                    target_path = Path.cwd().parent / target_path
                
                if not target_path.exists():
                    return jsonify({'success': False, 'error': f'目录不存在: {target_path}'})
                
                # 初始化分类器
                self.classifier = IPImageClassifier(
                    target_ip=target_ip, 
                    similarity_threshold=similarity_threshold
                )
                
                # 查找图片文件
                image_files = self.find_image_files(target_path)
                
                if not image_files:
                    return jsonify({'success': False, 'error': '未找到图片文件'})
                
                # 开始分类
                self.processing_status = {'status': 'classifying', 'progress': 0}
                
                results = self.classifier.classify_images(image_files)
                self.current_results = results
                
                # 生成报告
                report = self.classifier.generate_classification_report(results)
                
                self.processing_status = {'status': 'completed', 'progress': 100}
                
                return jsonify({
                    'success': True,
                    'report': report,
                    'total_images': len(image_files)
                })
                
            except Exception as e:
                self.processing_status = {'status': 'error', 'progress': 0, 'error': str(e)}
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/ip-classification/status')
        def api_ip_classification_status():
            """API: 获取处理状态"""
            return jsonify(self.processing_status)
        
        @self.app.route('/api/ip-classification/results')
        def api_ip_classification_results():
            """API: 获取分类结果"""
            if not self.current_results:
                return jsonify({'results': {}})
            
            # 构建简化的结果用于前端显示
            simplified_results = {}
            for category, images in self.current_results['classifications'].items():
                simplified_results[category] = {
                    'count': len(images),
                    'sample_images': images[:3]  # 只返回前3张作为示例
                }
            
            return jsonify({'results': simplified_results})
        
        @self.app.route('/api/ip-classification/organize', methods=['POST'])
        def api_ip_classification_organize():
            """API: 整理分类结果"""
            try:
                data = request.get_json()
                organize_config = data.get('config', {})
                dry_run = data.get('dry_run', False)
                
                if not self.current_results:
                    return jsonify({'success': False, 'error': '没有可整理的分类结果'})
                
                # 执行整理操作
                result = self.organize_classification_results(organize_config, dry_run)
                
                return jsonify({
                    'success': True,
                    'result': result
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/ip-classification/image/<path:image_path>')
        def api_ip_classification_image(image_path):
            """API: 获取图片文件"""
            try:
                # 处理图片路径
                decoded_path = Path(image_path)
                
                if decoded_path.is_absolute():
                    project_root = Path.cwd().parent
                    if str(decoded_path).startswith(str(project_root)):
                        safe_path = decoded_path.resolve()
                    else:
                        safe_path = (Path.cwd().parent / decoded_path).resolve()
                else:
                    project_root = Path.cwd().parent
                    safe_path = (project_root / decoded_path).resolve()
                
                # 安全检查
                if not str(safe_path).startswith(str(project_root)):
                    return jsonify({'error': '访问路径超出允许范围'}), 403
                
                if not safe_path.exists():
                    return jsonify({'error': '图片不存在'}), 404
                
                return send_from_directory(safe_path.parent, safe_path.name)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ip-classification/health')
        def api_ip_classification_health():
            """健康检查"""
            return jsonify({
                'status': 'healthy', 
                'service': 'ip_classification',
                'timestamp': datetime.now().isoformat()
            })
    
    def find_image_files(self, directory: Path) -> List[Path]:
        """查找目录中的图片文件"""
        image_files = []
        supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        for ext in supported_extensions:
            image_files.extend(list(directory.glob(f'**/*{ext}')))
            image_files.extend(list(directory.glob(f'**/*{ext.upper()}')))
        
        return list(set(image_files))  # 去重
    
    def organize_classification_results(self, config: Dict, dry_run: bool = False) -> Dict:
        """整理分类结果"""
        organize_result = {
            'files_moved': 0,
            'categories_organized': 0,
            'moved_files': []
        }
        
        try:
            base_dir = Path(config.get('base_dir', Path.cwd().parent))
            output_dir = base_dir / "ip_classification_results"
            
            if not dry_run:
                output_dir.mkdir(exist_ok=True)
            
            for category, images in self.current_results['classifications'].items():
                category_dir = output_dir / category
                
                if not dry_run:
                    category_dir.mkdir(exist_ok=True)
                
                self.logger.info(f"整理分类: {category} -> {len(images)} 张图片")
                
                for img_info in images:
                    try:
                        source_path = Path(img_info['file_path'])
                        target_path = category_dir / source_path.name
                        
                        # 处理文件名冲突
                        counter = 1
                        while target_path.exists():
                            stem = source_path.stem
                            suffix = source_path.suffix
                            target_path = category_dir / f"{stem}_{counter}{suffix}"
                            counter += 1
                        
                        if dry_run:
                            action = "将移动"
                        else:
                            action = "移动"
                            import shutil
                            shutil.move(str(source_path), str(target_path))
                        
                        organize_result['files_moved'] += 1
                        organize_result['moved_files'].append({
                            'source': str(source_path),
                            'target': str(target_path),
                            'category': category
                        })
                        
                        self.logger.info(f"  {action}: {source_path.name} -> {category}")
                        
                    except Exception as e:
                        self.logger.error(f"移动文件失败 {img_info['file_path']}: {e}")
                
                organize_result['categories_organized'] += 1
            
            return organize_result
            
        except Exception as e:
            self.logger.error(f"整理分类结果失败: {e}")
            return {
                'files_moved': 0,
                'categories_organized': 0,
                'error': str(e)
            }
    
    def run(self, host='0.0.0.0', port=5020, debug=False):
        """运行应用"""
        self.logger.info(f"IP分类应用启动中...")
        self.logger.info(f"访问地址: http://{host}:{port}/ip-classification")
        
        self.app.run(host=host, port=port, debug=debug)

def create_app():
    """创建应用实例"""
    return IPClassificationApp().app

if __name__ == '__main__':
    app = IPClassificationApp()
    app.run(debug=True)