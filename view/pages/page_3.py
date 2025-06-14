from PySide6.QtWidgets import QWidget
from ui_page.ui_page_3 import Ui_page_3  # 替换为你的UI文件


class Page3(QWidget, Ui_page_3):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # 暂时不需要 handler 和事件绑定
        # self.handler = YourPageHandler(self)  # 注释掉
        # self.bind_event()  # 注释掉

    # 如果需要简单的占位事件处理，可以直接在这里写
    def on_button_clicked(self):
        print("按钮被点击了")  # 简单的调试输出

    # 或者完全不绑定任何事件，按钮点击不会有任何反应
