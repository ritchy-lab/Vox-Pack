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
PETITE = os.path.join(RACINE, "assets", "sources", "icone-petite.png")
GRANDE = os.path.join(RACINE, "assets", "sources", "icone-vox-pack.png")

# Le monogramme pour les petites tailles, le détail à partir de 64 px.
MONOGRAMME = (16, 24, 32, 48)
DETAILLE = (64, 128, 256)


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
    if not (os.path.exists(PETITE) and os.path.exists(GRANDE)):
        print("     (dessins manquants : icon.ico non refait)")
        return 1

    petite = Image.open(PETITE).convert("RGBA")
    grande = Image.open(GRANDE).convert("RGBA")

    images = [petite.resize((c, c), Image.LANCZOS) for c in MONOGRAMME]
    images += [grande.resize((c, c), Image.LANCZOS) for c in DETAILLE]
    ecrire_ico(images, os.path.join(RACINE, "icon.ico"))
    print("     icon.ico : monogramme en " + "/".join(map(str, MONOGRAMME))
          + ", détail en " + "/".join(map(str, DETAILLE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
