"""
RAG智能问答系统
"""

from .core import RAGSystem, UnifiedRAGSystem, RAGResponse
from .config import EnhancedConfigManager
from .retrievers import BaseRetriever, ChromaDBRetriever
from .llm import BaseLLM, QwenLLM, DeepSeekLLM

__version__ = "3.0.0"  # 重构后版本
__author__ = "CategoryRAG Team"

__all__ = [
    'RAGSystem',           # 向后兼容的别名
    'UnifiedRAGSystem',    # 新的统一实现
    'RAGResponse',
    'EnhancedConfigManager',
    'BaseRetriever',
    'ChromaDBRetriever',
    'BaseLLM',
    'QwenLLM',
    'DeepSeekLLM'
]
