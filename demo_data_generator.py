#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示数据生成器
为IP分类系统生成模拟数据用于测试
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime

class DemoDataGenerator:
    """演示数据生成器"""
    
    def __init__(self):
        self.target_ips = ['抖音', '微信', '微博', '小红书', 'B站']
        self.image_categories = {
            '抖音': ['抖音Logo', '抖音特效', '抖音贴纸', '抖音表情包', '抖音挑战'],
            '微信': ['微信表情', '微信红包', '微信聊天', '微信支付', '微信小程序'],
            '微博': ['微博热搜', '微博表情', '微博话题', '微博大V', '微博转发'],
            '小红书': ['小红书笔记', '小红书种草', '小红书美妆', '小红书穿搭', '小红书探店'],
            'B站': ['B站弹幕', 'B站UP主', 'B站番剧', 'B站鬼畜', 'B站三连']
        }
        self.unrelated_categories = ['风景', '美食', '宠物', '自拍', '建筑', '汽车', '游戏', '动漫']
        
    def generate_demo_report(self, target_ip='抖音', total_images=200, similarity_threshold=0.7):
        """生成演示分类报告"""
        
        # 随机生成相关图片数量（基于阈值）
        target_ip_count = int(total_images * similarity_threshold * random.uniform(0.8, 1.2))
        unrelated_count = total_images - target_ip_count
        
        # 生成目标IP相关图片数据
        target_ip_images = []
        for i in range(target_ip_count):
            image_data = self._generate_target_ip_image(i, target_ip)
            target_ip_images.append(image_data)
        
        # 生成无关图片数据
        unrelated_images = []
        for i in range(unrelated_count):
            image_data = self._generate_unrelated_image(i)
            unrelated_images.append(image_data)
        
        # 构建报告
        report = {
            'summary': {
                'target_ip': target_ip,
                'target_ip_count': target_ip_count,
                'unrelated_count': unrelated_count,
                'total_images': total_images,
                'similarity_threshold': similarity_threshold,
                'processing_time': f'{random.uniform(5, 20):.1f}秒',
                'scan_time': datetime.now().isoformat()
            },
            'detailed_results': {
                target_ip: {
                    'count': target_ip_count,
                    'average_confidence': round(random.uniform(0.6, 0.9), 2),
                    'images': target_ip_images
                },
                'unrelated': {
                    'count': unrelated_count,
                    'average_confidence': round(random.uniform(0.1, 0.4), 2),
                    'images': unrelated_images
                }
            }
        }
        
        return report
    
    def _generate_target_ip_image(self, index, target_ip):
        """生成目标IP相关图片数据"""
        categories = self.image_categories.get(target_ip, ['通用表情'])
        category = random.choice(categories)
        
        return {
            'file_path': f'/demo/images/{target_ip}/image_{index:04d}.jpg',
            'file_name': f'{target_ip}_image_{index:04d}.jpg',
            'file_size': random.randint(50000, 500000),
            'image_size': [random.randint(400, 1200), random.randint(300, 800)],
            'confidence': round(random.uniform(0.6, 0.95), 3),
            'best_match': category,
            'detected_objects': self._generate_detected_objects(target_ip),
            'classification_reason': f'检测到{target_ip}特征: {category}'
        }
    
    def _generate_unrelated_image(self, index):
        """生成无关图片数据"""
        category = random.choice(self.unrelated_categories)
        
        return {
            'file_path': f'/demo/images/unrelated/image_{index:04d}.jpg',
            'file_name': f'unrelated_image_{index:04d}.jpg',
            'file_size': random.randint(50000, 500000),
            'image_size': [random.randint(400, 1200), random.randint(300, 800)],
            'confidence': round(random.uniform(0.05, 0.3), 3),
            'best_match': category,
            'detected_objects': self._generate_detected_objects('unrelated'),
            'classification_reason': f'与目标IP特征不匹配，识别为{category}'
        }
    
    def _generate_detected_objects(self, category_type):
        """生成检测到的对象列表"""
        if category_type == 'unrelated':
            objects = [
                {'label': '风景元素', 'confidence': round(random.uniform(0.7, 0.9), 2)},
                {'label': '自然物体', 'confidence': round(random.uniform(0.5, 0.8), 2)}
            ]
        else:
            objects = [
                {'label': '人物', 'confidence': round(random.uniform(0.8, 0.95), 2)},
                {'label': '文字', 'confidence': round(random.uniform(0.6, 0.9), 2)},
                {'label': '图标', 'confidence': round(random.uniform(0.7, 0.9), 2)}
            ]
            # 随机添加1-2个额外对象
            extra_objects = ['背景', '装饰', '特效', '边框']
            for _ in range(random.randint(1, 2)):
                obj = random.choice(extra_objects)
                objects.append({
                    'label': obj,
                    'confidence': round(random.uniform(0.4, 0.7), 2)
                })
        
        return objects
    
    def save_demo_report(self, report, filename='demo_classification_report.json'):
        """保存演示报告到文件"""
        demo_dir = Path('demo_data')
        demo_dir.mkdir(exist_ok=True)
        
        filepath = demo_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 演示报告已保存: {filepath}")
        return filepath

def main():
    """主函数"""
    print("🤖 IP分类系统演示数据生成器")
    print("=" * 50)
    
    generator = DemoDataGenerator()
    
    # 为每个目标IP生成演示报告
    for ip in generator.target_ips:
        print(f"📱 生成 {ip} 分类演示数据...")
        report = generator.generate_demo_report(target_ip=ip, total_images=150)
        filename = f'{ip}_classification_report.json'
        generator.save_demo_report(report, filename)
    
    print("\n🎉 所有演示数据生成完成！")
    print("💡 这些数据可用于前端界面测试和功能演示")

if __name__ == '__main__':
    main()