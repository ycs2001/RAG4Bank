"""
数据库操作命令
"""

import sys
from pathlib import Path
from .base_command import BaseCommand

class DbCommand(BaseCommand):
    """数据库操作命令"""
    
    def execute(self):
        """执行数据库操作"""
        action = self.args.db_action
        
        if action == 'rebuild':
            self._rebuild_database()
        elif action == 'backup':
            self._backup_database()
        elif action == 'restore':
            self._restore_database()
        else:
            print("❌ 未知的数据库操作")
    
    def _rebuild_database(self):
        """重建数据库"""
        print("🔄 重建向量数据库...")
        
        if not self.confirm("确认重建数据库（将删除现有数据）", False):
            print("⚠️ 操作已取消")
            return
        
        try:
            # 调用数据库构建器
            import subprocess
            result = subprocess.run([
                sys.executable, "collection_database_builder.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_success("数据库重建完成")
            else:
                self.print_error(f"数据库重建失败: {result.stderr}")
        except Exception as e:
            self.print_error(f"数据库重建失败: {e}")
    
    def _backup_database(self):
        """备份数据库"""
        print("💾 备份向量数据库...")
        print("-" * 30)

        try:
            import time
            import shutil
            import tarfile

            # 生成备份文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_filename = f"categoryrag_backup_{timestamp}.tar.gz"
            backup_path = Path("backups") / backup_filename

            # 创建备份目录
            backup_path.parent.mkdir(exist_ok=True)

            # 获取数据路径
            data_paths = self.get_data_paths()

            print(f"📁 备份目标: {backup_path}")
            print("📦 备份内容:")
            print("   - ChromaDB数据库")
            print("   - 分块文件")
            print("   - 配置文件")

            if not self.confirm("确认创建备份", True):
                print("⚠️ 操作已取消")
                return

            print("\n🚀 开始备份...")

            # 创建tar.gz备份
            with tarfile.open(backup_path, "w:gz") as tar:
                # 备份ChromaDB
                chroma_db_path = Path(data_paths["chroma_db"])
                if chroma_db_path.exists():
                    print("📄 备份ChromaDB...")
                    tar.add(chroma_db_path, arcname="chroma_db")

                # 备份分块文件
                chunks_path = Path(data_paths["chunks"])
                if chunks_path.exists():
                    print("📄 备份分块文件...")
                    tar.add(chunks_path, arcname="chunks")

                # 备份配置文件
                config_path = Path("config")
                if config_path.exists():
                    print("📄 备份配置文件...")
                    tar.add(config_path, arcname="config")

            # 获取备份文件大小
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB

            print(f"\n✅ 数据库备份完成!")
            print(f"📊 备份信息:")
            print(f"   文件: {backup_path}")
            print(f"   大小: {backup_size:.2f} MB")
            print(f"   时间: {timestamp}")

            print(f"\n💡 恢复命令:")
            print(f"   categoryrag db restore {backup_path}")

        except Exception as e:
            self.print_error(f"数据库备份失败: {e}")

    def _restore_database(self):
        """恢复数据库"""
        backup_file = getattr(self.args, 'backup_file', None)

        if not backup_file:
            self.print_error("请指定备份文件")
            print("💡 使用方法: categoryrag db restore backup.tar.gz")
            return

        backup_path = Path(backup_file)
        if not backup_path.exists():
            self.print_error(f"备份文件不存在: {backup_path}")
            return

        print(f"🔄 恢复数据库: {backup_path.name}")
        print("-" * 30)

        try:
            import tarfile
            import shutil

            # 显示备份信息
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            print(f"📊 备份文件信息:")
            print(f"   文件: {backup_path}")
            print(f"   大小: {backup_size:.2f} MB")

            print("\n⚠️ 警告: 此操作将:")
            print("   1. 停止当前系统")
            print("   2. 删除现有数据")
            print("   3. 恢复备份数据")

            if not self.confirm("确认恢复数据库", False):
                print("⚠️ 操作已取消")
                return

            print("\n🚀 开始恢复...")

            # 获取数据路径
            data_paths = self.get_data_paths()

            # 删除现有数据
            print("🗑️ 清理现有数据...")
            for path_key in ["chroma_db", "chunks"]:
                path = Path(data_paths[path_key])
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()

            # 恢复数据
            print("📦 恢复备份数据...")
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=".")

            print(f"\n✅ 数据库恢复完成!")
            print(f"💡 建议操作:")
            print(f"   1. 检查系统状态: categoryrag status")
            print(f"   2. 启动系统: categoryrag start")

        except Exception as e:
            self.print_error(f"数据库恢复失败: {e}")
