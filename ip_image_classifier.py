#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能IP表情图片分类器
基于深度学习的图像识别技术，识别特定IP相关的表情图片
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from datetime import datetime

import cv2
from PIL import Image, ImageFile
import torch
import torchvision.transforms as transforms
from transformers import CLIPProcessor, CLIPModel
from ultralytics import YOLO
from sklearn.metrics.pairwise import cosine_similarity

# 配置PIL以处理损坏的图片文件
ImageFile.LOAD_TRUNCATED_IMAGES = True

class IPImageClassifier:
    """智能IP表情图片分类器"""
    
    def __init__(self, target_ip: str = None, similarity_threshold: float = 0.7):
        """
        初始化分类器
        
        Args:
            target_ip: 目标IP名称
            similarity_threshold: 相似度阈值
        """
        self.target_ip = target_ip
        self.similarity_threshold = similarity_threshold
        self.logger = self.setup_logging()
        
        # 初始化模型
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"使用设备: {self.device}")
        
        # 加载模型
        self.clip_model = None
        self.clip_processor = None
        self.yolo_model = None
        self.ip_features = {}
        
        self.load_models()
        
        # 预定义IP特征库
        self.ip_feature_library = self.load_ip_feature_library()
    
    def setup_logging(self) -> logging.Logger:
        """设置日志配置"""
        logger = logging.getLogger('ip_image_classifier')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # 控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def load_models(self):
        """加载预训练模型"""
        try:
            # 加载CLIP模型用于特征提取和相似度计算
            self.logger.info("加载CLIP模型...")
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_model.to(self.device)
            
            # 加载YOLO模型用于目标检测
            self.logger.info("加载YOLO模型...")
            self.yolo_model = YOLO('yolov8n.pt')  # 使用轻量级版本
            
            self.logger.info("模型加载完成")
            
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            raise
    
    def load_ip_feature_library(self) -> Dict[str, List]:
        """加载IP特征库"""
        # 这里可以扩展为从文件或数据库加载预定义的IP特征
        ip_library = {
            "default": [
                "卡通人物", "动漫角色", "表情包", "贴纸", 
                "可爱形象", "吉祥物", "品牌形象"
            ],
            # 可以添加更多预定义的IP特征
            "douyin": [
                "抖音表情", "短视频贴纸", "网红形象", "流行元素"
            ],
            "wechat": [
                "微信表情", "聊天贴纸", "社交元素"
            ]
        }
        
        # 如果指定了目标IP，添加自定义特征
        if self.target_ip:
            ip_library[self.target_ip] = [
                f"{self.target_ip}角色", f"{self.target_ip}形象", 
                f"{self.target_ip}表情", f"{self.target_ip}贴纸"
            ]
        
        return ip_library
    
    def extract_image_features(self, image_path: Path) -> Optional[Dict]:
        """提取图片特征"""
        try:
            # 加载图片
            image = Image.open(image_path).convert('RGB')
            
            # 使用CLIP提取特征
            inputs = self.clip_processor(
                text=None,  # 只处理图片
                images=image, 
                return_tensors="pt", 
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                image_features = image_features.cpu().numpy()
            
            # 使用YOLO进行目标检测
            yolo_results = self.yolo_model(image_path)
            detected_objects = []
            
            for result in yolo_results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        label = self.yolo_model.names[class_id]
                        detected_objects.append({
                            'label': label,
                            'confidence': confidence,
                            'bbox': box.xyxy[0].cpu().numpy().tolist()
                        })
            
            return {
                'clip_features': image_features,
                'detected_objects': detected_objects,
                'image_size': image.size
            }
            
        except Exception as e:
            self.logger.warning(f"特征提取失败 {image_path}: {e}")
            return None
    
    def calculate_ip_similarity(self, image_features: np.ndarray, ip_keywords: List[str]) -> Dict:
        """计算图片与IP关键词的相似度"""
        try:
            # 将IP关键词转换为文本特征
            text_inputs = self.clip_processor(
                text=ip_keywords,
                return_tensors="pt",
                padding=True,
                truncation=True
            )
            text_inputs = {k: v.to(self.device) for k, v in text_inputs.items()}
            
            with torch.no_grad():
                text_features = self.clip_model.get_text_features(**text_inputs)
                text_features = text_features.cpu().numpy()
            
            # 计算余弦相似度
            similarities = cosine_similarity(image_features, text_features)
            max_similarity = float(np.max(similarities))
            best_match_index = int(np.argmax(similarities))
            best_match_keyword = ip_keywords[best_match_index]
            
            return {
                'max_similarity': max_similarity,
                'best_match': best_match_keyword,
                'all_similarities': similarities.flatten().tolist()
            }
            
        except Exception as e:
            self.logger.error(f"相似度计算失败: {e}")
            return {'max_similarity': 0.0, 'best_match': '', 'all_similarities': []}
    
    def analyze_image_content(self, image_path: Path) -> Dict:
        """分析图片内容并分类"""
        features = self.extract_image_features(image_path)
        if features is None:
            return {
                'classification': 'unknown',
                'confidence': 0.0,
                'reason': '特征提取失败',
                'detected_objects': []
            }
        
        classification_results = {}
        
        # 对每个IP库进行相似度计算
        for ip_name, ip_keywords in self.ip_feature_library.items():
            similarity_result = self.calculate_ip_similarity(
                features['clip_features'], ip_keywords
            )
            
            classification_results[ip_name] = {
                'similarity': similarity_result['max_similarity'],
                'best_match': similarity_result['best_match'],
                'confidence': similarity_result['max_similarity']
            }
        
        # 确定最佳分类
        best_ip = max(classification_results.items(), 
                     key=lambda x: x[1]['similarity'])
        
        ip_name, ip_info = best_ip
        confidence = ip_info['similarity']
        
        # 根据阈值确定分类
        if confidence >= self.similarity_threshold:
            classification = ip_name
        else:
            classification = 'unrelated'
        
        return {
            'classification': classification,
            'confidence': confidence,
            'best_match': ip_info['best_match'],
            'detected_objects': features['detected_objects'],
            'all_similarities': classification_results,
            'image_size': features['image_size']
        }
    
    def classify_images(self, image_files: List[Path]) -> Dict[str, List]:
        """批量分类图片"""
        self.logger.info(f"开始分类 {len(image_files)} 张图片")
        
        classification_results = defaultdict(list)
        
        for image_path in image_files:
            try:
                result = self.analyze_image_content(image_path)
                result['file_path'] = str(image_path)
                result['file_name'] = image_path.name
                result['file_size'] = image_path.stat().st_size
                
                classification_results[result['classification']].append(result)
                
                self.logger.info(f"分类结果: {image_path.name} -> {result['classification']} "
                               f"(置信度: {result['confidence']:.3f})")
                
            except Exception as e:
                self.logger.error(f"图片分类失败 {image_path}: {e}")
                error_result = {
                    'file_path': str(image_path),
                    'file_name': image_path.name,
                    'classification': 'error',
                    'confidence': 0.0,
                    'reason': str(e)
                }
                classification_results['error'].append(error_result)
        
        # 统计结果
        stats = {}
        for category, images in classification_results.items():
            stats[category] = len(images)
        
        self.logger.info(f"分类完成: {stats}")
        
        return {
            'classifications': dict(classification_results),
            'statistics': stats,
            'timestamp': datetime.now().isoformat(),
            'total_images': len(image_files)
        }
    
    def generate_classification_report(self, results: Dict) -> Dict:
        """生成分类报告"""
        report = {
            'summary': {
                'total_images': results['total_images'],
                'target_ip_count': len(results['classifications'].get(self.target_ip, [])),
                'unrelated_count': len(results['classifications'].get('unrelated', [])),
                'unknown_count': len(results['classifications'].get('unknown', [])),
                'error_count': len(results['classifications'].get('error', [])),
                'timestamp': results['timestamp']
            },
            'detailed_results': {}
        }
        
        for category, images in results['classifications'].items():
            category_results = []
            for img in images:
                category_results.append({
                    'file_path': img['file_path'],
                    'file_name': img['file_name'],
                    'confidence': img.get('confidence', 0.0),
                    'best_match': img.get('best_match', ''),
                    'detected_objects': img.get('detected_objects', []),
                    'image_size': img.get('image_size', (0, 0)),
                    'file_size': img.get('file_size', 0)
                })
            
            report['detailed_results'][category] = {
                'count': len(images),
                'images': category_results
            }
        
        return report
    
    def save_classification_report(self, report: Dict, output_dir: Path) -> Path:
        """保存分类报告"""
        output_dir.mkdir(exist_ok=True)
        
        report_file = output_dir / f"ip_classification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"分类报告已保存: {report_file}")
        return report_file

def main():
    """主函数 - 测试用"""
    import argparse
    
    parser = argparse.ArgumentParser(description='智能IP表情图片分类器')
    parser.add_argument('image_dir', help='图片目录路径')
    parser.add_argument('--ip', default='default', help='目标IP名称')
    parser.add_argument('--threshold', type=float, default=0.7, help='相似度阈值')
    
    args = parser.parse_args()
    
    # 创建分类器
    classifier = IPImageClassifier(target_ip=args.ip, similarity_threshold=args.threshold)
    
    # 查找图片文件
    image_dir = Path(args.image_dir)
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        image_files.extend(list(image_dir.glob(f'**/*{ext}')))
    
    if not image_files:
        print("未找到图片文件")
        return
    
    # 分类图片
    results = classifier.classify_images(image_files)
    
    # 生成报告
    report = classifier.generate_classification_report(results)
    
    # 保存报告
    report_file = classifier.save_classification_report(report, image_dir)
    
    print(f"\n分类完成!")
    print(f"目标IP图片: {report['summary']['target_ip_count']} 张")
    print(f"无关图片: {report['summary']['unrelated_count']} 张")
    print(f"报告文件: {report_file}")

if __name__ == "__main__":
    main()