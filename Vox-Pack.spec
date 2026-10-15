# -*- mode: python ; coding: utf-8 -*-
# ============================================================
# Vox-Pack — recette de compilation (PyInstaller)
#
#   macOS   : ./build.sh          (compile, signe, zippe, vérifie)
#   Windows : pyinstaller Vox-Pack.spec
#             (ou automatiquement par .github/workflows/windows.yml)
#
# Ce fichier est du Python : il s'adapte donc au système sur lequel il tourne.
# ============================================================
import sys

from PyInstaller.utils.hooks import collect_all

# Le logo et les drapeaux du sélecteur de langue doivent voyager avec
# l'application.
datas = [
    ('logo.png', '.'),
    # L'icône de la fenêtre : Windows ne prend pas celle de l'exécutable.
    ('icon.ico', '.'),
    ('icon.png', '.'),
    ('assets/sources/drapeau-fr.png', 'assets/sources'),
    ('assets/sources/drapeau-fr-estompe.png', 'assets/sources'),
    ('assets/sources/drapeau-en.png', 'assets/sources'),
    ('assets/sources/drapeau-en-estompe.png', 'assets/sources'),
]
binaries = []
hiddenimports = []

paquets = ['customtkinter', 'edge_tts']
if sys.platform != 'darwin':
    # Sur macOS, la conversion audio passe par afconvert et la lecture par
    # afplay : rien à embarquer. Ailleurs, tout se fait en Python, et ces
    # bibliothèques traînent des bibliothèques natives (libsndfile, PortAudio)
    # qu'il faut joindre à l'application.
    paquets += ['soundfile', 'soxr', 'sounddevice', 'numpy']

for paquet in paquets:
    try:
        d, b, h = collect_all(paquet)
    except Exception:
        # Un paquet absent ne doit pas faire échouer la compilation : sur
        # macOS, soundfile et compagnie ne sont même pas installés.
        continue
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

if sys.platform == 'darwin':
    # ---------- macOS : une application .app ----------
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
else:
    # ---------- Windows : un seul fichier .exe ----------
    # Un fichier unique est bien plus simple à télécharger et à lancer pour
    # quelqu'un qui veut juste essayer l'application.
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='Vox-Pack',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,      # pas de fenêtre noire derrière l'application
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.ico',
    )
