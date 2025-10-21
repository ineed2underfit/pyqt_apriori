# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_two.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QDoubleSpinBox, QGridLayout,
    QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget)

class Ui_page_two(object):
    def setupUi(self, page_two):
        if not page_two.objectName():
            page_two.setObjectName(u"page_two")
        page_two.resize(712, 484)
        self.verticalLayout = QVBoxLayout(page_two)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_2 = QLabel(page_two)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.doubleSpinBox = QDoubleSpinBox(page_two)
        self.doubleSpinBox.setObjectName(u"doubleSpinBox")
        self.doubleSpinBox.setMinimum(0.000000000000000)
        self.doubleSpinBox.setSingleStep(0.100000000000000)
        self.doubleSpinBox.setValue(1.200000000000000)

        self.gridLayout.addWidget(self.doubleSpinBox, 5, 0, 1, 1)

        self.label_3 = QLabel(page_two)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)

        self.doubleSpinBox_2 = QDoubleSpinBox(page_two)
        self.doubleSpinBox_2.setObjectName(u"doubleSpinBox_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_2.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_2.setSizePolicy(sizePolicy)
        self.doubleSpinBox_2.setWrapping(False)
        self.doubleSpinBox_2.setFrame(True)
        self.doubleSpinBox_2.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.doubleSpinBox_2.setDecimals(4)
        self.doubleSpinBox_2.setMinimum(0.000000000000000)
        self.doubleSpinBox_2.setMaximum(96.989999999999995)
        self.doubleSpinBox_2.setSingleStep(0.001000000000000)
        self.doubleSpinBox_2.setValue(0.005000000000000)

        self.gridLayout.addWidget(self.doubleSpinBox_2, 1, 0, 1, 1)

        self.doubleSpinBox_3 = QDoubleSpinBox(page_two)
        self.doubleSpinBox_3.setObjectName(u"doubleSpinBox_3")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.doubleSpinBox_3.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_3.setSizePolicy(sizePolicy1)
        self.doubleSpinBox_3.setDecimals(4)
        self.doubleSpinBox_3.setSingleStep(0.001000000000000)
        self.doubleSpinBox_3.setValue(0.500000000000000)

        self.gridLayout.addWidget(self.doubleSpinBox_3, 3, 0, 1, 1)

        self.label = QLabel(page_two)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_2 = QPushButton(page_two)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)
        self.pushButton_2.setMinimumSize(QSize(0, 30))
        self.pushButton_2.setAutoDefault(True)

        self.horizontalLayout_2.addWidget(self.pushButton_2)

        self.pushButton = QPushButton(page_two)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(1)
        sizePolicy2.setVerticalStretch(1)
        sizePolicy2.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy2)
        self.pushButton.setAutoDefault(True)

        self.horizontalLayout_2.addWidget(self.pushButton)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 2, 6, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.progressBar = QProgressBar(page_two)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.progressBar.setAutoFillBackground(False)
        self.progressBar.setValue(0)

        self.verticalLayout.addWidget(self.progressBar)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")

        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.textEdit_3 = QTextEdit(page_two)
        self.textEdit_3.setObjectName(u"textEdit_3")

        self.verticalLayout_3.addWidget(self.textEdit_3)


        self.horizontalLayout.addLayout(self.verticalLayout_3)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(page_two)

        self.pushButton_2.setDefault(True)
        self.pushButton.setDefault(False)


        QMetaObject.connectSlotsByName(page_two)
    # setupUi

    def retranslateUi(self, page_two):
        page_two.setWindowTitle(QCoreApplication.translate("page_two", u"Form", None))
        self.label_2.setText(QCoreApplication.translate("page_two", u"\u6700\u5c0f\u7f6e\u4fe1\u5ea6", None))
        self.label_3.setText(QCoreApplication.translate("page_two", u"\u6700\u5c0f\u63d0\u5347\u5ea6", None))
        self.label.setText(QCoreApplication.translate("page_two", u"\u6700\u5c0f\u652f\u6301\u5ea6", None))
        self.pushButton_2.setText(QCoreApplication.translate("page_two", u"\u63d0\u53d6\u8bed\u6599", None))
        self.pushButton.setText(QCoreApplication.translate("page_two", u"\u89c4\u5219\n"
"\u4f18\u5316", None))
    # retranslateUi

