# CategoryRAG 配置快速参考

## 🎯 控制最终文档数量的关键参数

### ⭐ 核心参数 (影响最终回答的文档数)

```yaml
# 配置文件: config/unified_config.yaml

# 1. 初始检索数量
retrieval:
  top_k: 30  # 从向量数据库检索的原始文档数

# 2. 重排后文档数量 ⭐ 最关键参数
reranker:
  cross_encoder:
    top_k: 20  # 最终用于生成回答的文档数量
```

## 📊 参数流程图

```
用户查询
    ↓
初始检索 (retrieval.top_k = 30)
    ↓
重排筛选 (reranker.top_k = 20) ← 🎯 控制最终文档数
    ↓
长度检查 (max_length = 50000字符)
    ↓
生成回答 (基于最终文档数)
```

## 🔧 常用配置场景

### 基于20个文档生成 (当前配置)
```yaml
retrieval:
  top_k: 30
reranker:
  cross_encoder:
    top_k: 20  # ✅ 已配置为20个文档
```

### 基于15个文档生成 (快速响应)
```yaml
retrieval:
  top_k: 25
reranker:
  cross_encoder:
    top_k: 15
```

### 基于30个文档生成 (深度分析)
```yaml
retrieval:
  top_k: 50
reranker:
  cross_encoder:
    top_k: 30
```

## ⚡ 快速修改方法

### 1. 编辑配置文件
```bash
vim config/unified_config.yaml
```

### 2. 找到重排器配置
```yaml
reranker:
  cross_encoder:
    top_k: 20  # 修改这个数值
```

### 3. 重启系统
```bash
./categoryrag start
```

## 📈 性能影响

| 文档数量 | 响应时间 | 回答质量 | 适用场景 |
|---------|---------|---------|---------|
| 10-15   | 快      | 中等     | 简单查询 |
| 15-20   | 中等    | 良好     | 日常使用 |
| 20-25   | 较慢    | 优秀     | 复杂分析 |
| 25-30   | 慢      | 最佳     | 深度研究 |

## 🔍 验证配置

### 检查当前配置
```bash
grep -A 5 "cross_encoder:" config/unified_config.yaml
```

### 查看系统状态
```bash
./categoryrag status
```

### 测试效果
```bash
./categoryrag start
# 然后提问并观察 "检索结果: X 个文档片段" 的数量
```

## ⚠️ 注意事项

1. **`retrieval.top_k`** 必须 ≥ **`reranker.top_k`**
2. 文档数量过多会增加API成本和响应时间
3. 文档数量过少可能导致信息不全面
4. 建议从默认配置开始，根据实际需求调整

## 🎯 当前状态

✅ **已配置为基于20个文档生成回答**
- `retrieval.top_k: 30` (初始检索30个)
- `reranker.top_k: 20` (最终使用20个)

---

💡 **记住**: `reranker.cross_encoder.top_k` 是控制最终文档数量的关键参数！
