from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from common.utils import show_dialog
from components.bar import ProgressInfoBar
from ui_page.ui_page_one import Ui_page_one
from view.pages.page_one_handler import PageOneHandler


class PageOne(QWidget, Ui_page_one):
    file_selected = Signal(str)
    dataset_configured = Signal(dict)

    def __init__(self, parent=None, apriori_service=None):
        super().__init__(parent)
        self.loading_bar = None
        self.setupUi(self)
        self.pushButton_clean.setEnabled(False)
        self.handler = PageOneHandler(self, apriori_service=apriori_service)
        self.bind_event()

    # 主动功能（绑定相关）
    def bind_event(self):
        self.pushButton.clicked.connect(self.handler.select_file)
        if hasattr(self, 'pushButton_clean'):
            self.pushButton_clean.clicked.connect(self.handler.clean_data)

    # 被动显示（辅助函数）
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
        self.file_selected.emit(file_path)

    def emit_dataset_config(self, info: dict):
        self.dataset_configured.emit(info)
