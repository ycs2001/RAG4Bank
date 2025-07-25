#!/usr/bin/env python3
"""
RAG系统功能测试脚本
"""

import os
import sys
from pathlib import Path

def test_system_components():
    """测试系统组件"""
    print('🔍 RAG系统功能测试')
    print('=' * 50)
    
    # 测试1: 配置文件
    config_file = './config/config.yaml'
    if os.path.exists(config_file):
        print('✅ 配置文件存在')
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'qwen' in content and 'chromadb' in content:
                print('   - LLM配置: Qwen API')
                print('   - 数据库配置: ChromaDB')
    else:
        print('❌ 配置文件不存在')
    
    # 测试2: 数据库文件
    db_file = './data/chroma_db/chroma.sqlite3'
    if os.path.exists(db_file):
        size = os.path.getsize(db_file)
        print(f'✅ 数据库文件存在: {size} bytes')
    else:
        print('❌ 数据库文件不存在')
    
    # 测试3: 分块文件统计
    chunks_dir = './data/processed_docs/chunks'
    if os.path.exists(chunks_dir):
        chunk_count = 0
        doc_folders = 0
        for root, dirs, files in os.walk(chunks_dir):
            if root != chunks_dir:  # 子文件夹
                doc_folders += 1
            chunk_count += len([f for f in files if f.endswith('.md')])
        print(f'✅ 文档分块: {chunk_count} 个文件，{doc_folders} 个文档')
    else:
        print('❌ 分块目录不存在')
    
    # 测试4: 源代码结构
    src_dir = './src'
    if os.path.exists(src_dir):
        components = []
        if os.path.exists('./src/core'):
            components.append('核心系统')
        if os.path.exists('./src/retrievers'):
            components.append('检索器')
        if os.path.exists('./src/llm'):
            components.append('LLM集成')
        if os.path.exists('./src/config'):
            components.append('配置管理')
        print(f'✅ 源代码结构: {", ".join(components)}')
    else:
        print('❌ 源代码目录不存在')
    
    # 测试5: 主要脚本
    scripts = [
        ('rag_app.py', 'RAG应用入口'),
        ('build_rag_system.py', '系统构建脚本'),
        ('test_multi_collection.py', '多集合测试'),
        ('rebuild_multi_collection_db.py', '数据库重建')
    ]
    
    print('\n📋 可用脚本:')
    for script, desc in scripts:
        if os.path.exists(script):
            print(f'   ✅ {script}: {desc}')
        else:
            print(f'   ❌ {script}: 不存在')

def test_sample_chunks():
    """测试样本分块内容"""
    print('\n📄 样本分块内容测试:')
    
    # 查找第一个分块文件
    chunks_dir = Path('./data/processed_docs/chunks')
    if chunks_dir.exists():
        for doc_dir in chunks_dir.iterdir():
            if doc_dir.is_dir():
                chunk_files = list(doc_dir.glob('*.md'))
                if chunk_files:
                    sample_file = chunk_files[0]
                    print(f'   📁 文档: {doc_dir.name}')
                    print(f'   📄 样本文件: {sample_file.name}')
                    
                    # 读取前几行
                    try:
                        with open(sample_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[:10]
                            print('   📝 内容预览:')
                            for i, line in enumerate(lines, 1):
                                print(f'      {i:2d}: {line.strip()[:60]}...')
                    except Exception as e:
                        print(f'   ❌ 读取失败: {e}')
                    break
    else:
        print('   ❌ 分块目录不存在')

def test_configuration():
    """测试配置内容"""
    print('\n⚙️ 配置内容测试:')
    
    config_file = './config/config.yaml'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查关键配置
            configs = [
                ('llm.qwen.model', 'LLM模型'),
                ('retrieval.strategy', '检索策略'),
                ('retrieval.chromadb.db_path', '数据库路径'),
                ('retrieval.top_k', '检索数量')
            ]
            
            for config_key, desc in configs:
                if config_key.split('.')[-1] in content:
                    print(f'   ✅ {desc}: 已配置')
                else:
                    print(f'   ⚠️ {desc}: 可能未配置')
                    
        except Exception as e:
            print(f'   ❌ 配置读取失败: {e}')
    else:
        print('   ❌ 配置文件不存在')

def main():
    """主函数"""
    test_system_components()
    test_sample_chunks()
    test_configuration()
    
    print('\n🎯 测试总结:')
    print('   - 系统架构: 多集合RAG智能问答系统')
    print('   - 技术栈: ChromaDB + BGE + Qwen API')
    print('   - 知识库: 金融监管领域专业文档')
    print('   - 功能: 智能检索 + 专业问答')
    
    print('\n💡 下一步建议:')
    print('   1. 安装完整依赖: pip install -r requirements.txt')
    print('   2. 配置BGE模型路径')
    print('   3. 验证Qwen API密钥')
    print('   4. 运行完整系统测试')

if __name__ == "__main__":
    main()
