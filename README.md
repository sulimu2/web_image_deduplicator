# 高级图片去重网页应用

基于Flask框架的智能图片去重工具，提供可视化界面和交互式操作。

## 功能特性

- 🖼️ **智能图片去重**: 基于感知哈希算法识别相似图片
- 🌐 **网页界面**: 直观的可视化操作界面
- 📊 **实时预览**: 支持相似图片组的实时预览
- 🔧 **批量操作**: 支持选择删除、全选删除等批量功能
- 📈 **进度显示**: 实时显示扫描进度和状态
- 🐳 **Docker支持**: 完整的容器化部署方案

## 技术栈

- **后端**: Flask + Flask-CORS
- **前端**: 原生JavaScript + CSS3
- **图片处理**: Pillow + OpenCV + ImageHash
- **部署**: Docker + Docker Compose

## 快速开始

### 环境要求

- Python 3.8+
- 或 Docker 20.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python app.py
```

或使用Docker:

```bash
# 构建镜像
docker build -t web-image-deduplicator .

# 运行容器
docker run -p 5010:5010 web-image-deduplicator
```

或使用Docker Compose:

```bash
docker-compose up
```

### 访问应用

打开浏览器访问: http://localhost:5010

## 使用方法

1. **选择目录**: 点击"浏览目录"按钮选择目标图片目录
2. **设置参数**: 调整相似度阈值、哈希大小等参数
3. **开始扫描**: 点击"开始扫描"按钮启动去重分析
4. **查看结果**: 浏览相似图片组，预览图片内容
5. **批量操作**: 选择要删除的相似组，执行删除操作

## API接口

### 扫描相关
- `POST /api/scan` - 扫描目录查找相似图片
- `GET /api/status` - 获取扫描状态

### 组管理
- `GET /api/groups` - 获取组列表
- `GET /api/group/<group_key>` - 获取组详情
- `POST /api/delete/selected` - 删除选中组
- `POST /api/delete/all` - 删除所有组

### 文件操作
- `GET /api/image/<path>` - 获取图片文件
- `GET /health` - 健康检查

## 配置说明

### 环境变量

```bash
# Flask应用密钥（生产环境必须修改）
SECRET_KEY=your-production-secret-key

# 可选配置
FLASK_ENV=production
FLASK_DEBUG=0
```

### 应用配置

```python
app.config['UPLOAD_FOLDER'] = 'uploads'  # 上传文件目录
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 最大文件大小
```

## 项目结构

```
web_image_deduplicator/
├── app.py                 # 主应用文件
├── requirements.txt       # Python依赖
├── Dockerfile            # Docker镜像配置
├── docker-compose.yml    # Docker Compose配置
├── static/               # 静态资源
│   ├── css/
│   └── js/
├── templates/            # HTML模板
├── uploads/             # 上传文件目录
└── logs/                 # 日志文件
```

## 开发说明

### 本地开发

```bash
# 克隆项目
git clone https://github.com/sulimu2/web_image_deduplicator.git
cd web_image_deduplicator

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python app.py
```

### 测试

```bash
python demo_test.py
```

## 版本信息

当前版本: 1.0.0  
发布日期: 2025-10-03

详细更新内容请查看 [CHANGELOG.md](CHANGELOG.md)

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- 项目地址: https://github.com/sulimu2/web_image_deduplicator
- 问题反馈: GitHub Issues