# -*- mode: python ; coding: utf-8 -*-

# 打包前请执行 `python pack_resources.py` 以生成最新的 ui_*.py 与 resource_rc.py

block_cipher = None

datas = [
    ('resource', 'resource'),
    ('Bayesian_1130', 'Bayesian_1130'),
    ('config.json', '.'),
]

binaries = []

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = [
    'PySide6.QtNetwork',
    'pandas._libs.tslibs.timedeltas',
] + collect_submodules('mlxtend') + collect_submodules('pgmpy') + collect_submodules('seaborn') + collect_submodules('statsmodels')

a = Analysis(
    ['entry.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt5.sip', 'PyQt5.QtNetwork'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pyqt_apriori',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resource/images/Gartoon-Team-Gartoon-Misc-Stock-New-Meeting-Hands.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pyqt_apriori',
)
