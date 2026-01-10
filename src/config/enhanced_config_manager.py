"""
增强的配置管理器
支持统一配置、配置验证等功能
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# 尝试导入python-dotenv，如果没有安装则跳过
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConfigValidationError(Exception):
    """配置验证错误"""
    message: str
    path: str
    value: Any = None

class EnhancedConfigManager:
    """增强的配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config = {}

        # 尝试加载.env文件
        self._load_dotenv()

        self._load_config()

    def _load_dotenv(self):
        """加载.env文件"""
        if DOTENV_AVAILABLE:
            env_file = Path('.env')
            if env_file.exists():
                load_dotenv(env_file)
                logger.info("✅ 加载.env文件")
            else:
                logger.debug("📄 .env文件不存在")
        else:
            logger.debug("📦 python-dotenv未安装，跳过.env文件加载")

    def _load_config(self):
        """加载配置文件"""
        try:
            # 加载统一配置文件
            unified_config_path = self.config_dir / "unified_config.yaml"
            if unified_config_path.exists():
                with open(unified_config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"✅ 加载配置文件: {unified_config_path}")
            else:
                raise FileNotFoundError(f"未找到配置文件: {unified_config_path}")

            # 处理环境变量
            self._process_env_variables()

            # 验证配置
            self.validate_config()

            logger.info(f"✅ 配置加载完成")

        except Exception as e:
            logger.error(f"❌ 配置加载失败: {e}")
            raise
    
    def _process_env_variables(self):
        """处理环境变量"""
        import os

        def process_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env_value = os.getenv(env_var)
                if env_value is not None:
                    logger.debug(f"✅ 环境变量替换: {value} -> {env_value[:10]}...")
                    return env_value
                else:
                    logger.warning(f"⚠️ 环境变量未设置: {env_var}")
                    return value
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            return value

        self.config = process_value(self.config)
        logger.info("✅ 环境变量处理完成")
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        获取配置值，支持嵌套路径
        
        Args:
            path: 配置路径，如 "llm.primary.model"
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, path: str, value: Any):
        """
        设置配置值
        
        Args:
            path: 配置路径
            value: 配置值
        """
        keys = path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def validate_config(self):
        """验证配置"""
        errors = []
        
        # 验证必需的配置项
        required_configs = [
            "system.name",
            "system.version",
            "embedding.model.path",
            "llm.primary.provider",
            "data.chroma_db_dir"
        ]
        
        for config_path in required_configs:
            if self.get(config_path) is None:
                errors.append(f"缺少必需配置: {config_path}")
        
        # 验证文件路径
        path_configs = [
            ("embedding.model.path", "BGE模型路径", False),  # 不是必需的
            ("data.chroma_db_dir", "ChromaDB数据库目录", True),
            ("data.raw_docs_dir", "原始文档目录", True),
            ("data.processed_docs_dir", "处理后文档目录", True)
        ]

        for config_path, description, required in path_configs:
            path_value = self.get(config_path)
            if path_value and not Path(path_value).exists():
                # 对于目录，尝试创建
                if "dir" in config_path:
                    try:
                        Path(path_value).mkdir(parents=True, exist_ok=True)
                        logger.info(f"✅ 创建目录: {path_value}")
                    except Exception as e:
                        if required:
                            errors.append(f"{description}创建失败: {path_value} ({e})")
                        else:
                            logger.warning(f"⚠️ {description}创建失败: {path_value} ({e})")
                else:
                    # 对于文件路径，如果不是必需的，只给出警告
                    if required:
                        errors.append(f"{description}不存在: {path_value}")
                    else:
                        logger.warning(f"⚠️ {description}不存在: {path_value}")
        
        # 验证数值范围
        numeric_configs = [
            ("retrieval.top_k", 1, 1000),
            ("retrieval.similarity_threshold", 0.0, 1.0),
            ("document_processing.text_chunking.chunk_size", 100, 10000),
            ("performance.max_workers", 1, 32)
        ]
        
        for config_path, min_val, max_val in numeric_configs:
            value = self.get(config_path)
            if value is not None:
                if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                    errors.append(f"配置值超出范围: {config_path}={value} (应在{min_val}-{max_val}之间)")
        
        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            raise ConfigValidationError(error_msg, "validation", errors)
        
        logger.info("✅ 配置验证通过")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "name": self.get("system.name", "CategoryRAG"),
            "version": self.get("system.version", "2.0"),
            "config_dir": str(self.config_dir),
            "log_level": self.get("system.log_level", "INFO")
        }
    
    def get_data_paths(self) -> Dict[str, str]:
        """获取数据路径配置"""
        return {
            "raw_docs": self.get("data.raw_docs_dir", "data/raw_docs"),
            "processed_docs": self.get("data.processed_docs_dir", "data/processed_docs"),
            "chunks": self.get("data.chunks_dir", "data/processed_docs/chunks"),
            "toc": self.get("data.toc_dir", "data/toc"),
            "chroma_db": self.get("data.chroma_db_dir", "data/chroma_db")
        }
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文档格式"""
        return self.get("document_processing.supported_formats", [".pdf", ".docx", ".doc", ".xlsx", ".xls"])
    
    def get_collections_config(self) -> Dict[str, Any]:
        """获取集合配置"""
        return self.get("collections", {})
    
    def get_topic_keywords(self) -> Dict[str, List[str]]:
        """获取主题关键词映射"""
        return self.get("topic_classification.keyword_mapping", {})
    
    def reload_config(self):
        """重新加载配置"""
        logger.info("🔄 重新加载配置...")
        self._load_config()
    
    def export_config(self, output_path: str):
        """导出当前配置"""
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, indent=2)
        logger.info(f"✅ 配置已导出到: {output_path}")
    
    def get_health_check_config(self) -> Dict[str, Any]:
        """获取健康检查配置"""
        return {
            "enabled": self.get("monitoring.health_check.enabled", True),
            "interval": self.get("monitoring.health_check.interval", 300),
            "endpoints": self.get("monitoring.health_check.endpoints", ["llm", "embedding", "database"])
        }
