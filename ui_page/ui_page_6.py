# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_6.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QPushButton, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_page_6(object):
    def setupUi(self, page_6):
        if not page_6.objectName():
            page_6.setObjectName(u"page_6")
        page_6.resize(712, 484)
        self.verticalLayout = QVBoxLayout(page_6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton = QPushButton(page_6)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMinimumSize(QSize(0, 30))
        self.pushButton.setCheckable(False)
        self.pushButton.setAutoDefault(True)

        self.horizontalLayout.addWidget(self.pushButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.textEdit = QTextEdit(page_6)
        self.textEdit.setObjectName(u"textEdit")

        self.verticalLayout.addWidget(self.textEdit)


        self.retranslateUi(page_6)

        self.pushButton.setDefault(True)


        QMetaObject.connectSlotsByName(page_6)
    # setupUi

    def retranslateUi(self, page_6):
        page_6.setWindowTitle(QCoreApplication.translate("page_6", u"Form", None))
        self.pushButton.setText(QCoreApplication.translate("page_6", u"\u5bfc\u51fa\u8d28\u91cf\u8bc4\u4f30\u62a5\u544a", None))
    # retranslateUi

