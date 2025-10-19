# -*- coding: utf-8 -*-
# 用于运行前编译pyside的资源文件和ui文件
import os
import sys
import site

# 找到site-packages目录
site_packages_path = site.getsitepackages()[-1]

# 找到 PySide6 工具的完整路径
pyside6_path = os.path.join(site_packages_path, 'PySide6')

# 根据操作系统设置可执行文件扩展名
if os.name == 'nt':  # Windows
    lrelease_exe = 'lrelease.exe'
    rcc_exe = 'rcc.exe'
    uic_exe = 'uic.exe'
else:  # Linux/Mac
    lrelease_exe = 'lrelease'
    rcc_exe = 'rcc'
    uic_exe = 'uic'

# 构建完整路径
lrelease_path = os.path.join(pyside6_path, lrelease_exe)
rcc_path = os.path.join(pyside6_path, rcc_exe)
uic_path = os.path.join(pyside6_path, uic_exe)

# 检查 PySide6 是否安装
if not os.path.exists(pyside6_path):
    print("❌ 错误：未找到 PySide6，请先安装：")
    print("   pip install PySide6")
    sys.exit(1)

print(f"✅ 找到 PySide6 路径: {pyside6_path}")

# 🌐 编译翻译文件（国际化支持）
if os.path.exists('resource/i18n/zh.ts'):
    print("\n📝 编译翻译文件...")
    result = os.system(f'"{lrelease_path}" -verbose resource/i18n/zh.ts -qm resource/i18n/zh.qm')
    if result == 0:
        print("✅ 翻译文件编译成功")
    else:
        print("⚠️ 翻译文件编译失败（可能不影响主要功能）")
else:
    print("⚠️ 跳过翻译文件编译（文件不存在）")

# 📦 编译资源文件（.qrc -> _rc.py） 将 .qrc 编译为 resource_rc.py
if os.path.exists('resource/resource.qrc'):
    print("\n📦 编译资源文件...")
    result = os.system(f'"{rcc_path}" resource/resource.qrc -o resource_rc.py')
    if result == 0:
        print("✅ 资源文件编译成功")
    else:
        print("❌ 资源文件编译失败")
else:
    print("⚠️ 跳过资源文件编译（文件不存在）")

# 🎨 编译 .ui 文件（UI 设计文件 -> Python 类）
print("\n🎨 编译 UI 文件...")

# 编译 ui_view 目录
if os.path.exists('ui_view'):
    ui_views = os.listdir('ui_view')
    for ui_view in ui_views:
        if ui_view.endswith('.ui'):
            output = f"ui_view/ui_{ui_view.split('.')[0]}.py"
            print(f"   编译: {ui_view} -> {output}")
            result = os.system(f'"{uic_path}" ui_view/{ui_view} -o {output}')
            if result != 0:
                print(f"   ❌ 编译失败: {ui_view}")

# 编译 ui_page 目录
if os.path.exists('ui_page'):
    ui_files = os.listdir('ui_page')
    compiled_count = 0
    for ui_file in ui_files:
        if ui_file.endswith('.ui'):
            output = f"ui_page/ui_{ui_file.split('.')[0]}.py"
            print(f"   编译: {ui_file} -> {output}")
            result = os.system(f'"{uic_path}" ui_page/{ui_file} -o {output}')
            if result == 0:
                compiled_count += 1
            else:
                print(f"   ❌ 编译失败: {ui_file}")
    print(f"\n✅ UI 文件编译完成，成功编译 {compiled_count} 个文件")

print("\n🎉 所有编译任务完成！")
