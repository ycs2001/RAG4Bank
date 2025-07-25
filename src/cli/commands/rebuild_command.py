"""
全量重建命令
"""

import sys
import subprocess
from pathlib import Path
from .base_command import BaseCommand

class RebuildCommand(BaseCommand):
    """全量重建命令"""
    
    def execute(self):
        """执行全量重建"""
        print("🔄 CategoryRAG 全量重建")
        print("=" * 50)
        
        if self.args.from_scratch:
            self._rebuild_from_scratch()
        elif self.args.incremental:
            self._incremental_rebuild()
        elif self.args.vectors_only:
            self._rebuild_vectors_only()
        else:
            self._interactive_rebuild()
    
    def _interactive_rebuild(self):
        """交互式重建"""
        print("🎯 交互式全量重建")
        print("-" * 30)
        
        # 显示当前状态
        self._show_rebuild_status()
        
        print("\n📋 重建选项:")
        print("   1. 从原始文档完全重建 (推荐)")
        print("   2. 增量重建 (仅处理新文档)")
        print("   3. 仅重建向量数据库")
        print("   4. 取消操作")
        
        while True:
            try:
                choice = input("\n📝 请选择重建选项 [1-4]: ").strip()
                
                if choice == "1":
                    self._rebuild_from_scratch()
                    break
                elif choice == "2":
                    self._incremental_rebuild()
                    break
                elif choice == "3":
                    self._rebuild_vectors_only()
                    break
                elif choice == "4":
                    print("⚠️ 操作已取消")
                    return
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效数字")
    
    def _rebuild_from_scratch(self):
        """从原始文档完全重建"""
        print("\n🔄 从原始文档完全重建")
        print("-" * 30)
        
        # 检查原始文档
        raw_docs_dir = Path(self.get_data_paths()["raw_docs"])
        if not raw_docs_dir.exists():
            self.print_error(f"原始文档目录不存在: {raw_docs_dir}")
            return
        
        # 查找原始文档
        supported_formats = self.config_manager.get_supported_formats()
        raw_documents = []
        for ext in supported_formats:
            raw_documents.extend(raw_docs_dir.rglob(f"*{ext}"))
        
        if not raw_documents:
            self.print_warning(f"在 {raw_docs_dir} 中未找到支持的文档")
            print(f"💡 支持的格式: {', '.join(supported_formats)}")
            return
        
        print(f"📚 找到 {len(raw_documents)} 个原始文档:")
        for doc in raw_documents[:5]:  # 只显示前5个
            print(f"   - {doc.name}")
        if len(raw_documents) > 5:
            print(f"   ... 还有 {len(raw_documents) - 5} 个文档")
        
        # 确认重建
        if not self.args.force:
            print("\n⚠️ 警告: 此操作将:")
            print("   1. 清空所有现有分块和向量数据")
            print("   2. 重新处理所有原始文档")
            print("   3. 重新构建向量数据库")
            
            if not self.confirm("确认执行完全重建", False):
                print("⚠️ 操作已取消")
                return
        
        # 执行重建
        try:
            # 步骤1: 清理现有数据
            print("\n🧹 步骤 1/3: 清理现有数据...")
            self._clean_existing_data()
            
            # 步骤2: 重新处理文档
            print("\n📄 步骤 2/3: 重新处理文档...")
            success_count = self._process_all_documents(raw_documents)
            
            # 步骤3: 重建向量数据库
            print("\n🔢 步骤 3/3: 重建向量数据库...")
            self._rebuild_vector_database()
            
            print(f"\n🎉 完全重建完成!")
            print(f"📊 处理结果:")
            print(f"   成功处理: {success_count}/{len(raw_documents)} 个文档")
            print(f"\n💡 下一步操作:")
            print(f"   1. 检查系统状态: categoryrag status")
            print(f"   2. 启动系统: categoryrag start")
            
        except Exception as e:
            self.print_error(f"完全重建失败: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
    
    def _incremental_rebuild(self):
        """增量重建"""
        print("\n📈 增量重建")
        print("-" * 30)
        
        try:
            # 检查新文档
            new_documents = self._find_new_documents()
            
            if not new_documents:
                print("✅ 没有发现新文档，无需增量重建")
                return
            
            print(f"📚 发现 {len(new_documents)} 个新文档:")
            for doc in new_documents:
                print(f"   - {doc}")
            
            if not self.args.force:
                if not self.confirm(f"确认处理 {len(new_documents)} 个新文档", True):
                    print("⚠️ 操作已取消")
                    return
            
            # 处理新文档
            success_count = self._process_new_documents(new_documents)
            
            # 更新向量数据库
            print("\n🔢 更新向量数据库...")
            self._update_vector_database()
            
            print(f"\n✅ 增量重建完成!")
            print(f"📊 处理结果: {success_count}/{len(new_documents)} 个新文档")
            
        except Exception as e:
            self.print_error(f"增量重建失败: {e}")
    
    def _rebuild_vectors_only(self):
        """仅重建向量数据库"""
        print("\n🔢 仅重建向量数据库")
        print("-" * 30)
        
        if not self.args.force:
            if not self.confirm("确认重建向量数据库", True):
                print("⚠️ 操作已取消")
                return
        
        try:
            print("🔄 正在重建向量数据库...")
            self._rebuild_vector_database()
            print("✅ 向量数据库重建完成!")
            
        except Exception as e:
            self.print_error(f"向量数据库重建失败: {e}")
    
    def _show_rebuild_status(self):
        """显示重建状态"""
        try:
            print("\n📊 当前状态:")
            
            # 原始文档统计
            raw_docs_dir = Path(self.get_data_paths()["raw_docs"])
            if raw_docs_dir.exists():
                supported_formats = self.config_manager.get_supported_formats()
                raw_count = 0
                for ext in supported_formats:
                    raw_count += len(list(raw_docs_dir.rglob(f"*{ext}")))
                print(f"   原始文档: {raw_count} 个")
            else:
                print("   原始文档: 目录不存在")
            
            # 处理后文档统计
            doc_manager = self._get_document_manager()
            stats = doc_manager.get_database_stats()
            
            if "error" not in stats:
                print(f"   已处理文档: {stats['total_documents']} 个")
                print(f"   分块文件: {stats['total_chunks']} 个")
                print(f"   向量数据: {stats['total_vectors']} 个")
            
        except Exception as e:
            self.print_warning(f"获取状态信息失败: {e}")
    
    def _clean_existing_data(self):
        """清理现有数据"""
        doc_manager = self._get_document_manager()
        result = doc_manager.clean_all_data()
        if not result.success:
            raise Exception(f"清理数据失败: {result.message}")
    
    def _process_all_documents(self, documents: list) -> int:
        """处理所有文档"""
        success_count = 0
        
        for i, doc_path in enumerate(documents, 1):
            try:
                print(f"📄 处理文档 {i}/{len(documents)}: {doc_path.name}")
                
                # 使用文档添加适配器
                from src.cli.adapters.document_workflow_adapter import DocumentWorkflowAdapter
                adapter = DocumentWorkflowAdapter(self.config_manager)
                
                collection_config = {
                    "collection_name": doc_path.stem,
                    "description": f"{doc_path.stem}相关文档",
                    "keywords": [doc_path.stem]
                }
                
                result = adapter.add_document(str(doc_path), collection_config)
                
                if result.status == "success":
                    success_count += 1
                    print(f"   ✅ 成功 (分块: {result.chunks_count})")
                else:
                    print(f"   ❌ 失败: {result.error_message}")
                    
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
        
        return success_count
    
    def _find_new_documents(self) -> list:
        """查找新文档"""
        # 这里应该实现逻辑来比较原始文档和已处理文档
        # 简化实现：返回所有原始文档
        raw_docs_dir = Path(self.get_data_paths()["raw_docs"])
        supported_formats = self.config_manager.get_supported_formats()
        
        new_documents = []
        for ext in supported_formats:
            new_documents.extend(raw_docs_dir.rglob(f"*{ext}"))
        
        return new_documents
    
    def _process_new_documents(self, documents: list) -> int:
        """处理新文档"""
        return self._process_all_documents(documents)
    
    def _rebuild_vector_database(self):
        """重建向量数据库"""
        try:
            # 调用数据库构建器
            result = subprocess.run([
                sys.executable, "collection_database_builder.py"
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            if result.returncode == 0:
                print("✅ 向量数据库构建成功")
            else:
                raise Exception(f"向量数据库构建失败: {result.stderr}")
                
        except Exception as e:
            raise Exception(f"调用数据库构建器失败: {e}")
    
    def _update_vector_database(self):
        """更新向量数据库"""
        # 对于增量更新，也调用完整的数据库构建器
        # 实际应该实现更智能的增量更新逻辑
        self._rebuild_vector_database()
    
    def _get_document_manager(self):
        """获取文档管理器"""
        try:
            from src.core.document_manager import DocumentManager
            return DocumentManager(self.config_manager)
        except ImportError as e:
            self.print_error(f"文档管理器加载失败: {e}")
            sys.exit(1)
        except Exception as e:
            self.print_error(f"文档管理器初始化失败: {e}")
            sys.exit(1)
