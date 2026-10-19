#!/bin/bash
# ============================================================
# Vox-Pack — construit Vox-Pack.app et son zip de publication
#   ./build.sh
# ------------------------------------------------------------
# Deux choses que PyInstaller ne fait pas seul :
#  1. il n'arrive pas à signer le paquet : le Finder y pose un attribut
#     com.apple.FinderInfo, et codesign refuse alors de signer. D'où le
#     nettoyage suivi d'une signature explicite.
#  2. sans signature valide, macOS affiche une icône de secours à la place de la
#     vraie icône — et une copie téléchargée peut être signalée « endommagée ».
#
# La compilation se fait dans un dossier temporaire, puis l'app et le zip sont
# recopiés dans dist/ : ça évite que le Finder ou un service de synchronisation
# ne vienne salir le paquet pendant la signature.
# ============================================================
set -e

cd "$(dirname "$0")"
# Le numéro de version vient de version.py : une seule source de vérité,
# partagée avec l'application et la recette PyInstaller.
VERSION=$(grep -o 'VERSION = "[^"]*"' version.py | head -1 | cut -d'"' -f2)
VERSION=${VERSION:-1.3}
NOM="Vox-Pack"

# L'environnement Python du projet. On passe par « python -m PyInstaller »
# plutôt que par la commande pyinstaller : ça marche même si l'environnement
# a été déplacé (les raccourcis gardent l'ancien chemin en mémoire).
PYTHON="./venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="$(command -v python3.11 || command -v python3)"
    echo "Environnement venv/ absent : j'utilise $PYTHON"
    echo "Pour le recréer : python3.11 -m venv venv && venv/bin/python -m pip install -r requirements.txt"
fi

TMP="$(mktemp -d)"
DIST="$TMP/dist"
APP="$DIST/$NOM.app"
ZIP="Vox-Pack-${VERSION}-macOS-arm64.zip"

# On efface le dossier temporaire même si la compilation échoue.
trap 'rm -rf "$TMP"' EXIT

# PyInstaller range son cache dans ~/Library/Application Support/pyinstaller.
# Si cet emplacement n'est pas accessible en écriture (bac à sable, disque en
# lecture seule, session partagée), on le déplace dans le dossier temporaire :
# sinon la compilation s'arrête sur une erreur de permission déroutante.
CACHE_PYI="$HOME/Library/Application Support/pyinstaller"
if ! mkdir -p "$CACHE_PYI" 2>/dev/null || ! touch "$CACHE_PYI/.essai" 2>/dev/null; then
    export PYINSTALLER_CONFIG_DIR="$TMP/pyinstaller"
else
    rm -f "$CACHE_PYI/.essai"
fi

echo "1/5  compilation dans un dossier temporaire…"
"$PYTHON" -m PyInstaller --noconfirm --clean --distpath "$DIST" --workpath "$TMP/build" \
    "$NOM.spec" > /dev/null

echo "2/5  nettoyage des attributs et signature…"
xattr -cr "$APP" 2>/dev/null || true
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP"

echo "3/5  fabrication du zip…"
ditto -c -k --norsrc --noextattr --noacl --keepParent "$APP" "$DIST/$ZIP"

echo "4/5  vérification du zip (comme le fera l'utilisateur)…"
mkdir -p "$TMP/verif"
ditto -x -k "$DIST/$ZIP" "$TMP/verif"
codesign --verify --deep --strict "$TMP/verif/$NOM.app"
rm -rf "$TMP/verif"

echo "5/5  copie des résultats dans dist/…"
mkdir -p dist
rm -rf "dist/$NOM.app"
ditto "$APP" "dist/$NOM.app"
cp "$DIST/$ZIP" "dist/$ZIP"
rm -rf "$TMP"

echo
echo "Terminé : dist/$ZIP"
lipo -info "dist/$NOM.app/Contents/MacOS/$NOM" | sed 's/.*: /architecture : /'
/usr/libexec/PlistBuddy -c "Print :CFBundleIconFile" "dist/$NOM.app/Contents/Info.plist" | sed 's/^/icône : /'
/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "dist/$NOM.app/Contents/Info.plist" | sed 's/^/version : /'
du -sh "dist/$NOM.app" "dist/$ZIP"
