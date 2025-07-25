# CategoryRAG后端API接口规范

## 启动后端服务

```bash
# 启动Web服务
python3 start_web.py

# 自定义端口
python3 start_web.py --port 8080

# 允许外部访问
python3 start_web.py --host 0.0.0.0
```

## 服务信息
- **地址**: `http://127.0.0.1:5000`
- **状态**: 运行中（10个集合，803个文档）

## API接口

### 1. 健康检查
```
GET /api/health
```
**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-25T13:35:19.135000",
  "service": "CategoryRAG Web API",
  "version": "1.0.0"
}
```

### 2. 系统状态
```
GET /api/status
```
**响应**:
```json
{
  "status": "running",
  "total_collections": 10,
  "total_documents": 803,
  "collections": [
    {
      "id": "report_1104_2024",
      "name": "1104报表_2024版",
      "document_count": 315
    }
  ],
  "features": {
    "intelligent_qa": true,
    "reranker_enabled": true
  }
}
```

### 3. 智能问答（核心功能）
```
POST /api/query
Content-Type: application/json
```
**请求**:
```json
{
  "question": "1104报表的资本充足率如何计算？"
}
```
**响应**:
```json
{
  "answer": "根据1104报表制度，资本充足率的计算公式为...",
  "question": "1104报表的资本充足率如何计算？",
  "retrieval_count": 20,
  "processing_time": 49.27,
  "collections_used": ["report_1104_2024", "report_1104_2022"],
  "timestamp": "2025-07-25T13:37:32.682000",
  "metadata": {
    "reranker_enabled": true,
    "query_enhanced": true
  }
}
```

### 4. 集合信息
```
GET /api/collections
```
**响应**:
```json
{
  "collections": [
    {
      "id": "report_1104_2024",
      "name": "1104报表_2024版",
      "description": "银行业监管统计报表制度2024版",
      "document_count": 315,
      "type": "监管报表"
    }
  ],
  "total_count": 10
}
```

### 5. 文档上传
```
POST /api/documents
Content-Type: multipart/form-data
```
**参数**:
- `file`: 文档文件（PDF、DOCX、XLSX）
- `collection_id`: 目标集合ID（可选）
- `description`: 文档描述（可选）

**响应**:
```json
{
  "message": "文档上传成功",
  "filename": "新监管制度.pdf",
  "file_path": "/data/KnowledgeBase/新监管制度.pdf",
  "collection_id": "regulatory_reference",
  "note": "请重启系统以加载新配置"
}
```

## 错误响应
```json
{
  "error": "错误描述",
  "timestamp": "2025-07-25T13:35:19.135000"
}
```

## 重要说明
- 查询处理时间：30-60秒
- 已启用重排器：从60个文档中重排序取前20个
- 支持多集合自动路由
- 建议设置90秒超时
