#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统仓储层
负责数据库备份还原等系统级数据访问操作
"""

import os
import sqlite3
import zipfile
import io
import json
from datetime import datetime
from typing import List, Dict, Any

from config import config


class SystemRepository:
    """系统仓储类"""
    
    def __init__(self):
        """初始化系统仓储"""
        # 获取当前文件所在目录作为基础目录
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # 向上两层目录（repository目录的上两层）
        self.base_dir = os.path.dirname(os.path.dirname(self.base_dir))
        
        # 排除备份的数据表
        self.excluded_tables = {
            'instruction_categories',
            'instruction_items',
            'instruction_parameters'
        }
    
    def get_db_path(self) -> str:
        """
        获取数据库文件路径
        
        Returns:
            str: 数据库文件路径
        """
        return config.DB_PATH
    
    def get_backup_dir(self) -> str:
        """
        获取备份目录路径
        
        Returns:
            str: 备份目录路径
        """
        backup_dir = os.path.join(self.base_dir, "backups")
        # 确保备份目录存在
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    def get_temp_dir(self) -> str:
        """
        获取临时目录路径
        
        Returns:
            str: 临时目录路径
        """
        temp_dir = os.path.join(self.base_dir, "temp")
        # 确保临时目录存在
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    def _get_all_tables(self) -> List[str]:
        """
        获取所有表名，排除指定表
        
        Returns:
            List[str]: 表名列表
        """
        conn = sqlite3.connect(self.get_db_path())
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        conn.close()
        
        # 排除指定表
        return [table for table in tables if table not in self.excluded_tables]
    
    def _get_table_data(self, table_name: str) -> Dict[str, Any]:
        """
        获取指定表的数据
        
        Args:
            table_name: 表名
            
        Returns:
            Dict[str, Any]: 表数据，包含表名、字段和数据
        """
        conn = sqlite3.connect(self.get_db_path())
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 获取表数据
        cursor.execute(f"SELECT * FROM {table_name};")
        data = cursor.fetchall()
        
        conn.close()
        
        # 转换为字典列表
        data_dict = [dict(zip(columns, row)) for row in data]
        
        return {
            'table_name': table_name,
            'columns': columns,
            'data': data_dict
        }
    
    def backup_database(self) -> dict:
        """
        备份数据库，格式为JSON文件的zip压缩格式，排除指定表
        
        Returns:
            dict: 备份结果，包含备份文件路径和信息
        """
        try:
            # 检查数据库文件是否存在
            if not os.path.exists(self.get_db_path()):
                return {
                    "success": False,
                    "message": "数据库文件不存在"
                }
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"db_backup_{timestamp}.zip"
            backup_path = os.path.join(self.get_backup_dir(), backup_filename)
            
            # 创建内存中的zip文件
            memory_zip = io.BytesIO()
            with zipfile.ZipFile(memory_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                # 获取所有需要备份的表
                tables = self._get_all_tables()
                
                # 备份每个表的数据
                for table_name in tables:
                    # 获取表数据
                    table_data = self._get_table_data(table_name)
                    
                    # 转换为JSON格式
                    table_json = json.dumps(table_data, ensure_ascii=False, indent=2)
                    
                    # 写入zip文件
                    zipf.writestr(f"{table_name}.json", table_json)
                
                # 添加备份信息
                backup_info = {
                    "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "database_path": self.get_db_path(),
                    "backup_version": "v1.0",
                    "tables_count": len(tables),
                    "tables": tables,
                    "excluded_tables": list(self.excluded_tables)
                }
                
                backup_info_json = json.dumps(backup_info, ensure_ascii=False, indent=2)
                zipf.writestr("backup_info.json", backup_info_json)
            
            # 将内存中的zip文件保存到磁盘
            memory_zip.seek(0)
            with open(backup_path, "wb") as f:
                f.write(memory_zip.read())
            
            return {
                "success": True,
                "message": "数据库备份成功",
                "data": {
                    "backup_path": backup_path,
                    "backup_filename": backup_filename,
                    "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "tables_count": len(tables),
                    "excluded_tables": list(self.excluded_tables)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"数据库备份失败: {str(e)}"
            }
    
    def restore_database(self, backup_file_path: str) -> dict:
        """
        从JSON文件的zip压缩包中还原数据库
        
        Args:
            backup_file_path: 备份文件路径
            
        Returns:
            dict: 还原结果
        """
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_file_path):
                return {
                    "success": False,
                    "message": "备份文件不存在"
                }
            
            # 验证备份文件格式
            if not zipfile.is_zipfile(backup_file_path):
                return {
                    "success": False,
                    "message": "无效的备份文件格式，必须是zip文件"
                }
            
            conn = sqlite3.connect(self.get_db_path())
            cursor = conn.cursor()
            
            # 关闭外键约束
            cursor.execute("PRAGMA foreign_keys = OFF;")
            
            try:
                # 读取备份文件
                with zipfile.ZipFile(backup_file_path, "r") as zipf:
                    # 获取所有JSON文件
                    json_files = [file for file in zipf.namelist() if file.endswith(".json") and file != "backup_info.json"]
                    
                    # 还原每个表的数据
                    for json_file in json_files:
                        # 读取JSON数据
                        with zipf.open(json_file) as f:
                            table_data = json.loads(f.read().decode('utf-8'))
                        
                        table_name = table_data['table_name']
                        columns = table_data['columns']
                        data = table_data['data']
                        
                        # 清空表数据
                        cursor.execute(f"DELETE FROM {table_name};")
                        
                        # 插入数据
                        if data:
                            # 构建插入语句
                            placeholders = ", ".join(["?"] * len(columns))
                            column_names = ", ".join(columns)
                            insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders});"
                            
                            # 批量插入数据
                            rows = [[row[col] for col in columns] for row in data]
                            cursor.executemany(insert_sql, rows)
                    
                # 提交事务
                conn.commit()
                
                return {
                    "success": True,
                    "message": "数据库还原成功"
                }
            except Exception as e:
                # 回滚事务
                conn.rollback()
                raise e
            finally:
                # 重新开启外键约束
                cursor.execute("PRAGMA foreign_keys = ON;")
                conn.close()
        except Exception as e:
            return {
                "success": False,
                "message": f"数据库还原失败: {str(e)}"
            }
    
    def get_backup_list(self) -> dict:
        """
        获取备份文件列表
        
        Returns:
            dict: 备份文件列表
        """
        try:
            backup_dir = self.get_backup_dir()
            if not os.path.exists(backup_dir):
                return {
                    "success": True,
                    "message": "备份目录不存在，无备份文件",
                    "data": []
                }
            
            # 获取备份文件列表
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith(".zip"):
                    file_path = os.path.join(backup_dir, filename)
                    file_stat = os.stat(file_path)
                    backup_files.append({
                        "filename": filename,
                        "file_path": file_path,
                        "size": file_stat.st_size,
                        "create_time": datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "modify_time": datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # 按创建时间降序排序
            backup_files.sort(key=lambda x: x["create_time"], reverse=True)
            
            return {
                "success": True,
                "message": "获取备份列表成功",
                "data": backup_files
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取备份列表失败: {str(e)}"
            }
    
    def delete_backup(self, backup_filename: str) -> dict:
        """
        删除备份文件
        
        Args:
            backup_filename: 备份文件名
            
        Returns:
            dict: 删除结果
        """
        try:
            backup_dir = self.get_backup_dir()
            backup_path = os.path.join(backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return {
                    "success": False,
                    "message": "备份文件不存在"
                }
            
            os.remove(backup_path)
            
            return {
                "success": True,
                "message": "备份文件删除成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"删除备份文件失败: {str(e)}"
            }
    
    def save_temp_file(self, file_content: bytes, filename: str) -> str:
        """
        保存临时文件
        
        Args:
            file_content: 文件内容
            filename: 文件名
            
        Returns:
            str: 临时文件路径
        """
        temp_dir = self.get_temp_dir()
        temp_file_path = os.path.join(temp_dir, filename)
        
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        return temp_file_path
    
    def delete_temp_file(self, temp_file_path: str) -> None:
        """
        删除临时文件
        
        Args:
            temp_file_path: 临时文件路径
        """
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
