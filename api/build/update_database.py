#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库更新脚本
用于在应用迭代安装时更新数据库中的表数据
特别是：instruction_categories、instruction_items、instruction_parameters三个表
"""

import sqlite3
import os
import datetime
import json


def get_db_connection(db_path=None):
    """
    获取数据库连接
    """
    if db_path is None:
        # 尝试不同位置的数据库文件
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'database.db'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db'),
            os.path.join(os.path.dirname(__file__), '..', 'database.db'),
            os.path.join(os.path.dirname(__file__), 'resources', 'backend', 'database.db')
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
def get_data_from_backup_file():
    """
    从备份文件获取数据
    """
    # 备份文件路径
    backup_file = os.path.join(os.path.dirname(__file__), 'instruction_data_backup.json')
    
    if not os.path.exists(backup_file):
        print(f"备份文件不存在: {backup_file}")
        return [], [], []
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # 提取数据
        categories_data = backup_data.get('data', {}).get('instruction_categories', [])
        items_data = backup_data.get('data', {}).get('instruction_items', [])
        parameters_data = backup_data.get('data', {}).get('instruction_parameters', [])
        
        # 转换为元组格式
        categories = []
        for cat in categories_data:
            categories.append((
                cat.get('id'),
                cat.get('name'),
                cat.get('description'),
                cat.get('sort_order', 1),
                cat.get('is_active', 1),
                cat.get('created_at'),
                cat.get('updated_at')
            ))
        
        items = []
        for item in items_data:
            items.append((
                item.get('id'),
                item.get('category_id'),
                item.get('name'),
                item.get('icon'),
                item.get('description'),
                item.get('python_script'),
                item.get('sort_order', 1),
                item.get('is_active', 1),
                item.get('created_at'),
                item.get('updated_at')
            ))
        
        parameters = []
        for param in parameters_data:
            parameters.append((
                param.get('id'),
                param.get('instruction_id'),
                param.get('name'),
                param.get('label'),
                param.get('description'),
                param.get('display_type', 'string'),
                param.get('value_type', 'string'),
                param.get('required', 0),
                param.get('default_value'),
                param.get('direction', 0),
                param.get('api_url'),
                param.get('event_script')
            ))
        
        print(f"从备份文件获取数据成功")
        print(f"数据统计: categories={len(categories)}, items={len(items)}, parameters={len(parameters)}")
        return categories, items, parameters
    except Exception as e:
        print(f"从备份文件获取数据失败: {e}")
        return [], [], []

def update_instruction_categories(conn, categories):
    """
    更新instruction_categories表
    """
    try:
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instruction_categories'")
        if not cursor.fetchone():
            # 创建表
            cursor.execute('''
                CREATE TABLE instruction_categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    sort_order INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("创建表 instruction_categories 成功")
        
        # 插入或更新数据
        for category_id, name, description, sort_order, is_active, created_at, updated_at in categories:
            # 检查是否存在
            cursor.execute("SELECT id FROM instruction_categories WHERE id = ?", (category_id,))
            if cursor.fetchone():
                # 更新
                cursor.execute('''
                    UPDATE instruction_categories 
                    SET name = ?, description = ?, sort_order = ?, is_active = ? 
                    WHERE id = ?
                ''', (name, description, sort_order, is_active, category_id))
            else:
                # 插入
                cursor.execute('''
                    INSERT INTO instruction_categories (id, name, description, sort_order, is_active, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (category_id, name, description, sort_order, is_active, created_at, updated_at))
        
        conn.commit()
        print("更新表 instruction_categories 成功")
        return True
    except Exception as e:
        print(f"更新表 instruction_categories 失败: {e}")
        conn.rollback()
        return False

def update_instruction_items(conn, items):
    """
    更新instruction_items表
    """
    try:
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instruction_items'")
        if not cursor.fetchone():
            # 创建表
            cursor.execute('''
                CREATE TABLE instruction_items (
                    id TEXT PRIMARY KEY,
                    category_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    icon TEXT,
                    description TEXT,
                    python_script TEXT,
                    sort_order INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES instruction_categories(id) ON DELETE CASCADE
                )
            ''')
            print("创建表 instruction_items 成功")
        
        # 插入或更新数据
        for item_id, category_id, name, icon, description, python_script, sort_order, is_active, created_at, updated_at in items:
            # 检查是否存在
            cursor.execute("SELECT id FROM instruction_items WHERE id = ?", (item_id,))
            if cursor.fetchone():
                # 更新
                cursor.execute('''
                    UPDATE instruction_items 
                    SET category_id = ?, name = ?, icon = ?, description = ?, python_script = ?, 
                        sort_order = ?, is_active = ? 
                    WHERE id = ?
                ''', (category_id, name, icon, description, python_script, sort_order, is_active, item_id))
            else:
                # 插入
                cursor.execute('''
                    INSERT INTO instruction_items (id, category_id, name, icon, description, python_script, sort_order, is_active, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item_id, category_id, name, icon, description, python_script, sort_order, is_active, created_at, updated_at))
        
        conn.commit()
        print("更新表 instruction_items 成功")
        return True
    except Exception as e:
        print(f"更新表 instruction_items 失败: {e}")
        conn.rollback()
        return False

def update_instruction_parameters(conn, parameters):
    """
    更新instruction_parameters表
    """
    try:
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instruction_parameters'")
        if not cursor.fetchone():
            # 创建表
            cursor.execute('''
                CREATE TABLE instruction_parameters (
                    id TEXT PRIMARY KEY,
                    instruction_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    label TEXT NOT NULL,
                    description TEXT,
                    display_type TEXT DEFAULT 'string',
                    value_type TEXT DEFAULT 'string',
                    required INTEGER DEFAULT 0,
                    default_value TEXT,
                    direction INTEGER DEFAULT 0,
                    api_url TEXT,
                    event_script TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (instruction_id) REFERENCES instruction_items(id) ON DELETE CASCADE
                )
            ''')
            print("创建表 instruction_parameters 成功")
        
        # 插入或更新数据
        for param_id, instruction_id, name, label, description, display_type, value_type, required, default_value, direction, api_url, event_script in parameters:
            # 检查是否存在
            cursor.execute("SELECT id FROM instruction_parameters WHERE id = ?", (param_id,))
            if cursor.fetchone():
                # 更新
                cursor.execute('''
                    UPDATE instruction_parameters 
                    SET instruction_id = ?, name = ?, label = ?, description = ?, display_type = ?, 
                        value_type = ?, required = ?, default_value = ?, direction = ?, 
                        api_url = ?, event_script = ? 
                    WHERE id = ?
                ''', (instruction_id, name, label, description, display_type, value_type, required, default_value, direction, api_url, event_script, param_id))
            else:
                # 插入
                cursor.execute('''
                    INSERT INTO instruction_parameters (id, instruction_id, name, label, description, display_type, value_type, required, default_value, direction, api_url, event_script) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (param_id, instruction_id, name, label, description, display_type, value_type, required, default_value, direction, api_url, event_script))
        
        conn.commit()
        print("更新表 instruction_parameters 成功")
        return True
    except Exception as e:
        print(f"更新表 instruction_parameters 失败: {e}")
        conn.rollback()
        return False

def update_business_tables(conn):
    """
    更新业务表数据和结构
    """
    try:    
        # cursor = conn.cursor()# 检查表是否存在
        # cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instruction_parameters'")
        # SQLite 不支持直接删除列或修改列类型，因此需要通过 “新建表 + 迁移数据” 的方式实现完整结构变更
        # if not cursor.fetchone():
            # === 步骤 1：重命名旧表 ===
            # cursor.execute("ALTER TABLE tableName RENAME TO tableName_old;")
        # === 步骤 2：创建新表（带新结构）===
        # cursor.execute("""
        # CREATE TABLE tableName (
        #     id INTEGER PRIMARY KEY,
        #     name TEXT NOT NULL,
        #     status TEXT DEFAULT 'active',
        #     created_at TEXT
        # );
        # """)
        # === 步骤 3：迁移旧数据（按字段映射）===
        # cursor.execute("""
        # INSERT INTO tableName (id, name)
        # SELECT id, name FROM tableName_old;
        # """)
        # === 步骤 4：更新字段值===
        # 更新单个值
        # cursor.execute("UPDATE tableName SET value = ? WHERE id = ?",(new_value, "id"))
        # 更新多个值
        # updates = [("active", 1), ("inactive", 2)]
        # cursor.execute("UPDATE tableName SET value = ? WHERE id = ?",updates)
        # if not cursor.fetchone():
            # === 步骤 4：删除旧表 ===
            # cursor.execute("DROP TABLE tableName_old;")
        # conn.commit()
        return True
    
    except Exception as e:
        # print(f"更新表 instruction_parameters 失败: {e}")
        # conn.rollback()
        return False
    pass
def main():
    """
    主函数
    """
    print("开始更新数据库...")
    
    # 获取数据库连接
    conn = get_db_connection()
    if not conn:
        print("无法连接数据库，更新失败")
        return
    
    try:
        # 更新业务表结构
        update_business_tables(conn)
        # 从备份文件获取数据
        categories, items, parameters = get_data_from_backup_file()
        
        # 更新表数据
        update_instruction_categories(conn, categories)
        update_instruction_items(conn, items)
        update_instruction_parameters(conn, parameters)
        
        print("数据库更新完成！")
    except Exception as e:
        print(f"更新过程中发生错误: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()