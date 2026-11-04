"""Isole un essai des données de l'utilisateur, macOS comme Windows.

L'application lit « ~/Documents/Vox-Pack ». Sous macOS, « ~ » vient de HOME ;
sous Windows, de USERPROFILE. Un essai qui ne règle que HOME écrirait donc
dans les vraies listes de Richard sur son PC — exactement ce qu'on veut
éviter. Ce module règle les deux et rend le dossier temporaire.

À appeler AVANT d'importer voxpack2 : l'application copie et lit ses listes
dès l'import (voir reprendre_ancienne_liste).
"""

import os
import tempfile


def isoler() -> str:
    """Donne à l'essai un dossier personnel vide, et le rend."""
    dossier = tempfile.mkdtemp(prefix="voxpack-essai-")
    os.environ["HOME"] = dossier
    if os.name == "nt":
        os.environ["USERPROFILE"] = dossier
        lecteur, chemin = os.path.splitdrive(dossier)
        os.environ["HOMEDRIVE"] = lecteur
        os.environ["HOMEPATH"] = chemin
    return dossier
