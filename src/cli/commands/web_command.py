"""
Web服务管理命令
"""

import sys
import subprocess
from pathlib import Path
from .base_command import BaseCommand

class WebCommand(BaseCommand):
    """Web服务管理命令"""
    
    def execute(self):
        """执行Web服务操作"""
        if self.args.action == 'start':
            self._start_web_service()
        elif self.args.action == 'test':
            self._test_web_service()
        else:
            self.print_error(f"未知的Web服务操作: {self.args.action}")
            sys.exit(1)
    
    def _start_web_service(self):
        """启动Web服务"""
        print("🚀 启动CategoryRAG Web服务")
        print("=" * 50)
        
        # 检查Web服务文件
        web_service_script = Path("start_web.py")
        if not web_service_script.exists():
            self.print_error("找不到Web服务启动脚本: start_web.py")
            self.print_info("请确保在CategoryRAG项目根目录中运行此命令")
            sys.exit(1)
        
        try:
            # 构建启动命令
            cmd = [
                sys.executable, str(web_service_script),
                '--host', self.args.host,
                '--port', str(self.args.port)
            ]
            
            if self.args.debug:
                cmd.append('--debug')
            
            self.print_info(f"启动Web服务: {self.args.host}:{self.args.port}")
            if self.args.debug:
                self.print_info("调试模式: 开启")
            
            # 启动Web服务
            subprocess.run(cmd)
            
        except KeyboardInterrupt:
            print("\n👋 Web服务已停止")
        except Exception as e:
            self.print_error(f"Web服务启动失败: {e}")
            sys.exit(1)
    
    def _test_web_service(self):
        """测试Web服务"""
        print("🔍 测试CategoryRAG Web API")
        print("=" * 50)
        
        # 检查测试脚本
        test_script = Path("test_web_api.py")
        if not test_script.exists():
            self.print_error("找不到Web API测试脚本: test_web_api.py")
            self.print_info("请确保在CategoryRAG项目根目录中运行此命令")
            sys.exit(1)
        
        try:
            # 构建测试命令
            base_url = f"http://{self.args.host}:{self.args.port}"
            cmd = [
                sys.executable, str(test_script),
                '--url', base_url
            ]
            
            self.print_info(f"测试Web服务: {base_url}")
            
            # 运行测试
            result = subprocess.run(cmd)
            
            if result.returncode == 0:
                self.print_success("Web API测试完成")
            else:
                self.print_error("Web API测试失败")
                sys.exit(1)
                
        except Exception as e:
            self.print_error(f"Web API测试异常: {e}")
            sys.exit(1)
