import sys
from PySide6.QtCore import QRect, QSize, Qt, QEvent
from PySide6.QtGui import QIcon, QPixmap, QPainter, QLinearGradient, QColor, QBrush, QAction
from PySide6.QtWidgets import QLabel, QMenu, QApplication, QSystemTrayIcon
from qfluentwidgets import FluentWindow, NavigationItemPosition, NavigationDisplayMode
from components.icon import MyIcon
from qfluentwidgets import FluentIcon as FIF
from services import AprioriService
from common.utils import resolve_bayesian_path
from view.pages.page_one import PageOne
from view.pages.page_two import PageTwo
from view.pages.page_3 import Page3
from view.pages.page_4 import Page4
from view.pages.page_5 import Page5
from view.pages.page_6 import Page6
from view.pages.setting_page import SettingInterface
class MainWindow(FluentWindow):
    """ 主界面 """

    def __init__(self):
        super().__init__()

        # 定义共享文件路径
        self.model_pkl_path = resolve_bayesian_path("Bayesian", "models", "final_bn_model.pkl")

        if sys.platform == "darwin":
            self.navigationInterface.panel.setReturnButtonVisible(False)
            self.navigationInterface.panel.topLayout.setContentsMargins(4, 24, 4, 0)
        else:
            self.navigationInterface.setExpandWidth(150)
            try:
                self.navigationInterface.setDisplayMode(NavigationDisplayMode.MENU)
                self.navigationInterface.setMinimumExpandWidth(0)
                if hasattr(self.navigationInterface, "setCollapsible"):
                    self.navigationInterface.setCollapsible(True)
                if hasattr(self.navigationInterface, "panel"):
                    panel = self.navigationInterface.panel
                    panel.setMenuButtonVisible(True)
                    self._override_navigation_event_filter(panel)
            except AttributeError:
                if hasattr(self.navigationInterface, "collapse"):
                    self.navigationInterface.collapse(useAni=False)

        # Service
        self.apriori_service = AprioriService()

        # 子界面
        self.settingInterface = SettingInterface(self)
        self.pageOne = PageOne(self, apriori_service=self.apriori_service)
        self.pageTwo = PageTwo(self, apriori_service=self.apriori_service)
        self.page3 = Page3(self)
        self.page4 = Page4(self)
        self.page5 = Page5(self)
        self.page6 = Page6(self)

        # 数据中心: 用于存储跨页面共享的数据
        self.dataset_path = None
        self.initial_rules_df = None
        self.optimized_rules_df = None

        # 连接信号与槽
        self.pageOne.file_selected.connect(self.on_file_path_changed)
        self.pageOne.dataset_configured.connect(self.on_dataset_configured)
        self.pageTwo.handler.initial_rules_ready.connect(self.on_initial_rules_ready)
        self.pageTwo.handler.optimized_rules_ready.connect(self.on_optimized_rules_ready)

        self.init_navigation()
        self.init_window()
        self.create_tray_icon()

    def _override_navigation_event_filter(self, panel):
        """Prevent navigation panel from auto collapse on resize or mouse release."""
        original_filter = panel.eventFilter

        def custom_filter(p, obj, event):
            if obj is p.window() and event.type() in (QEvent.MouseButtonRelease, QEvent.Resize):
                return False
            return original_filter(obj, event)

        panel.eventFilter = custom_filter.__get__(panel, type(panel))
        if panel.window():
            panel.window().removeEventFilter(panel)
            panel.window().installEventFilter(panel)

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(":/resource/images/army_icon.png"))

        tray_menu = QMenu(self)
        show_action = QAction("显示", self)
        quit_action = QAction("退出", self)

        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def systemTitleBarRect(self, size):
        return QRect(0, 0, 75, size.height())

    def init_navigation(self):
        sub_interface_list = [

            {'widget': self.pageOne, 'icon': MyIcon.IMPORT, 'text': '数据导入'},
            {'widget': self.pageTwo, 'icon': MyIcon.EXTRACTION, 'text': '规则挖掘'},
            {'widget': self.page3, 'icon': MyIcon.BRANCH, 'text': '贝叶斯网络'},
            {'widget': self.page4, 'icon': MyIcon.EXCEL, 'text': '质量评价'},
            {'widget': self.page5, 'icon': MyIcon.MAGNIFY, 'text': '历史查询'},
            {'widget': self.page6, 'icon': MyIcon.SAVE, 'text': '报告生成'}
        ]
        for item in sub_interface_list:
            self.addSubInterface(item['widget'], item['icon'], item['text'])
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)

    def init_window(self):
        if sys.platform != "darwin":
            self.setWindowIcon(QIcon(':/resource/images/army_icon.png'))
            self.setWindowTitle('装备使用质量评价系统')
        self.resize(1000, 800)
        self.move((self.screen().size().width() - self.width()) / 2,
                  (self.screen().size().height() - self.height()) / 2)

    def on_file_path_changed(self, path):
        """处理文件路径变化"""
        self.dataset_path = path  # 保存原始数据集路径
        self.pageTwo.set_dataset_path(path)
        if hasattr(self, "page3"):
            self.page3.set_dataset_path(path)

    def on_dataset_configured(self, info):
        self.dataset_config_info = info
        self.pageTwo.set_dataset_config_info(info)

    def on_initial_rules_ready(self, df):
        """接收并存储初始规则"""
        print(f"主窗口已接收到 {len(df)} 条初始规则。")
        self.initial_rules_df = df

    def on_optimized_rules_ready(self, df):
        """接收并存储优化后的规则"""
        print(f"主窗口已接收到 {len(df)} 条优化后规则。")
        self.optimized_rules_df = df
