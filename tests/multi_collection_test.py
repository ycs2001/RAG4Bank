#!/usr/bin/env python3
"""
多库智能检索系统测试脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import RAGSystem, ConfigManager
from src.utils import setup_logging

# 设置日志
setup_logging("INFO")
logger = logging.getLogger(__name__)

class MultiCollectionTester:
    """多集合测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.config_manager = ConfigManager()
        self.rag_system = RAGSystem(self.config_manager)
        
        # 测试查询集合
        self.test_queries = [
            # 主题明确的查询
            {
                'query': '1104报表中资本充足率如何计算？',
                'expected_collections': ['report_1104_2024'],
                'description': '1104报表相关查询'
            },
            {
                'query': 'EAST系统的数据结构包括哪些字段？',
                'expected_collections': ['east_data_structure'],
                'description': 'EAST数据结构查询'
            },
            {
                'query': '人民银行金融统计制度的报送要求是什么？',
                'expected_collections': ['pboc_statistics'],
                'description': '人民银行统计制度查询'
            },
            {
                'query': '一表通产品映射关系如何配置？',
                'expected_collections': ['ybt_product_mapping'],
                'description': '一表通产品映射查询'
            },
            
            # 版本对比查询
            {
                'query': '2024版和2022版1104报表有什么区别？',
                'expected_collections': ['report_1104_2024', 'report_1104_2022'],
                'description': '版本对比查询'
            },
            
            # 跨领域查询
            {
                'query': 'EAST和一表通系统的数据结构有什么不同？',
                'expected_collections': ['east_data_structure', 'ybt_data_structure'],
                'description': '跨系统对比查询'
            },
            
            # 模糊查询
            {
                'query': '银行监管报表的填报要求',
                'expected_collections': None,  # 可能触发不确定分类
                'description': '模糊查询'
            }
        ]
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 多库智能检索系统测试")
        print("=" * 60)
        
        # 1. 系统状态检查
        self._test_system_status()
        
        # 2. 主题分类测试
        self._test_topic_classification()
        
        # 3. 智能检索测试
        self._test_intelligent_retrieval()
        
        # 4. 手动指定集合测试
        self._test_manual_collection_selection()
        
        # 5. 性能对比测试
        self._test_performance_comparison()
        
        print("\n🎉 所有测试完成！")
    
    def _test_system_status(self):
        """测试系统状态"""
        print("\n📊 1. 系统状态检查")
        print("-" * 30)
        
        try:
            stats = self.rag_system.get_system_stats()
            
            print(f"系统名称: {stats['system']['name']}")
            print(f"系统版本: {stats['system']['version']}")
            print(f"检索策略: {stats['config'].get('retrieval_strategy', 'N/A')}")
            
            # 检索器统计
            retriever_stats = stats.get('retriever', {})
            if 'collections' in retriever_stats:
                print(f"总文档数: {retriever_stats['total_documents']}")
                print("集合分布:")
                for collection_id, collection_info in retriever_stats['collections'].items():
                    print(f"  - {collection_id}: {collection_info['document_count']} 个文档")
            
            print("✅ 系统状态正常")
            
        except Exception as e:
            print(f"❌ 系统状态检查失败: {e}")
    
    def _test_topic_classification(self):
        """测试主题分类"""
        print("\n🎯 2. 主题分类测试")
        print("-" * 30)
        
        for test_case in self.test_queries:
            query = test_case['query']
            expected = test_case['expected_collections']
            description = test_case['description']
            
            print(f"\n查询: {query}")
            print(f"描述: {description}")
            
            try:
                # 执行分类
                classification = self.rag_system.classify_query(query)
                
                if classification:
                    print(f"分类结果: {classification.collections}")
                    print(f"置信度: {classification.confidence:.2f}")
                    print(f"推理: {classification.reasoning}")
                    
                    # 验证结果
                    if expected:
                        if set(classification.collections) == set(expected):
                            print("✅ 分类正确")
                        else:
                            print(f"⚠️ 分类不完全匹配，期望: {expected}")
                    else:
                        print("ℹ️ 模糊查询，分类结果仅供参考")
                else:
                    print("❌ 分类器未启用或分类失败")
                    
            except Exception as e:
                print(f"❌ 分类测试失败: {e}")
    
    def _test_intelligent_retrieval(self):
        """测试智能检索"""
        print("\n🔍 3. 智能检索测试")
        print("-" * 30)
        
        for i, test_case in enumerate(self.test_queries[:3], 1):  # 测试前3个查询
            query = test_case['query']
            description = test_case['description']
            
            print(f"\n测试 {i}: {description}")
            print(f"查询: {query}")
            
            try:
                # 执行智能检索
                response = self.rag_system.answer_question(query)
                
                print(f"检索到文档: {response.retrieval_count} 个")
                print(f"处理时间: {response.processing_time:.2f}秒")
                
                # 显示来源信息
                if response.sources:
                    print("来源集合:")
                    collections = set()
                    for source in response.sources:
                        collections.add(source.get('collection', '未知'))
                    for collection in collections:
                        print(f"  - {collection}")
                
                # 显示回答摘要
                answer_preview = response.answer[:200] + "..." if len(response.answer) > 200 else response.answer
                print(f"回答摘要: {answer_preview}")
                
                print("✅ 智能检索成功")
                
            except Exception as e:
                print(f"❌ 智能检索失败: {e}")
    
    def _test_manual_collection_selection(self):
        """测试手动集合选择"""
        print("\n🎯 4. 手动集合选择测试")
        print("-" * 30)
        
        test_cases = [
            {
                'query': '资本充足率计算方法',
                'collections': ['report_1104_2024'],
                'description': '指定2024版1104报表'
            },
            {
                'query': '数据字段说明',
                'collections': ['east_metadata', 'ybt_data_structure'],
                'description': '指定EAST元数据和一表通数据结构'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case['query']
            collections = test_case['collections']
            description = test_case['description']
            
            print(f"\n测试 {i}: {description}")
            print(f"查询: {query}")
            print(f"指定集合: {collections}")
            
            try:
                # 手动指定集合检索
                response = self.rag_system.search_with_collections(
                    query=query,
                    collection_ids=collections
                )
                
                print(f"检索到文档: {response.retrieval_count} 个")
                print(f"处理时间: {response.processing_time:.2f}秒")
                
                # 验证来源集合
                actual_collections = set()
                for source in response.sources:
                    actual_collections.add(source.get('collection', '未知'))
                
                if actual_collections.intersection(set(collections)):
                    print("✅ 手动集合选择成功")
                else:
                    print("⚠️ 返回结果的集合与指定不符")
                
            except Exception as e:
                print(f"❌ 手动集合选择失败: {e}")
    
    def _test_performance_comparison(self):
        """测试性能对比"""
        print("\n⚡ 5. 性能对比测试")
        print("-" * 30)
        
        test_query = "1104报表资本充足率计算"
        
        try:
            # 智能检索
            print("智能检索模式:")
            response1 = self.rag_system.answer_question(test_query)
            print(f"  处理时间: {response1.processing_time:.2f}秒")
            print(f"  检索文档: {response1.retrieval_count} 个")
            
            # 手动指定集合
            print("\n手动指定集合模式:")
            response2 = self.rag_system.search_with_collections(
                query=test_query,
                collection_ids=['report_1104_2024']
            )
            print(f"  处理时间: {response2.processing_time:.2f}秒")
            print(f"  检索文档: {response2.retrieval_count} 个")
            
            # 性能对比
            if response1.processing_time > 0 and response2.processing_time > 0:
                speedup = response1.processing_time / response2.processing_time
                print(f"\n性能对比: 手动指定比智能检索快 {speedup:.1f}x")
            
            print("✅ 性能对比完成")
            
        except Exception as e:
            print(f"❌ 性能对比失败: {e}")

def main():
    """主函数"""
    print("🎯 多库智能检索系统测试工具")
    print("=" * 50)
    
    try:
        tester = MultiCollectionTester()
        tester.run_all_tests()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
