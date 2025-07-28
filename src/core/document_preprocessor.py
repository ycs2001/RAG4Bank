"""
文档预处理器：基于GROBID Docker服务 + LLM的智能目录提取
"""

import requests
import json
import yaml
import subprocess
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from .base_component import BaseComponent
from ..config import EnhancedConfigManager

class DocumentPreprocessor(BaseComponent):
    """文档预处理器 - 使用gorbid + LLM智能提取目录"""

    def __init__(self, config_manager: EnhancedConfigManager, llm=None):
        """
        初始化文档预处理器

        Args:
            config_manager: 配置管理器实例
            llm: LLM实例，用于智能分析
        """
        super().__init__(config_manager)

        self.llm = llm
        self.preprocessing_config = self.get_config('documents.preprocessing', {})
        self.enabled = self.preprocessing_config.get('enabled', True)
        self.ocr_pages_limit = self.preprocessing_config.get('ocr_pages_limit', 10)
        self.toc_extraction_enabled = self.preprocessing_config.get('toc_extraction_enabled', True)

        # GROBID服务配置
        self.grobid_url = self.preprocessing_config.get('grobid_url', 'http://localhost:8070')
        self.grobid_timeout = self.preprocessing_config.get('grobid_timeout', 300)

        if self.enabled:
            self._check_dependencies()
            self.logger.info("✅ 文档预处理器已启用 (GROBID Docker + LLM)")
        else:
            self.logger.info("ℹ️ 文档预处理器已禁用")
    
    def _check_dependencies(self):
        """检查GROBID服务和LLM是否可用"""
        try:
            # 尝试多个可能的GROBID端口
            possible_urls = [
                "http://localhost:8070",
                "http://localhost:8080",
                "http://localhost:8071"
            ]

            grobid_available = False
            for url in possible_urls:
                try:
                    health_url = f"{url}/api/isalive"
                    response = requests.get(health_url, timeout=5)

                    if response.status_code == 200:
                        self.grobid_url = url  # 更新为可用的URL
                        self.logger.info(f"✅ GROBID服务连接成功: {url}")

                        # 获取GROBID版本信息
                        try:
                            version_url = f"{url}/api/version"
                            version_response = requests.get(version_url, timeout=3)
                            if version_response.status_code == 200:
                                self.logger.info(f"📋 GROBID版本: {version_response.text.strip()}")
                        except:
                            pass

                        grobid_available = True
                        break
                except:
                    continue

            if not grobid_available:
                self.logger.warning("⚠️ GROBID服务在所有端口都不可用，将跳过GROBID检查继续运行")
                # 不禁用服务，允许继续运行

            # 检查LLM是否可用
            if not self.llm:
                self.logger.warning("⚠️ LLM未提供，目录分析功能将受限")

            self.logger.info("✅ 依赖检查完成")

        except Exception as e:
            self.logger.error(f"依赖检查失败: {e}")
            # 不禁用服务，允许继续运行
    
    def extract_document_toc(self, document_id: str, file_path: str) -> Dict[str, Any]:
        """
        使用gorbid + LLM提取文档目录结构

        Args:
            document_id: 文档ID
            file_path: 文档文件路径

        Returns:
            目录结构信息
        """
        if not self.enabled or not self.toc_extraction_enabled:
            return {'status': 'disabled', 'chapters': []}

        try:
            self.logger.info(f"开始提取文档目录: {document_id}")

            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"文档文件不存在: {file_path}")
                return {'status': 'file_not_found', 'chapters': []}

            # 步骤1：根据文件类型提取文本
            if file_path.suffix.lower() == '.pdf':
                extracted_text = self._extract_text_with_grobid(file_path)
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                # 使用LibreOffice转换为PDF，然后用GROBID提取
                pdf_path = self._convert_docx_to_pdf(file_path)
                if pdf_path:
                    extracted_text = self._extract_text_with_grobid(pdf_path)
                    # 清理临时PDF文件
                    try:
                        pdf_path.unlink()
                    except:
                        pass
                else:
                    extracted_text = None
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                self.logger.warning(f"跳过Excel文件的目录提取: {file_path}")
                return {'status': 'unsupported_format', 'chapters': []}
            else:
                # 尝试直接读取文本文件
                extracted_text = self._extract_text_from_file(file_path)

            if not extracted_text:
                return {'status': 'text_extraction_failed', 'chapters': []}

            # 步骤2：使用LLM分析目录结构
            toc_data = self._analyze_toc_with_llm(extracted_text, document_id)

            # 步骤3：更新配置文件
            self._update_toc_config(document_id, toc_data)

            return toc_data

        except Exception as e:
            self.logger.error(f"提取文档目录失败: {e}")
            return {'status': 'error', 'error': str(e), 'chapters': []}
    
    def _extract_text_with_grobid(self, file_path: Path) -> Optional[str]:
        """使用GROBID Docker服务提取文档文本"""
        try:
            self.logger.info(f"使用GROBID提取文本: {file_path}")

            # 使用processFulltextDocument API获取更完整的文档结构
            api_url = f"{self.grobid_url}/api/processFulltextDocument"

            # 设置请求参数 - 处理更多页面以获取完整目录
            params = {
                'start': 1,
                'end': min(self.ocr_pages_limit * 2, 20),  # 扩大页面范围
                'consolidateHeader': 0,
                'consolidateCitations': 0,
                'includeRawCitations': 0
            }

            # 准备文件
            with open(file_path, 'rb') as pdf_file:
                files = {'input': pdf_file}
                headers = {'Accept': 'application/xml'}

                # 发送请求
                response = requests.post(
                    api_url,
                    files=files,
                    data=params,
                    headers=headers,
                    timeout=self.grobid_timeout
                )

            if response.status_code == 200:
                # 从TEI XML中提取文本内容
                text_content = self._extract_text_from_tei(response.text)

                if not text_content:
                    self.logger.warning("GROBID提取的文本为空")
                    return None

                self.logger.info(f"GROBID提取成功，文本长度: {len(text_content)} 字符")
                return text_content

            elif response.status_code == 204:
                self.logger.warning("GROBID处理完成，但未提取到内容")
                return None
            elif response.status_code == 503:
                self.logger.error("GROBID服务繁忙，请稍后重试")
                return None
            else:
                self.logger.error(f"GROBID处理失败: HTTP {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            self.logger.error("GROBID处理超时")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GROBID请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"GROBID文本提取失败: {e}")
            return None

    def _extract_text_from_tei(self, tei_xml: str) -> str:
        """从TEI XML中提取纯文本内容"""
        try:
            import xml.etree.ElementTree as ET

            # 解析XML
            root = ET.fromstring(tei_xml)

            # 提取所有文本内容
            text_parts = []

            # 遍历所有文本节点
            for elem in root.iter():
                if elem.text:
                    text_parts.append(elem.text.strip())
                if elem.tail:
                    text_parts.append(elem.tail.strip())

            # 合并文本并清理
            full_text = ' '.join(text_parts)

            # 清理多余的空白字符
            import re
            full_text = re.sub(r'\s+', ' ', full_text).strip()

            return full_text

        except ET.ParseError as e:
            self.logger.error(f"TEI XML解析失败: {e}")
            # 如果XML解析失败，尝试直接返回文本内容
            return tei_xml
        except Exception as e:
            self.logger.error(f"从TEI提取文本失败: {e}")
            return tei_xml

    def _convert_docx_to_pdf(self, docx_path: Path) -> Optional[Path]:
        """使用LibreOffice将DOCX转换为PDF"""
        try:
            self.logger.info(f"使用LibreOffice转换DOCX为PDF: {docx_path}")

            # 创建临时目录
            temp_dir = Path(tempfile.mkdtemp())

            # LibreOffice转换命令 - 尝试多个可能的路径
            possible_commands = [
                '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                'soffice',
                'libreoffice'
            ]

            cmd = None
            for soffice_cmd in possible_commands:
                try:
                    # 测试命令是否可用
                    test_result = subprocess.run([soffice_cmd, '--version'],
                                                capture_output=True, timeout=10)
                    if test_result.returncode == 0:
                        cmd = [
                            soffice_cmd,
                            '--headless',
                            '--convert-to', 'pdf',
                            '--outdir', str(temp_dir),
                            str(docx_path)
                        ]
                        break
                except:
                    continue

            if not cmd:
                self.logger.error("LibreOffice/soffice未找到")
                return None

            # 执行转换
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                # 查找生成的PDF文件
                pdf_name = docx_path.stem + '.pdf'
                pdf_path = temp_dir / pdf_name

                if pdf_path.exists():
                    self.logger.info(f"DOCX转PDF成功: {pdf_path}")
                    return pdf_path
                else:
                    self.logger.error("PDF文件未生成")
                    return None
            else:
                self.logger.error(f"LibreOffice转换失败: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            self.logger.error("LibreOffice转换超时")
            return None
        except FileNotFoundError:
            self.logger.error("LibreOffice未安装或不在PATH中")
            self.logger.error("请安装LibreOffice: brew install --cask libreoffice")
            return None
        except Exception as e:
            self.logger.error(f"DOCX转PDF失败: {e}")
            return None



    def _extract_text_from_file(self, file_path: Path) -> Optional[str]:
        """从普通文本文件提取文本"""
        try:
            self.logger.info(f"从文本文件提取文本: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            self.logger.info(f"文本文件提取成功，文本长度: {len(text)} 字符")
            return text

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    text = f.read()
                self.logger.info(f"文本文件提取成功（GBK编码），文本长度: {len(text)} 字符")
                return text
            except Exception as e:
                self.logger.error(f"文本文件提取失败: {e}")
                return None
        except Exception as e:
            self.logger.error(f"文本文件提取失败: {e}")
            return None
    
    def _analyze_toc_with_llm(self, text_content: str, document_id: str) -> Dict[str, Any]:
        """使用LLM分析文档目录结构"""
        if not self.llm:
            self.logger.warning("LLM未提供，无法进行智能目录分析")
            return {'status': 'llm_unavailable', 'chapters': []}

        try:
            self.logger.info(f"使用LLM分析文档目录: {document_id}")

            # 获取目录分析的prompt模板
            prompt_template = self.get_config('documents.toc_analysis_prompt', self._get_default_toc_prompt())

            # 构建分析prompt - 扩大文本分析范围
            max_text_length = 20000  # 增加到20000字符以获取完整目录
            prompt = prompt_template.format(
                document_id=document_id,
                text_content=text_content[:max_text_length],
                max_pages=self.ocr_pages_limit
            )

            # 调用LLM分析 - 增加max_tokens以获取完整响应
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.chat(messages, temperature=0.1, max_tokens=8000)

            # 解析LLM响应
            toc_data = self._parse_llm_toc_response(response.text, document_id)

            return toc_data

        except Exception as e:
            self.logger.error(f"LLM目录分析失败: {e}")
            return {'status': 'llm_analysis_failed', 'error': str(e), 'chapters': []}
    

    
    def _update_toc_config(self, document_id: str, toc_data: Dict[str, Any]):
        """更新配置文件中的目录信息"""
        try:
            # 保存到单独的目录数据文件（使用YAML格式）
            toc_file_path = Path('data/toc') / f'{document_id}_toc.yaml'
            toc_file_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存详细的目录数据
            with open(toc_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(toc_data, f, default_flow_style=False, allow_unicode=True, indent=2)

            self.logger.info(f"✅ 目录数据已保存: {toc_file_path}")
            self.logger.info(f"📋 文档 {document_id} 提取完成，共 {len(toc_data.get('chapters', []))} 个章节")

            # 尝试更新配置状态（如果支持的话）
            self._try_update_config_status(document_id, toc_data)

        except Exception as e:
            self.logger.error(f"更新目录配置失败: {e}")

    def _try_update_config_status(self, document_id: str, toc_data: Dict[str, Any]):
        """尝试更新配置文件中的状态信息"""
        try:
            # 这里可以实现配置文件的状态更新
            # 目前先记录到日志，后续可以扩展为实际的配置文件更新
            status = toc_data.get('status', 'unknown')
            confidence = toc_data.get('confidence', 0.0)
            chapters_count = len(toc_data.get('chapters', []))

            self.logger.info(f"📊 {document_id} 状态更新:")
            self.logger.info(f"   - 提取状态: {status}")
            self.logger.info(f"   - 置信度: {confidence:.2f}")
            self.logger.info(f"   - 章节数: {chapters_count}")

        except Exception as e:
            self.logger.error(f"更新配置状态失败: {e}")

    def load_document_toc(self, document_id: str) -> Optional[Dict[str, Any]]:
        """加载文档的目录数据"""
        try:
            toc_file_path = Path('data/toc') / f'{document_id}_toc.yaml'

            if not toc_file_path.exists():
                return None

            with open(toc_file_path, 'r', encoding='utf-8') as f:
                toc_data = yaml.safe_load(f)

            return toc_data

        except Exception as e:
            self.logger.error(f"加载目录数据失败: {e}")
            return None
    
    def process_all_documents(self) -> Dict[str, Any]:
        """处理所有配置的文档"""
        if not self.enabled:
            return {'status': 'disabled'}
        
        toc_config = self.get_config('documents.toc', {})
        results = {}
        
        for document_id, doc_info in toc_config.items():
            if doc_info.get('extraction_status') == 'pending':
                file_path = doc_info.get('file_path')
                if file_path:
                    result = self.extract_document_toc(document_id, file_path)
                    results[document_id] = result
        
        return {
            'status': 'completed',
            'processed_documents': len(results),
            'results': results
        }

    def _get_default_toc_prompt(self) -> str:
        """获取默认的目录分析prompt模板"""
        return """你是一个专业的文档目录分析专家。请分析以下文档文本，提取其目录结构。

文档ID: {document_id}
文档文本:
{text_content}

请仔细分析文本内容，寻找以下目录特征：

**主要目录模式：**
1. 报表汇总表格式：包含"序号"、"表号"、"报表名称"等列
2. 章节编号：如"第一章"、"一、"、"二、"等
3. 表格编号：如"G01"、"G03"、"G4A"、"S63"等
4. 页码信息：数字页码或"月"、"季"、"半年"等频度信息

**银行监管报表特征：**
- 基础财务类：G01、G03、G04、G05等
- 资本充足类：G40、G4A、G4B、G4C、G4D等
- 风险管理类：G11、G12、G13、G14等
- 专项统计类：S63、S68、S70等

**层级关系识别：**
- 主分类：基础财务、股东情况、杠杆率、资本充足、信用风险等
- 子表格：每个主分类下的具体报表
- 附注部分：表格的详细说明和填报要求

请提取所有找到的表格和章节信息，不要遗漏任何报表。

请按以下JSON格式返回目录结构：
{{
    "status": "completed",
    "extraction_method": "llm_analysis",
    "last_updated": "当前时间",
    "confidence": 0.85,
    "chapters": [
        {{
            "chapter_num": "第一章",
            "title": "章节标题",
            "page": 1,
            "level": 1,
            "subsections": [
                {{
                    "chapter_num": "1.1",
                    "title": "子章节标题",
                    "page": 5,
                    "level": 2
                }}
            ]
        }}
    ]
}}

注意事项：
1. 如果文本中没有明显的目录结构，返回空的chapters数组
2. 尽量准确识别章节的层级关系
3. 如果页码信息不明确，可以设置为null
4. confidence表示识别的置信度（0.0-1.0）
5. 只返回JSON格式，不要添加其他说明文字"""

    def _parse_llm_toc_response(self, response_text: str, document_id: str) -> Dict[str, Any]:
        """解析LLM的目录分析响应"""
        try:
            # 记录原始响应用于调试
            self.logger.debug(f"LLM原始响应长度: {len(response_text)}")
            self.logger.debug(f"LLM响应前500字符: {response_text[:500]}")

            # 尝试提取JSON部分
            response_text = response_text.strip()

            # 如果响应被包装在代码块中，提取JSON部分
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                if end > start:
                    response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                if end > start:
                    response_text = response_text[start:end].strip()

            # 尝试解析JSON响应
            toc_data = json.loads(response_text)

            # 验证响应格式
            if 'chapters' not in toc_data:
                self.logger.warning("LLM响应缺少chapters字段")
                toc_data['chapters'] = []

            # 添加时间戳
            toc_data['last_updated'] = datetime.now().isoformat()
            toc_data['document_id'] = document_id

            chapters_count = len(toc_data.get('chapters', []))
            confidence = toc_data.get('confidence', 0.0)

            self.logger.info(f"LLM目录分析完成: {document_id}, {chapters_count}个章节, 置信度: {confidence}")

            return toc_data

        except json.JSONDecodeError:
            self.logger.error("LLM响应不是有效的JSON格式")
            # 尝试从文本中提取基本信息
            return self._fallback_parse_toc_response(response_text, document_id)
        except Exception as e:
            self.logger.error(f"解析LLM目录响应失败: {e}")
            return {
                'status': 'parse_failed',
                'error': str(e),
                'document_id': document_id,
                'last_updated': datetime.now().isoformat(),
                'chapters': []
            }

    def _fallback_parse_toc_response(self, response_text: str, document_id: str) -> Dict[str, Any]:
        """LLM响应解析失败时的兜底方法"""
        self.logger.info("使用兜底方法解析LLM响应")

        # 简单的文本解析，提取可能的章节信息
        lines = response_text.split('\n')
        chapters = []

        for line in lines:
            line = line.strip()
            if '章' in line or '节' in line or line.startswith(('第', '一', '二', '三', '四', '五')):
                chapters.append({
                    'title': line,
                    'page': None,
                    'level': 1,
                    'subsections': []
                })

        return {
            'status': 'fallback_parsed',
            'extraction_method': 'llm_fallback',
            'document_id': document_id,
            'last_updated': datetime.now().isoformat(),
            'confidence': 0.3,
            'chapters': chapters
        }
