# CategoryRAG后端API接口文档

## 📋 **服务信息**
- **服务地址**: `http://127.0.0.1:5000`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **当前状态**: ✅ 运行中（10个集合，803个文档）

---

## 📊 **API端点总览**

| 端点 | 方法 | 功能 | 状态 | 说明 |
|------|------|------|------|------|
| `/api/health` | GET | 健康检查 | ✅ 可用 | 检查服务运行状态 |
| `/api/status` | GET | 系统状态 | ✅ 可用 | 获取详细系统信息 |
| `/api/collections` | GET | 集合信息 | ✅ 可用 | 获取所有文档集合 |
| `/api/query` | POST | 智能问答 | ✅ 可用 | 核心问答功能 |
| `/api/documents` | POST | 文档上传 | ✅ 可用 | 上传新文档 |

---

## 🔧 **详细API规范**

### **1. 健康检查**

检查服务是否正常运行。

```http
GET /api/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-25T13:35:19.135000",
  "service": "CategoryRAG Web API",
  "version": "1.0.0"
}
```

**字段说明**:
- `status`: 服务状态（"healthy" | "unhealthy"）
- `timestamp`: 响应时间戳
- `service`: 服务名称
- `version`: 服务版本

---

### **2. 系统状态**

获取系统详细运行状态和统计信息。

```http
GET /api/status
```

**响应示例**:
```json
{
  "status": "running",
  "timestamp": "2025-07-25T13:35:19.135000",
  "collections": [
    {
      "id": "report_1104_2024",
      "name": "1104报表_2024版",
      "document_count": 315
    },
    {
      "id": "east_data_structure", 
      "name": "EAST数据结构",
      "document_count": 52
    }
  ],
  "total_collections": 10,
  "total_documents": 803,
  "features": {
    "intelligent_qa": true,
    "multi_collection": true,
    "reranker_enabled": true,
    "query_enhancement": true
  }
}
```

**字段说明**:
- `status`: 系统运行状态
- `collections`: 集合列表（仅显示部分）
- `total_collections`: 总集合数
- `total_documents`: 总文档数
- `features`: 功能特性状态

---

### **3. 集合信息**

获取所有文档集合的详细信息。

```http
GET /api/collections
```

**响应示例**:
```json
{
  "collections": [
    {
      "id": "report_1104_2024",
      "name": "1104报表_2024版", 
      "description": "银行业监管统计报表制度2024版",
      "document_count": 315,
      "type": "监管报表"
    },
    {
      "id": "east_data_structure",
      "name": "EAST数据结构",
      "description": "EAST监管数据报送系统数据结构文档", 
      "document_count": 52,
      "type": "数据报送"
    },
    {
      "id": "pboc_statistics",
      "name": "人民银行金融统计制度汇编",
      "description": "人民银行金融统计制度相关文档",
      "document_count": 85,
      "type": "统计制度"
    }
  ],
  "total_count": 10
}
```

**字段说明**:
- `id`: 集合唯一标识符
- `name`: 集合显示名称
- `description`: 集合描述
- `document_count`: 文档数量
- `type`: 集合类型

---

### **4. 智能问答（核心接口）**

执行智能问答查询，支持多集合检索和重排序。

```http
POST /api/query
Content-Type: application/json
```

**请求格式**:
```json
{
  "question": "1104报表的资本充足率如何计算？"
}
```

**请求参数**:
- `question` (string, 必填): 用户问题

**响应格式**:
```json
{
  "answer": "根据1104报表制度，资本充足率的计算公式为：资本充足率 = 合格资本 / 风险加权资产 × 100%。具体计算步骤如下：\n\n1. 合格资本的确定：\n- 核心一级资本：实收资本、资本公积、盈余公积、一般风险准备、未分配利润等\n- 其他一级资本：优先股、永续债等\n- 二级资本：二级资本债券、超额贷款损失准备等\n\n2. 风险加权资产的计算：\n- 信用风险加权资产\n- 市场风险资本要求×12.5\n- 操作风险资本要求×12.5\n\n3. 资本充足率指标：\n- 核心一级资本充足率 = 核心一级资本 / 风险加权资产 × 100%\n- 一级资本充足率 = 一级资本 / 风险加权资产 × 100%\n- 资本充足率 = 总资本 / 风险加权资产 × 100%\n\n监管要求：\n- 核心一级资本充足率不低于5%\n- 一级资本充足率不低于6%\n- 资本充足率不低于8%",
  "question": "1104报表的资本充足率如何计算？",
  "retrieval_count": 20,
  "processing_time": 49.27,
  "collections_used": ["report_1104_2024", "report_1104_2022"],
  "timestamp": "2025-07-25T13:37:32.682000",
  "metadata": {
    "context_length": 47836,
    "retrieval_scores": [0.85, 0.82, 0.79],
    "reranker_enabled": true,
    "query_enhanced": true
  }
}
```

**响应字段说明**:
- `answer`: AI生成的回答内容
- `question`: 原始问题
- `retrieval_count`: 检索到的文档片段数量
- `processing_time`: 处理时间（秒）
- `collections_used`: 使用的文档集合列表
- `timestamp`: 响应时间戳
- `metadata`: 元数据信息
  - `context_length`: 上下文总长度
  - `retrieval_scores`: 检索相似度分数
  - `reranker_enabled`: 是否启用重排器
  - `query_enhanced`: 是否进行查询增强

---

### **5. 文档上传**

上传新文档到知识库。

```http
POST /api/documents
Content-Type: multipart/form-data
```

**请求参数**:
- `file` (file, 必填): 文档文件（支持PDF、DOCX、XLSX等）
- `collection_id` (string, 可选): 目标集合ID
- `description` (string, 可选): 文档描述

**支持的文件格式**:
- PDF文档 (`.pdf`)
- Word文档 (`.docx`, `.doc`)
- Excel文档 (`.xlsx`, `.xls`)

**响应示例**:
```json
{
  "message": "文档上传成功",
  "filename": "新监管制度.pdf",
  "file_path": "/data/KnowledgeBase/新监管制度.pdf",
  "collection_id": "regulatory_reference",
  "timestamp": "2025-07-25T13:35:19.135000",
  "note": "请重启系统以加载新配置"
}
```

**响应字段说明**:
- `message`: 操作结果消息
- `filename`: 上传的文件名
- `file_path`: 文件存储路径
- `collection_id`: 分配的集合ID
- `note`: 重要提示信息

---

## 💻 **前端集成代码示例**

### **TypeScript 类型定义**

```typescript
// API基础配置
const API_BASE_URL = 'http://127.0.0.1:5000';

// 类型定义
interface QueryRequest {
  question: string;
}

interface QueryResponse {
  answer: string;
  question: string;
  retrieval_count: number;
  processing_time: number;
  collections_used: string[];
  timestamp: string;
  metadata: {
    context_length: number;
    retrieval_scores: number[];
    reranker_enabled: boolean;
    query_enhanced: boolean;
  };
}

interface SystemStatus {
  status: string;
  timestamp: string;
  collections: Array<{
    id: string;
    name: string;
    document_count: number;
  }>;
  total_collections: number;
  total_documents: number;
  features: {
    intelligent_qa: boolean;
    multi_collection: boolean;
    reranker_enabled: boolean;
    query_enhancement: boolean;
  };
}

interface Collection {
  id: string;
  name: string;
  description: string;
  document_count: number;
  type: string;
}

interface CollectionsResponse {
  collections: Collection[];
  total_count: number;
}

interface HealthResponse {
  status: string;
  timestamp: string;
  service: string;
  version: string;
}

interface UploadResponse {
  message: string;
  filename: string;
  file_path: string;
  collection_id: string;
  timestamp: string;
  note: string;
}

interface ErrorResponse {
  error: string;
  timestamp: string;
  details?: string;
}
```

### **API服务类**

```typescript
// API服务类
class CategoryRAGAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  // 健康检查
  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseURL}/api/health`);
    if (!response.ok) {
      throw new Error(`健康检查失败: ${response.status}`);
    }
    return response.json();
  }

  // 获取系统状态
  async getStatus(): Promise<SystemStatus> {
    const response = await fetch(`${this.baseURL}/api/status`);
    if (!response.ok) {
      throw new Error(`获取系统状态失败: ${response.status}`);
    }
    return response.json();
  }

  // 智能问答
  async query(question: string): Promise<QueryResponse> {
    const response = await fetch(`${this.baseURL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `查询失败: ${response.status}`);
    }

    return response.json();
  }

  // 获取集合信息
  async getCollections(): Promise<CollectionsResponse> {
    const response = await fetch(`${this.baseURL}/api/collections`);
    if (!response.ok) {
      throw new Error(`获取集合信息失败: ${response.status}`);
    }
    return response.json();
  }

  // 文档上传
  async uploadDocument(
    file: File,
    collectionId?: string,
    description?: string
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    if (collectionId) {
      formData.append('collection_id', collectionId);
    }

    if (description) {
      formData.append('description', description);
    }

    const response = await fetch(`${this.baseURL}/api/documents`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `文档上传失败: ${response.status}`);
    }

    return response.json();
  }
}
```

### **基础使用示例**

```typescript
// 创建API实例
const api = new CategoryRAGAPI();

// 示例1: 健康检查
async function checkHealth() {
  try {
    const health = await api.healthCheck();
    console.log('服务状态:', health.status);
    console.log('服务版本:', health.version);
  } catch (error) {
    console.error('健康检查失败:', error);
  }
}

// 示例2: 智能问答
async function askQuestion(question: string) {
  try {
    console.log('正在查询:', question);
    const result = await api.query(question);

    console.log('回答:', result.answer);
    console.log('处理时间:', result.processing_time, '秒');
    console.log('检索文档数:', result.retrieval_count);
    console.log('使用集合:', result.collections_used);
    console.log('重排器状态:', result.metadata.reranker_enabled);

    return result;
  } catch (error) {
    console.error('查询失败:', error);
    throw error;
  }
}

// 示例3: 获取系统状态
async function getSystemInfo() {
  try {
    const status = await api.getStatus();
    console.log('系统状态:', status.status);
    console.log('总文档数:', status.total_documents);
    console.log('集合数量:', status.total_collections);
    console.log('功能特性:', status.features);

    return status;
  } catch (error) {
    console.error('获取状态失败:', error);
    throw error;
  }
}

// 示例4: 获取集合信息
async function getCollectionList() {
  try {
    const collections = await api.getCollections();
    console.log('集合总数:', collections.total_count);

    collections.collections.forEach(collection => {
      console.log(`${collection.name}: ${collection.document_count}个文档`);
    });

    return collections;
  } catch (error) {
    console.error('获取集合失败:', error);
    throw error;
  }
}

// 示例5: 文档上传
async function uploadFile(fileInput: HTMLInputElement) {
  const file = fileInput.files?.[0];
  if (!file) {
    console.error('请选择文件');
    return;
  }

  try {
    console.log('正在上传文件:', file.name);
    const result = await api.uploadDocument(
      file,
      'regulatory_reference',
      '新上传的监管文档'
    );

    console.log('上传成功:', result.message);
    console.log('文件路径:', result.file_path);
    console.log('分配集合:', result.collection_id);
    console.log('注意事项:', result.note);

    return result;
  } catch (error) {
    console.error('上传失败:', error);
    throw error;
  }
}
```

### **React Hook 示例**

```typescript
import { useState, useEffect, useCallback } from 'react';

// 自定义Hook: 系统状态
export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const api = new CategoryRAGAPI();
        const statusData = await api.getStatus();
        setStatus(statusData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取状态失败');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, []);

  const refresh = useCallback(async () => {
    const api = new CategoryRAGAPI();
    try {
      const statusData = await api.getStatus();
      setStatus(statusData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '刷新失败');
    }
  }, []);

  return { status, loading, error, refresh };
}

// 自定义Hook: 智能问答
export function useQuery() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useCallback(async (question: string): Promise<QueryResponse | null> => {
    if (!question.trim()) {
      setError('问题不能为空');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const api = new CategoryRAGAPI();
      const result = await api.query(question);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : '查询失败');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { query, loading, error };
}

// 自定义Hook: 集合信息
export function useCollections() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        setLoading(true);
        const api = new CategoryRAGAPI();
        const data = await api.getCollections();
        setCollections(data.collections);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取集合失败');
      } finally {
        setLoading(false);
      }
    };

    fetchCollections();
  }, []);

  return { collections, loading, error };
}
```

### **React组件示例**

```typescript
import React, { useState } from 'react';

// 查询组件
export function QueryComponent() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<QueryResponse | null>(null);
  const { query, loading, error } = useQuery();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    const result = await query(question);
    if (result) {
      setAnswer(result);
    }
  };

  return (
    <div className="query-component">
      <form onSubmit={handleSubmit} className="query-form">
        <div className="input-group">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="请输入您的问题..."
            disabled={loading}
            className="query-input"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="query-button"
          >
            {loading ? '查询中...' : '提交'}
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <strong>错误:</strong> {error}
        </div>
      )}

      {answer && (
        <div className="answer-section">
          <h3>回答:</h3>
          <div className="answer-content">
            {answer.answer.split('\n').map((line, index) => (
              <p key={index}>{line}</p>
            ))}
          </div>

          <div className="answer-metadata">
            <div className="metadata-item">
              <span className="label">处理时间:</span>
              <span className="value">{answer.processing_time.toFixed(2)}秒</span>
            </div>
            <div className="metadata-item">
              <span className="label">检索文档:</span>
              <span className="value">{answer.retrieval_count}个</span>
            </div>
            <div className="metadata-item">
              <span className="label">使用集合:</span>
              <span className="value">{answer.collections_used.join(', ')}</span>
            </div>
            <div className="metadata-item">
              <span className="label">重排器:</span>
              <span className="value">
                {answer.metadata.reranker_enabled ? '✅ 已启用' : '❌ 未启用'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 系统状态组件
export function SystemStatusComponent() {
  const { status, loading, error, refresh } = useSystemStatus();

  if (loading) return <div className="loading">加载中...</div>;
  if (error) return <div className="error">错误: {error}</div>;
  if (!status) return <div className="no-data">无数据</div>;

  return (
    <div className="system-status">
      <div className="status-header">
        <h2>系统状态</h2>
        <button onClick={refresh} className="refresh-button">
          刷新
        </button>
      </div>

      <div className="status-grid">
        <div className="status-card">
          <h3>运行状态</h3>
          <div className={`status-indicator ${status.status}`}>
            {status.status === 'running' ? '✅ 运行中' : '❌ 异常'}
          </div>
        </div>

        <div className="status-card">
          <h3>文档统计</h3>
          <div className="stats">
            <div>总集合数: {status.total_collections}</div>
            <div>总文档数: {status.total_documents}</div>
          </div>
        </div>

        <div className="status-card">
          <h3>功能特性</h3>
          <div className="features">
            {Object.entries(status.features).map(([key, enabled]) => (
              <div key={key} className="feature-item">
                <span>{enabled ? '✅' : '❌'}</span>
                <span>{key}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="collections-preview">
        <h3>集合预览</h3>
        <div className="collections-list">
          {status.collections.slice(0, 5).map(collection => (
            <div key={collection.id} className="collection-item">
              <span className="collection-name">{collection.name}</span>
              <span className="collection-count">{collection.document_count}个文档</span>
            </div>
          ))}
          {status.collections.length > 5 && (
            <div className="more-collections">
              还有 {status.collections.length - 5} 个集合...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// 文档上传组件
export function DocumentUploadComponent() {
  const [file, setFile] = useState<File | null>(null);
  const [collectionId, setCollectionId] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { collections } = useCollections();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    setFile(selectedFile || null);
    setResult(null);
    setError(null);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const api = new CategoryRAGAPI();
      const uploadResult = await api.uploadDocument(file, collectionId, description);
      setResult(uploadResult);

      // 重置表单
      setFile(null);
      setDescription('');
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-component">
      <h2>文档上传</h2>

      <form onSubmit={handleUpload} className="upload-form">
        <div className="form-group">
          <label htmlFor="file-input">选择文件:</label>
          <input
            id="file-input"
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.docx,.doc,.xlsx,.xls"
            disabled={uploading}
          />
          <small>支持格式: PDF, Word, Excel</small>
        </div>

        <div className="form-group">
          <label htmlFor="collection-select">目标集合:</label>
          <select
            id="collection-select"
            value={collectionId}
            onChange={(e) => setCollectionId(e.target.value)}
            disabled={uploading}
          >
            <option value="">自动选择</option>
            {collections.map(collection => (
              <option key={collection.id} value={collection.id}>
                {collection.name} ({collection.document_count}个文档)
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="description-input">文档描述:</label>
          <textarea
            id="description-input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="请输入文档描述（可选）"
            disabled={uploading}
            rows={3}
          />
        </div>

        <button
          type="submit"
          disabled={!file || uploading}
          className="upload-button"
        >
          {uploading ? '上传中...' : '上传文档'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>上传失败:</strong> {error}
        </div>
      )}

      {result && (
        <div className="success-message">
          <h3>上传成功!</h3>
          <div className="result-details">
            <div><strong>文件名:</strong> {result.filename}</div>
            <div><strong>集合:</strong> {result.collection_id}</div>
            <div><strong>路径:</strong> {result.file_path}</div>
            <div className="note"><strong>注意:</strong> {result.note}</div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 🔄 **错误处理**

### **常见错误码**

| 状态码 | 含义 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | 正常处理响应 |
| 400 | 请求参数错误 | 检查请求格式和参数 |
| 404 | 接口不存在 | 检查API路径是否正确 |
| 500 | 服务器内部错误 | 检查服务状态，重试请求 |
| 503 | 服务不可用 | 等待服务恢复 |

### **错误响应格式**

```json
{
  "error": "错误描述信息",
  "timestamp": "2025-07-25T13:35:19.135000",
  "details": "详细错误信息（可选）"
}
```

### **错误处理最佳实践**

```typescript
// 通用错误处理函数
function handleAPIError(error: any): string {
  if (error instanceof Error) {
    const message = error.message;

    // 根据错误类型返回用户友好的消息
    if (message.includes('500')) {
      return '服务器内部错误，请稍后重试';
    } else if (message.includes('400')) {
      return '请求参数有误，请检查输入';
    } else if (message.includes('404')) {
      return 'API接口不存在，请检查配置';
    } else if (message.includes('503')) {
      return '服务暂时不可用，请稍后重试';
    } else if (message.includes('timeout')) {
      return '请求超时，请检查网络连接';
    } else {
      return message;
    }
  }

  return '未知错误，请联系技术支持';
}

// 带重试的API调用
async function apiCallWithRetry<T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall();
    } catch (error) {
      const errorMessage = handleAPIError(error);

      // 如果是最后一次重试，抛出错误
      if (i === maxRetries - 1) {
        throw new Error(errorMessage);
      }

      // 如果是服务器错误，等待后重试
      if (errorMessage.includes('服务器') || errorMessage.includes('超时')) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        continue;
      }

      // 其他错误直接抛出
      throw new Error(errorMessage);
    }
  }

  throw new Error('重试次数已用完');
}

// 使用示例
async function robustQuery(question: string): Promise<QueryResponse | null> {
  try {
    const api = new CategoryRAGAPI();

    return await apiCallWithRetry(
      () => api.query(question),
      3,  // 最多重试3次
      2000  // 延迟2秒
    );
  } catch (error) {
    console.error('查询失败:', error);
    return null;
  }
}
```

### **防抖查询实现**

```typescript
import { useCallback, useRef } from 'react';

// 防抖Hook
function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]) as T;
}

// 防抖查询组件
export function DebouncedQueryComponent() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<QueryResponse | null>(null);
  const { query, loading, error } = useQuery();

  // 防抖查询函数
  const debouncedQuery = useDebounce(async (q: string) => {
    if (q.trim().length > 3) {  // 至少4个字符才查询
      const result = await query(q);
      if (result) {
        setAnswer(result);
      }
    }
  }, 800);  // 800ms延迟

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuestion(value);
    debouncedQuery(value);
  };

  return (
    <div className="debounced-query">
      <input
        type="text"
        value={question}
        onChange={handleInputChange}
        placeholder="输入问题，自动搜索..."
        disabled={loading}
      />

      {loading && <div className="loading-indicator">搜索中...</div>}
      {error && <div className="error">{error}</div>}
      {answer && (
        <div className="answer">
          <p>{answer.answer}</p>
        </div>
      )}
    </div>
  );
}
```

---

## 📈 **性能优化建议**

### **1. 请求优化**

```typescript
// 请求缓存实现
class CachedCategoryRAGAPI extends CategoryRAGAPI {
  private cache = new Map<string, { data: any; timestamp: number }>();
  private cacheTimeout = 5 * 60 * 1000; // 5分钟缓存

  async query(question: string): Promise<QueryResponse> {
    const cacheKey = `query:${question}`;
    const cached = this.cache.get(cacheKey);

    // 检查缓存
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      console.log('使用缓存结果');
      return cached.data;
    }

    // 调用API
    const result = await super.query(question);

    // 存储到缓存
    this.cache.set(cacheKey, {
      data: result,
      timestamp: Date.now()
    });

    return result;
  }

  // 清理过期缓存
  clearExpiredCache() {
    const now = Date.now();
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > this.cacheTimeout) {
        this.cache.delete(key);
      }
    }
  }
}

// 请求超时设置
class TimeoutCategoryRAGAPI extends CategoryRAGAPI {
  private timeout: number;

  constructor(baseURL?: string, timeout: number = 90000) {
    super(baseURL);
    this.timeout = timeout;
  }

  async query(question: string): Promise<QueryResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseURL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`查询失败: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('请求超时，请稍后重试');
      }
      throw error;
    }
  }
}
```

### **2. 用户体验优化**

```typescript
// 查询进度指示器
export function QueryWithProgress() {
  const [question, setQuestion] = useState('');
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [answer, setAnswer] = useState<QueryResponse | null>(null);

  const handleQuery = async () => {
    if (!question.trim()) return;

    setProgress(0);
    setStatus('正在处理查询...');

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev < 90) return prev + 10;
        return prev;
      });
    }, 1000);

    try {
      const api = new CategoryRAGAPI();
      const result = await api.query(question);

      setProgress(100);
      setStatus('查询完成');
      setAnswer(result);

    } catch (error) {
      setStatus('查询失败');
      console.error(error);
    } finally {
      clearInterval(progressInterval);
      setTimeout(() => {
        setProgress(0);
        setStatus('');
      }, 2000);
    }
  };

  return (
    <div className="query-with-progress">
      <div className="query-input">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="请输入问题..."
        />
        <button onClick={handleQuery}>查询</button>
      </div>

      {progress > 0 && (
        <div className="progress-section">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="progress-text">{status} ({progress}%)</div>
        </div>
      )}

      {answer && (
        <div className="answer-section">
          <h3>回答:</h3>
          <p>{answer.answer}</p>
          <div className="answer-meta">
            处理时间: {answer.processing_time.toFixed(2)}秒 |
            检索文档: {answer.retrieval_count}个
          </div>
        </div>
      )}
    </div>
  );
}

// 查询历史管理
export function QueryHistory() {
  const [history, setHistory] = useState<QueryResponse[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const { query, loading, error } = useQuery();

  const handleQuery = async () => {
    if (!currentQuery.trim()) return;

    const result = await query(currentQuery);
    if (result) {
      setHistory(prev => [result, ...prev.slice(0, 9)]); // 保留最近10条
      setCurrentQuery('');
    }
  };

  const rerunQuery = async (question: string) => {
    setCurrentQuery(question);
    const result = await query(question);
    if (result) {
      setHistory(prev => [result, ...prev.filter(h => h.question !== question)]);
    }
  };

  return (
    <div className="query-history">
      <div className="current-query">
        <input
          type="text"
          value={currentQuery}
          onChange={(e) => setCurrentQuery(e.target.value)}
          placeholder="请输入问题..."
        />
        <button onClick={handleQuery} disabled={loading}>
          {loading ? '查询中...' : '查询'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="history-list">
        <h3>查询历史</h3>
        {history.map((item, index) => (
          <div key={index} className="history-item">
            <div className="history-question">
              <strong>Q:</strong> {item.question}
              <button
                onClick={() => rerunQuery(item.question)}
                className="rerun-button"
              >
                重新查询
              </button>
            </div>
            <div className="history-answer">
              <strong>A:</strong> {item.answer.substring(0, 200)}...
            </div>
            <div className="history-meta">
              {new Date(item.timestamp).toLocaleString()} |
              {item.processing_time.toFixed(2)}秒 |
              {item.collections_used.join(', ')}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🚀 **快速开始**

### **1. 验证服务可用性**

在开始集成之前，请确认后端服务正常运行：

```bash
# 检查服务健康状态
curl http://127.0.0.1:5000/api/health

# 获取系统状态
curl http://127.0.0.1:5000/api/status

# 获取集合信息
curl http://127.0.0.1:5000/api/collections
```

**预期响应**:
- 健康检查应返回 `{"status": "healthy"}`
- 系统状态应显示10个集合和803个文档
- 集合信息应列出所有可用的文档集合

### **2. 测试查询功能**

```bash
# 测试智能问答
curl -X POST http://127.0.0.1:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是1104报表？"}'
```

**预期响应**:
- 应返回详细的回答内容
- `processing_time` 通常在30-60秒之间
- `reranker_enabled` 应为 `true`
- `collections_used` 应包含相关集合

### **3. 集成到前端项目**

#### **步骤1: 安装依赖**

如果使用TypeScript，确保安装类型定义：

```bash
npm install --save-dev @types/node
```

#### **步骤2: 复制API代码**

将本文档中的TypeScript代码复制到项目中：

```
src/
├── api/
│   ├── categoryrag.ts      # API服务类
│   └── types.ts           # 类型定义
├── hooks/
│   ├── useQuery.ts        # 查询Hook
│   ├── useSystemStatus.ts # 状态Hook
│   └── useCollections.ts  # 集合Hook
└── components/
    ├── QueryComponent.tsx
    ├── SystemStatus.tsx
    └── DocumentUpload.tsx
```

#### **步骤3: 配置API基础URL**

根据部署环境调整API地址：

```typescript
// 开发环境
const API_BASE_URL = 'http://127.0.0.1:5000';

// 生产环境
const API_BASE_URL = 'https://your-domain.com/api';

// 使用环境变量
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';
```

#### **步骤4: 基础集成测试**

创建一个简单的测试组件：

```typescript
import React, { useEffect, useState } from 'react';
import { CategoryRAGAPI } from './api/categoryrag';

export function APITestComponent() {
  const [status, setStatus] = useState<string>('检测中...');

  useEffect(() => {
    const testAPI = async () => {
      try {
        const api = new CategoryRAGAPI();

        // 测试健康检查
        const health = await api.healthCheck();
        if (health.status === 'healthy') {
          setStatus('✅ API连接正常');
        } else {
          setStatus('❌ API状态异常');
        }
      } catch (error) {
        setStatus(`❌ API连接失败: ${error.message}`);
      }
    };

    testAPI();
  }, []);

  return (
    <div className="api-test">
      <h2>API连接测试</h2>
      <p>{status}</p>
    </div>
  );
}
```

### **4. 样式建议**

为了更好的用户体验，建议添加以下CSS样式：

```css
/* 查询组件样式 */
.query-component {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.query-form {
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.query-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.query-button {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.query-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 回答区域样式 */
.answer-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.answer-content {
  line-height: 1.6;
  margin-bottom: 15px;
}

.answer-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  font-size: 14px;
  color: #666;
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.metadata-item {
  display: flex;
  gap: 5px;
}

.label {
  font-weight: bold;
}

/* 错误和成功消息样式 */
.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin: 10px 0;
}

.success-message {
  background: #d4edda;
  color: #155724;
  padding: 12px;
  border-radius: 4px;
  margin: 10px 0;
}

/* 加载状态样式 */
.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.loading-indicator {
  display: inline-block;
  padding: 8px 16px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
  font-size: 14px;
}

/* 进度条样式 */
.progress-section {
  margin: 15px 0;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4caf50;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}
```

---

## 📞 **技术支持**

### **常见问题解答**

**Q: API调用超时怎么办？**
A: 智能问答通常需要30-60秒处理时间，建议设置90秒超时。可以使用进度指示器改善用户体验。

**Q: 如何处理大量并发查询？**
A: 建议实现查询队列和防抖机制，避免同时发送多个查询请求。

**Q: 可以自定义查询的集合范围吗？**
A: 当前版本会自动选择最相关的集合。如需指定集合，请联系后端开发人员添加此功能。

**Q: 上传的文档什么时候生效？**
A: 文档上传后需要重启系统才能生效。建议在维护窗口期间批量上传文档。

### **错误排查步骤**

1. **检查网络连接**: 确认能访问 `http://127.0.0.1:5000/api/health`
2. **验证请求格式**: 确保Content-Type为application/json
3. **检查参数**: 确认必填参数已正确传递
4. **查看浏览器控制台**: 检查是否有CORS或其他错误
5. **检查服务状态**: 调用 `/api/status` 确认系统正常

### **联系方式**

如果在集成过程中遇到问题，请提供以下信息：

1. **具体错误信息**: 完整的错误消息和堆栈跟踪
2. **请求详情**: 请求URL、方法、参数和响应
3. **浏览器信息**: 浏览器类型、版本和控制台日志
4. **代码片段**: 相关的前端代码实现
5. **复现步骤**: 详细的操作步骤

**技术支持渠道**:
- 📧 邮件: [技术支持邮箱]
- 💬 即时通讯: [内部沟通工具]
- 📋 问题跟踪: [项目管理系统]

---

## 📝 **更新日志**

### **v1.0.0** (2025-07-25)
- ✅ 初始版本发布
- ✅ 支持智能问答功能
- ✅ 启用重排器提升查询质量
- ✅ 支持多集合检索
- ✅ 支持文档上传
- ✅ 完整的错误处理机制

### **计划功能**
- 🔄 查询历史持久化
- 🔄 实时查询状态推送
- 🔄 批量文档处理
- 🔄 自定义集合选择
- 🔄 查询结果导出

---

**文档版本**: v1.0.0
**最后更新**: 2025-07-25
**维护者**: CategoryRAG开发团队
```
