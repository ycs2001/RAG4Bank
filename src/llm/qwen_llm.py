"""
Qwen LLM实现
"""

import requests
import time
from typing import Dict, Any, Optional, List
import logging
from .base_llm import BaseLLM, LLMResponse

logger = logging.getLogger(__name__)

class QwenLLM(BaseLLM):
    """Qwen LLM实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Qwen LLM
        
        Args:
            config: LLM配置
        """
        super().__init__(config)
        
        # Qwen特定配置
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 
                                  'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        self.model = config.get('model', 'qwen-turbo')
        self.repetition_penalty = config.get('repetition_penalty', 1.1)
        self.timeout = config.get('timeout')
        
        # 请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.initialize()
    
    def initialize(self):
        """初始化Qwen LLM"""
        if not self.api_key:
            raise ValueError("Qwen API密钥未配置")
        
        self.logger.info(f"✅ Qwen LLM初始化完成: {self.model}")
    
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
        # 转换为对话格式
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, max_tokens, temperature, **kwargs)
    
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
        start_time = time.time()
        
        try:
            # 使用传入参数或默认值
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature or self.temperature
            
            # 构建请求payload
            payload = {
                "model": self.model,
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": self.top_p,
                    "repetition_penalty": self.repetition_penalty,
                    **kwargs
                }
            }
            
            # 发送请求
            request_kwargs = {
                'headers': self.headers,
                'json': payload
            }
            if self.timeout:
                request_kwargs['timeout'] = self.timeout
            
            response = requests.post(self.base_url, **request_kwargs)
            processing_time = time.time() - start_time
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                
                if "output" in result and "text" in result["output"]:
                    text = result["output"]["text"].strip()
                    text = self.postprocess_response(text)
                    
                    # 提取使用统计
                    usage = result.get("usage", {})
                    
                    return LLMResponse(
                        text=text,
                        usage=usage,
                        metadata={
                            'model': self.model,
                            'status_code': response.status_code,
                            'request_id': result.get('request_id')
                        },
                        processing_time=processing_time
                    )
                else:
                    error_msg = f"API响应格式错误: {result}"
                    self.logger.error(error_msg)
                    return LLMResponse(
                        text="抱歉，API响应格式异常。",
                        metadata={'error': error_msg, 'status_code': response.status_code},
                        processing_time=processing_time
                    )
            else:
                error_msg = f"API请求失败: {response.status_code}, {response.text}"
                self.logger.error(error_msg)
                return LLMResponse(
                    text=f"抱歉，API请求失败（状态码: {response.status_code}）。",
                    metadata={'error': error_msg, 'status_code': response.status_code},
                    processing_time=processing_time
                )
                
        except requests.exceptions.Timeout:
            processing_time = time.time() - start_time
            error_msg = "API请求超时"
            self.logger.error(error_msg)
            return LLMResponse(
                text="抱歉，请求超时，请稍后重试。",
                metadata={'error': error_msg, 'timeout': True},
                processing_time=processing_time
            )
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"生成回答失败: {str(e)}"
            self.logger.error(error_msg)
            return LLMResponse(
                text=f"抱歉，生成回答时发生错误: {str(e)}",
                metadata={'error': error_msg},
                processing_time=processing_time
            )
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        try:
            # 发送简单的测试请求
            response = self.generate("你好", max_tokens=10, temperature=0.1)
            return len(response.text) > 0 and 'error' not in response.metadata
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取LLM统计信息
        
        Returns:
            统计信息字典
        """
        base_stats = super().get_stats()
        base_stats.update({
            'provider': 'qwen',
            'model': self.model,
            'base_url': self.base_url,
            'api_key_configured': bool(self.api_key)
        })
        return base_stats
