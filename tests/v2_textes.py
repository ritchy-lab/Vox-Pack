"""Vérifications de la v2 — les données et les textes, sans interface.

Ces contrôles ne touchent ni à Tk, ni au réseau, ni à l'application
publiée : ils lisent les tables et les fonctions pures. Ils sont donc
utilisables partout, y compris sur la machine Windows du robot.

    python tests/v2_textes.py

Ce qui est vérifié, et pourquoi :

- **les quinze tables de textes ont les mêmes clés** — une clé oubliée
  s'afficherait en anglais au milieu d'un écran japonais ;
- **chaque langue de `langues.py` a sa table de textes**, et l'inverse ;
- **aucun texte n'est vide** — un libellé vide ne se voit pas dans un
  fichier, il se voit à l'écran ;
- **la comparaison de versions est numérique** (`1.10 > 1.9`) ;
- **une liste fait l'aller-retour** CSV → mémoire → CSV sans se déformer ;
- **la table des langues reste cohérente** : pas de dossier ni de code en
  double, et la vitesse officielle donne le bon pourcentage.

Ce fichier ne fait pas partie de l'application : il n'est ni importé par
elle, ni embarqué dans un binaire.
"""

import asyncio
import csv
import io
import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

from isolement import isoler  # noqa: E402

isoler()

ECHELLES = []


def verifier(nom, condition, detail=""):
    if condition:
        print(f"  ok    {nom}")
    else:
        print(f"  ÉCHEC {nom} {detail}")
        ECHELLES.append(nom)


def tester_bilan_generation():
    """Le bilan compte les succès réels, et les erreurs ne s'additionnent
    que si elles sont consécutives."""
    import voxpack2

    class Progress:
        def set(self, valeur):
            pass

        def reset(self):
            pass

    class FauxApp:
        _robot = 0
        _niveau = 0
        output_dir = tempfile.mkdtemp(prefix="voxpack-bilan-")
        progress = Progress()

        def _robot_voice(self):
            return None

        def _robot_pitch(self):
            return None

        def _rate_effectif(self, voice_id):
            return "+0%"

        def _langue_effet(self, voice_id):
            return "fr"

        def _dire(self, texte):
            pass

        def after(self, delai, fonction):
            fonction()

        def _ouvrir_dossier(self, chemin):
            pass

    appels = []

    async def fausse_voix(texte, voice_id, destination, **options):
        appels.append(texte)
        if texte.startswith("err"):
            raise ConnectionError("connection reset")

    messages = []
    faux = FauxApp()
    faux._message = lambda texte, **options: messages.append(texte)
    vraie = voxpack2.fabriquer_wav
    voxpack2.fabriquer_wav = fausse_voix
    try:
        taches = [("a", "err1"), ("b", "ok1"), ("c", "err2"),
                  ("d", "ok2"), ("e", "err3"), ("f", "ok3")]
        asyncio.run(voxpack2.VoxPackApp._generer(faux, taches, "voix", []))
    finally:
        voxpack2.fabriquer_wav = vraie

    verifier("les six lignes sont tentées",
             len(appels) == 6, f"({len(appels)})")
    verifier("le bilan compte trois succès réels",
             bool(messages) and "3 fichiers créés sur 6" in messages[0],
             messages[:1])


def main() -> int:
    from voxpack_data.langues import LANGUES, PAR_CODE, PAR_DOSSIER
    from voxpack_data.textes import (TEXTES, LANGUES_TEXTES,
                                     verifier as verifier_textes)

    print("Langues et textes")
    verifier("quinze langues dans la table",
             len(LANGUES) == 15, f"({len(LANGUES)})")
    verifier("aucun code en double", len(PAR_CODE) == len(LANGUES))
    verifier("aucun dossier SD en double", len(PAR_DOSSIER) == len(LANGUES))
    verifier("chaque langue a ses textes",
             all(langue.code in TEXTES for langue in LANGUES),
             f"({sorted(set(l.code for l in LANGUES) - set(TEXTES))})")
    verifier("aucune table de textes orpheline",
             not (set(TEXTES) - set(PAR_CODE)),
             f"({sorted(set(TEXTES) - set(PAR_CODE))})")
    ecarts = verifier_textes()
    verifier("chaque langue a une table, aucun texte vide", not ecarts,
             " ; ".join(ecarts[:3]))
    verifier("toutes les langues annoncées ont une table",
             not (set(LANGUES_TEXTES) - set(TEXTES)))

    print("Textes : pas de trou")
    vides = [(code, cle) for code, table in TEXTES.items()
             for cle, texte in table.items() if not str(texte).strip()]
    verifier("aucun texte vide", not vides, f"({vides[:3]})")
    identiques = [cle for cle in TEXTES["fr"]
                  if TEXTES["fr"][cle] == TEXTES["en"].get(cle)]
    # Mots légitimement identiques dans les deux langues : « Let's Go » ne se
    # traduit pas (décision de Richard), et « phrase » comme « robot »
    # s'écrivent pareil en français et en anglais.
    admis = {"lets_go", "phrase", "robot"}
    verifier("peu de textes identiques entre français et anglais",
             set(identiques) <= admis, f"({sorted(set(identiques) - admis)[:4]})")

    print("Langues : la vitesse officielle")
    from voxpack_data.langues import langue
    verifier("anglais +10 %", langue("en").pour_cent == 10)
    verifier("suédois -10 %", langue("sv").pour_cent == -10)
    verifier("français 0 %", langue("fr").pour_cent == 0)
    verifier("un code inconnu retombe sur le français",
             langue("zz").code == "fr")

    print("Listes")
    # On vérifie le code de l'APPLICATION, pas celui de la maquette : c'est
    # voxpack2 qui écrit et relit les listes de l'utilisateur.
    import voxpack2

    class FauxListe:
        langue = "en"

        def __init__(self, lignes):
            self.lignes = [{"nom": nom, "texte": texte}
                           for nom, texte in lignes]
            self._bak_faits = set()
            self._erreur_sauvegarde = False

        def after(self, delai, fonction):
            pass

    lignes = [("armed", "armé"), ("geardn", "train sorti"), ("vide", "")]
    vrai_data_dir = voxpack2.DATA_DIR
    with tempfile.TemporaryDirectory() as dossier:
        voxpack2.DATA_DIR = dossier
        try:
            voxpack2.VoxPackApp._ecrire_csv(FauxListe(lignes))
            chemin = voxpack2.chemin_liste("en")
            with open(chemin, encoding="utf-8", newline="") as fichier:
                relues = [tuple(ligne) for ligne in csv.reader(fichier)]
        finally:
            voxpack2.DATA_DIR = vrai_data_dir
    verifier("aller-retour CSV de l'application", relues == lignes,
             f"({relues})")

    verifier("CSV à point-virgule",
             voxpack2.lire_lignes_csv(
                 io.StringIO("nom;phrase\narmed;armé\n"))
             == [["nom", "phrase"], ["armed", "armé"]])
    verifier("CSV à virgule avec une phrase citée",
             voxpack2.lire_lignes_csv(
                 io.StringIO('nom,phrase\narmed,"moteur, armé"\n'))
             == [["nom", "phrase"], ["armed", "moteur, armé"]])
    verifier("un en-tête est reconnu",
             voxpack2.est_entete(["nom", "phrase"]))

    print("Langue du système : les quinze codes")
    for valeur, attendu in (
            ("fr-FR", "fr"), ("fr_FR.UTF-8", "fr"), ("de-DE", "de"),
            ("es-ES", "es"), ("pt-BR", "pt"), ("ru-RU", "ru"),
            ("sv-SE", "sv"), ("uk-UA", "uk"), ("cs-CZ", "cs"),
            ("da-DK", "da"), ("ja-JP", "ja"), ("zh-CN", "cn"),
            ("zh-Hans", "cn"), ("zh-TW", "tw"), ("zh-Hant", "tw"),
            ("zh-HK", "hk"), ("C.UTF-8", None), ("xx-YY", None)):
        verifier(f"{valeur} → {attendu}",
                 voxpack2.code_langue_systeme(valeur) == attendu,
                 f"({voxpack2.code_langue_systeme(valeur)})")

    print("Voix officielles : allure et hauteur")
    import voxpack2
    verifier("le suédois officiel garde sa hauteur",
             voxpack2.reglage_voix("sv-SE-SofieNeural").get("pitch")
             == "-10Hz")
    verifier("l'anglais officiel garde son allure",
             voxpack2.reglage_voix("en-IE-EmilyNeural").get("rate")
             == "+10%")
    verifier("le libellé chinois n'imbrique pas les parenthèses",
             "（" not in voxpack2.voix_de_la_langue("cn")[0][0],
             voxpack2.voix_de_la_langue("cn")[0][0])

    print("Mises à jour : comparaison numérique")
    verifier("1.10 plus récente que 1.9",
             voxpack2.version_plus_recente("V1.10", "1.9"))
    verifier("même version : rien à faire",
             not voxpack2.version_plus_recente("V1.5.1", "1.5.1"))
    verifier("1.6 plus récente que 1.5.1",
             voxpack2.version_plus_recente("V1.6", "1.5.1"))
    verifier("une étiquette vide n'annonce rien",
             not voxpack2.version_plus_recente("", "1.5.1"))

    print("Génération : bilan et coupure réseau")
    tester_bilan_generation()

    print()
    if ECHELLES:
        print(f"{len(ECHELLES)} échec(s) :", ", ".join(ECHELLES))
        return 1
    print("tout est vert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
