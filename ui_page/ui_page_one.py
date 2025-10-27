# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_one.ui'
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

class Ui_page_one(object):
    def setupUi(self, page_one):
        if not page_one.objectName():
            page_one.setObjectName(u"page_one")
        page_one.resize(727, 580)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(page_one.sizePolicy().hasHeightForWidth())
        page_one.setSizePolicy(sizePolicy)
        page_one.setMinimumSize(QSize(0, 30))
        self.verticalLayout = QVBoxLayout(page_one)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton = QPushButton(page_one)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMinimumSize(QSize(0, 30))
        self.pushButton.setAutoDefault(True)

        self.horizontalLayout.addWidget(self.pushButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.textEdit = QTextEdit(page_one)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setMinimumSize(QSize(0, 60))

        self.verticalLayout.addWidget(self.textEdit)


        self.retranslateUi(page_one)

        self.pushButton.setDefault(True)


        QMetaObject.connectSlotsByName(page_one)
    # setupUi

    def retranslateUi(self, page_one):
        page_one.setWindowTitle(QCoreApplication.translate("page_one", u"Form", None))
        self.pushButton.setText(QCoreApplication.translate("page_one", u"\u5bfc\u5165\u6570\u636e", None))
    # retranslateUi

