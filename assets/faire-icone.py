# -*- coding: utf-8 -*-
"""Fabrique icon.png et le dossier icon.iconset à partir du dessin de la v2.

Le dessin de Richard (`assets/sources/icone-vox-pack-v3.png`, 539 x 539)
est un carré plein : l'émetteur sur fond noir, sans le mot VOX-PACK. Il est
posé à 1024 px, sans marge. La marge de 824 px de la grille d'Apple faisait
apparaître un contour blanc dans le Dock ; Richard a demandé le plein cadre,
et macOS accepte très bien les grandes icônes.

Windows, lui, n'impose pas de grille : `faire-ico.py` reprend le même dessin
et le fait remplir chaque taille.

    venv/bin/python assets/faire-icone.py

Appelé par assets/faire-les-images.sh.
"""

import os
import sys

from PIL import Image

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(RACINE, "assets", "sources", "icone-vox-pack-v3.png")

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
        print("     (dessin de la v2 manquant : icon.png non refait)")
        return 1

    dessin = carre(Image.open(SOURCE).convert("RGBA"))
    maitre = Image.new("RGBA", (COTE, COTE), (0, 0, 0, 0))
    reduit = dessin.resize((DESSIN, DESSIN), Image.LANCZOS)
    maitre.alpha_composite(reduit, ((COTE - DESSIN) // 2,
                                    (COTE - DESSIN) // 2))
    maitre.save(os.path.join(RACINE, "icon.png"))
    print(f"     icon.png : {COTE} x {COTE}, dessin sur {DESSIN} px "
          "(la grille du Mac)")

    dossier = os.path.join(RACINE, "icon.iconset")
    os.makedirs(dossier, exist_ok=True)
    for nom, taille in ICONSET:
        image = maitre.resize((taille, taille), Image.LANCZOS)
        image.save(os.path.join(dossier, nom))
    print(f"     icon.iconset : {len(ICONSET)} tailles, de 16 à 1024 px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
