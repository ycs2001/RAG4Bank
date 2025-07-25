"""
数据清理命令
"""

import sys
from .base_command import BaseCommand

class CleanCommand(BaseCommand):
    """数据清理命令"""
    
    def execute(self):
        """执行数据清理"""
        print("🧹 CategoryRAG 数据清理")
        print("=" * 50)
        
        if self.args.all:
            self._clean_all_data()
        elif self.args.chunks:
            self._clean_chunks_only()
        elif self.args.vectors:
            self._clean_vectors_only()
        elif self.args.temp:
            self._clean_temp_files()
        else:
            self._interactive_clean()
    
    def _interactive_clean(self):
        """交互式清理"""
        print("🎯 交互式数据清理")
        print("-" * 30)
        
        # 显示当前数据统计
        self._show_data_stats()
        
        print("\n📋 清理选项:")
        print("   1. 清理所有数据 (分块文件 + 向量数据)")
        print("   2. 仅清理分块文件")
        print("   3. 仅清理向量数据")
        print("   4. 清理临时文件")
        print("   5. 取消操作")
        
        while True:
            try:
                choice = input("\n📝 请选择清理选项 [1-5]: ").strip()
                
                if choice == "1":
                    self._clean_all_data()
                    break
                elif choice == "2":
                    self._clean_chunks_only()
                    break
                elif choice == "3":
                    self._clean_vectors_only()
                    break
                elif choice == "4":
                    self._clean_temp_files()
                    break
                elif choice == "5":
                    print("⚠️ 操作已取消")
                    return
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入有效数字")
    
    def _clean_all_data(self):
        """清理所有数据"""
        print("\n🚨 全量数据清理")
        print("-" * 30)
        
        # 显示警告
        print("⚠️ 警告: 此操作将删除所有文档数据!")
        print("   - 所有分块文件")
        print("   - 所有向量数据")
        print("   - ChromaDB中的所有集合")
        print("   - 原始文档将保留")
        
        if not self.args.force:
            if not self.confirm("确认执行全量清理", False):
                print("⚠️ 操作已取消")
                return
            
            # 二次确认
            confirmation = input("📝 请输入 'DELETE ALL' 确认删除: ").strip()
            if confirmation != "DELETE ALL":
                print("⚠️ 确认失败，操作已取消")
                return
        
        # 执行清理
        try:
            print("\n🧹 正在执行全量清理...")
            
            doc_manager = self._get_document_manager()
            result = doc_manager.clean_all_data()
            
            if result.success:
                print(f"\n✅ {result.message}")
                print(f"📊 清理统计:")
                print(f"   分块文件: {result.details.get('removed_chunks', 0)} 个")
                print(f"   集合数据: {result.details.get('removed_collections', 0)} 个")
                
                print(f"\n💡 后续操作:")
                print(f"   1. 重新添加文档: categoryrag add document.pdf")
                print(f"   2. 或全量重建: categoryrag rebuild --from-scratch")
            else:
                self.print_error(result.message)
        
        except Exception as e:
            self.print_error(f"清理操作失败: {e}")
    
    def _clean_chunks_only(self):
        """仅清理分块文件"""
        print("\n📄 分块文件清理")
        print("-" * 30)
        
        if not self.args.force:
            if not self.confirm("确认清理所有分块文件", False):
                print("⚠️ 操作已取消")
                return
        
        try:
            print("🧹 正在清理分块文件...")
            
            from pathlib import Path
            import shutil
            
            chunks_dir = Path(self.get_data_paths()["chunks"])
            removed_count = 0
            
            if chunks_dir.exists():
                for item in chunks_dir.iterdir():
                    if item.is_dir():
                        chunk_count = len(list(item.rglob("*.md")))
                        removed_count += chunk_count
                        shutil.rmtree(item)
                    elif item.is_file():
                        removed_count += 1
                        item.unlink()
            
            print(f"✅ 分块文件清理完成")
            print(f"📊 清理统计: {removed_count} 个文件")
            
        except Exception as e:
            self.print_error(f"分块文件清理失败: {e}")
    
    def _clean_vectors_only(self):
        """仅清理向量数据"""
        print("\n🔢 向量数据清理")
        print("-" * 30)
        
        if not self.args.force:
            if not self.confirm("确认清理所有向量数据", False):
                print("⚠️ 操作已取消")
                return
        
        try:
            print("🧹 正在清理向量数据...")
            
            doc_manager = self._get_document_manager()
            removed_collections = doc_manager._reset_chromadb()
            
            print(f"✅ 向量数据清理完成")
            print(f"📊 清理统计: {removed_collections} 个集合")
            
        except Exception as e:
            self.print_error(f"向量数据清理失败: {e}")
    
    def _clean_temp_files(self):
        """清理临时文件"""
        print("\n🗂️ 临时文件清理")
        print("-" * 30)
        
        try:
            from pathlib import Path
            
            temp_dirs = [
                Path("temp"),
                Path("tmp"),
                Path(".cache"),
                Path("logs")
            ]
            
            removed_count = 0
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    for item in temp_dir.iterdir():
                        if item.is_file() and item.suffix in ['.tmp', '.log', '.cache']:
                            item.unlink()
                            removed_count += 1
            
            print(f"✅ 临时文件清理完成")
            print(f"📊 清理统计: {removed_count} 个文件")
            
        except Exception as e:
            self.print_error(f"临时文件清理失败: {e}")
    
    def _show_data_stats(self):
        """显示数据统计"""
        try:
            print("\n📊 当前数据统计:")
            
            doc_manager = self._get_document_manager()
            stats = doc_manager.get_database_stats()
            
            if "error" in stats:
                self.print_warning(f"获取统计信息失败: {stats['error']}")
                return
            
            print(f"   文档数量: {stats['total_documents']} 个")
            print(f"   分块文件: {stats['total_chunks']} 个")
            print(f"   向量数据: {stats['total_vectors']} 个")
            print(f"   集合数量: {len(stats['collections'])} 个")
            
            if stats['collections']:
                print("   集合详情:")
                for collection in stats['collections']:
                    print(f"     - {collection['name']}: {collection['count']} 个向量")
        
        except Exception as e:
            self.print_warning(f"获取数据统计失败: {e}")
    
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
