# coding:utf-8
import datetime
import os
import sys

from qfluentwidgets import (qconfig, QConfig, ConfigItem, BoolValidator, ColorConfigItem)


class MyQConfig(QConfig):
    # 自定义fluent默认主题颜色
    themeColor = ColorConfigItem("QFluentWidgets", "ThemeColor", '#70d5f3')


class Config(MyQConfig):
    user = ConfigItem("User", "user", '')
    password = ConfigItem("User", "password", '')

    """ Config of application """

    auto_login = ConfigItem("MainWindow", "auto_login", False, BoolValidator())
    save_password = ConfigItem("MainWindow", "save_password", True, BoolValidator())


YEAR = datetime.datetime.now().year
AUTHOR = "Howard Cheung"
VERSION = '0.0.1'
FEEDBACK_URL = "https://github.com/Cheukfung"

cfg = Config()

# Dynamically determine the path for config.json
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    bundle_dir = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

internal_dir = os.path.join(bundle_dir, '_internal')
os.makedirs(internal_dir, exist_ok=True) # Ensure _internal directory exists

config_file_path = os.path.join(internal_dir, 'config.json')

qconfig.load(config_file_path, cfg)
