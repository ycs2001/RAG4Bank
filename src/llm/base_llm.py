"""
基础LLM接口：定义LLM的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import time

logger = logging.getLogger(__name__)

class LLMResponse:
    """LLM响应类"""
    
    def __init__(self, 
                 text: str,
                 usage: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 processing_time: float = 0.0):
        """
        初始化LLM响应
        
        Args:
            text: 生成的文本
            usage: 使用统计信息
            metadata: 元数据
            processing_time: 处理时间
        """
        self.text = text
        self.usage = usage or {}
        self.metadata = metadata or {}
        self.processing_time = processing_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text': self.text,
            'usage': self.usage,
            'metadata': self.metadata,
            'processing_time': self.processing_time
        }
    
    def __repr__(self):
        return f"LLMResponse(text_length={len(self.text)}, time={self.processing_time:.2f}s)"

class BaseLLM(ABC):
    """基础LLM抽象类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM
        
        Args:
            config: LLM配置
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 通用参数
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', 0.8)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
    
    @abstractmethod
    def initialize(self):
        """初始化LLM"""
        pass
    
    @abstractmethod
    def generate(self, 
                prompt: str,
                max_tokens: Optional[int] = None,
                temperature: Optional[float] = None,
                **kwargs) -> LLMResponse:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        pass
    
    @abstractmethod
    def chat(self, 
            messages: List[Dict[str, str]],
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            **kwargs) -> LLMResponse:
        """
        对话生成
        
        Args:
            messages: 对话消息列表
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        pass
    
    def generate_with_retry(self, 
                           prompt: str,
                           max_tokens: Optional[int] = None,
                           temperature: Optional[float] = None,
                           **kwargs) -> LLMResponse:
        """
        带重试的生成
        
        Args:
            prompt: 输入提示
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return self.generate(prompt, max_tokens, temperature, **kwargs)
            except Exception as e:
                last_error = e
                self.logger.warning(f"生成失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        # 所有重试都失败了
        error_msg = f"生成失败，已重试 {self.max_retries} 次: {last_error}"
        self.logger.error(error_msg)
        
        return LLMResponse(
            text=f"抱歉，生成回答时发生错误: {last_error}",
            metadata={'error': str(last_error), 'retries': self.max_retries}
        )
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        try:
            # 简单的测试生成
            response = self.generate("测试", max_tokens=10, temperature=0.1)
            return len(response.text) > 0
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取LLM统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'model_name': self.__class__.__name__,
            'config': self.config,
            'status': 'healthy' if self.health_check() else 'unhealthy'
        }
    
    def preprocess_prompt(self, prompt: str) -> str:
        """
        预处理提示词
        
        Args:
            prompt: 原始提示词
            
        Returns:
            处理后的提示词
        """
        # 基础预处理：去除首尾空白
        prompt = prompt.strip()
        
        # 可以在子类中扩展更多预处理逻辑
        return prompt
    
    def postprocess_response(self, response: str) -> str:
        """
        后处理响应
        
        Args:
            response: 原始响应
            
        Returns:
            处理后的响应
        """
        # 基础后处理：去除首尾空白
        response = response.strip()
        
        # 可以在子类中扩展更多后处理逻辑
        return response
