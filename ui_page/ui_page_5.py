# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_5.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QPushButton,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget)

class Ui_page_5(object):
    def setupUi(self, page_5):
        if not page_5.objectName():
            page_5.setObjectName(u"page_5")
        page_5.resize(712, 484)
        self.verticalLayout = QVBoxLayout(page_5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.comboBox_2 = QComboBox(page_5)
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.setObjectName(u"comboBox_2")
        self.comboBox_2.setMinimumSize(QSize(0, 25))
        self.comboBox_2.setEditable(True)

        self.horizontalLayout.addWidget(self.comboBox_2)

        self.pushButton_2 = QPushButton(page_5)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setMinimumSize(QSize(0, 30))
        self.pushButton_2.setCheckable(False)
        self.pushButton_2.setAutoDefault(True)

        self.horizontalLayout.addWidget(self.pushButton_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.textEdit = QTextEdit(page_5)
        self.textEdit.setObjectName(u"textEdit")

        self.verticalLayout.addWidget(self.textEdit)


        self.retranslateUi(page_5)

        self.pushButton_2.setDefault(True)


        QMetaObject.connectSlotsByName(page_5)
    # setupUi

    def retranslateUi(self, page_5):
        page_5.setWindowTitle(QCoreApplication.translate("page_5", u"Form", None))
        self.comboBox_2.setItemText(0, QCoreApplication.translate("page_5", u"DEV-001", None))
        self.comboBox_2.setItemText(1, QCoreApplication.translate("page_5", u"DEV-002", None))
        self.comboBox_2.setItemText(2, QCoreApplication.translate("page_5", u"DEV-003", None))
        self.comboBox_2.setItemText(3, QCoreApplication.translate("page_5", u"DEV-004", None))
        self.comboBox_2.setItemText(4, QCoreApplication.translate("page_5", u"DEV-005", None))
        self.comboBox_2.setItemText(5, QCoreApplication.translate("page_5", u"DEV-006", None))
        self.comboBox_2.setItemText(6, QCoreApplication.translate("page_5", u"DEV-007", None))
        self.comboBox_2.setItemText(7, QCoreApplication.translate("page_5", u"DEV-008", None))
        self.comboBox_2.setItemText(8, QCoreApplication.translate("page_5", u"DEV-009", None))
        self.comboBox_2.setItemText(9, QCoreApplication.translate("page_5", u"DEV-010", None))

        self.pushButton_2.setText(QCoreApplication.translate("page_5", u"\u67e5\u8be2\u8bbe\u5907\u6545\u969c\u8bb0\u5f55", None))
    # retranslateUi

