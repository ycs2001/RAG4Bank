#!/usr/bin/env python3
"""
CategoryRAG多集合数据库构建器
负责将文档分块按主题分类存储到对应的ChromaDB集合中
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from src.config.enhanced_config_manager import EnhancedConfigManager
from src.retrievers import ChromaDBRetriever

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CollectionDatabaseBuilder:
    """CategoryRAG多集合数据库构建器"""
    
    def __init__(self):
        """初始化构建器"""
        self.config_manager = EnhancedConfigManager()
        self.retriever = None
        
        # 文档到集合的映射规则
        self.doc_to_collection_mapping = {
            '人民银行金融统计制度汇编': 'pboc_statistics',
            '1104报表合辑【2024版】': 'report_1104_2024',
            '1104报表合辑【2022版】': 'report_1104_2022',
            'EAST数据结构': 'east_data_structure',
            'EAST元数据说明': 'east_metadata',
            'EAST自营资金报送范围': 'east_data_structure',
            'EAST表结构': 'east_data_structure',
            '一表通数据结构': 'ybt_data_structure',
            '一表通产品报送映射': 'ybt_product_mapping',
            'XX银行鑫悦结构性存款产品管理办法（试行）': 'bank_product_management',
            '白皮书参考': 'regulatory_reference',
            '监管口径答疑文档_v1.0': 'regulatory_qa_guidance'
        }
        
    def build(self):
        """重新构建多集合数据库"""
        logger.info("🚀 开始构建多集合数据库")
        
        try:
            # 1. 初始化检索器
            self._init_retriever()
            
            # 2. 处理每个文档类型
            chunks_dir = Path("data/processed_docs/chunks")
            
            for doc_folder in chunks_dir.iterdir():
                if doc_folder.is_dir():
                    doc_name = doc_folder.name
                    logger.info(f"📄 处理文档: {doc_name}")
                    
                    # 确定目标集合
                    collection_id = self._determine_collection_id(doc_name)
                    logger.info(f"  🎯 目标集合: {collection_id}")
                    
                    # 读取所有分块文件
                    chunks = self._read_chunks_from_folder(doc_folder, doc_name)
                    logger.info(f"  📊 读取到 {len(chunks)} 个分块")
                    
                    if chunks:
                        # 分批添加到集合
                        self._add_chunks_to_collection(chunks, collection_id, doc_name)
            
            # 3. 验证结果
            self._verify_build()
            
            logger.info("✅ 多集合数据库构建完成！")
            return True

        except Exception as e:
            logger.error(f"❌ 重建失败: {e}")
            return False

    def build_auto(self):
        """自动构建数据库（无交互）"""
        logger.info("🚀 开始自动构建多集合数据库")

        try:
            # 1. 初始化检索器
            self._init_retriever()

            # 2. 处理每个文档类型
            chunks_dir = Path("data/processed_docs/chunks")

            for doc_folder in chunks_dir.iterdir():
                if doc_folder.is_dir():
                    doc_name = doc_folder.name
                    logger.info(f"📄 处理文档: {doc_name}")

                    # 确定目标集合
                    collection_id = self._determine_collection_id(doc_name)
                    logger.info(f"  🎯 目标集合: {collection_id}")

                    # 读取所有分块文件
                    chunks = self._read_chunks_from_folder(doc_folder, doc_name)
                    logger.info(f"  📊 读取到 {len(chunks)} 个分块")

                    if chunks:
                        # 分批添加到集合
                        self._add_chunks_to_collection(chunks, collection_id, doc_name)

            # 3. 验证结果
            self._verify_build()

            logger.info("✅ 自动构建完成！")
            return True

        except Exception as e:
            logger.error(f"❌ 自动构建失败: {e}")
            return False
    
    def _init_retriever(self):
        """初始化检索器"""
        logger.info("🔧 初始化多集合检索器...")
        
        # 构建检索器配置（使用正确的嵌套结构）
        retriever_config = {
            'chromadb': {
                'db_path': self.config_manager.get('retrieval.chromadb.db_path', './data/chroma_db'),
                'default_collection_name': self.config_manager.get('retrieval.chromadb.default_collection_name', 'knowledge_base')
            },
            'embedding': {
                'model_path': self.config_manager.get('retrieval.embedding.model_path'),
                'normalize_embeddings': self.config_manager.get('retrieval.embedding.normalize_embeddings', True)
            },
            'collections': self.config_manager.get('embedding.collections', [])
        }
        
        self.retriever = ChromaDBRetriever(retriever_config)
        logger.info("✅ 多集合检索器初始化完成")
    
    def _read_chunks_from_folder(self, folder_path: Path, doc_name: str) -> List[Dict[str, Any]]:
        """从文件夹读取所有分块"""
        chunks = []

        for chunk_file in folder_path.glob("*.md"):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 解析YAML前置元数据和内容
                yaml_metadata = {}
                actual_content = content

                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1].strip()
                        actual_content = parts[2].strip()

                        # 解析YAML元数据
                        for line in yaml_content.split('\n'):
                            line = line.strip()
                            if ':' in line:
                                key, value = line.split(':', 1)
                                yaml_metadata[key.strip()] = value.strip()

                # 提取源文档信息
                source_document = (
                    yaml_metadata.get('源文档') or
                    yaml_metadata.get('源文件') or
                    doc_name
                )

                # 创建分块数据
                chunk_data = {
                    'content': actual_content,
                    'metadata': {
                        'document': doc_name,
                        'source_document': source_document,
                        'file_path': str(chunk_file),
                        'chunk_id': chunk_file.stem,
                        **yaml_metadata  # 包含所有YAML元数据
                    },
                    'id': f"{doc_name}_{chunk_file.stem}"
                }

                chunks.append(chunk_data)

            except Exception as e:
                logger.warning(f"⚠️ 读取分块文件失败 {chunk_file}: {e}")

        return chunks
    
    def _add_chunks_to_collection(self, chunks: List[Dict[str, Any]], collection_id: str, doc_name: str):
        """分批添加分块到集合"""
        batch_size = 30  # 减小批处理大小
        total_chunks = len(chunks)
        total_batches = (total_chunks + batch_size - 1) // batch_size
        
        for i in range(0, total_chunks, batch_size):
            end_idx = min(i + batch_size, total_chunks)
            batch_chunks = chunks[i:end_idx]
            
            current_batch = (i // batch_size) + 1
            logger.info(f"  📦 处理批次 {current_batch}/{total_batches} ({len(batch_chunks)} 个分块)")
            
            # 准备批次数据
            documents = [chunk['content'] for chunk in batch_chunks]
            metadatas = [chunk['metadata'] for chunk in batch_chunks]
            ids = [chunk['id'] for chunk in batch_chunks]
            
            try:
                # 添加到集合
                self.retriever.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    collection_id=collection_id
                )
                
                logger.info(f"    ✅ 批次 {current_batch} 添加成功")
                
            except Exception as e:
                logger.error(f"    ❌ 批次 {current_batch} 添加失败: {e}")
                # 继续处理下一批次
        
        logger.info(f"✅ {doc_name} → {collection_id} 集合完成 ({total_chunks} 个分块)")
    
    def _determine_collection_id(self, doc_name: str) -> str:
        """确定文档应该存储到哪个集合"""
        
        # 精确匹配
        if doc_name in self.doc_to_collection_mapping:
            return self.doc_to_collection_mapping[doc_name]
        
        # 模糊匹配
        doc_lower = doc_name.lower()
        
        if '人民银行' in doc_name or '金融统计' in doc_name:
            return 'pboc_statistics'
        elif '1104' in doc_name:
            if '2024' in doc_name:
                return 'report_1104_2024'
            elif '2022' in doc_name:
                return 'report_1104_2022'
            else:
                return 'report_1104_2024'  # 默认最新版
        elif 'east' in doc_lower:
            if '元数据' in doc_name or 'metadata' in doc_lower:
                return 'east_metadata'
            else:
                return 'east_data_structure'
        elif '一表通' in doc_name:
            if '映射' in doc_name or 'mapping' in doc_lower:
                return 'ybt_product_mapping'
            else:
                return 'ybt_data_structure'
        else:
            logger.warning(f"⚠️ 未知文档类型，存储到默认集合: {doc_name}")
            return 'default'
    
    def _verify_build(self):
        """验证构建结果"""
        logger.info("🔍 验证构建结果...")
        
        try:
            stats = self.retriever.get_stats()
            
            logger.info("📊 构建后统计:")
            logger.info(f"  总文档数: {stats['total_documents']}")
            
            for collection_id, collection_stats in stats['collections'].items():
                count = collection_stats['document_count']
                status = collection_stats['status']
                logger.info(f"  集合 {collection_id}: {count} 个文档 ({status})")
            
            if stats['total_documents'] > 0:
                logger.info("✅ 数据库构建验证通过")
            else:
                logger.warning("⚠️ 数据库为空，请检查分块文件")
                
        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")

def main():
    """主函数"""
    print("🎯 CategoryRAG多集合数据库构建工具")
    print("=" * 50)
    
    # 检查分块文件是否存在
    chunks_dir = Path("data/processed_docs/chunks")
    if not chunks_dir.exists():
        print(f"\n❌ 未找到分块目录: {chunks_dir}")
        return
    
    print(f"📂 找到分块目录: {chunks_dir}")
    
    # 列出可用文档
    doc_folders = [f for f in chunks_dir.iterdir() if f.is_dir()]
    print(f"📚 发现 {len(doc_folders)} 个文档类型:")
    for folder in doc_folders:
        chunk_count = len(list(folder.glob("*.md")))
        print(f"  - {folder.name}: {chunk_count} 个分块")
    
    # 确认重建
    response = input(f"\n⚠️ 这将重新构建数据库。是否继续？(y/N): ")
    if response.lower() != 'y':
        print("❌ 重建已取消")
        return
    
    try:
        builder = CollectionDatabaseBuilder()
        success = builder.build()
        
        if success:
            print("\n🎉 多集合数据库重建完成！")
            print("💡 现在可以使用新的多库智能检索功能了")
        else:
            print("\n❌ 重建失败，请检查日志")
        
    except Exception as e:
        print(f"\n❌ 重建失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
