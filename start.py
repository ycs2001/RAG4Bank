#!/usr/bin/env python3
"""
CategoryRAG系统启动脚本

这是CategoryRAG系统的统一启动入口。
"""

import sys
import os
import subprocess

def main():
    """启动CategoryRAG交互界面"""
    print("🎯 CategoryRAG智能问答系统")
    print("=" * 50)
    print("🚀 正在启动交互界面...")
    print()
    
    # 获取CLI脚本路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cli_script = os.path.join(script_dir, 'scripts', 'cli_interface.py')
    
    # 检查CLI脚本是否存在
    if not os.path.exists(cli_script):
        print(f"❌ 找不到CLI脚本: {cli_script}")
        print("💡 请确保您在CategoryRAG项目根目录中运行此脚本")
        sys.exit(1)
    
    try:
        # 启动交互界面
        subprocess.run([sys.executable, cli_script, '--interactive'])
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print(f"💡 请手动运行: python3 {cli_script} --interactive")
        sys.exit(1)

if __name__ == "__main__":
    main()
