# CategoryRAG Web服务使用指南

## 🎯 概述

CategoryRAG Web服务提供了简化的REST API接口，让您可以通过HTTP请求访问CategoryRAG的核心功能，包括问答查询、系统状态查看和文档管理。

## 🚀 快速开始

### 1. 安装Web服务依赖

```bash
# 安装Web服务所需依赖
python install_web_deps.py

# 或手动安装
pip install flask flask-cors requests
```

### 2. 启动Web服务

```bash
# 方式1: 使用启动脚本
python start_web.py

# 方式2: 使用categoryrag命令
./categoryrag web start

# 自定义配置启动
./categoryrag web start --host 0.0.0.0 --port 8080 --debug
```

### 3. 验证服务状态

```bash
# 测试Web API
./categoryrag web test

# 或手动测试
python test_web_api.py
```

## 📋 API接口文档

### **基础信息**
- **基础URL**: `http://127.0.0.1:5000`
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

### **1. 健康检查**

**GET** `/api/health`

检查Web服务是否正常运行。

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-25T08:00:00.000000",
  "service": "CategoryRAG Web API",
  "version": "1.0.0"
}
```

### **2. 系统状态**

**GET** `/api/status`

获取CategoryRAG系统的详细状态信息。

**响应示例**:
```json
{
  "status": "running",
  "timestamp": "2025-07-25T08:00:00.000000",
  "collections": [
    {
      "id": "pboc_statistics",
      "name": "人民银行金融统计制度汇编",
      "document_count": 85
    }
  ],
  "total_collections": 10,
  "total_documents": 803,
  "configuration": {
    "retrieval_top_k": 30,
    "reranker_top_k": 20,
    "similarity_threshold": 0.5
  }
}
```

### **3. 集合信息**

**GET** `/api/collections`

获取所有文档集合的详细信息。

**响应示例**:
```json
{
  "collections": [
    {
      "id": "pboc_statistics",
      "name": "人民银行金融统计制度汇编",
      "description": "人民银行金融统计制度相关文档",
      "type": "统计制度",
      "keywords": ["人行", "央行", "统计制度"],
      "document_count": 85,
      "version": "现行版",
      "priority": 1
    }
  ],
  "total_count": 10
}
```

### **4. 问答查询**

**POST** `/api/query`

提交问题并获取AI回答。

**请求体**:
```json
{
  "question": "什么是1104报表？"
}
```

**响应示例**:
```json
{
  "answer": "1104报表是银行业监管统计报表...",
  "question": "什么是1104报表？",
  "retrieval_count": 5,
  "processing_time": 3.25,
  "collections_used": ["report_1104_2024"],
  "timestamp": "2025-07-25T08:00:00.000000",
  "metadata": {
    "context_length": 15000,
    "retrieval_scores": [0.85, 0.82, 0.78, 0.75, 0.72]
  }
}
```

### **5. 文档添加**

**POST** `/api/documents`

上传并添加新文档到知识库。

**请求**: `multipart/form-data`
- `file`: 要上传的文档文件

**支持的文件格式**:
- PDF (.pdf)
- Word (.docx, .doc)
- Excel (.xlsx, .xls)

**响应示例**:
```json
{
  "message": "文档添加成功",
  "filename": "新文档.pdf",
  "file_path": "data/KnowledgeBase/新文档.pdf",
  "timestamp": "2025-07-25T08:00:00.000000",
  "note": "请重启系统以加载新配置"
}
```

## 🔧 使用示例

### **Python客户端示例**

```python
import requests

# 基础URL
base_url = "http://127.0.0.1:5000"

# 1. 健康检查
response = requests.get(f"{base_url}/api/health")
print(response.json())

# 2. 问答查询
query_data = {"question": "什么是EAST系统？"}
response = requests.post(f"{base_url}/api/query", json=query_data)
result = response.json()
print(f"回答: {result['answer']}")

# 3. 文档上传
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{base_url}/api/documents", files=files)
    print(response.json())
```

### **curl命令示例**

```bash
# 健康检查
curl http://127.0.0.1:5000/api/health

# 系统状态
curl http://127.0.0.1:5000/api/status

# 问答查询
curl -X POST http://127.0.0.1:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是1104报表？"}'

# 文档上传
curl -X POST http://127.0.0.1:5000/api/documents \
  -F "file=@document.pdf"
```

### **JavaScript/前端示例**

```javascript
// 问答查询
async function askQuestion(question) {
  const response = await fetch('http://127.0.0.1:5000/api/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question: question })
  });
  
  const result = await response.json();
  return result.answer;
}

// 文档上传
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://127.0.0.1:5000/api/documents', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}
```

## ⚙️ 配置选项

### **启动参数**

```bash
python start_web.py --help

选项:
  --host HOST     服务器地址 (默认: 127.0.0.1)
  --port PORT     服务器端口 (默认: 5000)
  --debug         启用调试模式
  --check-only    仅检查系统状态
  --skip-checks   跳过系统检查
```

### **环境变量**

```bash
# API密钥配置
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export QWEN_API_KEY="your_qwen_api_key"

# 服务配置
export CATEGORYRAG_HOST="0.0.0.0"
export CATEGORYRAG_PORT="8080"
export CATEGORYRAG_DEBUG="true"
```

## 🛠️ 故障排除

### **常见问题**

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :5000
   
   # 使用其他端口
   python start_web.py --port 8080
   ```

2. **依赖缺失**
   ```bash
   # 安装缺失依赖
   python install_web_deps.py
   ```

3. **系统未初始化**
   ```bash
   # 检查系统状态
   ./categoryrag status
   
   # 重建数据库
   python3 collection_database_builder.py
   ```

4. **跨域问题**
   - Web服务已启用CORS支持
   - 如需自定义CORS设置，请修改`web_service.py`

### **日志查看**

```bash
# Web服务日志
tail -f logs/web_service.log

# 系统日志
tail -f logs/rag_system.log
```

## 🔒 安全注意事项

1. **生产环境部署**
   - 不要在生产环境使用`--debug`模式
   - 配置适当的防火墙规则
   - 考虑使用反向代理(nginx/apache)

2. **文件上传安全**
   - 系统已限制支持的文件类型
   - 上传的文件保存在`data/KnowledgeBase/`目录
   - 建议定期清理不需要的文件

3. **访问控制**
   - 当前版本不包含身份验证
   - 生产环境建议添加API密钥或其他认证机制

## 📊 性能优化

1. **并发处理**
   - 当前版本使用同步处理
   - 大量并发请求可能导致响应延迟

2. **缓存策略**
   - 系统会缓存向量检索结果
   - 重复查询响应更快

3. **资源监控**
   - 监控内存使用情况
   - 大文档处理可能消耗较多内存

---

💡 **提示**: Web服务是对现有CLI功能的补充，完全保持了系统的兼容性。您可以同时使用CLI和Web API访问CategoryRAG的功能。
