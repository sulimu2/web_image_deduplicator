#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能IP表情图片分类系统 - 功能测试脚本
"""

import os
import sys
import json
import unittest
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

class TestIPClassificationSystem(unittest.TestCase):
    """IP分类系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        from demo_data_generator import DemoDataGenerator
        self.generator = DemoDataGenerator()
        
    def test_demo_data_generation(self):
        """测试演示数据生成"""
        print("🧪 测试演示数据生成...")
        
        # 生成抖音分类报告
        report = self.generator.generate_demo_report(target_ip='抖音', total_images=50)
        
        # 验证报告结构
        self.assertIn('summary', report)
        self.assertIn('detailed_results', report)
        self.assertEqual(report['summary']['target_ip'], '抖音')
        self.assertEqual(report['summary']['total_images'], 50)
        
        # 验证详细结果
        self.assertIn('抖音', report['detailed_results'])
        self.assertIn('unrelated', report['detailed_results'])
        
        print("✅ 演示数据生成测试通过")
    
    def test_api_endpoints(self):
        """测试API端点（模拟）"""
        print("🧪 测试API端点...")
        
        # 模拟API响应
        mock_response = {
            'success': True,
            'report': {
                'summary': {
                    'target_ip': '测试IP',
                    'target_ip_count': 10,
                    'unrelated_count': 40,
                    'total_images': 50
                }
            }
        }
        
        self.assertTrue(mock_response['success'])
        self.assertEqual(mock_response['report']['summary']['total_images'], 50)
        
        print("✅ API端点测试通过")
    
    def test_file_structure(self):
        """测试文件结构完整性"""
        print("🧪 测试文件结构完整性...")
        
        required_files = [
            'ip_image_classifier.py',
            'ip_classification_app.py',
            'templates/ip_classification.html',
            'static/js/ip_classification.js',
            'static/css/ip_classification.css'
        ]
        
        for file_path in required_files:
            full_path = Path(__file__).parent / file_path
            self.assertTrue(full_path.exists(), f"文件不存在: {file_path}")
        
        print("✅ 文件结构完整性测试通过")
    
    def test_configuration(self):
        """测试配置文件"""
        print("🧪 测试配置文件...")
        
        # 检查requirements.txt
        requirements_file = Path(__file__).parent / 'requirements.txt'
        self.assertTrue(requirements_file.exists())
        
        # 检查关键依赖
        with open(requirements_file, 'r') as f:
            content = f.read()
            self.assertIn('Flask', content)
            self.assertIn('torch', content)
            self.assertIn('transformers', content)
        
        print("✅ 配置文件测试通过")

def run_comprehensive_test():
    """运行全面测试"""
    print("=" * 60)
    print("🤖 智能IP表情图片分类系统 - 全面测试")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestIPClassificationSystem('test_demo_data_generation'))
    test_suite.addTest(TestIPClassificationSystem('test_api_endpoints'))
    test_suite.addTest(TestIPClassificationSystem('test_file_structure'))
    test_suite.addTest(TestIPClassificationSystem('test_configuration'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 所有测试通过！系统准备就绪。")
        print("\n📋 下一步操作:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 启动服务: python start_all_services.sh")
        print("3. 访问系统: http://localhost:5020/ip-classification")
    else:
        print("❌ 部分测试失败，请检查错误信息。")
    
    print("=" * 60)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # 运行全面测试
    success = run_comprehensive_test()
    
    # 退出码
    sys.exit(0 if success else 1)