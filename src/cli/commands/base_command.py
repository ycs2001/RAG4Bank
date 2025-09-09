"""
CategoryRAG CLI Commands Base Class

This module provides the foundational base class for all CLI commands in the CategoryRAG system.
It implements common functionality including configuration management, user interaction,
error handling, and standardized output formatting.

The BaseCommand class serves as the parent class for all specific command implementations
(add, remove, clean, rebuild, db, etc.) and ensures consistent behavior across the CLI interface.

Key Features:
- Unified configuration management integration
- Standardized user interaction methods (confirmations, input prompts)
- Consistent error handling and logging
- Formatted output with color coding and icons
- Data path management and validation
- Common utility methods for file operations

Author: CategoryRAG Development Team
License: MIT
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from src.config.enhanced_config_manager import EnhancedConfigManager

class BaseCommand(ABC):
    """基础命令类"""
    
    def __init__(self, args):
        """
        初始化命令
        
        Args:
            args: 命令行参数
        """
        self.args = args
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化配置管理器
        try:
            self.config_manager = EnhancedConfigManager(
                config_dir=args.config,
                env=args.env
            )
        except Exception as e:
            self.logger.error(f"❌ 配置初始化失败: {e}")
            sys.exit(1)
    
    @abstractmethod
    def execute(self):
        """执行命令"""
        pass
    
    def print_success(self, message: str):
        """打印成功消息"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """打印错误消息"""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """打印警告消息"""
        print(f"⚠️ {message}")
    
    def print_info(self, message: str):
        """打印信息消息"""
        print(f"ℹ️ {message}")
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """
        确认对话框
        
        Args:
            message: 确认消息
            default: 默认值
            
        Returns:
            用户确认结果
        """
        suffix = " [Y/n]" if default else " [y/N]"
        response = input(f"❓ {message}{suffix}: ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', '是', 'true', '1']
    
    def get_input(self, prompt: str, default: str = None) -> str:
        """
        获取用户输入
        
        Args:
            prompt: 提示信息
            default: 默认值
            
        Returns:
            用户输入
        """
        if default:
            full_prompt = f"📝 {prompt} [{default}]: "
        else:
            full_prompt = f"📝 {prompt}: "
        
        response = input(full_prompt).strip()
        return response if response else (default or "")
    
    def print_table(self, headers: list, rows: list):
        """
        打印表格
        
        Args:
            headers: 表头
            rows: 数据行
        """
        if not rows:
            print("📋 无数据")
            return
        
        # 计算列宽
        col_widths = [len(str(header)) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 打印表头
        header_row = " | ".join(str(headers[i]).ljust(col_widths[i]) for i in range(len(headers)))
        print(header_row)
        print("-" * len(header_row))
        
        # 打印数据行
        for row in rows:
            data_row = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
            print(data_row)
    
    def print_status_item(self, name: str, status: bool, details: str = ""):
        """
        打印状态项
        
        Args:
            name: 项目名称
            status: 状态
            details: 详细信息
        """
        status_icon = "✅" if status else "❌"
        if details:
            print(f"  {status_icon} {name}: {details}")
        else:
            print(f"  {status_icon} {name}")
    
    def get_system_info(self) -> dict:
        """获取系统信息"""
        return self.config_manager.get_system_info()
    
    def get_data_paths(self) -> dict:
        """获取数据路径"""
        return self.config_manager.get_data_paths()
