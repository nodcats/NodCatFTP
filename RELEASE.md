# NodCat FTP 同步工具 v1.0 发行说明

## 版本信息

- 版本号: 1.0
- 发布日期: [2025-06-07]

## 新功能

- 本地与 FTP 服务器文件夹双向同步
- 支持定时自动同步
- 支持中文路径
- 系统托盘运行
- 跨平台支持(Linux/Windows)

## 修复的问题

[修复同步时，已有文件同步需重复上传问题]

## 安装指南

### Linux (DEB 包)

1. 下载 nodcat-1.0-amd64.deb
2. 安装命令:
   ```bash
   sudo dpkg -i nodcat-1.0-amd64.deb
   ```
3. 如果缺少依赖，运行:
   ```bash
   sudo apt-get install -f
   ```

### Windows (EXE)

1. 下载 NodCat-1.0-setup.exe
2. 双击运行安装程序

## 系统要求

- Python 3.6+
- PyQt5
- Linux: dpkg 工具
- Windows: 无特殊要求
