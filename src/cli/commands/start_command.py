"""
系统启动命令
"""

import sys
import subprocess
from pathlib import Path
from .base_command import BaseCommand

class StartCommand(BaseCommand):
    """系统启动命令"""
    
    def execute(self):
        """执行启动"""
        print("🚀 CategoryRAG 系统启动")
        print("=" * 50)
        
        if self.args.check_deps:
            print("🔍 检查依赖...")
            if not self._check_dependencies():
                if self.args.auto_fix:
                    self._auto_fix_dependencies()
                else:
                    self.print_error("依赖检查失败，请使用 --auto-fix 自动修复")
                    sys.exit(1)
        
        if self.args.web:
            self._start_web_interface()
        else:
            self._start_cli_interface()
    
    def _check_dependencies(self) -> bool:
        """检查依赖"""
        print("📦 检查Python包...")
        
        required_packages = [
            "chromadb",
            "pandas", 
            "markitdown",
            "sentence_transformers",
            "yaml"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                self.print_status_item(f"包: {package}", True)
            except ImportError:
                self.print_status_item(f"包: {package}", False, "未安装")
                missing_packages.append(package)
        
        print("\n🤖 检查模型...")
        bge_path = self.config_manager.get("embedding.model.path")
        bge_exists = bge_path and Path(bge_path).exists()
        self.print_status_item("BGE模型", bge_exists, bge_path or "未配置")
        
        print("\n🔧 检查服务...")
        # 检查GROBID服务
        grobid_url = self.config_manager.get("services.grobid.url", "http://localhost:8070")
        grobid_available = self._check_grobid_service(grobid_url)
        self.print_status_item("GROBID服务", grobid_available, grobid_url)
        
        # 检查LLM配置
        llm_api_key = self.config_manager.get("llm.primary.api_key")
        llm_configured = bool(llm_api_key and not llm_api_key.startswith("${"))
        self.print_status_item("LLM API密钥", llm_configured)
        
        return len(missing_packages) == 0 and bge_exists and llm_configured
    
    def _check_grobid_service(self, url: str) -> bool:
        """检查GROBID服务"""
        try:
            import requests
            response = requests.get(f"{url}/api/isalive", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _auto_fix_dependencies(self):
        """自动修复依赖"""
        print("🔧 自动修复依赖...")
        
        # 安装缺失的包
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
            self.print_success("Python包安装完成")
        except subprocess.CalledProcessError as e:
            self.print_error(f"包安装失败: {e}")
        
        # 启动GROBID服务
        if self.config_manager.get("services.grobid.auto_start", False):
            self._start_grobid_service()
    
    def _start_grobid_service(self):
        """启动GROBID服务"""
        print("🐳 启动GROBID Docker容器...")
        try:
            subprocess.run([
                "docker", "run", "--rm", "-d", "-p", "8070:8070", 
                "lfoppiano/grobid:0.8.0"
            ], check=True, capture_output=True)
            self.print_success("GROBID服务已启动")
        except subprocess.CalledProcessError:
            self.print_error("GROBID服务启动失败")
        except FileNotFoundError:
            self.print_error("Docker未安装，无法启动GROBID服务")
    
    def _start_web_interface(self):
        """启动Web界面"""
        self.print_info("Web界面功能待实现")
        print("💡 当前请使用CLI界面: categoryrag start")
    
    def _start_cli_interface(self):
        """启动CLI界面"""
        print("🎯 启动CategoryRAG CLI界面...")
        
        try:
            # 启动原有的start.py
            start_script = Path("start.py")
            if start_script.exists():
                if self.args.background:
                    self.print_info("后台模式功能待实现")
                    print("💡 当前请使用前台模式")
                
                print("🔄 启动交互式问答系统...")
                subprocess.run([sys.executable, str(start_script)])
            else:
                self.print_error("start.py文件不存在")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n⚠️ 系统已停止")
        except Exception as e:
            self.print_error(f"启动失败: {e}")
            sys.exit(1)
