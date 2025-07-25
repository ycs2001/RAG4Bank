# 文档处理工作流程报告

## 处理统计

- **转换文件数**: 9
- **文本分块数**: 474
- **Excel分块数**: 121
- **错误数量**: 0

## 输出目录结构

```
processed_docs/
├── converted_markdown/     # 转换后的markdown文件
├── chunks/                # 所有文档分块（按文档归类）
│   ├── 文档1名称/         # 文档1的所有分块
│   ├── 文档2名称/         # 文档2的所有分块
│   └── ...
└── processing_report.md   # 本报告
```

## 处理详情

### 转换后的文档
- 位置: `processed_docs/converted_markdown`
- 格式: Markdown (.md)

### 文档分块
- 位置: `processed_docs/chunks`
- 分块方式: 固定大小分块（5000字符/块，1000字符重叠）
- 组织方式: 按文档归类到独立子文件夹
- 元信息: 包含源文档、分块ID、段落位置


## 使用说明

1. **查看转换结果**: 检查 `processed_docs/converted_markdown` 目录中的markdown文件
2. **使用文档分块**: `processed_docs/chunks` 中按文档归类的分块包含完整的元信息
3. **分块组织**: 每个源文档的分块都在独立的子文件夹中，便于管理和向量化

每个分块文件都包含YAML格式的元信息头，便于后续处理和检索。
