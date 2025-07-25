"""
自动化文档处理工作流程主脚本
整合文档转换、文本分块、Excel分块等功能
"""

import sys
import logging
import argparse
import shutil
from pathlib import Path
from typing import Dict

# 导入自定义模块
from document_converter import DocumentConverter
from text_chunker import TextChunker
from excel_chunker import ExcelChunker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_processing.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DocumentProcessingWorkflow:
    """文档处理工作流程类"""

    def __init__(self, input_dir: str = "KnowledgeBase", output_base_dir: str = "processed_documents",
                 chunk_size: int = 5000, overlap_size: int = 1000):
        """
        初始化工作流程

        Args:
            input_dir: 输入文档目录
            output_base_dir: 输出基础目录
            chunk_size: 文本分块大小（字符数）
            overlap_size: 分块重叠大小（字符数）
        """
        self.input_dir = Path(input_dir)
        self.output_base_dir = Path(output_base_dir)

        # 创建输出目录结构（统一切块文件夹）
        self.converted_dir = self.output_base_dir / "converted_markdown"
        self.chunks_dir = self.output_base_dir / "chunks"  # 统一的切块文件夹

        # 创建所有输出目录
        for dir_path in [self.converted_dir, self.chunks_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 初始化处理器
        self.converter = DocumentConverter(str(self.converted_dir))
        self.text_chunker = TextChunker(chunk_size=chunk_size, overlap_size=overlap_size)
        self.excel_chunker = ExcelChunker(chunk_size=40)

        # 处理结果统计
        self.processing_stats = {
            'converted_files': 0,
            'text_chunks': 0,
            'excel_chunks': 0,
            'errors': []
        }

    def run_full_workflow(self) -> Dict:
        """
        运行完整的文档处理工作流程

        Returns:
            处理结果统计
        """
        logger.info("开始执行文档处理工作流程")
        logger.info(f"输入目录: {self.input_dir}")
        logger.info(f"输出目录: {self.output_base_dir}")

        try:
            # 第零阶段：清理旧分块文件
            logger.info("=" * 50)
            logger.info("第零阶段：清理旧分块文件")
            self._clean_old_chunks()

            # 第一阶段：文档格式转换
            logger.info("=" * 50)
            logger.info("第一阶段：文档格式转换")
            conversion_results = self._convert_documents()

            # 第二阶段：文档分块处理
            logger.info("=" * 50)
            logger.info("第二阶段：文档分块处理")
            self._process_chunks(conversion_results)

            # 生成处理报告
            logger.info("=" * 50)
            logger.info("生成处理报告")
            try:
                self._generate_report()
            except Exception as e:
                logger.warning(f"报告生成失败，但不影响主要功能: {str(e)}")
                # 不将报告错误计入主要错误统计

            logger.info("文档处理工作流程完成")
            return self.processing_stats

        except Exception as e:
            error_msg = f"工作流程执行失败: {str(e)}"
            logger.error(error_msg)
            self.processing_stats['errors'].append(error_msg)
            return self.processing_stats

    def _clean_old_chunks(self):
        """
        清理旧的分块文件（按文档归类版）
        """
        if self.chunks_dir.exists():
            # 删除chunks目录中的所有.md文件（直接在根目录的文件）
            for md_file in self.chunks_dir.glob("*.md"):
                try:
                    md_file.unlink()
                    logger.debug(f"删除旧分块文件: {md_file.name}")
                except Exception as e:
                    logger.warning(f"删除文件失败 {md_file.name}: {str(e)}")

            # 删除所有子目录及其内容
            for subdir in self.chunks_dir.iterdir():
                if subdir.is_dir():
                    # 删除子目录中的所有.md文件
                    for md_file in subdir.glob("*.md"):
                        try:
                            md_file.unlink()
                            logger.debug(f"删除旧分块文件: {subdir.name}/{md_file.name}")
                        except Exception as e:
                            logger.warning(f"删除文件失败 {subdir.name}/{md_file.name}: {str(e)}")

                    # 删除子目录（无论是否为空）
                    try:
                        subdir.rmdir()
                        logger.debug(f"删除文档目录: {subdir.name}")
                    except Exception as e:
                        logger.warning(f"删除目录失败 {subdir.name}: {str(e)}")

            logger.info(f"清理完成: {self.chunks_dir}")
        else:
            logger.info(f"目录不存在，跳过清理: {self.chunks_dir}")

    def _convert_documents(self) -> Dict[str, str]:
        """
        第一阶段：转换所有文档为markdown格式

        Returns:
            转换结果字典 {原文件路径: 转换后文件路径}
        """
        logger.info("开始文档格式转换...")

        # 批量转换文档
        conversion_results = self.converter.convert_directory(str(self.input_dir))

        self.processing_stats['converted_files'] = len(conversion_results)

        if conversion_results:
            logger.info(f"文档转换完成，共转换 {len(conversion_results)} 个文件")
            logger.info("转换结果:")
            for original, converted in conversion_results.items():
                logger.info(f"  ✓ {Path(original).name} -> {Path(converted).name}")
        else:
            logger.warning("没有找到可转换的文档")

        return conversion_results

    def _process_chunks(self, conversion_results: Dict[str, str]):
        """
        第二阶段：处理文档分块

        Args:
            conversion_results: 文档转换结果
        """
        logger.info("开始文档分块处理...")

        # 处理转换后的markdown文档
        for original_file, converted_file in conversion_results.items():
            try:
                original_path = Path(original_file)
                converted_path = Path(converted_file)

                logger.info(f"处理文档: {original_path.name}")

                # 判断原文件类型
                if original_path.suffix.lower() in ['.xlsx', '.xls']:
                    # Excel文件：直接处理原文件
                    self._process_excel_file(str(original_path))
                else:
                    # 文本文档：处理转换后的markdown文件
                    self._process_text_file(str(converted_path), str(original_path))

            except Exception as e:
                error_msg = f"处理文档失败 {Path(original_file).name}: {str(e)}"
                logger.error(error_msg)
                self.processing_stats['errors'].append(error_msg)

    def _process_text_file(self, markdown_file: str, original_file: str):
        """
        处理文本文档分块（按文档归类版）

        Args:
            markdown_file: 转换后的markdown文件路径
            original_file: 原始文件路径
        """
        try:
            original_path = Path(original_file)
            doc_name = original_path.stem  # 不包含扩展名的文件名

            # 在chunks文件夹下为每个文档创建子文件夹
            doc_chunks_dir = self.chunks_dir / doc_name
            doc_chunks_dir.mkdir(exist_ok=True)

            # 读取markdown内容
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 按固定大小分块
            chunks = self.text_chunker.chunk_by_sections(content, original_path.name)

            if chunks:
                # 保存分块到文档专用子文件夹
                self.text_chunker.save_chunks(chunks, str(doc_chunks_dir))
                self.processing_stats['text_chunks'] += len(chunks)

                logger.info(f"文本分块完成: {original_path.name}, 生成 {len(chunks)} 个分块")
            else:
                logger.warning(f"文档没有生成有效分块: {original_path.name}")

        except Exception as e:
            raise Exception(f"文本分块处理失败: {str(e)}")

    def _process_excel_file(self, excel_file: str):
        """
        处理Excel文档分块（按文档归类版）

        Args:
            excel_file: Excel文件路径
        """
        try:
            excel_path = Path(excel_file)
            doc_name = excel_path.stem  # 不包含扩展名的文件名

            # 在chunks文件夹下为每个Excel文档创建子文件夹
            doc_chunks_dir = self.chunks_dir / doc_name
            doc_chunks_dir.mkdir(exist_ok=True)

            # 处理Excel文件
            chunks = self.excel_chunker.process_excel_file(excel_file)

            if chunks:
                # 保存分块到文档专用子文件夹
                self.excel_chunker.save_chunks(chunks, str(doc_chunks_dir))
                self.processing_stats['excel_chunks'] += len(chunks)

                logger.info(f"Excel分块完成: {excel_path.name}, 生成 {len(chunks)} 个分块")
            else:
                logger.warning(f"Excel文件没有生成有效分块: {excel_path.name}")

        except Exception as e:
            raise Exception(f"Excel分块处理失败: {str(e)}")

    def _generate_report(self):
        """生成处理报告（简化版）"""
        report_file = self.output_base_dir / "processing_report.md"

        # 简化的报告内容
        report_content = f"""# 文档处理工作流程报告

## 处理统计

- **转换文件数**: {self.processing_stats['converted_files']}
- **文本分块数**: {self.processing_stats['text_chunks']}
- **Excel分块数**: {self.processing_stats['excel_chunks']}
- **错误数量**: {len(self.processing_stats['errors'])}

## 输出目录

- **转换文件**: {self.converted_dir}
- **分块文件**: {self.chunks_dir}

## 分块说明

所有文档分块都按文档归类存储在chunks目录下，每个源文档有独立的子文件夹。
分块采用固定大小策略：5000字符/块，1000字符重叠。
"""

        if self.processing_stats['errors']:
            report_content += "\n## 错误信息\n\n"
            for i, error in enumerate(self.processing_stats['errors'], 1):
                report_content += f"{i}. {error}\n"

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"处理报告已生成: {report_file}")

        # 打印摘要
        logger.info("处理摘要:")
        logger.info(f"  转换文件: {self.processing_stats['converted_files']} 个")
        logger.info(f"  文本分块: {self.processing_stats['text_chunks']} 个")
        logger.info(f"  Excel分块: {self.processing_stats['excel_chunks']} 个")
        if self.processing_stats['errors']:
            logger.warning(f"  错误: {len(self.processing_stats['errors'])} 个")

    def process_single_document(self, file_path: str) -> Dict:
        """
        处理单个文档

        Args:
            file_path: 文档文件路径

        Returns:
            Dict: 处理结果
        """
        file_path = Path(file_path)
        logger.info(f"🚀 开始处理单个文档: {file_path.name}")

        if not file_path.exists():
            logger.error(f"❌ 文件不存在: {file_path}")
            return {"status": "error", "message": "文件不存在"}

        try:
            # 确定文档类型和处理方法
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Excel文档处理
                result = self._process_single_excel_document(file_path)
            else:
                # 其他文档处理
                result = self._process_single_regular_document(file_path)

            logger.info(f"✅ 单个文档处理完成: {file_path.name}")
            return result

        except Exception as e:
            logger.error(f"❌ 处理文档失败 {file_path.name}: {e}")
            return {"status": "error", "message": str(e)}

    def _process_single_regular_document(self, file_path: Path) -> Dict:
        """处理单个常规文档（非Excel）"""
        doc_name = file_path.stem

        # 步骤1: 文档转换
        logger.info(f"📄 转换文档: {file_path.name}")
        converted_file = self.converter.convert_document(str(file_path), str(self.converted_dir))

        if not converted_file:
            raise Exception("文档转换失败")

        # 步骤2: 文本分块
        logger.info(f"✂️ 分块文档: {file_path.name}")
        chunks_output_dir = self.chunks_dir / doc_name
        chunks_output_dir.mkdir(parents=True, exist_ok=True)

        chunk_files = self.text_chunker.chunk_document(
            converted_file,
            str(chunks_output_dir)
        )

        return {
            "status": "success",
            "document": doc_name,
            "converted_file": converted_file,
            "chunks_count": len(chunk_files),
            "chunks_dir": str(chunks_output_dir)
        }

    def _process_single_excel_document(self, file_path: Path) -> Dict:
        """处理单个Excel文档"""
        doc_name = file_path.stem

        # Excel文档直接分块
        logger.info(f"📊 分块Excel文档: {file_path.name}")
        chunks_output_dir = self.chunks_dir / doc_name
        chunks_output_dir.mkdir(parents=True, exist_ok=True)

        chunk_files = self.excel_chunker.chunk_excel(
            str(file_path),
            str(chunks_output_dir)
        )

        return {
            "status": "success",
            "document": doc_name,
            "chunks_count": len(chunk_files),
            "chunks_dir": str(chunks_output_dir)
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='自动化文档处理工作流程')
    parser.add_argument('--input', '-i', default='KnowledgeBase',
                       help='输入文档目录 (默认: KnowledgeBase)')
    parser.add_argument('--output', '-o', default='processed_documents',
                       help='输出目录 (默认: processed_documents)')
    parser.add_argument('--chunk-size', '-c', type=int, default=5000,
                       help='文本分块大小（字符数，默认: 5000）')
    parser.add_argument('--overlap-size', '-ol', type=int, default=1000,
                       help='文本分块重叠大小（字符数，默认: 1000）')
    parser.add_argument('--excel-chunk-size', '-ec', type=int, default=40,
                       help='Excel分块大小（行数，默认: 40）')

    args = parser.parse_args()

    # 检查输入目录
    if not Path(args.input).exists():
        logger.error(f"输入目录不存在: {args.input}")
        sys.exit(1)

    # 创建工作流程实例
    workflow = DocumentProcessingWorkflow(
        input_dir=args.input,
        output_base_dir=args.output,
        chunk_size=args.chunk_size,
        overlap_size=args.overlap_size
    )

    # 设置Excel分块大小
    workflow.excel_chunker.chunk_size = args.excel_chunk_size

    # 运行工作流程
    results = workflow.run_full_workflow()

    # 输出最终结果
    print("\n" + "=" * 60)
    print("文档处理工作流程完成!")
    print(f"转换文件: {results['converted_files']} 个")
    print(f"文本分块: {results['text_chunks']} 个")
    print(f"Excel分块: {results['excel_chunks']} 个")
    print(f"分块参数: {args.chunk_size}字符/块, {args.overlap_size}字符重叠")

    if results['errors']:
        print(f"错误: {len(results['errors'])} 个")
        print("详细错误信息请查看日志文件: document_processing.log")

    print(f"输出目录: {workflow.output_base_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()