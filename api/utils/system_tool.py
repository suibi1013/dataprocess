#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统工具类
包含授权码生成和验证的核心逻辑
"""

import base64
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class SystemTool:
    """系统工具类"""
    
    # 加密密钥，实际应用中应该从配置文件读取
    ENCRYPT_KEY = "dataprocess_license_key_2026"
    
    @staticmethod
    def _encrypt(data: str) -> str:
        """
        简单加密方法
        
        Args:
            data: 要加密的数据
            
        Returns:
            str: 加密后的数据
        """
        # 结合密钥进行哈希
        combined = data + SystemTool.ENCRYPT_KEY
        print("哈希："+combined)
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        hash_str = hash_obj.hexdigest()     
        
        # 将原始数据和哈希值组合后进行base64编码
        combined_data = f"{data}:{hash_str}"
        print("加密："+combined_data)
        encoded = base64.b64encode(combined_data.encode('utf-8'))
        return encoded.decode('utf-8')
    
    @staticmethod
    def _decrypt(encrypted_data: str) -> Optional[str]:
        """
        简单解密方法
        
        Args:
            encrypted_data: 加密的数据
            
        Returns:
            Optional[str]: 解密后的数据，如果解密失败返回None
        """
        try:
            # 解码base64
            decoded = base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
            
            # 分离原始数据和哈希值
            data, hash_str = decoded.split(':', 1)
            
            # 验证哈希值
            combined = data + SystemTool.ENCRYPT_KEY
            print("哈希："+combined)
            expected_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
            print("解密："+f"{data}:{expected_hash}")
            if hash_str == expected_hash:
                return data
            else:
                return None
        except Exception:
            return None
    
    @staticmethod
    def generate_license_key(expire_date: str) -> str:
        """
        生成授权码
        
        Args:
            expire_date: 截至日期，格式为YYYY-MM-DD
            
        Returns:
            str: 生成的授权码
        """        
        # 加密数据
        encrypted_data = SystemTool._encrypt(expire_date)
        
        # 格式化授权码，每8位加一个连字符
        formatted_key = '-'.join([encrypted_data[i:i+8] for i in range(0, len(encrypted_data), 8)])
        
        return formatted_key
    
    @staticmethod
    def validate_license_key(license_key: str) -> Dict[str, Any]:
        """
        验证授权码
        
        Args:
            license_key: 授权码
            
        Returns:
            Dict[str, Any]: 验证结果，包含success、message和data字段
        """
        try:
            # 移除连字符
            encrypted_data = license_key.replace('-', '')
            
            # 解密数据
            expire_date_str = SystemTool._decrypt(encrypted_data)
            
            if not expire_date_str:
                return {
                    "success": False,
                    "message": "授权码格式错误",
                    "data": None
                }            
            
            # 验证截至日期
            expire_date = datetime.strptime(expire_date_str, "%Y-%m-%d")
            current_date = datetime.now()
            
            if current_date > expire_date:
                return {
                    "success": False,
                    "message": "授权码已过期",
                    "data": {
                        "expire_date": expire_date_str
                    }
                }
            
            # 授权码有效
            return {
                "success": True,
                "message": "授权码验证成功",
                "data": {
                    "expire_date": expire_date_str,
                    "days_remaining": (expire_date - current_date).days
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"验证授权码失败: {str(e)}",
                "data": None
            }
    
    @staticmethod
    def generate_license_with_duration(duration_days: int = 365) -> str:
        """
        生成指定有效期的授权码
        使用示例：license_key = SystemTool.generate_license_with_duration(365)
        
        Args:
            duration_days: 有效期（天），默认365天
            
        Returns:
            str: 生成的授权码
        """
        # 计算截至日期
        expire_date = datetime.now() + timedelta(days=duration_days)
        expire_date_str = expire_date.strftime("%Y-%m-%d")
        
        # 生成授权码
        return SystemTool.generate_license_key(expire_date_str)
