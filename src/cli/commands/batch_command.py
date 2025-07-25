"""
批量操作命令
"""

from .base_command import BaseCommand

class BatchCommand(BaseCommand):
    """批量操作命令"""
    
    def execute(self):
        """执行批量操作"""
        action = self.args.batch_action
        
        if action == 'add':
            self._batch_add()
        else:
            print("❌ 未知的批量操作")
    
    def _batch_add(self):
        """批量添加文档"""
        self.print_info("批量添加功能请使用: categoryrag add directory/ --batch")
