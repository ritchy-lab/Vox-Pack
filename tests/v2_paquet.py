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

import json
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

    print("Choix du fichier de mise à jour")
    # Depuis la 2.0.0, deux .zip Mac coexistent. Se fier au « premier .zip »
    # a envoyé la version Intel aux Mac Apple Silicon : on se fie au NOM du
    # fichier, et l'ordre de la liste ne doit plus rien changer.
    zip_mac = {"name": "Vox-Pack.zip"}
    zip_intel = {"name": "Vox-Pack-Intel.zip"}
    setup = {"name": "Vox-Pack-Setup.exe"}
    portable = {"name": "Vox-Pack.exe"}
    vrai_plateforme = voxpack2.sys.platform
    vraie_machine = voxpack2.platform.machine

    def choisir(plateforme, machine, assets):
        voxpack2.sys.platform = plateforme
        voxpack2.platform.machine = lambda: machine
        try:
            return voxpack2.choisir_asset(assets)
        finally:
            voxpack2.sys.platform = vrai_plateforme
            voxpack2.platform.machine = vraie_machine

    verifier("Mac Apple Silicon : le .zip sans « intel », même s'il est après",
             choisir("darwin", "arm64", [zip_intel, zip_mac]) is zip_mac)
    verifier("Mac Intel : le .zip « intel », même s'il est après",
             choisir("darwin", "x86_64", [zip_mac, zip_intel]) is zip_intel)
    verifier("Mac Apple Silicon, seul l'Intel : on le prend quand même",
             choisir("darwin", "arm64", [zip_intel]) is zip_intel)
    verifier("Windows : l'installateur, même si le portable est avant",
             choisir("win32", "AMD64", [portable, setup]) is setup)
    verifier("Windows, pas d'installateur : le portable",
             choisir("win32", "AMD64", [portable]) is portable)
    verifier("un autre système : aucun fichier",
             choisir("linux", "x86_64", [zip_mac]) is None)

    print("Voix : étoile, remplacements et règle d'ajout")
    # Katja n'est plus proposée : l'étoile est sur Tanja, qui reprend son
    # son. Si Katja revenait, l'étoile reviendrait sur elle, sans doubler.
    vraie_voix = list(voxpack2.VOIX["de"])
    verifier("Katja retirée : l'étoile est sur Tanja",
             voxpack2.porte_etoile("de-DE-TanjaNeural"))
    verifier("Katja retirée : pas de seconde étoile",
             not voxpack2.porte_etoile("de-DE-ChristophNeural"))
    try:
        voxpack2.VOIX["de"].insert(
            0, ("de-DE-KatjaNeural", "Katja", "f", "allemagne"))
        verifier("Katja revenue : l'étoile revient à Katja",
                 voxpack2.porte_etoile("de-DE-KatjaNeural")
                 and not voxpack2.porte_etoile("de-DE-TanjaNeural"))
    finally:
        voxpack2.VOIX["de"] = vraie_voix

    # Les quatre noms allemands retirés par Microsoft ont une remplaçante
    # connue : sans elle, un utilisateur de Conrad retomberait sur Tanja.
    verifier("les remplaçantes allemandes sont connues",
             voxpack2.VOIX_REMPLACANTES.get("de-DE-ConradNeural")
             == "de-DE-ChristophNeural"
             and voxpack2.VOIX_REMPLACANTES.get("de-DE-KatjaNeural")
             == "de-DE-TanjaNeural")

    # Un utilisateur de Conrad (retiré) doit retrouver Christoph, le même
    # son, et non Tanja, la première voix du menu.
    class FauxApp:
        langue = "de"
        _reglages = {"voix": {"de": "de-DE-ConradNeural"}}

        class combo_voice:
            choix = ""

            @classmethod
            def configure(cls, **_options):
                pass

            @classmethod
            def set(cls, valeur):
                cls.choix = valeur

        def _maj_marque_voix(self):
            pass

    essai = FauxApp()
    voxpack2.VoxPackApp._remplir_voix(essai)
    verifier("Conrad retiré : son choix suit Christoph",
             "Christoph" in FauxApp.combo_voice.choix,
             FauxApp.combo_voice.choix)

    # Les mémoires des fenêtres doivent survivre à la relecture des
    # réglages : sinon, l'alerte reviendrait à chaque démarrage.
    gardes = voxpack2._reglages_surs(
        {"voix_signalees": ["de-DE-KatjaNeural", 3, ""],
         "voix_ajoutees": ["en-US-EmmaNeural"]})
    verifier("la mémoire des voix signalées est relue",
             gardes.get("voix_signalees") == ["de-DE-KatjaNeural"], gardes)
    verifier("la mémoire des voix ajoutées est relue",
             gardes.get("voix_ajoutees") == ["en-US-EmmaNeural"], gardes)

    class FauxSignal:
        def __init__(self):
            self._reglages = {}
            self.texte = ""

        def _montrer_quand_visible(self, texte, essais):
            self.texte = texte

    # Un renommage ne s'annonce pas : les anciens noms ont une remplaçante,
    # la fenêtre reste fermée.
    faux = FauxSignal()
    renommees = [("de-DE-KatjaNeural", "Katja", "f", "allemagne"),
                 ("de-DE-ConradNeural", "Conrad", "h", "allemagne")]
    voxpack2.VoxPackApp._signaler_voix_retirees(faux, renommees)
    verifier("un renommage reste silencieux", faux.texte == "", faux.texte)

    # Une vraie disparition parle, avec le nom de la voix.
    faux = FauxSignal()
    voxpack2.VoxPackApp._signaler_voix_retirees(
        faux, [("fr-FR-DeniseNeural", "Denise", "f", "france")])
    verifier("une voix perdue est annoncée", "Denise" in faux.texte,
             faux.texte)
    verifier("le texte français parle du service de voix de Microsoft",
             "service de voix de Microsoft"
             in voxpack2.TEXTES["fr"]["msg_voix_retirees_plusieurs"])

    # Un ajout est annoncé, avec le nom de la voix.
    faux = FauxSignal()
    voxpack2.VoxPackApp._signaler_voix_ajoutees(
        faux, [("en-US-EmmaNeural", "Emma", "f", "usa")])
    verifier("une voix ajoutée est annoncée", "Emma" in faux.texte,
             faux.texte)
    verifier("le texte français parle du service de voix de Microsoft",
             "ajoutée par le service de voix de Microsoft"
             in voxpack2.TEXTES["fr"]["msg_voix_ajoutees_une"])

    # La règle d'ajout ne lit aucun attribut de l'application : on peut
    # l'appeler sans instance (None comme « self »).
    dispo = {
        "de-DE-TanjaNeural": ("de-DE", "Female"),      # déjà dans la table
        "de-DE-NinaNeural": ("de-DE", "Female"),       # pays ouvert
        "de-AT-MartaNeural": ("de-AT", "Female"),
        "de-CH-EliasNeural": ("de-CH", "Male"),
        "de-LI-LeaNeural": ("de-LI", "Female"),        # pays non ouvert
        "de-DE-XMultilingualNeural": ("de-DE", "Female"),
        "en-US-AriaNeural": ("en-US", "Female"),       # autre langue
    }
    ajoutees = voxpack2.VoxPackApp._voix_nouvelles(None, "de", dispo)
    verifier("les voix d'un pays non ouvert restent dehors",
             all(entree[0] != "de-LI-LeaNeural" for entree in ajoutees),
             ajoutees)
    verifier("les voix d'une autre langue restent dehors",
             all(entree[0] != "en-US-AriaNeural" for entree in ajoutees))
    verifier("les Multilingue restent dehors",
             all("Multilingual" not in entree[0] for entree in ajoutees))
    verifier("un pays ouvert entre, trié par pays puis prénom",
             ajoutees == [
                 ("de-AT-MartaNeural", "Marta", "f", "autriche"),
                 ("de-CH-EliasNeural", "Elias", "h", "suisse"),
                 ("de-DE-NinaNeural", "Nina", "f", "allemagne")],
             ajoutees)

    # Les trois entrées chinoises sont trois écritures : chacune ne reçoit
    # que ses propres voix. Sans cela, « zh » mélangerait simplifié,
    # traditionnel et cantonais dans les trois menus.
    dispo_zh = {
        "zh-CN-XiaoxiaoNeural": ("zh-CN", "Female"),   # déjà dans la table
        "zh-CN-YunzeNeural": ("zh-CN", "Male"),        # même écriture
        "zh-TW-HsiaoChenNeural": ("zh-TW", "Female"),  # autre écriture
        "zh-HK-HiuGaaiNeural": ("zh-HK", "Female"),
    }
    cn = voxpack2.VoxPackApp._voix_nouvelles(None, "cn", dispo_zh)
    verifier("le chinois simplifié ne prend que le simplifié",
             [entree[0] for entree in cn] == ["zh-CN-YunzeNeural"], cn)
    tw = voxpack2.VoxPackApp._voix_nouvelles(None, "tw", dispo_zh)
    verifier("le chinois traditionnel ne prend que le traditionnel",
             tw == [], tw)

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

    print("Démarrage avec des fichiers abîmés")
    # Trois cas vus en vrai, ou plausibles : une liste réenregistrée par un
    # tableur (Latin-1 et point-virgule), et un réglage « voix » qui n'est
    # pas un dictionnaire. Chacun empêchait la fenêtre de s'ouvrir.
    os.makedirs(voxpack2.DATA_DIR, exist_ok=True)
    liste = os.path.join(voxpack2.DATA_DIR, "liste_fr.csv")
    with open(liste, "wb") as f:
        f.write("reacteur;Moteur armé\n".encode("latin-1"))
    with open(os.path.join(voxpack2.DATA_DIR, "reglages.json"), "w",
              encoding="utf-8") as f:
        json.dump({"langue_ui": "fr", "voix": "fr-DeniseNeural"}, f)
    app = None
    try:
        app = voxpack2.VoxPackApp()
        app.withdraw()
        app.update()
        verifier("une liste Latin-1 n'empêche plus le démarrage", True)
        verifier("le point-virgule du tableur est reconnu",
                 len(app.lignes) == 1 and app.lignes[0]["nom"] == "reacteur",
                 app.lignes[0]["nom"] if app.lignes else "aucune ligne")
        verifier("les accents de la liste sont lisibles",
                 bool(app.lignes) and app.lignes[0]["texte"] == "Moteur armé",
                 app.lignes[0]["texte"] if app.lignes else "")
        # Le 5 novembre, la liste était chargée mais plus dessinée : le
        # canevas restait vide à l'ouverture. On vérifie donc le dessin ici,
        # sur le démarrage lui-même, et sans changer de langue.
        verifier("la liste est dessinée dès l'ouverture",
                 len(app._toile.find_all()) > 0, len(app._toile.find_all()))
        verifier("la zone de défilement est posée",
                 str(app._toile.cget("scrollregion")).strip() != "",
                 app._toile.cget("scrollregion"))
        verifier("un réglage « voix » mal typé est ignoré",
                 isinstance(app._reglages.get("voix", {}), dict),
                 repr(app._reglages.get("voix")))
    except Exception as e:                      # noqa: BLE001
        verifier("une liste Latin-1 n'empêche plus le démarrage", False, repr(e))
    finally:
        if app is not None:
            try:
                app.destroy()
            except Exception:                   # noqa: BLE001
                pass

    print("Écriture des réglages")
    # Un remplacement d'un seul coup : le fichier reste lisible, et aucun
    # temporaire ne traîne à côté.
    reglages = os.path.join(voxpack2.DATA_DIR, "reglages.json")
    voxpack2.ecrire_reglages({"langue_ui": "fr", "allure": 12})
    try:
        with open(reglages, encoding="utf-8") as f:
            relus = json.load(f)
        verifier("les réglages écrits se relisent", relus.get("allure") == 12)
        verifier("aucun temporaire ne reste",
                 not os.path.exists(reglages + ".tmp"))
    except Exception as e:                      # noqa: BLE001
        verifier("les réglages écrits se relisent", False, repr(e))

    print()
    if ECHECS:
        print(f"{len(ECHECS)} échec(s) :", ", ".join(ECHECS))
        return 1
    print("tout est vert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
