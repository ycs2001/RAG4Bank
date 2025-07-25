# CategoryRAG 配置文件说明

## 📋 概述

CategoryRAG系统使用 `config/unified_config.yaml` 作为主配置文件，控制系统的各个方面，包括检索、重排、生成等核心功能。

## 🎯 关键参数：控制最终文档数量

### 📊 文档数量控制流程

```
用户查询 → 初始检索 → 重排筛选 → 长度限制 → 最终生成
          ↓           ↓           ↓           ↓
      top_k=30   reranker.top_k=20  max_length  实际文档数
```

### 🔧 核心参数配置

#### 1. **初始检索数量** (`retrieval.top_k`)
```yaml
retrieval:
  top_k: 30  # 每个集合的初始检索数量
```
- **作用**: 控制从向量数据库检索的原始文档数量
- **建议值**: 20-50
- **影响**: 数量越多，重排器可选择的文档越多，但计算开销越大

#### 2. **重排后文档数量** (`reranker.cross_encoder.top_k`) ⭐
```yaml
reranker:
  cross_encoder:
    top_k: 20  # 重排后保留的文档数量 - 关键参数！
```
- **作用**: **直接控制最终用于生成回答的文档数量**
- **重要性**: ⭐⭐⭐⭐⭐ (最关键参数)
- **建议值**: 
  - 简单查询: 10-15
  - 复杂查询: 15-25
  - 对比分析: 20-30

#### 3. **长度限制** (代码中硬编码)
```python
max_total_length = 50000  # 总字符数限制
```
- **作用**: 防止上下文过长导致API错误
- **影响**: 可能会截断部分文档

## 📝 完整配置结构

### 🔍 检索配置 (retrieval)
```yaml
retrieval:
  strategy: multi_collection        # 检索策略: single_collection | multi_collection
  default_retriever: chromadb       # 检索器类型
  top_k: 30                        # 初始检索数量
  similarity_threshold: 0.5         # 相似度阈值
  max_context_length: 16000         # 最大上下文长度
  
  topic_classification:             # 主题分类配置
    enabled: true                   # 是否启用主题分类
    confidence_threshold: 0.3       # 分类置信度阈值
    fallback_to_global: false       # 是否回退到全局检索
    max_collections: 3              # 最多同时检索的集合数
```

### 🎯 重排配置 (reranker)
```yaml
reranker:
  enabled: true                     # 是否启用重排器
  type: cross_encoder               # 重排器类型
  
  cross_encoder:
    model_name: cross-encoder/ms-marco-MiniLM-L-6-v2  # 模型名称
    device: cpu                     # 运行设备: cpu | cuda
    max_length: 512                 # 最大文本长度
    top_k: 20                      # ⭐ 重排后保留文档数 - 关键参数
```

### 🤖 LLM配置 (llm)
```yaml
llm:
  provider: deepseek               # LLM提供商
  deepseek:
    api_key: your_api_key         # API密钥
    base_url: https://api.deepseek.com
    model: deepseek-chat          # 模型名称
    max_tokens: 65535             # 最大生成token数
    temperature: 0                # 生成温度
    timeout: 1200                 # 超时时间(秒)
```

### 📊 向量化配置 (embedding)
```yaml
embedding:
  model:
    path: /path/to/bge-large-zh-v1.5  # BGE模型路径
    name: bge-large-zh-v1.5           # 模型名称
    device: cpu                       # 运行设备
    max_length: 512                   # 最大序列长度
    batch_size: 32                    # 批处理大小
    normalize: true                   # 是否归一化向量
```

## 🎯 常见配置场景

### 场景1: 提高回答质量 (基于更多文档)
```yaml
retrieval:
  top_k: 40                        # 增加初始检索数量
reranker:
  cross_encoder:
    top_k: 25                      # 增加最终文档数量
```

### 场景2: 提高响应速度
```yaml
retrieval:
  top_k: 20                        # 减少初始检索数量
reranker:
  cross_encoder:
    top_k: 10                      # 减少最终文档数量
```

### 场景3: 复杂对比分析
```yaml
retrieval:
  top_k: 50                        # 大量初始检索
reranker:
  cross_encoder:
    top_k: 30                      # 保留更多文档用于对比
```

## ⚠️ 注意事项

### 性能影响
- `retrieval.top_k` ↑ → 向量检索时间 ↑
- `reranker.top_k` ↑ → 重排计算时间 ↑ + LLM处理时间 ↑
- 总文档数 ↑ → 上下文长度 ↑ → API成本 ↑

### 质量权衡
- 文档数量过少 → 信息不全面
- 文档数量过多 → 噪音增加，重点不突出

### 建议配置
- **日常查询**: `top_k=20, reranker.top_k=15`
- **专业分析**: `top_k=30, reranker.top_k=20`
- **深度研究**: `top_k=40, reranker.top_k=25`

## 🔧 配置修改方法

1. **编辑配置文件**:
   ```bash
   vim config/unified_config.yaml
   ```

2. **重启系统**:
   ```bash
   ./categoryrag start
   ```

3. **验证配置**:
   ```bash
   ./categoryrag status
   ```

## 📈 监控和调优

### 关键指标
- **检索时间**: 初始检索耗时
- **重排时间**: 重排器处理耗时  
- **总处理时间**: 端到端响应时间
- **回答质量**: 用户满意度

### 调优建议
1. 从默认配置开始
2. 根据实际查询复杂度调整
3. 监控性能指标
4. 逐步优化参数

## 📚 集合配置 (embedding.collections)

### 集合定义结构
```yaml
embedding:
  collections:
    - name: "1104报表_2024版"           # 集合显示名称
      collection_id: report_1104_2024   # 集合唯一标识
      keywords:                         # 关键词匹配
        - "1104"
        - "2024"
        - "银行业监管统计"
      priority: 1                       # 优先级 (1=高, 2=中, 3=低)
      description: "2024版1104报表制度" # 集合描述
      version: "2024版"                 # 版本信息
      version_display: "[2024版]"       # 版本显示标签
      type: "监管报表"                   # 文档类型
```

### 主题分类规则
系统根据以下规则自动选择集合：

1. **版本比较查询** → 自动选择多个版本集合
2. **EAST查询** → 只使用EAST相关集合
3. **人民银行查询** → 只使用人民银行集合
4. **关键词匹配** → 根据keywords字段匹配

## 🔄 数据处理配置

### 文档处理 (data)
```yaml
data:
  raw_docs_dir: data/KnowledgeBase      # 原始文档目录
  processed_docs_dir: data/processed_docs  # 处理后文档目录
  chunks_dir: data/processed_docs/chunks   # 分块文件目录
  chroma_db_dir: data/chroma_db            # ChromaDB数据库目录
```

### 分块配置 (chunking)
```yaml
chunking:
  strategy: semantic                    # 分块策略: semantic | fixed | hybrid
  chunk_size: 1000                    # 分块大小(字符数)
  chunk_overlap: 200                   # 分块重叠(字符数)
  min_chunk_size: 100                  # 最小分块大小
  max_chunk_size: 2000                 # 最大分块大小
```

## 🚀 系统配置 (system)

### 基础配置
```yaml
system:
  name: "CategoryRAG智能问答系统"      # 系统名称
  version: "2.0.0"                    # 系统版本
  description: "银行监管领域智能问答"   # 系统描述
  log_level: INFO                     # 日志级别: DEBUG | INFO | WARNING | ERROR
  log_file: logs/rag_system.log       # 日志文件路径
```

### 调试配置 (debug)
```yaml
debug:
  enabled: false                      # 是否启用调试模式
  output_dir: ./debug_retrieval       # 调试输出目录
  save_raw_chunks: true               # 保存原始分块
  save_context: true                  # 保存上下文
  save_llm_responses: true            # 保存LLM响应
```

## 🔧 高级配置

### ChromaDB配置
```yaml
retrieval:
  chromadb:
    db_path: ./data/chroma_db           # 数据库路径
    default_collection_name: knowledge_base  # 默认集合名
  embedding:
    model_path: /path/to/bge-model      # 嵌入模型路径
    normalize_embeddings: true         # 是否归一化嵌入向量
```

### Prompt配置
```yaml
prompts:
  qa_template: |                      # 问答模板
    基于以下文档内容回答问题...
  comparison_template: |              # 对比分析模板
    请对比分析以下文档...
  summary_template: |                 # 总结模板
    请总结以下内容...
```

## 📊 性能优化配置

### 内存优化
```yaml
performance:
  max_memory_usage: 8GB               # 最大内存使用
  batch_processing: true              # 批处理模式
  cache_enabled: true                 # 启用缓存
  cache_size: 1000                    # 缓存大小
```

### 并发配置
```yaml
concurrency:
  max_workers: 4                      # 最大工作线程数
  timeout: 300                        # 超时时间(秒)
  retry_attempts: 3                   # 重试次数
```

## 🔍 故障排除

### 常见问题

#### 1. 文档数量不符合预期
**问题**: 实际使用的文档数量与配置不符
**解决**: 检查 `reranker.cross_encoder.top_k` 参数

#### 2. 响应时间过长
**问题**: 系统响应缓慢
**解决**:
- 降低 `retrieval.top_k`
- 降低 `reranker.top_k`
- 检查模型设备配置

#### 3. 回答质量不佳
**问题**: 回答不够准确或全面
**解决**:
- 增加 `reranker.top_k`
- 调整 `similarity_threshold`
- 检查集合配置

#### 4. 内存不足
**问题**: 系统内存占用过高
**解决**:
- 降低 `batch_size`
- 减少 `top_k` 参数
- 使用CPU而非GPU

### 配置验证
```bash
# 检查配置文件语法
python -c "import yaml; yaml.safe_load(open('config/unified_config.yaml'))"

# 验证系统状态
./categoryrag status

# 测试配置效果
./categoryrag start
```

---

💡 **关键提示**: 要基于20个文档生成回答，请设置 `reranker.cross_encoder.top_k: 20`

🔗 **相关文档**:
- [系统架构说明](architecture.md)
- [部署指南](deployment.md)
- [API文档](api.md)
