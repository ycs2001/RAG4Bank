"""
配置管理命令 - 增强版
"""

import json
import yaml
from pathlib import Path
from .base_command import BaseCommand
from ..utils.cli_utils import CLIUtils
from ...config.config_validator import ConfigValidator, ConfigMigrator
from ...config.prompt_manager import PromptManager
from ...config.dynamic_config_manager import DynamicConfigManager

class ConfigCommand(BaseCommand):
    """配置管理命令"""

    def __init__(self, config_manager, args):
        super().__init__(config_manager, args)
        self.cli_utils = CLIUtils()
        self.validator = ConfigValidator()
        self.migrator = ConfigMigrator()

    def execute(self):
        """执行配置管理"""
        action = getattr(self.args, 'config_action', 'show')

        if action == 'show':
            section = getattr(self.args, 'section', None)
            format_type = getattr(self.args, 'format', 'yaml')
            self.show_config(section, format_type)
        elif action == 'validate':
            config_file = getattr(self.args, 'config_file', 'unified_config.yaml')
            self.validate_config(config_file)
        elif action == 'migrate':
            source = getattr(self.args, 'source', None)
            target = getattr(self.args, 'target', None)
            self.migrate_config(source, target)
        elif action == 'prompts':
            prompt_action = getattr(self.args, 'prompt_action', 'list')
            category = getattr(self.args, 'category', None)
            name = getattr(self.args, 'name', None)
            self.manage_prompts(prompt_action, category, name)
        elif action == 'dynamic':
            dynamic_action = getattr(self.args, 'dynamic_action', 'status')
            self.manage_dynamic_config(dynamic_action)
        elif action == 'set':
            key = getattr(self.args, 'key', None)
            value = getattr(self.args, 'value', None)
            if key and value:
                self.set_config(key, value)
            else:
                print("❌ 请指定配置键和值")
        else:
            print("❌ 未知的配置操作")
            self._show_help()

    def show_config(self, section: str = None, format_type: str = "yaml"):
        """显示配置信息"""
        try:
            print("📋 CategoryRAG 配置信息")
            print("=" * 50)

            if section:
                # 显示特定章节
                config_value = self.config_manager.get(section)
                if config_value is None:
                    print(f"❌ 配置章节不存在: {section}")
                    return

                print(f"📄 配置章节: {section}")
                print("-" * 30)
                self._display_config(config_value, format_type)
            else:
                # 显示主要配置项
                self._show_main_config()

        except Exception as e:
            print(f"❌ 显示配置失败: {e}")

    def _show_main_config(self):
        """显示主要配置项"""
        config_items = [
            ("系统名称", "system.name"),
            ("系统版本", "system.version"),
            ("环境", "system.environment"),
            ("BGE模型路径", "embedding.model.path"),
            ("检索数量", "retrieval.top_k"),
            ("相似度阈值", "retrieval.similarity_threshold"),
            ("重排器启用", "reranker.enabled"),
            ("LLM提供商", "llm.primary.provider"),
            ("动态配置启用", "dynamic_documents.auto_update.enabled"),
            ("Prompt配置文件", "prompts.config_file")
        ]

        for name, path in config_items:
            value = self.config_manager.get(path)
            status = "✅" if value else "❌"
            print(f"  {status} {name}: {value}")

    def validate_config(self, config_file: str = "unified_config.yaml"):
        """验证配置文件"""
        try:
            print("🔍 验证配置文件...")
            print("=" * 50)

            result = self.validator.validate_config(config_file)

            # 显示验证结果
            if result["valid"]:
                print("✅ 配置文件验证通过")
            else:
                print("❌ 配置文件验证失败")

            # 显示错误
            if result["errors"]:
                print(f"\n🚨 错误 ({len(result['errors'])}个):")
                for i, error in enumerate(result["errors"], 1):
                    print(f"   {i}. {error}")

            # 显示警告
            if result["warnings"]:
                print(f"\n⚠️ 警告 ({len(result['warnings'])}个):")
                for i, warning in enumerate(result["warnings"], 1):
                    print(f"   {i}. {warning}")

            # 显示建议
            if result["suggestions"]:
                print(f"\n💡 建议 ({len(result['suggestions'])}个):")
                for i, suggestion in enumerate(result["suggestions"], 1):
                    print(f"   {i}. {suggestion}")

            # 显示元数据
            if result["metadata"]:
                print(f"\n📊 配置元数据:")
                for key, value in result["metadata"].items():
                    print(f"   {key}: {value}")

        except Exception as e:
            print(f"❌ 配置验证失败: {e}")

    def migrate_config(self, source: str = None, target: str = None):
        """迁移配置文件"""
        try:
            print("🔄 配置文件迁移...")
            print("=" * 50)

            # 确认迁移操作
            if not self.cli_utils.confirm("确认执行配置迁移操作？这将备份原配置文件"):
                print("⚠️ 迁移操作已取消")
                return

            # 执行迁移
            success = self.migrator.migrate_to_v2(
                source or "unified_config.yaml",
                target or "unified_config_v2.yaml"
            )

            if success:
                print("✅ 配置迁移成功")
                print("💡 建议运行 'categoryrag config validate' 验证迁移结果")
            else:
                print("❌ 配置迁移失败")

        except Exception as e:
            print(f"❌ 配置迁移失败: {e}")

    def manage_prompts(self, action: str, category: str = None, name: str = None):
        """管理Prompt配置"""
        try:
            prompt_manager = PromptManager()

            if action == "list":
                self._list_prompts(prompt_manager)
            elif action == "show":
                self._show_prompt(prompt_manager, category, name)
            elif action == "validate":
                self._validate_prompts(prompt_manager)
            elif action == "reload":
                self._reload_prompts(prompt_manager)
            else:
                print(f"❌ 未知的Prompt操作: {action}")
                print("💡 可用操作: list, show, validate, reload")

        except Exception as e:
            print(f"❌ Prompt管理失败: {e}")

    def _list_prompts(self, prompt_manager: PromptManager):
        """列出所有Prompt模板"""
        print("📋 可用的Prompt模板")
        print("=" * 50)

        available = prompt_manager.list_available_prompts()

        for category, prompts in available.items():
            print(f"\n📁 {category}:")
            for prompt_name in prompts:
                info = prompt_manager.get_prompt_info(category, prompt_name)
                variables = info.get('variables', [])
                print(f"   📄 {prompt_name}")
                if variables:
                    print(f"      变量: {', '.join(variables)}")

    def _show_prompt(self, prompt_manager: PromptManager, category: str, name: str):
        """显示特定Prompt模板"""
        if not category or not name:
            print("❌ 请指定分类和名称")
            print("💡 用法: categoryrag config prompts show <category> <name>")
            return

        print(f"📄 Prompt模板: {category}.{name}")
        print("=" * 50)

        info = prompt_manager.get_prompt_info(category, name)
        if not info:
            print(f"❌ Prompt模板不存在: {category}.{name}")
            return

        # 显示模板信息
        print(f"分类: {info['category']}")
        print(f"名称: {info['name']}")
        print(f"变量: {', '.join(info.get('variables', []))}")
        print(f"模板长度: {info['template_length']} 字符")

        # 显示模板内容（截取前500字符）
        try:
            template = prompt_manager.get_prompt(category, name, {})
            print(f"\n模板内容:")
            print("-" * 30)
            if len(template) > 500:
                print(template[:500] + "...")
                print(f"[已截取，完整长度: {len(template)} 字符]")
            else:
                print(template)
        except Exception as e:
            print(f"⚠️ 无法显示模板内容: {e}")

    def _validate_prompts(self, prompt_manager: PromptManager):
        """验证Prompt配置"""
        print("🔍 验证Prompt配置...")
        print("=" * 50)

        result = prompt_manager.validate_prompts()

        if result["valid"]:
            print("✅ Prompt配置验证通过")
        else:
            print("❌ Prompt配置验证失败")

        # 显示错误和警告
        for error in result.get("errors", []):
            print(f"🚨 错误: {error}")

        for warning in result.get("warnings", []):
            print(f"⚠️ 警告: {warning}")

        # 显示统计信息
        stats = result.get("statistics", {})
        if stats:
            print(f"\n📊 统计信息:")
            print(f"   总模板数: {stats.get('total_prompts', 0)}")
            print(f"   分类数: {stats.get('categories', 0)}")
            print(f"   全局变量数: {stats.get('global_variables', 0)}")

    def _reload_prompts(self, prompt_manager: PromptManager):
        """重新加载Prompt配置"""
        print("🔄 重新加载Prompt配置...")

        try:
            prompt_manager.reload_prompts()
            print("✅ Prompt配置重新加载成功")
        except Exception as e:
            print(f"❌ 重新加载失败: {e}")

    def manage_dynamic_config(self, action: str):
        """管理动态配置"""
        try:
            dynamic_manager = DynamicConfigManager()

            if action == "status":
                self._show_dynamic_status(dynamic_manager)
            elif action == "cleanup":
                self._cleanup_dynamic_config(dynamic_manager)
            else:
                print(f"❌ 未知的动态配置操作: {action}")
                print("💡 可用操作: status, cleanup")

        except Exception as e:
            print(f"❌ 动态配置管理失败: {e}")

    def _show_dynamic_status(self, dynamic_manager: DynamicConfigManager):
        """显示动态配置状态"""
        print("📊 动态配置状态")
        print("=" * 50)

        # 加载动态配置
        dynamic_config = dynamic_manager._load_dynamic_config()

        # 显示文档注册表
        registry = dynamic_config.get("document_registry", {})
        print(f"📄 文档注册表: {len(registry)} 个文档")

        if registry:
            print("\n最近添加的文档:")
            sorted_docs = sorted(
                registry.items(),
                key=lambda x: x[1].get("added_at", ""),
                reverse=True
            )[:5]

            for doc_name, doc_info in sorted_docs:
                added_at = doc_info.get("added_at", "未知")[:19]  # 截取日期时间
                collection = doc_info.get("collection_name", "未知")
                print(f"   📄 {doc_name} -> {collection} ({added_at})")

        # 显示自动生成的集合
        auto_collections = dynamic_config.get("auto_generated_collections", {})
        print(f"\n🤖 自动生成集合: {len(auto_collections)} 个")

    def _cleanup_dynamic_config(self, dynamic_manager: DynamicConfigManager):
        """清理动态配置"""
        print("🧹 清理动态配置...")

        if not self.cli_utils.confirm("确认清理动态配置？这将删除文档注册表和自动生成的配置"):
            print("⚠️ 清理操作已取消")
            return

        try:
            # 重置动态配置
            dynamic_manager.dynamic_config = {
                'version': '1.0',
                'created_at': dynamic_manager.dynamic_config.get('created_at'),
                'document_registry': {},
                'auto_generated_collections': {},
                'keyword_suggestions': {}
            }

            dynamic_manager._save_dynamic_config()
            print("✅ 动态配置清理完成")

        except Exception as e:
            print(f"❌ 清理失败: {e}")

    def set_config(self, key: str, value: str):
        """设置配置项"""
        try:
            print(f"⚙️ 设置配置项: {key} = {value}")

            # 尝试解析值的类型
            parsed_value = self._parse_value(value)

            # 设置配置
            self.config_manager.set(key, parsed_value)

            print("✅ 配置项设置成功")
            print("💡 建议运行 'categoryrag config validate' 验证配置")

        except Exception as e:
            print(f"❌ 设置配置项失败: {e}")

    def _parse_value(self, value: str):
        """解析配置值的类型"""
        # 尝试解析为不同类型
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        try:
            # 尝试解析为整数
            return int(value)
        except ValueError:
            pass

        try:
            # 尝试解析为浮点数
            return float(value)
        except ValueError:
            pass

        # 默认为字符串
        return value

    def _display_config(self, config, format_type: str):
        """显示配置内容"""
        if format_type == "json":
            print(json.dumps(config, ensure_ascii=False, indent=2))
        elif format_type == "yaml":
            print(yaml.dump(config, allow_unicode=True, indent=2, sort_keys=False))
        else:
            print(f"❌ 不支持的格式: {format_type}")

    def _show_help(self):
        """显示帮助信息"""
        print("📖 配置管理命令帮助")
        print("=" * 50)
        print("可用操作:")
        print("  show [section] [--format yaml|json]  - 显示配置")
        print("  validate [config_file]              - 验证配置文件")
        print("  migrate [source] [target]           - 迁移配置文件")
        print("  prompts list|show|validate|reload   - 管理Prompt")
        print("  dynamic status|cleanup              - 管理动态配置")
        print("  set <key> <value>                   - 设置配置项")
