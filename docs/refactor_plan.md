# CategoryRAG项目重构计划

## 🗑️ 需要删除的文件

### 重复和冗余脚本
- `rebuild_multi_collection_db.py` (保留simple_rebuild.py并重命名)
- `debug_error.py` (调试脚本)
- `debug_startup.py` (调试脚本)
- `diagnose_multi_collection.py` (诊断脚本)
- `fix_collection_mapping.py` (修复脚本)

### 临时文件和调试输出
- `debug_output.txt`
- `debug_output2.txt`
- `rebuild_output.txt`
- `rebuild_output2.txt`
- `vectorization.log`
- `rag_qa_system.log`
- `问题2_回答.txt`
- `问题3_回答.txt`

### 冗余文档和测试文件
- `ChromaDB向量化完成报告.md`
- `RAG参数配置指南.md`
- `RAG系统数据流水线完整分析报告.md`
- `RAG问答系统完成报告.md`
- `修复总结.md`
- `test/` 目录 (与tests/重复)

### 旧版本文件
- `document_converter.py` (根目录版本，保留src/utils/版本)
- `excel_chunker.py` (根目录版本)
- `text_chunker.py` (根目录版本)
- `vectorize_chunks.py` (旧版本)
- `vectors/` 目录 (旧版本向量存储)

## 📝 需要重命名的文件

### 功能性命名
- `simple_rebuild.py` → `collection_database_builder.py`
- `Chunk.py` → `document_processor.py`
- `build_rag_system.py` → `system_initializer.py`
- `test_multi_collection.py` → `multi_collection_test.py`
- `test_nine_questions.py` → `qa_system_test.py`
- `test_rag_system.py` → `rag_integration_test.py`

### 脚本目录整理
- `scripts/migrate_data.py` → `scripts/data_migration.py`
- `scripts/rag_cli.py` → `scripts/cli_interface.py`

## 🔧 需要合并的功能

### 数据库构建功能
- 合并 `rebuild_multi_collection_db.py` 和 `simple_rebuild.py` 的最佳实践
- 保留批处理和错误恢复功能

### 文档处理功能
- 整合根目录的处理脚本到 `src/utils/` 中

## 📁 目录结构优化

### 清理后的目录结构
```
CategoryRAG/
├── README.md
├── requirements.txt
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── config/
│   ├── core/
│   ├── llm/
│   ├── retrievers/
│   └── utils/
├── scripts/
│   ├── data_migration.py
│   └── cli_interface.py
├── tests/
│   ├── multi_collection_test.py
│   ├── qa_system_test.py
│   └── rag_integration_test.py
├── data/
│   ├── KnowledgeBase/
│   ├── chroma_db/
│   └── processed_docs/
├── logs/
├── docs/
├── rag_app.py
├── document_processor.py
├── collection_database_builder.py
└── system_initializer.py
```

## ✅ 重构执行顺序

1. 删除临时文件和调试输出
2. 删除重复脚本和冗余文档
3. 重命名文件使用功能性命名
4. 合并重复功能的脚本
5. 验证重构后的功能完整性
