# CategoryRAG前端集成快速指南

## 🚀 服务信息

- **服务地址**: `http://127.0.0.1:5000`
- **状态**: ✅ 运行中（10个集合，803个文档，重排器已启用）

## 📋 核心API

### 1. 智能问答（主要功能）

```typescript
// POST /api/query
const response = await fetch('http://127.0.0.1:5000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: '1104报表的资本充足率如何计算？' })
});

const result = await response.json();
// result.answer: 详细回答
// result.processing_time: 处理时间（30-60秒）
// result.collections_used: 使用的集合
// result.metadata.reranker_enabled: true（重排器已启用）
```

### 2. 系统状态

```typescript
// GET /api/status
const status = await fetch('http://127.0.0.1:5000/api/status').then(r => r.json());
// status.total_documents: 803
// status.total_collections: 10
// status.features.reranker_enabled: true
```

### 3. 健康检查

```typescript
// GET /api/health
const health = await fetch('http://127.0.0.1:5000/api/health').then(r => r.json());
// health.status: "healthy"
```

## 💻 TypeScript集成代码

```typescript
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
    reranker_enabled: boolean;
    query_enhanced: boolean;
  };
}

// API服务类
class CategoryRAGAPI {
  private baseURL = 'http://127.0.0.1:5000';

  async query(question: string): Promise<QueryResponse> {
    const response = await fetch(`${this.baseURL}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`查询失败: ${response.status}`);
    }

    return response.json();
  }

  async getStatus() {
    const response = await fetch(`${this.baseURL}/api/status`);
    return response.json();
  }

  async healthCheck() {
    const response = await fetch(`${this.baseURL}/api/health`);
    return response.json();
  }
}

// 使用示例
const api = new CategoryRAGAPI();

async function askQuestion() {
  try {
    const result = await api.query('什么是1104报表？');
    console.log('回答:', result.answer);
    console.log('处理时间:', result.processing_time, '秒');
  } catch (error) {
    console.error('查询失败:', error);
  }
}
```

## ⚛️ React Hook

```typescript
import { useState, useCallback } from 'react';

export function useQuery() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useCallback(async (question: string): Promise<QueryResponse | null> => {
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

// 组件使用
export function QueryComponent() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<QueryResponse | null>(null);
  const { query, loading, error } = useQuery();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await query(question);
    if (result) setAnswer(result);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="请输入问题..."
        disabled={loading}
      />
      <button type="submit" disabled={loading || !question.trim()}>
        {loading ? '查询中...' : '提交'}
      </button>
      
      {error && <div className="error">{error}</div>}
      {answer && (
        <div className="answer">
          <p>{answer.answer}</p>
          <small>
            处理时间: {answer.processing_time.toFixed(2)}秒 | 
            使用集合: {answer.collections_used.join(', ')}
          </small>
        </div>
      )}
    </form>
  );
}
```

## ⚠️ 重要注意事项

### 性能特点
- **查询时间**: 30-60秒（包含重排序优化）
- **重排器**: ✅ 已启用，从60个文档中重排序取前20个
- **并发限制**: 建议避免同时多个查询

### 错误处理
```typescript
// 推荐的错误处理
async function robustQuery(question: string) {
  try {
    const result = await api.query(question);
    return result;
  } catch (error) {
    if (error.message.includes('500')) {
      console.log('服务器错误，请稍后重试');
    } else if (error.message.includes('timeout')) {
      console.log('查询超时，请检查网络');
    }
    throw error;
  }
}
```

### 防抖优化
```typescript
// 防抖查询，避免频繁请求
import { useCallback, useRef } from 'react';

function useDebounce<T extends (...args: any[]) => any>(callback: T, delay: number): T {
  const timeoutRef = useRef<NodeJS.Timeout>();
  return useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => callback(...args), delay);
  }, [callback, delay]) as T;
}

// 使用
const debouncedQuery = useDebounce(async (q: string) => {
  if (q.length > 3) {
    const result = await api.query(q);
    setAnswer(result);
  }
}, 800);
```

## 🧪 快速测试

```bash
# 1. 检查服务状态
curl http://127.0.0.1:5000/api/health

# 2. 测试查询
curl -X POST http://127.0.0.1:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是EAST？"}'

# 3. 获取系统信息
curl http://127.0.0.1:5000/api/status
```

## 📊 当前系统能力

- ✅ **10个专业集合**: 1104报表、EAST、人行统计等
- ✅ **803个文档**: 覆盖监管报送全流程
- ✅ **智能重排序**: 从60个候选中精选20个最相关文档
- ✅ **查询增强**: 自动添加相关上下文
- ✅ **多集合路由**: 自动选择最相关的文档集合

## 🔗 完整文档

详细的API文档和高级功能请参考：[frontend_api_integration_guide.md](./frontend_api_integration_guide.md)

## 📞 技术支持

遇到问题请提供：
1. 具体错误信息
2. 请求和响应内容
3. 浏览器控制台日志
4. 相关代码片段

---

**快速开始**: 复制上述TypeScript代码到项目中，调整API地址，即可开始使用！
