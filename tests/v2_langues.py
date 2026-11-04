"""Contrôle des textes tels que l'application les affiche.

    python tests/v2_langues.py          # vérifie
    python tests/v2_langues.py --maj    # enregistre l'état (après un lot)

L'application fusionne deux sources : les textes de la 1.5.1 (fr, en, de,
255 clés) et les textes de `voxpack_data/textes.py`, dont les lots de
traduction des douze nouvelles langues. C'est cette table fusionnée que
l'écran affiche — et non le paquet seul, que vérifie `v2_textes.py`.

Une langue incomplète est normale : les textes arrivent par lots, écran par
écran (voir LOT_0 dans textes.py). L'état est enregistré dans
`tests/langues-etat.json`. Le test échoue si :

- une clé manquante n'était pas déjà connue (une régression) ;
- une clé de l'état est désormais traduite sans que l'état ait été mis à
  jour (le fichier mentirait sur l'avancement) ;
- une langue utilise une clé qui n'existe pas en français (faute de frappe) ;
- une traduction perd ou invente un champ `{nom}` : `t()` formate le texte,
  et un `{n}` devenu `{nombre}` ferait planter l'affichage.

Après un lot, relancer avec `--maj` : l'état est réécrit, et le test repart
au vert pour les clés restantes.
"""

import json
import os
import string
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

from isolement import isoler  # noqa: E402

isoler()

import voxpack2  # noqa: E402  (importe les tables fusionnées)

ETAT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "langues-etat.json")
COMPLETES = ("fr", "en", "de")


def champs(texte):
    """Les champs `{nom}` d'un texte, ou None si les accolades sont cassées."""
    try:
        return {nom for _litteral, nom, _format, _conversion
                in string.Formatter().parse(str(texte)) if nom}
    except ValueError:
        return None


def trous():
    """{langue: [clés absentes]} pour les quinze langues de l'application."""
    reference = set(voxpack2.TEXTES["fr"])
    return {code: sorted(reference - set(voxpack2.TEXTES.get(code, {})))
            for code in voxpack2.LANGUES
            if reference - set(voxpack2.TEXTES.get(code, {}))}


def main() -> int:
    echecs = []
    manquantes = trous()
    reference = set(voxpack2.TEXTES["fr"])

    print(f"Textes fusionnés : {len(voxpack2.LANGUES)} langues, "
          f"{len(reference)} clés de référence")

    for code in COMPLETES:
        if manquantes.get(code):
            echecs.append(f"{code} : {len(manquantes[code])} clé(s) manquante(s)")

    # Une clé inconnue du français ne s'afficherait jamais : c'est une faute.
    for code in voxpack2.LANGUES:
        inconnues = set(voxpack2.TEXTES[code]) - reference
        if inconnues:
            echecs.append(f"{code} : clés inconnues {sorted(inconnues)[:4]}")

    # Les champs {…} doivent être les mêmes que ceux du français.
    for code in voxpack2.LANGUES:
        for cle, texte in voxpack2.TEXTES[code].items():
            if cle not in reference:      # déjà signalé comme clé inconnue
                continue
            attendus = champs(voxpack2.TEXTES["fr"][cle])
            trouves = champs(texte)
            if trouves is None:
                echecs.append(f"{code} : accolades cassées dans « {cle} »")
            # Une traduction peut OMETTRE un champ (l'allemand n'a pas de
            # pluriel en {s}), mais jamais en inventer un : t() ne fournit
            # que les champs du français, et un champ en trop lèverait
            # KeyError au moment de l'affichage.
            elif attendus is not None and trouves - attendus:
                echecs.append(
                    f"{code} : champ(s) {sorted(trouves - attendus)} inconnu(s) "
                    f"dans « {cle} »")

    if "--maj" in sys.argv:
        with open(ETAT, "w", encoding="utf-8") as fichier:
            json.dump({code: cles for code, cles in sorted(manquantes.items())},
                      fichier, ensure_ascii=False, indent=1)
        print(f"état écrit dans {os.path.relpath(ETAT, RACINE)}")
    else:
        try:
            with open(ETAT, encoding="utf-8") as fichier:
                attendu = json.load(fichier)
        except FileNotFoundError:
            print("pas d'état enregistré : lancer avec --maj")
            return 1
        attendu = {code: set(cles) for code, cles in attendu.items()}
        for code in sorted(set(attendu) | set(manquantes)):
            nouvelles = set(manquantes.get(code, ())) - attendu.get(code, set())
            comblees = attendu.get(code, set()) - set(manquantes.get(code, ()))
            if nouvelles:
                echecs.append(
                    f"{code} : {len(nouvelles)} clé(s) nouvellement "
                    f"manquante(s) {sorted(nouvelles)[:3]}")
            if comblees and code in attendu:
                echecs.append(
                    f"{code} : {len(comblees)} clé(s) désormais traduite(s), "
                    f"relancer avec --maj")

    for code in sorted(manquantes):
        faites = len(reference) - len(manquantes[code])
        print(f"  {code:3s} {faites:3d}/{len(reference)}")

    if echecs:
        print()
        for echec in echecs:
            print("ÉCHEC", echec)
        return 1
    print("tout est vert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
