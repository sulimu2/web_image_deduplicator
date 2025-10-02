#!/bin/bash

# 高级图片去重网页应用启动脚本

echo "=========================================="
echo "  高级图片去重网页应用启动脚本"
echo "=========================================="

# 检查Python版本
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python3，请先安装Python3.8+"
    exit 1
fi

echo "检测到Python版本: $python_version"

# 检查依赖
echo "检查依赖包..."
pip3 install -r requirements.txt > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "警告: 依赖安装失败，尝试继续启动..."
fi

# 创建必要目录
mkdir -p uploads static/uploads logs

# 启动应用
echo "启动Flask应用..."
echo "应用将在 http://localhost:5010 运行"
echo "按 Ctrl+C 停止应用"

python3 run.py