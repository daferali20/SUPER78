# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# 1. إعداد مسارات المشروع
project_dir = os.path.dirname(os.path.abspath(__file__))
spx_trader_path = os.path.join(project_dir, 'spx_trader')

# 2. تحقق من وجود المسارات
if not os.path.exists(spx_trader_path):
    raise RuntimeError(f"مسار المشروع غير موجود: {spx_trader_path}")

a = Analysis(
    ['main.py'],
    pathex=[
        project_dir,
        spx_trader_path,
        os.path.join(spx_trader_path, 'core'),
        os.path.join(spx_trader_path, 'utils'),
        os.path.join(spx_trader_path, 'trading'),
    ],
    binaries=[],
    datas=[
        ('data/*.ini', 'data'),
        ('data/trades/*.csv', 'data/trades'),
    ],
    hiddenimports=[
        'ib_insync',
        'configparser',
        'pandas',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SPX_Trader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None
)