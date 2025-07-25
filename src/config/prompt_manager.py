"""
LLM Prompt 配置管理器
支持动态加载、变量替换和多语言
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class PromptManager:
    """Prompt配置管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_dir: str = "config", language: str = "zh-CN"):
        if hasattr(self, '_initialized'):
            return
            
        self.config_dir = Path(config_dir)
        self.prompts_file = self.config_dir / "prompts.yaml"
        self.language = language
        self.prompts = {}
        self.global_variables = {}
        self._last_modified = None
        
        self._load_prompts()
        self._initialized = True
    
    def _load_prompts(self):
        """加载Prompt配置"""
        try:
            if not self.prompts_file.exists():
                logger.warning(f"Prompt配置文件不存在: {self.prompts_file}")
                return
            
            # 检查文件修改时间
            current_modified = self.prompts_file.stat().st_mtime
            if self._last_modified and current_modified == self._last_modified:
                return  # 文件未修改，无需重新加载
            
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                logger.warning("Prompt配置文件为空")
                return
            
            self.prompts = config
            self.global_variables = config.get('global', {}).get('variables', {})
            self._last_modified = current_modified
            
            logger.info(f"✅ Prompt配置加载成功: {len(self._get_all_prompts())} 个模板")
            
        except Exception as e:
            logger.error(f"❌ 加载Prompt配置失败: {e}")
            raise
    
    def get_prompt(self, category: str, name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        获取Prompt模板并进行变量替换
        
        Args:
            category: 分类名称 (如 'qa_generation')
            name: 模板名称 (如 'main_qa')
            variables: 变量字典
            
        Returns:
            处理后的Prompt文本
        """
        # 自动重新加载（如果文件有更新）
        self._load_prompts()
        
        try:
            # 获取模板
            template_config = self.prompts.get(category, {}).get(name, {})
            if not template_config:
                raise ValueError(f"Prompt模板不存在: {category}.{name}")
            
            template = template_config.get('template', '')
            if not template:
                raise ValueError(f"Prompt模板内容为空: {category}.{name}")
            
            # 准备变量
            all_variables = self._prepare_variables(variables)
            
            # 变量替换
            processed_prompt = self._replace_variables(template, all_variables)
            
            logger.debug(f"✅ 获取Prompt: {category}.{name}")
            return processed_prompt
            
        except Exception as e:
            logger.error(f"❌ 获取Prompt失败: {category}.{name} - {e}")
            raise
    
    def _prepare_variables(self, user_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备所有变量"""
        # 基础变量
        base_variables = {
            'current_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_name': os.getenv('USER', 'User'),
            'system_name': 'CategoryRAG'
        }
        
        # 合并变量（优先级：用户变量 > 全局变量 > 基础变量）
        all_variables = {}
        all_variables.update(base_variables)
        all_variables.update(self.global_variables)
        if user_variables:
            all_variables.update(user_variables)
        
        return all_variables
    
    def _replace_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """替换模板中的变量"""
        try:
            # 使用format方法进行变量替换
            return template.format(**variables)
        except KeyError as e:
            missing_var = str(e).strip("'")
            logger.warning(f"⚠️ 模板变量缺失: {missing_var}")
            # 返回原模板，但标记缺失的变量
            return template.replace(f"{{{missing_var}}}", f"[缺失变量: {missing_var}]")
        except Exception as e:
            logger.error(f"❌ 变量替换失败: {e}")
            return template
    
    def get_qa_prompt(self, user_question: str, retrieved_content: str, 
                     multi_document: bool = False) -> str:
        """
        获取问答生成Prompt
        
        Args:
            user_question: 用户问题
            retrieved_content: 检索到的内容
            multi_document: 是否为多文档问答
            
        Returns:
            问答Prompt
        """
        prompt_name = "multi_document_qa" if multi_document else "main_qa"
        
        variables = {
            'user_question': user_question,
            'retrieved_content': retrieved_content
        }
        
        if multi_document:
            variables['document_sources'] = retrieved_content
        
        return self.get_prompt('qa_generation', prompt_name, variables)
    
    def get_toc_extraction_prompt(self, document_content: str) -> str:
        """获取TOC提取Prompt"""
        variables = {
            'document_content': document_content
        }
        return self.get_prompt('document_processing', 'toc_extraction', variables)
    
    def get_document_summary_prompt(self, document_name: str, document_type: str, 
                                   document_content: str) -> str:
        """获取文档摘要Prompt"""
        variables = {
            'document_name': document_name,
            'document_type': document_type,
            'document_content': document_content
        }
        return self.get_prompt('document_processing', 'document_summary', variables)
    
    def get_classification_prompt(self, user_query: str, available_collections: List[Dict]) -> str:
        """获取主题分类Prompt"""
        # 格式化集合信息
        collections_text = "\n".join([
            f"- {col.get('name', col.get('id'))}: {col.get('description', '')}"
            for col in available_collections
        ])
        
        variables = {
            'user_query': user_query,
            'available_collections': collections_text
        }
        return self.get_prompt('topic_classification', 'classify_query', variables)
    
    def get_keyword_extraction_prompt(self, document_name: str, document_type: str,
                                     document_content: str) -> str:
        """获取关键词提取Prompt"""
        variables = {
            'document_name': document_name,
            'document_type': document_type,
            'document_content': document_content
        }
        return self.get_prompt('keyword_extraction', 'extract_keywords', variables)
    
    def get_error_prompt(self, error_type: str, user_question: str = None) -> str:
        """获取错误处理Prompt"""
        if error_type == "no_relevant_docs":
            variables = {'user_question': user_question or ""}
            return self.get_prompt('error_handling', 'no_relevant_docs', variables)
        elif error_type == "system_error":
            variables = {'error_type': error_type}
            return self.get_prompt('error_handling', 'system_error', variables)
        else:
            return f"系统遇到未知错误: {error_type}"
    
    def _get_all_prompts(self) -> List[str]:
        """获取所有Prompt模板名称"""
        all_prompts = []
        for category, prompts in self.prompts.items():
            if category in ['global', 'languages', 'metadata']:
                continue
            for prompt_name in prompts.keys():
                all_prompts.append(f"{category}.{prompt_name}")
        return all_prompts
    
    def validate_prompts(self) -> Dict[str, Any]:
        """验证Prompt配置"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # 检查必需的分类
            required_categories = [
                'qa_generation', 'document_processing', 
                'topic_classification', 'error_handling'
            ]
            
            for category in required_categories:
                if category not in self.prompts:
                    validation_result['errors'].append(f"缺少必需分类: {category}")
                    validation_result['valid'] = False
            
            # 检查模板完整性
            total_prompts = 0
            for category, prompts in self.prompts.items():
                if category in ['global', 'languages', 'metadata']:
                    continue
                    
                for prompt_name, prompt_config in prompts.items():
                    total_prompts += 1
                    
                    # 检查模板内容
                    if 'template' not in prompt_config:
                        validation_result['errors'].append(
                            f"模板缺少内容: {category}.{prompt_name}"
                        )
                        validation_result['valid'] = False
                    
                    # 检查变量定义
                    template = prompt_config.get('template', '')
                    declared_vars = prompt_config.get('variables', [])
                    used_vars = self._extract_template_variables(template)
                    
                    # 检查未声明的变量
                    undeclared = set(used_vars) - set(declared_vars) - set(self.global_variables.keys())
                    if undeclared:
                        validation_result['warnings'].append(
                            f"模板 {category}.{prompt_name} 使用了未声明的变量: {list(undeclared)}"
                        )
            
            validation_result['statistics'] = {
                'total_prompts': total_prompts,
                'categories': len([k for k in self.prompts.keys() 
                                 if k not in ['global', 'languages', 'metadata']]),
                'global_variables': len(self.global_variables)
            }
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"验证过程出错: {e}")
        
        return validation_result
    
    def _extract_template_variables(self, template: str) -> List[str]:
        """从模板中提取变量名"""
        import re
        # 匹配 {variable_name} 格式的变量
        variables = re.findall(r'\{([^}]+)\}', template)
        return list(set(variables))
    
    def reload_prompts(self):
        """重新加载Prompt配置"""
        logger.info("🔄 重新加载Prompt配置...")
        self._last_modified = None  # 强制重新加载
        self._load_prompts()
    
    def get_prompt_info(self, category: str, name: str) -> Dict[str, Any]:
        """获取Prompt模板信息"""
        template_config = self.prompts.get(category, {}).get(name, {})
        if not template_config:
            return {}
        
        return {
            'category': category,
            'name': name,
            'variables': template_config.get('variables', []),
            'metadata': template_config.get('metadata', {}),
            'template_length': len(template_config.get('template', '')),
            'has_template': 'template' in template_config
        }
    
    def list_available_prompts(self) -> Dict[str, List[str]]:
        """列出所有可用的Prompt模板"""
        available = {}
        for category, prompts in self.prompts.items():
            if category in ['global', 'languages', 'metadata']:
                continue
            available[category] = list(prompts.keys())
        return available
