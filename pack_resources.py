# -*- coding: utf-8 -*-
# 用于运行前编译pyside的资源文件和ui文件
import os
import site

# 找到site-packages目录
site_packages_path = site.getsitepackages()[-1]
# 找到pyside6的lrelease.exe的路径
lr = 'lrelease.exe' if os.name == 'nt' else 'lrelease'
lrelease_path = os.path.join(site_packages_path, 'PySide6', lr)

# 🌐 编译翻译文件（国际化支持）
os.system(f'{lrelease_path} -verbose resource/i18n/zh.ts -qm resource/i18n/zh.qm')  # 编译翻译文件

# 📦 编译资源文件（.qrc -> _rc.py） 将 .qrc 编译为 resource_rc.py
os.system("pyside6-rcc resource/resource.qrc -o resource_rc.py")  # 编译资源文件

# 🎨 编译 .ui 文件（UI 设计文件 -> Python 类）
ui_files = os.listdir('ui_page')
ui_views = os.listdir('ui_view')
for ui_view in ui_views:
    if ui_view.endswith('.ui'):
        output = f"ui_view/ui_{ui_view.split('.')[0]}.py"
        os.system(f"pyside6-uic ui_view/{ui_view} -o {output}")  # 编译ui文件
for ui_file in ui_files:
    if ui_file.endswith('.ui'):
        output = f"ui_page/ui_{ui_file.split('.')[0]}.py"
        os.system(f"pyside6-uic ui_page/{ui_file} -o {output}")  # 编译ui文件
        # if os.name != 'nt':
        #     remove_setfont_from_ui(output,output)
