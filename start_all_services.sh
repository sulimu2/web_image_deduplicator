#!/bin/bash

# 智能图片处理系统 - 完整启动脚本
# 同时启动图片去重和IP分类系统

set -e

echo "==============================================="
echo "🤖 智能图片处理系统 - 完整启动"
echo "==============================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📚 安装依赖包..."
pip install -r requirements.txt

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p uploads data logs static/uploads demo_data

# 生成演示数据（可选）
echo "🎭 生成演示数据..."
python demo_data_generator.py

# 设置环境变量
export DEDUPLICATOR_PORT=5010
export IP_CLASSIFICATION_PORT=5020
export FLASK_ENV=production

echo "==============================================="
echo "🚀 启动服务..."
echo "==============================================="
echo "📷 图片去重系统: http://localhost:5010"
echo "🤖 IP分类系统: http://localhost:5020/ip-classification"
echo "🔧 健康检查: http://localhost:5020/api/ip-classification/health"
echo "⏹️  按 Ctrl+C 停止所有服务"
echo "==============================================="

# 启动集成应用
python integrated_app.py