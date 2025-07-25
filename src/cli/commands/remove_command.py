"""
文档删除命令
"""

import sys
from pathlib import Path
from .base_command import BaseCommand

class RemoveCommand(BaseCommand):
    """文档删除命令"""
    
    def execute(self):
        """执行文档删除"""
        print("🗑️ CategoryRAG 文档删除")
        print("=" * 50)
        
        if self.args.interactive:
            self._interactive_remove()
        elif self.args.document or self.args.path:
            self._single_remove()
        elif self.args.list:
            self._list_documents()
        else:
            self.print_error("请指定要删除的文档")
            print("💡 使用 --help 查看帮助信息")
    
    def _interactive_remove(self):
        """交互式删除文档"""
        print("🎯 交互式文档删除")
        print("-" * 30)
        
        # 获取文档管理器
        doc_manager = self._get_document_manager()
        
        # 列出所有文档
        documents = doc_manager.list_documents()
        
        if not documents:
            self.print_warning("没有找到任何文档")
            return
        
        print(f"\n📚 找到 {len(documents)} 个文档:")
        for i, doc in enumerate(documents, 1):
            print(f"   {i}. {doc.name} (集合: {doc.collection_id}, 分块: {len(doc.chunk_files)}, 向量: {doc.vector_count})")
        
        # 获取用户选择
        while True:
            try:
                choice = input(f"\n📝 请选择要删除的文档 [1-{len(documents)}] (0=取消): ").strip()
                
                if choice == "0":
                    print("⚠️ 操作已取消")
                    return
                
                index = int(choice) - 1
                if 0 <= index < len(documents):
                    selected_doc = documents[index]
                    break
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效数字")
        
        # 确认删除
        print(f"\n📋 删除确认:")
        print(f"   文档名称: {selected_doc.name}")
        print(f"   集合ID: {selected_doc.collection_id}")
        print(f"   分块文件: {len(selected_doc.chunk_files)} 个")
        print(f"   向量数据: {selected_doc.vector_count} 个")
        
        if not self.confirm(f"确认删除文档 '{selected_doc.name}'", False):
            print("⚠️ 操作已取消")
            return
        
        # 执行删除
        self._execute_remove(selected_doc.name, selected_doc.collection_id)
    
    def _single_remove(self):
        """单个文档删除"""
        document_name = self.args.document or self.args.path
        collection_id = getattr(self.args, 'collection', None)
        
        if not document_name:
            self.print_error("请指定文档名称")
            return
        
        # 如果是文件路径，提取文件名
        if Path(document_name).exists() or '/' in document_name or '\\' in document_name:
            document_name = Path(document_name).stem
        
        # 获取文档管理器
        doc_manager = self._get_document_manager()
        
        # 查找文档
        documents = doc_manager.list_documents(collection_id)
        matching_docs = [doc for doc in documents if doc.name == document_name]
        
        if not matching_docs:
            self.print_error(f"未找到文档: {document_name}")
            if collection_id:
                print(f"💡 在集合 '{collection_id}' 中未找到该文档")
            else:
                print("💡 使用 --list 查看所有可用文档")
            return
        
        if len(matching_docs) > 1 and not collection_id:
            print(f"⚠️ 找到多个同名文档:")
            for doc in matching_docs:
                print(f"   - {doc.name} (集合: {doc.collection_id})")
            print("💡 请使用 --collection 参数指定集合")
            return
        
        selected_doc = matching_docs[0]
        
        # 显示删除信息
        if not self.args.force:
            print(f"\n📋 删除信息:")
            print(f"   文档名称: {selected_doc.name}")
            print(f"   集合ID: {selected_doc.collection_id}")
            print(f"   分块文件: {len(selected_doc.chunk_files)} 个")
            print(f"   向量数据: {selected_doc.vector_count} 个")
            
            if not self.confirm(f"确认删除文档 '{selected_doc.name}'", False):
                print("⚠️ 操作已取消")
                return
        
        # 执行删除
        self._execute_remove(selected_doc.name, selected_doc.collection_id)
    
    def _list_documents(self):
        """列出所有文档"""
        print("📚 文档列表")
        print("-" * 30)
        
        doc_manager = self._get_document_manager()
        documents = doc_manager.list_documents()
        
        if not documents:
            self.print_warning("没有找到任何文档")
            return
        
        # 按集合分组显示
        collections = {}
        for doc in documents:
            if doc.collection_id not in collections:
                collections[doc.collection_id] = []
            collections[doc.collection_id].append(doc)
        
        for collection_id, docs in collections.items():
            print(f"\n📁 集合: {collection_id}")
            for doc in docs:
                print(f"   📄 {doc.name}")
                print(f"      分块: {len(doc.chunk_files)} 个")
                print(f"      向量: {doc.vector_count} 个")
        
        print(f"\n📊 总计: {len(documents)} 个文档")
    
    def _execute_remove(self, document_name: str, collection_id: str):
        """执行删除操作"""
        try:
            print(f"\n🗑️ 正在删除文档: {document_name}")
            
            doc_manager = self._get_document_manager()
            
            # 执行删除
            result = doc_manager.remove_document(document_name, collection_id)
            
            if result.success:
                print(f"\n✅ {result.message}")
                print(f"📊 删除统计:")
                print(f"   分块文件: {result.details.get('removed_chunks', 0)} 个")
                print(f"   向量数据: {result.details.get('removed_vectors', 0)} 个")
                
                print(f"\n💡 建议操作:")
                print(f"   1. 检查系统状态: categoryrag status")
                print(f"   2. 如需重建数据库: categoryrag db rebuild")
            else:
                self.print_error(result.message)
                if result.details and 'error' in result.details:
                    print(f"🔍 错误详情: {result.details['error']}")
        
        except Exception as e:
            self.print_error(f"删除操作失败: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
    
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
