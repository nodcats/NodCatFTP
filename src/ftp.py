import ftplib
import hashlib
import os
from typing import Dict, Optional
from PyQt5.QtWidgets import (QVBoxLayout, QPushButton, 
                           QLineEdit, QMessageBox,
                           QDialog, QFormLayout,
                           QTreeWidget, QTreeWidgetItem)


class FTPTreeDialog(QDialog):
    """FTP树状目录浏览器"""
    def __init__(self, ftp, initial_path="/", parent=None):
        super().__init__(parent)
        self.ftp = ftp
        self._setup_ui()
        self._load_directory(initial_path)
        
    def _setup_ui(self):
        """Initialize user interface"""
        self.setWindowTitle('选择远程目录')
        self.setGeometry(400, 200, 500, 400)
        
        layout = QVBoxLayout()
        
        # 树状视图
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel('FTP目录结构')
        self.tree.itemDoubleClicked.connect(self._on_item_selected)
        layout.addWidget(self.tree)
        
        # 确定按钮
        self.ok_button = QPushButton('确定')
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        
        self.setLayout(layout)
        
    def _load_directory(self, path):
        """加载指定路径的目录内容"""
        self.tree.clear()
        try:
            self.ftp.set_pasv(True)
            
            # 获取目录列表
            items = self._get_directory_listing(path)
            
            # 创建根节点
            root_item = QTreeWidgetItem(self.tree, [self._decode_path(path)])
            root_item.setData(0, 100, path)
            
            # 处理目录项
            if not items:
                QTreeWidgetItem(root_item, ["(空文件夹)"])
            else:
                self._process_directory_items(items, path, root_item)
            
            self.tree.expandItem(root_item)
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法加载目录: {str(e)}")

    def _get_directory_listing(self, path):
        """获取目录列表，尝试多种编码"""
        encodings = ['utf-8', 'gbk', 'latin-1']
        items = []
        last_error = None
        
        for encoding in encodings:
            try:
                self.ftp.encoding = encoding
                items = []
                # 优先尝试MLSD命令
                try:
                    self.ftp.retrlines('MLSD ' + path, items.append)
                    break
                except:
                    self.ftp.retrlines('NLST ' + path, items.append)
                    break
            except Exception as e:
                last_error = e
                continue
                
        if not items and last_error:
            raise last_error
            
        return items

    def _process_directory_items(self, items, parent_path, parent_item):
        """处理目录项并添加到树中"""
        for item in self._filter_items(items):
            name, item_type, full_path = self._parse_item(item, parent_path)
            
            if item_type == 'dir' or (item_type == 'unknown' and self._is_directory(full_path)):
                dir_item = QTreeWidgetItem(parent_item, [self._decode_item(name) + "/"])
                dir_item.setData(0, 100, full_path)
                QTreeWidgetItem(self._load_subdirectories(dir_item))
            else:
                file_item = QTreeWidgetItem(parent_item, [self._decode_item(name)])
                file_item.setData(0, 100, full_path)

    def _filter_items(self, items):
        """过滤掉.和..目录"""
        filtered = []
        for item in items:
            if ';' in item:  # MLSD格式
                name = item.split(';')[-1].strip()
                if name not in ['.', '..']:
                    filtered.append(item)
            else:  # NLST格式
                if item not in ['.', '..']:
                    filtered.append(item)
        return filtered

    def _parse_item(self, item, parent_path):
        """解析目录项"""
        if ';' in item:  # MLSD格式
            name = item.split(';')[-1].strip()
            item_type = 'dir' if 'type=dir' in item.lower() else 'file'
        else:  # NLST格式
            name = item
            item_type = 'unknown'
        
        full_path = parent_path.rstrip('/') + '/' + name.lstrip('/') if parent_path != '/' else '/' + name.lstrip('/')
        return name, item_type, full_path

    def _is_directory(self, path):
        """检查给定路径是否是目录"""
        try:
            old_pwd = self.ftp.pwd()
            try:
                self.ftp.cwd(path)
                self.ftp.cwd(old_pwd)
                return True
            except:
                return False
        except:
            return False

    def _decode_path(self, path):
        """解码路径，支持中英文显示"""
        if isinstance(path, str):
            return path
            
        for encoding in ['utf-8', 'gbk', 'latin1']:
            try:
                return path.decode(encoding)
            except UnicodeDecodeError:
                continue
                
        return str(path)

    def _decode_item(self, item):
        """解码路径项"""
        if isinstance(item, bytes):
            for encoding in ['utf-8', 'gbk', 'gb2312', 'big5', 'latin1']:
                try:
                    return item.decode(encoding)
                except UnicodeDecodeError:
                    continue
        return str(item)
    
    def _on_item_selected(self, item, column):
        """处理目录项双击事件"""
        path = item.data(0, 100)
        if self._is_directory(path):
            self._load_subdirectories(item)

    def _load_subdirectories(self, parent_item):
        """加载子目录"""
        path = parent_item.data(0, 100)
        try:
            parent_item.takeChildren()  # 清空现有的"加载中..."项
            
            items = self._get_directory_listing(path)
            
            if not items:
                QTreeWidgetItem(parent_item, ["(空文件夹)"])
                return
                
            self._process_directory_items(items, path, parent_item)
                    
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法加载子目录: {str(e)}")
            QTreeWidgetItem(parent_item, ["加载失败"])

    def get_selected_path(self):
        """获取当前选择的路径"""
        selected = self.tree.currentItem()
        return selected.data(0, 100) if selected else ""


class FTPSynchronizer:
    """FTP文件同步器（完全按照本地目录结构同步）"""
    def __init__(self, ftp: ftplib.FTP):
        self.ftp = ftp
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
        
    def sync_local_to_remote(self, local_path: str, remote_path: str):
        """
        完全按照本地目录同步到远程（删除远程多余文件）
        :param local_path: 本地目录路径
        :param remote_path: 远程FTP目录路径
        """
        if not os.path.isdir(local_path):
            raise ValueError(f"本地路径不是目录: {local_path}")
        # 确保远程目录存在
        self._ensure_remote_directory(remote_path)
        # 获取文件总数用于进度计算
        total_files = self._count_local_files(local_path)
        if total_files == 0:
            if self.progress_callback:
                self.progress_callback(100, "没有文件需要同步")
            return
            
        # 执行同步（包含清理远程多余文件）
        self._sync_local_to_remote(local_path, remote_path, total_files, 0)
        
    def _count_local_files(self, path: str) -> int:
        """统计本地文件总数"""
        count = 0
        for root, _, files in os.walk(path):
            count += len(files)
        return count
    
    def _ensure_remote_directory(self, path: str):
        """确保远程目录存在"""
        try:
            self.ftp.cwd(path)
        except:
            parts = [p for p in path.split('/') if p]
            current = ""
            for part in parts:
                current += f"/{part}"
                try:
                    self.ftp.cwd(current)
                except:
                    self.ftp.mkd(current)
    
    def _sync_local_to_remote(self, local_path: str, remote_path: str, total_files: int, processed: int) -> int:
        """
        高效同步方案（智能比对文件差异）
        :return: 已处理文件数
        """
        # 获取带元数据的文件列表
        remote_items = self._get_remote_items_with_meta(remote_path)
        local_items = self._get_local_items_with_meta(local_path)
        
        # 1. 处理需要删除的远程文件（本地不存在的）
        for name, remote_meta in remote_items.items():
            if name not in local_items:
                remote_item = f"{remote_path.rstrip('/')}/{name}"
                self._delete_remote_item(remote_item, remote_meta['type'])
                if self.progress_callback:
                    progress = int(processed / total_files * 100)
                    self.progress_callback(progress, f"清理远程: {name}")
        
        # 2. 智能同步文件
        for name, local_meta in local_items.items():
            local_item = os.path.join(local_path, name)
            remote_item = f"{remote_path.rstrip('/')}/{name}"
            remote_meta = remote_items.get(name)
            
            if local_meta['type'] == 'dir':
                # 处理目录
                self._ensure_remote_directory(remote_item)
                processed = self._sync_local_to_remote(local_item, remote_item, total_files, processed)
            else:
                # 检查是否需要同步
                if self._needs_sync(local_meta, remote_meta):
                    self._smart_upload(local_item, remote_item, local_meta)
                    processed += 1
                    if self.progress_callback:
                        progress = int(processed / total_files * 100)
                        self.progress_callback(progress, f"同步中: {name}")
                else:
                    processed += 1
                    if self.progress_callback:
                        self.progress_callback(int(processed / total_files * 100), f"跳过[最新]: {name}")

        return processed
    def _needs_sync(self, local_meta: dict, remote_meta: Optional[dict]) -> bool:
        """判断文件是否需要同步"""
        if not remote_meta:
            return True  # 远程不存在
        
        # 1. 大小不同肯定需要同步
        if local_meta['size'] != remote_meta['size']:
            return True
        
        if local_meta['mtime'] != remote_meta['mtime']:
            return True
        
        return False
    def _smart_upload(self, local_path: str, remote_path: str, local_meta: dict):
        """带断点续传的智能上传"""
        # 1. 尝试二进制追加模式（续传）
        try:
            remote_size = self.ftp.size(remote_path)
            if 0 < remote_size < local_meta['size']:
                with open(local_path, 'rb') as f:
                    f.seek(remote_size)
                    self.ftp.storbinary(
                        f"APPE {remote_path}", 
                        f,
                        blocksize=1024 * 1024  # 1MB块大小
                    )
                return
        except:
            pass
        
        # 2. 完整上传
        with open(local_path, 'rb') as f:
            self.ftp.storbinary(
                f"STOR {remote_path}",
                f,
                blocksize=1024 * 1024
            )
    def _get_local_items_with_meta(self, path: str) -> Dict[str, dict]:
        """获取本地文件列表（含元数据）"""
        items = {}
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            stat = os.stat(full_path)
            
            items[name] = {
                'type': 'dir' if os.path.isdir(full_path) else 'file',
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'checksum': self._file_checksum(full_path) if not os.path.isdir(full_path) else None
            }
        return items

    def _get_remote_items_with_meta(self, path: str) -> Dict[str, dict]:
        """获取远程文件列表（含轻量级校验和）"""
        items = {}
        try:
            lines = []
            self.ftp.retrlines(f'MLSD {path}', lines.append)
            for line in lines:
                parts = [p.strip() for p in line.split(';')]
                name = parts[-1]
                if name in ('.', '..'):
                    continue
                    
                attrs = {}
                for part in parts[:-1]:
                    if '=' in part:
                        k, v = part.split('=', 1)
                        attrs[k.lower()] = v.lower()
                
                remote_file = f"{path.rstrip('/')}/{name}"
                item = {
                    'type': 'dir' if attrs.get('type') == 'dir' else 'file',
                    'size': int(attrs.get('size', 0)),
                    'mtime': self._parse_ftp_time(attrs.get('modify'))
                }
                
                items[name] = item
                
        except:
            # 回退方案
            try:
                names = []
                self.ftp.retrlines(f'NLST {path}', names.append)
                for name in names:
                    if name in ('.', '..'):
                        continue
                        
                    remote_file = f"{path.rstrip('/')}/{name}"
                    is_dir = self._is_remote_dir(remote_file)
                    
                    item = {
                        'type': 'dir' if is_dir else 'file',
                        'size': self._get_remote_size(remote_file) if not is_dir else 0,
                        'mtime': None
                    }
                    items[name] = item
            except Exception as e:
                print(f"获取远程列表失败: {str(e)}")
        return items
    
    
    def _get_remote_checksum_light(self, remote_path: str) -> str:
        """远程文件轻量级校验和（基于头尾+大小）"""
        try:
            # 获取文件大小
            size = self.ftp.size(remote_path)
            if size is None or size == 0:
                return "0"
            
            # 获取文件头部 (前1KB)
            head = b''
            def head_callback(data: bytes):
                nonlocal head
                remaining = 1024 - len(head)
                head += data[:remaining]
            
            # 使用 REST 命令实现断点续传
            self.ftp.retrbinary(f'RETR {remote_path}', head_callback, blocksize=1024, rest=0)
            
            # 获取文件尾部 (最后1KB)
            tail = b''
            def tail_callback(data: bytes):
                nonlocal tail
                if len(tail) < 1024:
                    tail = data[-1024:] + tail[:1024-len(data)]
                else:
                    tail = data[-1024:] + tail[:-len(data)]
            
            start_pos = max(0, size - 1024)
            self.ftp.retrbinary(f'RETR {remote_path}', tail_callback, blocksize=1024, rest=start_pos)
            
            # 计算轻量级校验和
            return hashlib.md5(
                f"{size}-{head[:100]}-{tail[-100:]}".encode()
            ).hexdigest()
            
        except Exception as e:
            print(f"获取远程校验和失败 {remote_path}: {str(e)}")
            return "0"  # 返回默认值
    def _file_checksum(self, path: str) -> str:
        """计算文件校验和（快速版）"""
        # 使用文件头部+尾部+大小的组合作为轻量级校验
        size = os.path.getsize(path)
        with open(path, 'rb') as f:
            head = f.read(1024)
            f.seek(max(0, size-1024))
            tail = f.read(1024)
        return hashlib.md5(f"{size}-{head[:100]}-{tail[-100:]}".encode()).hexdigest()


    def _parse_ftp_time(self, time_str: Optional[str]) -> float:
        """解析FTP时间戳"""
        if not time_str:
            return 0
        try:
            from datetime import datetime
            return datetime.strptime(time_str, "%Y%m%d%H%M%S").timestamp()
        except:
            return 0

    def _get_remote_size(self, path: str) -> int:
        """获取远程文件大小"""
        try:
            return self.ftp.size(path)
        except:
            return 0
    def _get_local_items(self, path: str) -> Dict[str, str]:
        """获取本地文件/目录列表"""
        items = {}
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            items[name] = 'dir' if os.path.isdir(full_path) else 'file'
        return items
    def _get_remote_items(self, path: str) -> Dict[str, str]:
        """更健壮的远程文件列表获取方法"""
        items = {}
        
        # 方法1：尝试MLSD命令（最准确）
        try:
            lines = []
            self.ftp.retrlines(f'MLSD {path}', lines.append)
            for line in lines:
                parts = [p.strip() for p in line.split(';')]
                name = parts[-1]
                if name not in ('.', '..'):
                    item_type = 'dir' if 'type=dir' in line.lower() else 'file'
                    items[name] = item_type
            return items
        except Exception as mlsd_error:
            print(f"MLSD失败，尝试备用方法: {str(mlsd_error)}")

        # 方法2：尝试NLST命令（基本兼容）
        try:
            names = []
            self.ftp.retrlines(f'NLST {path}', names.append)
            for name in names:
                if name not in ('.', '..'):
                    try:
                        # 通过CWD测试是否为目录
                        old_pwd = self.ftp.pwd()
                        try:
                            self.ftp.cwd(name)
                            self.ftp.cwd(old_pwd)
                            items[name] = 'dir'
                        except:
                            items[name] = 'file'
                    except:
                        items[name] = 'unknown'
            return items
        except Exception as nlst_error:
            print(f"NLST失败: {str(nlst_error)}")

        # 方法3：最终回退方案
        try:
            # 尝试直接列出当前目录内容
            self.ftp.cwd(path)
            names = self.ftp.nlst()
            for name in names:
                if name not in ('.', '..'):
                    try:
                        self.ftp.cwd(name)
                        self.ftp.cwd('..')
                        items[name] = 'dir'
                    except:
                        items[name] = 'file'
            return items
        except Exception as final_error:
            print(f"所有方法均失败: {str(final_error)}")
            return {}  # 返回空字典而不是报错
    def _upload_file(self, local_path: str, remote_path: str):
        """上传文件到远程"""
        try:
            with open(local_path, 'rb') as f:
                self.ftp.storbinary(f"STOR {remote_path}", f)
        except Exception as e:
            print(f"上传失败 {local_path} -> {remote_path}: {str(e)}")
    


    def _delete_remote_item(self, remote_path: str, item_type: str):
        """删除远程文件或目录（解决编码问题）"""
        try:
            
            if item_type == 'dir':
                # 获取目录内容（已过滤特殊目录）
                items = self._get_remote_items(remote_path)
                for name, sub_type in items.items():
                    # 处理子路径编码
                    sub_path = f"{remote_path.rstrip('/')}/{name}"
                    self._delete_remote_item(sub_path, sub_type)

                # 删除目录本身
                try:
                    self.ftp.rmd(remote_path)
                except ftplib.error_perm as e:
                    if "550" in str(e):  # 目录可能非空
                        print(f"目录删除失败，可能非空: {remote_path}")
                    else:
                        raise
            else:
                # 删除文件
                self.ftp.delete(remote_path)
        except Exception as e:
            print(f"删除失败 {remote_path}: {str(e)}")

    def _is_remote_dir(self, path: str) -> bool:
        """检查是否为远程目录"""
        try:
            old_pwd = self.ftp.pwd()
            self.ftp.cwd(path)
            self.ftp.cwd(old_pwd)
            return True
        except:
            return False


class FTPConfigDialog(QDialog):
    """FTP配置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize user interface"""
        self.setWindowTitle('FTP服务器配置')
        self.setGeometry(400, 400, 400, 250)
        
        layout = QFormLayout()
        
        # 创建表单控件
        self._create_form_controls(layout)
        
        # 添加按钮
        self._add_buttons(layout)
        
        self.setLayout(layout)
    
    def _create_form_controls(self, layout):
        """创建表单控件"""
        self.ftp_host_edit = QLineEdit("")
        self.ftp_user_edit = QLineEdit("")
        self.ftp_pass_edit = QLineEdit("")
        self.ftp_pass_edit.setEchoMode(QLineEdit.Password)
        self.remote_path_edit = QLineEdit("/")
        
        layout.addRow('FTP服务器地址:', self.ftp_host_edit)
        layout.addRow('用户名:', self.ftp_user_edit)
        layout.addRow('密码:', self.ftp_pass_edit)
        layout.addRow('远程路径:', self.remote_path_edit)
    
    def _add_buttons(self, layout):
        """添加按钮"""
        self.test_button = QPushButton('测试连接')
        self.test_button.clicked.connect(self._test_connection)
        layout.addRow(self.test_button)
        
        self.browse_button = QPushButton('浏览')
        self.browse_button.clicked.connect(self._browse_remote_path)
        layout.addRow(self.browse_button)
        
        self.save_button = QPushButton('保存')
        self.save_button.clicked.connect(self.accept)
        layout.addRow(self.save_button)
    
    def _test_connection(self):
        """测试FTP连接"""
        host = self.ftp_host_edit.text()
        user = self.ftp_user_edit.text()
        password = self.ftp_pass_edit.text()
        
        if not all([host, user, password]):
            QMessageBox.warning(self, "警告", "请填写完整的FTP连接信息")
            return
            
        try:
            ftp = ftplib.FTP(host, user, password)
            ftp.quit()
            QMessageBox.information(self, "成功", "FTP连接测试成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接失败: {str(e)}")
    
    def _browse_remote_path(self):
        """浏览远程FTP路径"""
        host = self.ftp_host_edit.text()
        user = self.ftp_user_edit.text()
        password = self.ftp_pass_edit.text()
        
        if not all([host, user, password]):
            QMessageBox.warning(self, "警告", "请填写完整的FTP连接信息")
            return
            
        try:
            ftp = ftplib.FTP(timeout=10)
            ftp.connect(host, 21)
            ftp.login(user, password)
            
            initial_path = self.remote_path_edit.text() or "/"
            
            dialog = FTPTreeDialog(ftp, initial_path, self)
            dialog.setModal(True)
            dialog.show()
            
            if dialog.exec_() == QDialog.Accepted:
                selected_path = dialog.get_selected_path()
                if selected_path:
                    self.remote_path_edit.setText(selected_path)
            
            ftp.quit()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"浏览失败: {str(e)}")
        