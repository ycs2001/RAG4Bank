#!/usr/bin/env python3
"""
CategoryRAG 监管报送Web服务
基于现有web_service.py扩展，添加监管报送专用功能
"""

import os
import sys
import logging
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import werkzeug.exceptions

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.unified_rag_system import UnifiedRAGSystem
from src.config.enhanced_config_manager import EnhancedConfigManager
from smart_document_adder import SmartDocumentAdder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/regulatory_web_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RegulatoryAnalysisEngine:
    """监管分析引擎 - 处理监管特定的业务逻辑"""
    
    def __init__(self, rag_system: UnifiedRAGSystem):
        self.rag_system = rag_system
        self.logger = logging.getLogger(__name__ + '.RegulatoryAnalysisEngine')
    
    def analyze_loan_migration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """贷款质量迁徙分析"""
        try:
            # 构建监管查询
            query = self._build_loan_migration_query(data)
            
            # 使用RAG系统获取相关监管规定
            rag_response = self.rag_system.answer_question(query)
            
            # 执行具体的迁徙分析计算
            analysis_result = self._calculate_loan_migration(data)
            
            return {
                'analysis_type': 'loan_migration',
                'regulatory_guidance': rag_response.answer,
                'calculation_result': analysis_result,
                'data_sources': rag_response.collections_used,
                'processing_time': rag_response.processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"贷款迁徙分析失败: {e}")
            return {
                'error': str(e),
                'analysis_type': 'loan_migration',
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_financial_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """财务指标分析"""
        try:
            # 构建财务指标查询
            query = self._build_financial_query(data)
            
            # 获取监管要求
            rag_response = self.rag_system.answer_question(query)
            
            # 计算财务指标
            indicators = self._calculate_financial_indicators(data)
            
            return {
                'analysis_type': 'financial_indicators',
                'regulatory_requirements': rag_response.answer,
                'calculated_indicators': indicators,
                'compliance_status': self._check_compliance(indicators),
                'data_sources': rag_response.collections_used,
                'processing_time': rag_response.processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"财务指标分析失败: {e}")
            return {
                'error': str(e),
                'analysis_type': 'financial_indicators',
                'timestamp': datetime.now().isoformat()
            }
    
    def validate_report_data(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """报表数据验证"""
        try:
            # 构建验证查询
            query = f"请提供{report_type}报表的数据验证规则和要求"
            
            # 获取验证规则
            rag_response = self.rag_system.answer_question(query)
            
            # 执行数据验证
            validation_result = self._validate_data_structure(report_type, data)
            
            return {
                'validation_type': 'report_data',
                'report_type': report_type,
                'validation_rules': rag_response.answer,
                'validation_result': validation_result,
                'is_valid': validation_result.get('is_valid', False),
                'errors': validation_result.get('errors', []),
                'warnings': validation_result.get('warnings', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"报表验证失败: {e}")
            return {
                'error': str(e),
                'validation_type': 'report_data',
                'report_type': report_type,
                'timestamp': datetime.now().isoformat()
            }
    
    def _build_loan_migration_query(self, data: Dict[str, Any]) -> str:
        """构建贷款迁徙查询"""
        report_type = data.get('reportType', '贷款')
        return f"请提供{report_type}质量迁徙分析的监管要求、计算方法和相关规定"
    
    def _build_financial_query(self, data: Dict[str, Any]) -> str:
        """构建财务指标查询"""
        indicators = data.get('indicators', [])
        if indicators:
            indicator_list = '、'.join(indicators)
            return f"请提供{indicator_list}等财务指标的监管要求、计算公式和合规标准"
        else:
            return "请提供银行财务指标的监管要求和计算方法"
    
    def _calculate_loan_migration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算贷款迁徙率"""
        # 这里实现具体的迁徙率计算逻辑
        # 示例实现
        try:
            loan_data = data.get('data', {})
            
            # 模拟计算逻辑
            normal_to_concern = loan_data.get('normal_to_concern', 0)
            normal_balance = loan_data.get('normal_balance', 1)
            
            migration_rate = (normal_to_concern / normal_balance) * 100 if normal_balance > 0 else 0
            
            return {
                'migration_rate': round(migration_rate, 2),
                'calculation_method': '迁徙率 = 期初正常类贷款中转为关注类的金额 / 期初正常类贷款余额 × 100%',
                'input_data': loan_data,
                'result_interpretation': self._interpret_migration_rate(migration_rate)
            }
            
        except Exception as e:
            return {'error': f'计算失败: {e}'}
    
    def _calculate_financial_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算财务指标"""
        # 实现财务指标计算
        try:
            financial_data = data.get('data', {})
            indicators = {}
            
            # 资本充足率
            if 'capital' in financial_data and 'risk_assets' in financial_data:
                capital_ratio = (financial_data['capital'] / financial_data['risk_assets']) * 100
                indicators['capital_adequacy_ratio'] = round(capital_ratio, 2)
            
            # 不良贷款率
            if 'npl_amount' in financial_data and 'total_loans' in financial_data:
                npl_ratio = (financial_data['npl_amount'] / financial_data['total_loans']) * 100
                indicators['npl_ratio'] = round(npl_ratio, 2)
            
            # ROA
            if 'net_income' in financial_data and 'total_assets' in financial_data:
                roa = (financial_data['net_income'] / financial_data['total_assets']) * 100
                indicators['roa'] = round(roa, 2)
            
            return {
                'calculated_indicators': indicators,
                'calculation_date': datetime.now().isoformat(),
                'input_data': financial_data
            }
            
        except Exception as e:
            return {'error': f'指标计算失败: {e}'}
    
    def _check_compliance(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """检查合规状态"""
        compliance = {}
        calculated = indicators.get('calculated_indicators', {})
        
        # 资本充足率合规检查 (最低8%)
        if 'capital_adequacy_ratio' in calculated:
            car = calculated['capital_adequacy_ratio']
            compliance['capital_adequacy'] = {
                'value': car,
                'threshold': 8.0,
                'compliant': car >= 8.0,
                'status': '合规' if car >= 8.0 else '不合规'
            }
        
        # 不良贷款率合规检查 (建议<5%)
        if 'npl_ratio' in calculated:
            npl = calculated['npl_ratio']
            compliance['npl_ratio'] = {
                'value': npl,
                'threshold': 5.0,
                'compliant': npl <= 5.0,
                'status': '良好' if npl <= 5.0 else '需关注'
            }
        
        return compliance
    
    def _validate_data_structure(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据结构"""
        errors = []
        warnings = []
        
        # 基础数据验证
        if not data:
            errors.append("数据不能为空")
        
        if report_type == "1104报表":
            # 1104报表特定验证
            required_fields = ['report_date', 'institution_code', 'data']
            for field in required_fields:
                if field not in data:
                    errors.append(f"缺少必填字段: {field}")
        
        # 数据类型验证
        if 'data' in data and not isinstance(data['data'], dict):
            errors.append("数据字段必须是对象类型")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validated_fields': list(data.keys()) if data else []
        }
    
    def _interpret_migration_rate(self, rate: float) -> str:
        """解释迁徙率结果"""
        if rate <= 2:
            return "迁徙率较低，资产质量良好"
        elif rate <= 5:
            return "迁徙率正常，需持续关注"
        elif rate <= 10:
            return "迁徙率偏高，需要加强风险管控"
        else:
            return "迁徙率过高，存在较大风险隐患"

class CategoryRAGRegulatoryWebService:
    """CategoryRAG监管报送Web服务类"""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # 启用跨域支持
        
        # 初始化组件
        self.config_manager = None
        self.rag_system = None
        self.document_adder = None
        self.analysis_engine = None
        
        # 设置路由
        self._setup_routes()
        self._setup_error_handlers()
        
        # 初始化系统
        self._initialize_system()
    
    def _initialize_system(self):
        """初始化CategoryRAG系统"""
        try:
            logger.info("🚀 初始化CategoryRAG监管报送Web服务...")
            
            # 1. 初始化配置管理器
            self.config_manager = EnhancedConfigManager()
            logger.info("✅ 配置管理器初始化完成")
            
            # 2. 初始化RAG系统
            self.rag_system = UnifiedRAGSystem(self.config_manager)
            logger.info("✅ RAG系统初始化完成")
            
            # 3. 初始化文档添加器
            self.document_adder = SmartDocumentAdder()
            logger.info("✅ 智能文档添加器初始化完成")
            
            # 4. 初始化监管分析引擎
            self.analysis_engine = RegulatoryAnalysisEngine(self.rag_system)
            logger.info("✅ 监管分析引擎初始化完成")
            
            logger.info("🎉 CategoryRAG监管报送Web服务初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise

    def _setup_routes(self):
        """设置API路由"""

        # ==================== 基础接口 ====================

        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'CategoryRAG Regulatory Web API',
                'version': '1.0.0'
            })

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """获取系统状态"""
            try:
                if not self.rag_system:
                    return jsonify({'error': 'RAG系统未初始化'}), 500

                # 获取集合信息
                collections_info = []
                if hasattr(self.rag_system.retriever, 'collections'):
                    for collection_id, collection in self.rag_system.retriever.collections.items():
                        try:
                            doc_count = collection.count()
                            collections_info.append({
                                'id': collection_id,
                                'name': collection_id,
                                'document_count': doc_count
                            })
                        except Exception as e:
                            logger.warning(f"获取集合 {collection_id} 信息失败: {e}")

                return jsonify({
                    'status': 'running',
                    'timestamp': datetime.now().isoformat(),
                    'service_type': 'regulatory_reporting',
                    'collections': collections_info,
                    'total_collections': len(collections_info),
                    'total_documents': sum(c['document_count'] for c in collections_info),
                    'features': {
                        'rag_query': True,
                        'loan_migration_analysis': True,
                        'financial_indicators': True,
                        'report_validation': True,
                        'document_upload': True
                    }
                })

            except Exception as e:
                logger.error(f"获取系统状态失败: {e}")
                return jsonify({'error': str(e)}), 500

        # ==================== 监管报送专用接口 ====================

        @self.app.route('/api/analyze', methods=['POST'])
        def analyze():
            """监管分析接口 - 对应前端的核心分析功能"""
            try:
                if not self.analysis_engine:
                    return jsonify({'error': '分析引擎未初始化'}), 500

                # 获取请求数据
                data = request.get_json()
                if not data:
                    return jsonify({'error': '请求数据不能为空'}), 400

                report_type = data.get('reportType', '')
                analysis_data = data.get('data', {})
                template = data.get('template', '')

                logger.info(f"🔍 监管分析请求: {report_type}")

                # 根据报表类型选择分析方法
                if '贷款' in report_type or '迁徙' in report_type:
                    result = self.analysis_engine.analyze_loan_migration(data)
                elif '财务' in report_type or '指标' in report_type:
                    result = self.analysis_engine.analyze_financial_indicators(data)
                else:
                    # 通用RAG查询
                    query = f"请分析{report_type}相关的监管要求和填报指导"
                    rag_response = self.rag_system.answer_question(query)

                    result = {
                        'analysis_type': 'general_regulatory',
                        'report_type': report_type,
                        'guidance': rag_response.answer,
                        'data_sources': rag_response.collections_used,
                        'processing_time': rag_response.processing_time,
                        'timestamp': datetime.now().isoformat()
                    }

                logger.info(f"✅ 监管分析完成: {report_type}")
                return jsonify(result)

            except Exception as e:
                logger.error(f"监管分析失败: {e}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/templates', methods=['GET'])
        def get_templates():
            """获取报表模板信息 - 基于现有集合"""
            try:
                if not self.rag_system:
                    return jsonify({'error': 'RAG系统未初始化'}), 500

                templates = []
                if hasattr(self.rag_system.retriever, 'collections'):
                    for collection_id, collection in self.rag_system.retriever.collections.items():
                        try:
                            doc_count = collection.count()

                            # 根据集合ID生成模板信息
                            template_info = self._generate_template_info(collection_id, doc_count)
                            if template_info:
                                templates.append(template_info)

                        except Exception as e:
                            logger.warning(f"获取集合 {collection_id} 模板信息失败: {e}")

                return jsonify({
                    'templates': templates,
                    'total_count': len(templates),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"获取模板信息失败: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/validate', methods=['POST'])
        def validate():
            """报表数据验证"""
            try:
                if not self.analysis_engine:
                    return jsonify({'error': '分析引擎未初始化'}), 500

                data = request.get_json()
                if not data:
                    return jsonify({'error': '请求数据不能为空'}), 400

                report_type = data.get('reportType', '')
                report_data = data.get('data', {})

                logger.info(f"🔍 报表验证请求: {report_type}")

                # 执行验证
                result = self.analysis_engine.validate_report_data(report_type, report_data)

                logger.info(f"✅ 报表验证完成: {report_type}")
                return jsonify(result)

            except Exception as e:
                logger.error(f"报表验证失败: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/upload', methods=['POST'])
        def upload():
            """文档上传 - 复用现有功能"""
            try:
                if not self.document_adder:
                    return jsonify({'error': '文档添加器未初始化'}), 500

                # 检查是否有文件上传
                if 'file' not in request.files:
                    return jsonify({'error': '没有上传文件'}), 400

                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': '文件名为空'}), 400

                # 检查文件类型
                allowed_extensions = {'.pdf', '.docx', '.doc', '.xlsx', '.xls'}
                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in allowed_extensions:
                    return jsonify({
                        'error': f'不支持的文件类型: {file_ext}',
                        'supported_types': list(allowed_extensions)
                    }), 400

                # 保存文件到KnowledgeBase目录
                knowledge_base_dir = Path('data/KnowledgeBase')
                knowledge_base_dir.mkdir(parents=True, exist_ok=True)

                file_path = knowledge_base_dir / file.filename
                file.save(str(file_path))

                logger.info(f"📄 文件已保存: {file_path}")

                # 使用智能文档添加器处理
                success = self.document_adder.process_document(str(file_path))

                if success:
                    return jsonify({
                        'message': '文档上传成功',
                        'filename': file.filename,
                        'file_path': str(file_path),
                        'timestamp': datetime.now().isoformat(),
                        'note': '请重启系统以加载新配置'
                    })
                else:
                    return jsonify({
                        'error': '文档处理失败',
                        'filename': file.filename
                    }), 500

            except Exception as e:
                logger.error(f"文档上传失败: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        # ==================== 扩展接口 ====================

        @self.app.route('/api/history', methods=['GET'])
        def get_history():
            """获取分析历史 - 简化实现"""
            try:
                # 这里可以实现历史记录功能
                # 目前返回模拟数据
                history = [
                    {
                        'id': '1',
                        'report_type': '1104报表',
                        'analysis_type': 'loan_migration',
                        'timestamp': datetime.now().isoformat(),
                        'status': 'completed'
                    }
                ]

                return jsonify({
                    'history': history,
                    'total_count': len(history),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"获取历史记录失败: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/reports', methods=['GET'])
        def get_reports():
            """获取报表列表"""
            try:
                # 基于现有集合生成报表列表
                reports = []
                if hasattr(self.rag_system.retriever, 'collections'):
                    for collection_id in self.rag_system.retriever.collections.keys():
                        report_info = self._generate_report_info(collection_id)
                        if report_info:
                            reports.append(report_info)

                return jsonify({
                    'reports': reports,
                    'total_count': len(reports),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"获取报表列表失败: {e}")
                return jsonify({'error': str(e)}), 500

        # ==================== 兼容性接口 ====================

        @self.app.route('/api/query', methods=['POST'])
        def query():
            """通用RAG查询 - 保持向后兼容"""
            try:
                if not self.rag_system:
                    return jsonify({'error': 'RAG系统未初始化'}), 500

                data = request.get_json()
                if not data or 'question' not in data:
                    return jsonify({'error': '缺少question参数'}), 400

                question = data['question'].strip()
                if not question:
                    return jsonify({'error': '问题不能为空'}), 400

                logger.info(f"🔍 通用RAG查询: {question}")

                # 调用RAG系统
                response = self.rag_system.answer_question(question)

                # 构建返回结果
                result = {
                    'answer': response.answer,
                    'question': question,
                    'retrieval_count': response.retrieval_count,
                    'processing_time': round(response.processing_time, 2),
                    'collections_used': response.collections_used,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'context_length': response.metadata.get('context_length', 0),
                        'retrieval_scores': response.metadata.get('retrieval_scores', [])
                    }
                }

                logger.info(f"✅ 通用RAG查询完成，耗时 {response.processing_time:.2f}秒")
                return jsonify(result)

            except Exception as e:
                logger.error(f"查询处理失败: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/api/collections', methods=['GET'])
        def get_collections():
            """获取集合信息 - 保持向后兼容"""
            try:
                if not self.rag_system:
                    return jsonify({'error': 'RAG系统未初始化'}), 500

                collections = []
                if hasattr(self.rag_system.retriever, 'collections'):
                    for collection_id, collection in self.rag_system.retriever.collections.items():
                        try:
                            doc_count = collection.count()
                            collections.append({
                                'id': collection_id,
                                'name': collection_id,
                                'description': f'{collection_id}相关文档',
                                'document_count': doc_count,
                                'type': self._get_collection_type(collection_id)
                            })
                        except Exception as e:
                            logger.warning(f"获取集合 {collection_id} 详细信息失败: {e}")

                return jsonify({
                    'collections': collections,
                    'total_count': len(collections)
                })

            except Exception as e:
                logger.error(f"获取集合信息失败: {e}")
                return jsonify({'error': str(e)}), 500

    def _generate_template_info(self, collection_id: str, doc_count: int) -> Optional[Dict[str, Any]]:
        """根据集合ID生成模板信息"""
        template_mapping = {
            'report_1104_2024': {
                'id': 'template_1104_2024',
                'name': '1104报表模板(2024版)',
                'type': '监管报表',
                'description': '银行业监管统计报表制度2024版',
                'document_count': doc_count,
                'supported_analysis': ['loan_migration', 'financial_indicators']
            },
            'report_1104_2022': {
                'id': 'template_1104_2022',
                'name': '1104报表模板(2022版)',
                'type': '监管报表',
                'description': '银行业监管统计报表制度2022版',
                'document_count': doc_count,
                'supported_analysis': ['loan_migration', 'financial_indicators']
            },
            'east_data_structure': {
                'id': 'template_east',
                'name': 'EAST数据模板',
                'type': '数据报送',
                'description': 'EAST监管数据报送模板',
                'document_count': doc_count,
                'supported_analysis': ['data_validation']
            },
            'pboc_statistics': {
                'id': 'template_pboc',
                'name': '人民银行统计模板',
                'type': '统计报表',
                'description': '人民银行金融统计制度模板',
                'document_count': doc_count,
                'supported_analysis': ['financial_indicators']
            }
        }

        return template_mapping.get(collection_id)

    def _generate_report_info(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """根据集合ID生成报表信息"""
        report_mapping = {
            'report_1104_2024': {
                'id': 'report_1104_2024',
                'name': '1104报表(2024版)',
                'category': '银行业监管统计',
                'frequency': '月报',
                'status': 'active'
            },
            'report_1104_2022': {
                'id': 'report_1104_2022',
                'name': '1104报表(2022版)',
                'category': '银行业监管统计',
                'frequency': '月报',
                'status': 'archived'
            },
            'east_data_structure': {
                'id': 'east_report',
                'name': 'EAST数据报送',
                'category': '监管数据',
                'frequency': '实时',
                'status': 'active'
            },
            'pboc_statistics': {
                'id': 'pboc_report',
                'name': '人民银行统计报表',
                'category': '金融统计',
                'frequency': '月报',
                'status': 'active'
            }
        }

        return report_mapping.get(collection_id)

    def _get_collection_type(self, collection_id: str) -> str:
        """获取集合类型"""
        if 'report_1104' in collection_id:
            return '监管报表'
        elif 'east' in collection_id:
            return '数据报送'
        elif 'pboc' in collection_id:
            return '统计制度'
        elif 'ybt' in collection_id:
            return '产品报送'
        else:
            return '其他文档'

    def _setup_error_handlers(self):
        """设置错误处理器"""

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'error': 'API端点不存在',
                'message': '请检查URL路径',
                'available_endpoints': [
                    'GET /api/health',
                    'GET /api/status',
                    'POST /api/analyze',
                    'GET /api/templates',
                    'POST /api/validate',
                    'POST /api/upload',
                    'GET /api/history',
                    'GET /api/reports',
                    'POST /api/query',
                    'GET /api/collections'
                ]
            }), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"内部服务器错误: {error}")
            return jsonify({
                'error': '内部服务器错误',
                'timestamp': datetime.now().isoformat()
            }), 500

        @self.app.errorhandler(Exception)
        def handle_exception(e):
            if isinstance(e, werkzeug.exceptions.HTTPException):
                return e

            logger.error(f"未处理的异常: {e}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': '服务器内部错误',
                'timestamp': datetime.now().isoformat()
            }), 500

    def run(self, host='127.0.0.1', port=8010, debug=False):
        """启动Web服务"""
        logger.info(f"🚀 启动CategoryRAG监管报送Web服务: http://{host}:{port}")
        logger.info("📋 可用API端点:")
        logger.info("   GET  /api/health      - 健康检查")
        logger.info("   GET  /api/status      - 系统状态")
        logger.info("   POST /api/analyze     - 监管分析")
        logger.info("   GET  /api/templates   - 报表模板")
        logger.info("   POST /api/validate    - 数据验证")
        logger.info("   POST /api/upload      - 文档上传")
        logger.info("   GET  /api/history     - 分析历史")
        logger.info("   GET  /api/reports     - 报表列表")
        logger.info("   POST /api/query       - 通用查询")
        logger.info("   GET  /api/collections - 集合信息")

        self.app.run(host=host, port=port, debug=debug)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='CategoryRAG监管报送Web服务')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=8010, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')

    args = parser.parse_args()

    # 确保日志目录存在
    Path('logs').mkdir(exist_ok=True)

    try:
        # 创建并启动Web服务
        web_service = CategoryRAGRegulatoryWebService()
        web_service.run(host=args.host, port=args.port, debug=args.debug)

    except KeyboardInterrupt:
        logger.info("👋 监管报送Web服务已停止")
    except Exception as e:
        logger.error(f"❌ 监管报送Web服务启动失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
