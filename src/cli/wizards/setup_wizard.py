"""
系统设置向导
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

class SetupWizard:
    """系统设置向导"""
    
    def __init__(self):
        """初始化向导"""
        self.config = {}
    
    def run(self) -> Dict[str, Any]:
        """运行设置向导"""
        print("🧙‍♂️ CategoryRAG 设置向导")
        print("=" * 50)
        print("我将引导您完成CategoryRAG的初始配置\n")
        
        # 步骤1: 基本配置
        self._step_basic_config()
        
        # 步骤2: 模型配置
        self._step_model_config()
        
        # 步骤3: LLM配置
        self._step_llm_config()
        
        # 步骤4: 服务配置
        self._step_service_config()
        
        # 步骤5: 确认配置
        self._step_confirm_config()
        
        return self.config
    
    def _step_basic_config(self):
        """基本配置步骤"""
        print("📋 步骤 1/5: 基本配置")
        print("-" * 30)
        
        # 系统名称
        system_name = self._get_input(
            "系统名称", 
            "CategoryRAG",
            "用于标识您的CategoryRAG实例"
        )
        
        # 环境
        environment = self._get_choice(
            "运行环境",
            ["development", "production", "testing"],
            "development",
            "选择系统运行环境"
        )
        
        # 数据目录
        data_dir = self._get_input(
            "数据目录",
            "data",
            "存储文档和数据库的根目录"
        )
        
        self.config.update({
            "system": {
                "name": system_name,
                "environment": environment
            },
            "data_dir": data_dir
        })
        
        print("✅ 基本配置完成\n")
    
    def _step_model_config(self):
        """模型配置步骤"""
        print("📋 步骤 2/5: 模型配置")
        print("-" * 30)
        
        # BGE模型路径
        print("🤖 配置BGE嵌入模型:")
        print("BGE模型用于将文档转换为向量，是系统的核心组件")
        
        while True:
            bge_path = self._get_input(
                "BGE模型路径",
                "/Users/chongshenyang/Desktop/bge-large-zh-v1.5",
                "BGE模型的本地路径"
            )
            
            if not bge_path:
                if self._confirm("跳过BGE模型配置（稍后可手动配置）"):
                    break
                continue
            
            if Path(bge_path).exists():
                print("✅ BGE模型路径验证成功")
                break
            else:
                print("❌ 路径不存在")
                if not self._confirm("重新输入路径"):
                    bge_path = ""
                    break
        
        # 重排模型配置
        use_reranker = self._confirm(
            "启用Cross-Encoder重排模型",
            True,
            "重排模型可以提高检索精度，但会增加计算时间"
        )
        
        self.config.update({
            "embedding": {
                "model": {
                    "path": bge_path
                }
            },
            "reranker": {
                "enabled": use_reranker
            }
        })
        
        print("✅ 模型配置完成\n")
    
    def _step_llm_config(self):
        """LLM配置步骤"""
        print("📋 步骤 3/5: LLM配置")
        print("-" * 30)
        
        print("🔗 配置大语言模型:")
        print("LLM用于生成最终答案，需要API密钥")
        
        # 选择主要LLM提供商
        llm_provider = self._get_choice(
            "主要LLM提供商",
            ["deepseek", "qwen", "openai"],
            "deepseek",
            "选择您的主要LLM服务提供商"
        )
        
        # 检查API密钥
        api_key_env_map = {
            "deepseek": "DEEPSEEK_API_KEY",
            "qwen": "QWEN_API_KEY", 
            "openai": "OPENAI_API_KEY"
        }
        
        env_var = api_key_env_map[llm_provider]
        api_key = os.getenv(env_var)
        
        if api_key:
            print(f"✅ 检测到 {env_var} 环境变量")
        else:
            print(f"⚠️ 未检测到 {env_var} 环境变量")
            print(f"💡 请设置环境变量: export {env_var}=your_api_key")
        
        # 配置备用LLM
        use_fallback = self._confirm(
            "配置备用LLM",
            False,
            "备用LLM在主要LLM不可用时使用"
        )
        
        fallback_provider = None
        if use_fallback:
            available_providers = [p for p in ["deepseek", "qwen", "openai"] if p != llm_provider]
            fallback_provider = self._get_choice(
                "备用LLM提供商",
                available_providers,
                available_providers[0],
                "选择备用LLM提供商"
            )
        
        self.config.update({
            "llm": {
                "primary": {
                    "provider": llm_provider
                },
                "fallback": {
                    "provider": fallback_provider
                } if fallback_provider else None
            }
        })
        
        print("✅ LLM配置完成\n")
    
    def _step_service_config(self):
        """服务配置步骤"""
        print("📋 步骤 4/5: 服务配置")
        print("-" * 30)
        
        # GROBID服务配置
        print("🔧 配置GROBID服务:")
        print("GROBID用于解析PDF文档结构，提高文档处理质量")
        
        use_grobid = self._confirm(
            "启用GROBID服务",
            True,
            "建议启用以获得更好的PDF处理效果"
        )
        
        grobid_url = "http://localhost:8070"
        if use_grobid:
            grobid_url = self._get_input(
                "GROBID服务URL",
                "http://localhost:8070",
                "GROBID服务的访问地址"
            )
        
        # 性能配置
        print("\n⚡ 性能配置:")
        max_workers = self._get_number_input(
            "最大工作线程数",
            4,
            1, 16,
            "并行处理的线程数，建议设置为CPU核心数"
        )
        
        self.config.update({
            "services": {
                "grobid": {
                    "enabled": use_grobid,
                    "url": grobid_url
                }
            },
            "performance": {
                "max_workers": max_workers
            }
        })
        
        print("✅ 服务配置完成\n")
    
    def _step_confirm_config(self):
        """确认配置步骤"""
        print("📋 步骤 5/5: 确认配置")
        print("-" * 30)
        
        print("📋 配置摘要:")
        print(f"   系统名称: {self.config['system']['name']}")
        print(f"   运行环境: {self.config['system']['environment']}")
        print(f"   数据目录: {self.config['data_dir']}")
        print(f"   BGE模型: {self.config['embedding']['model']['path'] or '未配置'}")
        print(f"   重排模型: {'启用' if self.config['reranker']['enabled'] else '禁用'}")
        print(f"   主要LLM: {self.config['llm']['primary']['provider']}")
        print(f"   GROBID: {'启用' if self.config['services']['grobid']['enabled'] else '禁用'}")
        print(f"   工作线程: {self.config['performance']['max_workers']}")
        
        if not self._confirm("确认以上配置", True):
            print("⚠️ 配置已取消")
            return False
        
        print("✅ 配置确认完成\n")
        return True
    
    def _get_input(self, prompt: str, default: str = "", description: str = "") -> str:
        """获取用户输入"""
        if description:
            print(f"💡 {description}")
        
        if default:
            full_prompt = f"📝 {prompt} [{default}]: "
        else:
            full_prompt = f"📝 {prompt}: "
        
        response = input(full_prompt).strip()
        return response if response else default
    
    def _get_choice(self, prompt: str, choices: list, default: str, description: str = "") -> str:
        """获取用户选择"""
        if description:
            print(f"💡 {description}")
        
        print(f"📝 {prompt}:")
        for i, choice in enumerate(choices, 1):
            marker = " (默认)" if choice == default else ""
            print(f"   {i}. {choice}{marker}")
        
        while True:
            response = input("请选择 [1-{}]: ".format(len(choices))).strip()
            
            if not response:
                return default
            
            try:
                index = int(response) - 1
                if 0 <= index < len(choices):
                    return choices[index]
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入数字")
    
    def _get_number_input(self, prompt: str, default: int, min_val: int, max_val: int, description: str = "") -> int:
        """获取数字输入"""
        if description:
            print(f"💡 {description}")
        
        while True:
            response = input(f"📝 {prompt} [{default}] ({min_val}-{max_val}): ").strip()
            
            if not response:
                return default
            
            try:
                value = int(response)
                if min_val <= value <= max_val:
                    return value
                else:
                    print(f"❌ 数值必须在 {min_val}-{max_val} 之间")
            except ValueError:
                print("❌ 请输入有效数字")
    
    def _confirm(self, prompt: str, default: bool = False, description: str = "") -> bool:
        """确认对话框"""
        if description:
            print(f"💡 {description}")
        
        suffix = " [Y/n]" if default else " [y/N]"
        response = input(f"❓ {prompt}{suffix}: ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', '是', 'true', '1']
