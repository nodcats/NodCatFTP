import os
import sys

APP_ICON_LINUX = "./img/icon.png"
APP_ICON_WINDOWS = "./img/icon.ico"
APP_ICON_MAC = "./img/icon.icns"

def resource_path(relative_path):
    """获取打包后的资源绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后的临时目录 (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # 开发环境的当前目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_icon_path():
    """根据平台返回正确的图标路径"""
    # 获取当前脚本所在目录
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    
    if sys.platform == 'win32':
        icon_path = os.path.join(base_path, 'img', 'icon.ico')
    elif sys.platform == 'darwin':
        icon_path = os.path.join(base_path, 'img', 'icon.icns')
    else:
        icon_path = os.path.join(base_path, 'img', 'icon.png')
    
    # 检查文件是否存在
    if not os.path.exists(icon_path):
        # 如果打包后找不到，尝试从资源路径获取
        if sys.platform == 'win32':
            return resource_path(APP_ICON_WINDOWS)
        elif sys.platform == 'darwin':
            return resource_path(APP_ICON_MAC)
        else:
            return resource_path(APP_ICON_LINUX)
    
    return icon_path