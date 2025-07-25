"""
文档转换器 - 将各种格式文档转换为Markdown
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

logger = logging.getLogger(__name__)

class DocumentConverter:
    """文档转换器 - 支持PDF、Word等格式转换为Markdown"""

    def __init__(self, output_dir: str = None):
        """
        初始化文档转换器

        Args:
            output_dir: 默认输出目录（可选）
        """
        self.default_output_dir = output_dir
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt', '.md']
        
        if MARKITDOWN_AVAILABLE:
            self.md_converter = MarkItDown()
            logger.info("✅ MarkItDown转换器已初始化")
        else:
            self.md_converter = None
            logger.warning("⚠️ MarkItDown未安装，文档转换功能受限")
    
    def convert_document(self, input_file: str, output_dir: str) -> Optional[str]:
        """
        转换文档为Markdown格式
        
        Args:
            input_file: 输入文件路径
            output_dir: 输出目录路径
            
        Returns:
            转换后的Markdown文件路径，失败返回None
        """
        input_path = Path(input_file)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            logger.error(f"❌ 输入文件不存在: {input_file}")
            return None
        
        if input_path.suffix.lower() not in self.supported_formats:
            logger.error(f"❌ 不支持的文件格式: {input_path.suffix}")
            return None
        
        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        output_file = output_path / f"{input_path.stem}.md"
        
        try:
            if input_path.suffix.lower() in ['.txt', '.md']:
                # 文本文件直接复制
                return self._convert_text_file(input_path, output_file)
            else:
                # 使用MarkItDown转换其他格式
                return self._convert_with_markitdown(input_path, output_file)
                
        except Exception as e:
            logger.error(f"❌ 文档转换失败 {input_file}: {e}")
            return None
    
    def _convert_text_file(self, input_path: Path, output_file: Path) -> str:
        """转换文本文件"""
        logger.info(f"📄 转换文本文件: {input_path.name}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加文档头信息
        markdown_content = f"""# {input_path.stem}

{content}
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"✅ 文本文件转换完成: {output_file}")
        return str(output_file)
    
    def _convert_with_markitdown(self, input_path: Path, output_file: Path) -> str:
        """使用MarkItDown转换文档"""
        if not self.md_converter:
            raise Exception("MarkItDown转换器不可用")
        
        logger.info(f"📄 使用MarkItDown转换: {input_path.name}")
        
        # 转换文档
        result = self.md_converter.convert(str(input_path))
        
        if not result or not result.text_content:
            raise Exception("转换结果为空")
        
        # 保存转换结果
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.text_content)
        
        logger.info(f"✅ MarkItDown转换完成: {output_file}")
        return str(output_file)
    
    def get_supported_formats(self) -> list:
        """获取支持的文件格式"""
        return self.supported_formats.copy()
    
    def is_supported(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        return Path(file_path).suffix.lower() in self.supported_formats
