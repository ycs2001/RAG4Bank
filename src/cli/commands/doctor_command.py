"""
系统健康检查命令
"""

from .base_command import BaseCommand

class DoctorCommand(BaseCommand):
    """系统健康检查命令"""
    
    def execute(self):
        """执行健康检查"""
        print("🏥 CategoryRAG 系统健康检查")
        print("=" * 50)
        
        issues = self._run_health_check()
        
        if not issues:
            self.print_success("系统健康状况良好！")
        else:
            print(f"\n⚠️ 发现 {len(issues)} 个问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            if self.args.fix:
                self._auto_fix_issues(issues)
            else:
                print("\n💡 使用 --fix 参数自动修复问题")
        
        if self.args.report:
            self._generate_report(issues)
    
    def _run_health_check(self) -> list:
        """运行健康检查"""
        issues = []
        
        print("🔍 检查配置...")
        try:
            self.config_manager.validate_config()
            self.print_status_item("配置验证", True)
        except Exception as e:
            self.print_status_item("配置验证", False, str(e))
            issues.append(f"配置验证失败: {e}")
        
        print("\n📁 检查目录结构...")
        data_paths = self.get_data_paths()
        for name, path in data_paths.items():
            from pathlib import Path
            exists = Path(path).exists()
            self.print_status_item(f"目录: {name}", exists, path)
            if not exists:
                issues.append(f"目录不存在: {path}")
        
        print("\n🤖 检查模型...")
        bge_path = self.config_manager.get("embedding.model.path")
        if bge_path:
            from pathlib import Path
            bge_exists = Path(bge_path).exists()
            self.print_status_item("BGE模型", bge_exists, bge_path)
            if not bge_exists:
                issues.append(f"BGE模型不存在: {bge_path}")
        else:
            self.print_status_item("BGE模型", False, "未配置")
            issues.append("BGE模型路径未配置")
        
        print("\n🔧 检查服务...")
        # 检查LLM配置
        llm_api_key = self.config_manager.get("llm.primary.api_key")
        llm_configured = bool(llm_api_key and not llm_api_key.startswith("${"))
        self.print_status_item("LLM API密钥", llm_configured)
        if not llm_configured:
            issues.append("LLM API密钥未配置")
        
        return issues
    
    def _auto_fix_issues(self, issues: list):
        """自动修复问题"""
        print(f"\n🔧 尝试自动修复 {len(issues)} 个问题...")
        
        fixed_count = 0
        for issue in issues:
            if "目录不存在" in issue:
                # 创建缺失的目录
                path = issue.split(": ")[-1]
                try:
                    from pathlib import Path
                    Path(path).mkdir(parents=True, exist_ok=True)
                    self.print_success(f"已创建目录: {path}")
                    fixed_count += 1
                except Exception as e:
                    self.print_error(f"创建目录失败: {e}")
            else:
                self.print_warning(f"无法自动修复: {issue}")
        
        print(f"\n✅ 已修复 {fixed_count}/{len(issues)} 个问题")
    
    def _generate_report(self, issues: list):
        """生成健康报告"""
        from datetime import datetime
        
        report_file = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("CategoryRAG 系统健康报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {datetime.now()}\n\n")
            
            if issues:
                f.write(f"发现问题 ({len(issues)} 个):\n")
                for i, issue in enumerate(issues, 1):
                    f.write(f"  {i}. {issue}\n")
            else:
                f.write("✅ 系统健康状况良好\n")
        
        self.print_success(f"健康报告已生成: {report_file}")
