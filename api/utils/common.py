import hashlib
import base64
class CommonUtils:
    @staticmethod
    def generate_unique_code(text: str):        
        """
        根据文本生成稳定的标识码（不可逆）。
        
        Args:
            text (str): 字符串文本（可以包含中文）
        
        Returns:
            str: 32位十六进制的MD5标识码
        """
        # 1. 将文本字符串编码为UTF-8字节序列
        # 这确保了中文、英文、特殊字符都能被正确处理
        text_bytes = text.encode('utf-8')
        
        # 2. 创建MD5哈希对象并更新数据
        hash_object = hashlib.md5()
        hash_object.update(text_bytes)
        
        # 3. 获取十六进制表示的哈希值
        unique_code = hash_object.hexdigest()
        
        return unique_code

    def encode_text_to_code(text: str) -> str:
        """
        将文本编码为Base64字符串（可逆）。
        
        Args:
            text (str): 原始文本
        
        Returns:
            str: Base64编码后的字符串
        """
        # 将字符串编码为UTF-8字节，再进行Base64编码
        text_bytes = text.encode('utf-8')
        
        # 使用 URL安全的Base64编码，并去除填充符 '='
        code_bytes = base64.urlsafe_b64encode(text_bytes)
        code = code_bytes.decode('ascii').rstrip('=')  # Base64结果是ASCII字符
        return code

    def decode_code_to_text(code: str) -> str:
        """
        将用于文件名的Base64字符串解码为原始文本。
        
        Args:
            code (str): 经过 encode_text_to_code 编码后的字符串
        
        Returns:
            str: 解码得到的原始文本
        """
        # 计算需要补回多少个 '=' 才能使长度成为4的倍数
        missing_padding = len(code) % 4
        if missing_padding:
            # 补齐到4的倍数
            code += '=' * (4 - missing_padding)
        
        # 使用 URL安全的Base64解码
        text_bytes = base64.urlsafe_b64decode(code)
        
        # 将字节解码为UTF-8字符串
        text = text_bytes.decode('utf-8')
        
        return text