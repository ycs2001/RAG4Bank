# CategoryRAG自动化Pipeline使用指南

## 🚀 概述

CategoryRAG自动化Pipeline是一个完整的文档目录提取流水线，能够：
- 自动清理旧数据
- 批量处理所有配置文档
- 使用DeepSeek API进行智能分析
- 自动验证提取质量
- 生成详细报告
- 测试语义增强功能

## 📋 快速开始

### 一键运行完整Pipeline

```bash
# 处理所有配置的文档
python3 scripts/toc_extraction_pipeline.py --pipeline --all

# 或者使用原有脚本的Pipeline模式
python3 scripts/extract_document_toc.py --pipeline --all
```

### 处理特定文档

```bash
# 只处理1104报表
python3 scripts/toc_extraction_pipeline.py --pipeline --docs report_1104_2024 report_1104_2022

# 处理单个文档
python3 scripts/extract_document_toc.py --pipeline --document pboc_statistics
```

## 🔧 命令行参数

### Pipeline脚本参数

```bash
python3 scripts/toc_extraction_pipeline.py [OPTIONS]

选项:
  --pipeline          运行完整Pipeline（必需）
  --all              处理所有配置的文档
  --docs DOC1 DOC2   指定要处理的文档ID列表
  --no-semantic      跳过语义增强功能测试
  -h, --help         显示帮助信息
```

### 原有脚本的Pipeline模式

```bash
python3 scripts/extract_document_toc.py [OPTIONS]

选项:
  --pipeline, -p     运行自动化Pipeline（推荐）
  --document, -d     指定单个文档ID
  --all, -a          处理所有文档
  --verbose, -v      详细日志输出
  --list, -l         列出所有可用文档ID
```

## 📊 Pipeline执行流程

### 1. 初始化阶段
- ✅ 检查DeepSeek API配置
- ✅ 初始化GROBID服务连接
- ✅ 创建必要的目录结构

### 2. 数据清理阶段
- 🧹 自动删除旧的YAML目录文件
- 🧹 清理临时文件和缓存

### 3. 文档处理阶段
- 📄 逐个处理配置的文档
- 🔄 DOCX→PDF转换（LibreOffice）
- 📊 GROBID文本提取
- 🧠 DeepSeek智能目录分析
- 💾 保存YAML格式目录数据

### 4. 质量验证阶段
- 🔍 检查章节数量是否合理
- 📈 验证置信度是否达标
- 📋 统计表格编号识别情况
- ⚠️ 报告质量问题

### 5. 报告生成阶段
- 📊 生成控制台统计报告
- 💾 保存详细JSON报告文件
- 📈 计算成功率和处理时间

### 6. 语义增强测试阶段
- 🧠 重新加载目录缓存
- 🔍 测试查询意图分析
- ✅ 验证语义增强功能

## 📈 输出示例

### 控制台输出

```
🚀 CategoryRAG文档目录提取Pipeline启动
================================================================================
🔧 初始化系统组件...
✅ DeepSeek LLM初始化完成
✅ 文档预处理器初始化完成
✅ 语义增强器初始化完成

🧹 清理旧的目录数据...
✅ 清理完成，删除了 3 个旧文件

📋 发现 4 个配置的文档
  • report_1104_2024: 银行业监管统计报表制度2024版 ✅
  • report_1104_2022: 银行业监管统计报表制度2022版 ✅
  • pboc_statistics: 人民银行金融统计制度汇编 ✅
  • east_data_structure: EAST系统数据结构说明 ❌

============================================================
📖 处理进度: 1/4 - report_1104_2024
============================================================
📄 开始处理: report_1104_2024 - 银行业监管统计报表制度2024版
✅ 提取成功: 22个章节, 45个子项, 置信度: 0.88
📊 识别的表格编号: ['G01', 'G03', 'G04', 'G05', 'G07', 'G08', 'G40', 'G4A', 'G4B', 'G4C']...
⏱️ 处理耗时: 45.2秒

📊 提取成功率: 100.0% (4/4)
✅ 所有文档质量检查通过

📋 生成处理结果汇总报告...
================================================================================
🕐 Pipeline总耗时: 180.5秒
📚 处理文档数量: 4
✅ 成功提取: 4
❌ 提取失败: 0

📊 详细统计:
--------------------------------------------------------------------------------
文档ID               章节数   子项数   置信度   表格数   耗时(s)  状态
--------------------------------------------------------------------------------
report_1104_2024     22       45       0.88     24       45.2     ✅
report_1104_2022     20       42       0.85     22       42.1     ✅
pboc_statistics      29       5        0.90     8        38.7     ✅
east_data_structure  0        0        0.00     0        2.1      ❌

💾 详细报告已保存: logs/toc_pipeline_report_20250722_153045.json

🧠 测试语义增强功能...
============================================================
📚 目录缓存数量: 3
  • report_1104_2024: 22个章节, 置信度: 0.88, 状态: completed
  • report_1104_2022: 20个章节, 置信度: 0.85, 状态: completed
  • pboc_statistics: 29个章节, 置信度: 0.90, 状态: completed

🔍 测试查询意图分析:
  查询: 资本充足率相关的报表有哪些
    启用: True, 置信度: 0.85
    关键词: ['资本充足率', 'G40', 'G4A']
✅ 语义增强功能测试完成

🎉 Pipeline执行完成！
```

### 生成的文件

1. **目录数据文件**: `data/toc/*.yaml`
   - `report_1104_2024_toc.yaml`
   - `report_1104_2022_toc.yaml`
   - `pboc_statistics_toc.yaml`

2. **日志文件**: `logs/toc_pipeline.log`

3. **详细报告**: `logs/toc_pipeline_report_YYYYMMDD_HHMMSS.json`

## 🔧 故障排除

### 常见问题

#### 1. DeepSeek API配置错误
```
❌ DeepSeek API密钥未配置
```
**解决方案**: 检查 `config/config.yaml` 中的DeepSeek配置

#### 2. GROBID服务不可用
```
❌ 文档预处理器未启用
```
**解决方案**: 确保GROBID Docker容器正在运行

#### 3. LibreOffice转换失败
```
❌ LibreOffice未安装或不在PATH中
```
**解决方案**: 安装LibreOffice或检查路径配置

#### 4. 文档文件不存在
```
❌ 文件不存在: data/KnowledgeBase/xxx.docx
```
**解决方案**: 检查文档文件路径和文件是否存在

### 调试模式

```bash
# 启用详细日志
python3 scripts/toc_extraction_pipeline.py --pipeline --all --verbose

# 查看日志文件
tail -f logs/toc_pipeline.log
```

## 🎯 最佳实践

1. **首次运行**: 使用 `--pipeline --all` 处理所有文档
2. **增量更新**: 使用 `--docs` 参数处理特定文档
3. **质量检查**: 关注Pipeline报告中的质量问题
4. **定期维护**: 定期清理日志文件和临时数据

## 📚 相关文档

- [GROBID集成指南](./GROBID_SETUP_GUIDE.md)
- [系统配置说明](../config/config.yaml)
- [API文档](./API_REFERENCE.md)
