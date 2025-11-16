from PySide6.QtWidgets import QWidget, QLabel
import os
from common.utils import show_dialog
from components.bar import ProgressInfoBar
from ui_page.ui_page_two import Ui_page_two
from view.pages.page_two_handler import PageTwoHandler


# 从ui文件生成的Ui_page_one类继承
class PageTwo(QWidget, Ui_page_two):

    def __init__(self, parent=None, apriori_service=None):
        super().__init__(parent)
        self.loading_bar = None
        self.dataset_path = None
        self.dataset_config_info = None
        self.apriori_service = apriori_service
        self.setupUi(self)
        self.handler = PageTwoHandler(self, apriori_service=apriori_service)
        self.bind_event()

        # 初始化界面状态
        self.init_ui_state()

    def init_ui_state(self):
        # 设置默认值
        self.doubleSpinBox_lift.setValue(1.2)      # 最小提升度 (lift)
        self.doubleSpinBox_support.setValue(0.005)  # 最小支持度 (support)
        self.doubleSpinBox_confidence.setValue(0.5)    # 最小置信度 (confidence)
        self.doubleSpinBox_binning.setValue(5)
        self.pushButton_extract.setEnabled(False)     # 开始挖掘按钮初始禁用
        self.progressBar.setValue(0)            # 重置进度条为0

        # 创建并设置数据集标签
        self.label_dataset = QLabel("当前数据集：未选择")
        self.verticalLayout.insertWidget(0, self.label_dataset)

        # 创建并设置状态标签
        self.label_status = QLabel("状态：待命")
        # 将状态标签添加到主垂直布局中
        self.verticalLayout.addWidget(self.label_status)

    def bind_event(self):
        # 绑定开始挖掘按钮
        self.pushButton_extract.clicked.connect(self.handler.start_mining)
        # 绑定参数调整的信号
        self.doubleSpinBox_lift.valueChanged.connect(self.handler.on_parameter_changed)
        self.doubleSpinBox_support.valueChanged.connect(self.handler.on_parameter_changed)
        self.doubleSpinBox_confidence.valueChanged.connect(self.handler.on_parameter_changed)
        self.doubleSpinBox_binning.valueChanged.connect(self.handler.on_parameter_changed)

    def set_dataset_path(self, path):
        """设置数据集路径并更新UI状态"""
        self.dataset_path = path
        # 更新数据集标签
        self.label_dataset.setText(f"当前数据集：{os.path.basename(path)}")
        # 启用开始挖掘按钮
        self.pushButton_extract.setEnabled(True)
        # 清空之前的结果
        self.textEdit_3.clear()
        if self.dataset_config_info:
            self._show_dataset_config_summary()

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

    def set_dataset_config_info(self, info: dict):
        self.dataset_config_info = info
        self._show_dataset_config_summary()

    def _show_dataset_config_summary(self):
        if not self.dataset_config_info:
            return
        info = self.dataset_config_info
        numerical = ", ".join(info.get('numerical_cols', [])) or "无"
        categorical = ", ".join(info.get('categorical_cols', [])) or "无"
        html = '<div style="font-size: 10pt; line-height: 1.6; font-family: Arial, sans-serif;">'
        html += '<div style="margin-bottom: 12px; padding: 12px; background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); border-radius: 6px;">'
        html += '<h3 style="margin: 0 0 8px 0; color: #2c3e50;">数据集配置确认</h3>'
        html += f'<p><strong>目标列</strong>: {info.get("target_col", "-")}</p>'
        html += f'<p><strong>正常值</strong>: {info.get("normal_value", "-")}</p>'
        html += f'<p><strong>数值列</strong>: {numerical}</p>'
        html += f'<p><strong>分类列</strong>: {categorical}</p>'
        html += f'<p><strong>规则模式</strong>: {info.get("rule_pattern", "-")}</p>'
        html += '</div>'
        html += '<p style="color:#7f8c8d;">请设置最小支持度/置信度/提升度后，点击“提取语料”开始规则挖掘。</p>'
        html += '</div>'
        self.textEdit_3.setHtml(html)
