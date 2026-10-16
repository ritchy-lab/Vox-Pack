# -*- coding: utf-8 -*-
"""Fabrique l'icône Windows (icon.ico) à partir des deux dessins.

Windows attend un fichier .ico contenant plusieurs tailles : il pioche selon
le contexte (barre des tâches, explorateur, liste, grandes icônes). Comme pour
le .icns du Mac, les petites tailles viennent du monogramme VP — le dessin
détaillé y serait une tache — et les grandes du dessin détaillé.

Pillow ne sait pas assembler deux dessins différents dans un .ico (son
paramètre append_images est ignoré) : on écrit donc le fichier nous-mêmes.
Le format est simple, et chaque image y est stockée en PNG — ce que Windows
comprend depuis Vista.

Appelé par assets/faire-les-images.sh.
"""

import io
import os
import struct
import sys

from PIL import Image

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRANDE = os.path.join(RACINE, "assets", "sources", "icone-vox-pack.png")

# Un seul dessin, à toutes les tailles : Richard veut son émetteur partout.
# Le monogramme VP, pourtant plus net en 16 px, a été écarté par Richard — il
# ne veut pas deux icônes selon l'endroit où on regarde.
TAILLES = (16, 24, 32, 48, 64, 128, 256)


def recadrer(image, respiration=0.01):
    """Rase les bords transparents, en gardant à peine 1 % de respiration.

    Windows n'impose aucune grille : ses applications remplissent leur case.
    Le monogramme de Richard n'occupait que 69 % de son image, et le dessin
    détaillé 87 % — une fois posés dans la barre des tâches, ils paraissaient
    plus petits que les autres applications. Sur macOS, la marge est au
    contraire imposée par Apple (toutes les icônes s'alignent sur une grille) :
    elle est donc conservée dans le .icns, et retirée ici.
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
    if not os.path.exists(GRANDE):
        print("     (dessins manquants : icon.ico non refait)")
        return 1

    grande = recadrer(Image.open(GRANDE).convert("RGBA"))
    images = [grande.resize((c, c), Image.LANCZOS) for c in TAILLES]
    ecrire_ico(images, os.path.join(RACINE, "icon.ico"))
    print("     icon.ico : le dessin à toutes les tailles ("
          + "/".join(map(str, TAILLES)) + "), recadré pour remplir sa case")
    return 0


if __name__ == "__main__":
    sys.exit(main())
