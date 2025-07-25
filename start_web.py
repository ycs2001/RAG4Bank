#!/usr/bin/env python3
"""
CategoryRAG Web服务启动脚本
简化的启动入口，支持基本配置
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    required_packages = ['flask', 'flask-cors']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 请安装缺少的依赖:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_system_status():
    """检查CategoryRAG系统状态"""
    print("🔍 检查CategoryRAG系统状态...")
    
    # 检查配置文件
    config_file = Path('config/unified_config.yaml')
    if not config_file.exists():
        print("❌ 配置文件不存在: config/unified_config.yaml")
        return False
    
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

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='CategoryRAG Web服务启动器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python start_web.py                    # 默认启动 (127.0.0.1:5000)
  python start_web.py --host 0.0.0.0    # 允许外部访问
  python start_web.py --port 8080       # 自定义端口
  python start_web.py --debug           # 调试模式
  python start_web.py --check-only      # 仅检查系统状态
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1', 
                       help='服务器地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='服务器端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    parser.add_argument('--check-only', action='store_true',
                       help='仅检查系统状态，不启动服务')
    parser.add_argument('--skip-checks', action='store_true',
                       help='跳过系统检查，直接启动')
    
    args = parser.parse_args()
    
    print("🎯 CategoryRAG Web服务启动器")
    print("=" * 50)
    
    # 检查依赖
    if not args.skip_checks:
        print("📦 检查Python依赖...")
        if not check_dependencies():
            sys.exit(1)
        
        # 检查系统状态
        if not check_system_status():
            print("\n❌ 系统检查失败")
            print("💡 请确保CategoryRAG系统已正确配置和初始化")
            sys.exit(1)
    
    if args.check_only:
        print("\n✅ 系统检查完成，一切正常")
        return
    
    # 启动Web服务
    print(f"\n🚀 启动CategoryRAG Web服务...")
    print(f"   地址: http://{args.host}:{args.port}")
    print(f"   调试模式: {'开启' if args.debug else '关闭'}")
    print("\n📋 API端点:")
    print(f"   健康检查: http://{args.host}:{args.port}/api/health")
    print(f"   系统状态: http://{args.host}:{args.port}/api/status")
    print(f"   集合信息: http://{args.host}:{args.port}/api/collections")
    print(f"   问答查询: http://{args.host}:{args.port}/api/query")
    print(f"   文档添加: http://{args.host}:{args.port}/api/documents")
    print("\n💡 按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        # 启动Web服务
        cmd = [
            sys.executable, 'web_service.py',
            '--host', args.host,
            '--port', str(args.port)
        ]
        
        if args.debug:
            cmd.append('--debug')
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 Web服务已停止")
    except FileNotFoundError:
        print("❌ 找不到web_service.py文件")
        print("💡 请确保在CategoryRAG项目根目录中运行此脚本")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
