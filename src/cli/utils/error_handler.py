"""
错误处理和用户反馈工具
"""

import logging
import traceback
from typing import Optional, Dict, Any
from enum import Enum

class ErrorLevel(Enum):
    """错误级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, verbose: bool = False):
        """
        初始化错误处理器
        
        Args:
            verbose: 是否显示详细错误信息
        """
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, 
                    error: Exception, 
                    context: str = "", 
                    level: ErrorLevel = ErrorLevel.ERROR,
                    suggestions: Optional[list] = None) -> Dict[str, Any]:
        """
        处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            level: 错误级别
            suggestions: 解决建议
            
        Returns:
            错误信息字典
        """
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "level": level.value,
            "suggestions": suggestions or []
        }
        
        # 记录日志
        log_message = f"{context}: {error}" if context else str(error)
        
        if level == ErrorLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == ErrorLevel.ERROR:
            self.logger.error(log_message)
        elif level == ErrorLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # 显示用户友好的错误信息
        self._display_error(error_info)
        
        # 详细错误信息
        if self.verbose:
            self._display_traceback(error)
        
        return error_info
    
    def _display_error(self, error_info: Dict[str, Any]):
        """显示错误信息"""
        level_icons = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }
        
        icon = level_icons.get(error_info["level"], "❓")
        print(f"\n{icon} {error_info['level']}: {error_info['message']}")
        
        if error_info["context"]:
            print(f"📍 上下文: {error_info['context']}")
        
        if error_info["suggestions"]:
            print("💡 建议解决方案:")
            for i, suggestion in enumerate(error_info["suggestions"], 1):
                print(f"   {i}. {suggestion}")
    
    def _display_traceback(self, error: Exception):
        """显示详细错误信息"""
        print("\n🔍 详细错误信息:")
        print("-" * 50)
        traceback.print_exc()
        print("-" * 50)
    
    @staticmethod
    def get_common_suggestions(error_type: str) -> list:
        """获取常见错误的解决建议"""
        suggestions_map = {
            "FileNotFoundError": [
                "检查文件路径是否正确",
                "确认文件是否存在",
                "检查文件权限"
            ],
            "PermissionError": [
                "检查文件/目录权限",
                "尝试使用管理员权限运行",
                "确认文件未被其他程序占用"
            ],
            "ImportError": [
                "检查是否安装了所需的Python包",
                "运行: pip install -r requirements.txt",
                "检查Python环境是否正确"
            ],
            "ConnectionError": [
                "检查网络连接",
                "确认服务是否正在运行",
                "检查防火墙设置"
            ],
            "ConfigValidationError": [
                "检查配置文件格式",
                "运行: categoryrag config validate",
                "使用: categoryrag init --wizard 重新配置"
            ]
        }
        
        return suggestions_map.get(error_type, [
            "查看日志文件获取更多信息",
            "使用 --verbose 参数获取详细错误信息",
            "联系技术支持"
        ])

class ProgressReporter:
    """进度报告器"""
    
    def __init__(self, total: int, description: str = "处理中"):
        """
        初始化进度报告器
        
        Args:
            total: 总数
            description: 描述
        """
        self.total = total
        self.current = 0
        self.description = description
    
    def update(self, increment: int = 1, message: str = ""):
        """
        更新进度
        
        Args:
            increment: 增量
            message: 消息
        """
        self.current += increment
        percentage = (self.current / self.total) * 100
        
        # 简单的进度条
        bar_length = 30
        filled_length = int(bar_length * self.current // self.total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        status_line = f"\r🔄 {self.description}: [{bar}] {percentage:.1f}% ({self.current}/{self.total})"
        if message:
            status_line += f" - {message}"
        
        print(status_line, end='', flush=True)
        
        if self.current >= self.total:
            print()  # 换行
    
    def finish(self, message: str = "完成"):
        """完成进度"""
        self.current = self.total
        self.update(0, message)

class UserFeedback:
    """用户反馈工具"""
    
    @staticmethod
    def success(message: str):
        """成功消息"""
        print(f"✅ {message}")
    
    @staticmethod
    def error(message: str):
        """错误消息"""
        print(f"❌ {message}")
    
    @staticmethod
    def warning(message: str):
        """警告消息"""
        print(f"⚠️ {message}")
    
    @staticmethod
    def info(message: str):
        """信息消息"""
        print(f"ℹ️ {message}")
    
    @staticmethod
    def step(step_num: int, total_steps: int, description: str):
        """步骤消息"""
        print(f"📋 步骤 {step_num}/{total_steps}: {description}")
    
    @staticmethod
    def section(title: str):
        """章节标题"""
        print(f"\n📊 {title}")
        print("=" * (len(title) + 4))
    
    @staticmethod
    def subsection(title: str):
        """子章节标题"""
        print(f"\n🔹 {title}")
        print("-" * (len(title) + 4))
