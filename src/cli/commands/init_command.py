"""
系统初始化命令
"""

import os
from pathlib import Path
from .base_command import BaseCommand

class InitCommand(BaseCommand):
    """系统初始化命令"""
    
    def execute(self):
        """执行初始化"""
        print("🚀 CategoryRAG 系统初始化")
        print("=" * 50)
        
        if self.args.wizard:
            self._wizard_init()
        else:
            self._standard_init()
    
    def _standard_init(self):
        """标准初始化"""
        print("📁 创建必要的目录结构...")
        self._create_directories()
        
        print("\n⚙️ 检查配置文件...")
        self._check_config()
        
        print("\n🔍 验证依赖...")
        self._check_dependencies()
        
        print("\n✅ 初始化完成！")
        self._print_next_steps()
    
    def _wizard_init(self):
        """向导式初始化"""
        try:
            from src.cli.wizards.setup_wizard import SetupWizard

            # 1. 创建目录
            print("📁 创建目录结构...")
            self._create_directories()

            # 2. 运行设置向导
            wizard = SetupWizard()
            wizard_config = wizard.run()

            if wizard_config:
                # 3. 保存配置
                self._save_wizard_config(wizard_config)
                print("\n🎉 向导配置完成！")
                self._print_next_steps()
            else:
                print("⚠️ 向导配置已取消")

        except ImportError as e:
            self.print_error(f"向导模块加载失败: {e}")
            print("💡 回退到标准初始化模式")
            self._standard_init()
    
    def _create_directories(self):
        """创建目录结构"""
        data_paths = self.get_data_paths()
        
        for name, path in data_paths.items():
            path_obj = Path(path)
            if not path_obj.exists():
                path_obj.mkdir(parents=True, exist_ok=True)
                self.print_success(f"创建目录: {path}")
            else:
                self.print_info(f"目录已存在: {path}")
        
        # 创建日志目录
        logs_dir = Path("logs")
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
            self.print_success("创建日志目录: logs")
    
    def _check_config(self):
        """检查配置文件"""
        try:
            self.config_manager.validate_config()
            self.print_success("配置文件验证通过")
        except Exception as e:
            self.print_warning(f"配置验证失败: {e}")
            
            if self.confirm("是否创建默认配置文件"):
                self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置文件"""
        # 这里可以创建一个基础的配置文件
        self.print_info("创建默认配置文件功能待实现")
    
    def _check_dependencies(self):
        """检查依赖"""
        dependencies = [
            ("chromadb", "向量数据库"),
            ("pandas", "Excel处理"),
            ("markitdown", "文档转换"),
            ("sentence_transformers", "重排模型"),
            ("yaml", "配置文件解析")
        ]
        
        for package, description in dependencies:
            try:
                __import__(package)
                self.print_success(f"{description}: {package}")
            except ImportError:
                self.print_error(f"{description}: {package} (未安装)")
    
    def _configure_bge_model(self):
        """配置BGE模型"""
        current_path = self.config_manager.get("embedding.model.path")
        
        if current_path and Path(current_path).exists():
            print(f"✅ 当前BGE模型路径: {current_path}")
            if not self.confirm("是否重新配置BGE模型路径"):
                return
        
        while True:
            model_path = self.get_input("请输入BGE模型路径", current_path)
            
            if not model_path:
                self.print_warning("跳过BGE模型配置")
                break
            
            if Path(model_path).exists():
                self.config_manager.set("embedding.model.path", model_path)
                self.print_success(f"BGE模型路径已设置: {model_path}")
                break
            else:
                self.print_error(f"路径不存在: {model_path}")
                if not self.confirm("是否重新输入"):
                    break
    
    def _configure_llm(self):
        """配置LLM服务"""
        print("配置LLM API密钥...")
        
        # DeepSeek配置
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            self.print_success("DeepSeek API密钥已配置")
        else:
            self.print_warning("DeepSeek API密钥未配置")
            print("💡 请设置环境变量: export DEEPSEEK_API_KEY=your_key")
        
        # Qwen配置
        qwen_key = os.getenv("QWEN_API_KEY")
        if qwen_key:
            self.print_success("Qwen API密钥已配置")
        else:
            self.print_warning("Qwen API密钥未配置")
            print("💡 请设置环境变量: export QWEN_API_KEY=your_key")
    
    def _save_wizard_config(self, wizard_config: dict):
        """保存向导配置"""
        try:
            import yaml
            config_path = Path(self.config_manager.config_dir) / "wizard_config.yaml"

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(wizard_config, f, allow_unicode=True, indent=2)

            self.print_success(f"向导配置已保存: {config_path}")
        except Exception as e:
            self.print_error(f"保存向导配置失败: {e}")

    def _finalize_config(self):
        """完成配置"""
        try:
            # 保存配置
            config_path = Path(self.config_manager.config_dir) / "user_config.yaml"
            self.config_manager.export_config(str(config_path))
            self.print_success(f"配置已保存: {config_path}")
        except Exception as e:
            self.print_error(f"保存配置失败: {e}")
    
    def _print_next_steps(self):
        """打印后续步骤"""
        print("\n📋 后续步骤:")
        print("1. 添加文档到知识库:")
        print("   categoryrag add document.pdf")
        print("   categoryrag add docs/ --batch")
        print()
        print("2. 构建向量数据库:")
        print("   python3 collection_database_builder.py")
        print()
        print("3. 启动系统:")
        print("   categoryrag start")
        print()
        print("4. 检查系统状态:")
        print("   categoryrag status")
        print()
        print("💡 使用 'categoryrag --help' 查看所有可用命令")
