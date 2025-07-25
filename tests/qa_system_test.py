#!/usr/bin/env python3
"""
九个专业问题测试脚本
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def search_in_chunks(query, chunks_dir="./data/processed_docs/chunks"):
    """在分块文件中搜索相关内容"""
    results = []
    chunks_path = Path(chunks_dir)
    
    if not chunks_path.exists():
        return []
    
    # 搜索关键词
    keywords = query.lower().split()
    
    for doc_dir in chunks_path.iterdir():
        if doc_dir.is_dir():
            for chunk_file in doc_dir.glob("*.md"):
                try:
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                    # 计算匹配度
                    matches = sum(1 for keyword in keywords if keyword in content)
                    if matches > 0:
                        results.append({
                            'file': chunk_file,
                            'doc': doc_dir.name,
                            'matches': matches,
                            'content': content[:500]  # 前500字符
                        })
                except Exception:
                    continue
    
    # 按匹配度排序
    results.sort(key=lambda x: x['matches'], reverse=True)
    return results[:5]  # 返回前5个结果

def test_question(question_num, query):
    """测试单个问题"""
    print(f"\n{'='*60}")
    print(f"🔍 问题 {question_num}: {query}")
    print('='*60)
    
    results = search_in_chunks(query)
    
    if results:
        print(f"📚 找到 {len(results)} 个相关文档片段:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 📄 文档: {result['doc']}")
            print(f"   📁 文件: {result['file'].name}")
            print(f"   🎯 匹配度: {result['matches']} 个关键词")
            print(f"   📝 内容预览: {result['content'][:200]}...")
    else:
        print("❌ 未找到相关内容")

def main():
    """主函数 - 测试九个问题"""
    
    questions = [
        "普惠金融领域贷款涉及哪些报送表",
        "2024年1104报送要求相比于2022年1104报送要求变化",
        "人民银行A1411金融机构资产负债项目月报贷款余额与1104报表G01_V贷款余额差异",
        "G01_III存贷款明细报表各项贷款与G01_V主要资产负债项目分币种情况表贷款差别",
        "人民银行普惠金融领域贷款专项统计季报与1104报表S71普惠型小微企业贷款差别",
        "同业存款应当报送在EAST哪些报表",
        "EAST报送表贸易融资业务表包含哪些业务产品",
        "鑫悦存款产品涉及哪些报送表",
        "贴现票据本金100万利息1万实付99万贷款金额和贷款余额填报"
    ]
    
    print("🎯 CategoryRAG系统九个专业问题测试")
    print("=" * 60)
    print("📊 测试方式: 基于文档分块的关键词匹配检索")
    print("📚 知识库: 595个专业文档分块")
    print("🎯 领域: 银行监管报表、EAST系统、人民银行统计制度")
    
    for i, question in enumerate(questions, 1):
        test_question(i, question)
    
    print(f"\n{'='*60}")
    print("🎉 九个问题测试完成")
    print("💡 注意: 这是基于关键词匹配的简化测试")
    print("🚀 完整RAG系统将提供更准确的语义检索和智能回答")
    print("=" * 60)

if __name__ == "__main__":
    main()
