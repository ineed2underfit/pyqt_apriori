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
from view.pages.page_5 import Page5
from view.pages.setting_page import SettingInterface
from PySide6.QtWidgets import QLabel
import os


class MainWindow(FluentWindow):
    """ 主界面 """

    def __init__(self):
        super().__init__()

        # 定义共享文件路径
        self.model_pkl_path = os.path.abspath("new_bayesian/pkl/bn_bayesian_model.pkl")

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
        self.page5 = Page5(self)

        # 数据中心: 用于存储跨页面共享的数据
        self.dataset_path = None
        self.initial_rules_df = None
        self.optimized_rules_df = None

        # 连接信号与槽
        self.pageOne.file_selected.connect(self.on_file_path_changed)
        self.pageTwo.handler.initial_rules_ready.connect(self.on_initial_rules_ready)
        self.pageTwo.handler.optimized_rules_ready.connect(self.on_optimized_rules_ready)

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
        # self.background_image = QPixmap("resource/images/China_army.jpg")  # 使用相对路径

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

            {'widget': self.pageOne, 'icon': MyIcon.PAGE_BREAK, 'text': '数据导入'},
            {'widget': self.pageTwo, 'icon': MyIcon.EXTRACTION, 'text': '规则挖掘'},
            {'widget': self.page3, 'icon': MyIcon.EXCEL, 'text': '贝叶斯网络'},
            {'widget': self.page4, 'icon': MyIcon.BRANCH, 'text': '质量评估'},
            {'widget': self.page5, 'icon': MyIcon.PAGE_BREAK, 'text': '历史查询'}
        ]
        for item in sub_interface_list:
            self.addSubInterface(item['widget'], item['icon'], item['text'])
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)

    def init_window(self):
        if sys.platform != "darwin":
            self.setWindowIcon(QIcon(':/resource/images/army_icon.png'))
            self.setWindowTitle('装备质量评估系统')
        self.resize(900, 700)
        self.move((self.screen().size().width() - self.width()) / 2,
                  (self.screen().size().height() - self.height()) / 2)

    def on_file_path_changed(self, path):
        """处理文件路径变化"""
        self.dataset_path = path  # 保存原始数据集路径
        self.pageTwo.set_dataset_path(path)

    def on_initial_rules_ready(self, df):
        """接收并存储初始规则"""
        print(f"主窗口已接收到 {len(df)} 条初始规则。")
        self.initial_rules_df = df

    def on_optimized_rules_ready(self, df):
        """接收并存储优化后的规则"""
        print(f"主窗口已接收到 {len(df)} 条优化后规则。")
        self.optimized_rules_df = df
