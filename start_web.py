#!/usr/bin/env python3
"""
CategoryRAG统一Web服务启动器
支持基础RAG服务和监管报送服务
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

class CategoryRAGLauncher:
    """CategoryRAG统一启动器"""

    def __init__(self):
        self.service_modes = {
            'basic': {
                'name': 'CategoryRAG基础服务',
                'script': 'web_service.py',
                'default_port': 5000,
                'endpoints': [
                    'GET  /api/health      - 健康检查',
                    'GET  /api/status      - 系统状态',
                    'GET  /api/collections - 集合信息',
                    'POST /api/query       - 问答查询',
                    'POST /api/documents   - 文档添加'
                ]
            }
        }

    def check_dependencies(self):
        """检查Python依赖"""
        # 包名映射：pip包名 -> Python导入名
        required_packages = {
            'flask': 'flask',
            'flask_cors': 'flask_cors',
            'chromadb': 'chromadb',
            'sentence_transformers': 'sentence_transformers',
            'pyyaml': 'yaml',  # PyYAML包的导入名是yaml
            'openai': 'openai',
            'pandas': 'pandas',
            'openpyxl': 'openpyxl'
        }

        missing_packages = []
        for pip_name, import_name in required_packages.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(pip_name)

        if missing_packages:
            print("❌ 缺少以下依赖包:")
            for package in missing_packages:
                print(f"   - {package}")
            print("\n💡 请安装缺少的依赖:")
            print(f"   pip install {' '.join(missing_packages)}")
            return False

        print("✅ Python依赖检查通过")
        return True

    def check_system_status(self):
        """检查CategoryRAG系统状态"""
        print("🔍 检查CategoryRAG系统状态...")

        # 检查配置文件
        config_file = Path('config/unified_config.yaml')
        if not config_file.exists():
            print("❌ 配置文件不存在: config/unified_config.yaml")
            print("💡 请先配置系统或运行: python3 collection_database_builder.py")
            return False

        # 检查配置文件是否为空
        if config_file.stat().st_size <= 10:
            print("⚠️ 配置文件为空，将使用默认配置")
            print("💡 建议运行: python3 collection_database_builder.py 重建配置")

        # 检查数据库
        db_path = Path('data/chroma_db')
        if not db_path.exists():
            print("❌ ChromaDB数据库不存在: data/chroma_db")
            print("💡 请先运行: python3 collection_database_builder.py")
            return False

        # 检查BGE模型
        bge_path = Path('bge-large-zh-v1.5')
        if not bge_path.exists():
            print("⚠️ BGE模型目录不存在，将使用配置文件中的路径")

        print("✅ 系统检查通过")
        return True

    def launch_service(self, mode='basic', host='127.0.0.1', port=None, debug=False):
        """启动Web服务"""
        service_config = self.service_modes[mode]
        service_port = port or service_config['default_port']

        print(f"\n🚀 启动{service_config['name']}...")
        print(f"   地址: http://{host}:{service_port}")
        print(f"   调试模式: {'开启' if debug else '关闭'}")
        print(f"\n📋 API端点:")
        for endpoint in service_config['endpoints']:
            print(f"   {endpoint}")
        print("\n💡 按 Ctrl+C 停止服务")
        print("-" * 50)

        try:
            # 启动Web服务
            cmd = [
                sys.executable, service_config['script'],
                '--host', host,
                '--port', str(service_port)
            ]

            if debug:
                cmd.append('--debug')

            subprocess.run(cmd)

        except KeyboardInterrupt:
            print(f"\n👋 {service_config['name']}已停止")
        except FileNotFoundError:
            print(f"❌ 找不到{service_config['script']}文件")
            print("💡 请确保在CategoryRAG项目根目录中运行此脚本")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='CategoryRAG统一Web服务启动器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python start_web.py                    # 默认启动基础服务 (127.0.0.1:5000)
  python start_web.py --host 0.0.0.0    # 允许外部访问
  python start_web.py --port 8080       # 自定义端口
  python start_web.py --debug           # 调试模式
  python start_web.py --check-only      # 仅检查系统状态
        """
    )

    parser.add_argument('--mode', choices=['basic'], default='basic',
                       help='服务模式 (默认: basic)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='服务器地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int,
                       help='服务器端口 (默认: 根据模式自动选择)')
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    parser.add_argument('--check-only', action='store_true',
                       help='仅检查系统状态，不启动服务')
    parser.add_argument('--skip-checks', action='store_true',
                       help='跳过系统检查，直接启动')

    args = parser.parse_args()

    # 创建启动器实例
    launcher = CategoryRAGLauncher()

    print("🎯 CategoryRAG统一Web服务启动器")
    print("=" * 50)

    # 检查依赖和系统状态
    if not args.skip_checks:
        print("📦 检查Python依赖...")
        if not launcher.check_dependencies():
            sys.exit(1)

        # 检查系统状态
        if not launcher.check_system_status():
            print("\n❌ 系统检查失败")
            print("💡 请确保CategoryRAG系统已正确配置和初始化")
            sys.exit(1)

    if args.check_only:
        print("\n✅ 系统检查完成，一切正常")
        return

    # 启动Web服务
    launcher.launch_service(
        mode=args.mode,
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == '__main__':
    main()
