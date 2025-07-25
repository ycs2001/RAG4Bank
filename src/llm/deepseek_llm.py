"""
DeepSeek LLM实现
"""

import requests
import json
from typing import Dict, Any, Optional, List
from .base_llm import BaseLLM


class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化DeepSeek LLM
        
        Args:
            config: LLM配置
        """
        super().__init__(config)
        
        # DeepSeek特定配置
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.deepseek.com')
        self.model = config.get('model', 'deepseek-chat')
        self.timeout = config.get('timeout', 120)
        
        # 请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.initialize()
    
    def initialize(self):
        """初始化DeepSeek LLM"""
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未配置")
        
        self.logger.info(f"✅ DeepSeek LLM初始化完成: {self.model}")
    
    def generate(self, 
                prompt: str,
                max_tokens: Optional[int] = None,
                temperature: Optional[float] = None,
                **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, max_tokens=max_tokens, temperature=temperature, **kwargs)
        return response.text
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             max_tokens: Optional[int] = None,
             temperature: Optional[float] = None,
             **kwargs) -> Any:
        """
        对话生成
        
        Args:
            messages: 消息列表
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            响应对象
        """
        try:
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "stream": False
            }
            
            # 添加其他参数
            for key, value in kwargs.items():
                if key not in data and value is not None:
                    data[key] = value
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 创建响应对象
            class ChatResponse:
                def __init__(self, response_data):
                    self.data = response_data
                    if 'choices' in response_data and len(response_data['choices']) > 0:
                        self.text = response_data['choices'][0]['message']['content']
                    else:
                        self.text = ""
                
                def __str__(self):
                    return self.text
            
            return ChatResponse(result)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"DeepSeek API请求失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"DeepSeek LLM调用失败: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "deepseek",
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not self.api_key:
            self.logger.error("DeepSeek API密钥未配置")
            return False
        
        if not self.base_url:
            self.logger.error("DeepSeek API基础URL未配置")
            return False
        
        return True
