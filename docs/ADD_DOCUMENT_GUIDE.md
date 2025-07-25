# CategoryRAG文档添加指南

## 🎯 概述

本指南介绍如何向CategoryRAG系统添加新文档，包括完整的自动化工作流程。

## 📋 支持的文档格式

- **Word文档**: `.docx`, `.doc`
- **PDF文档**: `.pdf`
- **Excel文档**: `.xlsx`, `.xls`

## 🚀 快速开始

### 方法1: 交互式添加（推荐）

```bash
# 启动交互式文档添加工具
python3 scripts/add_document_workflow.py --interactive
```

按照提示输入：
1. 文档路径
2. 集合配置信息
3. 关键词设置

### 方法2: 命令行添加

```bash
# 添加单个文档
python3 scripts/add_document_workflow.py \
  --file "path/to/your/document.docx" \
  --collection-id "new_doc_collection" \
  --collection-name "新文档集合" \
  --collection-desc "新添加的专业文档" \
  --keywords "关键词1,关键词2,关键词3"
```

## 📁 目录结构

```
CategoryRAG/
├── data/
│   ├── raw_docs/           # 原始文档存放目录
│   ├── processed_docs/     # 处理后的文档
│   │   ├── converted_markdown/  # 转换后的markdown文件
│   │   └── chunks/         # 文档分块
│   ├── toc/               # 文档目录文件
│   └── chroma_db/         # 向量数据库
├── scripts/
│   └── add_document_workflow.py  # 文档添加工具
└── config/
    └── config.yaml        # 系统配置文件
```

## 🔄 工作流程详解

### 步骤1: 文档预处理
- 复制文档到`data/raw_docs/`目录
- 验证文档格式和完整性

### 步骤2: 文档转换和分块
- 使用GROBID服务处理PDF文档
- 将文档转换为Markdown格式
- 按语义进行智能分块（500-1000字符/块）

### 步骤3: TOC提取（仅PDF和Word文档）
- 使用LLM提取文档目录结构
- 生成YAML格式的目录文件
- 用于查询增强功能
- **支持格式**: PDF (.pdf) 和Word (.docx, .doc) 文档
- **跳过格式**: Excel (.xlsx, .xls)、文本 (.txt, .md) 文档将自动跳过此步骤

### 步骤4: 向量化
- 使用BGE模型生成文档向量
- 存储到ChromaDB向量数据库
- 按集合组织文档

### 步骤5: 配置更新
- 更新主题分类关键词映射
- 添加新集合配置信息
- 确保系统能够正确检索新文档

## ⚙️ 配置说明

### 集合配置

在`config/config.yaml`中会自动添加：

```yaml
topic_classification:
  keyword_mapping:
    new_doc_collection:
      - "关键词1"
      - "关键词2"

retrieval:
  collections:
    new_doc_collection:
      name: "新文档集合"
      description: "新添加的专业文档"
      enabled: true
```

### 文档映射

在`collection_database_builder.py`中会自动添加：

```python
doc_to_collection_mapping = {
    '新文档名称': 'new_doc_collection',
    # ... 其他映射
}
```

## 🧪 验证步骤

### 1. 检查文档处理结果

```bash
# 查看分块文件
ls -la data/processed_docs/chunks/新文档名称/

# 查看TOC文件
ls -la data/toc/新文档名称_toc.yaml
```

### 2. 验证数据库更新

```bash
# 检查ChromaDB集合
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='./data/chroma_db')
collections = client.list_collections()
for c in collections:
    print(f'{c.name}: {c.count()} 个文档')
"
```

### 3. 测试检索功能

```bash
# 重启系统
python3 start.py

# 在交互模式中测试
# 输入与新文档相关的查询
```

## 🔧 故障排除

### 常见问题

**问题1**: GROBID服务未启动
```bash
# 启动GROBID服务
docker run --rm -d -p 8070:8070 lfoppiano/grobid:0.8.0

# 验证服务状态
curl -f http://localhost:8070/api/isalive
```

**问题2**: BGE模型路径错误
```bash
# 检查模型路径配置
python3 -c "
from src.config import ConfigManager
config = ConfigManager()
print(config.get('retrieval.embedding.model_path'))
"
```

**问题3**: 文档处理失败
- 检查文档格式是否支持
- 确认文档没有损坏
- 查看日志文件：`logs/add_document.log`

### 日志文件

- **文档添加日志**: `logs/add_document.log`
- **文档处理日志**: `document_processing.log`
- **TOC提取日志**: `logs/toc_pipeline.log`
- **向量化日志**: `logs/chromadb_vectorization.log`

## 📊 性能优化

### 批量添加文档

如需添加多个文档，建议：

1. 将所有文档放入`data/raw_docs/`目录
2. 运行完整的文档处理流程：
   ```bash
   python3 document_processor.py
   python3 scripts/toc_extraction_pipeline.py
   python3 collection_database_builder.py
   ```

### 系统资源

- **内存需求**: 建议8GB以上
- **存储空间**: 每个文档约需要原文档大小的3-5倍空间
- **处理时间**: 平均每MB文档需要1-2分钟

## 🎉 完成

添加文档后，请：

1. 重启CategoryRAG系统
2. 测试新文档的检索功能
3. 验证主题分类是否正确
4. 检查查询增强功能是否生效

```bash
# 重启系统
python3 start.py

# 测试查询
# 在交互模式中输入与新文档相关的问题
```

## 📞 支持

如遇到问题，请：

1. 查看相关日志文件
2. 检查系统配置
3. 验证依赖服务状态
4. 参考故障排除章节

---

**祝您使用愉快！** 🚀
