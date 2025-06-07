from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTimeEdit, QComboBox,
                            QDialog, QFormLayout)
from PyQt5.QtCore import QTime


class ScheduleConfigDialog(QDialog):
    """定时配置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('定时同步配置')
        self.setGeometry(400, 400, 400, 300)
        
        main_layout = QVBoxLayout()
        
        # 添加表单布局
        self._setup_form_layout(main_layout)
        
        # 添加按钮布局
        self._setup_button_layout(main_layout)
        
        self.setLayout(main_layout)

    def _setup_form_layout(self, parent_layout):
        """设置表单布局"""
        form_layout = QFormLayout()
        
        # 频率选择
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(['每天', '每周', '每月'])
        form_layout.addRow('同步频率:', self.freq_combo)
        
        # 时间选择
        self.time_edit = QTimeEdit()
        self._configure_time_edit()
        form_layout.addRow('同步时间:', self.time_edit)
        
        parent_layout.addLayout(form_layout)

    def _configure_time_edit(self):
        """配置时间编辑控件"""
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setTimeRange(QTime(0, 0), QTime(23, 59))

    def _setup_button_layout(self, parent_layout):
        """设置按钮布局"""
        button_layout = QHBoxLayout()
        
        # 确定按钮
        self.ok_button = QPushButton('确定')
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        # 取消按钮
        self.cancel_button = QPushButton('取消')
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        parent_layout.addLayout(button_layout)

    def get_schedule_interval(self):
        """计算定时器间隔(毫秒)"""
        return 86400000  # 默认每天