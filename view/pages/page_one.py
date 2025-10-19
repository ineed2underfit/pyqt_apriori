from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from common.utils import show_dialog
from components.bar import ProgressInfoBar
from ui_page.ui_page_one import Ui_page_one
from view.pages.page_one_handler import PageOneHandler


class PageOne(QWidget, Ui_page_one):
    # 添加文件选择信号
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading_bar = None
        self.setupUi(self)
        # PageOne 创建 Handler 实例并建立双向引用
        self.handler = PageOneHandler(self)
        self.bind_event()

    # 主动功能（绑定相关）：
    def bind_event(self):
        # View 将按钮点击事件委托给 Handler
        self.pushButton.clicked.connect(self.handler.select_file) # 绑定事件
        # self.pushButton_2.clicked.connect(self.handler.handle_case_split) # 绑定事件

    # 被动显示（辅助函数）：
    def show_state_tooltip(self, title, content):
        self.loading_bar = ProgressInfoBar(title, content, self)
        self.loading_bar.show()

    def close_state_tooltip(self):
        if self.loading_bar:
            self.loading_bar.hide()
            self.loading_bar = None

    def on_common_error(self, msg):
        show_dialog(self, msg, '提示')

    def emit_file_selected(self, file_path):
        """发送文件选择信号"""
        self.file_selected.emit(file_path)
