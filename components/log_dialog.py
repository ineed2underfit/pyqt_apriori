from PySide6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QPushButton
from PySide6.QtCore import QSettings, QByteArray

class LogDialog(QDialog):
    def __init__(self, title="过程日志", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)

        # 初始化QSettings
        self.settings = QSettings("MyCompany", "AprioriApp")

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
        self.settings.setValue(f"LogDialog/{self.windowTitle()}/geometry", self.saveGeometry())
        super().closeEvent(event)

    def restore_geometry(self):
        geometry = self.settings.value(f"LogDialog/{self.windowTitle()}/geometry")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)

    def append_log(self, message):
        self.text_edit.appendPlainText(message)
        # 自动滚动到底部
        self.text_edit.verticalScrollBar().setValue(
            self.text_edit.verticalScrollBar().maximum()
        )
