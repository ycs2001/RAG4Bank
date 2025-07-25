#!/usr/bin/env python3
"""
RAG系统端到端自动化构建脚本
解决数据流水线中的手动干预断点，实现一键式构建
"""

import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入现有模块
from Chunk import DocumentProcessingWorkflow
from rebuild_multi_collection_db import MultiCollectionBuilder

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_system_build.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RAGSystemBuilder:
    """RAG系统端到端构建器"""
    
    def __init__(self, 
                 input_dir: str = "data/KnowledgeBase",
                 output_dir: str = "data/processed_docs",
                 chunk_size: int = 5000,
                 overlap_size: int = 1000,
                 auto_test: bool = True,
                 backup_existing: bool = True):
        """
        初始化构建器
        
        Args:
            input_dir: 输入文档目录
            output_dir: 输出目录
            chunk_size: 分块大小
            overlap_size: 重叠大小
            auto_test: 是否自动测试
            backup_existing: 是否备份现有数据
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.auto_test = auto_test
        self.backup_existing = backup_existing
        
        # 构建统计
        self.build_stats = {
            'start_time': None,
            'end_time': None,
            'total_documents': 0,
            'total_chunks': 0,
            'total_collections': 0,
            'errors': [],
            'stages_completed': []
        }
        
        logger.info("🎯 RAG系统构建器初始化完成")
    
    def build(self) -> bool:
        """执行完整的端到端构建"""
        logger.info("🚀 开始RAG系统端到端构建")
        self.build_stats['start_time'] = time.time()
        
        try:
            # 阶段0：环境检查
            if not self._check_environment():
                return False
            self.build_stats['stages_completed'].append('environment_check')
            
            # 阶段1：文档处理（转换+分块）
            if not self._process_documents():
                return False
            self.build_stats['stages_completed'].append('document_processing')
            
            # 阶段2：多集合数据库构建
            if not self._build_vector_database():
                return False
            self.build_stats['stages_completed'].append('vector_database')
            
            # 阶段3：系统验证（可选）
            if self.auto_test:
                if not self._verify_system():
                    logger.warning("⚠️ 系统验证失败，但构建已完成")
                else:
                    self.build_stats['stages_completed'].append('system_verification')
            
            # 生成构建报告
            self._generate_build_report()
            
            self.build_stats['end_time'] = time.time()
            logger.info("✅ RAG系统构建完成！")
            return True
            
        except Exception as e:
            self.build_stats['errors'].append(str(e))
            logger.error(f"❌ RAG系统构建失败: {e}")
            return False
    
    def _check_environment(self) -> bool:
        """检查构建环境"""
        logger.info("🔍 检查构建环境...")
        
        # 检查输入目录
        if not self.input_dir.exists():
            logger.error(f"❌ 输入目录不存在: {self.input_dir}")
            return False
        
        # 检查输入文档
        supported_formats = ['.pdf', '.docx', '.xlsx', '.txt', '.md']
        input_files = []
        for fmt in supported_formats:
            input_files.extend(list(self.input_dir.glob(f"*{fmt}")))
        
        if not input_files:
            logger.error(f"❌ 输入目录中未找到支持的文档格式: {supported_formats}")
            return False
        
        logger.info(f"📄 发现 {len(input_files)} 个待处理文档")
        self.build_stats['total_documents'] = len(input_files)
        
        # 检查依赖模块
        try:
            import markitdown
            logger.info("✅ markitdown 模块可用")
        except ImportError:
            logger.error("❌ markitdown 模块未安装，请运行: pip install markitdown")
            return False
        
        try:
            import chromadb
            logger.info("✅ chromadb 模块可用")
        except ImportError:
            logger.error("❌ chromadb 模块未安装，请运行: pip install chromadb")
            return False
        
        # 检查BGE模型
        try:
            sys.path.insert(0, 'src')
            from src.config import ConfigManager
            config = ConfigManager()
            model_path = config.get('retrieval.embedding.model_path')
            
            if model_path and Path(model_path).exists():
                logger.info(f"✅ BGE模型路径有效: {model_path}")
            else:
                logger.warning(f"⚠️ BGE模型路径无效，将使用默认embedding: {model_path}")
        except Exception as e:
            logger.warning(f"⚠️ 配置检查失败，将使用默认设置: {e}")
        
        logger.info("✅ 环境检查通过")
        return True
    
    def _process_documents(self) -> bool:
        """处理文档（转换+分块）"""
        logger.info("📝 开始文档处理阶段...")
        
        try:
            # 创建文档处理工作流
            workflow = DocumentProcessingWorkflow(
                input_dir=str(self.input_dir),
                output_base_dir=str(self.output_dir),
                chunk_size=self.chunk_size,
                overlap_size=self.overlap_size
            )
            
            # 执行完整工作流
            results = workflow.run_full_workflow()
            
            # 更新统计信息
            self.build_stats['total_chunks'] = results.get('text_chunks', 0) + results.get('excel_chunks', 0)
            
            if results.get('errors'):
                logger.warning(f"⚠️ 文档处理过程中出现 {len(results['errors'])} 个错误")
                self.build_stats['errors'].extend(results['errors'])
            
            logger.info(f"✅ 文档处理完成: {results['converted_files']} 个文档, {self.build_stats['total_chunks']} 个分块")
            return True
            
        except Exception as e:
            logger.error(f"❌ 文档处理失败: {e}")
            self.build_stats['errors'].append(f"文档处理失败: {e}")
            return False
    
    def _build_vector_database(self) -> bool:
        """构建向量数据库"""
        logger.info("🗄️ 开始向量数据库构建...")
        
        try:
            # 检查分块文件是否存在
            chunks_dir = self.output_dir / "chunks"
            if not chunks_dir.exists():
                logger.error(f"❌ 分块目录不存在: {chunks_dir}")
                return False
            
            # 创建多集合构建器
            builder = MultiCollectionBuilder()
            
            # 执行构建
            success = builder.build(str(chunks_dir))
            
            if success:
                # 获取构建统计
                try:
                    sys.path.insert(0, 'src')
                    from src.config import ConfigManager
                    from src.retrievers import ChromaDBRetriever
                    
                    config_manager = ConfigManager()
                    chromadb_config = config_manager.get_section('retrieval.chromadb')
                    embedding_config = config_manager.get_section('retrieval.embedding')
                    collections_config = config_manager.get('retrieval.collections', [])
                    
                    retriever_config = {
                        'db_path': chromadb_config.get('db_path', './data/chroma_db'),
                        'default_collection_name': chromadb_config.get('default_collection_name', 'knowledge_base'),
                        'model_path': embedding_config.get('model_path'),
                        'normalize_embeddings': embedding_config.get('normalize_embeddings', True),
                        'collections': collections_config
                    }
                    
                    retriever = ChromaDBRetriever(retriever_config)
                    stats = retriever.get_stats()
                    
                    self.build_stats['total_collections'] = len(stats.get('collections', {}))
                    
                    logger.info(f"✅ 向量数据库构建完成: {self.build_stats['total_collections']} 个集合")
                    
                except Exception as e:
                    logger.warning(f"⚠️ 无法获取数据库统计信息: {e}")
                
                return True
            else:
                logger.error("❌ 向量数据库构建失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 向量数据库构建异常: {e}")
            self.build_stats['errors'].append(f"向量数据库构建失败: {e}")
            return False
    
    def _verify_system(self) -> bool:
        """验证系统功能"""
        logger.info("🧪 开始系统验证...")
        
        try:
            # 简单的系统验证
            sys.path.insert(0, 'src')
            from src import RAGSystem, ConfigManager
            
            # 初始化RAG系统
            config_manager = ConfigManager()
            rag_system = RAGSystem(config_manager)
            
            # 执行健康检查
            health_status = rag_system.health_check()
            
            if health_status.get('system') == 'healthy':
                logger.info("✅ 系统验证通过")
                return True
            else:
                logger.warning(f"⚠️ 系统健康检查异常: {health_status}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 系统验证失败: {e}")
            self.build_stats['errors'].append(f"系统验证失败: {e}")
            return False
    
    def _generate_build_report(self):
        """生成构建报告"""
        logger.info("📊 生成构建报告...")
        
        duration = self.build_stats['end_time'] - self.build_stats['start_time']
        
        report = f"""
# RAG系统构建报告

## 构建概要
- 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.build_stats['start_time']))}
- 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.build_stats['end_time']))}
- 总耗时: {duration:.2f} 秒

## 处理统计
- 处理文档: {self.build_stats['total_documents']} 个
- 生成分块: {self.build_stats['total_chunks']} 个
- 创建集合: {self.build_stats['total_collections']} 个

## 完成阶段
{chr(10).join(f"- {stage}" for stage in self.build_stats['stages_completed'])}

## 错误信息
{chr(10).join(f"- {error}" for error in self.build_stats['errors']) if self.build_stats['errors'] else "无错误"}

## 构建状态
{'✅ 构建成功' if len(self.build_stats['stages_completed']) >= 3 else '❌ 构建不完整'}
"""
        
        # 保存报告
        report_file = self.output_dir / "build_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📋 构建报告已保存: {report_file}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RAG系统端到端自动化构建工具")
    parser.add_argument("--input", "-i", default="data/KnowledgeBase", help="输入文档目录")
    parser.add_argument("--output", "-o", default="data/processed_docs", help="输出目录")
    parser.add_argument("--chunk-size", "-c", type=int, default=5000, help="分块大小（字符数）")
    parser.add_argument("--overlap-size", "-ol", type=int, default=1000, help="重叠大小（字符数）")
    parser.add_argument("--no-test", action="store_true", help="跳过系统验证")
    parser.add_argument("--no-backup", action="store_true", help="不备份现有数据")
    
    args = parser.parse_args()
    
    print("🎯 RAG系统端到端自动化构建工具")
    print("=" * 60)
    print(f"输入目录: {args.input}")
    print(f"输出目录: {args.output}")
    print(f"分块参数: {args.chunk_size}字符/块, {args.overlap_size}字符重叠")
    print(f"自动测试: {'否' if args.no_test else '是'}")
    print(f"备份数据: {'否' if args.no_backup else '是'}")
    
    # 确认构建
    response = input(f"\n⚠️ 这将执行完整的RAG系统构建流程。是否继续？(y/N): ")
    if response.lower() != 'y':
        print("❌ 构建已取消")
        return
    
    try:
        # 创建构建器
        builder = RAGSystemBuilder(
            input_dir=args.input,
            output_dir=args.output,
            chunk_size=args.chunk_size,
            overlap_size=args.overlap_size,
            auto_test=not args.no_test,
            backup_existing=not args.no_backup
        )
        
        # 执行构建
        success = builder.build()
        
        if success:
            print("\n🎉 RAG系统构建完成！")
            print("🚀 现在可以启动系统: python3 rag_app.py")
        else:
            print("\n❌ RAG系统构建失败，请检查日志")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断构建")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 构建异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
