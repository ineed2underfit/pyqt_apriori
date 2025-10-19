from PySide6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QPushButton
from PySide6.QtCore import QSettings

class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("挖掘过程日志")
        self.setMinimumSize(400, 300)

        # 初始化QSettings
        self.settings = QSettings("PyQtApriori", "AprioriMiner")

        # 布局和控件
        layout = QVBoxLayout(self)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.close_button = QPushButton("关闭")

        layout.addWidget(self.text_edit)
        layout.addWidget(self.close_button)

        # 连接信号
        self.close_button.clicked.connect(self.close)

        # 恢复窗口位置和大小
        self.restore_geometry()

    def closeEvent(self, event):
        # 保存窗口位置和大小
        self.settings.setValue("LogDialog/geometry", self.saveGeometry())
        event.accept()

    def restore_geometry(self):
        geometry = self.settings.value("LogDialog/geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def append_log(self, message):
        self.text_edit.appendPlainText(message)
        # 自动滚动到底部
        self.text_edit.verticalScrollBar().setValue(
            self.text_edit.verticalScrollBar().maximum()
        )
