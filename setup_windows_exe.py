from cx_Freeze import setup, Executable

setup(
    name="NodCat",
    version="1.0",
    description="一个简单实用的FTP同步工具。",
    executables=[Executable("./src/main.py", base="Win32GUI", icon="./img/icon.ico")]
)
