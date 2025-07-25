"""
提示词管理器：管理和格式化提示词模板
"""

from typing import Dict, List
from ..retrievers.base_retriever import RetrievalResult
from .base_component import BaseComponent
from ..config import ConfigManager

class PromptManager(BaseComponent):
    """提示词管理器"""

    def __init__(self, config_manager: ConfigManager):
        """
        初始化提示词管理器

        Args:
            config_manager: 配置管理器实例
        """
        super().__init__(config_manager)

        # 从配置管理器获取prompt配置
        prompt_config = self.get_config_section('prompts')

        self.system_prompt = prompt_config.get('system_prompt', '')
        self.user_template = prompt_config.get('user_template', '')

        # 如果配置为空，使用默认模板
        if not self.system_prompt:
            self.system_prompt = self._get_default_system_prompt()

        if not self.user_template:
            self.user_template = self._get_default_user_template()

        self.logger.info("✅ PromptManager初始化完成")
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        if self.config_manager:
            return self.config_manager.get('prompts.system_prompt',
                """你是一个专业的金融监管领域智能助手，专门回答关于银行监管报表、EAST系统、人民银行统计制度等相关问题。

请基于提供的文档内容，准确、专业地回答用户的问题。特别注意版本信息的标注和处理。""")
        else:
            return """你是一个专业的金融监管领域智能助手，专门回答关于银行监管报表、EAST系统、人民银行统计制度等相关问题。

请基于提供的文档内容，准确、专业地回答用户的问题。特别注意版本信息的标注和处理。"""
    
    def _get_default_user_template(self) -> str:
        """获取默认用户模板"""
        default_template = """=== 相关文档内容 ===
{context}

=== 用户问题 ===
{query}

=== 回答要求 ===
1. 请基于上述文档内容进行回答，确保答案准确可靠
2. **重要：如果文档来源于不同版本，请在答案中明确标注每个信息的版本来源**
3. 对于表格、字段、规则等具体内容，请标注其所属版本（如"2024版"、"2022版"）
4. 如果涉及版本对比，请清晰列出版本间的差异
5. 避免重复列举相同的表格或内容，如果多个版本都有相同表格，请说明版本差异或合并说明
6. 回答要专业、详细，适合金融监管从业人员阅读
7. 如果涉及具体的表格、数据结构或报送要求，请详细说明
8. 在回答末尾注明主要参考的文档来源及其版本

请开始回答："""

        if self.config_manager:
            return self.config_manager.get('prompts.user_template', default_template)
        else:
            return default_template
    
    def build_context(self, retrieval_results: List[RetrievalResult]) -> str:
        """
        构建上下文（带去重和筛选）

        Args:
            retrieval_results: 检索结果列表

        Returns:
            构建的上下文字符串
        """
        if not retrieval_results:
            return "没有找到相关文档。"

        # 去重处理：基于内容相似度去重
        deduplicated_results = self._deduplicate_results(retrieval_results)

        context_parts = []
        for i, result in enumerate(deduplicated_results, 1):
            metadata = result.metadata
            document_name = metadata.get('document', '未知文档')
            collection_id = metadata.get('source_collection', '未知集合')
            score = result.score
            content = result.content

            # 根据集合ID确定版本信息
            version_info = self._get_version_info(collection_id)

            context_part = f"""
【文档{i}】
- 来源：{document_name} {version_info}
- 相似度：{score:.3f}
- 内容：{content}
"""
            context_parts.append(context_part)

        # 添加文档汇总信息
        doc_summary = self._build_document_summary(deduplicated_results)
        context_parts.append(doc_summary)

        return "\n".join(context_parts)

    def _build_document_summary(self, results: List[RetrievalResult]) -> str:
        """构建文档汇总信息（去重版本）"""
        collection_info = {}

        for result in results:
            metadata = result.metadata
            document_name = metadata.get('document', '未知文档')
            collection_id = metadata.get('source_collection', '未知集合')
            version_info = self._get_version_info(collection_id)

            # 按集合分组统计
            if collection_id not in collection_info:
                collection_info[collection_id] = {
                    'name': document_name,
                    'version': version_info,
                    'count': 0
                }
            collection_info[collection_id]['count'] += 1

        # 构建汇总信息
        summary_parts = ["\n=== 文档来源汇总 ==="]
        for collection_id, info in collection_info.items():
            clean_name = info['name'].replace('【', '').replace('】', '')
            summary_parts.append(f"- {clean_name} {info['version']} (引用{info['count']}次)")

        summary_parts.append("\n注意：在参考文档部分请使用上述具体的文档名称，不要重复列举。")

        return "\n".join(summary_parts)

    def _deduplicate_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """去重检索结果"""
        if not results:
            return results

        # 基于内容相似度去重
        deduplicated = []
        seen_contents = set()

        for result in results:
            # 提取内容的关键特征用于去重
            content_key = self._extract_content_key(result.content)

            if content_key not in seen_contents:
                seen_contents.add(content_key)
                deduplicated.append(result)

        # 按相似度排序，保留最相关的结果
        deduplicated.sort(key=lambda x: x.score, reverse=True)

        # 限制结果数量，避免过长的上下文
        max_results = 10  # 最多保留10个最相关的结果
        return deduplicated[:max_results]

    def _extract_content_key(self, content: str) -> str:
        """提取内容的关键特征用于去重"""
        # 提取表格名称作为去重的关键特征
        import re

        # 匹配表格名称模式
        table_patterns = [
            r'([SGG]\d+(?:_[IVX]+)?)\s',  # S71, G01_III等
            r'表名[：:]\s*([^\n\s]+)',     # 表名: XXX
            r'表格[：:]\s*([^\n\s]+)',     # 表格: XXX
        ]

        for pattern in table_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        # 如果没有匹配到表格名称，使用内容的前100个字符作为特征
        return content[:100].strip()

    def _get_version_info(self, collection_id: str) -> str:
        """根据集合ID获取版本信息"""
        # 从配置中获取集合信息
        if self.config_manager:
            collections = self.config_manager.get('retrieval.collections', [])

            for collection in collections:
                if collection.get('collection_id') == collection_id:
                    return collection.get('version_display', f'[{collection_id}]')

        # 默认映射（兼容性）
        default_mapping = {
            'report_1104_2024': '[2024版]',
            'report_1104_2022': '[2022版]',
            'pboc_statistics': '[人民银行统计制度]',
            'east_data_structure': '[EAST数据结构]',
            'east_metadata': '[EAST元数据]',
            'ybt_data_structure': '[一表通数据结构]',
            'ybt_product_mapping': '[一表通产品映射]',
            'default': '[默认集合]',
            'knowledge_base': '[知识库]'
        }
        return default_mapping.get(collection_id, f'[{collection_id}]')

    def format_prompt(self, query: str, retrieval_results: List[RetrievalResult]) -> str:
        """
        格式化完整提示词
        
        Args:
            query: 用户查询
            retrieval_results: 检索结果
            
        Returns:
            格式化的提示词
        """
        # 构建上下文
        context = self.build_context(retrieval_results)
        
        # 格式化用户模板
        user_prompt = self.user_template.format(
            context=context,
            query=query
        )
        
        # 组合系统提示词和用户提示词
        if self.system_prompt:
            full_prompt = f"{self.system_prompt}\n\n{user_prompt}"
        else:
            full_prompt = user_prompt
        
        return full_prompt
    
    def format_chat_messages(self, query: str, retrieval_results: List[RetrievalResult]) -> List[Dict[str, str]]:
        """
        格式化为对话消息格式
        
        Args:
            query: 用户查询
            retrieval_results: 检索结果
            
        Returns:
            对话消息列表
        """
        messages = []
        
        # 添加系统消息
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # 构建用户消息
        context = self.build_context(retrieval_results)
        user_content = self.user_template.format(
            context=context,
            query=query
        )
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    def update_templates(self, 
                        system_prompt: str = None, 
                        user_template: str = None):
        """
        更新提示词模板
        
        Args:
            system_prompt: 新的系统提示词
            user_template: 新的用户模板
        """
        if system_prompt is not None:
            self.system_prompt = system_prompt
            self.logger.info("✅ 系统提示词已更新")

        if user_template is not None:
            self.user_template = user_template
            self.logger.info("✅ 用户模板已更新")
    
    def get_templates(self) -> Dict[str, str]:
        """
        获取当前模板
        
        Returns:
            模板字典
        """
        return {
            'system_prompt': self.system_prompt,
            'user_template': self.user_template
        }
