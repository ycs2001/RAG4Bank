"""Cross-Encoder重排器实现"""

import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from .base_reranker import BaseReranker

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    CrossEncoder = None

class CrossEncoderReranker(BaseReranker):
    """Cross-Encoder重排器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Cross-Encoder重排器
        
        Args:
            config: 重排器配置
        """
        super().__init__(config)
        
        if not CROSS_ENCODER_AVAILABLE:
            self.logger.warning("sentence-transformers未安装，Cross-Encoder重排器不可用")
            self.enabled = False
            self.model = None
            return
            
        self.model_name = config.get('model_name', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.max_length = config.get('max_length', 512)
        self.device = config.get('device', 'cpu')
        self.top_k = config.get('top_k', 10)
        
        try:
            self.logger.info(f"正在加载Cross-Encoder模型: {self.model_name}")
            self.model = CrossEncoder(self.model_name, device=self.device)
            self.logger.info("Cross-Encoder模型加载成功")
            # 模型加载成功，启用重排器
            self.enabled = True
        except Exception as e:
            self.logger.error(f"加载Cross-Encoder模型失败: {e}")
            self.enabled = False
            self.model = None
    
    def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用Cross-Encoder重排文档
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            重排后的文档列表
        """
        if not self.enabled or not self.model or not documents:
            return documents
            
        try:
            # 准备输入对
            query_doc_pairs = []
            for doc in documents:
                content = doc.get('content', '')
                # 截断过长的文档
                if len(content) > self.max_length:
                    content = content[:self.max_length]
                query_doc_pairs.append([query, content])
            
            # 计算重排分数
            self.logger.debug(f"正在为{len(query_doc_pairs)}个文档计算重排分数")
            rerank_scores = self.model.predict(query_doc_pairs)
            
            # 将分数添加到文档中
            reranked_docs = []
            for i, doc in enumerate(documents):
                doc_copy = doc.copy()
                doc_copy['rerank_score'] = float(rerank_scores[i])
                doc_copy['original_score'] = doc.get('score', 0.0)
                reranked_docs.append(doc_copy)
            
            # 按重排分数排序
            reranked_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # 取top_k
            if self.top_k > 0:
                reranked_docs = reranked_docs[:self.top_k]
            
            self.logger.info(f"重排完成，从{len(documents)}个文档中选出{len(reranked_docs)}个")
            return reranked_docs
            
        except Exception as e:
            self.logger.error(f"重排过程出错: {e}")
            return documents
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'max_length': self.max_length,
            'top_k': self.top_k,
            'enabled': self.enabled,
            'available': CROSS_ENCODER_AVAILABLE
        }
