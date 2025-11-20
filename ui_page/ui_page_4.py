# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'page_4.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_page_4(object):
    def setupUi(self, page_4):
        if not page_4.objectName():
            page_4.setObjectName(u"page_4")
        page_4.resize(665, 632)
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
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 643, 366))
        self.horizontalLayout_4 = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.pushButton_solely = QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_solely.setObjectName(u"pushButton_solely")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.pushButton_solely.sizePolicy().hasHeightForWidth())
        self.pushButton_solely.setSizePolicy(sizePolicy1)
        self.pushButton_solely.setMinimumSize(QSize(0, 30))
        self.pushButton_solely.setAutoDefault(False)

        self.verticalLayout_4.addWidget(self.pushButton_solely)

        self.progressBar = QProgressBar(self.scrollAreaWidgetContents)
        self.progressBar.setObjectName(u"progressBar")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progressBar.setSizePolicy(sizePolicy2)
        self.progressBar.setValue(0)

        self.verticalLayout_4.addWidget(self.progressBar)


        self.verticalLayout_2.addLayout(self.verticalLayout_4)

        self.textEdit_solely = QTextEdit(self.scrollAreaWidgetContents)
        self.textEdit_solely.setObjectName(u"textEdit_solely")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.textEdit_solely.sizePolicy().hasHeightForWidth())
        self.textEdit_solely.setSizePolicy(sizePolicy3)

        self.verticalLayout_2.addWidget(self.textEdit_solely)


        self.horizontalLayout_4.addLayout(self.verticalLayout_2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)

        self.splitter.addWidget(self.verticalLayoutWidget_2)

        self.horizontalLayout_2.addWidget(self.splitter)


        self.retranslateUi(page_4)

        self.pushButton_import.setDefault(True)
        self.pushButton_assessment.setDefault(False)
        self.pushButton_solely.setDefault(False)


        QMetaObject.connectSlotsByName(page_4)
    # setupUi

    def retranslateUi(self, page_4):
        page_4.setWindowTitle(QCoreApplication.translate("page_4", u"Form", None))
        self.pushButton_import.setText(QCoreApplication.translate("page_4", u"\u5bfc\u5165\u6d4b\u8bd5\u6570\u636e", None))
        self.pushButton_assessment.setText(QCoreApplication.translate("page_4", u"\u6279\u91cf\u8d28\u91cf\u8bc4\u4f30", None))
        self.pushButton_solely.setText(QCoreApplication.translate("page_4", u"\u5355\u6b21\u8d28\u91cf\u8bc4\u4f30", None))
        self.textEdit_solely.setMarkdown("")
    # retranslateUi

