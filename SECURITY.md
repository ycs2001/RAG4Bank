# 安全配置指南

## 🔒 敏感信息处理

### API密钥安全
- ✅ 使用环境变量或配置文件存储API密钥
- ❌ 不要将API密钥硬编码在源代码中
- ❌ 不要将包含真实API密钥的配置文件提交到Git

### 配置文件安全
```bash
# 正确的做法
cp config/unified_config.yaml.example config/unified_config.yaml
# 编辑 unified_config.yaml 填入真实API密钥

# 错误的做法 - 不要这样做
git add config/unified_config.yaml  # 包含真实密钥的文件
```

## 📁 敏感文件清单

以下文件包含敏感信息，已在.gitignore中排除：

### 配置文件
- `config/unified_config.yaml` - 包含API密钥
- `.env` - 环境变量
- `config/api_keys.yaml` - API密钥配置

### 数据文件
- `data/KnowledgeBase/` - 可能包含敏感文档
- `data/chroma_db/` - 向量数据库
- `logs/` - 日志文件可能包含敏感信息

### 模型文件
- `bge-large-zh-v1.5/` - 大型模型文件
- `*.bin`, `*.safetensors` - 模型权重文件

## 🛡️ 生产环境安全建议

### 1. 访问控制
- 配置防火墙规则
- 使用HTTPS加密传输
- 实施API访问限制

### 2. 数据保护
- 定期备份重要数据
- 加密存储敏感文档
- 实施数据访问审计

### 3. 系统监控
- 监控异常访问模式
- 记录API调用日志
- 设置安全告警

## 🚨 安全事件响应

如果发现安全问题：

1. **立即行动**
   - 撤销泄露的API密钥
   - 更改所有相关密码
   - 检查访问日志

2. **评估影响**
   - 确定泄露范围
   - 评估潜在损失
   - 通知相关人员

3. **修复措施**
   - 修复安全漏洞
   - 更新安全配置
   - 加强监控措施

## 📞 安全联系方式

如发现安全漏洞，请联系：
- 邮箱: security@yourcompany.com
- 加密通信: [PGP公钥]
