# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_3.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
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
from PySide6.QtWidgets import (QApplication, QPushButton, QSizePolicy, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_page_3(object):
    def setupUi(self, page_3):
        if not page_3.objectName():
            page_3.setObjectName(u"page_3")
        page_3.resize(712, 484)
        self.verticalLayout = QVBoxLayout(page_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pushButton_2 = QPushButton(page_3)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setMinimumSize(QSize(0, 30))
        self.pushButton_2.setCheckable(False)
        self.pushButton_2.setAutoDefault(True)

        self.verticalLayout.addWidget(self.pushButton_2)

        self.textEdit = QTextEdit(page_3)
        self.textEdit.setObjectName(u"textEdit")

        self.verticalLayout.addWidget(self.textEdit)


        self.retranslateUi(page_3)

        self.pushButton_2.setDefault(True)


        QMetaObject.connectSlotsByName(page_3)
    # setupUi

    def retranslateUi(self, page_3):
        page_3.setWindowTitle(QCoreApplication.translate("page_3", u"Form", None))
        self.pushButton_2.setText(QCoreApplication.translate("page_3", u"\u6784\u5efa\u8d1d\u53f6\u65af\u7f51\u7edc", None))
    # retranslateUi

