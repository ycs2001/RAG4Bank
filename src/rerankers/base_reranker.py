"""重排器基类"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import logging

class BaseReranker(ABC):
    """重排器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化重排器
        
        Args:
            config: 重排器配置
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = config.get('enabled', False)
        
    @abstractmethod
    def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重排文档
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档包含content、score等字段
            
        Returns:
            重排后的文档列表
        """
        pass
    
    def is_enabled(self) -> bool:
        """检查重排器是否启用"""
        return self.enabled
