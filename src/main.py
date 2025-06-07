import argparse
import os
import sys
import ftplib
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                            QFileDialog, QLineEdit, QLabel, QProgressBar,
                            QMessageBox, QSystemTrayIcon, QMenu, QAction,
                            QDialog)
from PyQt5.QtCore import QTimer, QTime, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import config
from ftp import FTPConfigDialog, FTPSynchronizer
from schedule import ScheduleConfigDialog
from utils import get_icon_path
class SyncWorker(QThread):
    """FTP同步工作线程"""
    progress_updated = pyqtSignal(int, str)
    sync_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ftp_config, local_path, remote_path, parent=None):
        super().__init__(parent)
        self.ftp_config = ftp_config
        self.local_path = local_path
        self.remote_path = remote_path
        self._stopped = False
        
    def run(self):
        """执行同步操作"""
        try:
            with ftplib.FTP(
                self.ftp_config['host'],
                self.ftp_config['username'],
                self.ftp_config['password']
            ) as ftp:
                ftp.encoding = 'utf-8'
                ftp.cwd(self.remote_path)
                
                synchronizer = FTPSynchronizer(ftp)
                synchronizer.set_progress_callback(self._on_progress_update)
                synchronizer.sync_local_to_remote(self.local_path, self.remote_path)
                
                if not self._stopped:
                    self.sync_finished.emit()
        except Exception as e:
            if not self._stopped:
                self.error_occurred.emit(str(e))
    
    def _on_progress_update(self, progress, message):
        """处理进度更新"""
        if not self._stopped:
            self.progress_updated.emit(progress, message)
    
    def stop(self):
        """停止同步"""
        self._stopped = True

class FTPSyncApp(QWidget):
    def __init__(self):
        super().__init__()
        self.config = config.load_config()
        self.timer = None
        self.tray_icon = None
        self.sync_worker = None
        # 锁定窗口大小，禁用最大化
        self.setFixedSize(400, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self._setup_ui()
        self._setup_tray_icon()
        self._setup_schedule_sync()
        
    def closeEvent(self, event):
        """Override close event to minimize to tray instead of quitting"""
        self.hide()
        self._show_tray_notification(
            "FTP同步工具",
            "程序已最小化到系统托盘"
        )
        event.ignore()  # 再阻止默认关闭行为
    def showEvent(self, event):
        print("当前窗口图标:", self.windowIcon().availableSizes())
        print("窗口管理器类名:", self.window().windowHandle().metaObject().className())
    def _show_about_dialog(self):
        """Show about dialog"""
        about_text = """
        <b>FTP文件夹同步</b><br><br>
        版本: 1.0<br>
        作者: 盹猫<br>
        联系方式: 1461361074@qq.com<br><br>
        功能说明:<br>
        - 本地与FTP服务器文件夹双向同步<br>
        - 支持定时自动同步<br>
        - 支持中文路径<br>
        - 系统托盘运行<br><br>
        项目地址: <br>
        CSDN博客: https://blog.csdn.net/2202_75618418<br>
        ©2025 版权所有
        """
        msg = QMessageBox(self)  # 设置父窗口为self
        msg.setWindowTitle("关于NodCat")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowModality(Qt.ApplicationModal)  # 设置为应用程序模态
        msg.setAttribute(Qt.WA_DeleteOnClose, False)  # 防止关闭时删除对象
        msg.exec_()  # 使用exec_()确保模态行为

    def _setup_tray_icon(self):
        """Initialize system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path=get_icon_path()
        print(icon_path,QIcon(icon_path).isNull())
        self.tray_icon.setIcon(QIcon(icon_path))
        
        tray_menu = QMenu()
        actions = [
            ("显示窗口", self.show),
            ("FTP配置", self.show_ftp_config),
            ("同步一下", self.sync_folders),
            ("关于", self._show_about_dialog),
            ("退出", QApplication.quit)
        ]
        
        # 添加分隔线
        tray_menu.addSeparator()
        
        for text, slot in actions:
            action = QAction(text, self)
            action.triggered.connect(slot)
            tray_menu.addAction(action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _setup_ui(self):
        """Initialize user interface"""
        self.setWindowTitle('NodCat FTP同步')
        self.setWindowIcon(QIcon(get_icon_path()))
        self.setGeometry(300, 300, 400, 300)  # 增加高度以适应进度条

        layout = QVBoxLayout()

        # Local path selection
        self.local_path_edit = QLineEdit(self.config.get('local_path', ''))
        self._add_path_selection_widgets(layout, "选择本地路径:", self.local_path_edit)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("准备同步")
        layout.addWidget(self.progress_bar)

        # Control buttons
        buttons = [
            ('FTP服务器配置', self.show_ftp_config),
            ('同步一下', self.sync_folders),
            ('定时同步配置', self.show_schedule_config)
        ]
        
        for text, slot in buttons:
            button = QPushButton(text)
            button.clicked.connect(slot)
            layout.addWidget(button)

        self.setLayout(layout)

    def _add_path_selection_widgets(self, layout, label_text, line_edit):
        """Helper method to add path selection widgets"""
        layout.addWidget(QLabel(label_text))
        layout.addWidget(line_edit)
        browse_button = QPushButton('浏览')
        browse_button.clicked.connect(lambda: self._select_directory(line_edit))
        layout.addWidget(browse_button)

    def _select_directory(self, line_edit):
        """Select directory and update the given line edit"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择本地文件夹")
        if folder_path:
            line_edit.setText(folder_path)
            self._update_config('local_path', folder_path)

    def _update_config(self, key, value):
        """Update config value and save"""
        self.config[key] = value
        config.save_config(self.config)


    def _show_tray_notification(self, title, message):
        """Show tray notification with blinking icon"""
        icon_path = get_icon_path()
        
        if sys.platform == 'darwin':  # macOS
            try:
                from Foundation import NSUserNotification
                from Foundation import NSUserNotificationCenter
                
                notification = NSUserNotification.alloc().init()
                notification.setTitle_(title)
                notification.setInformativeText_(message)
                
                center = NSUserNotificationCenter.defaultUserNotificationCenter()
                center.deliverNotification_(notification)
                return
            except Exception as e:
                print(f"macOS原生通知失败: {e}")
                
        # 获取当前平台对应的图标路径
        icon_path = get_icon_path()
        notification_icon = QIcon(icon_path)
        
        print(icon_path,notification_icon.isNull())
            
        # 默认使用Qt通知
        if not hasattr(self, 'tray_icon') or self.tray_icon is None:
            self.tray_icon = QSystemTrayIcon()
            self.tray_icon.setIcon(notification_icon)  # 设置托盘图标
            self.tray_icon.show()  # 必须显示托盘图标
        
        self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.NoIcon,  # 无图标
                2000
        )

    def _setup_schedule_sync(self):
        """根据配置设置定时同步"""
        if self.timer:
            self.timer.stop()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.sync_folders)
        
        # 从配置获取参数
        schedule_time = QTime.fromString(self.config['schedule']['time'], 'HH:mm')
        frequency = self.config['schedule']['frequency']
        
        # 计算首次触发延迟
        current_time = QTime.currentTime()
        msecs_to_trigger = current_time.msecsTo(schedule_time)
        
        # 处理已过时间的情况
        if msecs_to_trigger <= 0:
            msecs_to_trigger += 24 * 60 * 60 * 1000  # 加到明天同一时间
        
        # 根据频率设置不同间隔
        if frequency == "每周":
            interval = 7 * 24 * 60 * 60 * 1000  # 每周
        elif frequency == "每月":
            interval = 30 * 24 * 60 * 60 * 1000  # 每月（简化按30天计算）
        else:  # 默认每天
            interval = 24 * 60 * 60 * 1000
        
        # 确保最小间隔为1小时（防止意外设置）
        interval = max(interval, 3600000)
        
        # 设置定时器（分阶段确保首次触发时间准确）
        QTimer.singleShot(msecs_to_trigger, lambda: [
            self.sync_folders(),  # 立即执行一次
            self.timer.start(interval)  # 启动定期执行
        ])
        
        print(f"定时同步已设置: 频率={frequency}, "
            f"首次触发={schedule_time.toString('HH:mm')}, "
            f"间隔={interval/(60 * 60 * 1000)}小时")
        
    def show_ftp_config(self):
        """Show FTP configuration dialog"""
        dialog = FTPConfigDialog(self)
        ftp_config = self.config.setdefault('ftp', {})
        
        dialog.ftp_host_edit.setText(ftp_config.get('host', ''))
        dialog.ftp_user_edit.setText(ftp_config.get('username', ''))
        dialog.ftp_pass_edit.setText(ftp_config.get('password', ''))
        dialog.remote_path_edit.setText(ftp_config.get('remote_path', ''))
        
        if dialog.exec_() == QDialog.Accepted:
            ftp_config.update({
                'host': dialog.ftp_host_edit.text(),
                'username': dialog.ftp_user_edit.text(),
                'password': dialog.ftp_pass_edit.text(),
                'remote_path': dialog.remote_path_edit.text()
            })
            config.save_config(self.config)

    def _on_sync_progress(self, progress, message):
        """更新同步进度"""
        self.progress_bar.setValue(progress)
        """设置进度条文本，确保不超过10个字符"""
        max_len = 20
        if len(message) > max_len:
            message = message[:max_len-3] + "..."  # 保留前7个字符 + "..."
        self.progress_bar.setFormat(message)

    def _on_sync_finished(self):
        """同步完成处理"""
        self.progress_bar.setFormat("同步完成")
        self._show_tray_notification("同步成功", "文件夹同步完成")
        self.sync_worker = None

    def _on_sync_error(self, error):
        """同步错误处理"""
        self.progress_bar.setFormat("同步失败")
        self._show_tray_notification("同步失败", f"同步失败: {error}")
        self.sync_worker = None

    def sync_folders(self):
        """Synchronize folders between local and FTP"""
        if self.sync_worker and self.sync_worker.isRunning():
            QMessageBox.warning(self, "警告", "同步正在进行中，请等待完成")
            return

        local_path = self.local_path_edit.text()
        ftp_config = self.config.get('ftp', {})

        if not self._validate_sync_parameters(local_path, ftp_config):
            return

        # 重置进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("正在同步...")

        # 创建并启动工作线程
        self.sync_worker = SyncWorker(ftp_config, local_path, ftp_config['remote_path'], self)
        self.sync_worker.progress_updated.connect(self._on_sync_progress)
        self.sync_worker.sync_finished.connect(self._on_sync_finished)
        self.sync_worker.error_occurred.connect(self._on_sync_error)
        self.sync_worker.start()

    def _validate_sync_parameters(self, local_path, ftp_config):
        """Validate sync parameters"""
        required_fields = [
            local_path,
            ftp_config.get('remote_path', ''),
            ftp_config.get('host', ''),
            ftp_config.get('username', ''),
            ftp_config.get('password', '')
        ]
        
        if not all(required_fields):
            QMessageBox.warning(self, "警告", "请确保已填写并保存所有FTP信息和路径设置。")
            return False
            
        # 验证本地路径
        if not os.path.exists(local_path):
            QMessageBox.warning(self, "警告", f"本地路径不存在: {local_path}\n请选择有效的本地路径。")
            return False
            
        if not os.path.isdir(local_path):
            QMessageBox.warning(self, "警告", f"本地路径不是目录: {local_path}\n请选择有效的目录路径。")
            return False
            
        # 验证远程路径
        try:
            with self._create_ftp_connection(ftp_config) as ftp:
                try:
                    ftp.cwd(ftp_config['remote_path'])
                except ftplib.error_perm as e:
                    if '550' in str(e):  # 路径不存在错误码
                        QMessageBox.warning(self, "警告", 
                            f"远程路径不存在: {ftp_config['remote_path']}\n"
                            "请在FTP配置中设置正确的远程路径。")
                        return False
                    raise
        except Exception as e:
            QMessageBox.warning(self, "警告", f"验证远程路径时出错: {str(e)}")
            return False
            
        return True

    def _create_ftp_connection(self, ftp_config):
        """Create and return FTP connection"""
        ftp = ftplib.FTP(
            ftp_config['host'],
            ftp_config['username'],
            ftp_config['password']
        )
        ftp.encoding = 'utf-8'
        ftp.cwd(ftp_config['remote_path'])
        return ftp

    def _sync_local_to_remote(self, ftp, local_path, remote_path):
        """同步本地到远程"""
        synchronizer = FTPSynchronizer(ftp)
        try:
            synchronizer.sync_local_to_remote(local_path, remote_path)
            self._show_tray_notification("同步完成", f"本地目录已成功同步到FTP服务器")
        except Exception as e:
            self._show_tray_notification("同步失败", f"同步过程中发生错误: {str(e)}")
            raise
            
    def _sync_remote_to_local(self, ftp, local_path, remote_path):
        """Sync remote FTP files to local"""
        for file_name in ftp.nlst():
            local_file = os.path.join(local_path, file_name)
            if not os.path.exists(local_file):
                with open(local_file, 'wb') as file:
                    ftp.retrbinary(f'RETR {file_name}', file.write)

    def show_schedule_config(self):
        """Show schedule configuration dialog"""
        dialog = ScheduleConfigDialog(self)
        schedule_config = self.config.setdefault('schedule', {
            'frequency': '每天',
            'time': '00:00'
        })
        
        dialog.freq_combo.setCurrentText(schedule_config.get('frequency', '每天'))
        dialog.time_edit.setTime(QTime.fromString(schedule_config.get('time', '00:00'), 'hh:mm'))
        
        if dialog.exec_() == QDialog.Accepted:
            schedule_config.update({
                'frequency': dialog.freq_combo.currentText(),
                'time': dialog.time_edit.time().toString('hh:mm')
            })
            config.save_config(self.config)
            self._setup_schedule_sync()
            QMessageBox.information(self, "成功", "定时同步设置已保存")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Node Catalog Application')
    
    # 添加 --config 参数，默认值为 /etc/nodcat/config.json
    parser.add_argument('--config', 
                        default='~/.config/nodcat/config.json',
                        help='Path to config file (default: ~/.config/nodcat/config.json)')
    
    # 解析参数
    args = parser.parse_args()
    
    # 打印调试信息（可选）
    print(f"Loading config from: {args.config}")

    config.CONFIG_FILE=args.config;
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    
    ex = FTPSyncApp()    
    ex.show()
    
    sys.exit(app.exec_())