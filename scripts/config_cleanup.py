#!/usr/bin/env python3
"""
配置文件清理脚本
安全删除冗余配置文件并整合配置项
"""

import os
import yaml
import shutil
from pathlib import Path
from datetime import datetime

class ConfigCleaner:
    """配置文件清理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.backup_dir = Path(f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
    def analyze_redundancy(self):
        """分析配置冗余"""
        print("🔍 分析配置文件冗余...")
        
        # 读取所有配置文件
        configs = {}
        for config_file in self.config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    configs[config_file.name] = yaml.safe_load(f)
                print(f"   ✅ 读取: {config_file.name}")
            except Exception as e:
                print(f"   ❌ 读取失败: {config_file.name} - {e}")
        
        # 分析重复配置项
        redundant_items = self._find_redundant_items(configs)
        
        print(f"\n📊 冗余分析结果:")
        for item, files in redundant_items.items():
            if len(files) > 1:
                print(f"   🔄 重复项 '{item}': {', '.join(files)}")
        
        return redundant_items
    
    def _find_redundant_items(self, configs: dict) -> dict:
        """查找重复配置项"""
        redundant = {}
        
        def extract_keys(data, prefix=""):
            """递归提取配置键"""
            keys = []
            if isinstance(data, dict):
                for key, value in data.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    keys.append(full_key)
                    if isinstance(value, dict):
                        keys.extend(extract_keys(value, full_key))
            return keys
        
        # 提取所有配置键
        all_keys = {}
        for filename, config in configs.items():
            if config:
                keys = extract_keys(config)
                for key in keys:
                    if key not in all_keys:
                        all_keys[key] = []
                    all_keys[key].append(filename)
        
        # 找出重复项
        for key, files in all_keys.items():
            if len(files) > 1:
                redundant[key] = files
        
        return redundant
    
    def create_backup(self):
        """创建备份"""
        print(f"💾 创建配置备份: {self.backup_dir}")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        shutil.copytree(self.config_dir, self.backup_dir)
        print(f"   ✅ 备份完成")
    
    def identify_obsolete_files(self):
        """识别过时的配置文件"""
        print("🗑️ 识别过时配置文件...")
        
        # 基于CLI 2.0的使用情况分析
        file_status = {
            "config.yaml": {
                "status": "legacy",
                "reason": "被unified_config.yaml替代，仅作回退使用",
                "action": "保留但标记为遗留"
            },
            "unified_config.yaml": {
                "status": "active",
                "reason": "CLI 2.0主要配置文件",
                "action": "保留并优化"
            },
            "version_mapping.yaml": {
                "status": "orphaned",
                "reason": "未被CLI系统集成使用",
                "action": "集成到unified_config.yaml"
            }
        }
        
        for filename, info in file_status.items():
            file_path = self.config_dir / filename
            if file_path.exists():
                print(f"   📄 {filename}: {info['status']} - {info['reason']}")
        
        return file_status
    
    def safe_cleanup(self, dry_run: bool = True):
        """安全清理配置文件"""
        print(f"🧹 开始配置清理 {'(预览模式)' if dry_run else '(执行模式)'}")
        
        if not dry_run:
            self.create_backup()
        
        file_status = self.identify_obsolete_files()
        
        # 执行清理操作
        for filename, info in file_status.items():
            file_path = self.config_dir / filename
            
            if not file_path.exists():
                continue
                
            if info["action"] == "集成到unified_config.yaml":
                print(f"   🔄 需要集成: {filename}")
                if not dry_run:
                    self._integrate_config(filename)
            
            elif info["action"] == "保留但标记为遗留":
                print(f"   📝 标记为遗留: {filename}")
                if not dry_run:
                    self._mark_as_legacy(filename)
        
        print(f"✅ 清理完成")
    
    def _integrate_config(self, filename: str):
        """集成配置文件到unified_config.yaml"""
        source_path = self.config_dir / filename
        target_path = self.config_dir / "unified_config.yaml"
        
        # 读取源配置
        with open(source_path, 'r', encoding='utf-8') as f:
            source_config = yaml.safe_load(f)
        
        # 读取目标配置
        with open(target_path, 'r', encoding='utf-8') as f:
            target_config = yaml.safe_load(f)
        
        # 集成配置（这里需要根据具体文件实现）
        if filename == "version_mapping.yaml":
            # 将版本映射集成到unified_config.yaml
            if 'version_mapping' not in target_config:
                target_config['version_mapping'] = source_config.get('version_mapping', {})
            if 'version_strategies' not in target_config:
                target_config['version_strategies'] = source_config.get('version_strategies', {})
        
        # 写回目标配置
        with open(target_path, 'w', encoding='utf-8') as f:
            yaml.dump(target_config, f, allow_unicode=True, indent=2, sort_keys=False)
        
        print(f"   ✅ 已集成 {filename} 到 unified_config.yaml")
    
    def _mark_as_legacy(self, filename: str):
        """标记文件为遗留"""
        file_path = self.config_dir / filename
        legacy_path = self.config_dir / f"legacy_{filename}"
        
        # 添加遗留标记注释
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        legacy_header = f"""# ⚠️ 遗留配置文件 - 仅作回退使用
# 此文件已被 unified_config.yaml 替代
# 请优先使用 unified_config.yaml 进行配置
# 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
"""
        
        with open(legacy_path, 'w', encoding='utf-8') as f:
            f.write(legacy_header + content)
        
        print(f"   ✅ 已标记 {filename} 为遗留文件")
    
    def validate_cleanup(self):
        """验证清理结果"""
        print("✅ 验证清理结果...")
        
        # 检查CLI系统是否仍能正常加载配置
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from src.config.enhanced_config_manager import EnhancedConfigManager
            
            config_manager = EnhancedConfigManager()
            print("   ✅ 配置管理器加载成功")
            
            # 验证关键配置项
            key_configs = [
                "system.name",
                "embedding.model.path", 
                "retrieval.top_k",
                "llm.primary.provider"
            ]
            
            for key in key_configs:
                value = config_manager.get(key)
                if value is not None:
                    print(f"   ✅ 配置项 {key}: {value}")
                else:
                    print(f"   ⚠️ 配置项 {key}: 未找到")
            
        except Exception as e:
            print(f"   ❌ 配置验证失败: {e}")
            return False
        
        return True

def main():
    """主函数"""
    cleaner = ConfigCleaner()
    
    print("🔧 CategoryRAG 配置文件清理工具")
    print("=" * 50)
    
    # 1. 分析冗余
    cleaner.analyze_redundancy()
    
    # 2. 预览清理
    print("\n" + "=" * 50)
    cleaner.safe_cleanup(dry_run=True)
    
    # 3. 确认执行
    print("\n" + "=" * 50)
    response = input("❓ 是否执行实际清理操作? [y/N]: ").strip().lower()
    
    if response in ['y', 'yes']:
        cleaner.safe_cleanup(dry_run=False)
        
        # 4. 验证结果
        print("\n" + "=" * 50)
        if cleaner.validate_cleanup():
            print("🎉 配置清理成功完成!")
        else:
            print("⚠️ 配置清理完成，但验证发现问题，请检查配置")
    else:
        print("⚠️ 清理操作已取消")

if __name__ == "__main__":
    main()
