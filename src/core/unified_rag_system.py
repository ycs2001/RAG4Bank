"""
统一的RAG系统 - 整合所有功能，配置驱动，简化架构
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from ..config import EnhancedConfigManager
from ..llm.deepseek_llm import DeepSeekLLM
from ..retrievers.chromadb_retriever import ChromaDBRetriever
from ..rerankers import BaseReranker, CrossEncoderReranker


@dataclass
class RAGResponse:
    """RAG响应结果"""
    answer: str
    retrieval_count: int
    processing_time: float
    collections_used: List[str]
    metadata: Dict[str, Any]


class TopicClassifier:
    """简化的主题分类器"""
    
    def __init__(self, config_manager: EnhancedConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 加载集合配置
        self.collections_config = config_manager.get('embedding.collections', [])
        
        # 构建关键词映射
        self.keyword_mapping = {}
        for collection in self.collections_config:
            collection_id = collection['collection_id']
            keywords = collection.get('keywords', [])
            self.keyword_mapping[collection_id] = keywords
    
    def classify(self, query: str) -> List[str]:
        """分类查询，返回推荐的集合ID列表"""
        query_lower = query.lower()
        matched_collections = []

        # 1. 版本检测
        version_info = self._detect_version_intent(query_lower)
        self.logger.info(f"🔍 版本检测结果: {version_info}")

        # 2. 检测比较查询关键词
        comparison_keywords = ['对比', '比较', '差异', '差别', '区别', '相比']
        is_comparison = (
            any(keyword in query_lower for keyword in comparison_keywords) or
            ('和' in query_lower and ('分析' in query_lower or '对比' in query_lower or '比较' in query_lower)) or
            version_info['is_comparison']  # 基于版本检测的比较判断
        )

        # 3. 检测涉及的系统
        has_east = 'east' in query_lower
        has_ybt = '一表通' in query_lower
        has_pboc = any(keyword in query_lower for keyword in ['人民银行', '央行', '金融统计', '大集中'])
        has_1104 = any(keyword in query_lower for keyword in ['1104', 's71', 'g01'])

        # 4. 智能1104集合选择（优先处理）
        if has_1104:
            selected_1104_collections = self._select_1104_collections(version_info, is_comparison)
            if selected_1104_collections:
                matched_collections.extend(selected_1104_collections)
                self.logger.info(f"🎯 1104集合选择: {selected_1104_collections}")

                # 如果是纯1104查询且已选择，直接返回
                if not (has_east or has_ybt or has_pboc):
                    return matched_collections[:3]

        # 5. 比较查询：包含多个系统
        if is_comparison:
            if has_pboc and has_1104:
                matched_collections = ['pboc_statistics', 'report_1104_2024']
                self.logger.info(f"🔄 检测到人民银行与1104报表比较查询")
            elif has_east and has_1104:
                matched_collections = ['east_data_structure', 'east_metadata', 'report_1104_2024']
                self.logger.info(f"🔄 检测到EAST与1104报表比较查询")
            elif has_ybt and has_1104:
                matched_collections = ['ybt_data_structure', 'ybt_product_mapping', 'report_1104_2024']
                self.logger.info(f"🔄 检测到一表通与1104报表比较查询")
            else:
                # 通用比较查询，使用多个相关集合
                if has_pboc:
                    matched_collections.append('pboc_statistics')
                if has_1104 and 'report_1104' not in str(matched_collections):
                    # 如果1104还没有被处理，使用比较逻辑
                    matched_collections.extend(['report_1104_2024', 'report_1104_2022'])
                if has_east:
                    matched_collections.extend(['east_data_structure', 'east_metadata'])
                if has_ybt:
                    matched_collections.extend(['ybt_data_structure', 'ybt_product_mapping'])
                self.logger.info(f"🔄 检测到比较查询，使用多集合检索")

            if matched_collections:
                return matched_collections[:3]  # 限制最多3个集合

        # 单一系统查询（排他性匹配）
        if has_east:
            matched_collections = ['east_data_structure', 'east_metadata']
            self.logger.info(f"🎯 检测到EAST查询，只使用EAST集合")
            return matched_collections
        elif has_ybt:
            matched_collections = ['ybt_data_structure', 'ybt_product_mapping']
            self.logger.info(f"🎯 检测到一表通查询，只使用一表通集合")
            return matched_collections
        elif has_pboc:
            matched_collections = ['pboc_statistics']
            self.logger.info(f"🎯 检测到人民银行查询，只使用人民银行集合")
            return matched_collections

        # 6. 关键词匹配（作为补充，排除已处理的1104集合）
        keyword_matched = self._keyword_matching_with_priority(query_lower, matched_collections, has_1104)
        matched_collections.extend(keyword_matched)

        # 特殊处理：普惠金融相关查询（仅在没有明确系统指向时）
        if not matched_collections and any(keyword in query_lower for keyword in ['普惠金融', '报送表', '涉及哪些表']):
            for collection_id in ['report_1104_2024', 'pboc_statistics']:
                if collection_id not in matched_collections:
                    matched_collections.append(collection_id)

        # 如果没有匹配，默认使用最新的1104报表
        if not matched_collections:
            matched_collections = ['report_1104_2024']
            self.logger.info(f"🔄 未匹配到特定集合，使用默认1104报表")

        # 限制最多3个集合
        return matched_collections[:3]

    def _detect_version_intent(self, query_lower: str) -> Dict[str, Any]:
        """检测查询中的版本意图"""
        import re

        # 版本模式匹配
        version_patterns = {
            '2024': [r'2024年?', r'2024版', r'最新版?', r'新版', r'当前版'],
            '2022': [r'2022年?', r'2022版', r'旧版', r'老版', r'历史版'],
        }

        detected_versions = []
        explicit_versions = []

        # 检测明确的版本表达
        for version, patterns in version_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    detected_versions.append(version)
                    if pattern in [r'2024年?', r'2024版', r'2022年?', r'2022版']:
                        explicit_versions.append(version)
                    break

        # 检测比较意图
        is_comparison = (
            len(detected_versions) > 1 or  # 检测到多个版本
            any(keyword in query_lower for keyword in ['变化', '更新', '修订', '调整']) or
            ('新旧' in query_lower) or
            ('历史' in query_lower and '对比' in query_lower)
        )

        # 确定优先版本
        preferred_version = None
        if explicit_versions:
            # 如果有明确版本，优先使用最新的明确版本
            preferred_version = max(explicit_versions)
        elif detected_versions and not is_comparison:
            # 如果只检测到一个版本且非比较查询
            preferred_version = detected_versions[0]

        return {
            'detected_versions': detected_versions,
            'explicit_versions': explicit_versions,
            'preferred_version': preferred_version,
            'is_comparison': is_comparison,
            'confidence': len(explicit_versions) / max(len(detected_versions), 1) if detected_versions else 0
        }

    def _select_1104_collections(self, version_info: Dict[str, Any], is_comparison: bool) -> List[str]:
        """智能选择1104集合"""
        available_collections = ['report_1104_2024', 'report_1104_2022']

        # 1. 比较查询：返回所有版本
        if is_comparison:
            self.logger.info("📊 检测到比较查询，选择所有1104版本")
            return available_collections

        # 2. 明确版本偏好
        preferred_version = version_info.get('preferred_version')
        if preferred_version:
            if preferred_version == '2024':
                self.logger.info("🎯 明确要求2024版本")
                return ['report_1104_2024']
            elif preferred_version == '2022':
                self.logger.info("🎯 明确要求2022版本")
                return ['report_1104_2022']

        # 3. 检测到多个版本但非比较查询：使用最新版本
        detected_versions = version_info.get('detected_versions', [])
        if len(detected_versions) > 1:
            self.logger.info("⚖️ 检测到多版本但非比较查询，优先使用最新版本")
            return ['report_1104_2024']

        # 4. 默认策略：优先使用最新版本
        self.logger.info("📋 使用默认策略：优先最新版本")
        return ['report_1104_2024']

    def _keyword_matching_with_priority(self, query_lower: str, existing_collections: List[str], skip_1104: bool = False) -> List[str]:
        """优先级感知的关键词匹配"""
        matched_collections = []
        collection_scores = []

        # 获取集合配置信息
        collections_config = self.config_manager.get('embedding.collections', [])

        for collection_config in collections_config:
            collection_id = collection_config.get('collection_id')
            keywords = collection_config.get('keywords', [])
            priority = collection_config.get('priority', 999)  # 默认低优先级

            # 跳过已选择的集合
            if collection_id in existing_collections:
                continue

            # 跳过1104集合（如果已经处理过）
            if skip_1104 and collection_id.startswith('report_1104'):
                continue

            # 计算匹配分数
            match_score = 0
            matched_keywords = []

            for keyword in keywords:
                keyword_str = str(keyword).lower() if keyword is not None else ""
                if keyword_str and keyword_str in query_lower:
                    match_score += 1
                    matched_keywords.append(keyword_str)

            if match_score > 0:
                collection_scores.append({
                    'collection_id': collection_id,
                    'score': match_score,
                    'priority': priority,
                    'matched_keywords': matched_keywords
                })

        # 按优先级和匹配分数排序
        collection_scores.sort(key=lambda x: (-x['score'], x['priority']))

        # 选择最佳匹配
        for item in collection_scores:
            if item['collection_id'] not in matched_collections:
                matched_collections.append(item['collection_id'])
                self.logger.info(f"🔍 关键词匹配: {item['collection_id']} (分数:{item['score']}, 优先级:{item['priority']}, 关键词:{item['matched_keywords']})")

        return matched_collections


class UnifiedRAGSystem:
    """统一的RAG系统"""
    
    def __init__(self, config_manager: EnhancedConfigManager):
        """初始化RAG系统"""
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 从配置读取参数
        self.top_k = config_manager.get('retrieval.top_k', 10)
        self.similarity_threshold = config_manager.get('retrieval.similarity_threshold', 0.5)
        
        # 初始化组件
        self._initialize_components()
        
        self.logger.info("✅ 统一RAG系统初始化完成")
        self.logger.info(f"📊 配置: top_k={self.top_k}, threshold={self.similarity_threshold} (无字符限制)")

    def _init_reranker(self):
        """初始化重排器"""
        try:
            reranker_config = self.config_manager.get('reranker', {})

            if not reranker_config.get('enabled', False):
                self.reranker = None
                self.logger.info("重排器未启用")
                return

            reranker_type = reranker_config.get('type', 'cross_encoder')

            if reranker_type == 'cross_encoder':
                cross_encoder_config = reranker_config.get('cross_encoder', {})
                self.reranker = CrossEncoderReranker(cross_encoder_config)
            else:
                self.logger.warning(f"未知的重排器类型: {reranker_type}")
                self.reranker = None
                return

            if self.reranker and self.reranker.is_enabled():
                self.logger.info(f"✅ 重排器初始化成功: {reranker_type}")
            else:
                self.logger.warning("重排器初始化失败或被禁用")
                self.reranker = None

        except Exception as e:
            self.logger.error(f"重排器初始化失败: {e}")
            self.reranker = None
    
    def _initialize_components(self):
        """初始化所有组件"""
        # 1. 验证配置
        self._validate_configuration()
        
        # 2. 初始化LLM
        deepseek_config = self.config_manager.get('llm.deepseek', {})
        self.llm = DeepSeekLLM(deepseek_config)
        
        # 3. 初始化检索器
        retrieval_config = self.config_manager.get('retrieval', {})
        # 添加集合配置
        retrieval_config['collections'] = self.config_manager.get('embedding.collections', [])
        self.retriever = ChromaDBRetriever(retrieval_config)
        
        # 4. 初始化主题分类器
        self.topic_classifier = TopicClassifier(self.config_manager)

        # 5. 初始化重排器
        self._init_reranker()

        self.logger.info("✅ 所有组件初始化完成")
    
    def _validate_configuration(self):
        """验证配置完整性"""
        # 检查DeepSeek配置
        deepseek_config = self.config_manager.get('llm.deepseek', {})
        if not deepseek_config.get('api_key'):
            raise ValueError("DeepSeek API密钥未配置")
        
        # 检查BGE模型路径
        embedding_config = self.config_manager.get('retrieval.embedding', {})
        model_path = embedding_config.get('model_path')
        if not model_path or not Path(model_path).exists():
            raise ValueError(f"BGE模型路径无效: {model_path}")
        
        # 检查ChromaDB路径
        chromadb_config = self.config_manager.get('retrieval.chromadb', {})
        db_path = chromadb_config.get('db_path', './data/chroma_db')
        if not Path(db_path).exists():
            raise ValueError(f"ChromaDB数据库不存在: {db_path}")
        
        # 检查集合配置
        collections = self.config_manager.get('embedding.collections', [])
        if not collections:
            raise ValueError("未配置任何文档集合")
    
    def answer_question(self, question: str) -> RAGResponse:
        """回答问题"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🔍 处理问题: {question}")

            # 1. 查询语义增强
            enhanced_query_info = self._enhance_query(question)

            # 2. 主题分类（使用增强后的信息）
            collections = enhanced_query_info.get('collections', self.topic_classifier.classify(question))
            self.logger.info(f"🎯 推荐集合: {collections}")

            # 3. 检索相关文档（使用增强的关键词）
            search_queries = enhanced_query_info.get('keywords', [question])
            retrieval_results = self._enhanced_retrieve(search_queries, collections)
            
            if not retrieval_results:
                raise ValueError("未找到相关文档")
            
            self.logger.info(f"📚 检索到 {len(retrieval_results)} 个相关文档片段")
            
            # 3. 构建上下文
            context = self._build_context(retrieval_results)
            
            # 4. 生成答案
            answer = self._generate_answer(question, context)
            
            # 5. 构建响应
            processing_time = time.time() - start_time
            
            response = RAGResponse(
                answer=answer,
                retrieval_count=len(retrieval_results),
                processing_time=processing_time,
                collections_used=collections,
                metadata={
                    'retrieval_scores': [r.score for r in retrieval_results[:5]],
                    'context_length': len(context)
                }
            )
            
            self.logger.info(f"✅ 问题处理完成，耗时 {processing_time:.2f}秒")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"处理问题时发生错误: {e}"
            self.logger.error(error_msg)
            
            return RAGResponse(
                answer=f"抱歉，{error_msg}",
                retrieval_count=0,
                processing_time=processing_time,
                collections_used=[],
                metadata={'error': str(e)}
            )
    
    def _build_context(self, retrieval_results: List[Any]) -> str:
        """构建上下文"""
        context_parts = []
        total_length = 0
        max_total_length = 50000  # 简单的总长度限制，避免API错误
        max_single_doc_length = 20000  # 单个文档的最大长度

        # 使用检索到的文档，但控制总长度
        for i, result in enumerate(retrieval_results):
            # 优先使用原文档名称，回退到集合ID
            source_doc = result.metadata.get('source_document', result.metadata.get('collection_id', '未知'))

            # 截断过长的文档内容
            content = result.content
            if len(content) > max_single_doc_length:
                content = content[:max_single_doc_length] + "...[内容已截断]"

            doc_text = (
                f"文档{i+1} (来源: {source_doc}, 相似度: {result.score:.3f}):\n"
                f"{content}\n"
            )

            # 检查是否会超过长度限制
            if total_length + len(doc_text) > max_total_length and len(context_parts) > 0:
                self.logger.info(f"📏 达到长度限制，使用前{i}个文档")
                break

            context_parts.append(doc_text)
            total_length += len(doc_text)

            # 确保至少包含一个文档
            if i == 0 and len(doc_text) > max_total_length:
                self.logger.info(f"📏 第一个文档过长({len(doc_text)}字符)，已截断")
                break

        context = "\n".join(context_parts)
        self.logger.info(f"📝 构建上下文: {len(context_parts)}个文档, 总长度{len(context)}字符")
        return context
    
    def _generate_answer(self, question: str, context: str) -> str:
        """生成答案"""
        try:
            # 🔄 使用Prompt管理器获取问答模板
            from ..config.prompt_manager import PromptManager

            prompt_manager = PromptManager()
            prompt = prompt_manager.get_qa_prompt(
                user_question=question,
                retrieved_content=context,
                multi_document=len(context.split("来源:")) > 2  # 简单判断是否多文档
            )

            response = self.llm.generate(
                prompt,
                max_tokens=2000,
                temperature=0
            )
            return response.strip()

        except Exception as e:
            # 如果Prompt管理器失败，使用回退Prompt
            self.logger.warning(f"Prompt管理器失败，使用回退Prompt: {e}")

            fallback_prompt = f"""
基于以下文档内容，回答用户问题。请确保答案准确、专业，并引用具体的文档名称和条款。

问题: {question}

相关文档内容:
{context}

要求:
1. 基于提供的文档内容回答
2. 引用信息时必须使用文档的原始名称
3. 答案要简洁明了，重点突出
4. 如果文档内容不足以回答问题，请明确说明

答案:
"""

            try:
                response = self.llm.generate(
                    fallback_prompt,
                    max_tokens=2000,
                    temperature=0
                )
                return response.strip()
            except Exception as e:
                raise RuntimeError(f"答案生成失败: {e}")

    def _enhance_query(self, question: str) -> Dict[str, Any]:
        """简单的查询改写 - 三步走"""
        try:
            # 第一步：使用TopicClassifier确定目标文档集合
            target_collections = self.topic_classifier.classify(question)
            self.logger.info(f"🎯 预选文档集合: {target_collections}")

            # 第二步：尝试基于TOC进行查询增强（添加目录上下文）
            enhanced_query = self._simple_query_rewrite(question, target_collections)

            if enhanced_query and enhanced_query != question:
                # 查询增强成功
                enhanced_info = {
                    'original_query': question,
                    'keywords': [enhanced_query],  # 使用增强后的查询
                    'collections': target_collections,
                    'enhanced': True,
                    'enhanced_query': enhanced_query,
                    'enhancement_type': 'toc_context_enhanced'
                }

                self.logger.info(f"✅ 查询增强成功")
                self.logger.info(f"   原查询: {question}")
                self.logger.info(f"   增强后: {enhanced_query[:100]}..." if len(enhanced_query) > 100 else f"   增强后: {enhanced_query}")

                return enhanced_info
            else:
                # 查询增强失败或跳过，使用原查询
                self.logger.info("🔄 查询增强跳过，使用原查询")
                return {
                    'original_query': question,
                    'keywords': [question],
                    'collections': target_collections,
                    'enhanced': False,
                    'enhancement_type': 'no_enhancement'
                }

        except Exception as e:
            self.logger.warning(f"查询增强失败: {e}")
            return {
                'original_query': question,
                'keywords': [question],
                'collections': self.topic_classifier.classify(question),
                'enhanced': False,
                'enhancement_type': 'error'
            }

    def _enhanced_retrieve(self, search_queries: List[str], collections: List[str]) -> List[Any]:
        """增强检索方法 - 支持重排器"""
        # 使用第一个查询进行检索
        main_query = search_queries[0] if search_queries else ""

        try:
            # 检索更多文档用于重排
            results = self.retriever.retrieve(
                query=main_query,
                top_k=self.top_k,  # 现在是50个
                collection_ids=collections
            )
            self.logger.info(f"🔍 初始检索完成: 查询'{main_query[:50]}...' 返回{len(results)}个结果")

            # 应用重排器
            if self.reranker and self.reranker.is_enabled() and results:
                # 转换为重排器需要的格式
                docs_for_rerank = []
                for result in results:
                    docs_for_rerank.append({
                        'content': result.content,
                        'score': result.score,
                        'metadata': getattr(result, 'metadata', {}),
                        'original_result': result
                    })

                # 执行重排
                reranked_docs = self.reranker.rerank(main_query, docs_for_rerank)

                # 转换回原始结果格式
                final_results = []
                for doc in reranked_docs:
                    original_result = doc['original_result']
                    # 更新分数为重排分数
                    original_result.score = doc.get('rerank_score', original_result.score)
                    final_results.append(original_result)

                self.logger.info(f"🎯 重排完成: {len(results)}个 → {len(final_results)}个")
                return final_results
            else:
                # 没有重排器，返回原始结果
                return results

        except Exception as e:
            self.logger.error(f"检索失败: {e}")
            return []

    def _simple_query_rewrite(self, query: str, target_collections: List[str]) -> str:
        """查询增强函数 - 添加目录上下文而不是改写查询"""
        try:
            # 第一步：接收选定的文档集合作为参数（已完成）

            # 第二步：读取对应的TOC YAML文件
            toc_content = self._load_toc_for_collections(target_collections)
            if not toc_content:
                self.logger.info("📋 目标集合无对应TOC文件，跳过查询增强")
                return query

            # 第三步：提取相关目录内容并与原查询合并
            relevant_context = self._extract_relevant_toc_context(query, toc_content)
            if relevant_context:
                enhanced_query = f"{query} | 相关文档结构: {relevant_context}"
                self.logger.info(f"✅ 查询增强成功，添加了 {len(relevant_context)} 字符的目录上下文")
                return enhanced_query
            else:
                self.logger.info("📋 未找到相关目录内容，使用原查询")
                return query

        except Exception as e:
            self.logger.warning(f"查询增强过程出错: {e}")
            return query

    def _load_toc_for_collections(self, collections: List[str]) -> str:
        """为指定集合加载TOC内容"""
        import yaml
        from pathlib import Path

        toc_dir = Path("data/toc")
        if not toc_dir.exists():
            return ""

        toc_content_parts = []

        for collection in collections:
            # 尝试不同的文件名格式
            possible_files = [
                f"{collection}_toc.yaml",
                f"{collection}.yaml",
                f"{collection}_toc",
                f"{collection}"
            ]

            for filename in possible_files:
                toc_file = toc_dir / filename
                if toc_file.exists():
                    try:
                        with open(toc_file, 'r', encoding='utf-8') as f:
                            toc_data = yaml.safe_load(f)

                        # 构建简洁的TOC内容
                        content = self._format_toc_content(collection, toc_data)
                        if content:
                            toc_content_parts.append(content)
                            self.logger.info(f"✅ 加载TOC文件: {filename}")
                        break
                    except Exception as e:
                        self.logger.warning(f"读取TOC文件失败 {filename}: {e}")

        return "\n\n".join(toc_content_parts)

    def _format_toc_content(self, collection: str, toc_data: Dict[str, Any]) -> str:
        """格式化TOC内容为简洁的文本"""
        if not toc_data:
            return ""

        lines = [f"=== {collection} 目录结构 ==="]

        chapters = toc_data.get('chapters', [])
        for chapter in chapters:
            chapter_title = chapter.get('title', '')
            chapter_num = chapter.get('chapter_num', '')

            if chapter_title:
                lines.append(f"{chapter_num} {chapter_title}")

                # 添加子章节
                subsections = chapter.get('subsections', [])
                for subsection in subsections:
                    subsection_title = subsection.get('title', '')
                    if subsection_title:
                        lines.append(f"  - {subsection_title}")

        return "\n".join(lines)

    def _extract_relevant_toc_context(self, query: str, toc_content: str) -> str:
        """使用LLM从TOC内容中提取与查询相关的目录上下文"""
        try:
            prompt = f"""请分析用户查询，从以下文档目录结构中提取与查询最相关的章节和子章节信息。

用户查询: {query}

文档目录结构:
{toc_content}

请找出与用户查询最相关的章节和子章节，并按以下格式返回：
- 只返回相关的章节标题和子章节名称
- 用简洁的格式组织信息
- 如果没有相关内容，返回"无相关内容"

请直接返回相关的目录信息，不要其他解释："""

            response = self.llm.generate(prompt, max_tokens=300, temperature=0.1)
            relevant_context = response.strip()

            # 验证响应
            if relevant_context and relevant_context != "无相关内容" and len(relevant_context) > 10:
                return relevant_context
            else:
                return ""

        except Exception as e:
            self.logger.warning(f"LLM提取相关TOC上下文失败: {e}")
            return ""

    def _llm_rewrite_query(self, query: str, toc_content: str) -> str:
        """使用LLM根据TOC内容改写查询"""
        prompt = f"""请根据以下文档目录结构，改写用户查询以提高搜索准确性。

原始查询: {query}

文档目录结构:
{toc_content}

请分析用户查询与目录结构的关联，然后生成一个更精确的查询。改写要求：
1. 保持查询的核心意图不变
2. 加入目录中相关的具体术语和表格名称
3. 使查询更容易匹配到相关文档内容
4. 如果找不到相关内容，返回原查询

请直接返回改写后的查询，不要其他解释："""

        try:
            response = self.llm.generate(prompt, max_tokens=200, temperature=0.1)
            rewritten = response.strip()

            # 简单验证：改写后的查询不能为空且不能过长
            if rewritten and len(rewritten) > 5 and len(rewritten) < 200:
                return rewritten
            else:
                return query

        except Exception as e:
            self.logger.warning(f"LLM查询改写失败: {e}")
            return query

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'system_type': 'UnifiedRAGSystem',
            'configuration': {
                'top_k': self.top_k,
                'similarity_threshold': self.similarity_threshold
            },
            'components': {
                'llm_available': hasattr(self, 'llm') and self.llm is not None,
                'retriever_available': hasattr(self, 'retriever') and self.retriever is not None,
                'topic_classifier_available': hasattr(self, 'topic_classifier') and self.topic_classifier is not None,
                'toc_enhancement_available': True,  # TOC增强功能总是可用
                'reranker_available': hasattr(self, 'reranker') and self.reranker is not None,
                'reranker_enabled': hasattr(self, 'reranker') and self.reranker and self.reranker.is_enabled()
            },
            'collections': {
                'configured': len(self.config_manager.get('retrieval.collections', [])),
                'loaded': len(self.retriever.collections) if hasattr(self, 'retriever') else 0
            }
        }
