#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模板页面配置仓储类
实现数据模板页面配置的增删改查功能
"""

import json
from typing import List, Optional
from repository.base_repository import BaseRepository, SQLiteConnectionPool
from entity.template_slide import TemplateSlide


class TemplateSlideRepository(BaseRepository[TemplateSlide]):
    """数据模板页面配置仓储类"""
    
    TABLE_NAME = "template_slides"
    
    def __init__(self, db_pool: SQLiteConnectionPool):
        """初始化数据模板页面配置仓储类
        
        Args:
            db_pool: SQLite连接池实例
        """
        super().__init__(db_pool)
        # 初始化表结构
        self._init_table()
    
    def _init_table(self):
        """初始化数据模板页面配置表结构"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            slide_index INTEGER NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            background TEXT NOT NULL,
            elements TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (template_id) REFERENCES template_infos(id) ON DELETE CASCADE
        )
        """
        self.execute_non_query(create_table_sql)
    
    def add(self, template_slide: TemplateSlide) -> bool:
        """添加数据模板页面配置
        
        Args:
            template_slide: 数据模板页面配置实体
            
        Returns:
            bool: 添加是否成功
        """
        # 将elements转换为JSON字符串
        elements_json = json.dumps(template_slide.elements)
        
        data = {
            "id": template_slide.id,
            "template_id": template_slide.template_id,
            "slide_index": template_slide.slide_index,
            "width": template_slide.width,
            "height": template_slide.height,
            "background": template_slide.background,
            "elements": elements_json,
            "created_at": template_slide.created_at,
            "updated_at": template_slide.updated_at
        }
        return self.insert(self.TABLE_NAME, data)
    
    def update(self, template_slide: TemplateSlide) -> bool:
        """更新数据模板页面配置
        
        Args:
            template_slide: 数据模板页面配置实体
            
        Returns:
            bool: 更新是否成功
        """
        # 将elements转换为JSON字符串
        elements_json = json.dumps(template_slide.elements)
        
        data = {
            "template_id": template_slide.template_id,
            "slide_index": template_slide.slide_index,
            "width": template_slide.width,
            "height": template_slide.height,
            "background": template_slide.background,
            "elements": elements_json,
            "updated_at": template_slide.updated_at
        }
        return super().update(self.TABLE_NAME, data, "id = ?", (template_slide.id,))
    
    def delete(self, id: str) -> bool:
        """删除数据模板页面配置
        
        Args:
            id: 数据模板页面配置ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "id = ?", (id,))
    
    def delete_by_template_id(self, template_id: str) -> bool:
        """根据模板ID删除所有数据模板页面配置
        
        Args:
            template_id: 模板ID
            
        Returns:
            bool: 删除是否成功
        """
        return super().delete(self.TABLE_NAME, "template_id = ?", (template_id,))
    
    def find_by_id(self, id: str) -> Optional[TemplateSlide]:
        """根据ID查找数据模板页面配置
        
        Args:
            id: 数据模板页面配置ID
            
        Returns:
            Optional[TemplateSlide]: 数据模板页面配置实体，如果不存在则返回None
        """
        result = super().find_by_id(self.TABLE_NAME, id)
        if result:
            return self._convert_result_to_slide(result)
        return None
    
    def find_by_template_id(self, template_id: str) -> List[TemplateSlide]:
        """根据模板ID查找所有数据模板页面配置
        
        Args:
            template_id: 模板ID
            
        Returns:
            List[TemplateSlide]: 数据模板页面配置列表
        """
        results = super().find_all(self.TABLE_NAME, "template_id = ?", (template_id,))
        return [self._convert_result_to_slide(result) for result in results]
    
    def find_by_template_id_and_index(self, template_id: str, slide_index: int) -> Optional[TemplateSlide]:
        """根据模板ID和幻灯片索引查找数据模板页面配置
        
        Args:
            template_id: 模板ID
            slide_index: 幻灯片索引
            
        Returns:
            Optional[TemplateSlide]: 数据模板页面配置实体，如果不存在则返回None
        """
        results = super().find_all(
            self.TABLE_NAME, 
            "template_id = ? AND slide_index = ?", 
            (template_id, slide_index)
        )
        if results:
            return self._convert_result_to_slide(results[0])
        return None
    
    def find_all(self) -> List[TemplateSlide]:
        """查找所有数据模板页面配置
        
        Returns:
            List[TemplateSlide]: 数据模板页面配置列表
        """
        results = super().find_all(self.TABLE_NAME)
        return [self._convert_result_to_slide(result) for result in results]
    
    def _convert_result_to_slide(self, result: dict) -> TemplateSlide:
        """将查询结果转换为数据模板页面配置实体
        
        Args:
            result: 查询结果
            
        Returns:
            TemplateSlide: 数据模板页面配置实体
        """
        # 解析elements JSON字符串
        if result["elements"]:
            result["elements"] = json.loads(result["elements"])
        
        return self.dict_to_model(result, TemplateSlide)
