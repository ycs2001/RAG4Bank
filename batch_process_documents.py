#!/usr/bin/env python3
"""
批量处理KnowledgeBase中的所有文档
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 文档配置映射
DOCUMENT_CONFIGS = [
    {
        "file": "1104报表合辑【2022版】.docx",
        "collection": "1104报表_2022版",
        "keywords": "1104,2022,银行业监管统计,报表制度,旧版"
    },
    {
        "file": "1104报表合辑【2024版】.docx", 
        "collection": "1104报表_2024版",
        "keywords": "1104,2024,银行业监管统计,报表制度,新版"
    },
    {
        "file": "EAST数据结构.xlsx",
        "collection": "EAST数据结构",
        "keywords": "EAST,数据结构,监管数据,报送系统"
    },
    {
        "file": "EAST元数据说明.xlsx",
        "collection": "EAST元数据说明", 
        "keywords": "EAST,元数据,数据说明"
    },
    {
        "file": "EAST表结构.xlsx",
        "collection": "EAST表结构",
        "keywords": "EAST,表结构,数据表"
    },
    {
        "file": "EAST自营资金报送范围.xlsx",
        "collection": "EAST自营资金",
        "keywords": "EAST,自营资金,报送范围"
    },
    {
        "file": "一表通数据结构.xlsx",
        "collection": "一表通数据结构",
        "keywords": "一表通,数据结构,产品报送"
    },
    {
        "file": "一表通产品报送映射.xlsx",
        "collection": "一表通产品映射",
        "keywords": "一表通,产品映射,报送映射"
    },
    {
        "file": "XX银行鑫悦结构性存款产品管理办法（试行）.docx",
        "collection": "银行产品管理办法",
        "keywords": "银行,产品管理,存款,管理办法"
    }
]

def process_document(doc_config):
    """处理单个文档"""
    file_path = f"data/KnowledgeBase/{doc_config['file']}"
    collection = doc_config['collection']
    keywords = doc_config['keywords']
    
    print(f"\n🚀 处理文档: {doc_config['file']}")
    print(f"   集合: {collection}")
    print(f"   关键词: {keywords}")
    
    # 构建命令
    cmd = [
        "./categoryrag", "add", file_path,
        "--collection", collection,
        "--keywords", keywords
    ]
    
    try:
        # 执行命令
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300  # 5分钟超时
        )
        
        processing_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"   ✅ 成功 (耗时: {processing_time:.1f}秒)")
            return True
        else:
            print(f"   ❌ 失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ 超时 (超过5分钟)")
        return False
    except Exception as e:
        print(f"   💥 异常: {e}")
        return False

def main():
    """主函数"""
    print("🎯 CategoryRAG批量文档处理")
    print("=" * 50)
    
    # 检查工作目录
    if not Path("./categoryrag").exists():
        print("❌ 错误: 请在CategoryRAG项目根目录下运行此脚本")
        sys.exit(1)
    
    # 检查KnowledgeBase目录
    kb_dir = Path("data/KnowledgeBase")
    if not kb_dir.exists():
        print("❌ 错误: KnowledgeBase目录不存在")
        sys.exit(1)
    
    # 统计信息
    total_docs = len(DOCUMENT_CONFIGS)
    success_count = 0
    failed_docs = []
    
    print(f"📚 准备处理 {total_docs} 个文档")
    
    # 逐个处理文档
    for i, doc_config in enumerate(DOCUMENT_CONFIGS, 1):
        print(f"\n📄 [{i}/{total_docs}] 处理进度")
        
        # 检查文件是否存在
        file_path = kb_dir / doc_config['file']
        if not file_path.exists():
            print(f"   ⚠️ 跳过: 文件不存在 - {doc_config['file']}")
            failed_docs.append(doc_config['file'])
            continue
        
        # 处理文档
        if process_document(doc_config):
            success_count += 1
        else:
            failed_docs.append(doc_config['file'])
        
        # 短暂休息，避免系统过载
        if i < total_docs:
            print("   ⏸️ 休息2秒...")
            time.sleep(2)
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 处理总结")
    print(f"   总文档数: {total_docs}")
    print(f"   成功处理: {success_count}")
    print(f"   失败文档: {len(failed_docs)}")
    
    if failed_docs:
        print("\n❌ 失败的文档:")
        for doc in failed_docs:
            print(f"   - {doc}")
    
    if success_count == total_docs:
        print("\n🎉 所有文档处理完成！")
    else:
        print(f"\n⚠️ 有 {len(failed_docs)} 个文档处理失败")
    
    print("\n💡 下一步: 运行向量数据库构建")
    print("   python3 collection_database_builder.py")

if __name__ == "__main__":
    main()
