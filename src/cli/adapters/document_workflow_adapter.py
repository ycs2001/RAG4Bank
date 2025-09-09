"""
文档工作流适配器
用于将新的CLI系统与现有的文档处理工作流集成
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DocumentAddResult:
    """文档添加结果"""
    status: str  # success, error
    doc_name: str
    collection_id: str
    chunks_count: int
    processing_time: float
    error_message: Optional[str] = None

class DocumentWorkflowAdapter:
    """文档工作流适配器"""
    
    def __init__(self, config_manager):
        """
        初始化适配器
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager
    
    def add_document(self, file_path: str, collection_config: Dict[str, Any]) -> DocumentAddResult:
        """
        添加文档到知识库
        
        Args:
            file_path: 文档路径
            collection_config: 集合配置
            
        Returns:
            文档添加结果
        """
        start_time = time.time()
        
        try:
            # 验证文件
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 检查文件格式
            supported_formats = self.config_manager.get_supported_formats()
            if file_path_obj.suffix.lower() not in supported_formats:
                raise ValueError(f"不支持的文件格式: {file_path_obj.suffix}")
            
            # 准备配置
            collection_name = collection_config.get("collection_name", file_path_obj.stem)
            collection_id = collection_config.get("collection_id", self._generate_collection_id(collection_name))
            keywords = collection_config.get("keywords", [file_path_obj.stem])
            description = collection_config.get("description", f"{file_path_obj.stem}相关文档")
            
            # 调用真实的文档处理工作流
            result = self._call_real_workflow(
                file_path=file_path,
                collection_id=collection_id,
                collection_name=collection_name,
                keywords=keywords,
                description=description
            )

            # 🔄 自动更新动态配置
            try:
                from ...config.dynamic_config_manager import DynamicConfigManager

                dynamic_manager = DynamicConfigManager()
                dynamic_collection_config = {
                    'collection_name': collection_name,
                    'collection_id': collection_id,
                    'description': description,
                    'keywords': keywords,
                    'priority': 1,
                    'type': 'document'
                }

                # 自动更新配置
                dynamic_manager.auto_update_on_document_add(file_path, dynamic_collection_config)

            except Exception as e:
                # 动态配置更新失败不影响主流程
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ 动态配置更新失败: {e}")

            processing_time = time.time() - start_time

            return DocumentAddResult(
                status="success",
                doc_name=file_path_obj.name,
                collection_id=collection_id,
                chunks_count=result["chunks_count"],
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return DocumentAddResult(
                status="error",
                doc_name=Path(file_path).name,
                collection_id="",
                chunks_count=0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _generate_collection_id(self, collection_name: str) -> str:
        """生成集合ID"""
        # 简单的ID生成逻辑
        import re
        collection_id = re.sub(r'[^a-zA-Z0-9_]', '_', collection_name.lower())
        collection_id = re.sub(r'_+', '_', collection_id).strip('_')
        return collection_id or "default_collection"
    
    def _process_document_mock(self, **kwargs) -> Dict[str, Any]:
        """
        模拟文档处理（临时实现）
        实际应该调用真实的文档处理工作流
        """
        file_path = kwargs["file_path"]
        file_path_obj = Path(file_path)
        
        # 模拟处理时间
        import time
        time.sleep(0.5)
        
        # 根据文件类型估算分块数
        if file_path_obj.suffix.lower() in ['.xlsx', '.xls']:
            # Excel文件估算
            try:
                import pandas as pd
                df = pd.read_excel(file_path)
                rows = len(df)
                chunks_count = max(1, rows // 40)  # 假设每40行一个分块
            except:
                chunks_count = 1
        else:
            # 其他文件类型估算
            try:
                file_size = file_path_obj.stat().st_size
                chunks_count = max(1, file_size // 2000)  # 假设每2KB一个分块
            except:
                chunks_count = 1
        
        return {
            "chunks_count": chunks_count,
            "status": "success"
        }
    
    def _call_real_workflow(self, **kwargs) -> Dict[str, Any]:
        """
        调用真实的文档处理工作流
        这个方法应该替换_process_document_mock
        """
        try:
            # 添加项目根目录到Python路径
            project_root = Path(__file__).resolve().parents[4]
            sys.path.append(str(project_root))
            
            # 导入真实的工作流
            from scripts.add_document_workflow import DocumentAddWorkflow
            
            # 创建工作流实例
            workflow = DocumentAddWorkflow()
            
            # 构建参数
            collection_config = {
                "collection_name": kwargs["collection_name"],
                "description": kwargs["description"],
                "keywords": kwargs["keywords"]
            }
            
            if "collection_id" in kwargs:
                collection_config["collection_id"] = kwargs["collection_id"]
            
            # 执行工作流
            result = workflow.add_document(kwargs["file_path"], collection_config)
            
            return {
                "chunks_count": result.chunks_count if hasattr(result, 'chunks_count') else 0,
                "status": result.status if hasattr(result, 'status') else "success"
            }
            
        except Exception as e:
            raise Exception(f"文档处理工作流执行失败: {e}")
    
    def validate_document(self, file_path: str) -> Dict[str, Any]:
        """
        验证文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            验证结果
        """
        file_path_obj = Path(file_path)
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        # 检查文件存在
        if not file_path_obj.exists():
            result["valid"] = False
            result["errors"].append(f"文件不存在: {file_path}")
            return result
        
        # 检查文件格式
        supported_formats = self.config_manager.get_supported_formats()
        if file_path_obj.suffix.lower() not in supported_formats:
            result["valid"] = False
            result["errors"].append(f"不支持的文件格式: {file_path_obj.suffix}")
            result["info"]["supported_formats"] = supported_formats
            return result
        
        # 检查文件大小
        file_size = file_path_obj.stat().st_size
        if file_size == 0:
            result["valid"] = False
            result["errors"].append("文件为空")
        elif file_size > 100 * 1024 * 1024:  # 100MB
            result["warnings"].append("文件较大，处理可能需要较长时间")
        
        # 添加文件信息
        result["info"].update({
            "file_name": file_path_obj.name,
            "file_size": file_size,
            "file_extension": file_path_obj.suffix,
            "estimated_chunks": self._estimate_chunks(file_path_obj)
        })
        
        return result
    
    def _estimate_chunks(self, file_path: Path) -> int:
        """估算分块数量"""
        try:
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                import pandas as pd
                df = pd.read_excel(file_path)
                return max(1, len(df) // 40)
            else:
                file_size = file_path.stat().st_size
                return max(1, file_size // 2000)
        except:
            return 1
