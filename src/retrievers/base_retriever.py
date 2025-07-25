"""
基础检索器接口：定义检索器的标准接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RetrievalResult:
    """检索结果类"""
    
    def __init__(self, 
                 content: str,
                 metadata: Dict[str, Any],
                 score: float,
                 distance: float = None):
        """
        初始化检索结果
        
        Args:
            content: 文档内容
            metadata: 元数据
            score: 相似度分数 (0-1, 越高越相似)
            distance: 距离分数 (越小越相似)
        """
        self.content = content
        self.metadata = metadata
        self.score = score
        self.distance = distance if distance is not None else (1 - score)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'content': self.content,
            'metadata': self.metadata,
            'score': self.score,
            'distance': self.distance
        }
    
    def __repr__(self):
        return f"RetrievalResult(score={self.score:.3f}, content_length={len(self.content)})"

class BaseRetriever(ABC):
    """基础检索器抽象类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化检索器
        
        Args:
            config: 检索器配置
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def initialize(self):
        """初始化检索器"""
        pass
    
    @abstractmethod
    def retrieve(self, 
                query: str, 
                top_k: int = 5,
                filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            
        Returns:
            检索结果列表
        """
        pass
    
    @abstractmethod
    def add_documents(self, 
                     documents: List[str],
                     metadatas: List[Dict[str, Any]],
                     ids: Optional[List[str]] = None):
        """
        添加文档到检索器
        
        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            ids: 文档ID列表
        """
        pass
    
    @abstractmethod
    def delete_documents(self, ids: List[str]):
        """
        删除文档
        
        Args:
            ids: 要删除的文档ID列表
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        获取检索器统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        try:
            stats = self.get_stats()
            return stats.get('status') == 'healthy'
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    def preprocess_query(self, query: str) -> str:
        """
        预处理查询文本
        
        Args:
            query: 原始查询
            
        Returns:
            处理后的查询
        """
        # 基础预处理：去除首尾空白
        query = query.strip()
        
        # 可以在子类中扩展更多预处理逻辑
        return query
    
    def postprocess_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        后处理检索结果
        
        Args:
            results: 原始检索结果
            
        Returns:
            处理后的检索结果
        """
        # 基础后处理：按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 可以在子类中扩展更多后处理逻辑
        return results
