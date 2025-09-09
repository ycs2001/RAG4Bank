#!/usr/bin/env python3
"""
文档目录提取脚本
用于批量或单独提取文档的目录结构
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.config import EnhancedConfigManager
from src.core.document_preprocessor import DocumentPreprocessor
from src.llm.qwen_llm import QwenLLM

def setup_logging(verbose: bool = False):
    """设置日志配置"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/document_extraction.log')
        ]
    )

def extract_single_document(document_id: str, config_manager: EnhancedConfigManager,
                          preprocessor: DocumentPreprocessor) -> bool:
    """
    提取单个文档的目录
    
    Args:
        document_id: 文档ID
        config_manager: 配置管理器
        preprocessor: 文档预处理器
        
    Returns:
        是否成功
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 获取文档配置
        toc_config = config_manager.get('documents.toc', {})
        if document_id not in toc_config:
            logger.error(f"❌ 文档ID不存在: {document_id}")
            return False
        
        doc_info = toc_config[document_id]
        file_path = doc_info.get('file_path')
        
        if not file_path:
            logger.error(f"❌ 文档 {document_id} 缺少file_path配置")
            return False
        
        if not Path(file_path).exists():
            logger.error(f"❌ 文档文件不存在: {file_path}")
            return False
        
        logger.info(f"🔍 开始提取文档目录: {document_id}")
        logger.info(f"📁 文件路径: {file_path}")
        
        # 执行目录提取
        result = preprocessor.extract_document_toc(document_id, file_path)
        
        if result.get('status') == 'completed':
            chapters_count = len(result.get('chapters', []))
            confidence = result.get('confidence', 0.0)
            logger.info(f"✅ 目录提取成功: {document_id}")
            logger.info(f"📋 提取到 {chapters_count} 个章节")
            logger.info(f"🎯 置信度: {confidence:.2f}")
            return True
        else:
            logger.error(f"❌ 目录提取失败: {document_id}")
            logger.error(f"错误信息: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 处理文档 {document_id} 时发生异常: {e}")
        return False

def extract_all_documents(config_manager: EnhancedConfigManager,
                         preprocessor: DocumentPreprocessor,
                         force: bool = False) -> dict:
    """
    批量提取所有文档的目录
    
    Args:
        config_manager: 配置管理器
        preprocessor: 文档预处理器
        force: 是否强制重新提取已完成的文档
        
    Returns:
        处理结果统计
    """
    logger = logging.getLogger(__name__)
    
    toc_config = config_manager.get('documents.toc', {})
    if not toc_config:
        logger.warning("⚠️ 没有配置任何文档")
        return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
    
    results = {
        'total': len(toc_config),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'details': {}
    }
    
    logger.info(f"🚀 开始批量处理 {results['total']} 个文档")
    
    for i, (document_id, doc_info) in enumerate(toc_config.items(), 1):
        logger.info(f"\n📄 处理文档 {i}/{results['total']}: {document_id}")
        
        # 检查是否需要跳过
        extraction_status = doc_info.get('extraction_status', 'pending')
        if extraction_status == 'completed' and not force:
            logger.info(f"⏭️ 跳过已完成的文档: {document_id}")
            results['skipped'] += 1
            results['details'][document_id] = 'skipped'
            continue
        
        # 执行提取
        success = extract_single_document(document_id, config_manager, preprocessor)
        
        if success:
            results['success'] += 1
            results['details'][document_id] = 'success'
        else:
            results['failed'] += 1
            results['details'][document_id] = 'failed'
        
        # 显示进度
        progress = (i / results['total']) * 100
        logger.info(f"📊 进度: {progress:.1f}% ({i}/{results['total']})")
    
    return results

def print_summary(results: dict):
    """打印处理结果摘要"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "="*50)
    logger.info("📊 处理结果摘要")
    logger.info("="*50)
    logger.info(f"总文档数: {results['total']}")
    logger.info(f"成功: {results['success']}")
    logger.info(f"失败: {results['failed']}")
    logger.info(f"跳过: {results['skipped']}")
    
    if results.get('details'):
        logger.info("\n📋 详细结果:")
        for doc_id, status in results['details'].items():
            status_icon = {
                'success': '✅',
                'failed': '❌', 
                'skipped': '⏭️'
            }.get(status, '❓')
            logger.info(f"  {status_icon} {doc_id}: {status}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='文档目录提取工具')
    parser.add_argument('--document', '-d', type=str, help='指定要处理的文档ID')
    parser.add_argument('--all', '-a', action='store_true', help='处理所有文档')
    parser.add_argument('--force', '-f', action='store_true', help='强制重新处理已完成的文档')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细日志输出')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用的文档ID')
    parser.add_argument('--pipeline', '-p', action='store_true', help='运行自动化Pipeline（推荐）')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Pipeline模式
        if args.pipeline:
            logger.info("🚀 启动自动化Pipeline模式...")
            import sys
            from pathlib import Path

            # 添加脚本目录到路径
            script_dir = Path(__file__).resolve().parent
            sys.path.append(str(script_dir))

            from toc_extraction_pipeline import TOCExtractionPipeline

            pipeline = TOCExtractionPipeline()
            target_docs = [args.document] if args.document else None

            success = pipeline.run_full_pipeline(
                target_docs=target_docs if not args.all else None,
                test_semantic=True
            )

            if success:
                logger.info("🎉 Pipeline执行成功！")
            else:
                logger.error("💥 Pipeline执行失败！")
                sys.exit(1)
            return

        # 初始化配置管理器
        logger.info("🔧 初始化配置管理器...")
        config_manager = EnhancedConfigManager()

        # 列出文档ID
        if args.list:
            toc_config = config_manager.get('documents.toc', {})
            logger.info("📋 可用的文档ID:")
            for doc_id, doc_info in toc_config.items():
                status = doc_info.get('extraction_status', 'pending')
                title = doc_info.get('title', '未知标题')
                logger.info(f"  • {doc_id}: {title} (状态: {status})")
            return
        
        # 初始化LLM
        logger.info("🤖 初始化LLM...")
        default_provider = config_manager.get('llm.default_provider', 'deepseek')

        if default_provider == 'deepseek':
            from src.llm.deepseek_llm import DeepSeekLLM
            deepseek_config = config_manager.get('llm.deepseek', {})
            llm = DeepSeekLLM(deepseek_config)
        else:
            # 默认使用Qwen
            qwen_config = config_manager.get('llm.qwen', {})
            llm = QwenLLM(qwen_config)
        
        # 初始化文档预处理器
        logger.info("📄 初始化文档预处理器...")
        preprocessor = DocumentPreprocessor(config_manager, llm)
        
        if not preprocessor.enabled:
            logger.error("❌ 文档预处理器未启用，请检查配置")
            return
        
        # 执行处理
        if args.document:
            # 处理单个文档
            success = extract_single_document(args.document, config_manager, preprocessor)
            if success:
                logger.info("🎉 文档处理完成")
            else:
                logger.error("💥 文档处理失败")
                sys.exit(1)
                
        elif args.all:
            # 批量处理
            results = extract_all_documents(config_manager, preprocessor, args.force)
            print_summary(results)
            
            if results['failed'] > 0:
                logger.warning(f"⚠️ 有 {results['failed']} 个文档处理失败")
                sys.exit(1)
            else:
                logger.info("🎉 所有文档处理完成")
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断操作")
    except Exception as e:
        logger.error(f"💥 程序执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
