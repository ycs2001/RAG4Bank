#!/usr/bin/env python3
"""
CategoryRAG文档目录提取自动化Pipeline
一键完成所有文档的目录提取、验证和报告生成
"""

import os
import sys
import time
import json
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.config import EnhancedConfigManager
from src.core.document_preprocessor import DocumentPreprocessor
from src.llm.deepseek_llm import DeepSeekLLM
from src.core.semantic_enhancer import SemanticEnhancer

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/toc_pipeline.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DocumentResult:
    """文档处理结果"""
    doc_id: str
    title: str
    file_path: str
    status: str
    chapters_count: int
    subsections_count: int
    confidence: float
    processing_time: float
    error_message: Optional[str] = None
    table_numbers: List[str] = None

class TOCExtractionPipeline:
    """文档目录提取Pipeline"""
    
    def __init__(self):
        """初始化Pipeline"""
        self.config_manager = ConfigManager()
        self.results: List[DocumentResult] = []
        self.start_time = datetime.now()
        
        # 创建必要的目录
        Path('logs').mkdir(exist_ok=True)
        Path('data/toc').mkdir(parents=True, exist_ok=True)
        
        logger.info("🚀 CategoryRAG文档目录提取Pipeline启动")
        logger.info("=" * 80)
    
    def initialize_components(self) -> bool:
        """初始化系统组件"""
        try:
            logger.info("🔧 初始化系统组件...")
            
            # 初始化DeepSeek LLM
            deepseek_config = self.config_manager.get('llm.deepseek', {})
            if not deepseek_config.get('api_key'):
                logger.error("❌ DeepSeek API密钥未配置")
                return False
            
            self.llm = DeepSeekLLM(deepseek_config)
            logger.info("✅ DeepSeek LLM初始化完成")
            
            # 初始化文档预处理器
            self.preprocessor = DocumentPreprocessor(self.config_manager, self.llm)
            if not self.preprocessor.enabled:
                logger.error("❌ 文档预处理器未启用")
                return False
            
            logger.info("✅ 文档预处理器初始化完成")
            
            # 初始化语义增强器
            self.enhancer = SemanticEnhancer(self.config_manager, self.llm)
            logger.info("✅ 语义增强器初始化完成")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            return False
    
    def cleanup_old_data(self):
        """清理旧的目录数据"""
        logger.info("🧹 清理旧的目录数据...")
        
        toc_dir = Path('data/toc')
        if toc_dir.exists():
            yaml_files = list(toc_dir.glob('*.yaml'))
            json_files = list(toc_dir.glob('*.json'))
            
            for file in yaml_files + json_files:
                try:
                    file.unlink()
                    logger.debug(f"删除文件: {file}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {file}: {e}")
            
            logger.info(f"✅ 清理完成，删除了 {len(yaml_files + json_files)} 个旧文件")
        else:
            logger.info("📁 目录数据文件夹不存在，跳过清理")
    
    def get_configured_documents(self) -> Dict[str, Dict[str, Any]]:
        """获取配置的文档列表"""
        toc_config = self.config_manager.get('documents.toc', {})
        logger.info(f"📋 发现 {len(toc_config)} 个配置的文档")
        
        for doc_id, doc_info in toc_config.items():
            title = doc_info.get('title', '未知标题')
            file_path = doc_info.get('file_path', '未知路径')
            exists = "✅" if Path(file_path).exists() else "❌"
            logger.info(f"  • {doc_id}: {title} {exists}")
        
        return toc_config
    
    def extract_single_document(self, doc_id: str, doc_info: Dict[str, Any]) -> DocumentResult:
        """提取单个文档的目录"""
        title = doc_info.get('title', '未知标题')
        file_path = doc_info.get('file_path', '')
        
        logger.info(f"📄 开始处理: {doc_id} - {title}")
        logger.info(f"📁 文件路径: {file_path}")
        
        start_time = time.time()
        
        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                error_msg = f"文件不存在: {file_path}"
                logger.error(f"❌ {error_msg}")
                return DocumentResult(
                    doc_id=doc_id,
                    title=title,
                    file_path=file_path,
                    status="file_not_found",
                    chapters_count=0,
                    subsections_count=0,
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    error_message=error_msg
                )
            
            # 执行目录提取
            result = self.preprocessor.extract_document_toc(doc_id, file_path)
            processing_time = time.time() - start_time
            
            # 分析结果
            status = result.get('status', 'unknown')
            chapters = result.get('chapters', [])
            confidence = result.get('confidence', 0.0)
            
            # 统计子章节数量和表格编号
            subsections_count = 0
            table_numbers = []
            
            for chapter in chapters:
                subsections = chapter.get('subsections', [])
                subsections_count += len(subsections)
                
                # 提取表格编号
                chapter_num = chapter.get('chapter_num', '')
                if chapter_num and any(c.isdigit() or c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' for c in chapter_num):
                    table_numbers.append(chapter_num)
                
                for subsection in subsections:
                    sub_num = subsection.get('chapter_num', '')
                    if sub_num and any(c.isdigit() or c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' for c in sub_num):
                        table_numbers.append(sub_num)
            
            # 创建结果对象
            doc_result = DocumentResult(
                doc_id=doc_id,
                title=title,
                file_path=file_path,
                status=status,
                chapters_count=len(chapters),
                subsections_count=subsections_count,
                confidence=confidence,
                processing_time=processing_time,
                table_numbers=table_numbers
            )
            
            # 记录结果
            if status == 'completed':
                logger.info(f"✅ 提取成功: {len(chapters)}个章节, {subsections_count}个子项, 置信度: {confidence:.2f}")
                if table_numbers:
                    logger.info(f"📊 识别的表格编号: {table_numbers[:10]}{'...' if len(table_numbers) > 10 else ''}")
            else:
                logger.warning(f"⚠️ 提取状态: {status}, 置信度: {confidence:.2f}")
            
            logger.info(f"⏱️ 处理耗时: {processing_time:.1f}秒")
            
            return doc_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"处理异常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return DocumentResult(
                doc_id=doc_id,
                title=title,
                file_path=file_path,
                status="error",
                chapters_count=0,
                subsections_count=0,
                confidence=0.0,
                processing_time=processing_time,
                error_message=error_msg
            )
    
    def run_extraction_pipeline(self, target_docs: Optional[List[str]] = None) -> bool:
        """运行提取Pipeline"""
        logger.info("🔄 开始批量文档目录提取...")
        
        # 获取要处理的文档
        all_docs = self.get_configured_documents()
        
        if target_docs:
            docs_to_process = {k: v for k, v in all_docs.items() if k in target_docs}
            logger.info(f"🎯 指定处理 {len(docs_to_process)} 个文档")
        else:
            docs_to_process = all_docs
            logger.info(f"📚 处理所有 {len(docs_to_process)} 个文档")
        
        # 逐个处理文档
        for i, (doc_id, doc_info) in enumerate(docs_to_process.items(), 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"📖 处理进度: {i}/{len(docs_to_process)} - {doc_id}")
            logger.info(f"{'='*60}")
            
            result = self.extract_single_document(doc_id, doc_info)
            self.results.append(result)
            
            # 短暂休息，避免API限制
            if i < len(docs_to_process):
                logger.info("⏳ 等待2秒...")
                time.sleep(2)
        
        return True

    def validate_extraction_results(self) -> Dict[str, Any]:
        """验证提取结果质量"""
        logger.info("\n🔍 验证提取结果质量...")
        logger.info("=" * 60)

        validation_report = {
            'total_documents': len(self.results),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'quality_issues': [],
            'statistics': {}
        }

        for result in self.results:
            if result.status == 'completed':
                validation_report['successful_extractions'] += 1

                # 质量检查
                quality_issues = []

                # 检查章节数量
                if result.doc_id.startswith('report_1104') and result.chapters_count < 15:
                    quality_issues.append(f"1104报表章节数量偏少: {result.chapters_count} < 15")

                if result.doc_id == 'pboc_statistics' and result.chapters_count < 20:
                    quality_issues.append(f"人民银行统计制度章节数量偏少: {result.chapters_count} < 20")

                # 检查置信度
                if result.confidence < 0.7:
                    quality_issues.append(f"置信度偏低: {result.confidence:.2f} < 0.7")

                # 检查表格编号
                if result.table_numbers and len(result.table_numbers) < 5:
                    quality_issues.append(f"识别的表格编号偏少: {len(result.table_numbers)} < 5")

                if quality_issues:
                    validation_report['quality_issues'].append({
                        'doc_id': result.doc_id,
                        'issues': quality_issues
                    })

                # 统计信息
                validation_report['statistics'][result.doc_id] = {
                    'chapters': result.chapters_count,
                    'subsections': result.subsections_count,
                    'confidence': result.confidence,
                    'table_numbers_count': len(result.table_numbers) if result.table_numbers else 0,
                    'processing_time': result.processing_time
                }

            else:
                validation_report['failed_extractions'] += 1

        # 输出验证结果
        success_rate = validation_report['successful_extractions'] / validation_report['total_documents'] * 100
        logger.info(f"📊 提取成功率: {success_rate:.1f}% ({validation_report['successful_extractions']}/{validation_report['total_documents']})")

        if validation_report['quality_issues']:
            logger.warning(f"⚠️ 发现 {len(validation_report['quality_issues'])} 个质量问题:")
            for issue in validation_report['quality_issues']:
                logger.warning(f"  • {issue['doc_id']}: {', '.join(issue['issues'])}")
        else:
            logger.info("✅ 所有文档质量检查通过")

        return validation_report

    def generate_summary_report(self, validation_report: Dict[str, Any]):
        """生成汇总报告"""
        logger.info("\n📋 生成处理结果汇总报告...")
        logger.info("=" * 80)

        total_time = (datetime.now() - self.start_time).total_seconds()

        # 控制台报告
        logger.info(f"🕐 Pipeline总耗时: {total_time:.1f}秒")
        logger.info(f"📚 处理文档数量: {len(self.results)}")
        logger.info(f"✅ 成功提取: {validation_report['successful_extractions']}")
        logger.info(f"❌ 提取失败: {validation_report['failed_extractions']}")

        logger.info("\n📊 详细统计:")
        logger.info("-" * 80)
        logger.info(f"{'文档ID':<20} {'章节数':<8} {'子项数':<8} {'置信度':<8} {'表格数':<8} {'耗时(s)':<8} {'状态'}")
        logger.info("-" * 80)

        for result in self.results:
            table_count = len(result.table_numbers) if result.table_numbers else 0
            status_icon = "✅" if result.status == 'completed' else "❌"

            logger.info(f"{result.doc_id:<20} {result.chapters_count:<8} {result.subsections_count:<8} "
                       f"{result.confidence:<8.2f} {table_count:<8} {result.processing_time:<8.1f} {status_icon}")

        # 保存详细报告到文件
        report_data = {
            'pipeline_info': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_duration_seconds': total_time,
                'processed_documents': len(self.results)
            },
            'validation_report': validation_report,
            'detailed_results': []
        }

        for result in self.results:
            report_data['detailed_results'].append({
                'doc_id': result.doc_id,
                'title': result.title,
                'file_path': result.file_path,
                'status': result.status,
                'chapters_count': result.chapters_count,
                'subsections_count': result.subsections_count,
                'confidence': result.confidence,
                'processing_time': result.processing_time,
                'table_numbers': result.table_numbers,
                'error_message': result.error_message
            })

        # 保存报告
        report_file = f"logs/toc_pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 详细报告已保存: {report_file}")

    def test_semantic_enhancement(self) -> bool:
        """测试语义增强功能"""
        logger.info("\n🧠 测试语义增强功能...")
        logger.info("=" * 60)

        try:
            # 重新加载目录数据
            self.enhancer._load_all_toc_data()
            cache_count = len(self.enhancer._toc_cache)

            logger.info(f"📚 目录缓存数量: {cache_count}")

            if cache_count == 0:
                logger.warning("⚠️ 目录缓存为空，语义增强功能可能无法正常工作")
                return False

            # 显示缓存详情
            for doc_id, toc_data in self.enhancer._toc_cache.items():
                chapters = toc_data.get('chapters', [])
                confidence = toc_data.get('confidence', 0.0)
                status = toc_data.get('status', 'unknown')
                logger.info(f"  • {doc_id}: {len(chapters)}个章节, 置信度: {confidence:.2f}, 状态: {status}")

            # 测试查询意图分析
            test_queries = [
                "资本充足率相关的报表有哪些",
                "G01资产负债项目统计表的填报要求",
                "普惠金融领域贷款涉及哪些报送表"
            ]

            logger.info("\n🔍 测试查询意图分析:")
            for query in test_queries:
                try:
                    intent_result = self.enhancer.analyze_query_intent(query)
                    enabled = intent_result.get('enabled', False)
                    confidence = intent_result.get('confidence', 0.0)
                    keywords = intent_result.get('keywords', [])

                    logger.info(f"  查询: {query}")
                    logger.info(f"    启用: {enabled}, 置信度: {confidence:.2f}")
                    logger.info(f"    关键词: {keywords[:3] if keywords else '无'}")
                except Exception as e:
                    logger.error(f"  查询失败: {query} - {e}")

            logger.info("✅ 语义增强功能测试完成")
            return True

        except Exception as e:
            logger.error(f"❌ 语义增强功能测试失败: {e}")
            return False

    def run_full_pipeline(self, target_docs: Optional[List[str]] = None,
                         test_semantic: bool = True) -> bool:
        """运行完整Pipeline"""
        try:
            # 1. 初始化组件
            if not self.initialize_components():
                return False

            # 2. 清理旧数据
            self.cleanup_old_data()

            # 3. 运行提取Pipeline
            if not self.run_extraction_pipeline(target_docs):
                return False

            # 4. 验证结果
            validation_report = self.validate_extraction_results()

            # 5. 生成报告
            self.generate_summary_report(validation_report)

            # 6. 测试语义增强（可选）
            if test_semantic:
                self.test_semantic_enhancement()

            logger.info("\n🎉 Pipeline执行完成！")
            return True

        except Exception as e:
            logger.error(f"❌ Pipeline执行失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CategoryRAG文档目录提取自动化Pipeline')
    parser.add_argument('--pipeline', action='store_true', help='运行完整Pipeline')
    parser.add_argument('--all', action='store_true', help='处理所有配置的文档')
    parser.add_argument('--docs', nargs='+', help='指定要处理的文档ID')
    parser.add_argument('--no-semantic', action='store_true', help='跳过语义增强测试')

    args = parser.parse_args()

    if not args.pipeline:
        print("请使用 --pipeline 参数运行Pipeline")
        print("示例: python3 scripts/toc_extraction_pipeline.py --pipeline --all")
        return

    # 创建Pipeline实例
    pipeline = TOCExtractionPipeline()

    # 确定要处理的文档
    target_docs = None
    if args.docs:
        target_docs = args.docs
    elif not args.all:
        print("请指定 --all 处理所有文档，或使用 --docs 指定特定文档")
        return

    # 运行Pipeline
    success = pipeline.run_full_pipeline(
        target_docs=target_docs,
        test_semantic=not args.no_semantic
    )

    if success:
        print("\n✅ Pipeline执行成功！")
        sys.exit(0)
    else:
        print("\n❌ Pipeline执行失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()
