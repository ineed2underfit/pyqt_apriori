from PySide6.QtWidgets import QWidget
from common.utils import show_dialog
from ui_page.ui_page_4 import Ui_page_4
from view.pages.page_4_handler import PageFourHandler

class Page4(QWidget, Ui_page_4):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.handler = PageFourHandler(self)
        self.init_ui_state()
        self.bind_event()

    def init_ui_state(self):
        """初始化界面状态"""
        # 初始时禁用“质量评估”按钮，因为还未选择测试文件
        self.pushButton_assessment.setEnabled(False)

    def bind_event(self):
        """绑定按钮事件到处理器"""
        # “导入测试数据”按钮
        self.pushButton_import.clicked.connect(self.handler.select_test_file)
        # “质量评估”按钮 (批量)
        self.pushButton_assessment.clicked.connect(self.handler.start_batch_assessment)
        # “故障概率评估”按钮 (单次)
        self.pushButton_solely.clicked.connect(self.handler.assess_single_instance)

    def on_common_error(self, msg):
        """通用错误弹窗"""
        show_dialog(self, msg, '错误')

