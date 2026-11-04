#!/bin/bash
# ============================================================
# Vox-Pack — fabrication des images de l'application
# ------------------------------------------------------------
# Les dessins d'origine sont dans assets/sources/ :
#   bandeau-vox-pack.png   le logo large (en-tête de la fenêtre)
#   icone-vox-pack.png     l'icône carrée (toutes les tailles, sans marge)
#
# (Le monogramme VP de icone-petite.png ne sert plus : l'icône a été redessinée
# en version pleine le 16 octobre 2026, lisible même en 16 px.)
#
# Ce script en fabrique :
#   logo.png      le bandeau affiché en haut de l'application
#   icon.png      l'icône carrée en 1024 px (pour le dépôt GitHub)
#   icon.icns     l'icône macOS (Dock, Finder, barre des menus)
#   icon.ico      l'icône Windows (barre des tâches, explorateur)
#
# Le .icns comme le .ico contiennent PLUSIEURS images : le système choisit la
# bonne selon la taille affichée.
#
#
#   ./assets/faire-les-images.sh
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

SOURCES="assets/sources"
BANDEAU="$SOURCES/bandeau-vox-pack.png"
# Le dessin de la v2 (3 novembre 2026) : l'émetteur avec le mot VOX-PACK.
ICONE="$SOURCES/icone-vox-pack-v2.png"
TRAVAIL="/tmp/voxpack-images"
COTE=1024          # côté de l'icône macOS moderne
mkdir -p "$TRAVAIL" icon.iconset

for f in "$BANDEAU" "$ICONE"; do
  [ -f "$f" ] || { echo "Fichier manquant : $f"; exit 1; }
done


echo "1/4  Bandeau de l'en-tête -> logo.png"
# On écrit d'abord dans le dossier temporaire, PUIS on remplace :
# ainsi, une interruption ne peut jamais laisser un fichier abîmé.
sips -s format png "$BANDEAU" --out "$TRAVAIL/logo.png" >/dev/null
cp "$TRAVAIL/logo.png" logo.png
echo "     logo.png ($(sips -g pixelWidth -g pixelHeight logo.png | tail -2 | tr -d ' \n' | sed 's/pixelWidth://;s/pixelHeight:/x/'))"

echo "2/4  Icône carrée -> icon.png (${COTE}x${COTE}) et icon.iconset"
# Pillow pose le dessin sur la grille d'Apple (824 px dans un carré de 1024) :
# sans cette marge, l'icône paraît plus grosse que ses voisines dans le Dock.
if [ -x venv/bin/python ]; then
  venv/bin/python assets/faire-icone.py
else
  echo "     (venv absent : icon.png non refait)"
  exit 1
fi

echo "3/4  Icône macOS -> icon.icns"
# iconutil n'arrive pas à écrire directement sur le volume du projet :
# on fabrique l'icône dans le dossier temporaire, puis on la copie.
iconutil -c icns icon.iconset -o "$TRAVAIL/icon.icns"
cp "$TRAVAIL/icon.icns" icon.icns

echo "4/4  Icône Windows -> icon.ico"
# Windows veut un .ico multi-tailles. Pillow sait y assembler deux dessins
# différents : le monogramme en petit, le détail en grand.
if [ -x venv/bin/python ]; then
  venv/bin/python assets/faire-ico.py
else
  echo "     (venv absent : icon.ico non refait)"
fi

echo
ls -lh logo.png icon.png icon.icns icon.ico 2>/dev/null
