from PySide6.QtWidgets import QWidget
from common.utils import show_dialog

from ui_page.ui_page_6 import Ui_page_6  # 替换为你的UI文件
from view.pages.page_6_handler import Page6Handler
from components.bar import ProgressInfoBar




# 或者完全不绑定任何事件，按钮点击不会有任何反应

class Page6(QWidget, Ui_page_6):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading_bar = None
        self.setupUi(self)
        # PageOne 创建 Handler 实例并建立双向引用
        self.handler = Page6Handler(self)
        self.bind_event()

    def bind_event(self):
        # 绑定生成报告按钮
        self.pushButton.clicked.connect(self.handler.generate_report)

    def show_state_tooltip(self, title, content):
        self.loading_bar = ProgressInfoBar(title, content, self)
        self.loading_bar.show()

    def close_state_tooltip(self):
        if self.loading_bar:
            self.loading_bar.hide()
            self.loading_bar = None

    def on_common_error(self, msg):
        show_dialog(self, msg, '提示')
