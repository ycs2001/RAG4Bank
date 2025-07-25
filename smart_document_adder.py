#!/usr/bin/env python3
"""
智能文档添加工具
自动生成集合配置、更新映射规则并处理文档
"""

import os
import sys
import yaml
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartDocumentAdder:
    """智能文档添加器"""
    
    def __init__(self):
        self.config_file = "config/unified_config.yaml"
        self.mapping_file = "collection_database_builder.py"
        
    def generate_collection_config(self, doc_name: str) -> Dict:
        """根据文档名称自动生成集合配置"""
        
        # 清理文档名称
        clean_name = doc_name.replace('.xlsx', '').replace('.docx', '').replace('.pdf', '')
        
        # 生成集合ID（转换为英文标识符）
        collection_id = self._generate_collection_id(clean_name)
        
        # 生成关键词
        keywords = self._generate_keywords(clean_name)
        
        # 生成描述和类型
        description, doc_type = self._generate_description_and_type(clean_name)
        
        # 确定优先级
        priority = self._determine_priority(clean_name)
        
        # 生成版本信息
        version, version_display = self._extract_version_info(clean_name)
        
        return {
            'name': clean_name,
            'collection_id': collection_id,
            'keywords': keywords,
            'priority': priority,
            'description': description,
            'version': version,
            'version_display': version_display,
            'type': doc_type
        }
    
    def _generate_collection_id(self, name: str) -> str:
        """生成集合ID"""
        # 映射规则
        mappings = {
            '监管口径答疑': 'regulatory_qa_guidance',
            '监管答疑': 'regulatory_qa_guidance',
            '口径答疑': 'regulatory_qa_guidance',
            '监管参考': 'regulatory_reference',
            '白皮书': 'regulatory_reference',
            '参考资料': 'regulatory_reference',
            '银行产品管理': 'bank_product_management',
            '产品管理办法': 'bank_product_management',
            '结构性存款': 'bank_product_management',
            '1104': 'report_1104',
            'EAST': 'east_data',
            '一表通': 'ybt_data',
            '人民银行': 'pboc_statistics',
            '金融统计': 'pboc_statistics',
            '央行': 'pboc_statistics'
        }
        
        name_lower = name.lower()
        
        # 检查映射规则
        for key, value in mappings.items():
            if key in name:
                # 处理版本信息
                if '2024' in name:
                    return f"{value}_2024" if 'report' in value else value
                elif '2022' in name:
                    return f"{value}_2022" if 'report' in value else value
                elif 'v1.0' in name or 'v2.0' in name:
                    return value
                else:
                    return value
        
        # 默认生成规则
        # 移除特殊字符，转换为英文标识符
        clean_id = re.sub(r'[^\w\u4e00-\u9fff]', '_', name)
        clean_id = re.sub(r'_+', '_', clean_id).strip('_')
        
        # 简化中文转英文
        chinese_to_english = {
            '监管': 'regulatory',
            '口径': 'guidance',
            '答疑': 'qa',
            '文档': 'document',
            '参考': 'reference',
            '资料': 'material',
            '银行': 'bank',
            '产品': 'product',
            '管理': 'management',
            '办法': 'regulation',
            '报表': 'report',
            '数据': 'data',
            '结构': 'structure',
            '元数据': 'metadata',
            '映射': 'mapping',
            '统计': 'statistics',
            '制度': 'system',
            '汇编': 'compilation'
        }
        
        for cn, en in chinese_to_english.items():
            clean_id = clean_id.replace(cn, en)
        
        return clean_id.lower()
    
    def _generate_keywords(self, name: str) -> List[str]:
        """生成关键词"""
        keywords = []
        
        # 基础关键词提取
        if '监管' in name:
            keywords.extend(['监管', '监管要求', '合规'])
        if '口径' in name:
            keywords.extend(['口径', '填报口径', '统计口径'])
        if '答疑' in name:
            keywords.extend(['答疑', '问答', '解释'])
        if '1104' in name:
            keywords.extend(['1104', '银行业监管统计', '报表制度'])
        if 'EAST' in name:
            keywords.extend(['EAST', '监管数据', '报送系统'])
        if '一表通' in name:
            keywords.extend(['一表通', '产品报送', '产品制度'])
        if '人民银行' in name:
            keywords.extend(['人民银行', '央行', '金融统计'])
        if '银行产品' in name:
            keywords.extend(['银行产品', '产品管理', '风险管理'])
        if '白皮书' in name:
            keywords.extend(['白皮书', '政策解读', '行业指导'])
        
        # 版本关键词
        if '2024' in name:
            keywords.append('2024')
        if '2022' in name:
            keywords.append('2022')
        if 'v1.0' in name:
            keywords.append('v1.0')
        
        # 去重并返回
        return list(set(keywords))
    
    def _generate_description_and_type(self, name: str) -> Tuple[str, str]:
        """生成描述和类型"""
        if '监管口径答疑' in name:
            return "监管口径答疑和填报指导文档", "答疑指导"
        elif '1104' in name:
            return f"银行业监管统计报表制度文档", "监管报表"
        elif 'EAST' in name:
            return "EAST监管数据报送相关文档", "数据报送"
        elif '一表通' in name:
            return "一表通产品报送相关文档", "产品报送"
        elif '人民银行' in name:
            return "人民银行金融统计制度相关文档", "统计制度"
        elif '银行产品' in name:
            return "银行产品管理制度相关文档", "产品管理"
        elif '白皮书' in name:
            return "监管政策参考资料和白皮书", "参考资料"
        else:
            return f"{name}相关文档", "其他文档"
    
    def _determine_priority(self, name: str) -> int:
        """确定优先级"""
        if any(x in name for x in ['1104', 'EAST', '人民银行']):
            return 1  # 高优先级
        elif any(x in name for x in ['监管口径', '答疑', '银行产品']):
            return 1  # 高优先级
        else:
            return 2  # 中优先级
    
    def _extract_version_info(self, name: str) -> Tuple[str, str]:
        """提取版本信息"""
        if '2024' in name:
            return "2024版", "[2024版]"
        elif '2022' in name:
            return "2022版", "[2022版]"
        elif 'v1.0' in name:
            return "v1.0", "[v1.0]"
        elif 'v2.0' in name:
            return "v2.0", "[v2.0]"
        else:
            return "现行版", "[现行版]"
    
    def update_config_file(self, new_collection: Dict) -> bool:
        """更新配置文件"""
        try:
            # 读取现有配置
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查是否已存在
            existing_collections = config.get('embedding', {}).get('collections', [])
            for collection in existing_collections:
                if collection.get('collection_id') == new_collection['collection_id']:
                    logger.info(f"集合 {new_collection['collection_id']} 已存在，跳过添加")
                    return True
            
            # 添加新集合
            existing_collections.append(new_collection)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"✅ 已添加集合配置: {new_collection['name']} (ID: {new_collection['collection_id']})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新配置文件失败: {e}")
            return False
    
    def update_mapping_file(self, doc_name: str, collection_id: str) -> bool:
        """更新映射文件"""
        try:
            # 读取映射文件
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已存在映射
            if f"'{doc_name}'" in content:
                logger.info(f"文档映射 {doc_name} 已存在，跳过添加")
                return True
            
            # 找到映射字典的结束位置
            pattern = r"(self\.doc_to_collection_mapping = \{[^}]+)(\s*\})"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                # 添加新映射
                new_mapping = f",\n            '{doc_name}': '{collection_id}'"
                new_content = content.replace(
                    match.group(0),
                    match.group(1) + new_mapping + match.group(2)
                )
                
                # 保存文件
                with open(self.mapping_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"✅ 已添加文档映射: {doc_name} → {collection_id}")
                return True
            else:
                logger.error("❌ 未找到映射字典位置")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新映射文件失败: {e}")
            return False
    
    def process_document(self, file_path: str) -> bool:
        """处理文档"""
        try:
            # 提取文档名称
            doc_name = Path(file_path).stem
            
            logger.info(f"🚀 开始智能处理文档: {doc_name}")
            
            # 1. 生成集合配置
            collection_config = self.generate_collection_config(doc_name)
            logger.info(f"📋 生成集合配置: {collection_config['name']} (ID: {collection_config['collection_id']})")
            
            # 2. 更新配置文件
            if not self.update_config_file(collection_config):
                return False
            
            # 3. 更新映射文件
            if not self.update_mapping_file(doc_name, collection_config['collection_id']):
                return False
            
            # 4. 处理文档
            cmd = [
                "./categoryrag", "add", file_path,
                "--collection", collection_config['name'],
                "--keywords", ",".join(collection_config['keywords'])
            ]
            
            logger.info(f"📄 执行文档处理: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ 文档处理成功: {doc_name}")
                return True
            else:
                logger.error(f"❌ 文档处理失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 处理文档失败: {e}")
            return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python smart_document_adder.py <文档路径>")
        print("示例: python smart_document_adder.py data/KnowledgeBase/新文档.xlsx")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    
    adder = SmartDocumentAdder()
    
    print("🎯 CategoryRAG智能文档添加工具")
    print("=" * 50)
    
    if adder.process_document(file_path):
        print("\n🎉 文档添加完成！")
        print("💡 配置文件和映射规则已自动更新")
        print("🔄 建议运行数据库重建以应用更改:")
        print("   python3 collection_database_builder.py")
    else:
        print("\n❌ 文档添加失败，请检查日志")
        sys.exit(1)

if __name__ == "__main__":
    main()
