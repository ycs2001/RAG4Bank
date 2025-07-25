"""
文本分块器 - 将Markdown文档智能分块
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TextChunker:
    """文本分块器 - 按语义和结构分块"""
    
    def __init__(self, chunk_size: int = 1000, overlap_size: int = 200):
        """
        初始化文本分块器
        
        Args:
            chunk_size: 分块大小（字符数）
            overlap_size: 重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        logger.info(f"✅ 文本分块器已初始化 (块大小: {chunk_size}, 重叠: {overlap_size})")
    
    def chunk_document(self, markdown_file: str, output_dir: str) -> List[str]:
        """
        分块Markdown文档
        
        Args:
            markdown_file: Markdown文件路径
            output_dir: 输出目录路径
            
        Returns:
            生成的分块文件路径列表
        """
        input_path = Path(markdown_file)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            logger.error(f"❌ Markdown文件不存在: {markdown_file}")
            return []
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 读取Markdown内容
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分块处理
            chunks = self._split_content(content)
            
            # 生成分块文件
            chunk_files = []
            for i, chunk in enumerate(chunks):
                chunk_file = output_path / f"{input_path.stem}_chunk_{i+1}.md"
                
                # 创建分块内容
                chunk_content = self._create_chunk_content(
                    input_path.name, chunk, i+1, len(chunks)
                )
                
                # 保存分块文件
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    f.write(chunk_content)
                
                chunk_files.append(str(chunk_file))
                logger.debug(f"📝 创建分块: {chunk_file.name}")
            
            logger.info(f"✅ 文档分块完成: {len(chunk_files)}个分块")
            return chunk_files
            
        except Exception as e:
            logger.error(f"❌ 文档分块失败 {markdown_file}: {e}")
            return []
    
    def _split_content(self, content: str) -> List[str]:
        """分割内容为多个块"""
        chunks = []
        
        # 首先尝试按标题分割
        header_chunks = self._split_by_headers(content)
        
        # 如果按标题分割的块太大，再按段落分割
        for header_chunk in header_chunks:
            if len(header_chunk) <= self.chunk_size:
                chunks.append(header_chunk)
            else:
                # 块太大，按段落进一步分割
                paragraph_chunks = self._split_by_paragraphs(header_chunk)
                chunks.extend(paragraph_chunks)
        
        return chunks
    
    def _split_by_headers(self, content: str) -> List[str]:
        """按标题分割内容"""
        # 匹配Markdown标题
        header_pattern = r'^(#{1,6}\s+.+)$'
        lines = content.split('\n')
        
        chunks = []
        current_chunk = []
        
        for line in lines:
            if re.match(header_pattern, line, re.MULTILINE) and current_chunk:
                # 遇到新标题，保存当前块
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)
        
        # 保存最后一个块
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _split_by_paragraphs(self, content: str) -> List[str]:
        """按段落分割内容"""
        # 按双换行符分割段落
        paragraphs = content.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            if current_size + paragraph_size > self.chunk_size and current_chunk:
                # 当前块已满，保存并开始新块
                chunks.append('\n\n'.join(current_chunk))
                
                # 新块从重叠部分开始
                if self.overlap_size > 0 and current_chunk:
                    overlap_text = '\n\n'.join(current_chunk)[-self.overlap_size:]
                    current_chunk = [overlap_text, paragraph]
                    current_size = len(overlap_text) + paragraph_size
                else:
                    current_chunk = [paragraph]
                    current_size = paragraph_size
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size
        
        # 保存最后一个块
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _create_chunk_content(self, source_file: str, chunk_text: str, 
                             chunk_num: int, total_chunks: int) -> str:
        """创建分块内容"""
        content = f"""---
源文档: {source_file}
分块编号: {chunk_num}/{total_chunks}
分块ID: {Path(source_file).stem}_chunk_{chunk_num}
---

{chunk_text}
"""
        return content
