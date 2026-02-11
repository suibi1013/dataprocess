#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令数据备份脚本
用于在打包准备阶段备份instruction_categories、instruction_items、instruction_parameters三个表的数据
"""

import sqlite3
import os
import json
import datetime

def get_db_connection(db_path=None):
    """
    获取数据库连接
    """
    if db_path is None:
        # 尝试不同位置的数据库文件
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'database.db'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db'),
            os.path.join(os.path.dirname(__file__), 'database.db')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if db_path is None:
            print("数据库文件不存在")
            return None
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return None

def backup_instruction_data():
    """
    备份指令相关表数据
    """
    # 获取数据库连接
    conn = get_db_connection()
    if not conn:
        print("无法连接数据库，备份失败")
        return False
    
    try:
        cursor = conn.cursor()
        
        # 备份instruction_categories表
        cursor.execute("SELECT id, name, description, sort_order, is_active, created_at, updated_at FROM instruction_categories")
        categories = [dict(row) for row in cursor.fetchall()]
        
        # 备份instruction_items表
        cursor.execute("SELECT id, category_id, name, icon, description, python_script, sort_order, is_active, created_at, updated_at FROM instruction_items")
        items = [dict(row) for row in cursor.fetchall()]
        
        # 备份instruction_parameters表
        cursor.execute("SELECT id, instruction_id, name, label, description, display_type, value_type, required, default_value, direction, api_url, event_script FROM instruction_parameters")
        parameters = [dict(row) for row in cursor.fetchall()]
        
        # 准备备份数据
        backup_data = {
            "version": "1.0",
            "backup_time": datetime.datetime.now().isoformat(),
            "data": {
                "instruction_categories": categories,
                "instruction_items": items,
                "instruction_parameters": parameters
            }
        }
        
        # 保存备份数据到文件
        backup_file = os.path.join(os.path.dirname(__file__), 'instruction_data_backup.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"指令数据备份成功，保存到: {backup_file}")
        print(f"备份统计: categories={len(categories)}, items={len(items)}, parameters={len(parameters)}")
        
        return True
    except Exception as e:
        print(f"备份指令数据失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """
    主函数
    """
    print("开始备份指令数据...")
    success = backup_instruction_data()
    if success:
        print("指令数据备份完成！")
    else:
        print("指令数据备份失败！")


if __name__ == "__main__":
    main()
