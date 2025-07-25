#!/usr/bin/env python3
"""
Collection（集合）概念演示
"""

def demo_collection_concept():
    """演示Collection概念和作用"""
    print("📚 CategoryRAG Collection（集合）概念演示")
    print("=" * 60)
    
    print("🎯 什么是Collection？")
    print("Collection是文档的逻辑分组，类似于图书馆的不同书架：")
    print()
    
    # 现有集合示例
    collections = [
        {
            "name": "1104报表_2024版",
            "id": "report_1104_2024", 
            "keywords": ["1104", "报表", "2024", "最新版"],
            "docs": 207,
            "description": "银行业监管统计报表制度2024版"
        },
        {
            "name": "人民银行金融统计制度汇编",
            "id": "pboc_statistics",
            "keywords": ["人行", "央行", "统计制度", "金融统计"],
            "docs": 104,
            "description": "人民银行金融统计制度相关文档"
        },
        {
            "name": "EAST数据结构",
            "id": "east_data_structure",
            "keywords": ["EAST", "数据结构", "报送系统"],
            "docs": 52,
            "description": "EAST系统数据结构文档"
        }
    ]
    
    print("📋 现有Collection示例：")
    for i, col in enumerate(collections, 1):
        print(f"\n{i}. {col['name']}")
        print(f"   ID: {col['id']}")
        print(f"   文档数: {col['docs']}个")
        print(f"   关键词: {', '.join(col['keywords'])}")
        print(f"   描述: {col['description']}")

def demo_smart_routing():
    """演示智能路由机制"""
    print("\n🧠 智能文档路由演示")
    print("=" * 40)
    
    test_queries = [
        {
            "query": "1104报表G01表的填报要求",
            "matched_collections": ["1104报表_2024版", "1104报表_2022版"],
            "reason": "包含关键词：1104、报表"
        },
        {
            "query": "人民银行统计制度中的贷款分类",
            "matched_collections": ["人民银行金融统计制度汇编"],
            "reason": "包含关键词：人民银行、统计制度"
        },
        {
            "query": "EAST系统数据字段说明",
            "matched_collections": ["EAST数据结构", "EAST元数据说明"],
            "reason": "包含关键词：EAST、数据"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n📝 查询{i}: {test['query']}")
        print(f"🎯 匹配集合: {', '.join(test['matched_collections'])}")
        print(f"💡 匹配原因: {test['reason']}")
        print(f"✅ 效果: 只在相关文档中检索，提高准确性和速度")

def demo_adding_new_collection():
    """演示添加新Collection的过程"""
    print("\n➕ 添加新Collection演示")
    print("=" * 35)
    
    print("假设您要添加一个新的监管文件：")
    print()
    
    print("📄 新文档: 银行理财产品管理办法.pdf")
    print()
    
    print("🔧 添加命令:")
    print("python3 scripts/add_document_workflow.py \\")
    print("  --file '银行理财产品管理办法.pdf' \\")
    print("  --collection-name '银行理财产品管理办法' \\")
    print("  --keywords '理财产品,管理办法,银行理财'")
    print()
    
    print("📊 系统会自动:")
    print("1. 创建新Collection:")
    print("   - 名称: 银行理财产品管理办法")
    print("   - ID: bank_wealth_management_regulation")
    print("   - 关键词: [理财产品, 管理办法, 银行理财]")
    print()
    
    print("2. 处理文档:")
    print("   - 转换为Markdown格式")
    print("   - 智能分块处理")
    print("   - 提取TOC目录结构")
    print("   - 生成向量并存储")
    print()
    
    print("3. 更新系统配置:")
    print("   - 添加到config.yaml")
    print("   - 配置关键词映射")
    print("   - 启用智能路由")

def demo_collection_benefits():
    """演示Collection的优势"""
    print("\n🎉 Collection机制的优势")
    print("=" * 30)
    
    benefits = [
        {
            "title": "🎯 精准检索",
            "description": "只在相关文档中搜索，避免无关结果",
            "example": "问1104报表问题时，不会搜索EAST文档"
        },
        {
            "title": "⚡ 提升速度", 
            "description": "减少搜索范围，提高响应速度",
            "example": "从1000个文档缩小到200个相关文档"
        },
        {
            "title": "📊 智能分类",
            "description": "自动识别问题类型，选择合适的文档集",
            "example": "自动区分监管报表、统计制度、数据结构等"
        },
        {
            "title": "🔧 易于管理",
            "description": "文档按主题分组，便于维护和更新",
            "example": "可以单独更新某个Collection而不影响其他"
        },
        {
            "title": "🎨 个性化配置",
            "description": "每个Collection可以有不同的配置和优先级",
            "example": "新版本文档优先级高于旧版本"
        }
    ]
    
    for benefit in benefits:
        print(f"\n{benefit['title']}")
        print(f"   {benefit['description']}")
        print(f"   💡 例如: {benefit['example']}")

def main():
    """主函数"""
    demo_collection_concept()
    demo_smart_routing()
    demo_adding_new_collection()
    demo_collection_benefits()
    
    print("\n" + "=" * 60)
    print("🎓 总结:")
    print("Collection是CategoryRAG的核心概念，它让系统能够:")
    print("• 智能地将问题路由到相关文档")
    print("• 提供更精准、更快速的检索结果")
    print("• 支持灵活的文档分组和管理")
    print()
    print("💡 使用建议:")
    print("• 按业务领域或文档类型创建Collection")
    print("• 设置清晰的关键词帮助智能分类")
    print("• 定期维护和优化Collection配置")

if __name__ == "__main__":
    main()
