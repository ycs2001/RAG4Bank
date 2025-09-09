#!/usr/bin/env python3
"""
CategoryRAG Web服务
基于Flask的简化Web API，复用现有核心组件
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import werkzeug.exceptions

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from src.core.unified_rag_system import UnifiedRAGSystem
from src.config.enhanced_config_manager import EnhancedConfigManager
from smart_document_adder import SmartDocumentAdder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CategoryRAGWebService:
    """CategoryRAG Web服务类"""
    
    def __init__(self, enable_regulatory=False):
        self.app = Flask(__name__)
        CORS(self.app)  # 启用跨域支持
        self.enable_regulatory = enable_regulatory

        # 初始化组件
        self.config_manager = None
        self.rag_system = None
        self.document_adder = None

        # 设置路由
        self._setup_routes()

        # 设置监管报送路由（如果启用）
        if self.enable_regulatory:
            self._setup_regulatory_routes()

        self._setup_error_handlers()

        # 初始化系统
        self._initialize_system()
    
    def _initialize_system(self):
        """初始化CategoryRAG系统"""
        try:
            logger.info("🚀 初始化CategoryRAG Web服务...")
            
            # 1. 初始化配置管理器
            self.config_manager = EnhancedConfigManager()
            logger.info("✅ 配置管理器初始化完成")
            
            # 2. 初始化RAG系统
            self.rag_system = UnifiedRAGSystem(self.config_manager)
            logger.info("✅ RAG系统初始化完成")
            
            # 3. 初始化文档添加器
            self.document_adder = SmartDocumentAdder()
            logger.info("✅ 智能文档添加器初始化完成")
            
            logger.info("🎉 CategoryRAG Web服务初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _setup_routes(self):
        """设置API路由"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'CategoryRAG Web API',
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
                
                # 获取配置信息
                config_info = {
                    'retrieval_top_k': self.config_manager.get('retrieval.top_k', 30),
                    'reranker_top_k': self.config_manager.get('reranker.cross_encoder.top_k', 20),
                    'similarity_threshold': self.config_manager.get('retrieval.similarity_threshold', 0.5)
                }
                
                return jsonify({
                    'status': 'running',
                    'timestamp': datetime.now().isoformat(),
                    'collections': collections_info,
                    'total_collections': len(collections_info),
                    'total_documents': sum(c['document_count'] for c in collections_info),
                    'configuration': config_info
                })
                
            except Exception as e:
                logger.error(f"获取系统状态失败: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/collections', methods=['GET'])
        def get_collections():
            """获取集合信息"""
            try:
                if not self.rag_system:
                    return jsonify({'error': 'RAG系统未初始化'}), 500
                
                collections = []
                if hasattr(self.rag_system.retriever, 'collections'):
                    for collection_id, collection in self.rag_system.retriever.collections.items():
                        try:
                            doc_count = collection.count()
                            
                            # 从配置中获取集合详细信息
                            collection_configs = self.config_manager.get('embedding.collections', [])
                            collection_config = next(
                                (c for c in collection_configs if c.get('collection_id') == collection_id),
                                {}
                            )
                            
                            collections.append({
                                'id': collection_id,
                                'name': collection_config.get('name', collection_id),
                                'description': collection_config.get('description', ''),
                                'type': collection_config.get('type', ''),
                                'keywords': collection_config.get('keywords', []),
                                'document_count': doc_count,
                                'version': collection_config.get('version', ''),
                                'priority': collection_config.get('priority', 2)
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
        
        @self.app.route('/api/query', methods=['POST'])
        def query():
            """问答查询"""
            try:
                if not self.rag_system:
                    return jsonify({'error': 'RAG系统未初始化'}), 500
                
                # 获取请求数据
                data = request.get_json()
                if not data or 'question' not in data:
                    return jsonify({'error': '缺少question参数'}), 400
                
                question = data['question'].strip()
                if not question:
                    return jsonify({'error': '问题不能为空'}), 400
                
                logger.info(f"🔍 Web API查询: {question}")
                
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
                        'retrieval_scores': self._clean_scores(response.metadata.get('retrieval_scores', []))
                    }
                }
                
                logger.info(f"✅ Web API查询完成，耗时 {response.processing_time:.2f}秒")
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"查询处理失败: {e}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/documents', methods=['POST'])
        def add_document():
            """添加文档"""
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
                        'message': '文档添加成功',
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
                logger.error(f"文档添加失败: {e}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def _clean_scores(self, scores):
        """清理分数列表，移除NaN值"""
        import math
        cleaned_scores = []
        for score in scores:
            if isinstance(score, (int, float)) and not math.isnan(score):
                cleaned_scores.append(round(score, 3))
        return cleaned_scores

    def _setup_regulatory_routes(self):
        """设置监管报送相关路由"""

        @self.app.route('/api/analyze', methods=['POST'])
        def analyze_regulatory_document():
            """监管文档分析"""
            try:
                data = request.get_json()
                if not data or 'content' not in data:
                    return jsonify({'error': '缺少文档内容'}), 400

                content = data['content']
                analysis_type = data.get('type', 'general')

                # 使用RAG系统进行分析
                if self.rag_system:
                    query = f"请分析以下{analysis_type}文档的合规性和要点：{content[:1000]}"
                    result = self.rag_system.query(query)

                    return jsonify({
                        'analysis': result.get('answer', ''),
                        'type': analysis_type,
                        'timestamp': datetime.now().isoformat(),
                        'confidence': result.get('confidence', 0.8)
                    })
                else:
                    return jsonify({'error': 'RAG系统未初始化'}), 500

            except Exception as e:
                logger.error(f"监管文档分析失败: {e}")
                return jsonify({'error': f'分析失败: {str(e)}'}), 500

        @self.app.route('/api/templates', methods=['GET'])
        def get_regulatory_templates():
            """获取监管报表模板"""
            try:
                templates = [
                    {
                        'id': '1104_template',
                        'name': '1104报表模板',
                        'description': '银行业监管统计报表',
                        'version': '2024版',
                        'category': '监管报表'
                    },
                    {
                        'id': 'east_template',
                        'name': 'EAST数据模板',
                        'description': 'EAST监管数据报送模板',
                        'version': '现行版',
                        'category': '数据报送'
                    }
                ]

                return jsonify({
                    'templates': templates,
                    'total_count': len(templates),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"获取模板失败: {e}")
                return jsonify({'error': f'获取模板失败: {str(e)}'}), 500

        @self.app.route('/api/validate', methods=['POST'])
        def validate_regulatory_data():
            """验证监管数据"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': '缺少验证数据'}), 400

                # 简单的验证逻辑
                validation_result = {
                    'is_valid': True,
                    'errors': [],
                    'warnings': [],
                    'timestamp': datetime.now().isoformat()
                }

                # 这里可以添加具体的验证逻辑
                if 'required_fields' in data:
                    for field in data['required_fields']:
                        if not data.get(field):
                            validation_result['errors'].append(f'缺少必填字段: {field}')
                            validation_result['is_valid'] = False

                return jsonify(validation_result)

            except Exception as e:
                logger.error(f"数据验证失败: {e}")
                return jsonify({'error': f'验证失败: {str(e)}'}), 500

        @self.app.route('/api/upload', methods=['POST'])
        def upload_regulatory_document():
            """上传监管文档（监管报送专用）"""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': '没有上传文件'}), 400

                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': '文件名为空'}), 400

                # 保存文件并处理
                file_path = f"data/regulatory_uploads/{file.filename}"
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)

                return jsonify({
                    'message': '监管文档上传成功',
                    'filename': file.filename,
                    'file_path': file_path,
                    'timestamp': datetime.now().isoformat(),
                    'note': '文档已保存到监管文档目录'
                })

            except Exception as e:
                logger.error(f"监管文档上传失败: {e}")
                return jsonify({'error': f'上传失败: {str(e)}'}), 500

        @self.app.route('/api/history', methods=['GET'])
        def get_analysis_history():
            """获取分析历史"""
            try:
                # 这里可以从数据库或文件中读取历史记录
                history = [
                    {
                        'id': '1',
                        'type': '1104报表分析',
                        'timestamp': '2025-07-25T10:00:00',
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
                return jsonify({'error': f'获取历史失败: {str(e)}'}), 500

        @self.app.route('/api/reports', methods=['GET'])
        def get_regulatory_reports():
            """获取监管报表列表"""
            try:
                reports = [
                    {
                        'id': 'report_1104_2024',
                        'name': '1104报表_2024版',
                        'type': '监管报表',
                        'status': 'active',
                        'last_updated': '2024-12-01'
                    },
                    {
                        'id': 'east_data_structure',
                        'name': 'EAST数据结构',
                        'type': '数据结构',
                        'status': 'active',
                        'last_updated': '2024-11-15'
                    }
                ]

                return jsonify({
                    'reports': reports,
                    'total_count': len(reports),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"获取报表列表失败: {e}")
                return jsonify({'error': f'获取报表失败: {str(e)}'}), 500

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
                    'GET /api/collections',
                    'POST /api/query',
                    'POST /api/documents'
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
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """启动Web服务"""
        logger.info(f"🚀 启动CategoryRAG Web服务: http://{host}:{port}")
        logger.info("📋 可用API端点:")
        logger.info("   GET  /api/health      - 健康检查")
        logger.info("   GET  /api/status      - 系统状态")
        logger.info("   GET  /api/collections - 集合信息")
        logger.info("   POST /api/query       - 问答查询")
        logger.info("   POST /api/documents   - 文档添加")
        
        self.app.run(host=host, port=port, debug=debug)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='CategoryRAG统一Web服务')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--regulatory', action='store_true', help='启用监管报送功能')

    args = parser.parse_args()

    # 确保日志目录存在
    Path('logs').mkdir(exist_ok=True)

    try:
        # 创建并启动Web服务
        web_service = CategoryRAGWebService(enable_regulatory=args.regulatory)

        if args.regulatory:
            logger.info("🏛️ 启用监管报送功能")
            logger.info("📋 额外API端点:")
            logger.info("   POST /api/analyze     - 监管文档分析")
            logger.info("   GET  /api/templates   - 报表模板")
            logger.info("   POST /api/validate    - 数据验证")
            logger.info("   POST /api/upload      - 文档上传")
            logger.info("   GET  /api/history     - 分析历史")
            logger.info("   GET  /api/reports     - 报表列表")

        web_service.run(host=args.host, port=args.port, debug=args.debug)

    except KeyboardInterrupt:
        logger.info("👋 Web服务已停止")
    except Exception as e:
        logger.error(f"❌ Web服务启动失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
