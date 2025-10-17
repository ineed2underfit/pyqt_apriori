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
from PySide6.QtWidgets import (QApplication, QComboBox, QDateTimeEdit, QDoubleSpinBox,
    QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSplitter, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_page_4(object):
    def setupUi(self, page_4):
        if not page_4.objectName():
            page_4.setObjectName(u"page_4")
        page_4.resize(816, 738)
        self.horizontalLayout_2 = QHBoxLayout(page_4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.splitter = QSplitter(page_4)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.verticalLayoutWidget_3 = QWidget(self.splitter)
        self.verticalLayoutWidget_3.setObjectName(u"verticalLayoutWidget_3")
        self.verticalLayout_9 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_6 = QPushButton(self.verticalLayoutWidget_3)
        self.pushButton_6.setObjectName(u"pushButton_6")
        self.pushButton_6.setMinimumSize(QSize(0, 30))
        self.pushButton_6.setAutoDefault(True)

        self.horizontalLayout.addWidget(self.pushButton_6)

        self.pushButton_8 = QPushButton(self.verticalLayoutWidget_3)
        self.pushButton_8.setObjectName(u"pushButton_8")
        self.pushButton_8.setMinimumSize(QSize(0, 30))
        self.pushButton_8.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pushButton_8)


        self.verticalLayout_10.addLayout(self.horizontalLayout)

        self.textEdit_3 = QTextEdit(self.verticalLayoutWidget_3)
        self.textEdit_3.setObjectName(u"textEdit_3")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textEdit_3.sizePolicy().hasHeightForWidth())
        self.textEdit_3.setSizePolicy(sizePolicy)

        self.verticalLayout_10.addWidget(self.textEdit_3)


        self.verticalLayout_9.addLayout(self.verticalLayout_10)

        self.splitter.addWidget(self.verticalLayoutWidget_3)
        self.verticalLayoutWidget_2 = QWidget(self.splitter)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayout_3 = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(self.verticalLayoutWidget_2)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 777, 444))
        self.horizontalLayout_4 = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_8 = QLabel(self.scrollAreaWidgetContents)
        self.label_8.setObjectName(u"label_8")

        self.verticalLayout.addWidget(self.label_8)

        self.dateTimeEdit = QDateTimeEdit(self.scrollAreaWidgetContents)
        self.dateTimeEdit.setObjectName(u"dateTimeEdit")
        self.dateTimeEdit.setMinimumSize(QSize(0, 25))
        self.dateTimeEdit.setDateTime(QDateTime(QDate(2023, 6, 1), QTime(0, 0, 0)))

        self.verticalLayout.addWidget(self.dateTimeEdit)

        self.label_7 = QLabel(self.scrollAreaWidgetContents)
        self.label_7.setObjectName(u"label_7")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.label_7)

        self.comboBox_2 = QComboBox(self.scrollAreaWidgetContents)
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

        self.verticalLayout.addWidget(self.comboBox_2)

        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.comboBox = QComboBox(self.scrollAreaWidgetContents)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.setObjectName(u"comboBox")
        sizePolicy1.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy1)
        self.comboBox.setMinimumSize(QSize(0, 25))
        self.comboBox.setAutoFillBackground(False)
        self.comboBox.setEditable(True)

        self.verticalLayout.addWidget(self.comboBox)

        self.label_2 = QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.doubleSpinBox_3 = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_3.setObjectName(u"doubleSpinBox_3")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_3.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_3.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_3.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_3.setDecimals(4)
        self.doubleSpinBox_3.setSingleStep(0.000200000000000)
        self.doubleSpinBox_3.setValue(58.000000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_3)

        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)

        self.doubleSpinBox_2 = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_2.setObjectName(u"doubleSpinBox_2")
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_2.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_2.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_2.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_2.setFrame(True)
        self.doubleSpinBox_2.setDecimals(4)
        self.doubleSpinBox_2.setSingleStep(0.000200000000000)
        self.doubleSpinBox_2.setValue(1.400000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_2)

        self.label_4 = QLabel(self.scrollAreaWidgetContents)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.doubleSpinBox_6 = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_6.setObjectName(u"doubleSpinBox_6")
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_6.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_6.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_6.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_6.setDecimals(4)
        self.doubleSpinBox_6.setMinimum(0.000000000000000)
        self.doubleSpinBox_6.setSingleStep(0.000200000000000)
        self.doubleSpinBox_6.setValue(11.000000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_6)

        self.label_5 = QLabel(self.scrollAreaWidgetContents)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout.addWidget(self.label_5)

        self.doubleSpinBox_4 = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_4.setObjectName(u"doubleSpinBox_4")
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_4.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_4.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_4.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_4.setDecimals(4)
        self.doubleSpinBox_4.setMaximum(380.000000000000000)
        self.doubleSpinBox_4.setSingleStep(0.000200000000000)
        self.doubleSpinBox_4.setValue(220.000000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_4)

        self.label_6 = QLabel(self.scrollAreaWidgetContents)
        self.label_6.setObjectName(u"label_6")

        self.verticalLayout.addWidget(self.label_6)

        self.doubleSpinBox_5 = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_5.setObjectName(u"doubleSpinBox_5")
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_5.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_5.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_5.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_5.setDecimals(4)
        self.doubleSpinBox_5.setMaximum(5000.000000000000000)
        self.doubleSpinBox_5.setSingleStep(0.000200000000000)
        self.doubleSpinBox_5.setValue(2020.000000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_5)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout_4.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.pushButton_7 = QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_7.setObjectName(u"pushButton_7")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_7.sizePolicy().hasHeightForWidth())
        self.pushButton_7.setSizePolicy(sizePolicy3)
        self.pushButton_7.setMinimumSize(QSize(0, 30))
        self.pushButton_7.setAutoDefault(False)

        self.verticalLayout_4.addWidget(self.pushButton_7)


        self.verticalLayout_2.addLayout(self.verticalLayout_4)

        self.textEdit = QTextEdit(self.scrollAreaWidgetContents)
        self.textEdit.setObjectName(u"textEdit")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.textEdit.sizePolicy().hasHeightForWidth())
        self.textEdit.setSizePolicy(sizePolicy4)

        self.verticalLayout_2.addWidget(self.textEdit)


        self.horizontalLayout_4.addLayout(self.verticalLayout_2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)

        self.splitter.addWidget(self.verticalLayoutWidget_2)

        self.horizontalLayout_2.addWidget(self.splitter)


        self.retranslateUi(page_4)

        self.pushButton_6.setDefault(True)
        self.pushButton_8.setDefault(False)
        self.comboBox.setCurrentIndex(0)
        self.pushButton_7.setDefault(False)


        QMetaObject.connectSlotsByName(page_4)
    # setupUi

    def retranslateUi(self, page_4):
        page_4.setWindowTitle(QCoreApplication.translate("page_4", u"Form", None))
        self.pushButton_6.setText(QCoreApplication.translate("page_4", u"\u5bfc\u5165\u6d4b\u8bd5\u6570\u636e", None))
        self.pushButton_8.setText(QCoreApplication.translate("page_4", u"\u8d28\u91cf\u8bc4\u4f30", None))
        self.label_8.setText(QCoreApplication.translate("page_4", u"\u65f6\u95f4", None))
        self.label_7.setText(QCoreApplication.translate("page_4", u"\u8bbe\u5907\u578b\u53f7", None))
        self.comboBox_2.setItemText(0, QCoreApplication.translate("page_4", u"DEV-001", None))
        self.comboBox_2.setItemText(1, QCoreApplication.translate("page_4", u"DEV-002", None))
        self.comboBox_2.setItemText(2, QCoreApplication.translate("page_4", u"DEV-003", None))
        self.comboBox_2.setItemText(3, QCoreApplication.translate("page_4", u"DEV-004", None))
        self.comboBox_2.setItemText(4, QCoreApplication.translate("page_4", u"DEV-005", None))
        self.comboBox_2.setItemText(5, QCoreApplication.translate("page_4", u"DEV-006", None))
        self.comboBox_2.setItemText(6, QCoreApplication.translate("page_4", u"DEV-007", None))
        self.comboBox_2.setItemText(7, QCoreApplication.translate("page_4", u"DEV-008", None))
        self.comboBox_2.setItemText(8, QCoreApplication.translate("page_4", u"DEV-009", None))
        self.comboBox_2.setItemText(9, QCoreApplication.translate("page_4", u"DEV-010", None))

        self.label.setText(QCoreApplication.translate("page_4", u"\u9009\u62e9\u90e8\u95e8", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("page_4", u"\u751f\u4ea7\u90e8", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("page_4", u"\u7ef4\u4fee\u90e8", None))
        self.comboBox.setItemText(2, QCoreApplication.translate("page_4", u"\u7814\u53d1\u90e8", None))
        self.comboBox.setItemText(3, QCoreApplication.translate("page_4", u"\u8d28\u68c0\u90e8", None))

        self.comboBox.setCurrentText(QCoreApplication.translate("page_4", u"\u751f\u4ea7\u90e8", None))
        self.comboBox.setPlaceholderText(QCoreApplication.translate("page_4", u"\u9009\u62e9\u6240\u5c5e\u90e8\u95e8", None))
        self.label_2.setText(QCoreApplication.translate("page_4", u"\u6e29\u5ea6", None))
        self.label_3.setText(QCoreApplication.translate("page_4", u"\u632f\u52a8", None))
        self.label_4.setText(QCoreApplication.translate("page_4", u"\u6cb9\u538b", None))
        self.label_5.setText(QCoreApplication.translate("page_4", u"\u7535\u538b", None))
        self.label_6.setText(QCoreApplication.translate("page_4", u"\u8f6c\u901f", None))
        self.pushButton_7.setText(QCoreApplication.translate("page_4", u"\u6545\u969c\u6982\u7387\u8bc4\u4f30", None))
        self.textEdit.setMarkdown(QCoreApplication.translate("page_4", u"\u64b8\u7ba1\n"
"\n"
"", None))
    # retranslateUi

