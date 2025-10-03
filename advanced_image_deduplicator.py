#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级图片去重工具 - 基于感知哈希(pHash)算法
支持检测高度相似的图片，而不仅仅是完全相同的文件
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict

import numpy as np
from PIL import Image, ImageFile
import imagehash
from tqdm import tqdm

# 可选导入OpenCV，如果不可用则跳过
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("警告: OpenCV不可用，部分功能可能受限")

# 配置PIL以处理损坏的图片文件
ImageFile.LOAD_TRUNCATED_IMAGES = True

# 支持的图片格式
SUPPORTED_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', 
    '.tiff', '.tif', '.ico', '.svg'
}

class AdvancedImageDeduplicator:
    """高级图片去重器 - 基于感知哈希算法"""
    
    def __init__(self, target_dir: str, similarity_threshold: float = 0.75, 
                 hash_size: int = 8, recursive: bool = True):
        """
        初始化去重器
        
        Args:
            target_dir: 目标目录路径
            similarity_threshold: 相似度阈值 (0-1)
            hash_size: 哈希大小 (8, 16, 32)
            recursive: 是否递归扫描子目录
        """
        self.target_dir = Path(target_dir).resolve()
        self.similarity_threshold = similarity_threshold
        self.hash_size = hash_size
        self.recursive = recursive
        self.logger = self.setup_logging()
        
        if not self.target_dir.exists():
            raise ValueError(f"目标目录不存在: {self.target_dir}")
        
        # 创建输出目录
        self.output_dir = self.target_dir / "deduplication_results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"初始化完成 - 目标目录: {self.target_dir}")
        self.logger.info(f"相似度阈值: {self.similarity_threshold}, 哈希大小: {self.hash_size}")
    
    def setup_logging(self) -> logging.Logger:
        """设置日志配置"""
        logger = logging.getLogger('advanced_image_deduplicator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # 文件handler
            log_file = self.target_dir / "advanced_deduplication.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            
            # 控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def is_image_file(self, file_path: Path) -> bool:
        """检查文件是否为支持的图片格式"""
        return file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    
    def find_image_files(self) -> List[Path]:
        """查找目录中的所有图片文件"""
        image_files = []
        
        try:
            if self.recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in self.target_dir.glob(pattern):
                if file_path.is_file() and self.is_image_file(file_path):
                    image_files.append(file_path)
                        
            self.logger.info(f"找到 {len(image_files)} 个图片文件")
            return image_files
            
        except OSError as e:
            self.logger.error(f"遍历目录失败: {e}")
            return []
    
    def load_image(self, file_path: Path) -> Optional[Image.Image]:
        """加载图片文件，处理各种异常情况"""
        try:
            # 尝试使用PIL加载图片
            with Image.open(file_path) as img:
                # 转换为RGB模式（如果图片有透明度）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                return img.copy()
        except Exception as e:
            self.logger.warning(f"无法加载图片 {file_path}: {e}")
            return None
    
    def calculate_phash(self, image: Image.Image) -> Optional[imagehash.ImageHash]:
        """计算图片的感知哈希值"""
        try:
            return imagehash.phash(image, hash_size=self.hash_size)
        except Exception as e:
            self.logger.warning(f"计算pHash失败: {e}")
            return None
    
    def calculate_dhash(self, image: Image.Image) -> Optional[imagehash.ImageHash]:
        """计算图片的差异哈希值"""
        try:
            return imagehash.dhash(image, hash_size=self.hash_size)
        except Exception as e:
            self.logger.warning(f"计算dHash失败: {e}")
            return None
    
    def calculate_whash(self, image: Image.Image) -> Optional[imagehash.ImageHash]:
        """计算图片的小波哈希值"""
        try:
            return imagehash.whash(image, hash_size=self.hash_size)
        except Exception as e:
            self.logger.warning(f"计算wHash失败: {e}")
            return None
    
    def get_file_info(self, file_path: Path) -> Tuple[float, int, datetime]:
        """获取文件信息（创建时间、大小、修改时间）"""
        try:
            stat = file_path.stat()
            creation_time = stat.st_birthtime if hasattr(stat, 'st_birthtime') else stat.st_mtime
            file_size = stat.st_size
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            return creation_time, file_size, mod_time
        except OSError as e:
            self.logger.error(f"获取文件信息失败: {file_path} - {e}")
            return float('inf'), 0, datetime.now()

    def assess_image_quality(self, image: Image.Image, file_path: Path) -> dict:
        """评估图片质量，返回质量评分"""
        quality_score = 0.0
        resolution_score = 0.0
        size_score = 0.0
        sharpness_score = 0.5  # 默认值
        mode_score = 0.5  # 默认值
        width, height = 0, 0
        file_size = 0
        
        try:
            # 获取文件大小
            file_size = file_path.stat().st_size
            
            # 1. 分辨率评分 (权重: 40%)
            width, height = image.size
            resolution_score = (width * height) / (1920 * 1080)  # 以1080p为基准
            resolution_score = min(resolution_score, 2.0)  # 最高2倍分数
            quality_score += resolution_score * 0.4
            
            # 2. 文件大小评分 (权重: 30%)
            # 假设合理文件大小范围: 10KB - 10MB
            if file_size < 10 * 1024:  # 小于10KB，质量较差
                size_score = 0.1
            elif file_size > 10 * 1024 * 1024:  # 大于10MB，可能过大
                size_score = 0.8
            else:
                # 在10KB-10MB之间，线性评分
                size_score = min((file_size - 10 * 1024) / (10 * 1024 * 1024 - 10 * 1024), 1.0)
            quality_score += size_score * 0.3
            
            # 3. 清晰度评估 (权重: 30%)
            # 使用拉普拉斯方差评估图片清晰度
            if OPENCV_AVAILABLE:
                try:
                    # 转换为灰度图
                    if image.mode != 'L':
                        gray_image = image.convert('L')
                    else:
                        gray_image = image
                    
                    # 转换为numpy数组
                    img_array = np.array(gray_image)
                    
                    # 计算拉普拉斯方差
                    laplacian_var = cv2.Laplacian(img_array, cv2.CV_64F).var()
                    
                    # 标准化清晰度评分 (经验阈值)
                    if laplacian_var < 100:  # 模糊图片
                        sharpness_score = 0.1
                    elif laplacian_var > 1000:  # 非常清晰的图片
                        sharpness_score = 1.0
                    else:
                        sharpness_score = min((laplacian_var - 100) / 900, 1.0)
                    
                    quality_score += sharpness_score * 0.3
                    
                except Exception as e:
                    self.logger.warning(f"清晰度评估失败: {file_path} - {e}")
                    # 如果清晰度评估失败，给中等评分
                    quality_score += 0.5 * 0.3
            else:
                # 如果没有OpenCV，使用简单的替代方法
                # 基于图片模式评分
                if image.mode in ('RGB', 'RGBA'):
                    mode_score = 0.8
                else:
                    mode_score = 0.5
                quality_score += mode_score * 0.3
            
            # 确保评分在0-1之间
            quality_score = max(0.0, min(1.0, quality_score))
            
            # 确定最终使用的清晰度评分
            final_sharpness_score = sharpness_score if OPENCV_AVAILABLE else mode_score
            
            return {
                'overall_score': quality_score,
                'resolution_score': resolution_score,
                'size_score': size_score,
                'sharpness_score': final_sharpness_score,
                'width': width,
                'height': height,
                'file_size': file_size
            }
            
        except Exception as e:
            self.logger.warning(f"图片质量评估失败: {file_path} - {e}")
            return {
                'overall_score': 0.5,  # 默认中等评分
                'resolution_score': 0.5,
                'size_score': 0.5,
                'sharpness_score': 0.5,
                'width': 0,
                'height': 0,
                'file_size': file_size
            }
    
    def calculate_similarity(self, hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> float:
        """计算两个哈希值的相似度（0-1）"""
        try:
            # 计算汉明距离
            hamming_distance = hash1 - hash2
            # 转换为相似度（距离越小，相似度越高）
            max_distance = len(hash1.hash) ** 2
            similarity = 1 - (hamming_distance / max_distance)
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            self.logger.warning(f"计算相似度失败: {e}")
            return 0.0
    
    def find_similar_images(self) -> dict:
        """查找相似的图片文件"""
        image_files = self.find_image_files()
        if not image_files:
            return {}
        
        # 存储图片信息和哈希值
        image_data = []
        failed_files = []
        
        self.logger.info("开始计算图片哈希值...")
        
        # 使用进度条显示处理进度
        for file_path in tqdm(image_files, desc="计算哈希值"):
            # 加载图片
            image = self.load_image(file_path)
            if image is None:
                failed_files.append(str(file_path))
                continue
            
            # 计算各种哈希值
            phash = self.calculate_phash(image)
            dhash = self.calculate_dhash(image)
            whash = self.calculate_whash(image)
            
            if phash is None and dhash is None and whash is None:
                failed_files.append(str(file_path))
                continue
            
            # 获取文件信息
            creation_time, file_size, mod_time = self.get_file_info(file_path)
            
            # 评估图片质量
            quality_info = self.assess_image_quality(image, file_path)
            
            image_data.append({
                'path': file_path,
                'phash': phash,
                'dhash': dhash,
                'whash': whash,
                'creation_time': creation_time,
                'file_size': file_size,
                'mod_time': mod_time,
                'quality_score': quality_info['overall_score'],
                'quality_details': quality_info
            })
        
        if failed_files:
            self.logger.warning(f"{len(failed_files)} 个文件处理失败")
            # 保存失败文件列表
            with open(self.output_dir / "failed_files.txt", 'w', encoding='utf-8') as f:
                for file_path in failed_files:
                    f.write(f"{file_path}\n")
        
        self.logger.info(f"成功处理 {len(image_data)} 个图片文件")
        
        # 查找相似图片
        similar_groups = self.group_similar_images(image_data)
        
        return similar_groups
    
    def group_similar_images(self, image_data: list) -> dict:
        """根据相似度对图片进行分组"""
        similar_groups = {}
        group_id = 0
        
        self.logger.info("开始查找相似图片...")
        
        # 使用集合跟踪已处理的图片
        processed = set()
        
        for i, img1 in enumerate(tqdm(image_data, desc="查找相似图片")):
            if i in processed:
                continue
            
            # 创建新的相似组
            similar_images = [img1]
            processed.add(i)
            
            for j, img2 in enumerate(image_data[i+1:], i+1):
                if j in processed:
                    continue
                
                # 计算相似度（使用多种哈希算法）
                similarities = []
                
                if img1['phash'] and img2['phash']:
                    similarities.append(self.calculate_similarity(img1['phash'], img2['phash']))
                
                if img1['dhash'] and img2['dhash']:
                    similarities.append(self.calculate_similarity(img1['dhash'], img2['dhash']))
                
                if img1['whash'] and img2['whash']:
                    similarities.append(self.calculate_similarity(img1['whash'], img2['whash']))
                
                # 如果任一哈希算法的相似度超过阈值，则认为图片相似
                if similarities and max(similarities) >= self.similarity_threshold:
                    similar_images.append(img2)
                    processed.add(j)
            
            # 如果组内有多个图片，则保存该组
            if len(similar_images) > 1:
                group_key = f"group_{group_id:04d}"
                similar_groups[group_key] = similar_images
                group_id += 1
        
        self.logger.info(f"发现 {len(similar_groups)} 组相似图片")
        return similar_groups
    
    def generate_report(self, similar_groups: dict, action: str = "preview") -> dict:
        """生成处理报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_directory': str(self.target_dir),
            'similarity_threshold': self.similarity_threshold,
            'hash_size': self.hash_size,
            'action': action,
            'summary': {
                'total_groups': len(similar_groups),
                'total_images': sum(len(group) for group in similar_groups.values()),
                'unique_images': 0,
                'duplicate_images': 0,
                'estimated_space_saved': 0,
                'average_quality_score': 0.0
            },
            'groups': {}
        }
        
        total_quality_score = 0.0
        total_quality_images = 0
        
        for group_key, images in similar_groups.items():
            # 按质量评分排序（质量最高的排第一）
            images.sort(key=lambda x: x['quality_score'], reverse=True)
            
            group_info = {
                'representative': str(images[0]['path']),
                'representative_quality': images[0]['quality_score'],
                'images': [],
                'group_size': len(images),
                'space_savings': sum(img['file_size'] for img in images[1:]),
                'quality_range': {
                    'max': images[0]['quality_score'],
                    'min': images[-1]['quality_score'],
                    'avg': sum(img['quality_score'] for img in images) / len(images)
                }
            }
            
            for i, img in enumerate(images):
                # 确保所有数据都是JSON可序列化的
                img_info = {
                    'path': str(img['path']),
                    'file_size': img['file_size'],
                    'creation_time': str(img['creation_time']),
                    'mod_time': img['mod_time'].isoformat() if hasattr(img['mod_time'], 'isoformat') else str(img['mod_time']),
                    'is_representative': i == 0,
                    'quality_score': img['quality_score'],
                    'quality_details': img['quality_details']
                }
                group_info['images'].append(img_info)
                
                # 统计质量评分
                total_quality_score += img['quality_score']
                total_quality_images += 1
            
            report['groups'][group_key] = group_info
        
        # 计算统计信息
        report['summary']['unique_images'] = len(similar_groups)
        report['summary']['duplicate_images'] = report['summary']['total_images'] - report['summary']['unique_images']
        report['summary']['estimated_space_saved'] = sum(
            group['space_savings'] for group in report['groups'].values()
        )
        
        # 计算平均质量评分
        if total_quality_images > 0:
            report['summary']['average_quality_score'] = total_quality_score / total_quality_images
        
        return report
    
    def save_report(self, report: Dict[str, any], filename: str) -> Path:
        """保存报告到文件"""
        report_file = self.output_dir / filename
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"报告已保存: {report_file}")
        return report_file
    
    def preview_similar_images(self, similar_groups: Dict[str, List[Dict]]) -> None:
        """预览相似图片信息"""
        if not similar_groups:
            print("未发现相似图片")
            return
        
        report = self.generate_report(similar_groups, "preview")
        
        print("\n" + "="*100)
        print("相似图片预览报告")
        print("="*100)
        print(f"目标目录: {report['target_directory']}")
        print(f"相似度阈值: {report['similarity_threshold']}")
        print(f"发现 {report['summary']['total_groups']} 组相似图片")
        print(f"涉及 {report['summary']['total_images']} 个图片文件")
        print(f"预计可释放空间: {report['summary']['estimated_space_saved']} 字节 "
              f"({report['summary']['estimated_space_saved']/1024/1024:.2f} MB)")
        print(f"平均质量评分: {report['summary']['average_quality_score']:.3f}")
        
        for group_key, group_info in report['groups'].items():
            print(f"\n{group_key}:")
            print(f"  代表图片(质量最高): {group_info['representative']}")
            print(f"  质量评分: {group_info['representative_quality']:.3f}")
            print(f"  组内图片数: {group_info['group_size']}")
            print(f"  质量范围: {group_info['quality_range']['min']:.3f} - {group_info['quality_range']['max']:.3f}")
            print(f"  平均质量: {group_info['quality_range']['avg']:.3f}")
            print(f"  可释放空间: {group_info['space_savings']} 字节")
            
            for i, img in enumerate(group_info['images']):
                status = "保留(质量最高)" if img['is_representative'] else "处理"
                print(f"  [{status}] {img['path']} (质量: {img['quality_score']:.3f}, 大小: {img['file_size']} 字节)")
        
        # 保存预览报告
        self.save_report(report, "preview_report.json")
    
    def delete_similar_images(self, similar_groups: dict, dry_run: bool = False) -> dict:
        """删除相似图片，保留每组中质量最高的图片"""
        if not similar_groups:
            return {'total_groups': 0, 'files_deleted': 0, 'space_saved': 0}
        
        deletion_summary = {
            'total_groups': len(similar_groups),
            'files_deleted': 0,
            'space_saved': 0,
            'deleted_files': [],
            'quality_improvement': 0.0
        }
        
        total_quality_improvement = 0.0
        
        for group_key, images in similar_groups.items():
            # 按质量评分排序（质量最高的排第一）
            images.sort(key=lambda x: x['quality_score'], reverse=True)
            
            # 保留质量最高的文件，删除其他相似文件
            best_quality_file = images[0]['path']
            best_quality_score = images[0]['quality_score']
            similar_files = images[1:]
            
            self.logger.info(f"相似组 {group_key}:")
            self.logger.info(f"  保留(质量最高): {best_quality_file} (质量评分: {best_quality_score:.3f})")
            
            # 计算质量改进（保留的质量评分 - 平均质量评分）
            avg_quality = sum(img['quality_score'] for img in images) / len(images)
            quality_improvement = best_quality_score - avg_quality
            total_quality_improvement += quality_improvement
            
            for img in similar_files:
                try:
                    if dry_run:
                        action = "将删除"
                    else:
                        action = "删除"
                        os.remove(img['path'])
                    
                    deletion_summary['files_deleted'] += 1
                    deletion_summary['space_saved'] += img['file_size']
                    deletion_summary['deleted_files'].append(str(img['path']))
                    
                    self.logger.info(f"  {action}: {img['path']} (质量评分: {img['quality_score']:.3f}, 大小: {img['file_size']} 字节)")
                    
                except OSError as e:
                    self.logger.error(f"删除文件失败: {img['path']} - {e}")
        
        deletion_summary['quality_improvement'] = total_quality_improvement
        
        return deletion_summary
    
    def organize_similar_images(self, similar_groups: dict, 
                               dry_run: bool = False) -> dict:
        """将相似图片整理到不同的文件夹"""
        if not similar_groups:
            return {'total_groups': 0, 'files_moved': 0, 'space_saved': 0}
        
        # 创建整理目录
        organize_dir = self.output_dir / "organized_duplicates"
        if not dry_run:
            organize_dir.mkdir(exist_ok=True)
        
        organize_summary = {
            'total_groups': len(similar_groups),
            'files_moved': 0,
            'space_saved': 0,
            'moved_files': []
        }
        
        for group_key, images in similar_groups.items():
            # 按创建时间排序（最早的排第一）
            images.sort(key=lambda x: x['creation_time'])
            
            # 保留最早的文件，移动其他相似文件到对应组目录
            original_file = images[0]['path']
            similar_files = images[1:]
            
            # 创建组目录
            group_dir = organize_dir / group_key
            if not dry_run:
                group_dir.mkdir(exist_ok=True)
            
            self.logger.info(f"相似组 {group_key}:")
            self.logger.info(f"  保留: {original_file}")
            self.logger.info(f"  移动目录: {group_dir}")
            
            for img in similar_files:
                try:
                    target_path = group_dir / img['path'].name
                    # 处理文件名冲突
                    counter = 1
                    while target_path.exists():
                        stem = img['path'].stem
                        suffix = img['path'].suffix
                        target_path = group_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    if dry_run:
                        action = "将移动"
                    else:
                        action = "移动"
                        import shutil
                        shutil.move(str(img['path']), str(target_path))
                    
                    organize_summary['files_moved'] += 1
                    organize_summary['space_saved'] += img['file_size']
                    organize_summary['moved_files'].append({
                        'original': str(img['path']),
                        'target': str(target_path)
                    })
                    
                    self.logger.info(f"  {action}: {img['path']} -> {target_path}")
                    
                except OSError as e:
                    self.logger.error(f"移动文件失败: {img['path']} - {e}")
        
        return organize_summary

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='高级图片去重工具 - 基于感知哈希算法')
    parser.add_argument('directory', help='要扫描的目录路径')
    parser.add_argument('--threshold', type=float, default=0.95,
                       help='相似度阈值 (0-1, 默认: 0.95)')
    parser.add_argument('--hash-size', type=int, default=8, choices=[8, 16, 32],
                       help='哈希大小 (8, 16, 32, 默认: 8)')
    parser.add_argument('--no-recursive', action='store_true',
                       help='不递归扫描子目录')
    parser.add_argument('--preview', action='store_true',
                       help='仅预览相似图片，不执行操作')
    parser.add_argument('--delete', action='store_true',
                       help='删除相似图片（保留每组中最早的图片）')
    parser.add_argument('--organize', action='store_true',
                       help='整理相似图片到不同文件夹')
    parser.add_argument('--dry-run', action='store_true',
                       help='模拟运行，不实际执行操作')
    
    args = parser.parse_args()
    
    try:
        # 创建去重器实例
        deduplicator = AdvancedImageDeduplicator(
            args.directory,
            similarity_threshold=args.threshold,
            hash_size=args.hash_size,
            recursive=not args.no_recursive
        )
        
        # 查找相似图片
        similar_groups = deduplicator.find_similar_images()
        
        if not similar_groups:
            print("未发现相似图片")
            return
        
        # 预览模式
        if args.preview or (not args.delete and not args.organize):
            deduplicator.preview_similar_images(similar_groups)
            return
        
        # 删除模式
        if args.delete:
            if not args.dry_run:
                response = input("\n确认删除相似图片？(y/N): ").strip().lower()
                if response not in ('y', 'yes'):
                    print("操作已取消")
                    return
            
            result = deduplicator.delete_similar_images(similar_groups, dry_run=args.dry_run)
            action = "模拟删除" if args.dry_run else "删除"
            
            # 生成最终报告
            report = deduplicator.generate_report(similar_groups, action)
            deduplicator.save_report(report, "deletion_report.json")
            
            print("\n" + "="*80)
            print(f"{action}操作完成")
            print("="*80)
            print(f"处理组数: {result['total_groups']}")
            print(f"{action}文件数: {result['files_deleted']}")
            print(f"释放空间: {result['space_saved']} 字节 ({result['space_saved']/1024/1024:.2f} MB)")
        
        # 整理模式
        elif args.organize:
            if not args.dry_run:
                response = input("\n确认整理相似图片？(y/N): ").strip().lower()
                if response not in ('y', 'yes'):
                    print("操作已取消")
                    return
            
            result = deduplicator.organize_similar_images(similar_groups, dry_run=args.dry_run)
            action = "模拟整理" if args.dry_run else "整理"
            
            # 生成最终报告
            report = deduplicator.generate_report(similar_groups, action)
            deduplicator.save_report(report, "organization_report.json")
            
            print("\n" + "="*80)
            print(f"{action}操作完成")
            print("="*80)
            print(f"处理组数: {result['total_groups']}")
            print(f"{action}文件数: {result['files_moved']}")
            print(f"释放空间: {result['space_saved']} 字节 ({result['space_saved']/1024/1024:.2f} MB)")
        
        print(f"详细日志和报告已保存到: {deduplicator.output_dir}")
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 使用示例
    if len(sys.argv) == 1:
        print("高级图片去重工具使用说明:")
        print("python advanced_image_deduplicator.py [目录] [选项]")
        print("\n核心功能:")
        print("  基于感知哈希(pHash)算法，检测高度相似的图片")
        print("  支持多种图片格式和相似度阈值配置")
        print("\n常用选项:")
        print("  --preview         仅预览相似图片")
        print("  --delete          删除相似图片（保留最早的）")
        print("  --organize        整理相似图片到不同文件夹")
        print("  --threshold FLOAT 相似度阈值 (0-1, 默认: 0.95)")
        print("  --hash-size INT   哈希大小 (8, 16, 32, 默认: 8)")
        print("  --dry-run         模拟运行")
        print("  --no-recursive    不递归扫描子目录")
        print("\n示例:")
        print("  python advanced_image_deduplicator.py ./stickers_output --preview")
        print("  python advanced_image_deduplicator.py ./stickers_output --delete --threshold 0.9")
        print("  python advanced_image_deduplicator.py ./stickers_output --organize --hash-size 16")
    else:
        main()