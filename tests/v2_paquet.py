"""L'application est-elle livrable ?

    python tests/v2_paquet.py

Trois choses, sans lancer ni compiler :

1. **La recette compile le bon fichier** : `Vox-Pack.spec` pointe sur
   `voxpack2.py` (et non sur la 1.5.1).
2. **Tout ce que l'application ouvre au démarrage est joint** : la carcasse,
   le bandeau de l'aide, l'image de survol du soutien, les listes de base.
   Un fichier oublié dans la recette ne se voit qu'une fois le paquet
   installé chez quelqu'un — c'est le genre d'erreur qu'on ne veut pas
   découvrir en publication.
3. **L'application démarre sans la carcasse** : le fond uni de secours prend
   le relais, au lieu d'une exception au lancement.
"""

import os
import re
import sys
import tempfile

from PIL import Image

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

# Les données de Richard ne doivent être ni lues ni écrites.
from isolement import isoler  # noqa: E402

isoler()

ECHECS = []


def verifier(nom, condition, detail=""):
    if condition:
        print(f"  ok    {nom}")
    else:
        print(f"  ÉCHEC {nom} {detail}")
        ECHECS.append(nom)


def main() -> int:
    import voxpack2

    spec = open(os.path.join(RACINE, "Vox-Pack.spec"), encoding="utf-8").read()

    print("Recette")
    verifier("la recette compile voxpack2.py",
             re.search(r"Analysis\(\s*\[\s*'voxpack2\.py'", spec) is not None)
    verifier("la recette ne compile plus la 1.5.1",
             "'voxpack.py'" not in spec)

    print("Fichiers joints")
    for nom in ("carcasse.webp", "bandeau-vp2.webp", "ko-fi-survol.png",
                "logo.png", "ko-fi.png", "icon.ico", "icon.png"):
        verifier(nom, os.path.exists(os.path.join(RACINE, nom))
                 and f"('{nom}'" in spec)
    bases = os.path.join(RACINE, "voxpack_data", "listes-base")
    verifier("les listes de base sont jointes",
             "voxpack_data/listes-base" in spec)

    print("Listes de base")
    for code in voxpack2.LANGUES:
        if code in ("fr", "en", "de"):
            continue
        fichier = os.path.join(bases, code + ".csv")
        verifier(f"{code}.csv", os.path.exists(fichier))

    print("Sons système : CSV et dossier SD")
    # On intercepte le téléchargement : aucun réseau, mais on vérifie que
    # chaque langue demande SON fichier et pas le CSV anglais par défaut.
    class Reponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return (
                '"String ID","Source text","Translation","Context",'
                '"Path","Filename"\n'
                '"1","0","Bonjour","","SYSTEM","0000.wav"\n'
            ).encode("utf-8")

    urls = []
    vraie_urlopen = voxpack2.urllib.request.urlopen
    vrai_data_dir = voxpack2.DATA_DIR
    voxpack2.DATA_DIR = tempfile.mkdtemp(prefix="voxpack-paquet-")
    voxpack2.urllib.request.urlopen = (
        lambda url, **options: (urls.append(url), Reponse())[1])
    try:
        for code, csv, dossier in (
                ("ja", "ja-JP", "jp"), ("cs", "cs-CZ", "cz"),
                ("sv", "sv-SE", "se"), ("uk", "uk-UA", "ua-ostap"),
                ("pt", "pt-PT", "pt"), ("da", "da_DK", "da")):
            lignes, dossier_lu, _cache = \
                voxpack2.csv_officiel_sons_systeme(code)
            verifier(f"{code} : le CSV {csv}.csv",
                     urls[-1].endswith(f"/voices/{csv}.csv"), urls[-1])
            verifier(f"{code} : le dossier SOUNDS/{dossier}",
                     dossier_lu == dossier, dossier_lu)
            verifier(f"{code} : la phrase SYSTEM",
                     lignes == [("0000", "Bonjour")], lignes)
    finally:
        voxpack2.urllib.request.urlopen = vraie_urlopen
        voxpack2.DATA_DIR = vrai_data_dir

    print("En-têtes d'import")
    for code in voxpack2.LANGUES:
        entete = voxpack2.TEXTES[code].get("entete_nom", "")
        verifier(f"{code} : {entete!r}",
                 bool(entete)
                 and voxpack2.est_entete([entete, "phrase"]))
    verifier("une ligne de données n'est pas un en-tête",
             not voxpack2.est_entete(["armed", "Motor armed"]))

    print("Démarrage sans carcasse")
    # Deux verrous plutôt qu'un : le chemin (trouver_ressource) ET l'ouverture
    # de l'image (Image.open). Sur un poste où le premier ne suffit pas, le
    # second rend l'absence certaine — et le détail dit ce qui s'est passé.
    vrai_ressource = voxpack2.trouver_ressource
    vrai_open = Image.open
    voxpack2.trouver_ressource = lambda *morceaux: os.path.join(
        "/inexistant", *morceaux)

    def open_absent(*args, **kwargs):
        raise OSError("carcasse absente (simulé par le test)")

    Image.open = open_absent
    app = None
    try:
        app = voxpack2.VoxPackApp()
        app.withdraw()
        app.update()
        verifier("l'application s'ouvre quand même", True)
        verifier("le fond de secours a la taille de la fenêtre",
                 app._fond_image.size == (app._format, app._format),
                 f"({app._fond_image.size})")
        trouvee = getattr(app, "_carcasse", "attribut absent")
        verifier("la carcasse est signalée absente", trouvee is None,
                 f"({trouvee!r})")
    except Exception as e:                      # noqa: BLE001
        verifier("l'application s'ouvre quand même", False, repr(e))
    finally:
        voxpack2.trouver_ressource = vrai_ressource
        Image.open = vrai_open
        if app is not None:
            try:
                app.destroy()
            except Exception:                   # noqa: BLE001
                pass

    print()
    if ECHECS:
        print(f"{len(ECHECS)} échec(s) :", ", ".join(ECHECS))
        return 1
    print("tout est vert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
