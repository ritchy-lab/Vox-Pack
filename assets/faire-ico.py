# -*- coding: utf-8 -*-
"""Fabrique l'icône Windows (icon.ico) à partir du dessin de la v2.

Windows attend un fichier .ico contenant plusieurs tailles : il pioche selon
le contexte (barre des tâches, explorateur, liste, grandes icônes).

Pillow ne sait pas assembler plusieurs dessins dans un .ico (son paramètre
append_images est ignoré) : on écrit donc le fichier nous-mêmes. Le format est
simple, et chaque image y est stockée en PNG — ce que Windows comprend depuis
Vista.

Appelé par assets/faire-les-images.sh.
"""

import io
import os
import struct
import sys

from PIL import Image

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Deux dessins : le détaillé (avec le mot) pour les grandes tailles, et
# l'émetteur seul pour les petites (16/24), où le détaillé serait illisible.
GRANDE = os.path.join(RACINE, "assets", "sources", "icone-vox-pack-v2-1024.png")
PETITE = os.path.join(RACINE, "assets", "sources", "icone-vox-pack-v3.png")

# 16/20/24 : le petit dessin. 30 et au-dessus : le dessin détaillé.
TAILLES = (16, 20, 24, 30, 32, 36, 40, 48, 64, 96, 128, 256)
PETITES = (16, 20, 24)


def recadrer(image, respiration=0.0):
    """Rase les bords transparents, sans ajouter de marge.

    Windows n'impose aucune grille : ses applications remplissent leur case.
    On ne garde aucune respiration, pour qu'aucun contour blanc
    n'apparaisse dans la barre des tâches.
    """
    boite = image.getbbox()
    if boite is None:
        return image
    gauche, haut, droite, bas = boite
    cote = max(droite - gauche, bas - haut)
    marge = int(cote * respiration)
    # On recadre au plus juste, puis on remet la copie dans un carré : les
    # icônes doivent être carrées.
    carre = image.crop((gauche, haut, droite, bas))
    cote = max(carre.width, carre.height)
    fond = Image.new("RGBA", (cote, cote), (0, 0, 0, 0))
    fond.alpha_composite(carre, ((cote - carre.width) // 2,
                                 (cote - carre.height) // 2))
    if marge:
        reduit = Image.new("RGBA", (cote - 2 * marge, cote - 2 * marge),
                           (0, 0, 0, 0))
        reduit.alpha_composite(fond.resize(reduit.size, Image.LANCZOS))
        fond = reduit
    return fond


def ecrire_ico(images, chemin):
    """Écrit un .ico multi-tailles : en-tête, répertoire, puis les images."""
    contenus = []
    for image in images:
        tampon = io.BytesIO()
        image.save(tampon, format="PNG")
        contenus.append((image.width, image.height, tampon.getvalue()))

    entete = struct.pack("<HHH", 0, 1, len(contenus))   # 1 = icône
    decalage = 6 + 16 * len(contenus)
    repertoire, donnees = b"", b""
    for largeur, hauteur, contenu in contenus:
        # 256 s'écrit 0 dans un octet ; les autres champs restent neutres.
        repertoire += struct.pack("<BBBBHHII", largeur % 256, hauteur % 256,
                                  0, 0, 1, 32, len(contenu), decalage)
        donnees += contenu
        decalage += len(contenu)

    with open(chemin, "wb") as fichier:
        fichier.write(entete + repertoire + donnees)


def main():
    if not os.path.exists(GRANDE) or not os.path.exists(PETITE):
        print("     (dessins manquants : icon.ico non refait)")
        return 1

    grande = recadrer(Image.open(GRANDE).convert("RGBA"))
    petite = recadrer(Image.open(PETITE).convert("RGBA"))
    images = [(petite if c in PETITES else grande).resize((c, c),
                                                          Image.LANCZOS)
              for c in TAILLES]
    ecrire_ico(images, os.path.join(RACINE, "icon.ico"))
    print("     icon.ico : " + "/".join(map(str, TAILLES))
          + " ; 16/20/24 en petit format, 30+ en détaillé")
    return 0


if __name__ == "__main__":
    sys.exit(main())
