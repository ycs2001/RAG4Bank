# CategoryRAG - 智能文档问答系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

CategoryRAG是一个基于检索增强生成(RAG)技术的智能文档问答系统，专门针对监管报送、金融统计等专业领域文档进行优化。

## ✨ 核心特性

- 🧠 **智能问答**: 基于大语言模型的专业文档问答
- 📚 **多集合管理**: 支持多个文档集合的智能路由
- 🔍 **重排序优化**: 使用Cross-Encoder提升检索质量
- 🚀 **查询增强**: 自动添加相关上下文提升回答准确性
- 🌐 **Web API**: 提供RESTful API接口
- 📊 **实时监控**: 系统状态和性能监控

## 🏗️ 系统架构

```
CategoryRAG
├── 检索层 (ChromaDB + BGE嵌入)
├── 重排序层 (Cross-Encoder)
├── 生成层 (DeepSeek/Qwen LLM)
└── Web服务层 (Flask API)
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 8GB+ RAM (推荐16GB)
- 10GB+ 磁盘空间

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/CategoryRAG.git
cd CategoryRAG
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **下载BGE模型**
```bash
# 下载BGE-large-zh-v1.5模型到项目根目录
# 可从HuggingFace下载: https://huggingface.co/BAAI/bge-large-zh-v1.5
```

4. **配置系统**
```bash
# 复制配置文件模板
cp config/unified_config.yaml.example config/unified_config.yaml

# 编辑配置文件，填入API密钥
nano config/unified_config.yaml
```

5. **初始化数据库**
```bash
# 添加文档到知识库
python3 collection_database_builder.py
```

6. **启动Web服务**
```bash
# 启动API服务
python3 start_web.py

# 自定义端口
python3 start_web.py --port 8080
```

### 使用示例

```python
import requests

# 智能问答
response = requests.post('http://127.0.0.1:5000/api/query', 
                        json={'question': '什么是1104报表？'})
result = response.json()
print(result['answer'])
```

## 📁 项目结构

```
CategoryRAG/
├── src/                          # 源代码
│   ├── core/                     # 核心模块
│   ├── retrievers/               # 检索器
│   ├── rerankers/               # 重排器
│   └── config/                  # 配置管理
├── config/                      # 配置文件
├── data/                        # 数据目录
├── docs/                       # 文档
├── web_service.py              # Web服务
└── start_web.py               # 启动脚本
```

## 🔧 配置说明

### API密钥配置

在 `config/unified_config.yaml` 中配置：

```yaml
llm:
  deepseek:
    api_key: "YOUR_DEEPSEEK_API_KEY"
  qwen:
    api_key: "YOUR_QWEN_API_KEY"
```

## 📊 性能指标

- **查询响应时间**: 30-60秒
- **支持文档格式**: PDF, DOCX, XLSX
- **重排序优化**: 从60个候选中选择20个最相关

## 🔒 安全注意事项

- ⚠️ **API密钥**: 不要将API密钥提交到版本控制
- ⚠️ **敏感文档**: 知识库文档可能包含敏感信息
- ⚠️ **访问控制**: 生产环境请配置适当的访问控制

## 📝 API文档

详细的API文档请参考: [docs/backend_api_spec.md](docs/backend_api_spec.md)

## 📄 许可证

本项目采用 MIT 许可证

## 🙏 致谢

- [BGE](https://github.com/FlagOpen/FlagEmbedding) - 中文嵌入模型
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
- [DeepSeek](https://www.deepseek.com/) - 大语言模型
- [Flask](https://flask.palletsprojects.com/) - Web框架
