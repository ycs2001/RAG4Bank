"""
基础组件类：统一依赖注入和配置管理
"""

import logging
from typing import Any, Optional
from ..config import ConfigManager

class BaseComponent:
    """所有核心组件的基类，统一配置管理和日志"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化基础组件
        
        Args:
            config_manager: 配置管理器实例
        """
        if not isinstance(config_manager, ConfigManager):
            raise TypeError("config_manager must be an instance of ConfigManager")
            
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 验证必要的配置项
        self._validate_config()
    
    def _validate_config(self):
        """验证组件所需的配置项，子类可重写"""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项的便捷方法
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config_manager.get(key, default)
    
    def get_config_section(self, section: str) -> dict:
        """
        获取配置段的便捷方法
        
        Args:
            section: 配置段名称
            
        Returns:
            配置段字典
        """
        return self.config_manager.get_section(section)
    
    def health_check(self) -> bool:
        """
        组件健康检查，子类可重写
        
        Returns:
            健康状态
        """
        return True
