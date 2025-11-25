from enum import Enum
import sys
from pathlib import Path

from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel
from qfluentwidgets import Theme, Dialog, StyleSheetBase, qconfig


class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    WINDOW = "main_window"
    LOGIN = "login_window"
    SETTINGS = "setting_interface"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f":/resource/qss/{theme.value.lower()}/{self.value}.qss"


def show_dialog(parent, content, title='提示', url=None, callback=None):
    w = Dialog(title, content, parent)
    w.contentLabel.setOpenExternalLinks(True)
    if url:
        w.contentLabel.mousePressEvent = lambda e: QDesktopServices.openUrl(url)
    max_height = 400
    if parent:
        max_height = parent.screen().availableGeometry().height() * 0.5
    w.contentLabel.setMaximumHeight(max_height * 0.5)
    # w.contentLabel.setMinimumWidth(240)
    w.windowTitleLabel.hide()
    if not callback:
        w.yesButton.hide()
        w.cancelButton.setText('确定')
        w.buttonLayout.insertWidget(0, QLabel(''))
        w.buttonLayout.setStretch(0, 1)
        w.buttonLayout.setStretch(1, 1)
    if w.exec():
        if callback:
            callback()
    else:
        pass


def set_window_center(window):
    """ set window center """
    qr = window.frameGeometry()
    cp = window.screen().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())


def get_data_directory() -> str:
    """Return the datas directory, handling dev vs PyInstaller environments."""
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
        data_dir = base_dir / "datas"
    else:
        project_root = Path(__file__).resolve().parent.parent
        data_dir = project_root / "Bayesian_1130" / "datas"

    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir)
