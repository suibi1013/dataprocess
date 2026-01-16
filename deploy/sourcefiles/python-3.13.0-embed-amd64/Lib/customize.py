# customize.py - 嵌入式Python环境初始化脚本
import sys
import os

# 获取当前脚本所在目录（Lib目录）
lib_dir = os.path.dirname(os.path.abspath(__file__))
python_embed_dir = os.path.dirname(lib_dir)

# 获取上层site-packages目录路径
parent_site_packages = os.path.join(python_embed_dir, '..', 'site-packages')

# 添加win32和win32/lib目录到Python路径
win32_path = os.path.join(parent_site_packages, 'win32')
win32_lib_path = os.path.join(parent_site_packages, 'win32', 'lib')

if win32_path not in sys.path:
    sys.path.insert(1, win32_path)
if win32_lib_path not in sys.path:
    sys.path.insert(1, win32_lib_path)

# 添加pywin32_system32目录到系统PATH，确保DLL文件能被找到
pywin32_system32 = os.path.join(parent_site_packages, 'pywin32_system32')
if pywin32_system32 not in os.environ['PATH']:
    os.environ['PATH'] = pywin32_system32 + ';' + os.environ['PATH']

# 尝试初始化pythoncom模块（可选）
try:
    import pythoncom
    # 初始化COM库（对于某些嵌入式环境可能需要）
    # pythoncom.CoInitialize()
except ImportError:
    pass  # 忽略导入失败，继续执行
