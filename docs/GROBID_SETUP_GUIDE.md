# GROBID Docker集成使用指南

## 📋 概述

CategoryRAG系统现已集成GROBID Docker服务，用于高质量的PDF文档文本提取和结构化分析。GROBID是一个机器学习库，专门用于提取和解析学术文档的书目信息。

## 🐳 GROBID Docker设置

### 1. 快速启动

使用提供的脚本快速设置GROBID服务：

```bash
# 运行设置脚本
./scripts/setup_grobid.sh
```

### 2. 手动启动

如果需要手动控制，可以使用以下命令：

```bash
# 拉取GROBID镜像
docker pull grobid/grobid:0.8.2

# 启动GROBID服务（完整版本）
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.2

# 或者启动轻量级CRF版本（更快启动，较小内存占用）
docker pull lfoppiano/grobid:0.8.2
docker run --rm --init --ulimit core=0 -p 8070:8070 lfoppiano/grobid:0.8.2
```

### 3. 服务验证

启动后，验证服务是否正常运行：

```bash
# 检查服务状态
curl http://localhost:8070/api/isalive

# 获取版本信息
curl http://localhost:8070/api/version

# 访问Web界面
open http://localhost:8070
```

## ⚙️ 配置说明

在 `config/config.yaml` 中的GROBID相关配置：

```yaml
documents:
  preprocessing:
    enabled: true
    grobid_url: "http://localhost:8070"  # GROBID服务地址
    grobid_timeout: 300                  # 请求超时时间（秒）
    ocr_pages_limit: 10                  # 处理的页面数量
    toc_extraction_enabled: true         # 启用目录提取
```

### 配置参数说明

- `grobid_url`: GROBID服务的URL地址
- `grobid_timeout`: API请求的超时时间
- `ocr_pages_limit`: 处理文档的前N页（用于目录提取）
- `toc_extraction_enabled`: 是否启用目录提取功能

## 🧪 测试集成

### 1. 运行集成测试

```bash
# 运行完整的GROBID集成测试
python3 test_grobid_integration.py
```

### 2. 测试文档目录提取

```bash
# 列出可用文档
python3 scripts/extract_document_toc.py --list

# 提取单个文档目录
python3 scripts/extract_document_toc.py --document report_1104_2024 --verbose

# 批量处理所有文档
python3 scripts/extract_document_toc.py --all
```

## 📊 API使用说明

### 主要API端点

GROBID提供多个API端点，CategoryRAG主要使用：

1. **processHeaderDocument** - 提取文档头部信息和结构
2. **processFulltextDocument** - 完整文档处理
3. **isalive** - 健康检查
4. **version** - 版本信息

### 请求参数

- `start/end`: 处理的页面范围
- `consolidateHeader`: 头部信息整合级别
- `consolidateCitations`: 引用整合级别
- `includeRawCitations`: 是否包含原始引用

## 🔧 故障排除

### 常见问题

#### 1. GROBID服务无法启动

**症状**: Docker容器启动失败或无法访问

**解决方案**:
```bash
# 检查Docker是否运行
docker --version

# 检查端口是否被占用
lsof -i :8070

# 查看容器日志
docker logs grobid-service

# 重新启动容器
docker stop grobid-service
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.2
```

#### 2. 文档处理超时

**症状**: 大文档处理时出现超时错误

**解决方案**:
```yaml
# 在config.yaml中增加超时时间
documents:
  preprocessing:
    grobid_timeout: 600  # 增加到10分钟
```

#### 3. 内存不足

**症状**: Docker容器因内存不足而崩溃

**解决方案**:
```bash
# 使用轻量级版本
docker run --rm --init --ulimit core=0 -p 8070:8070 lfoppiano/grobid:0.8.2

# 或者限制处理页面数
# 在config.yaml中设置较小的ocr_pages_limit
```

#### 4. 网络连接问题

**症状**: CategoryRAG无法连接到GROBID服务

**解决方案**:
```bash
# 检查服务是否运行
curl http://localhost:8070/api/isalive

# 检查防火墙设置
# 确保端口8070未被阻止

# 检查Docker网络
docker network ls
```

## 📈 性能优化

### 1. 选择合适的镜像版本

- **完整版本** (`grobid/grobid:0.8.2`): 包含深度学习模型，准确度高但资源消耗大
- **CRF版本** (`lfoppiano/grobid:0.8.2`): 仅使用CRF模型，速度快但准确度略低

### 2. 调整处理参数

```yaml
# 针对不同文档类型优化
documents:
  preprocessing:
    ocr_pages_limit: 5   # 对于简单文档，减少处理页面
    grobid_timeout: 120  # 对于小文档，减少超时时间
```

### 3. 并发处理

GROBID支持并发请求，但建议：
- 单个实例最多2-3个并发请求
- 大文档建议串行处理
- 监控内存使用情况

## 🔄 服务管理

### 启动服务

```bash
# 后台启动
docker run -d --name grobid-service --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.2
```

### 停止服务

```bash
# 停止容器
docker stop grobid-service
```

### 查看状态

```bash
# 查看运行中的容器
docker ps --filter name=grobid-service

# 查看日志
docker logs grobid-service

# 查看资源使用
docker stats grobid-service
```

## 📚 更多资源

- [GROBID官方文档](https://grobid.readthedocs.io/)
- [GROBID Docker文档](https://grobid.readthedocs.io/en/latest/Grobid-docker/)
- [GROBID API文档](https://grobid.readthedocs.io/en/latest/Grobid-service/)
- [CategoryRAG项目文档](./README.md)
