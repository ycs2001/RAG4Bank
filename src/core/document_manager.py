"""
文档管理核心模块
提供文档分块和向量数据的增删改查功能
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

@dataclass
class DocumentInfo:
    """文档信息"""
    name: str
    collection_id: str
    chunk_files: List[str]
    vector_count: int
    file_path: Optional[str] = None

@dataclass
class OperationResult:
    """操作结果"""
    success: bool
    message: str
    details: Dict[str, Any] = None
    affected_items: int = 0

class DocumentManager:
    """文档管理器"""
    
    def __init__(self, config_manager):
        """
        初始化文档管理器
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager
        self.data_paths = config_manager.get_data_paths()
        self.chroma_client = None
        self._init_chroma_client()
    
    def _init_chroma_client(self):
        """初始化ChromaDB客户端"""
        try:
            chroma_db_path = self.data_paths["chroma_db"]
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"✅ ChromaDB客户端初始化成功: {chroma_db_path}")
        except Exception as e:
            logger.error(f"❌ ChromaDB客户端初始化失败: {e}")
            raise
    
    def list_documents(self, collection_id: Optional[str] = None) -> List[DocumentInfo]:
        """
        列出文档信息
        
        Args:
            collection_id: 集合ID，为None时列出所有文档
            
        Returns:
            文档信息列表
        """
        documents = []
        chunks_dir = Path(self.data_paths["chunks"])
        
        if not chunks_dir.exists():
            return documents
        
        # 遍历分块目录
        for doc_dir in chunks_dir.iterdir():
            if not doc_dir.is_dir():
                continue
            
            doc_name = doc_dir.name
            
            # 查找分块文件
            chunk_files = list(doc_dir.glob("*.md"))
            
            # 从ChromaDB获取向量数量
            vector_count = self._get_document_vector_count(doc_name, collection_id)
            
            # 推断集合ID（从分块文件元数据或目录结构）
            inferred_collection_id = self._infer_collection_id(doc_dir)
            
            if collection_id is None or inferred_collection_id == collection_id:
                documents.append(DocumentInfo(
                    name=doc_name,
                    collection_id=inferred_collection_id,
                    chunk_files=[str(f) for f in chunk_files],
                    vector_count=vector_count
                ))
        
        return documents
    
    def _get_document_vector_count(self, doc_name: str, collection_id: Optional[str] = None) -> int:
        """获取文档在向量数据库中的数量"""
        try:
            collections = self.chroma_client.list_collections()
            total_count = 0
            
            for collection in collections:
                if collection_id and collection.name != collection_id:
                    continue
                
                # 查询包含该文档名的向量
                try:
                    # 获取所有数据，然后在客户端过滤
                    results = collection.get()
                    if results and results.get('ids') and results.get('metadatas'):
                        for metadata in results['metadatas']:
                            if metadata and 'source' in metadata:
                                if doc_name in metadata['source']:
                                    total_count += 1
                except Exception as e:
                    logger.warning(f"查询集合 {collection.name} 失败: {e}")
                    continue
            
            return total_count
        except Exception as e:
            logger.warning(f"获取文档向量数量失败: {e}")
            return 0
    
    def _infer_collection_id(self, doc_dir: Path) -> str:
        """从分块文件推断集合ID"""
        try:
            # 尝试从第一个分块文件的元数据中获取集合信息
            chunk_files = list(doc_dir.glob("*.md"))
            if chunk_files:
                with open(chunk_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单的元数据解析
                    if "集合ID:" in content:
                        for line in content.split('\n'):
                            if "集合ID:" in line:
                                return line.split("集合ID:")[-1].strip()
            
            # 如果无法从元数据获取，使用目录名作为默认值
            return doc_dir.name.lower().replace(' ', '_')
        except Exception:
            return "unknown"
    
    def remove_document(self, document_name: str, collection_id: Optional[str] = None) -> OperationResult:
        """
        删除指定文档的所有数据
        
        Args:
            document_name: 文档名称
            collection_id: 集合ID
            
        Returns:
            操作结果
        """
        try:
            removed_chunks = 0
            removed_vectors = 0
            
            # 1. 删除分块文件
            chunks_dir = Path(self.data_paths["chunks"])
            doc_chunk_dir = chunks_dir / document_name
            
            if doc_chunk_dir.exists():
                chunk_files = list(doc_chunk_dir.glob("*.md"))
                removed_chunks = len(chunk_files)
                shutil.rmtree(doc_chunk_dir)
                logger.info(f"✅ 删除分块目录: {doc_chunk_dir}")
            
            # 2. 从ChromaDB删除向量数据
            removed_vectors = self._remove_document_vectors(document_name, collection_id)
            
            return OperationResult(
                success=True,
                message=f"成功删除文档 '{document_name}'",
                details={
                    "removed_chunks": removed_chunks,
                    "removed_vectors": removed_vectors,
                    "document_name": document_name,
                    "collection_id": collection_id
                },
                affected_items=removed_chunks + removed_vectors
            )
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return OperationResult(
                success=False,
                message=f"删除文档 '{document_name}' 失败: {e}",
                details={"error": str(e)}
            )
    
    def _remove_document_vectors(self, document_name: str, collection_id: Optional[str] = None) -> int:
        """从ChromaDB删除文档向量"""
        removed_count = 0
        
        try:
            collections = self.chroma_client.list_collections()
            
            for collection in collections:
                if collection_id and collection.name != collection_id:
                    continue
                
                try:
                    # 获取所有数据，然后在客户端过滤
                    results = collection.get()
                    ids_to_delete = []

                    if results and results.get('ids') and results.get('metadatas'):
                        for i, metadata in enumerate(results['metadatas']):
                            if metadata and 'source' in metadata:
                                if document_name in metadata['source']:
                                    ids_to_delete.append(results['ids'][i])

                    if ids_to_delete:
                        collection.delete(ids=ids_to_delete)
                        removed_count += len(ids_to_delete)
                        logger.info(f"✅ 从集合 {collection.name} 删除 {len(ids_to_delete)} 个向量")

                except Exception as e:
                    logger.warning(f"从集合 {collection.name} 删除向量失败: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"删除文档向量失败: {e}")
        
        return removed_count
    
    def clean_all_data(self) -> OperationResult:
        """
        清空所有文档分块和向量数据
        
        Returns:
            操作结果
        """
        try:
            removed_chunks = 0
            removed_collections = 0
            
            # 1. 清空分块目录
            chunks_dir = Path(self.data_paths["chunks"])
            if chunks_dir.exists():
                for item in chunks_dir.iterdir():
                    if item.is_dir():
                        chunk_count = len(list(item.rglob("*.md")))
                        removed_chunks += chunk_count
                        shutil.rmtree(item)
                    elif item.is_file():
                        removed_chunks += 1
                        item.unlink()
                
                logger.info(f"✅ 清空分块目录: {chunks_dir}")
            
            # 2. 重置ChromaDB
            removed_collections = self._reset_chromadb()
            
            return OperationResult(
                success=True,
                message="成功清空所有文档数据",
                details={
                    "removed_chunks": removed_chunks,
                    "removed_collections": removed_collections
                },
                affected_items=removed_chunks + removed_collections
            )
            
        except Exception as e:
            logger.error(f"清空数据失败: {e}")
            return OperationResult(
                success=False,
                message=f"清空数据失败: {e}",
                details={"error": str(e)}
            )
    
    def _reset_chromadb(self) -> int:
        """重置ChromaDB数据库"""
        try:
            collections = self.chroma_client.list_collections()
            removed_count = len(collections)
            
            for collection in collections:
                self.chroma_client.delete_collection(collection.name)
                logger.info(f"✅ 删除集合: {collection.name}")
            
            return removed_count
        except Exception as e:
            logger.error(f"重置ChromaDB失败: {e}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            stats = {
                "collections": [],
                "total_documents": 0,
                "total_vectors": 0,
                "total_chunks": 0
            }
            
            # ChromaDB统计
            collections = self.chroma_client.list_collections()
            for collection in collections:
                collection_info = {
                    "name": collection.name,
                    "count": collection.count()
                }
                stats["collections"].append(collection_info)
                stats["total_vectors"] += collection_info["count"]
            
            # 分块文件统计
            chunks_dir = Path(self.data_paths["chunks"])
            if chunks_dir.exists():
                for doc_dir in chunks_dir.iterdir():
                    if doc_dir.is_dir():
                        stats["total_documents"] += 1
                        chunk_files = list(doc_dir.glob("*.md"))
                        stats["total_chunks"] += len(chunk_files)
            
            return stats
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            return {"error": str(e)}
