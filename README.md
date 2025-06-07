# NodCat FTP 同步工具

![NodCat图标](img/icon.png)

一个简单实用的 FTP 文件夹同步工具，支持定时自动同步和系统托盘运行。

## 功能特性

- 本地与 FTP 服务器文件夹双向同步
- 支持定时自动同步
- 支持中文路径
- 系统托盘运行
- 跨平台支持(Linux/Windows)

## 安装指南

### Linux (DEB 包)

1. 下载最新版本的 DEB 包
2. 使用以下命令安装:
   ```bash
   sudo dpkg -i nodcat.deb
   ```
3. 如果缺少依赖，运行:
   ```bash
   sudo apt-get install -f
   ```

### Windows (EXE)

1. 下载最新版本的 EXE 安装包
2. 双击运行安装程序
3. 按照向导完成安装

### 从源代码构建

#### 依赖项

- Python 3.6+
- PyQt5
- PyInstaller (Linux)
- cx_Freeze (Windows)

#### Linux 构建

```bash
python setup_linux_deb.py
```

#### Windows 构建

```bash
python setup_windows_exe.py
```

## 使用方法

1. 安装程序会自动创建配置文件`config.json`
2. 点击"FTP 设置"配置服务器信息
3. 选择本地同步路径
4. 点击"同步"按钮开始手动同步
5. 使用"定时设置"配置自动同步

程序会最小化到系统托盘，右键托盘图标可打开主界面或退出程序。

## 配置说明

配置文件`config.json`示例:

```json
{
  "ftp": {
    "host": "ftp.example.com",
    "username": "your_username",
    "password": "your_password",
    "remote_path": "/remote/path"
  },
  "local_path": "/local/path",
  "schedule": {
    "frequency": "每天",
    "time": "00:00"
  }
}
```

## 开发与贡献

欢迎提交 Issue 和 Pull Request。

项目地址: [CSDN 博客](https://blog.csdn.net/2202_75618418)

## 许可证

©2025 版权所有
