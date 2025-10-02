# Docker 部署指南

## 快速开始

### 1. 构建Docker镜像

```bash
# 构建镜像
docker build -t web-image-deduplicator .

# 或者使用docker-compose
docker-compose up --build
```

### 2. 运行容器

```bash
# 直接运行
docker run -d -p 5010:5010 --name image-deduplicator web-image-deduplicator

# 使用docker-compose
docker-compose up -d
```

### 3. 访问应用

应用将在 http://localhost:5010 上运行

## 配置说明

### 环境变量

可以设置以下环境变量：

```bash
# Flask配置
FLASK_ENV=production
SECRET_KEY=your-secret-key

# 应用配置
PORT=5010
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600  # 100MB
```

### 数据持久化

容器使用以下卷来持久化数据：

- `./uploads` - 上传的文件
- `./logs` - 应用日志
- `./data` - 其他数据文件

## 生产环境部署

### 使用Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  image-deduplicator:
    build: .
    ports:
      - "5010:5010"
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5010/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 使用反向代理（Nginx）

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 健康检查

应用提供健康检查端点：`/health`

```bash
curl http://localhost:5010/health
# 返回: {"status": "healthy", "timestamp": "2025-10-03T01:52:09"}
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :5010
   # 停止占用进程或更改端口
   ```

2. **权限问题**
   ```bash
   # 确保挂载目录有正确权限
   chmod 755 uploads logs data
   ```

3. **构建失败**
   ```bash
   # 清理缓存重新构建
   docker system prune
   docker build --no-cache -t web-image-deduplicator .
   ```

### 日志查看

```bash
# 查看容器日志
docker logs image-deduplicator

# 实时查看日志
docker logs -f image-deduplicator
```

## 更新部署

```bash
# 停止旧容器
docker stop image-deduplicator
docker rm image-deduplicator

# 重新构建和运行
docker-compose down
docker-compose up --build -d
```

## 安全建议

1. 在生产环境中设置强密码的SECRET_KEY
2. 使用HTTPS加密通信
3. 定期更新基础镜像和安全补丁
4. 限制容器资源使用
5. 使用非root用户运行容器