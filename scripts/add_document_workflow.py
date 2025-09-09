#!/usr/bin/env python3
"""
CategoryRAG文档添加自动化工作流
一键完成新文档的处理、向量化和集成
"""

import sys
import time
import json
import yaml
import logging
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.config import EnhancedConfigManager
from src.core.document_preprocessor import DocumentPreprocessor
from src.llm.deepseek_llm import DeepSeekLLM
from src.retrievers import ChromaDBRetriever

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/add_document.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DocumentAddResult:
    """文档添加结果"""
    doc_name: str
    file_path: str
    status: str
    chunks_count: int
    collection_id: str
    processing_time: float
    error_message: Optional[str] = None

class DocumentAddWorkflow:
    """文档添加工作流"""
    
    def __init__(self):
        """初始化工作流"""
        self.config_manager = EnhancedConfigManager()
        self.project_root = project_root
        self.raw_docs_dir = self.project_root / "data" / "raw_docs"
        self.processed_docs_dir = self.project_root / "data" / "processed_docs"
        self.chunks_dir = self.processed_docs_dir / "chunks"
        self.toc_dir = self.project_root / "data" / "toc"
        
        # 确保目录存在
        self.raw_docs_dir.mkdir(parents=True, exist_ok=True)
        self.processed_docs_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.toc_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📁 工作流目录结构已准备完成")
    
    def add_document(self, file_path: str, collection_config: Optional[Dict] = None) -> DocumentAddResult:
        """
        添加单个文档到系统
        
        Args:
            file_path: 文档文件路径
            collection_config: 集合配置信息
            
        Returns:
            DocumentAddResult: 处理结果
        """
        start_time = time.time()
        file_path = Path(file_path)
        doc_name = file_path.stem
        
        logger.info(f"🚀 开始处理文档: {doc_name}")
        
        try:
            # 步骤1: 复制文档到raw_docs目录
            if not file_path.parent == self.raw_docs_dir:
                target_path = self.raw_docs_dir / file_path.name
                shutil.copy2(file_path, target_path)
                logger.info(f"📋 文档已复制到: {target_path}")
                file_path = target_path
            
            # 步骤2: 文档处理和分块
            chunks_count = self._process_document(file_path)
            
            # 步骤3: TOC提取
            self._extract_toc(file_path)
            
            # 步骤4: 向量化和数据库更新
            collection_id = self._update_database(doc_name, collection_config)
            
            # 步骤5: 更新配置文件
            self._update_config(doc_name, collection_id, collection_config)
            
            processing_time = time.time() - start_time
            
            result = DocumentAddResult(
                doc_name=doc_name,
                file_path=str(file_path),
                status="success",
                chunks_count=chunks_count,
                collection_id=collection_id,
                processing_time=processing_time
            )
            
            logger.info(f"✅ 文档添加完成: {doc_name} ({processing_time:.2f}秒)")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"❌ 文档添加失败: {doc_name} - {error_msg}")
            
            return DocumentAddResult(
                doc_name=doc_name,
                file_path=str(file_path),
                status="failed",
                chunks_count=0,
                collection_id="",
                processing_time=processing_time,
                error_message=error_msg
            )
    
    def _process_document(self, file_path: Path) -> int:
        """处理文档并生成分块"""
        logger.info(f"📄 开始处理文档: {file_path.name}")
        
        # 调用现有的文档处理器
        from document_processor import DocumentProcessingWorkflow

        processor = DocumentProcessingWorkflow(
            input_dir=str(self.raw_docs_dir),
            output_base_dir=str(self.processed_docs_dir)
        )

        # 处理单个文档
        result = processor.process_single_document(str(file_path))
        if result['status'] != 'success':
            raise Exception(f"文档处理失败: {result.get('message', '未知错误')}")
        
        # 统计生成的分块数量
        doc_name = file_path.stem
        doc_chunks_dir = self.chunks_dir / doc_name
        
        if doc_chunks_dir.exists():
            chunks_count = len(list(doc_chunks_dir.glob("*.md")))
            logger.info(f"📊 生成分块数量: {chunks_count}")
            return chunks_count
        else:
            logger.warning(f"⚠️ 未找到分块目录: {doc_chunks_dir}")
            return 0
    
    def _extract_toc(self, file_path: Path):
        """提取文档目录（仅支持PDF和Word文档）"""
        file_ext = file_path.suffix.lower()

        # 检查文件格式是否支持TOC提取
        if file_ext not in ['.pdf', '.docx', '.doc']:
            logger.info(f"📑 跳过TOC提取: {file_path.name} (不支持的格式: {file_ext})")
            logger.info(f"💡 TOC提取仅支持PDF和Word文档格式")
            return

        logger.info(f"📑 开始提取TOC: {file_path.name}")

        try:
            # 调用TOC提取脚本
            from toc_extraction_pipeline import TOCExtractionPipeline

            toc_pipeline = TOCExtractionPipeline()
            toc_pipeline.process_single_document(str(file_path))

            logger.info(f"✅ TOC提取完成: {file_path.name}")

        except Exception as e:
            logger.warning(f"⚠️ TOC提取失败: {e}")
            logger.info(f"💡 TOC提取失败不会影响文档的正常添加和检索功能")
    
    def _update_database(self, doc_name: str, collection_config: Optional[Dict]) -> str:
        """更新向量数据库"""
        logger.info(f"🗄️ 开始更新数据库: {doc_name}")
        
        # 确定集合ID
        if collection_config and 'collection_id' in collection_config:
            collection_id = collection_config['collection_id']
        else:
            # 生成默认集合ID
            collection_id = doc_name.lower().replace(' ', '_').replace('【', '_').replace('】', '_')
        
        # 调用数据库构建器
        from collection_database_builder import CollectionDatabaseBuilder

        builder = CollectionDatabaseBuilder()

        # 添加新的文档映射
        builder.doc_to_collection_mapping[doc_name] = collection_id

        # 重新构建数据库（自动模式）
        builder.build_auto()
        
        logger.info(f"✅ 数据库更新完成: {collection_id}")
        return collection_id
    
    def _update_config(self, doc_name: str, collection_id: str, collection_config: Optional[Dict]):
        """更新配置文件"""
        logger.info(f"⚙️ 开始更新配置: {doc_name}")
        
        config_path = self.project_root / "config" / "config.yaml"
        
        # 读取现有配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 更新主题分类关键词映射
        if 'topic_classification' not in config:
            config['topic_classification'] = {}
        if 'keyword_mapping' not in config['topic_classification']:
            config['topic_classification']['keyword_mapping'] = {}
        
        # 添加新集合的关键词
        if collection_config and 'keywords' in collection_config:
            keywords = collection_config['keywords']
        else:
            # 使用文档名作为默认关键词
            keywords = [doc_name, collection_id]
        
        config['topic_classification']['keyword_mapping'][collection_id] = keywords
        
        # 更新集合配置
        if 'retrieval' not in config:
            config['retrieval'] = {}
        if 'collections' not in config['retrieval']:
            config['retrieval']['collections'] = {}
        
        collection_name = collection_config.get('name', doc_name) if collection_config else doc_name
        collection_desc = collection_config.get('description', f'{doc_name}相关文档') if collection_config else f'{doc_name}相关文档'
        
        config['retrieval']['collections'][collection_id] = {
            'name': collection_name,
            'description': collection_desc,
            'enabled': True
        }
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 配置更新完成: {collection_id}")
    
    def interactive_add(self):
        """交互式添加文档"""
        print("🎯 CategoryRAG文档添加工具")
        print("=" * 50)
        
        # 获取文档路径
        while True:
            file_path = input("📁 请输入文档路径: ").strip()
            if not file_path:
                print("❌ 路径不能为空")
                continue
            
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"❌ 文件不存在: {file_path}")
                continue
            
            if file_path.suffix.lower() not in ['.docx', '.doc', '.pdf', '.xlsx', '.xls']:
                print(f"❌ 不支持的文件格式: {file_path.suffix}")
                print(f"💡 支持的格式: PDF (.pdf), Word (.docx, .doc), Excel (.xlsx, .xls)")
                continue
            
            break
        
        # 获取集合配置
        print(f"\n📚 配置文档集合信息:")
        collection_id = input("集合ID (留空自动生成): ").strip()
        collection_name = input("集合名称: ").strip()
        collection_desc = input("集合描述: ").strip()
        keywords_input = input("关键词 (用逗号分隔): ").strip()
        
        collection_config = {}
        if collection_id:
            collection_config['collection_id'] = collection_id
        if collection_name:
            collection_config['name'] = collection_name
        if collection_desc:
            collection_config['description'] = collection_desc
        if keywords_input:
            collection_config['keywords'] = [k.strip() for k in keywords_input.split(',')]
        
        # 执行添加
        print(f"\n🚀 开始添加文档...")
        result = self.add_document(str(file_path), collection_config)
        
        # 显示结果
        print(f"\n📊 处理结果:")
        print(f"   状态: {'✅ 成功' if result.status == 'success' else '❌ 失败'}")
        print(f"   文档: {result.doc_name}")
        print(f"   分块数: {result.chunks_count}")
        print(f"   集合ID: {result.collection_id}")
        print(f"   处理时间: {result.processing_time:.2f}秒")
        
        if result.error_message:
            print(f"   错误信息: {result.error_message}")
        
        if result.status == "success":
            print(f"\n🎉 文档添加成功！请重启CategoryRAG系统以使用新文档。")
            print(f"   重启命令: python3 start.py")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CategoryRAG文档添加工具")
    parser.add_argument("--file", "-f", help="要添加的文档路径")
    parser.add_argument("--collection-id", help="集合ID")
    parser.add_argument("--collection-name", help="集合名称")
    parser.add_argument("--collection-desc", help="集合描述")
    parser.add_argument("--keywords", help="关键词，用逗号分隔")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式模式")
    
    args = parser.parse_args()
    
    workflow = DocumentAddWorkflow()
    
    if args.interactive or not args.file:
        workflow.interactive_add()
    else:
        collection_config = {}
        if args.collection_id:
            collection_config['collection_id'] = args.collection_id
        if args.collection_name:
            collection_config['name'] = args.collection_name
        if args.collection_desc:
            collection_config['description'] = args.collection_desc
        if args.keywords:
            collection_config['keywords'] = [k.strip() for k in args.keywords.split(',')]
        
        result = workflow.add_document(args.file, collection_config)
        
        if result.status == "success":
            print(f"✅ 文档添加成功: {result.doc_name}")
        else:
            print(f"❌ 文档添加失败: {result.error_message}")
            sys.exit(1)

if __name__ == "__main__":
    main()
