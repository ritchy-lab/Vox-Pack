"""Imprime le texte de la page « Releases » d'une version donnée.

    python3 docs/page-de-version.py V1.4.2 > page.md

`docs/notes-de-version.md` est l'HISTORIQUE complet, dans les deux langues :
c'est pratique pour nous, mais une page de version ne doit montrer que ce qui
est nouveau DANS cette version, puis comment l'installer. Ce programme fait le
découpage :

    introduction + « Nouveautés de la X » + à télécharger / à savoir
    puis la même chose en anglais (## English …)

Si une section manque (faute de frappe dans un titre, version inconnue), on
n'imprime pas une page vide : on imprime le fichier entier et on le dit sur la
sortie d'erreur. Le robot de publication ne peut donc jamais publier une page
blanche.
"""

import re
import sys
from pathlib import Path

FICHIER = Path(__file__).with_name("notes-de-version.md")

# Les titres qui encadrent les morceaux à garder. Les sections de nouveautés
# sont reconnues par leur préfixe, la version étant comparée à part.
TITRE_NOUVEAUTES_FR = "Nouveautés de la"
TITRE_NOUVEAUTES_EN = "What's new in"
TITRE_TELECHARGER_FR = "À télécharger"
TITRE_SAVOIR_FR = "Ce qu'il faut savoir"
TITRE_ANGLAIS = "English"
TITRE_TELECHARGER_EN = "What to download"
TITRE_SAVOIR_EN = "Good to know"

MOTIF_NOUVEAUTES_FR = re.compile(r"^Nouveautés de la\s+(.+)$", re.I)
MOTIF_NOUVEAUTES_EN = re.compile(r"^What's new in\s+(.+)$", re.I)


def normaliser(version):
    """« V1.4.2 », « v1.4.2 » et « 1.4.2 » sont la même version."""
    return version.strip().lower().lstrip("v").strip()


def decouper(lignes):
    """Renvoie [(titre, début, fin)] pour chaque titre de niveau 2 ou 3.

    Un titre de niveau 3 ferme le bloc du titre de niveau 2 qui le précède :
    sans cela, « ### What to download » se retrouverait collé à la dernière
    section de nouveautés.
    """
    titres = []
    for i, ligne in enumerate(lignes):
        trouve = re.match(r"^(#{2,3})\s+(.+?)\s*$", ligne)
        if trouve:
            titres.append((trouve.group(2), i))
    blocs = []
    for rang, (titre, debut) in enumerate(titres):
        fin = titres[rang + 1][1] if rang + 1 < len(titres) else len(lignes)
        blocs.append((titre, debut, fin))
    return blocs, (titres[0][1] if titres else len(lignes))


def texte(lignes, debut, fin):
    return "\n".join(lignes[debut:fin]).strip("\n")


def bloc_exact(lignes, blocs, titre_voulu):
    for titre, debut, fin in blocs:
        if titre.lower() == titre_voulu.lower():
            return texte(lignes, debut, fin)
    return None


def bloc_nouveautes(lignes, blocs, motif, version):
    for titre, debut, fin in blocs:
        trouve = motif.match(titre)
        if trouve and normaliser(trouve.group(1)) == normaliser(version):
            return texte(lignes, debut, fin)
    return None


def bloc_jusqu_a(lignes, blocs, titre_depart, titre_arret):
    """Du titre de départ jusqu'au titre d'arrêt, exclus."""
    debut = None
    for titre, d, _ in blocs:
        if titre.lower() == titre_depart.lower():
            debut = d
            break
    if debut is None:
        return None
    fin = len(lignes)
    for titre, d, _ in blocs:
        if d > debut and titre.lower() == titre_arret.lower():
            fin = d
            break
    return texte(lignes, debut, fin)


def bloc_depuis(lignes, blocs, titre_depart):
    """Du titre de départ jusqu'à la fin du fichier."""
    for titre, debut, _ in blocs:
        if titre.lower() == titre_depart.lower():
            return texte(lignes, debut, len(lignes))
    return None


def partie_anglaise(lignes, blocs):
    """« ## English » et son introduction, jusqu'aux nouveautés anglaises."""
    debut = None
    for titre, d, _ in blocs:
        if titre.lower() == TITRE_ANGLAIS.lower():
            debut = d
            break
    if debut is None:
        return None
    for titre, d, _ in blocs:
        if d > debut and MOTIF_NOUVEAUTES_EN.match(titre):
            return texte(lignes, debut, d)
    return None


def composer(lignes, version):
    """Le texte de la page, ou None si un morceau manque."""
    blocs, premier_titre = decouper(lignes)

    # L'introduction : tout ce qui précède le premier titre. Le commentaire
    # HTML d'en-tête (consignes aux auteurs) n'a rien à faire sur une page.
    introduction = lignes[:premier_titre]
    if introduction and introduction[0].startswith("<!--"):
        for i, ligne in enumerate(introduction):
            if "-->" in ligne:
                introduction = introduction[i + 1:]
                break

    morceaux = {
        "introduction": texte(introduction, 0, len(introduction)),
        "nouveautés FR": bloc_nouveautes(lignes, blocs,
                                         MOTIF_NOUVEAUTES_FR, version),
        "à télécharger FR": bloc_jusqu_a(lignes, blocs,
                                         TITRE_TELECHARGER_FR, TITRE_ANGLAIS),
        "partie anglaise": partie_anglaise(lignes, blocs),
        "nouveautés EN": bloc_nouveautes(lignes, blocs,
                                         MOTIF_NOUVEAUTES_EN, version),
        "à télécharger EN": bloc_depuis(lignes, blocs, TITRE_TELECHARGER_EN),
    }

    manquants = [nom for nom, valeur in morceaux.items() if not valeur]
    if manquants:
        print("Section(s) introuvable(s) pour %s : %s — page complète imprimée."
              % (version, ", ".join(manquants)), file=sys.stderr)
        return None
    return "\n\n".join(morceaux.values())


def main():
    if len(sys.argv) != 2:
        print("usage : page-de-version.py <V1.4.2>", file=sys.stderr)
        return 2
    lignes = FICHIER.read_text(encoding="utf-8").splitlines()
    page = composer(lignes, sys.argv[1])
    if page is None:
        page = FICHIER.read_text(encoding="utf-8")
    print(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
