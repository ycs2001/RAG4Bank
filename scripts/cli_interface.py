#!/usr/bin/env python3
"""
RAG系统命令行工具
"""

import sys
import os
import argparse
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.config import ConfigManager
from src.core.unified_rag_system import UnifiedRAGSystem
import logging

def setup_logging(level: str, log_file: str = None):
    """简单的日志设置"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=log_file
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RAG智能问答系统")
    
    # 基本参数
    parser.add_argument("--config", "-c", help="配置文件路径")
    parser.add_argument("--query", "-q", help="问题查询")
    parser.add_argument("--document", "-d", help="指定文档过滤")
    parser.add_argument("--top-k", "-k", type=int, help="检索文档数量")
    parser.add_argument("--temperature", "-t", type=float, help="生成温度")
    
    # 输出格式
    parser.add_argument("--format", "-f", 
                       choices=["console", "json", "simple"],
                       default="console",
                       help="输出格式")
    
    # 系统操作
    parser.add_argument("--stats", action="store_true", help="显示系统统计信息")
    parser.add_argument("--health", action="store_true", help="健康检查")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    
    # 日志配置
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="日志级别")
    parser.add_argument("--log-file", help="日志文件路径")
    
    args = parser.parse_args()
    
    try:
        # 设置日志
        setup_logging(args.log_level, args.log_file)
        
        # 加载配置
        config_manager = ConfigManager()
        if args.config:
            config_manager.load_config(args.config)
        
        # 应用命令行参数覆盖
        if args.top_k:
            config_manager.set('retrieval.top_k', args.top_k)
        if args.temperature:
            config_manager.set('llm.qwen.temperature', args.temperature)
        
        # 初始化RAG系统
        print("🔄 正在初始化RAG系统...")
        rag_system = UnifiedRAGSystem(config_manager)
        print("✅ 系统初始化完成！")
        
        # 执行操作
        if args.stats:
            # 显示统计信息
            stats = rag_system.get_system_status()
            if args.format == "json":
                print(json.dumps(stats, indent=2, ensure_ascii=False))
            else:
                print("📊 系统状态:")
                print(f"   系统类型: {stats.get('system_type', 'Unknown')}")
                print(f"   配置参数: top_k={stats.get('configuration', {}).get('top_k', 'N/A')}")
                print(f"   组件状态:")
                for comp, status in stats.get('components', {}).items():
                    status_icon = "✅" if status else "❌"
                    print(f"     {comp}: {status_icon}")

        elif args.health:
            # 健康检查（简化版）
            stats = rag_system.get_system_status()
            components = stats.get('components', {})
            all_healthy = all(components.values())

            if args.format == "json":
                health_data = {"overall": all_healthy, "components": components}
                print(json.dumps(health_data, indent=2, ensure_ascii=False))
            else:
                status = "✅ 健康" if all_healthy else "❌ 不健康"
                print(f"系统状态: {status}")
                for component, healthy in components.items():
                    comp_status = "✅" if healthy else "❌"
                    print(f"  {component}: {comp_status}")

        elif args.query:
            # 单次查询
            response = rag_system.answer_question(args.query)

            # 格式化输出
            if args.format == "json":
                response_data = {
                    "answer": response.answer,
                    "retrieval_count": response.retrieval_count,
                    "processing_time": response.processing_time,
                    "collections_used": response.collections_used,
                    "metadata": response.metadata
                }
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
            elif args.format == "simple":
                print(response.answer)
            else:
                print(f"\n📋 回答:")
                print(f"{response.answer}")
                print(f"\n📊 检索信息:")
                print(f"   检索结果: {response.retrieval_count} 个文档片段")
                print(f"   使用集合: {response.collections_used}")
                print(f"   处理时间: {response.processing_time:.2f} 秒")
        
        elif args.interactive:
            # 交互模式
            run_interactive_mode(rag_system, args.format)
        
        else:
            # 显示帮助
            parser.print_help()
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

def run_interactive_mode(rag_system: UnifiedRAGSystem, output_format: str):
    """运行交互模式"""
    print("\n🎯 CategoryRAG智能问答系统 - 交互模式")
    print("💡 专业领域：银行监管报表、EAST系统、人民银行统计制度")
    print("📝 输入 'quit' 退出，'help' 查看帮助，'stats' 查看统计")
    print("🚀 支持查询增强：基于文档目录结构的智能检索")
    
    while True:
        try:
            user_input = input("\n🔍 请输入您的问题: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif user_input.lower() == 'stats':
                stats = rag_system.get_system_status()
                print("📊 系统状态:")
                print(f"   系统类型: {stats.get('system_type', 'Unknown')}")
                print(f"   配置参数: top_k={stats.get('configuration', {}).get('top_k', 'N/A')}")
                print(f"   组件状态:")
                for comp, status in stats.get('components', {}).items():
                    status_icon = "✅" if status else "❌"
                    print(f"     {comp}: {status_icon}")
                continue
            elif not user_input:
                continue
            
            # 全局检索（简化，移除文档特定查询功能）
            response = rag_system.answer_question(user_input)

            # 格式化输出
            if output_format == "json":
                response_data = {
                    "answer": response.answer,
                    "retrieval_count": response.retrieval_count,
                    "processing_time": response.processing_time,
                    "collections_used": response.collections_used,
                    "metadata": response.metadata
                }
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
            elif output_format == "simple":
                print(response.answer)
            else:
                print(f"\n📋 回答:")
                print(f"{response.answer}")
                print(f"\n📊 检索信息:")
                print(f"   检索结果: {response.retrieval_count} 个文档片段")
                print(f"   使用集合: {response.collections_used}")
                print(f"   处理时间: {response.processing_time:.2f} 秒")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ 处理问题时发生错误: {e}")
    
    print("\n👋 感谢使用RAG智能问答系统！")

def print_help():
    """打印帮助信息"""
    print("""
🆘 交互模式帮助:
- 直接输入问题进行查询
- 输入 'stats' 查看系统统计信息
- 输入 'quit' 或 'exit' 退出

💡 示例问题:
  * 普惠金融领域贷款涉及哪些报送表？
  * 1104报表的资本充足率如何计算？
  * EAST系统的数据报送要求是什么？
  * 人民银行A1411报表与金监局G01_V报表的贷款余额差异

🚀 查询增强功能:
  系统会自动基于文档目录结构增强您的查询，提供更精准的答案
    """)

if __name__ == "__main__":
    main()
