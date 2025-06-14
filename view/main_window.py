import sys
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QLinearGradient, QColor, QBrush
from qfluentwidgets import FluentWindow, NavigationItemPosition
from components.icon import MyIcon
from qfluentwidgets import FluentIcon as FIF
from view.pages.page_one import PageOne
from view.pages.page_two import PageTwo
from view.pages.page_3 import Page3
from view.pages.page_4 import Page4
from view.pages.setting_page import SettingInterface
from PySide6.QtWidgets import QLabel


class MainWindow(FluentWindow):
    """ 主界面 """

    def __init__(self):
        super().__init__()

        if sys.platform == "darwin":
            self.navigationInterface.panel.setReturnButtonVisible(False)
            self.navigationInterface.panel.topLayout.setContentsMargins(4, 24, 4, 0)
        else:
            self.navigationInterface.setExpandWidth(150)

        # 子界面
        self.settingInterface = SettingInterface(self)
        self.pageOne = PageOne(self)
        self.pageTwo = PageTwo(self)
        self.page3 = Page3(self)
        self.page4 = Page4(self)

        self.init_navigation()
        self.init_window()


        # 注释掉背景相关代码
        # 在 __init__ 最后加
        # self.backgroundMask = QLabel(self)
        # self.backgroundMask.resize(self.size())
        # self.backgroundMask.setStyleSheet("background-color: rgba(255, 255, 255, 70);")  # 半透明白
        # self.backgroundMask.lower()  # 保证在最底层，不遮住内容
        # self.resizeEvent = self._resizeEvent  # 确保窗口变化时遮罩也跟着变
        #
        #
        #
        # # 背景图路径（建议使用相对路径）
        # self.background_image = QPixmap(r"E:\PycharmProjects\pyqt_fluent_widgets\my_pyqt_fluent_testability\resource\images\China_army.jpg")

    # 注释掉背景相关方法
    # def _resizeEvent(self, event):
    #         self.backgroundMask.resize(self.size())
    #         super().resizeEvent(event)
    #
    #
    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.Antialiasing)
    #
    #     # 绘制背景图（缩放铺满）
    #     if not self.background_image.isNull():
    #         scaled_pixmap = self.background_image.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    #         painter.drawPixmap(0, 0, scaled_pixmap)
    #
    #     # 添加一个顶部到底部的渐变遮罩（黑色到透明）
    #     gradient = QLinearGradient(0, 0, 0, self.height())
    #     gradient.setColorAt(0.0, QColor(0, 0, 0, 100))  # 顶部偏黑色
    #     gradient.setColorAt(1.0, QColor(0, 0, 0, 30))   # 底部偏透明
    #     painter.fillRect(self.rect(), QBrush(gradient))

    def systemTitleBarRect(self, size):
        return QRect(0, 0, 75, size.height())

    def init_navigation(self):
        sub_interface_list = [

            {'widget': self.pageOne, 'icon': MyIcon.PAGE_BREAK, 'text': '案例分割'},
            {'widget': self.pageTwo, 'icon': MyIcon.EXTRACTION, 'text': '语料提取'},
            {'widget': self.page3, 'icon': MyIcon.EXCEL, 'text': '规则提取'},
            {'widget': self.page4, 'icon': MyIcon.BRANCH, 'text': '智能核查'}
        ]
        for item in sub_interface_list:
            self.addSubInterface(item['widget'], item['icon'], item['text'])
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)

    def init_window(self):
        if sys.platform != "darwin":
            self.setWindowIcon(QIcon(':/resource/images/army_icon.png'))
            self.setWindowTitle('装备测试性核查页面')
        self.resize(900, 700)
        self.move((self.screen().size().width() - self.width()) / 2,
                  (self.screen().size().height() - self.height()) / 2)
