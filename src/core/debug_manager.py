"""
调试管理器：用于保存和管理检索调试信息
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from .base_component import BaseComponent
from ..config import ConfigManager
from ..retrievers.base_retriever import RetrievalResult

class DebugManager(BaseComponent):
    """调试管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化调试管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        super().__init__(config_manager)
        
        self.debug_config = self.get_config_section('debug')
        self.enabled = self.debug_config.get('enabled', False)
        self.output_dir = Path(self.debug_config.get('output_dir', './debug_retrieval'))
        self.save_raw_chunks = self.debug_config.get('save_raw_chunks', True)
        self.save_context = self.debug_config.get('save_context', True)
        self.save_llm_responses = self.debug_config.get('save_llm_responses', True)
        self.max_debug_files = self.debug_config.get('max_debug_files', 100)
        self.retention_days = self.debug_config.get('file_retention_days', 7)
        
        # 创建调试目录
        if self.enabled:
            self._setup_debug_directory()
            self._cleanup_old_files()
            self.logger.info(f"✅ 调试管理器已启用，输出目录: {self.output_dir}")
        else:
            self.logger.info("ℹ️ 调试管理器已禁用")
    
    def _setup_debug_directory(self):
        """设置调试目录"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建子目录
            (self.output_dir / 'retrieval').mkdir(exist_ok=True)
            (self.output_dir / 'context').mkdir(exist_ok=True)
            (self.output_dir / 'llm_responses').mkdir(exist_ok=True)
            
        except Exception as e:
            self.logger.error(f"创建调试目录失败: {e}")
            self.enabled = False
    
    def _cleanup_old_files(self):
        """清理过期的调试文件"""
        if not self.enabled:
            return
            
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for file_path in self.output_dir.rglob('*.json'):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    self.logger.debug(f"删除过期调试文件: {file_path}")
                    
        except Exception as e:
            self.logger.error(f"清理调试文件失败: {e}")
    
    def _generate_query_hash(self, query: str) -> str:
        """生成查询的哈希值"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()[:8]
    
    def save_retrieval_debug(self, 
                           query: str, 
                           retrieval_results: List[RetrievalResult],
                           collection_ids: List[str],
                           processing_time: float) -> Optional[str]:
        """
        保存检索调试信息
        
        Args:
            query: 用户查询
            retrieval_results: 检索结果
            collection_ids: 检索的集合ID列表
            processing_time: 处理时间
            
        Returns:
            调试文件路径
        """
        if not self.enabled or not self.save_raw_chunks:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_hash = self._generate_query_hash(query)
            filename = f"debug_retrieval_{timestamp}_{query_hash}.json"
            file_path = self.output_dir / 'retrieval' / filename
            
            debug_data = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'query_hash': query_hash,
                'collection_ids': collection_ids,
                'processing_time': processing_time,
                'total_results': len(retrieval_results),
                'results': []
            }
            
            # 保存每个检索结果的详细信息
            for i, result in enumerate(retrieval_results):
                result_data = {
                    'index': i,
                    'content': result.content,
                    'score': result.score,
                    'metadata': result.metadata,
                    'source_collection': result.metadata.get('source_collection', 'unknown'),
                    'document': result.metadata.get('document', 'unknown')
                }
                debug_data['results'].append(result_data)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"保存检索调试信息: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"保存检索调试信息失败: {e}")
            return None
    
    def save_context_debug(self, 
                          query: str, 
                          context: str, 
                          retrieval_count: int) -> Optional[str]:
        """
        保存上下文调试信息
        
        Args:
            query: 用户查询
            context: 构建的上下文
            retrieval_count: 检索文档数量
            
        Returns:
            调试文件路径
        """
        if not self.enabled or not self.save_context:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_hash = self._generate_query_hash(query)
            filename = f"debug_context_{timestamp}_{query_hash}.json"
            file_path = self.output_dir / 'context' / filename
            
            debug_data = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'query_hash': query_hash,
                'retrieval_count': retrieval_count,
                'context_length': len(context),
                'context': context
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"保存上下文调试信息: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"保存上下文调试信息失败: {e}")
            return None
    
    def save_llm_response_debug(self, 
                               query: str, 
                               response: str, 
                               classification_info: Dict[str, Any],
                               processing_time: float) -> Optional[str]:
        """
        保存LLM响应调试信息
        
        Args:
            query: 用户查询
            response: LLM响应
            classification_info: 分类信息
            processing_time: 处理时间
            
        Returns:
            调试文件路径
        """
        if not self.enabled or not self.save_llm_responses:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_hash = self._generate_query_hash(query)
            filename = f"debug_llm_{timestamp}_{query_hash}.json"
            file_path = self.output_dir / 'llm_responses' / filename
            
            debug_data = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'query_hash': query_hash,
                'response': response,
                'response_length': len(response),
                'classification_info': classification_info,
                'processing_time': processing_time
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"保存LLM响应调试信息: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"保存LLM响应调试信息失败: {e}")
            return None
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """获取调试信息摘要"""
        if not self.enabled:
            return {'enabled': False}
            
        try:
            summary = {
                'enabled': True,
                'output_dir': str(self.output_dir),
                'total_files': 0,
                'file_types': {
                    'retrieval': 0,
                    'context': 0,
                    'llm_responses': 0
                }
            }
            
            for subdir in ['retrieval', 'context', 'llm_responses']:
                subdir_path = self.output_dir / subdir
                if subdir_path.exists():
                    files = list(subdir_path.glob('*.json'))
                    summary['file_types'][subdir] = len(files)
                    summary['total_files'] += len(files)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取调试摘要失败: {e}")
            return {'enabled': True, 'error': str(e)}
