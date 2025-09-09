"""DeepSeek LLM实现"""

import requests
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
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> LLMResponse:
        """生成文本"""

        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, max_tokens=max_tokens, temperature=temperature, **kwargs)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> LLMResponse:
        """对话生成"""

        start_time = time.time()

        try:
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "stream": False,
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
                timeout=self.timeout,
            )

            processing_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    text = result["choices"][0]["message"]["content"].strip()
                    text = self.postprocess_response(text)
                    usage = result.get("usage", {})

                    return LLMResponse(
                        text=text,
                        usage=usage,
                        metadata={
                            "model": self.model,
                            "status_code": response.status_code,
                        },
                        processing_time=processing_time,
                    )

                error_msg = f"API响应格式错误: {result}"
                self.logger.error(error_msg)
                return LLMResponse(
                    text="抱歉，API响应格式异常。",
                    metadata={"error": error_msg, "status_code": response.status_code},
                    processing_time=processing_time,
                )
            else:
                error_msg = (
                    f"API请求失败: {response.status_code}, {response.text}"
                )
                self.logger.error(error_msg)
                return LLMResponse(
                    text=f"抱歉，API请求失败（状态码: {response.status_code}）。",
                    metadata={"error": error_msg, "status_code": response.status_code},
                    processing_time=processing_time,
                )

        except requests.exceptions.RequestException as e:
            processing_time = time.time() - start_time
            error_msg = f"DeepSeek API请求失败: {e}"
            self.logger.error(error_msg)
            return LLMResponse(
                text="抱歉，API请求失败。",
                metadata={"error": error_msg},
                processing_time=processing_time,
            )
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"DeepSeek LLM调用失败: {e}"
            self.logger.error(error_msg)
            return LLMResponse(
                text=f"抱歉，生成回答时发生错误: {e}",
                metadata={"error": error_msg},
                processing_time=processing_time,
            )
    
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
