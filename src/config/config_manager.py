"""
配置管理器：统一管理系统配置
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: Optional[str] = None):
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，默认为 config/config.yaml
        """
        if config_path is None:
            # 查找配置文件
            possible_paths = [
                "config/config.yaml",
                "config/config.yml",
                "../config/config.yaml",
                "../config/config.yml"
            ]
            
            config_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if config_path is None:
                raise FileNotFoundError("未找到配置文件，请确保 config/config.yaml 存在")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    self._config = yaml.safe_load(f)
                elif config_path.endswith('.json'):
                    self._config = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_path}")
            
            logger.info(f"✅ 配置文件加载成功: {config_path}")
            
            # 处理环境变量覆盖
            self._apply_env_overrides()
            
            # 验证配置
            self._validate_config()
            
        except Exception as e:
            logger.error(f"❌ 配置文件加载失败: {e}")
            raise
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        # 支持通过环境变量覆盖关键配置
        env_mappings = {
            'QWEN_API_KEY': ['llm', 'qwen', 'api_key'],
            'CHROMADB_PATH': ['retrieval', 'chromadb', 'db_path'],
            'BGE_MODEL_PATH': ['retrieval', 'embedding', 'model_path'],
            'LOG_LEVEL': ['system', 'log_level'],
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self._set_nested_value(config_path, env_value)
                logger.info(f"🔧 环境变量覆盖: {env_var} -> {'.'.join(config_path)}")
    
    def _set_nested_value(self, path: list, value: Any):
        """设置嵌套配置值"""
        current = self._config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _validate_config(self):
        """验证配置完整性"""
        required_sections = ['system', 'retrieval', 'llm', 'knowledge_base']
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"配置文件缺少必需的节: {section}")
        
        # 验证关键配置项
        if not self.get('llm.qwen.api_key'):
            logger.warning("⚠️ 未配置Qwen API密钥")
        
        if not os.path.exists(self.get('retrieval.embedding.model_path', '')):
            logger.warning("⚠️ BGE模型路径不存在")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键，如 'llm.qwen.api_key'
            default: 默认值
            
        Returns:
            配置值
        """
        if self._config is None:
            self.load_config()
        
        keys = key.split('.')
        current = self._config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        if self._config is None:
            self.load_config()
        
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置节
        
        Args:
            section: 节名称
            
        Returns:
            配置节字典
        """
        return self.get(section, {})
    
    def reload(self):
        """重新加载配置"""
        self._config = None
        self.load_config()
        logger.info("🔄 配置已重新加载")
    
    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        if self._config is None:
            self.load_config()
        return self._config.copy()
    
    def save_config(self, config_path: str):
        """
        保存配置到文件
        
        Args:
            config_path: 保存路径
        """
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
                elif config_path.endswith('.json'):
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_path}")
            
            logger.info(f"✅ 配置已保存到: {config_path}")
            
        except Exception as e:
            logger.error(f"❌ 配置保存失败: {e}")
            raise

# 全局配置实例
config = ConfigManager()
