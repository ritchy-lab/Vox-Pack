# -*- mode: python ; coding: utf-8 -*-
# ============================================================
# Vox-Pack — recette de compilation (PyInstaller)
#   ./build.sh          (recommandé : compile, signe, zippe, vérifie)
# ============================================================
from PyInstaller.utils.hooks import collect_all

# Le logo doit voyager avec l'application.
datas = [('logo.png', '.')]
binaries = []
hiddenimports = []
for paquet in ('customtkinter', 'edge_tts'):
    d, b, h = collect_all(paquet)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ['voxpack.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='Vox-Pack',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX n'est pas installé sur macOS (et déconseillé)
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    # None = architecture de la machine. La version universelle (Intel +
    # Apple Silicon) est impossible : Pillow n'existe pas en binaire
    # universel sur PyPI (ses binaires sont mono-architecture).
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Vox-Pack',
)
app = BUNDLE(
    coll,
    name='Vox-Pack.app',
    icon='icon.icns',
    bundle_identifier='com.ritchy-lab.vox-pack',
    version='1.0',
    info_plist={
        'CFBundleShortVersionString': '1.0',
        'NSHumanReadableCopyright': '© 2026 ritchy-lab',
        'LSMinimumSystemVersion': '11.0',
    },
)
