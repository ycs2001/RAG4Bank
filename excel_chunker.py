"""
Excel分块器 - 将Excel文档按工作表和行数分块
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExcelChunker:
    """Excel分块器 - 按工作表和行数分块"""
    
    def __init__(self, chunk_size: int = 40, rows_per_chunk: int = None):
        """
        初始化Excel分块器

        Args:
            chunk_size: 每个分块的行数（为了兼容性）
            rows_per_chunk: 每个分块的行数（优先使用）
        """
        # 兼容两种参数名
        self.rows_per_chunk = rows_per_chunk if rows_per_chunk is not None else chunk_size
        
        if not PANDAS_AVAILABLE:
            logger.error("❌ pandas未安装，Excel分块功能不可用")
            raise ImportError("pandas is required for Excel chunking")
        
        logger.info(f"✅ Excel分块器已初始化 (每块行数: {rows_per_chunk})")
    
    def chunk_excel(self, excel_file: str, output_dir: str) -> List[str]:
        """
        分块Excel文档
        
        Args:
            excel_file: Excel文件路径
            output_dir: 输出目录路径
            
        Returns:
            生成的分块文件路径列表
        """
        input_path = Path(excel_file)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            logger.error(f"❌ Excel文件不存在: {excel_file}")
            return []
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 读取Excel文件
            excel_data = pd.ExcelFile(excel_file)
            chunk_files = []
            
            logger.info(f"📊 开始处理Excel文件: {input_path.name}")
            logger.info(f"📋 发现工作表: {excel_data.sheet_names}")
            
            for sheet_name in excel_data.sheet_names:
                logger.info(f"📄 处理工作表: {sheet_name}")
                
                # 读取工作表数据
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                if df.empty:
                    logger.warning(f"⚠️ 工作表为空: {sheet_name}")
                    continue
                
                # 分块处理
                sheet_chunks = self._chunk_dataframe(df, sheet_name, input_path.stem, output_path)
                chunk_files.extend(sheet_chunks)
            
            logger.info(f"✅ Excel分块完成: {len(chunk_files)}个分块")
            return chunk_files
            
        except Exception as e:
            logger.error(f"❌ Excel分块失败 {excel_file}: {e}")
            return []
    
    def _chunk_dataframe(self, df: pd.DataFrame, sheet_name: str, 
                        file_stem: str, output_path: Path) -> List[str]:
        """分块DataFrame数据"""
        chunk_files = []
        total_rows = len(df)
        
        logger.info(f"📊 工作表 '{sheet_name}' 共有 {total_rows} 行数据")
        
        # 按行数分块
        for start_row in range(0, total_rows, self.rows_per_chunk):
            end_row = min(start_row + self.rows_per_chunk, total_rows)
            chunk_df = df.iloc[start_row:end_row]
            
            # 生成分块文件名
            chunk_filename = f"{file_stem}_{sheet_name}_rows_{start_row+1}_{end_row}.md"
            chunk_file_path = output_path / chunk_filename
            
            # 创建分块内容
            chunk_content = self._create_chunk_content(
                file_stem, sheet_name, chunk_df, start_row+1, end_row, total_rows
            )
            
            # 保存分块文件
            with open(chunk_file_path, 'w', encoding='utf-8') as f:
                f.write(chunk_content)
            
            chunk_files.append(str(chunk_file_path))
            logger.debug(f"📝 创建分块: {chunk_filename}")
        
        return chunk_files
    
    def _create_chunk_content(self, file_stem: str, sheet_name: str, 
                             chunk_df: pd.DataFrame, start_row: int, 
                             end_row: int, total_rows: int) -> str:
        """创建分块内容"""
        
        # 生成表格的Markdown格式
        try:
            # 使用pandas的to_markdown方法
            table_markdown = chunk_df.to_markdown(index=False)
        except Exception:
            # 如果to_markdown失败，使用简单的表格格式
            table_markdown = self._dataframe_to_simple_markdown(chunk_df)
        
        # 创建完整的分块内容
        content = f"""---
源文件: {file_stem}.xlsx
工作表: {sheet_name}
行范围: 第{start_row}-{end_row}行 (共{total_rows}行)
分块ID: {file_stem}_{sheet_name}_rows_{start_row}_{end_row}
列数: {len(chunk_df.columns)}
---

# {sheet_name} - 第{start_row}-{end_row}行

**表头信息:** {' | '.join(chunk_df.columns.astype(str))}

**数据内容:**

{table_markdown}

**统计信息:**
- 数据行数: {len(chunk_df)}
- 列数: {len(chunk_df.columns)}
- 数据范围: 第{start_row}-{end_row}行 (总共{total_rows}行)
"""
        return content
    
    def _dataframe_to_simple_markdown(self, df: pd.DataFrame) -> str:
        """将DataFrame转换为简单的Markdown表格"""
        if df.empty:
            return "| 无数据 |\n|--------|\n"
        
        # 表头
        headers = df.columns.astype(str).tolist()
        header_row = "| " + " | ".join(headers) + " |"
        separator_row = "|" + "|".join([" --- " for _ in headers]) + "|"
        
        # 数据行
        data_rows = []
        for _, row in df.iterrows():
            row_data = [str(val) if pd.notna(val) else "" for val in row]
            data_row = "| " + " | ".join(row_data) + " |"
            data_rows.append(data_row)
        
        # 组合表格
        table_lines = [header_row, separator_row] + data_rows
        return "\n".join(table_lines)
    
    def get_excel_info(self, excel_file: str) -> Dict[str, Any]:
        """获取Excel文件信息"""
        try:
            excel_data = pd.ExcelFile(excel_file)
            info = {
                "file_name": Path(excel_file).name,
                "sheet_names": excel_data.sheet_names,
                "sheet_count": len(excel_data.sheet_names),
                "sheets_info": {}
            }
            
            for sheet_name in excel_data.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                info["sheets_info"][sheet_name] = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist()
                }
            
            return info
            
        except Exception as e:
            logger.error(f"❌ 获取Excel信息失败: {e}")
            return {}
