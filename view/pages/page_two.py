from PySide6.QtWidgets import QWidget, QLabel
import os
from common.utils import show_dialog
from components.bar import ProgressInfoBar
from ui_page.ui_page_two import Ui_page_two
from view.pages.page_two_handler import PageTwoHandler


# 从ui文件生成的Ui_page_one类继承
class PageTwo(QWidget, Ui_page_two):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading_bar = None
        self.dataset_path = None
        self.setupUi(self)
        # PageOne 创建 Handler 实例并建立双向引用
        self.handler = PageTwoHandler(self)
        self.bind_event()

        # 初始化界面状态
        self.init_ui_state()

    def init_ui_state(self):
        # 设置默认值
        self.doubleSpinBox.setValue(1.2)      # 最小提升度 (lift)
        self.doubleSpinBox_2.setValue(0.005)  # 最小支持度 (support)
        self.doubleSpinBox_3.setValue(0.5)    # 最小置信度 (confidence)
        self.pushButton_2.setEnabled(False)     # 开始挖掘按钮初始禁用
        self.progressBar.setValue(0)            # 重置进度条为0
        self.progressBar.setStyleSheet("")      # 恢复进度条为主题默认颜色

        # 创建并设置数据集标签
        self.label_dataset = QLabel("当前数据集：未选择")
        self.verticalLayout.insertWidget(0, self.label_dataset)

        # 创建并设置状态标签
        self.label_status = QLabel("状态：待命")
        # 将状态标签添加到主垂直布局中
        self.verticalLayout.addWidget(self.label_status)

    def bind_event(self):
        # 绑定开始挖掘按钮
        self.pushButton_2.clicked.connect(self.handler.start_mining)

        # 绑定参数调整的信号
        self.doubleSpinBox.valueChanged.connect(self.handler.on_parameter_changed)
        self.doubleSpinBox_2.valueChanged.connect(self.handler.on_parameter_changed)
        self.doubleSpinBox_3.valueChanged.connect(self.handler.on_parameter_changed)

    def set_dataset_path(self, path):
        """设置数据集路径并更新UI状态"""
        self.dataset_path = path
        # 更新数据集标签
        self.label_dataset.setText(f"当前数据集：{os.path.basename(path)}")
        # 启用开始挖掘按钮
        self.pushButton_2.setEnabled(True)
        # 清空之前的结果
        self.textEdit_3.clear()

    def update_progress(self, progress, message):
        """更新进度条"""
        self.progressBar.setValue(progress)
        if message:
            self.label_status.setText(message)

    def show_state_tooltip(self, title, content):
        self.loading_bar = ProgressInfoBar(title, content, self)
        self.loading_bar.show()

    def close_state_tooltip(self):
        if self.loading_bar:
            self.loading_bar.hide()
            self.loading_bar = None

    def on_common_error(self, msg):
        show_dialog(self, msg, '错误')
