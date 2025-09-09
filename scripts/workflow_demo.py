#!/usr/bin/env python3
"""
CategoryRAG文档添加工作流演示
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

def main():
    print("🎯 CategoryRAG文档添加工作流")
    print("=" * 50)
    
    print("📋 支持的文档格式:")
    print("  - Word文档: .docx, .doc")
    print("  - PDF文档: .pdf")
    print("  - Excel文档: .xlsx, .xls")
    
    print("\n🚀 使用方法:")
    print("1. 交互式添加:")
    print("   python3 scripts/add_document_workflow.py --interactive")
    
    print("\n2. 命令行添加:")
    print("   python3 scripts/add_document_workflow.py \\")
    print("     --file 'document.docx' \\")
    print("     --collection-name '新文档集合'")
    
    print("\n📁 目录结构:")
    dirs_to_check = [
        "data/raw_docs",
        "data/processed_docs/chunks", 
        "data/toc",
        "config"
    ]
    
    for dir_path in dirs_to_check:
        full_path = project_root / dir_path
        status = "✅" if full_path.exists() else "❌"
        print(f"   {status} {dir_path}")
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"      已创建目录: {dir_path}")
    
    print("\n🔄 工作流程:")
    print("   1. 文档预处理 → 复制到raw_docs目录")
    print("   2. 文档转换 → 转换为Markdown格式")
    print("   3. 智能分块 → 按语义分割文档")
    print("   4. TOC提取 → 提取文档目录结构 (仅PDF/Word)")
    print("   5. 向量化 → 生成文档向量并存储")
    print("   6. 配置更新 → 更新系统配置文件")

    print("\n📋 格式支持说明:")
    print("   ✅ PDF/Word: 完整支持 (包括TOC提取)")
    print("   ⚠️ Excel: 部分支持 (跳过TOC提取)")
    
    print("\n✅ 工作流已准备就绪！")
    print("💡 提示: 使用 --interactive 参数启动交互式添加模式")

if __name__ == "__main__":
    main()
