#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级图片去重网页应用 - 基于Flask框架
提供可视化界面和交互式操作
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os

# 导入原有的去重算法
try:
    # 尝试从父目录导入
    sys.path.append('..')
    from advanced_image_deduplicator import AdvancedImageDeduplicator
except ImportError:
    try:
        # 尝试从当前目录导入
        from .advanced_image_deduplicator import AdvancedImageDeduplicator
    except ImportError:
        # 如果导入失败，创建一个简单的替代类用于演示
        class AdvancedImageDeduplicator:
            def __init__(self, target_dir, similarity_threshold=0.75, hash_size=8, recursive=True):
                self.target_dir = target_dir
                self.similarity_threshold = similarity_threshold
                self.hash_size = hash_size
                self.recursive = recursive
                self.logger = self.setup_logging()
            
            def setup_logging(self):
                import logging
                logger = logging.getLogger('demo_deduplicator')
                logger.setLevel(logging.INFO)
                return logger
            
            def find_similar_images(self):
                self.logger.info("演示模式: 返回空结果")
                return {}
            
            def generate_report(self, groups, action):
                return {
                    'summary': {
                        'total_groups': 0, 
                        'total_images': 0,
                        'estimated_space_saved': 0
                    },
                    'groups': {}
                }
            
            def delete_similar_images(self, groups, dry_run=False):
                self.logger.info(f"演示模式: 模拟删除 {len(groups)} 个组")
                return {'files_deleted': 0, 'space_saved': 0, 'total_groups': len(groups)}

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
CORS(app)

# 配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# 创建必要的目录
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

class WebDeduplicator:
    """网页版去重器"""
    
    def __init__(self):
        self.current_deduplicator = None
        self.similar_groups = {}
        self.processing_status = {'status': 'idle', 'progress': 0}
    
    def scan_directory(self, target_dir, similarity_threshold=0.75, hash_size=8, recursive=True):
        """扫描目录并查找相似图片"""
        try:
            self.processing_status = {'status': 'scanning', 'progress': 0}
            
            # 创建去重器实例
            self.current_deduplicator = AdvancedImageDeduplicator(
                target_dir, similarity_threshold, hash_size, recursive
            )
            
            # 查找相似图片
            self.similar_groups = self.current_deduplicator.find_similar_images()
            
            # 生成报告
            report = self.current_deduplicator.generate_report(self.similar_groups, "web_preview")
            
            # 确保所有数据都是JSON可序列化的
            serializable_groups = {}
            for group_key, images in self.similar_groups.items():
                serializable_images = []
                for img in images:
                    serializable_img = {
                        'path': str(img['path']),
                        'file_size': img['file_size'],
                        'creation_time': str(img['creation_time']),
                        'mod_time': img['mod_time'].isoformat() if hasattr(img['mod_time'], 'isoformat') else str(img['mod_time']),
                        'phash': str(img['phash']) if img['phash'] else None,
                        'dhash': str(img['dhash']) if img['dhash'] else None,
                        'whash': str(img['whash']) if img['whash'] else None
                    }
                    serializable_images.append(serializable_img)
                serializable_groups[group_key] = serializable_images
            
            self.processing_status = {'status': 'completed', 'progress': 100}
            return {'success': True, 'report': report, 'groups': serializable_groups}
            
        except Exception as e:
            self.processing_status = {'status': 'error', 'progress': 0, 'error': str(e)}
            return {'success': False, 'error': str(e)}
    
    def delete_selected_groups(self, group_keys):
        """删除选中的相似组"""
        try:
            if not self.current_deduplicator or not self.similar_groups:
                return {'success': False, 'error': '没有可处理的相似组'}
            
            # 筛选出选中的组
            selected_groups = {key: self.similar_groups[key] for key in group_keys if key in self.similar_groups}
            
            if not selected_groups:
                return {'success': False, 'error': '没有选中任何组'}
            
            # 执行删除操作
            result = self.current_deduplicator.delete_similar_images(selected_groups, dry_run=False)
            
            # 更新剩余的组
            remaining_groups = {key: self.similar_groups[key] for key in self.similar_groups if key not in group_keys}
            self.similar_groups = remaining_groups
            
            # 生成删除报告
            report = self.current_deduplicator.generate_report(selected_groups, "delete_selected")
            
            return {
                'success': True, 
                'result': result,
                'remaining_groups_count': len(remaining_groups),
                'report': report
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_all_groups(self):
        """删除所有相似组"""
        try:
            if not self.current_deduplicator or not self.similar_groups:
                return {'success': False, 'error': '没有可处理的相似组'}
            
            # 执行删除操作
            result = self.current_deduplicator.delete_similar_images(self.similar_groups, dry_run=False)
            
            # 清空相似组
            self.similar_groups = {}
            
            return {
                'success': True, 
                'result': result,
                'report': self.current_deduplicator.generate_report({}, "delete_all")
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# 创建全局去重器实例
deduplicator = WebDeduplicator()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """API: 扫描目录"""
    try:
        data = request.get_json()
        target_dir = data.get('target_dir')
        similarity_threshold = float(data.get('similarity_threshold', 0.75))
        hash_size = int(data.get('hash_size', 8))
        recursive = bool(data.get('recursive', True))
        
        if not target_dir:
            return jsonify({'success': False, 'error': '请提供目录路径'})
        
        # 处理相对路径和绝对路径
        target_path = Path(target_dir)
        if not target_path.is_absolute():
            # 如果是相对路径，相对于当前工作目录的父目录
            # 因为用户选择的目录可能在web_image_deduplicator的父目录中
            target_path = Path.cwd().parent / target_path
        
        # 检查目录是否存在
        if not target_path.exists():
            return jsonify({'success': False, 'error': f'目录不存在: {target_path}'})
        
        if not target_path.is_dir():
            return jsonify({'success': False, 'error': f'路径不是目录: {target_dir}'})
        
        # 使用绝对路径进行扫描
        result = deduplicator.scan_directory(str(target_path), similarity_threshold, hash_size, recursive)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def api_status():
    """API: 获取处理状态"""
    return jsonify(deduplicator.processing_status)

@app.route('/api/delete/selected', methods=['POST'])
def api_delete_selected():
    """API: 删除选中的组"""
    try:
        data = request.get_json()
        group_keys = data.get('group_keys', [])
        
        result = deduplicator.delete_selected_groups(group_keys)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete/all', methods=['POST'])
def api_delete_all():
    """API: 删除所有组"""
    try:
        result = deduplicator.delete_all_groups()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/image/<path:image_path>')
def api_image(image_path):
    """API: 获取图片文件"""
    try:
        # 解码URL编码的路径
        decoded_path = Path(image_path)
        
        # 处理绝对路径：如果路径已经是绝对路径，直接使用
        if decoded_path.is_absolute():
            # 检查路径是否在项目根目录内
            project_root = Path.cwd().parent  # 项目根目录
            if str(decoded_path).startswith(str(project_root)):
                safe_path = decoded_path.resolve()
            else:
                # 如果绝对路径不在项目根目录内，尝试作为相对路径处理
                safe_path = (Path.cwd().parent / decoded_path).resolve()
        else:
            # 如果是相对路径，相对于项目根目录
            project_root = Path.cwd().parent  # 项目根目录
            safe_path = (project_root / decoded_path).resolve()
        
        # 安全检查：确保路径在允许的目录内
        # 允许访问项目根目录及其子目录
        project_root = Path.cwd().parent
        if not str(safe_path).startswith(str(project_root)):
            # 调试信息：打印路径信息
            print(f"安全检查失败: safe_path={safe_path}, project_root={project_root}")
            return jsonify({'error': '访问路径超出允许范围'}), 403
        
        if not safe_path.exists():
            print(f"图片不存在: {safe_path}")
            return jsonify({'error': f'图片不存在: {safe_path}'}), 404
        
        if not safe_path.is_file():
            return jsonify({'error': '路径不是文件'}), 400
        
        # 返回图片文件
        return send_from_directory(safe_path.parent, safe_path.name)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups')
def api_groups():
    """API: 获取当前相似组信息"""
    try:
        if not deduplicator.similar_groups:
            return jsonify({'groups': {}})
        
        # 构建组信息（不包含完整的图片数据，只包含基本信息）
        groups_info = {}
        for key, images in deduplicator.similar_groups.items():
            groups_info[key] = {
                'count': len(images),
                'representative': str(images[0]['path']) if images else '',
                'total_size': sum(img['file_size'] for img in images),
                'space_savings': sum(img['file_size'] for img in images[1:]) if len(images) > 1 else 0
            }
        
        return jsonify({'groups': groups_info})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/group/<group_key>')
def api_group_detail(group_key):
    """API: 获取特定组的详细信息"""
    try:
        if group_key not in deduplicator.similar_groups:
            return jsonify({'error': '组不存在'}), 404
        
        images = deduplicator.similar_groups[group_key]
        group_info = {
            'key': group_key,
            'images': []
        }
        
        for i, img in enumerate(images):
            # 确保所有数据都是JSON可序列化的
            group_info['images'].append({
                'path': str(img['path']),
                'file_size': img['file_size'],
                'creation_time': str(img['creation_time']) if img['creation_time'] else None,
                'mod_time': img['mod_time'].isoformat() if hasattr(img['mod_time'], 'isoformat') else str(img['mod_time']),
                'is_representative': i == 0
            })
        
        return jsonify(group_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("高级图片去重网页应用启动中...")
    print("访问地址: http://localhost:5010")
    print("API文档: http://localhost:5010/health")
    
    app.run(host='0.0.0.0', port=5010, debug=True)