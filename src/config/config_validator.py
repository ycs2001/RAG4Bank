"""
配置文件验证和迁移工具
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigValidator:
    """配置文件验证器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict[str, Any]:
        """加载配置文件模式"""
        return {
            "required_sections": [
                "system", "data", "document_processing", 
                "embedding", "retrieval", "llm"
            ],
            "required_fields": {
                "system": ["name", "version", "environment"],
                "data": ["raw_docs_dir", "processed_docs_dir", "chroma_db_dir"],
                "embedding.model": ["name", "path"],
                "llm.primary": ["provider", "model"]
            },
            "field_types": {
                "system.version": str,
                "retrieval.top_k": int,
                "retrieval.similarity_threshold": float,
                "embedding.model.batch_size": int
            },
            "field_ranges": {
                "retrieval.top_k": (1, 1000),
                "retrieval.similarity_threshold": (0.0, 1.0),
                "embedding.model.batch_size": (1, 256)
            }
        }
    
    def validate_config(self, config_file: str) -> Dict[str, Any]:
        """
        验证配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            验证结果
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "metadata": {}
        }
        
        try:
            # 加载配置文件
            config_path = self.config_dir / config_file
            if not config_path.exists():
                result["valid"] = False
                result["errors"].append(f"配置文件不存在: {config_file}")
                return result
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                result["valid"] = False
                result["errors"].append("配置文件为空")
                return result
            
            # 验证必需章节
            self._validate_required_sections(config, result)
            
            # 验证必需字段
            self._validate_required_fields(config, result)
            
            # 验证字段类型
            self._validate_field_types(config, result)
            
            # 验证字段范围
            self._validate_field_ranges(config, result)
            
            # 验证路径存在性
            self._validate_paths(config, result)
            
            # 验证环境变量
            self._validate_environment_variables(config, result)
            
            # 生成建议
            self._generate_suggestions(config, result)
            
            # 收集元数据
            result["metadata"] = self._collect_metadata(config)
            
        except yaml.YAMLError as e:
            result["valid"] = False
            result["errors"].append(f"YAML格式错误: {e}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"验证过程出错: {e}")
        
        return result
    
    def _validate_required_sections(self, config: Dict[str, Any], result: Dict[str, Any]):
        """验证必需章节"""
        for section in self.schema["required_sections"]:
            if section not in config:
                result["errors"].append(f"缺少必需章节: {section}")
                result["valid"] = False
    
    def _validate_required_fields(self, config: Dict[str, Any], result: Dict[str, Any]):
        """验证必需字段"""
        for section, fields in self.schema["required_fields"].items():
            section_parts = section.split('.')
            current = config
            
            # 导航到指定章节
            for part in section_parts:
                if part not in current:
                    result["errors"].append(f"缺少章节: {section}")
                    result["valid"] = False
                    break
                current = current[part]
            else:
                # 验证字段
                for field in fields:
                    if field not in current:
                        result["errors"].append(f"缺少必需字段: {section}.{field}")
                        result["valid"] = False
    
    def _validate_field_types(self, config: Dict[str, Any], result: Dict[str, Any]):
        """验证字段类型"""
        for field_path, expected_type in self.schema["field_types"].items():
            value = self._get_nested_value(config, field_path)
            if value is not None and not isinstance(value, expected_type):
                result["warnings"].append(
                    f"字段类型不匹配: {field_path} 期望 {expected_type.__name__}, 实际 {type(value).__name__}"
                )
    
    def _validate_field_ranges(self, config: Dict[str, Any], result: Dict[str, Any]):
        """验证字段范围"""
        for field_path, (min_val, max_val) in self.schema["field_ranges"].items():
            value = self._get_nested_value(config, field_path)
            if value is not None:
                if not (min_val <= value <= max_val):
                    result["warnings"].append(
                        f"字段值超出范围: {field_path} = {value}, 有效范围 [{min_val}, {max_val}]"
                    )
    
    def _validate_paths(self, config: Dict[str, Any], result: Dict[str, Any]):
        """验证路径存在性"""
        path_fields = [
            "data.raw_docs_dir",
            "data.processed_docs_dir", 
            "data.chroma_db_dir",
            "embedding.model.path"
        ]
        
        for field_path in path_fields:
            path_value = self._get_nested_value(config, field_path)
            if path_value:
                path_obj = Path(path_value)
                if not path_obj.exists():
                    if "model.path" in field_path:
                        result["errors"].append(f"模型路径不存在: {path_value}")
                        result["valid"] = False
                    else:
                        result["warnings"].append(f"路径不存在: {path_value}")
    
    def _validate_environment_variables(self, config: Dict[str, Any], result: Dict[str, Any]):
        """验证环境变量"""
        env_var_fields = [
            "llm.primary.api_key",
            "llm.fallback.api_key"
        ]
        
        for field_path in env_var_fields:
            value = self._get_nested_value(config, field_path)
            if value and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                if not os.getenv(env_var):
                    result["warnings"].append(f"环境变量未设置: {env_var}")
    
    def _generate_suggestions(self, config: Dict[str, Any], result: Dict[str, Any]):
        """生成优化建议"""
        # 性能优化建议
        top_k = self._get_nested_value(config, "retrieval.top_k")
        if top_k and top_k > 100:
            result["suggestions"].append("建议将 retrieval.top_k 设置为 50-100 以提高性能")
        
        # 安全建议
        debug = self._get_nested_value(config, "system.debug")
        environment = self._get_nested_value(config, "system.environment")
        if debug and environment == "production":
            result["suggestions"].append("生产环境建议关闭 debug 模式")
    
    def _collect_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """收集配置元数据"""
        return {
            "config_version": self._get_nested_value(config, "config_metadata.version"),
            "system_version": self._get_nested_value(config, "system.version"),
            "environment": self._get_nested_value(config, "system.environment"),
            "sections_count": len(config),
            "has_dynamic_config": "dynamic_documents" in config,
            "has_prompt_config": "prompts" in config,
            "has_version_mapping": "version_mapping" in config
        }
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典的值"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current

class ConfigMigrator:
    """配置文件迁移工具"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
    
    def migrate_to_v2(self, source_file: str = "unified_config.yaml", 
                     target_file: str = "unified_config_v2.yaml") -> bool:
        """
        迁移配置文件到v2版本
        
        Args:
            source_file: 源配置文件
            target_file: 目标配置文件
            
        Returns:
            迁移是否成功
        """
        try:
            source_path = self.config_dir / source_file
            target_path = self.config_dir / target_file
            
            # 读取源配置
            if not source_path.exists():
                logger.error(f"源配置文件不存在: {source_file}")
                return False
            
            with open(source_path, 'r', encoding='utf-8') as f:
                source_config = yaml.safe_load(f)
            
            # 读取目标模板
            if not target_path.exists():
                logger.error(f"目标配置模板不存在: {target_file}")
                return False
            
            with open(target_path, 'r', encoding='utf-8') as f:
                target_config = yaml.safe_load(f)
            
            # 执行迁移
            migrated_config = self._perform_migration(source_config, target_config)
            
            # 保存迁移后的配置
            backup_path = self.config_dir / f"{source_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            source_path.rename(backup_path)
            
            with open(source_path, 'w', encoding='utf-8') as f:
                yaml.dump(migrated_config, f, ensure_ascii=False, indent=2, sort_keys=False)
            
            logger.info(f"✅ 配置迁移成功: {source_file} -> v2")
            logger.info(f"📦 原配置备份: {backup_path.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置迁移失败: {e}")
            return False
    
    def _perform_migration(self, source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        """执行配置迁移"""
        # 使用目标配置作为基础
        migrated = target.copy()
        
        # 迁移映射规则
        migration_rules = {
            "system": "system",
            "data": "data", 
            "document_processing": "document_processing",
            "embedding": "embedding",
            "retrieval": "retrieval",
            "reranker": "reranker",
            "llm": "llm"
        }
        
        # 执行字段迁移
        for source_key, target_key in migration_rules.items():
            if source_key in source and target_key in migrated:
                migrated[target_key] = self._merge_configs(
                    migrated[target_key], source[source_key]
                )
        
        # 更新元数据
        migrated["config_metadata"]["last_updated"] = datetime.now().isoformat()
        migrated["config_metadata"]["migration_required"] = False
        
        return migrated
    
    def _merge_configs(self, target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置字典"""
        result = target.copy()
        
        for key, value in source.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_configs(result[key], value)
                else:
                    result[key] = value  # 源配置优先
            else:
                result[key] = value
        
        return result
