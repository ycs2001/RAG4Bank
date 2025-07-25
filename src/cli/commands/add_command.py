"""
文档添加命令
"""

import os
import sys
from pathlib import Path
from .base_command import BaseCommand

class AddCommand(BaseCommand):
    """文档添加命令"""
    
    def execute(self):
        """执行文档添加"""
        if self.args.interactive or not self.args.path:
            self._interactive_add()
        elif self.args.batch:
            self._batch_add()
        else:
            self._single_add()
    
    def _interactive_add(self):
        """交互式添加文档"""
        print("🎯 CategoryRAG 交互式文档添加")
        print("=" * 50)
        
        # 获取文档路径
        while True:
            file_path = self.get_input("请输入文档路径")
            if not file_path:
                print("❌ 路径不能为空")
                continue
            
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"❌ 文件不存在: {file_path}")
                continue
            
            # 检查文件格式
            supported_formats = self.config_manager.get_supported_formats()
            if file_path.suffix.lower() not in supported_formats:
                print(f"❌ 不支持的文件格式: {file_path.suffix}")
                print(f"💡 支持的格式: {', '.join(supported_formats)}")
                continue
            
            break
        
        # 获取集合配置
        print(f"\n📚 配置文档集合信息:")
        collection_id = self.get_input("集合ID (留空自动生成)")
        collection_name = self.get_input("集合名称", file_path.stem)
        collection_desc = self.get_input("集合描述", f"{file_path.stem}相关文档")
        keywords_input = self.get_input("关键词 (用逗号分隔)", file_path.stem)
        
        # 构建配置
        collection_config = {
            "collection_name": collection_name,
            "description": collection_desc,
            "keywords": [k.strip() for k in keywords_input.split(',') if k.strip()]
        }
        
        if collection_id:
            collection_config["collection_id"] = collection_id
        
        # 预览配置
        print(f"\n📋 配置预览:")
        print(f"   文档路径: {file_path}")
        print(f"   集合名称: {collection_name}")
        print(f"   集合描述: {collection_desc}")
        print(f"   关键词: {', '.join(collection_config['keywords'])}")
        
        if not self.confirm("确认添加文档", True):
            print("⚠️ 操作已取消")
            return
        
        # 执行添加
        self._execute_add(str(file_path), collection_config)
    
    def _single_add(self):
        """单个文档添加"""
        file_path = Path(self.args.path)

        # 验证文件
        if not file_path.exists():
            self.print_error(f"文件不存在: {file_path}")
            sys.exit(1)

        # 检查格式
        supported_formats = self.config_manager.get_supported_formats()
        if file_path.suffix.lower() not in supported_formats:
            self.print_error(f"不支持的文件格式: {file_path.suffix}")
            self.print_info(f"支持的格式: {', '.join(supported_formats)}")
            sys.exit(1)

        # 增量处理检查
        if self.args.incremental:
            if self._check_document_exists(file_path):
                if not self.args.force:
                    self.print_warning(f"文档 '{file_path.name}' 已存在")
                    if not self.confirm("是否覆盖现有文档", False):
                        print("⚠️ 操作已取消")
                        return

                # 删除现有文档
                self._remove_existing_document(file_path)

        # 构建配置
        collection_config = {
            "collection_name": self.args.collection or file_path.stem,
            "description": f"{file_path.stem}相关文档"
        }

        if self.args.keywords:
            collection_config["keywords"] = [k.strip() for k in self.args.keywords.split(',')]
        else:
            collection_config["keywords"] = [file_path.stem]

        # 预览模式
        if self.args.preview:
            print("📋 预览模式 - 不会实际执行")
            print(f"   文档路径: {file_path}")
            print(f"   集合名称: {collection_config['collection_name']}")
            print(f"   关键词: {', '.join(collection_config['keywords'])}")
            print(f"   增量模式: {'是' if self.args.incremental else '否'}")
            return

        # 执行添加
        self._execute_add(str(file_path), collection_config)
    
    def _batch_add(self):
        """批量添加文档"""
        directory = Path(self.args.path)
        
        if not directory.exists() or not directory.is_dir():
            self.print_error(f"目录不存在: {directory}")
            sys.exit(1)
        
        # 查找支持的文档
        supported_formats = self.config_manager.get_supported_formats()
        documents = []
        
        for ext in supported_formats:
            documents.extend(directory.rglob(f"*{ext}"))
        
        if not documents:
            self.print_warning(f"在目录 {directory} 中未找到支持的文档")
            return
        
        print(f"📁 找到 {len(documents)} 个文档:")
        for doc in documents[:10]:  # 只显示前10个
            print(f"   - {doc.name}")
        if len(documents) > 10:
            print(f"   ... 还有 {len(documents) - 10} 个文档")
        
        if not self.confirm(f"确认批量添加 {len(documents)} 个文档", True):
            print("⚠️ 操作已取消")
            return
        
        # 批量处理
        success_count = 0
        for i, doc_path in enumerate(documents, 1):
            print(f"\n📄 处理文档 {i}/{len(documents)}: {doc_path.name}")
            
            try:
                collection_config = {
                    "collection_name": f"{doc_path.stem}",
                    "description": f"{doc_path.stem}相关文档",
                    "keywords": [doc_path.stem]
                }
                
                self._execute_add(str(doc_path), collection_config, show_progress=False)
                success_count += 1
                self.print_success(f"添加成功: {doc_path.name}")
                
            except Exception as e:
                self.print_error(f"添加失败: {doc_path.name} - {e}")
        
        print(f"\n🎉 批量添加完成: {success_count}/{len(documents)} 个文档成功")
    
    def _execute_add(self, file_path: str, collection_config: dict, show_progress: bool = True):
        """执行文档添加"""
        try:
            if show_progress:
                print(f"\n🚀 开始添加文档: {Path(file_path).name}")

            # 使用文档工作流适配器
            from src.cli.adapters.document_workflow_adapter import DocumentWorkflowAdapter

            adapter = DocumentWorkflowAdapter(self.config_manager)

            # 验证文档
            validation_result = adapter.validate_document(file_path)
            if not validation_result["valid"]:
                for error in validation_result["errors"]:
                    self.print_error(error)
                raise Exception("文档验证失败")

            # 显示警告
            for warning in validation_result["warnings"]:
                self.print_warning(warning)

            # 执行添加
            result = adapter.add_document(file_path, collection_config)

            if result.status == "success":
                if show_progress:
                    print(f"\n📊 处理结果:")
                    print(f"   状态: ✅ 成功")
                    print(f"   文档: {result.doc_name}")
                    print(f"   分块数: {result.chunks_count}")
                    print(f"   集合ID: {result.collection_id}")
                    print(f"   处理时间: {result.processing_time:.2f}秒")

                    print(f"\n💡 下一步操作:")
                    print(f"   1. 运行数据库构建: categoryrag db rebuild")
                    print(f"   2. 重启系统: categoryrag start")

                return result
            else:
                raise Exception(result.error_message or "未知错误")

        except Exception as e:
            if show_progress:
                self.print_error(f"文档添加失败: {e}")
            raise

    def _check_document_exists(self, file_path: Path) -> bool:
        """检查文档是否已存在"""
        try:
            from src.core.document_manager import DocumentManager
            doc_manager = DocumentManager(self.config_manager)

            documents = doc_manager.list_documents()
            document_name = file_path.stem

            return any(doc.name == document_name for doc in documents)
        except Exception as e:
            self.print_warning(f"检查文档存在性失败: {e}")
            return False

    def _remove_existing_document(self, file_path: Path):
        """删除现有文档"""
        try:
            from src.core.document_manager import DocumentManager
            doc_manager = DocumentManager(self.config_manager)

            document_name = file_path.stem
            result = doc_manager.remove_document(document_name)

            if result.success:
                self.print_info(f"已删除现有文档: {document_name}")
            else:
                self.print_warning(f"删除现有文档失败: {result.message}")
        except Exception as e:
            self.print_warning(f"删除现有文档失败: {e}")
