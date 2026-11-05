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

from version import VERSION
from PyInstaller.utils.hooks import collect_all

# Le logo et les icônes doivent voyager avec l'application. (Les dessins de
# drapeaux restent dans assets/sources/ : ils ne servent plus depuis qu'il n'y
# a qu'une seule langue.)
datas = [
    ('logo.png', '.'),
    ('ko-fi.png', '.'),
    # La licence et la notice voyagent avec l'application : le code est
    # MIT, mais l'identité visuelle ne l'est pas (voir NOTICE).
    ('LICENSE', '.'),
    ('NOTICE', '.'),
    # L'écran de la v2 : la carcasse dessinée, le bandeau de l'aide et
    # l'image de survol du lien de soutien. Sans elles, l'application
    # s'ouvrirait sur un fond uni (voir _charger_carcasse) : autant les
    # joindre.
    ('carcasse.webp', '.'),
    ('bandeau-vp2.webp', '.'),
    ('ko-fi-survol.png', '.'),
    # L'icône de la fenêtre : Windows ne prend pas celle de l'exécutable.
    ('icon.ico', '.'),
    ('icon.png', '.'),
    # Les données du paquet `voxpack_data` : les modules .py voyagent tout
    # seuls (imports), mais les CSV des listes de départ sont des fichiers.
    ('voxpack_data/listes-base', 'voxpack_data/listes-base'),
]
binaries = []
hiddenimports = []

paquets = ['customtkinter', 'edge_tts']
if sys.platform == 'darwin':
    # PyObjC : le sélecteur de dossier natif (feuille NSOpenPanel) qui parle
    # français, au lieu du sélecteur de Tk qui écrit « Choose » en dur.
    paquets += ['objc', 'AppKit', 'Foundation', 'CoreFoundation']
if sys.platform != 'darwin':
    # Sur macOS, la conversion audio passe par afconvert et la lecture par
    # afplay : rien à embarquer. Ailleurs, tout se fait en Python, et ces
    # bibliothèques traînent des bibliothèques natives (libsndfile, PortAudio)
    # qu'il faut joindre à l'application.
    # Les bibliothèques natives de soundfile (libsndfile) et de sounddevice
    # (PortAudio) sont rangées dans des paquets à part : sans eux, le .exe
    # démarrerait mais échouerait à la première conversion audio.
    paquets += ['soundfile', 'soxr', 'sounddevice', 'numpy',
                '_soundfile_data', '_sounddevice_data']

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
    ['voxpack2.py'],
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

# ------------------------------------------------------------------
# La jauge animée du splash
# ------------------------------------------------------------------
# Le splash de PyInstaller ne sait afficher qu'une image et une ligne de
# texte. Pour avoir la jauge rouge de l'application, on ajoute du Tcl au
# script qu'il exécute : la jauge avance pendant la décompression et une
# ligne d'état défile. Le script est construit par Splash.generate_script :
# on remplace la fonction de template le temps de la compilation.
import PyInstaller.building.splash_templates as _splash_templates

_JAUGE_SPLASH = r"""
font create splashTexte {*}[font actual TkDefaultFont]
font configure splashTexte -size 9
.root.canvas create rectangle 20 184 620 192 -fill "#040B0C" -outline ""
set barreJauge [.root.canvas create rectangle 20 186 20 190 -fill "#FF0D00" -outline ""]
.root.canvas create text 20 232 -anchor sw -fill "#7C959A" -font splashTexte -text "Chargement de Vox-Pack..." -tag texteEtat
set departJauge [clock milliseconds]
set etats [list "Chargement de Vox-Pack..." "Décompression des fichiers..." "Ouverture de l'interface..."]
set numeroEtat 0
proc animerJauge {} {
    global departJauge barreJauge
    set ecoule [expr {[clock milliseconds] - $departJauge}]
    set part [expr {1.0 - exp(-$ecoule / 6500.0)}]
    if {$part > 0.93} { set part 0.93 }
    set x [expr {20.0 + 600.0 * $part}]
    .root.canvas coords $barreJauge 20 186 $x 190
    after 50 animerJauge
}
proc faireDefilerEtat {} {
    global etats numeroEtat
    incr numeroEtat
    if {$numeroEtat >= [llength $etats]} { set numeroEtat 0 }
    .root.canvas itemconfigure texteEtat -text [lindex $etats $numeroEtat]
    after 3000 faireDefilerEtat
}
after 50 animerJauge
after 3000 faireDefilerEtat
"""

_build_script_origine = _splash_templates.build_script


def _build_script_voxpack(text_options=None, always_on_top=False):
    return (_build_script_origine(text_options=None,
                                  always_on_top=always_on_top)
            + "\n" + _JAUGE_SPLASH)


_splash_templates.build_script = _build_script_voxpack

# Windows : un écran de démarrage pendant que PyInstaller décompresse le
# .exe (9 à 14 s sur un PC, voir la passation du 5 novembre). Le splash ne
# raccourcit pas l'attente, mais il la montre : l'application ne paraît plus
# ne pas démarrer. Sur macOS, le .app est déjà un dossier : rien à attendre.
splash = None
if sys.platform != 'darwin':
    splash = Splash(
        'splash.png',
        binaries=a.binaries,
        datas=a.datas,
        always_on_top=True,
    )

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
        version=VERSION,
        info_plist={
            'CFBundleShortVersionString': VERSION,
            'NSHumanReadableCopyright': '© 2026 ritchy-lab',
            'LSMinimumSystemVersion': '11.0',
            # Sans ces deux lignes, les fenêtres fournies par macOS (choix
            # d'un dossier, d'un fichier…) s'affichent en anglais même sur un
            # Mac français : macOS choisit leur langue d'après les langues que
            # l'application déclare, et PyInstaller n'en déclare aucune.
            # C'est le même correctif que Python a appliqué à son propre
            # lanceur (Python.app) en 3.12.
            # Les quinze langues de l'interface : macOS choisit la langue
            # de ses propres fenêtres (dossier, fichier…) d'après cette
            # liste. Les codes suivent ceux de `voxpack_data/langues.py`.
            'CFBundleLocalizations': ['fr', 'en', 'de', 'es', 'it', 'pt',
                                      'ru', 'sv', 'uk', 'cs', 'da', 'ja',
                                      'zh-Hans', 'zh-Hant', 'zh-HK'],
            'CFBundleAllowMixedLocalizations': True,
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
        splash,
        splash.binaries,
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
