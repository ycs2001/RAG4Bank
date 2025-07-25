"""核心模块 - 重构后的统一架构"""

from .unified_rag_system import UnifiedRAGSystem, RAGResponse

# 为了向后兼容，将UnifiedRAGSystem别名为RAGSystem
RAGSystem = UnifiedRAGSystem

__all__ = ['RAGSystem', 'UnifiedRAGSystem', 'RAGResponse']
