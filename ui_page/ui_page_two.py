# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_two.ui'
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
        self.label_confidence = QLabel(page_two)
        self.label_confidence.setObjectName(u"label_confidence")

        self.gridLayout.addWidget(self.label_confidence, 2, 0, 1, 1)

        self.doubleSpinBox_support = QDoubleSpinBox(page_two)
        self.doubleSpinBox_support.setObjectName(u"doubleSpinBox_support")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_support.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_support.setSizePolicy(sizePolicy)
        self.doubleSpinBox_support.setWrapping(False)
        self.doubleSpinBox_support.setFrame(True)
        self.doubleSpinBox_support.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.doubleSpinBox_support.setDecimals(3)
        self.doubleSpinBox_support.setMinimum(0.000000000000000)
        self.doubleSpinBox_support.setMaximum(96.989999999999995)
        self.doubleSpinBox_support.setSingleStep(0.001000000000000)
        self.doubleSpinBox_support.setValue(0.010000000000000)

        self.gridLayout.addWidget(self.doubleSpinBox_support, 1, 0, 1, 1)

        self.doubleSpinBox_confidence = QDoubleSpinBox(page_two)
        self.doubleSpinBox_confidence.setObjectName(u"doubleSpinBox_confidence")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.doubleSpinBox_confidence.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_confidence.setSizePolicy(sizePolicy1)
        self.doubleSpinBox_confidence.setDecimals(3)
        self.doubleSpinBox_confidence.setSingleStep(0.010000000000000)
        self.doubleSpinBox_confidence.setValue(0.550000000000000)

        self.gridLayout.addWidget(self.doubleSpinBox_confidence, 3, 0, 1, 1)

        self.label_support = QLabel(page_two)
        self.label_support.setObjectName(u"label_support")

        self.gridLayout.addWidget(self.label_support, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton_extract = QPushButton(page_two)
        self.pushButton_extract.setObjectName(u"pushButton_extract")
        sizePolicy.setHeightForWidth(self.pushButton_extract.sizePolicy().hasHeightForWidth())
        self.pushButton_extract.setSizePolicy(sizePolicy)
        self.pushButton_extract.setMinimumSize(QSize(0, 30))
        self.pushButton_extract.setAutoDefault(True)

        self.horizontalLayout_2.addWidget(self.pushButton_extract)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 2, 6, 1)

        self.label_lift = QLabel(page_two)
        self.label_lift.setObjectName(u"label_lift")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_lift.sizePolicy().hasHeightForWidth())
        self.label_lift.setSizePolicy(sizePolicy2)

        self.gridLayout.addWidget(self.label_lift, 0, 1, 1, 1)

        self.doubleSpinBox_lift = QDoubleSpinBox(page_two)
        self.doubleSpinBox_lift.setObjectName(u"doubleSpinBox_lift")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.doubleSpinBox_lift.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_lift.setSizePolicy(sizePolicy3)
        self.doubleSpinBox_lift.setMinimumSize(QSize(2, 0))
        self.doubleSpinBox_lift.setMinimum(0.000000000000000)
        self.doubleSpinBox_lift.setSingleStep(0.100000000000000)
        self.doubleSpinBox_lift.setValue(1.200000000000000)

        self.gridLayout.addWidget(self.doubleSpinBox_lift, 1, 1, 1, 1)

        self.doubleSpinBox_binning = QDoubleSpinBox(page_two)
        self.doubleSpinBox_binning.setObjectName(u"doubleSpinBox_binning")
        self.doubleSpinBox_binning.setDecimals(0)
        self.doubleSpinBox_binning.setMaximum(15.000000000000000)
        self.doubleSpinBox_binning.setValue(5.000000000000000)

        self.gridLayout.addWidget(self.doubleSpinBox_binning, 3, 1, 1, 1)

        self.label_binning = QLabel(page_two)
        self.label_binning.setObjectName(u"label_binning")

        self.gridLayout.addWidget(self.label_binning, 2, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.progressBar = QProgressBar(page_two)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.progressBar.setAutoFillBackground(False)
        self.progressBar.setValue(0)

        self.verticalLayout.addWidget(self.progressBar)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.textEdit_3 = QTextEdit(page_two)
        self.textEdit_3.setObjectName(u"textEdit_3")

        self.verticalLayout_3.addWidget(self.textEdit_3)


        self.horizontalLayout.addLayout(self.verticalLayout_3)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(page_two)

        self.pushButton_extract.setDefault(True)


        QMetaObject.connectSlotsByName(page_two)
    # setupUi

    def retranslateUi(self, page_two):
        page_two.setWindowTitle(QCoreApplication.translate("page_two", u"Form", None))
        self.label_confidence.setText(QCoreApplication.translate("page_two", u"\u6700\u5c0f\u7f6e\u4fe1\u5ea6", None))
        self.label_support.setText(QCoreApplication.translate("page_two", u"\u6700\u5c0f\u652f\u6301\u5ea6", None))
        self.pushButton_extract.setText(QCoreApplication.translate("page_two", u"\u63d0\u53d6\u8bed\u6599", None))
        self.label_lift.setText(QCoreApplication.translate("page_two", u"\u6700\u5c0f\u63d0\u5347\u5ea6", None))
        self.label_binning.setText(QCoreApplication.translate("page_two", u"\u5206\u7bb1\u6570\u91cf", None))
    # retranslateUi

