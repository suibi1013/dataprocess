#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系统备份还原功能
"""

import os
import zipfile
import json
from repository.system_repository import SystemRepository


def test_backup_database():
    """
    测试数据库备份功能
    """
    print("=== 测试数据库备份功能 ===")
    
    try:
        # 创建系统仓储实例
        system_repo = SystemRepository()
        
        # 执行备份
        result = system_repo.backup_database()
        
        if result["success"]:
            print(f"✅ 备份成功，备份文件路径: {result['data']['backup_path']}")
            print(f"✅ 备份文件名: {result['data']['backup_filename']}")
            print(f"✅ 备份时间: {result['data']['backup_time']}")
            print(f"✅ 备份表数量: {result['data']['tables_count']}")
            print(f"✅ 排除的表: {result['data']['excluded_tables']}")
            
            # 检查备份文件是否存在
            if os.path.exists(result['data']['backup_path']):
                print("✅ 备份文件存在")
                
                # 检查备份文件格式
                if zipfile.is_zipfile(result['data']['backup_path']):
                    print("✅ 备份文件为zip格式")
                    
                    # 检查zip文件内容
                    with zipfile.ZipFile(result['data']['backup_path'], 'r') as zipf:
                        files = zipf.namelist()
                        print(f"✅ zip文件内容: {files}")
                        
                        # 检查是否包含backup_info.json
                        if 'backup_info.json' in files:
                            print("✅ 包含备份信息文件backup_info.json")
                            
                            # 读取备份信息
                            with zipf.open('backup_info.json') as f:
                                backup_info = json.load(f)
                                print(f"✅ 备份信息: {json.dumps(backup_info, ensure_ascii=False, indent=2)}")
                        
                        # 检查是否包含排除的表
                        excluded_tables = ['instruction_categories.json', 'instruction_items.json', 'instruction_parameters.json']
                        for excluded_table in excluded_tables:
                            if excluded_table not in files:
                                print(f"✅ 成功排除了表: {excluded_table.replace('.json', '')}")
                            else:
                                print(f"❌ 未排除表: {excluded_table.replace('.json', '')}")
                                
                        # 检查是否包含其他表的JSON文件
                        has_other_tables = any(file.endswith('.json') and file != 'backup_info.json' for file in files)
                        if has_other_tables:
                            print("✅ 包含其他表的JSON文件")
                        else:
                            print("❌ 不包含其他表的JSON文件")
                else:
                    print("❌ 备份文件不是zip格式")
            else:
                print("❌ 备份文件不存在")
        else:
            print(f"❌ 备份失败: {result['message']}")
            
        return result
    except Exception as e:
        print(f"❌ 测试备份功能时发生错误: {str(e)}")
        return {
            "success": False,
            "message": f"测试备份功能时发生错误: {str(e)}"
        }


if __name__ == "__main__":
    test_backup_database()
