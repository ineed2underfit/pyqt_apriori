# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_3.ui'
##
## Created by: Qt User Interface Compiler version 6.9.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGraphicsView, QHBoxLayout, QProgressBar,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_page_3(object):
    def setupUi(self, page_3):
        if not page_3.objectName():
            page_3.setObjectName(u"page_3")
        page_3.resize(712, 484)
        self.verticalLayout_2 = QVBoxLayout(page_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton = QPushButton(page_3)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMinimumSize(QSize(0, 30))
        self.pushButton.setCheckable(False)
        self.pushButton.setAutoDefault(True)

        self.horizontalLayout.addWidget(self.pushButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.progressBar = QProgressBar(page_3)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)

        self.verticalLayout.addWidget(self.progressBar)

        self.graphicsView = QGraphicsView(page_3)
        self.graphicsView.setObjectName(u"graphicsView")

        self.verticalLayout.addWidget(self.graphicsView)


        self.verticalLayout_2.addLayout(self.verticalLayout)


        self.retranslateUi(page_3)

        self.pushButton.setDefault(False)


        QMetaObject.connectSlotsByName(page_3)
    # setupUi

    def retranslateUi(self, page_3):
        page_3.setWindowTitle(QCoreApplication.translate("page_3", u"Form", None))
        self.pushButton.setText(QCoreApplication.translate("page_3", u"\u6784\u5efa\u8d1d\u53f6\u65af\u7f51\u7edc", None))
    # retranslateUi

