# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['build/protected_source/python_prototype/ui/main.py'],
    pathex=['build/protected_source/python_prototype'],
    binaries=[],
    datas=[
        ('assets', 'assets'), 
        ('build/protected_source/python_prototype', 'python_prototype'),
        ('build/protected_source/pyarmor_runtime_000000', 'pyarmor_runtime_000000')
    ],
    hiddenimports=['sqlite3', 'json', 'math', 'time', 'random', 'PIL', 'pygame'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Cardflow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/images/cardflow_logo.ico',
)
