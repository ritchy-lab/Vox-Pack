# -*- coding: utf-8 -*-
"""Fabrique icon.png et le dossier icon.iconset à partir du dessin de la v2.

Le dessin détaillé fourni par Richard (`icone-vox-pack-v2-1024.png`,
1024 x 1024) fait l'icône du Mac à **toutes** les tailles. Il est plein cadre,
sans la marge de 824 px de la grille d'Apple qui faisait apparaître un contour
blanc dans le Dock. Le Mac ne prend pas le petit dessin 16/24 : il garde ce
dessin détaillé partout.

    venv/bin/python assets/faire-icone.py

Appelé par assets/faire-les-images.sh.
"""

import os
import sys

from PIL import Image

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(RACINE, "assets", "sources", "icone-vox-pack-v2-1024.png")

COTE = 1024        # côté du carré macOS moderne
DESSIN = 1024      # plein cadre : plus de marge blanche (demande de Richard)

# Les fichiers attendus par iconutil, avec leur taille en pixels.
ICONSET = (
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
)


def carre(image):
    """Le dessin dans un carré transparent, sans le déformer.

    La source fait 516 x 512 : quatre pixels de large en trop. On la pose au
    centre d'un carré plutôt que de l'étirer de 0,8 %.
    """
    cote = max(image.width, image.height)
    carre = Image.new("RGBA", (cote, cote), (0, 0, 0, 0))
    carre.alpha_composite(image, ((cote - image.width) // 2,
                                  (cote - image.height) // 2))
    return carre


def main():
    if not os.path.exists(SOURCE):
        print("     (dessin manquant : icon.png non refait)")
        return 1

    dessin = carre(Image.open(SOURCE).convert("RGBA"))
    maitre = Image.new("RGBA", (COTE, COTE), (0, 0, 0, 0))
    reduit = dessin.resize((DESSIN, DESSIN), Image.LANCZOS)
    maitre.alpha_composite(reduit, ((COTE - DESSIN) // 2,
                                    (COTE - DESSIN) // 2))
    maitre.save(os.path.join(RACINE, "icon.png"))
    print(f"     icon.png : {COTE} x {COTE}, dessin détaillé sur {DESSIN} px")

    dossier = os.path.join(RACINE, "icon.iconset")
    os.makedirs(dossier, exist_ok=True)
    for nom, taille in ICONSET:
        image = maitre.resize((taille, taille), Image.LANCZOS)
        image.save(os.path.join(dossier, nom))
    print(f"     icon.iconset : {len(ICONSET)} tailles, "
          "le dessin détaillé partout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
