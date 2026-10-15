#!/bin/bash
# ============================================================
# Vox-Pack — fabrication des images de l'application
# ------------------------------------------------------------
# Les dessins d'origine sont dans assets/sources/ :
#   bandeau-vox-pack.png   le logo large (en-tête de la fenêtre)
#   icone-vox-pack.png     l'icône carrée détaillée (grandes tailles)
#   icone-petite.png       le monogramme VP (16 à 64 px : barre des tâches,
#                          petites vues du Finder), où le dessin détaillé
#                          deviendrait une tache illisible
#
# Ce script en fabrique :
#   logo.png      le bandeau affiché en haut de l'application
#   icon.png      l'icône carrée en 1024 px (pour le dépôt GitHub)
#   icon.icns     l'icône macOS (Dock, Finder, barre des menus)
#   icon.ico      l'icône Windows (barre des tâches, explorateur)
#
# Le .icns comme le .ico contiennent PLUSIEURS images : le système choisit la
# bonne selon la taille affichée. C'est ainsi qu'on garde la finesse du dessin
# en grand et la lisibilité du monogramme en petit.
#
#   ./assets/faire-les-images.sh
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

SOURCES="assets/sources"
BANDEAU="$SOURCES/bandeau-vox-pack.png"
ICONE="$SOURCES/icone-vox-pack.png"
ICONE_PETITE="$SOURCES/icone-petite.png"
TRAVAIL="/tmp/voxpack-images"
COTE=1024          # côté de l'icône macOS moderne
mkdir -p "$TRAVAIL" icon.iconset

for f in "$BANDEAU" "$ICONE" "$ICONE_PETITE"; do
  [ -f "$f" ] || { echo "Fichier manquant : $f"; exit 1; }
done

echo "1/4  Bandeau de l'en-tête -> logo.png"
# On écrit d'abord dans le dossier temporaire, PUIS on remplace :
# ainsi, une interruption ne peut jamais laisser un fichier abîmé.
sips -s format png "$BANDEAU" --out "$TRAVAIL/logo.png" >/dev/null
cp "$TRAVAIL/logo.png" logo.png
echo "     logo.png ($(sips -g pixelWidth -g pixelHeight logo.png | tail -2 | tr -d ' \n' | sed 's/pixelWidth://;s/pixelHeight:/x/'))"

echo "2/4  Icône carrée -> icon.png (${COTE}x${COTE})"
sips -s format png -z "$COTE" "$COTE" "$ICONE" --out "$TRAVAIL/icone-$COTE.png" >/dev/null
cp "$TRAVAIL/icone-$COTE.png" icon.png

# Les petites tailles viennent du monogramme, les grandes du dessin détaillé.
# On part des originaux (et non d'un 1024 intermédiaire) pour ne rien perdre.
for taille in 16 32 64; do
  sips -s format png -z "$taille" "$taille" "$ICONE_PETITE" --out "$TRAVAIL/i_${taille}.png" >/dev/null
done
for taille in 128 256 512 1024; do
  sips -s format png -z "$taille" "$taille" "$TRAVAIL/icone-$COTE.png" --out "$TRAVAIL/i_${taille}.png" >/dev/null
done

cp "$TRAVAIL/i_16.png"    icon.iconset/icon_16x16.png
cp "$TRAVAIL/i_32.png"    icon.iconset/icon_16x16@2x.png
cp "$TRAVAIL/i_32.png"    icon.iconset/icon_32x32.png
cp "$TRAVAIL/i_64.png"    icon.iconset/icon_32x32@2x.png
cp "$TRAVAIL/i_128.png"   icon.iconset/icon_128x128.png
cp "$TRAVAIL/i_256.png"   icon.iconset/icon_128x128@2x.png
cp "$TRAVAIL/i_256.png"   icon.iconset/icon_256x256.png
cp "$TRAVAIL/i_512.png"   icon.iconset/icon_256x256@2x.png
cp "$TRAVAIL/i_512.png"   icon.iconset/icon_512x512.png
cp "$TRAVAIL/i_1024.png"  icon.iconset/icon_512x512@2x.png

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
