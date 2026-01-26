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
    page4_debug_log = ConfigItem("Page4", "debug_log", False, BoolValidator())
    page2_debug_log = ConfigItem("Page2", "debug_log", True, BoolValidator())
    page3_debug_log = ConfigItem("Page3", "debug_log", True, BoolValidator())


YEAR = datetime.datetime.now().year
AUTHOR = "Howard Cheung"
VERSION = '0.0.1'
FEEDBACK_URL = "https://github.com/Cheukfung"

cfg = Config()

# Dynamically determine the path for config.json
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    bundle_dir = os.path.dirname(sys.executable)
    internal_dir = os.path.join(bundle_dir, '_internal')
    os.makedirs(internal_dir, exist_ok=True)
    config_file_path = os.path.join(internal_dir, 'config.json')
else:
    # Running in a normal Python environment
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    internal_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_internal')
    os.makedirs(internal_dir, exist_ok=True)
    project_config = os.path.join(project_root, 'config.json')
    internal_config = os.path.join(internal_dir, 'config.json')
    config_file_path = project_config if os.path.exists(project_config) else internal_config

qconfig.load(config_file_path, cfg)
