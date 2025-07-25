#!/usr/bin/env python3
"""
CategoryRAG Web服务依赖安装脚本
"""

import subprocess
import sys

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """主函数"""
    print("🎯 CategoryRAG Web服务依赖安装")
    print("=" * 50)
    
    # Web服务所需的额外依赖
    web_dependencies = [
        'flask>=2.0.0',
        'flask-cors>=3.0.0',
        'requests>=2.25.0'
    ]
    
    print("📦 安装Web服务依赖...")
    
    failed_packages = []
    for package in web_dependencies:
        print(f"   安装 {package}...")
        if install_package(package):
            print(f"   ✅ {package} 安装成功")
        else:
            print(f"   ❌ {package} 安装失败")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ 以下依赖安装失败:")
        for package in failed_packages:
            print(f"   - {package}")
        print("\n💡 请手动安装:")
        print(f"   pip install {' '.join(failed_packages)}")
        sys.exit(1)
    else:
        print("\n✅ 所有Web服务依赖安装成功！")
        print("\n🚀 现在可以启动Web服务:")
        print("   python start_web.py")
        print("   或者")
        print("   ./categoryrag web start")

if __name__ == '__main__':
    main()
