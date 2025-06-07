# setup.py
import os
import subprocess
from setuptools import setup
import PyInstaller.__main__

def build_executable():
    # PyInstaller打包命令
    PyInstaller.__main__.run([
        './src/main.py',
        '--onefile',
        '--name=nodcat',
        '--add-data=config.json:.',
        '--add-data=./img/*:img/',
        '--distpath=./dist'
    ])

if __name__ == '__main__':
    build_executable()

    # 复制文件到deb打包目录
    os.system('cp dist/nodcat deb_package/usr/bin/')
    
    print("正在构建deb包...")
    # 执行dpkg-deb命令
    subprocess.run(["dpkg-deb", "--build", "deb_package", "./build/v1.0/nodcat.deb"], check=True)
    print("deb包构建完成！请在 build/v1.0/nodcat-1.0-amd64.deb 下查看")

