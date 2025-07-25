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
        self.print_info("数据库备份功能待实现")
    
    def _restore_database(self):
        """恢复数据库"""
        self.print_info("数据库恢复功能待实现")
