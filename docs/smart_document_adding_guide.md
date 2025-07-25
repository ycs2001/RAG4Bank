# CategoryRAG 智能文档添加指南

## 🎯 概述

CategoryRAG现在支持智能文档添加功能，能够自动生成集合配置、更新映射规则并处理文档，无需手动修改配置文件。

## 🚀 快速使用

### 基本用法
```bash
python smart_document_adder.py <文档路径>
```

### 示例
```bash
# 添加监管口径答疑文档
python smart_document_adder.py data/KnowledgeBase/监管口径答疑文档_v1.0.xlsx

# 添加新的1104报表文档
python smart_document_adder.py data/KnowledgeBase/1104报表补充说明_2024.docx

# 添加EAST相关文档
python smart_document_adder.py data/KnowledgeBase/EAST新增字段说明.xlsx
```

## 🔧 智能功能

### 1. **自动集合ID生成**

系统根据文档名称自动生成合适的集合ID：

| 文档类型 | 示例文档名 | 生成的集合ID |
|---------|-----------|-------------|
| 监管答疑 | 监管口径答疑文档_v1.0 | `regulatory_qa_guidance` |
| 1104报表 | 1104报表合辑【2024版】 | `report_1104_2024` |
| EAST文档 | EAST数据结构说明 | `east_data_structure` |
| 一表通 | 一表通产品映射 | `ybt_product_mapping` |
| 人民银行 | 人民银行统计制度 | `pboc_statistics` |
| 银行产品 | XX银行产品管理办法 | `bank_product_management` |

### 2. **智能关键词提取**

系统自动从文档名称中提取相关关键词：

```yaml
# 监管口径答疑文档_v1.0.xlsx
keywords:
  - 监管
  - 口径
  - 答疑
  - 填报口径
  - 监管问答
  - v1.0
```

### 3. **自动描述生成**

根据文档类型自动生成描述和分类：

```yaml
name: 监管口径答疑文档_v1.0
description: 监管口径答疑和填报指导文档
type: 答疑指导
priority: 1
version: v1.0
version_display: "[v1.0]"
```

### 4. **版本信息识别**

自动识别文档中的版本信息：
- `2024版` → `version: "2024版", version_display: "[2024版]"`
- `2022版` → `version: "2022版", version_display: "[2022版]"`
- `v1.0` → `version: "v1.0", version_display: "[v1.0]"`
- `v2.0` → `version: "v2.0", version_display: "[v2.0]"`

## 📋 完整工作流程

### 步骤1: 智能分析
```
📄 文档: 监管口径答疑文档_v1.0.xlsx
🔍 分析文档名称...
📋 生成集合配置:
   - 集合ID: regulatory_qa_guidance
   - 关键词: [监管, 口径, 答疑, ...]
   - 类型: 答疑指导
   - 优先级: 1
```

### 步骤2: 自动配置更新
```
📝 更新 config/unified_config.yaml
   ✅ 添加新集合配置到 embedding.collections

📝 更新 collection_database_builder.py
   ✅ 添加文档映射规则到 doc_to_collection_mapping
```

### 步骤3: 文档处理
```
🚀 执行文档处理:
   ./categoryrag add <文档路径> --collection <集合名> --keywords <关键词>

📦 生成分块文件
🔢 向量化处理
💾 存储到ChromaDB
```

## 🎯 支持的文档类型

### 监管类文档
- **监管口径答疑**: `regulatory_qa_guidance`
- **监管参考资料**: `regulatory_reference`
- **白皮书文档**: `regulatory_reference`

### 报表制度文档
- **1104报表**: `report_1104_2024` / `report_1104_2022`
- **EAST文档**: `east_data_structure` / `east_metadata`
- **一表通文档**: `ybt_data_structure` / `ybt_product_mapping`

### 统计制度文档
- **人民银行文档**: `pboc_statistics`
- **金融统计制度**: `pboc_statistics`

### 产品管理文档
- **银行产品管理**: `bank_product_management`
- **产品制度文档**: `bank_product_management`

## ⚙️ 高级配置

### 自定义映射规则

如需自定义映射规则，可以修改 `smart_document_adder.py` 中的映射字典：

```python
mappings = {
    '监管口径答疑': 'regulatory_qa_guidance',
    '新文档类型': 'custom_collection_id',
    # 添加更多映射规则...
}
```

### 自定义关键词规则

修改关键词生成逻辑：

```python
def _generate_keywords(self, name: str) -> List[str]:
    keywords = []
    
    # 添加自定义关键词规则
    if '新类型' in name:
        keywords.extend(['新类型', '相关词1', '相关词2'])
    
    return keywords
```

## 🔄 完整示例

### 添加新文档的完整流程

```bash
# 1. 将文档放入KnowledgeBase目录
cp 新监管文档_v2.0.xlsx data/KnowledgeBase/

# 2. 使用智能添加工具
python smart_document_adder.py data/KnowledgeBase/新监管文档_v2.0.xlsx

# 输出:
# 🎯 CategoryRAG智能文档添加工具
# ==================================================
# 🚀 开始智能处理文档: 新监管文档_v2.0
# 📋 生成集合配置: 新监管文档_v2.0 (ID: regulatory_document_v2)
# ✅ 已添加集合配置: 新监管文档_v2.0 (ID: regulatory_document_v2)
# ✅ 已添加文档映射: 新监管文档_v2.0 → regulatory_document_v2
# 📄 执行文档处理: ./categoryrag add ...
# ✅ 文档处理成功: 新监管文档_v2.0
# 
# 🎉 文档添加完成！
# 💡 配置文件和映射规则已自动更新

# 3. 重建数据库以应用更改
python3 collection_database_builder.py

# 4. 重启系统
./categoryrag start
```

## 📊 验证结果

### 检查配置更新
```bash
# 查看新增的集合配置
grep -A 10 "新监管文档" config/unified_config.yaml

# 查看新增的映射规则
grep "新监管文档" collection_database_builder.py
```

### 检查系统状态
```bash
# 查看系统状态
./categoryrag status

# 应该显示新增的集合
```

## ⚠️ 注意事项

1. **文档名称规范**: 建议使用有意义的中文文档名，便于自动识别
2. **版本标识**: 在文档名中包含版本信息（如v1.0、2024版）
3. **重复检查**: 系统会自动检查重复，避免重复添加
4. **数据库重建**: 添加文档后需要重建数据库以应用更改
5. **系统重启**: 配置更新后需要重启系统以加载新配置

## 🎉 优势

- ✅ **零配置**: 无需手动编辑配置文件
- ✅ **智能识别**: 自动识别文档类型和版本
- ✅ **一键添加**: 单个命令完成所有操作
- ✅ **错误处理**: 自动检查重复和错误
- ✅ **标准化**: 确保配置格式一致性

---

💡 **提示**: 使用智能文档添加工具可以大大简化文档管理流程，确保配置的一致性和正确性！
