# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_4.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_page_4(object):
    def setupUi(self, page_4):
        if not page_4.objectName():
            page_4.setObjectName(u"page_4")
        page_4.resize(712, 484)
        self.verticalLayout = QVBoxLayout(page_4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pushButton_4 = QPushButton(page_4)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setMinimumSize(QSize(0, 30))
        self.pushButton_4.setAutoDefault(True)

        self.verticalLayout.addWidget(self.pushButton_4)

        self.textEdit = QTextEdit(page_4)
        self.textEdit.setObjectName(u"textEdit")

        self.verticalLayout.addWidget(self.textEdit)

        self.line = QFrame(page_4)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_y = QPushButton(page_4)
        self.pushButton_y.setObjectName(u"pushButton_y")
        self.pushButton_y.setMinimumSize(QSize(0, 30))
        self.pushButton_y.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pushButton_y)

        self.pushButton_n = QPushButton(page_4)
        self.pushButton_n.setObjectName(u"pushButton_n")
        self.pushButton_n.setMinimumSize(QSize(0, 30))

        self.horizontalLayout.addWidget(self.pushButton_n)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_2 = QLabel(page_4)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_2.addWidget(self.label_2)

        self.textEdit_3 = QTextEdit(page_4)
        self.textEdit_3.setObjectName(u"textEdit_3")

        self.verticalLayout_2.addWidget(self.textEdit_3)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label = QLabel(page_4)
        self.label.setObjectName(u"label")

        self.verticalLayout_3.addWidget(self.label)

        self.textEdit_2 = QTextEdit(page_4)
        self.textEdit_2.setObjectName(u"textEdit_2")

        self.verticalLayout_3.addWidget(self.textEdit_2)


        self.horizontalLayout_2.addLayout(self.verticalLayout_3)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(page_4)

        self.pushButton_4.setDefault(True)
        self.pushButton_y.setDefault(False)


        QMetaObject.connectSlotsByName(page_4)
    # setupUi

    def retranslateUi(self, page_4):
        page_4.setWindowTitle(QCoreApplication.translate("page_4", u"Form", None))
        self.pushButton_4.setText(QCoreApplication.translate("page_4", u"\u9009\u62e9\u6570\u636e", None))
        self.pushButton_y.setText(QCoreApplication.translate("page_4", u"\u63a5\u53d7 (y)", None))
        self.pushButton_n.setText(QCoreApplication.translate("page_4", u"\u62d2\u7edd (n)", None))
        self.label_2.setText(QCoreApplication.translate("page_4", u"<html><head/><body><p><span style=\" color:#ffffff;\">\u95ee\u9898\u5e93</span></p></body></html>", None))
        self.label.setText(QCoreApplication.translate("page_4", u"<html><head/><body><p><span style=\" color:#ffffff;\">\u6848\u4f8b\u5e93</span></p></body></html>", None))
    # retranslateUi

