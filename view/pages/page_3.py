from PySide6.QtWidgets import QWidget, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtCore import Qt
from ui_page.ui_page_3 import Ui_page_3
from view.pages.page_3_handler import PageThreeHandler
from common.utils import show_dialog

class Page3(QWidget, Ui_page_3):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.handler = PageThreeHandler(self)
        
        # 初始化场景和图形项
        self.scene = QGraphicsScene(self)
        self.graphicsView.setScene(self.scene)
        self.pixmap_item1 = QGraphicsPixmapItem()
        self.pixmap_item2 = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item1)
        self.scene.addItem(self.pixmap_item2)
        
        self.original_pixmap1 = QPixmap()
        self.original_pixmap2 = QPixmap()

        self.bind_event()

    def bind_event(self):
        """绑定按钮事件"""
        self.pushButton.clicked.connect(self.handler.build_bayesian_network)

    def display_images(self, image_path1, image_path2):
        """加载原始图片并进行首次缩放"""
        self.original_pixmap1.load(image_path1)
        self.original_pixmap2.load(image_path2)

        if self.original_pixmap1.isNull() or self.original_pixmap2.isNull():
            self.on_common_error("加载图片失败，文件可能不存在或已损坏。")
            self.pixmap_item1.setPixmap(QPixmap()) # 清空图片
            self.pixmap_item2.setPixmap(QPixmap())
            return

        self.update_image_scaling()

    def update_image_scaling(self):
        """根据当前视图宽度，更新图片缩放和位置"""
        if self.original_pixmap1.isNull():
            return

        # 使用视口（viewport）的宽度更精确
        view_width = self.graphicsView.viewport().width()

        # 缩放第一张图
        scaled_pixmap1 = self.original_pixmap1.scaledToWidth(view_width, Qt.TransformationMode.SmoothTransformation)
        self.pixmap_item1.setPixmap(scaled_pixmap1)

        # 缩放第二张图
        scaled_pixmap2 = self.original_pixmap2.scaledToWidth(view_width, Qt.TransformationMode.SmoothTransformation)
        self.pixmap_item2.setPixmap(scaled_pixmap2)

        # 更新第二张图的位置
        self.pixmap_item2.setPos(0, scaled_pixmap1.height() + 10)

    def resizeEvent(self, event: QResizeEvent):
        """重写窗口大小改变事件"""
        super().resizeEvent(event)
        # 当窗口大小改变时，重新缩放图片
        self.update_image_scaling()

    def update_progress(self, progress, message):
        """更新进度条"""
        if hasattr(self, 'progressBar'):
            self.progressBar.setValue(progress)

    def on_common_error(self, msg):
        """通用错误弹窗"""
        show_dialog(self, msg, '提示')
