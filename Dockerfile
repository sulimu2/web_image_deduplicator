FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装系统依赖（用于图像处理和深度学习）
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads static/uploads logs

# 设置Python路径
ENV PYTHONPATH=/app

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONPATH=/app:$PYTHONPATH

# 暴露端口（图片去重 + IP分类）
EXPOSE 5010 5020

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5010/health || exit 1

# 启动集成应用（同时运行图片去重和IP分类系统）
CMD ["python", "integrated_app.py"]