"""
系统状态检查命令
"""

import json
import os
import requests
from pathlib import Path
from .base_command import BaseCommand

class StatusCommand(BaseCommand):
    """系统状态检查命令"""
    
    def execute(self):
        """执行状态检查"""
        print("🔍 CategoryRAG 系统状态检查")
        print("=" * 50)
        
        if self.args.json:
            status_data = self._get_status_data()
            print(json.dumps(status_data, indent=2, ensure_ascii=False))
        else:
            self._print_status()
    
    def _print_status(self):
        """打印状态信息"""
        # 系统基本信息
        system_info = self.get_system_info()
        print(f"📊 系统信息:")
        print(f"   名称: {system_info['name']}")
        print(f"   版本: {system_info['version']}")
        print(f"   环境: {system_info['environment']}")
        print(f"   配置目录: {system_info['config_dir']}")
        print()
        
        # 配置状态
        print("⚙️ 配置状态:")
        try:
            self.config_manager.validate_config()
            self.print_status_item("配置验证", True, "所有配置项正常")
        except Exception as e:
            self.print_status_item("配置验证", False, str(e))
        print()
        
        # 数据目录状态
        print("📁 数据目录状态:")
        data_paths = self.get_data_paths()
        for name, path in data_paths.items():
            path_obj = Path(path)
            exists = path_obj.exists()
            if exists and path_obj.is_dir():
                file_count = len(list(path_obj.rglob("*"))) if path_obj.exists() else 0
                details = f"{path} ({file_count} 个文件)"
            else:
                details = f"{path} (不存在)"
            self.print_status_item(name, exists, details)
        print()
        
        # 模型状态
        print("🤖 模型状态:")
        self._check_models()
        print()
        
        # 服务状态
        print("🔧 服务状态:")
        self._check_services()
        print()
        
        # 集合状态
        print("📚 集合状态:")
        self._check_collections()
        print()
        
        if self.args.detailed:
            # 详细信息
            print("📋 详细信息:")
            self._print_detailed_info()
    
    def _check_models(self):
        """检查模型状态"""
        # 检查BGE模型
        bge_path = self.config_manager.get("embedding.model.path")
        if bge_path:
            bge_exists = Path(bge_path).exists()
            self.print_status_item("BGE嵌入模型", bge_exists, bge_path)
        else:
            self.print_status_item("BGE嵌入模型", False, "未配置路径")
        
        # 检查重排模型
        reranker_enabled = self.config_manager.get("reranker.enabled", False)
        if reranker_enabled:
            model_name = self.config_manager.get("reranker.cross_encoder.model_name")
            self.print_status_item("Cross-Encoder重排模型", True, model_name)
        else:
            self.print_status_item("Cross-Encoder重排模型", False, "未启用")
    
    def _check_services(self):
        """检查服务状态"""
        # 检查GROBID服务
        grobid_url = self.config_manager.get("services.grobid.url", "http://localhost:8070")
        grobid_status = self._check_grobid_service(grobid_url)
        self.print_status_item("GROBID服务", grobid_status, grobid_url)
        
        # 检查LLM配置
        llm_provider = self.config_manager.get("llm.primary.provider")
        llm_api_key = self.config_manager.get("llm.primary.api_key")
        llm_configured = bool(llm_provider and llm_api_key and not llm_api_key.startswith("${"))
        details = f"{llm_provider}" if llm_configured else "API密钥未配置"
        self.print_status_item("LLM服务", llm_configured, details)
    
    def _check_grobid_service(self, url: str) -> bool:
        """检查GROBID服务状态"""
        try:
            response = requests.get(f"{url}/api/isalive", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_collections(self):
        """检查集合状态"""
        try:
            # 检查ChromaDB
            chroma_db_path = self.config_manager.get("data.chroma_db_dir")
            if chroma_db_path and Path(chroma_db_path).exists():
                try:
                    import chromadb
                    client = chromadb.PersistentClient(path=chroma_db_path)
                    collections = client.list_collections()
                    
                    if collections:
                        for collection in collections:
                            count = collection.count()
                            self.print_status_item(
                                f"集合: {collection.name}", 
                                True, 
                                f"{count} 个文档"
                            )
                    else:
                        self.print_status_item("ChromaDB集合", False, "无集合")
                except Exception as e:
                    self.print_status_item("ChromaDB", False, f"访问失败: {e}")
            else:
                self.print_status_item("ChromaDB", False, "数据库目录不存在")
        except ImportError:
            self.print_status_item("ChromaDB", False, "chromadb未安装")
    
    def _print_detailed_info(self):
        """打印详细信息"""
        # 环境变量
        env_vars = ["DEEPSEEK_API_KEY", "QWEN_API_KEY", "OPENAI_API_KEY"]
        for var in env_vars:
            value = os.getenv(var)
            if value:
                masked_value = value[:8] + "..." if len(value) > 8 else "***"
                self.print_status_item(f"环境变量 {var}", True, masked_value)
            else:
                self.print_status_item(f"环境变量 {var}", False, "未设置")
        
        print()
        
        # 配置摘要
        print("📋 配置摘要:")
        config_items = [
            ("检索策略", "retrieval.strategy"),
            ("检索数量", "retrieval.top_k"),
            ("相似度阈值", "retrieval.similarity_threshold"),
            ("重排器", "reranker.enabled"),
            ("文本分块大小", "document_processing.text_chunking.chunk_size"),
            ("Excel分块行数", "document_processing.excel_chunking.rows_per_chunk")
        ]
        
        for name, path in config_items:
            value = self.config_manager.get(path)
            print(f"   {name}: {value}")
    
    def _get_status_data(self) -> dict:
        """获取状态数据（JSON格式）"""
        system_info = self.get_system_info()
        data_paths = self.get_data_paths()
        
        # 检查各种状态
        config_valid = True
        try:
            self.config_manager.validate_config()
        except:
            config_valid = False
        
        # 检查数据目录
        directories = {}
        for name, path in data_paths.items():
            path_obj = Path(path)
            directories[name] = {
                "path": path,
                "exists": path_obj.exists(),
                "file_count": len(list(path_obj.rglob("*"))) if path_obj.exists() else 0
            }
        
        # 检查模型
        models = {
            "bge": {
                "path": self.config_manager.get("embedding.model.path"),
                "exists": Path(self.config_manager.get("embedding.model.path", "")).exists()
            },
            "reranker": {
                "enabled": self.config_manager.get("reranker.enabled", False),
                "model": self.config_manager.get("reranker.cross_encoder.model_name")
            }
        }
        
        # 检查服务
        grobid_url = self.config_manager.get("services.grobid.url", "http://localhost:8070")
        services = {
            "grobid": {
                "url": grobid_url,
                "available": self._check_grobid_service(grobid_url)
            },
            "llm": {
                "provider": self.config_manager.get("llm.primary.provider"),
                "configured": bool(self.config_manager.get("llm.primary.api_key"))
            }
        }
        
        # 检查集合
        collections = {}
        try:
            chroma_db_path = self.config_manager.get("data.chroma_db_dir")
            if chroma_db_path and Path(chroma_db_path).exists():
                import chromadb
                client = chromadb.PersistentClient(path=chroma_db_path)
                for collection in client.list_collections():
                    collections[collection.name] = {
                        "count": collection.count()
                    }
        except:
            pass
        
        return {
            "system": system_info,
            "config": {
                "valid": config_valid
            },
            "directories": directories,
            "models": models,
            "services": services,
            "collections": collections,
            "timestamp": str(Path().cwd())
        }
