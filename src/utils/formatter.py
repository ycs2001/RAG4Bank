"""
响应格式化工具
"""

from typing import Dict, Any
from ..core.rag_system import RAGResponse

class ResponseFormatter:
    """响应格式化器"""
    
    @staticmethod
    def format_console_output(response: RAGResponse) -> str:
        """
        格式化控制台输出
        
        Args:
            response: RAG响应
            
        Returns:
            格式化的字符串
        """
        output = []
        output.append("=" * 80)
        output.append("🤖 智能问答系统回答")
        output.append("=" * 80)
        
        output.append(f"\n📝 问题: {response.query}")
        output.append(f"\n💡 回答:")
        output.append(response.answer)
        
        if response.sources:
            output.append(f"\n📚 参考来源 (共{response.retrieval_count}个文档):")
            for i, source in enumerate(response.sources, 1):
                output.append(f"  {i}. 📄 {source['document']} (相似度: {source['score']:.3f})")
                output.append(f"     内容预览: {source['content_preview']}")
        
        output.append(f"\n⏱️ 处理时间: {response.processing_time:.2f}秒")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    @staticmethod
    def format_json_output(response: RAGResponse) -> Dict[str, Any]:
        """
        格式化JSON输出
        
        Args:
            response: RAG响应
            
        Returns:
            JSON格式的字典
        """
        return response.to_dict()
    
    @staticmethod
    def format_simple_output(response: RAGResponse) -> str:
        """
        格式化简单输出（仅回答内容）
        
        Args:
            response: RAG响应
            
        Returns:
            简单格式的字符串
        """
        return response.answer
    
    @staticmethod
    def format_stats_output(stats: Dict[str, Any]) -> str:
        """
        格式化统计信息输出
        
        Args:
            stats: 统计信息
            
        Returns:
            格式化的统计信息字符串
        """
        output = []
        output.append("📊 系统统计信息")
        output.append("=" * 50)
        
        # 系统信息
        if 'system' in stats:
            system = stats['system']
            output.append(f"🎯 系统名称: {system.get('name', 'N/A')}")
            output.append(f"📦 版本: {system.get('version', 'N/A')}")
            output.append(f"💚 状态: {system.get('status', 'N/A')}")
        
        # 检索器信息
        if 'retriever' in stats:
            retriever = stats['retriever']
            output.append(f"\n🔍 检索器信息:")
            output.append(f"   📄 总文档数: {retriever.get('total_documents', 0)}")
            output.append(f"   💾 数据库路径: {retriever.get('db_path', 'N/A')}")
            output.append(f"   🤖 嵌入模型: {retriever.get('embedding_model', 'N/A')}")
        
        # LLM信息
        if 'llm' in stats:
            llm = stats['llm']
            output.append(f"\n🧠 LLM信息:")
            output.append(f"   🏷️ 提供商: {llm.get('provider', 'N/A')}")
            output.append(f"   🤖 模型: {llm.get('model', 'N/A')}")
            output.append(f"   💚 状态: {llm.get('status', 'N/A')}")
        
        # 配置信息
        if 'config' in stats:
            config = stats['config']
            output.append(f"\n⚙️ 配置信息:")
            output.append(f"   🔢 检索数量: {config.get('retrieval_top_k', 'N/A')}")
            output.append(f"   🌡️ 温度: {config.get('temperature', 'N/A')}")
        
        return "\n".join(output)
