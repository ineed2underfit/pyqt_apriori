import os
from PySide6.QtWidgets import QWidget, QGraphicsScene, QGraphicsPixmapItem, QLabel
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
        self.datasetLabel = QLabel("当前数据集：未选择", self)
        self.datasetLabel.setObjectName("label_dataset")
        self.verticalLayout.insertWidget(0, self.datasetLabel)

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
        self.pushButton.clicked.connect(self.handler.build_bayesian_network)

    def set_dataset_path(self, path):
        name = os.path.basename(path) if path else "未选择"
        self.datasetLabel.setText(f"当前数据集：{name}")

    def display_images(self, network_path, confusion_path=None):
        """加载贝叶斯网络结构图，第二张图可选"""
        self.original_pixmap1.load(network_path)
        if confusion_path:
            self.original_pixmap2.load(confusion_path)
        else:
            self.original_pixmap2 = QPixmap()

        if self.original_pixmap1.isNull():
            self.on_common_error("加载贝叶斯网络结构图失败，文件可能不存在或已损坏")
            self.pixmap_item1.setPixmap(QPixmap())
            self.pixmap_item2.setPixmap(QPixmap())
            return

        self.update_image_scaling()

    def update_image_scaling(self):
        if self.original_pixmap1.isNull():
            return

        view_width = self.graphicsView.viewport().width()
        scaled_pixmap1 = self.original_pixmap1.scaledToWidth(
            view_width, Qt.TransformationMode.SmoothTransformation
        )
        self.pixmap_item1.setPixmap(scaled_pixmap1)

        if not self.original_pixmap2.isNull():
            scaled_pixmap2 = self.original_pixmap2.scaledToWidth(
                view_width, Qt.TransformationMode.SmoothTransformation
            )
            self.pixmap_item2.setPixmap(scaled_pixmap2)
            self.pixmap_item2.setPos(0, scaled_pixmap1.height() + 10)
        else:
            self.pixmap_item2.setPixmap(QPixmap())

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_image_scaling()

    def update_progress(self, progress, message):
        if hasattr(self, 'progressBar'):
            self.progressBar.setValue(progress)
            if message:
                self.label_status.setText(message) if hasattr(self, 'label_status') else None

    def on_common_error(self, msg):
        show_dialog(self, msg, '提示')
