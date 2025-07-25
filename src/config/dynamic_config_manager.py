"""
动态文档配置管理器
支持文档添加时自动更新配置
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamicConfigManager:
    """动态配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "unified_config.yaml"
        self.dynamic_config_file = self.config_dir / "dynamic_documents.yaml"
        
    def auto_update_on_document_add(self, 
                                   document_path: str,
                                   collection_config: Dict[str, Any]) -> bool:
        """
        文档添加时自动更新配置
        
        Args:
            document_path: 文档路径
            collection_config: 集合配置
            
        Returns:
            更新是否成功
        """
        try:
            # 1. 更新集合配置
            self._update_collections_config(collection_config)
            
            # 2. 更新关键词映射
            self._update_keyword_mapping(collection_config)
            
            # 3. 更新文档路径记录
            self._update_document_registry(document_path, collection_config)
            
            # 4. 保存动态配置
            self._save_dynamic_config()
            
            logger.info(f"✅ 动态配置更新成功: {Path(document_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 动态配置更新失败: {e}")
            return False
    
    def _update_collections_config(self, collection_config: Dict[str, Any]):
        """更新集合配置"""
        # 加载当前配置
        config = self._load_config()
        
        if 'collections' not in config:
            config['collections'] = {}
        
        collection_id = collection_config.get('collection_id') or \
                       self._generate_collection_id(collection_config['collection_name'])
        
        # 更新或添加集合配置
        config['collections'][collection_id] = {
            'name': collection_config['collection_name'],
            'description': collection_config.get('description', ''),
            'enabled': True,
            'priority': collection_config.get('priority', 1),
            'version': collection_config.get('version', 'latest'),
            'type': collection_config.get('type', 'document'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 保存配置
        self._save_config(config)
        logger.info(f"✅ 更新集合配置: {collection_id}")
    
    def _update_keyword_mapping(self, collection_config: Dict[str, Any]):
        """更新关键词映射"""
        config = self._load_config()
        
        if 'topic_classification' not in config:
            config['topic_classification'] = {}
        if 'keyword_mapping' not in config['topic_classification']:
            config['topic_classification']['keyword_mapping'] = {}
        
        collection_id = collection_config.get('collection_id') or \
                       self._generate_collection_id(collection_config['collection_name'])
        
        keywords = collection_config.get('keywords', [])
        if keywords:
            config['topic_classification']['keyword_mapping'][collection_id] = keywords
            
            # 保存配置
            self._save_config(config)
            logger.info(f"✅ 更新关键词映射: {collection_id} -> {keywords}")
    
    def _update_document_registry(self, document_path: str, collection_config: Dict[str, Any]):
        """更新文档注册表"""
        registry = self._load_dynamic_config()
        
        if 'document_registry' not in registry:
            registry['document_registry'] = {}
        
        doc_name = Path(document_path).stem
        collection_id = collection_config.get('collection_id') or \
                       self._generate_collection_id(collection_config['collection_name'])
        
        registry['document_registry'][doc_name] = {
            'original_path': document_path,
            'collection_id': collection_id,
            'collection_name': collection_config['collection_name'],
            'keywords': collection_config.get('keywords', []),
            'added_at': datetime.now().isoformat(),
            'file_size': self._get_file_size(document_path),
            'file_type': Path(document_path).suffix.lower()
        }
        
        self.dynamic_config = registry
        logger.info(f"✅ 更新文档注册表: {doc_name}")
    
    def _generate_collection_id(self, collection_name: str) -> str:
        """生成集合ID"""
        import re
        collection_id = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', collection_name.lower())
        collection_id = re.sub(r'_+', '_', collection_id).strip('_')
        return collection_id or "default_collection"
    
    def _get_file_size(self, file_path: str) -> int:
        """获取文件大小"""
        try:
            return Path(file_path).stat().st_size
        except:
            return 0
    
    def _load_config(self) -> Dict[str, Any]:
        """加载主配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_file}")
            return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, Any]):
        """保存主配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, indent=2, sort_keys=False)
            
            logger.info(f"✅ 配置文件已保存: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def _load_dynamic_config(self) -> Dict[str, Any]:
        """加载动态配置文件"""
        if not hasattr(self, 'dynamic_config'):
            try:
                with open(self.dynamic_config_file, 'r', encoding='utf-8') as f:
                    self.dynamic_config = yaml.safe_load(f) or {}
            except FileNotFoundError:
                self.dynamic_config = {
                    'version': '1.0',
                    'created_at': datetime.now().isoformat(),
                    'document_registry': {},
                    'auto_generated_collections': {},
                    'keyword_suggestions': {}
                }
        
        return self.dynamic_config
    
    def _save_dynamic_config(self):
        """保存动态配置文件"""
        try:
            # 更新时间戳
            self.dynamic_config['updated_at'] = datetime.now().isoformat()
            
            with open(self.dynamic_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.dynamic_config, f, allow_unicode=True, indent=2, sort_keys=False)
            
            logger.info(f"✅ 动态配置已保存: {self.dynamic_config_file}")
        except Exception as e:
            logger.error(f"保存动态配置失败: {e}")
            raise
    
    def auto_detect_collection_info(self, document_path: str) -> Dict[str, Any]:
        """
        自动检测文档的集合信息
        
        Args:
            document_path: 文档路径
            
        Returns:
            自动检测的集合配置
        """
        doc_path = Path(document_path)
        
        # 基于文件名和路径的智能检测
        collection_info = {
            'collection_name': doc_path.stem,
            'description': f"{doc_path.stem}相关文档",
            'keywords': [],
            'auto_detected': True
        }
        
        # 基于文件名的关键词提取
        filename_keywords = self._extract_keywords_from_filename(doc_path.name)
        collection_info['keywords'].extend(filename_keywords)
        
        # 基于目录结构的信息提取
        directory_info = self._extract_info_from_directory(doc_path.parent)
        if directory_info:
            collection_info.update(directory_info)
        
        # 基于文件类型的分类
        file_type_info = self._classify_by_file_type(doc_path.suffix)
        if file_type_info:
            collection_info.update(file_type_info)
        
        logger.info(f"🤖 自动检测集合信息: {collection_info}")
        return collection_info
    
    def _extract_keywords_from_filename(self, filename: str) -> List[str]:
        """从文件名提取关键词"""
        import re
        
        # 移除文件扩展名
        name = Path(filename).stem
        
        # 分割关键词（支持中文、英文、数字）
        keywords = []
        
        # 基于常见分隔符分割
        parts = re.split(r'[_\-\s\.\(\)\[\]]+', name)
        for part in parts:
            if len(part) >= 2:  # 过滤太短的词
                keywords.append(part)
        
        # 提取数字（可能是版本号、年份等）
        numbers = re.findall(r'\d{4}|\d{2,3}', name)
        keywords.extend(numbers)
        
        return list(set(keywords))  # 去重
    
    def _extract_info_from_directory(self, directory: Path) -> Optional[Dict[str, Any]]:
        """从目录结构提取信息"""
        dir_name = directory.name.lower()
        
        # 预定义的目录类型映射
        directory_mappings = {
            'reports': {'type': '报表', 'keywords': ['报表', '统计']},
            'docs': {'type': '文档', 'keywords': ['文档', '说明']},
            'manuals': {'type': '手册', 'keywords': ['手册', '指南']},
            'policies': {'type': '政策', 'keywords': ['政策', '规定']},
            'technical': {'type': '技术', 'keywords': ['技术', '开发']},
        }
        
        for pattern, info in directory_mappings.items():
            if pattern in dir_name:
                return {
                    'type': info['type'],
                    'keywords': info['keywords']
                }
        
        return None
    
    def _classify_by_file_type(self, file_extension: str) -> Optional[Dict[str, Any]]:
        """基于文件类型分类"""
        ext = file_extension.lower()
        
        type_mappings = {
            '.pdf': {'type': 'PDF文档', 'keywords': ['PDF', '文档']},
            '.docx': {'type': 'Word文档', 'keywords': ['Word', '文档']},
            '.doc': {'type': 'Word文档', 'keywords': ['Word', '文档']},
            '.xlsx': {'type': 'Excel表格', 'keywords': ['Excel', '表格', '数据']},
            '.xls': {'type': 'Excel表格', 'keywords': ['Excel', '表格', '数据']},
        }
        
        return type_mappings.get(ext)
    
    def get_collection_suggestions(self, document_path: str) -> List[Dict[str, Any]]:
        """获取集合建议"""
        # 自动检测
        auto_info = self.auto_detect_collection_info(document_path)
        
        # 基于现有集合的相似性建议
        existing_collections = self._get_existing_collections()
        similar_collections = self._find_similar_collections(auto_info, existing_collections)
        
        suggestions = [
            {
                'type': 'auto_detected',
                'confidence': 0.8,
                'config': auto_info
            }
        ]
        
        for collection in similar_collections:
            suggestions.append({
                'type': 'similar_existing',
                'confidence': collection['similarity'],
                'config': collection['config']
            })
        
        return suggestions
    
    def _get_existing_collections(self) -> List[Dict[str, Any]]:
        """获取现有集合"""
        config = self._load_config()
        collections = config.get('collections', {})
        
        return [
            {
                'id': cid,
                'config': cconfig
            }
            for cid, cconfig in collections.items()
        ]
    
    def _find_similar_collections(self, target_info: Dict[str, Any], 
                                 existing_collections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """查找相似的集合"""
        similar = []
        target_keywords = set(target_info.get('keywords', []))
        
        for collection in existing_collections:
            # 基于关键词相似性计算
            existing_keywords = set(collection['config'].get('keywords', []))
            
            if target_keywords and existing_keywords:
                intersection = target_keywords & existing_keywords
                union = target_keywords | existing_keywords
                similarity = len(intersection) / len(union) if union else 0
                
                if similarity > 0.3:  # 相似度阈值
                    similar.append({
                        'similarity': similarity,
                        'config': collection['config']
                    })
        
        # 按相似度排序
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:3]  # 返回前3个最相似的
