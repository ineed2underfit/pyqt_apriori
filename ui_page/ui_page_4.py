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
    QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSplitter,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_page_4(object):
    def setupUi(self, page_4):
        if not page_4.objectName():
            page_4.setObjectName(u"page_4")
        page_4.resize(576, 632)
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
        self.pushButton_import = QPushButton(self.verticalLayoutWidget_3)
        self.pushButton_import.setObjectName(u"pushButton_import")
        self.pushButton_import.setMinimumSize(QSize(0, 30))
        self.pushButton_import.setAutoDefault(True)

        self.horizontalLayout.addWidget(self.pushButton_import)

        self.pushButton_assessment = QPushButton(self.verticalLayoutWidget_3)
        self.pushButton_assessment.setObjectName(u"pushButton_assessment")
        self.pushButton_assessment.setMinimumSize(QSize(0, 30))
        self.pushButton_assessment.setAutoDefault(False)

        self.horizontalLayout.addWidget(self.pushButton_assessment)


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
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 537, 444))
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

        self.comboBox_model = QComboBox(self.scrollAreaWidgetContents)
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.addItem("")
        self.comboBox_model.setObjectName(u"comboBox_model")
        self.comboBox_model.setMinimumSize(QSize(0, 25))
        self.comboBox_model.setEditable(True)

        self.verticalLayout.addWidget(self.comboBox_model)

        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.comboBox_apt = QComboBox(self.scrollAreaWidgetContents)
        self.comboBox_apt.addItem("")
        self.comboBox_apt.addItem("")
        self.comboBox_apt.addItem("")
        self.comboBox_apt.addItem("")
        self.comboBox_apt.setObjectName(u"comboBox_apt")
        sizePolicy1.setHeightForWidth(self.comboBox_apt.sizePolicy().hasHeightForWidth())
        self.comboBox_apt.setSizePolicy(sizePolicy1)
        self.comboBox_apt.setMinimumSize(QSize(0, 25))
        self.comboBox_apt.setAutoFillBackground(False)
        self.comboBox_apt.setEditable(True)

        self.verticalLayout.addWidget(self.comboBox_apt)

        self.label_2 = QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout.addWidget(self.label_2)

        self.doubleSpinBox_temp = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_temp.setObjectName(u"doubleSpinBox_temp")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_temp.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_temp.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_temp.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_temp.setDecimals(4)
        self.doubleSpinBox_temp.setMaximum(299.990000000000009)
        self.doubleSpinBox_temp.setSingleStep(0.000200000000000)
        self.doubleSpinBox_temp.setValue(58.000000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_temp)

        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)

        self.doubleSpinBox_vibration = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_vibration.setObjectName(u"doubleSpinBox_vibration")
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_vibration.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_vibration.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_vibration.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_vibration.setFrame(True)
        self.doubleSpinBox_vibration.setDecimals(4)
        self.doubleSpinBox_vibration.setSingleStep(0.000200000000000)
        self.doubleSpinBox_vibration.setValue(1.400000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_vibration)

        self.label_4 = QLabel(self.scrollAreaWidgetContents)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.doubleSpinBox_oil = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_oil.setObjectName(u"doubleSpinBox_oil")
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_oil.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_oil.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_oil.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_oil.setDecimals(4)
        self.doubleSpinBox_oil.setMinimum(0.000000000000000)
        self.doubleSpinBox_oil.setSingleStep(0.000200000000000)
        self.doubleSpinBox_oil.setValue(11.000000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_oil)

        self.label_5 = QLabel(self.scrollAreaWidgetContents)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout.addWidget(self.label_5)

        self.doubleSpinBox_voltage = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_voltage.setObjectName(u"doubleSpinBox_voltage")
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_voltage.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_voltage.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_voltage.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_voltage.setDecimals(4)
        self.doubleSpinBox_voltage.setMaximum(500.000000000000000)
        self.doubleSpinBox_voltage.setSingleStep(0.000200000000000)
        self.doubleSpinBox_voltage.setValue(220.000000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_voltage)

        self.label_6 = QLabel(self.scrollAreaWidgetContents)
        self.label_6.setObjectName(u"label_6")

        self.verticalLayout.addWidget(self.label_6)

        self.doubleSpinBox_rpm = QDoubleSpinBox(self.scrollAreaWidgetContents)
        self.doubleSpinBox_rpm.setObjectName(u"doubleSpinBox_rpm")
        sizePolicy2.setHeightForWidth(self.doubleSpinBox_rpm.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_rpm.setSizePolicy(sizePolicy2)
        self.doubleSpinBox_rpm.setMinimumSize(QSize(0, 25))
        self.doubleSpinBox_rpm.setDecimals(4)
        self.doubleSpinBox_rpm.setMaximum(6999.000000000000000)
        self.doubleSpinBox_rpm.setSingleStep(0.000200000000000)
        self.doubleSpinBox_rpm.setValue(2020.000000000000000)

        self.verticalLayout.addWidget(self.doubleSpinBox_rpm)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout_4.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.pushButton_solely = QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_solely.setObjectName(u"pushButton_solely")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushButton_solely.sizePolicy().hasHeightForWidth())
        self.pushButton_solely.setSizePolicy(sizePolicy3)
        self.pushButton_solely.setMinimumSize(QSize(0, 30))
        self.pushButton_solely.setAutoDefault(False)

        self.verticalLayout_4.addWidget(self.pushButton_solely)

        self.progressBar = QProgressBar(self.scrollAreaWidgetContents)
        self.progressBar.setObjectName(u"progressBar")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progressBar.setSizePolicy(sizePolicy4)
        self.progressBar.setValue(0)

        self.verticalLayout_4.addWidget(self.progressBar)


        self.verticalLayout_2.addLayout(self.verticalLayout_4)

        self.textEdit_solely = QTextEdit(self.scrollAreaWidgetContents)
        self.textEdit_solely.setObjectName(u"textEdit_solely")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.textEdit_solely.sizePolicy().hasHeightForWidth())
        self.textEdit_solely.setSizePolicy(sizePolicy5)

        self.verticalLayout_2.addWidget(self.textEdit_solely)


        self.horizontalLayout_4.addLayout(self.verticalLayout_2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)

        self.splitter.addWidget(self.verticalLayoutWidget_2)

        self.horizontalLayout_2.addWidget(self.splitter)


        self.retranslateUi(page_4)

        self.pushButton_import.setDefault(True)
        self.pushButton_assessment.setDefault(False)
        self.comboBox_apt.setCurrentIndex(0)
        self.pushButton_solely.setDefault(False)


        QMetaObject.connectSlotsByName(page_4)
    # setupUi

    def retranslateUi(self, page_4):
        page_4.setWindowTitle(QCoreApplication.translate("page_4", u"Form", None))
        self.pushButton_import.setText(QCoreApplication.translate("page_4", u"\u5bfc\u5165\u6d4b\u8bd5\u6570\u636e", None))
        self.pushButton_assessment.setText(QCoreApplication.translate("page_4", u"\u8d28\u91cf\u8bc4\u4f30", None))
        self.label_8.setText(QCoreApplication.translate("page_4", u"\u65f6\u95f4", None))
        self.label_7.setText(QCoreApplication.translate("page_4", u"\u8bbe\u5907\u578b\u53f7", None))
        self.comboBox_model.setItemText(0, QCoreApplication.translate("page_4", u"DEV-001", None))
        self.comboBox_model.setItemText(1, QCoreApplication.translate("page_4", u"DEV-002", None))
        self.comboBox_model.setItemText(2, QCoreApplication.translate("page_4", u"DEV-003", None))
        self.comboBox_model.setItemText(3, QCoreApplication.translate("page_4", u"DEV-004", None))
        self.comboBox_model.setItemText(4, QCoreApplication.translate("page_4", u"DEV-005", None))
        self.comboBox_model.setItemText(5, QCoreApplication.translate("page_4", u"DEV-006", None))
        self.comboBox_model.setItemText(6, QCoreApplication.translate("page_4", u"DEV-007", None))
        self.comboBox_model.setItemText(7, QCoreApplication.translate("page_4", u"DEV-008", None))
        self.comboBox_model.setItemText(8, QCoreApplication.translate("page_4", u"DEV-009", None))
        self.comboBox_model.setItemText(9, QCoreApplication.translate("page_4", u"DEV-010", None))

        self.label.setText(QCoreApplication.translate("page_4", u"\u9009\u62e9\u90e8\u95e8", None))
        self.comboBox_apt.setItemText(0, QCoreApplication.translate("page_4", u"\u751f\u4ea7\u90e8", None))
        self.comboBox_apt.setItemText(1, QCoreApplication.translate("page_4", u"\u7ef4\u4fee\u90e8", None))
        self.comboBox_apt.setItemText(2, QCoreApplication.translate("page_4", u"\u7814\u53d1\u90e8", None))
        self.comboBox_apt.setItemText(3, QCoreApplication.translate("page_4", u"\u8d28\u68c0\u90e8", None))

        self.comboBox_apt.setCurrentText(QCoreApplication.translate("page_4", u"\u751f\u4ea7\u90e8", None))
        self.comboBox_apt.setPlaceholderText(QCoreApplication.translate("page_4", u"\u9009\u62e9\u6240\u5c5e\u90e8\u95e8", None))
        self.label_2.setText(QCoreApplication.translate("page_4", u"\u6e29\u5ea6", None))
        self.label_3.setText(QCoreApplication.translate("page_4", u"\u632f\u52a8", None))
        self.label_4.setText(QCoreApplication.translate("page_4", u"\u6cb9\u538b", None))
        self.label_5.setText(QCoreApplication.translate("page_4", u"\u7535\u538b", None))
        self.label_6.setText(QCoreApplication.translate("page_4", u"\u8f6c\u901f", None))
        self.pushButton_solely.setText(QCoreApplication.translate("page_4", u"\u6545\u969c\u6982\u7387\u8bc4\u4f30", None))
        self.textEdit_solely.setMarkdown("")
    # retranslateUi

