"""
ChromaDB检索器实现
"""

import os
from typing import List, Dict, Any, Optional
import logging
from .base_retriever import BaseRetriever, RetrievalResult

logger = logging.getLogger(__name__)

class ChromaDBRetriever(BaseRetriever):
    """ChromaDB检索器（支持多集合）"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化ChromaDB检索器

        Args:
            config: 检索器配置
        """
        super().__init__(config)
        self.client = None
        self.collections = {}  # 存储多个集合 {collection_id: collection_object}
        self.embedding_function = None

        # 从配置中获取参数
        chromadb_config = config.get('chromadb', {})
        embedding_config = config.get('embedding', {})

        self.db_path = chromadb_config.get('db_path', './data/chroma_db')
        self.default_collection_name = chromadb_config.get('default_collection_name', 'knowledge_base')
        self.model_path = embedding_config.get('model_path')
        self.normalize_embeddings = embedding_config.get('normalize_embeddings', True)
        self.collections_config = config.get('collections', [])

        self.initialize()
    
    def initialize(self):
        """初始化ChromaDB（支持多集合）"""
        try:
            import chromadb
            from chromadb.config import Settings
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

            # 创建ChromaDB客户端
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )

            # 强制使用BGE模型，不允许降级
            if not self.model_path or not os.path.exists(self.model_path):
                raise ValueError(f"BGE模型路径无效或不存在: {self.model_path}")

            self.embedding_function = SentenceTransformerEmbeddingFunction(
                model_name=self.model_path,
                normalize_embeddings=self.normalize_embeddings
            )
            self.logger.info(f"✅ 强制使用BGE模型: {self.model_path}")

            # 初始化所有配置的集合
            self._initialize_collections()

        except ImportError:
            raise ImportError("ChromaDB未安装，请运行: pip install chromadb")
        except Exception as e:
            self.logger.error(f"❌ ChromaDB初始化失败: {e}")
            raise

    def _initialize_collections(self):
        """初始化所有集合 - 仅加载配置的专用集合"""
        # 移除默认集合逻辑，强制使用明确的集合配置

        # 初始化配置的专用集合
        for collection_config in self.collections_config:
            collection_id = collection_config['collection_id']
            collection_name = collection_config['name']

            try:
                collection = self.client.get_collection(
                    name=collection_id,
                    embedding_function=self.embedding_function
                )
                count = collection.count()
                self.collections[collection_id] = collection
                self.logger.info(f"✅ 连接到集合: {collection_name} (ID: {collection_id}, 文档数: {count})")
            except Exception:
                collection = self.client.create_collection(
                    name=collection_id,
                    embedding_function=self.embedding_function,
                    metadata={
                        "description": collection_config.get('description', ''),
                        "keywords": ",".join(collection_config.get('keywords', []))  # 将列表转换为字符串
                    }
                )
                self.collections[collection_id] = collection
                self.logger.info(f"✅ 创建集合: {collection_name} (ID: {collection_id})")

        self.logger.info(f"🎯 多集合初始化完成，共 {len(self.collections)} 个集合")
    
    def retrieve(self,
                query: str,
                top_k: int = 5,
                filters: Optional[Dict[str, Any]] = None,
                collection_ids: Optional[List[str]] = None) -> List[RetrievalResult]:
        """
        检索相关文档（支持多集合）

        Args:
            query: 查询文本
            top_k: 每个集合返回结果数量
            filters: 过滤条件
            collection_ids: 指定检索的集合ID列表，None表示使用默认集合

        Returns:
            检索结果列表
        """
        try:
            # 预处理查询
            query = self.preprocess_query(query)

            # 强制要求指定集合ID，不允许默认检索
            if not collection_ids:
                raise ValueError("必须指定collection_ids，不支持默认集合检索")

            # 多集合检索
            return self._multi_collection_retrieve(query, top_k, filters, collection_ids)

        except Exception as e:
            self.logger.error(f"❌ 检索失败: {e}")
            raise  # 不再静默返回空列表，而是抛出异常

    def _single_collection_retrieve(self,
                                   query: str,
                                   top_k: int,
                                   filters: Optional[Dict[str, Any]],
                                   collection_id: str) -> List[RetrievalResult]:
        """单集合检索"""
        if collection_id not in self.collections:
            self.logger.error(f"集合不存在: {collection_id}")
            return []

        collection = self.collections[collection_id]

        # 构建where条件
        where_condition = None
        if filters:
            where_condition = {}
            for key, value in filters.items():
                if isinstance(value, str):
                    where_condition[key] = {"$eq": value}
                elif isinstance(value, list):
                    where_condition[key] = {"$in": value}
                else:
                    where_condition[key] = value

        # 执行检索
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_condition,
            include=['documents', 'metadatas', 'distances']
        )

        # 转换结果格式
        retrieval_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                content = results['documents'][0][i]
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0.0
                score = max(0, 1 - distance)  # 转换为相似度分数

                # 添加集合信息到元数据
                metadata['collection_id'] = collection_id

                result = RetrievalResult(
                    content=content,
                    metadata=metadata,
                    score=score,
                    distance=distance
                )
                retrieval_results.append(result)

        return retrieval_results

    def _multi_collection_retrieve(self,
                                  query: str,
                                  top_k: int,
                                  filters: Optional[Dict[str, Any]],
                                  collection_ids: List[str]) -> List[RetrievalResult]:
        """多集合检索"""
        all_results = []

        for collection_id in collection_ids:
            if collection_id not in self.collections:
                self.logger.warning(f"跳过不存在的集合: {collection_id}")
                continue

            # 从每个集合检索
            collection_results = self._single_collection_retrieve(
                query, top_k, filters, collection_id
            )

            # 添加集合标识
            for result in collection_results:
                result.metadata['source_collection'] = collection_id

            all_results.extend(collection_results)

            self.logger.info(f"🔍 集合 {collection_id} 检索到 {len(collection_results)} 个结果")

        # 按相似度分数排序
        all_results.sort(key=lambda x: x.score, reverse=True)

        # 后处理结果
        all_results = self.postprocess_results(all_results)

        self.logger.info(f"🎯 多集合检索完成: 查询='{query}', 总结果数={len(all_results)}")
        return all_results
    
    def add_documents(self,
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None,
                     collection_id: str = 'default'):
        """
        添加文档到指定集合

        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            ids: 文档ID列表
            collection_id: 目标集合ID
        """
        try:
            if collection_id not in self.collections:
                raise ValueError(f"集合不存在: {collection_id}")

            if ids is None:
                ids = [f"{collection_id}_doc_{i}" for i in range(len(documents))]

            collection = self.collections[collection_id]
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            self.logger.info(f"✅ 添加文档到集合 {collection_id}: {len(documents)} 个文档")

        except Exception as e:
            self.logger.error(f"❌ 添加文档失败: {e}")
            raise

    def add_documents_to_collection_by_source(self,
                                             documents: List[str],
                                             metadatas: List[Dict[str, Any]],
                                             source_document: str,
                                             ids: Optional[List[str]] = None):
        """
        根据源文档名称自动选择集合并添加文档

        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            source_document: 源文档名称
            ids: 文档ID列表
        """
        # 根据源文档名称确定目标集合
        collection_id = self._determine_collection_by_source(source_document)

        # 添加源文档信息到元数据
        for metadata in metadatas:
            metadata['source_document'] = source_document

        self.add_documents(documents, metadatas, ids, collection_id)

    def _determine_collection_by_source(self, source_document: str) -> str:
        """根据源文档名称确定目标集合"""
        source_lower = source_document.lower()

        # 匹配规则
        if '人民银行' in source_document or '金融统计' in source_document:
            return 'pboc_statistics'
        elif '1104' in source_document:
            if '2024' in source_document:
                return 'report_1104_2024'
            elif '2022' in source_document:
                return 'report_1104_2022'
            else:
                return 'report_1104_2024'  # 默认最新版
        elif 'east' in source_lower:
            if '元数据' in source_document or 'metadata' in source_lower:
                return 'east_metadata'
            else:
                return 'east_data_structure'
        elif '一表通' in source_document:
            if '映射' in source_document or 'mapping' in source_lower:
                return 'ybt_product_mapping'
            else:
                return 'ybt_data_structure'
        else:
            return 'default'  # 默认集合
    
    def delete_documents(self, ids: List[str]):
        """
        删除文档
        
        Args:
            ids: 要删除的文档ID列表
        """
        try:
            self.collection.delete(ids=ids)
            self.logger.info(f"✅ 删除文档成功: {len(ids)} 个文档")
            
        except Exception as e:
            self.logger.error(f"❌ 删除文档失败: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取检索器统计信息（多集合）

        Returns:
            统计信息字典
        """
        try:
            collection_stats = {}
            total_documents = 0

            for collection_id, collection in self.collections.items():
                try:
                    count = collection.count()
                    total_documents += count

                    # 获取样本文档分析分布
                    sample_results = collection.get(limit=min(10, count))
                    doc_stats = {}
                    if sample_results and 'metadatas' in sample_results:
                        for metadata in sample_results['metadatas']:
                            doc_name = metadata.get('document', 'Unknown')
                            doc_stats[doc_name] = doc_stats.get(doc_name, 0) + 1

                    collection_stats[collection_id] = {
                        'document_count': count,
                        'status': 'healthy',
                        'document_distribution': doc_stats
                    }
                except Exception as e:
                    collection_stats[collection_id] = {
                        'document_count': 0,
                        'status': 'error',
                        'error': str(e)
                    }

            return {
                'status': 'healthy',
                'type': 'ChromaDB (Multi-Collection)',
                'total_documents': total_documents,
                'collections': collection_stats,
                'db_path': self.db_path,
                'embedding_model': self.model_path or 'default',
                'strategy': 'multi_collection'
            }

        except Exception as e:
            self.logger.error(f"❌ 获取统计信息失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def clear_collection(self):
        """清空集合"""
        try:
            # 删除现有集合
            self.client.delete_collection(self.collection_name)
            self.logger.info(f"🗑️ 删除集合: {self.collection_name}")
            
            # 重新创建集合
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "RAG知识库向量集合"}
            )
            self.logger.info(f"✅ 重新创建集合: {self.collection_name}")
            
        except Exception as e:
            self.logger.error(f"❌ 清空集合失败: {e}")
            raise
    
    def search_by_document(self, 
                          query: str, 
                          document_name: str, 
                          top_k: int = 5) -> List[RetrievalResult]:
        """
        在指定文档中检索
        
        Args:
            query: 查询文本
            document_name: 文档名称
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        filters = {"document": document_name}
        return self.retrieve(query, top_k, filters)
