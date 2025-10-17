from PySide6.QtWidgets import QWidget
from common.utils import show_dialog

from ui_page.ui_page_4 import Ui_page_4  # 替换为你的UI文件
from view.pages.page_4_handler import Page4Handler
from components.bar import ProgressInfoBar




    # 或者完全不绑定任何事件，按钮点击不会有任何反应

class Page4(QWidget, Ui_page_4):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading_bar = None
        self.setupUi(self)
        # PageOne 创建 Handler 实例并建立双向引用
        self.handler = Page4Handler(self)
        self.bind_event()

    def bind_event(self):
        # View 将按钮点击事件委托给 Handler
        self.pushButton_6.clicked.connect(self.handler.select_file) # 绑定事件
        self.pushButton_7.clicked.connect(self.handler.show_case_lib_popout) # 绑定事件
        # self.pushButton_n.clicked.connect(self.handler.show_question_lib_confirm_dialog) # 绑定事件

    def show_state_tooltip(self, title, content):
        self.loading_bar = ProgressInfoBar(title, content, self)
        self.loading_bar.show()

    def close_state_tooltip(self):
        if self.loading_bar:
            self.loading_bar.hide()
            self.loading_bar = None

    def on_common_error(self, msg):
        show_dialog(self, msg, '提示')

