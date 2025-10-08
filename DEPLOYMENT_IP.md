# 智能IP表情图片分类系统 - 部署指南

## 部署方式概览

系统支持多种部署方式，可根据需求选择：

| 部署方式 | 适用场景 | 复杂度 | 推荐度 |
|---------|---------|--------|--------|
| 本地开发模式 | 开发测试 | ⭐ | ★★★★★ |
| Docker容器化 | 生产环境 | ⭐⭐ | ★★★★☆ |
| 集成模式 | 多服务协同 | ⭐⭐⭐ | ★★★☆☆ |

## 1. 本地开发模式部署

### 环境准备
```bash
# 克隆项目（如已存在则跳过）
git clone <项目地址>
cd web_image_deduplicator

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 启动服务

#### 方式一：独立启动IP分类系统
```bash
# 启动IP分类系统（端口5020）
python start_ip_classification.py
```

#### 方式二：集成启动（推荐）
```bash
# 同时启动图片去重和IP分类系统
python integrated_app.py
```

#### 方式三：分别启动
```bash
# 终端1：启动图片去重系统
python app.py

# 终端2：启动IP分类系统（修改端口避免冲突）
export IP_CLASSIFICATION_PORT=5020
python start_ip_classification.py
```

### 访问地址
- **图片去重系统**: http://localhost:5010
- **IP分类系统**: http://localhost:5020/ip-classification
- **健康检查**: http://localhost:5020/api/ip-classification/health

## 2. Docker容器化部署

### Docker单容器部署
```bash
# 构建镜像
docker build -t ip-image-classifier .

# 运行容器
docker run -d \
  -p 5020:5020 \
  -v /path/to/your/images:/app/uploads \
  --name ip-classifier \
  ip-image-classifier
```

### Docker Compose部署（推荐）
```bash
# 使用docker-compose.yml
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### Docker Compose配置示例
```yaml
version: '3.8'
services:
  ip-classification:
    build: .
    ports:
      - "5020:5020"
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
    environment:
      - IP_CLASSIFICATION_PORT=5020
      - CUDA_VISIBLE_DEVICES=0  # 如有GPU
    restart: unless-stopped
```

## 3. 生产环境部署建议

### 系统要求
```bash
# 基础配置
CPU: 4核+
内存: 8GB+
存储: SSD推荐，根据图片库大小
网络: 稳定的互联网连接（模型下载）

# 高性能配置（推荐）
CPU: 8核+
内存: 16GB+
GPU: NVIDIA GPU with CUDA
存储: NVMe SSD
```

### 安全配置
```bash
# 1. 使用反向代理（Nginx）
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5020;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 2. 启用HTTPS
# 使用Let's Encrypt免费证书

# 3. 防火墙配置
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 性能优化配置
```bash
# 环境变量配置
export CUDA_VISIBLE_DEVICES=0  # 使用GPU
export OMP_NUM_THREADS=4       # CPU线程数
export TF_FORCE_GPU_ALLOW_GROWTH=true  # GPU内存优化

# Flask生产配置
export FLASK_ENV=production
export FLASK_DEBUG=0
```

## 4. 模型文件管理

### 首次运行模型下载
系统首次运行时会自动下载以下模型：
- CLIP-ViT-Base (~400MB)
- YOLOv8检测模型 (~200MB)
- 其他依赖模型 (~500MB)

总大小约1.1GB，请确保网络通畅。

### 离线部署方案
如需离线环境部署，可预先下载模型：
```bash
# 下载模型到本地目录
python -c "
from transformers import CLIPModel, CLIPProcessor
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
"

# 设置模型缓存路径
export TRANSFORMERS_CACHE=/path/to/model/cache
```

## 5. 监控与维护

### 健康检查
```bash
# 手动检查服务状态
curl http://localhost:5020/api/ip-classification/health

# 预期响应
{
  "status": "healthy",
  "service": "ip_classification",
  "timestamp": "2025-10-03T06:00:00.000000"
}
```

### 日志查看
```bash
# Docker容器日志
docker logs ip-classifier -f

# 本地运行日志
tail -f nohup.out  # 如使用nohup运行
```

### 性能监控
建议配置监控系统跟踪：
- 内存使用情况
- CPU/GPU利用率
- 请求响应时间
- 错误率统计

## 6. 故障排除

### 常见问题解决

#### 问题1: 端口冲突
```bash
# 解决方案：修改端口
export IP_CLASSIFICATION_PORT=5021
python start_ip_classification.py
```

#### 问题2: 模型下载失败
```bash
# 解决方案：手动下载或使用代理
export HTTPS_PROXY=http://your-proxy:port
python start_ip_classification.py
```

#### 问题3: 内存不足
```bash
# 解决方案：限制处理批量大小
export MAX_BATCH_SIZE=32  # 减少批量大小
python start_ip_classification.py
```

#### 问题4: GPU无法使用
```bash
# 解决方案：强制使用CPU
export CUDA_VISIBLE_DEVICES=-1
python start_ip_classification.py
```

### 日志级别调整
```python
# 在代码中调整日志级别
import logging
logging.getLogger().setLevel(logging.WARNING)  # 减少日志输出
```

## 7. 备份与恢复

### 数据备份
```bash
# 备份重要数据
tar -czf backup_$(date +%Y%m%d).tar.gz \
  uploads/ \
  data/ \
  logs/ \
  demo_data/
```

### 配置文件备份
```bash
# 备份环境配置
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

## 8. 升级指南

### 版本升级步骤
1. 备份当前数据和配置
2. 拉取最新代码
3. 更新依赖包
4. 测试新功能
5. 逐步切换流量

### 回滚方案
保持旧版本镜像和配置，确保可快速回滚。

---

## 总结

智能IP表情图片分类系统提供了灵活的部署方案，从简单的本地开发到生产环境的高可用部署。建议根据实际需求选择合适的部署方式，并遵循安全最佳实践。

**推荐部署流程**：
1. 本地开发测试 → 2. Docker容器化 → 3. 生产环境部署

如有问题，请参考项目文档或提交Issue寻求帮助。