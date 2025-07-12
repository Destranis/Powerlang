# -*- mode: python ; coding: utf-8 -*-

# This is a PyInstaller spec file.
# It gives us detailed control over the build process.

a = Analysis(
    ['powerlang.py'],
    pathex=[],
    binaries=[],
    # Add our other python scripts here so PyInstaller knows about them
    datas=[
        ('database.py', '.'),
        ('tts_handler.py', '.'),
        ('translations.py', '.')
    ],
    hiddenimports=['deepl'], # Keep this for good measure
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Powerlang',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # This is the equivalent of --windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)