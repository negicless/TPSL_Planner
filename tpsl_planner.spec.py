# tpsl_planner.spec
# Run with: pyinstaller tpsl_planner.spec

import sys, os
from PyInstaller.utils.hooks import collect_all

# Collect PyQt5 + matplotlib fully
pyqt5_datas, pyqt5_binaries, pyqt5_hiddenimports = collect_all('PyQt5')
mpl_datas,  mpl_binaries,  mpl_hiddenimports  = collect_all('matplotlib')

assets = [
    ('tpsl_planner/assets', 'assets'),  # pack into ./assets at runtime
]

a = Analysis(
    ['tpsl_planner/__main__.py'],
    pathex=[],
    binaries=pyqt5_binaries + mpl_binaries,
    datas=pyqt5_datas + mpl_datas + assets,
    hiddenimports=pyqt5_hiddenimports + mpl_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='tpsl_planner',
    icon='tpsl_planner/assets/icons/app.ico',
    console=False,   # no console window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='tpsl_planner'
)
