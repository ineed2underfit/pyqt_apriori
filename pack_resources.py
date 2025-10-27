# -*- coding: utf-8 -*-
# 用于运行前编译pyside的资源文件和ui文件
import os
import sys
import site
import subprocess
from pathlib import Path

def find_pyside_tool(tool_name):
    """查找 PySide6 工具的路径"""
    # 方法1: 直接尝试命令
    try:
        result = subprocess.run([tool_name, '--help'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return tool_name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # 方法2: 在 site-packages 中查找
    for site_path in site.getsitepackages():
        tool_path = Path(site_path) / 'PySide6' / f'{tool_name}.exe' if os.name == 'nt' else Path(site_path) / 'PySide6' / tool_name
        if tool_path.exists():
            return str(tool_path)
    
    # 方法3: 在 Scripts 目录查找
    scripts_path = Path(sys.executable).parent / 'Scripts' / f'{tool_name}.exe' if os.name == 'nt' else Path(sys.executable).parent / tool_name
    if scripts_path.exists():
        return str(scripts_path)
    
    return None

# 找到site-packages目录
site_packages_path = site.getsitepackages()[-1]
# 找到pyside6的lrelease.exe的路径 - 优先使用 pyside6-lrelease
lrelease_path = find_pyside_tool('pyside6-lrelease') or find_pyside_tool('lrelease')

def run_command(cmd):
    """安全地运行命令"""
    try:
        print(f"执行命令: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 成功: {cmd}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ 失败: {cmd}")
            print(f"错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        return False

# 🌐 编译翻译文件（国际化支持）
if lrelease_path and Path('resource/i18n/zh.ts').exists():
    run_command(f'"{lrelease_path}" -verbose resource/i18n/zh.ts -qm resource/i18n/zh.qm')
else:
    print("⚠️ 跳过翻译文件编译：lrelease 工具未找到或源文件不存在")

# 📦 编译资源文件（.qrc -> _rc.py） 将 .qrc 编译为 resource_rc.py
rcc_tool = find_pyside_tool('pyside6-rcc')
if rcc_tool and Path('resource/resource.qrc').exists():
    run_command(f'"{rcc_tool}" resource/resource.qrc -o resource_rc.py')
else:
    print("⚠️ 跳过资源文件编译：pyside6-rcc 工具未找到或 .qrc 文件不存在")

# 🎨 编译 .ui 文件（UI 设计文件 -> Python 类）
uic_tool = find_pyside_tool('pyside6-uic')
if uic_tool:
    # 处理 ui_page 目录
    if Path('ui_page').exists():
        ui_files = [f for f in os.listdir('ui_page') if f.endswith('.ui')]
        for ui_file in ui_files:
            output = f"ui_page/ui_{ui_file.split('.')[0]}.py"
            run_command(f'"{uic_tool}" ui_page/{ui_file} -o {output}')
    
    # 处理 ui_view 目录
    if Path('ui_view').exists():
        ui_views = [f for f in os.listdir('ui_view') if f.endswith('.ui')]
        for ui_view in ui_views:
            output = f"ui_view/ui_{ui_view.split('.')[0]}.py"
            run_command(f'"{uic_tool}" ui_view/{ui_view} -o {output}')
else:
    print("⚠️ 跳过 UI 文件编译：pyside6-uic 工具未找到")

print("🎉 资源编译完成！")
