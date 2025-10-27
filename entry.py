import sys

from PySide6.QtCore import Qt, QTranslator, QLocale
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from common.config import cfg
from common.my_logger import my_logger as logger
from common.utils import show_dialog
from view.login_window.window import LoginWindow
from view.main_window import MainWindow


def main():
    # 将 QApplication 创建移到 main 函数内部
    # 适配缩放比例
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon = QIcon(":/resource/images/army_icon.png")
    app.setWindowIcon(icon)

    # 解决不同地区数字格式问题 (例如 逗号/点 作为小数点)
    # 强制使用 'C' locale (POSIX/standard)
    QLocale.setDefault(QLocale.C)

    font = app.font()
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)  # 解决弹dialog后frameless窗口无法在调整大小
    translator = QTranslator()
    translator.load(":/resource/i18n/zh.qm")
    app.installTranslator(translator)

    if cfg.auto_login.value:
        logger.debug('判断是否登录')
        if True:
            logger.debug('已登录')
            main_window = MainWindow()
            main_window.show()
            return app.exec()

    login_window = LoginWindow()
    if login_window.exec() == LoginWindow.DialogCode.Accepted:
        main_window = MainWindow()
        main_window.show()
        return app.exec()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        show_dialog(parent=None, content='程序出现异常，请尝试重新运行！')


# import sys
#
# from PySide6.QtCore import Qt, QTranslator
# from PySide6.QtGui import QFont
# from PySide6.QtWidgets import QApplication
#
# from common.config import cfg
# from common.my_logger import my_logger as logger
# from common.utils import show_dialog
# from view.login_window.window import LoginWindow
# from view.main_window import MainWindow
#
# # 适配缩放比例
# QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
# app = QApplication(sys.argv)
# font = app.font()
# font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
# app.setFont(font)
# app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings) # 解决弹dialog后frameless窗口无法在调整大小
# translator = QTranslator()
# translator.load(":/resource/i18n/zh.qm")
# app.installTranslator(translator)
#
#
# def main():
#     if cfg.auto_login.value:
#         logger.debug('判断是否登录')
#         if True:
#             logger.debug('已登录')
#             main_window = MainWindow()
#             main_window.show()
#             app.exec()
#             return
#     login_window = LoginWindow()
#     if login_window.exec() == LoginWindow.DialogCode.Accepted:
#         main_window = MainWindow()
#         main_window.show()
#         app.exec()
#
#
# try:
#     main()
# except Exception as e:
#     logger.exception(e)
#     show_dialog(parent=None, content='程序出现异常，请尝试重新运行！')