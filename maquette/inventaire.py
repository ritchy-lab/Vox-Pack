"""Combien de sons système chaque langue apporte-t-elle ?

Sert à décider, données en main, ce que la v2 peut promettre : une langue
dont le CSV officiel ne contient que soixante sons ne se vend pas comme une
langue complète. Le script télécharge les quinze CSV (une fois, puis cache),
compte les sons du dossier SYSTEM, et mesure la couverture des trente-quatre
phrases candidates retenues dans `docs/vox-pack-new.md`.

    python maquette/inventaire.py

Écrit aussi `docs/langues-couverture.md`, le tableau lisible par Richard.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))

from voxpack_data.langues import (LANGUES, lire_csv_complet,  # noqa: E402
                                  telecharger)

CACHE = Path("/tmp/voxpack-csv")

# Les trente-quatre phrases candidates, recopiées de `docs/vox-pack-new.md`
# (§ « Les 34 phrases de départ candidates »). Ce sont des noms de FICHIERS
# EdgeTX, pas des phrases : c'est ainsi qu'on mesure la couverture.
CANDIDATES = [
    "armed", "disarm", "gearup", "geardn", "flapup", "flapdn", "attero",
    "engoff", "midtrim", "maxtrim", "mintrim", "timovr1", "timovr2",
    "timovr3", "spdmod", "thmmod", "nrmmod", "lnding", "acro", "lvlmod",
    "fm-1", "fm-2", "fm-3", "fm-pwr", "fm-lnd", "fm-spd", "fm-nrm",
    "fm-crs", "fm-acr", "lowbatt", "inactiv", "hello", "trnon", "trnoff",
]


def csv_d_une_langue(code: str) -> str:
    """Le CSV officiel, depuis le cache s'il y est déjà."""
    CACHE.mkdir(parents=True, exist_ok=True)
    fichier = CACHE / f"{code}.csv"
    if fichier.exists():
        return fichier.read_text(encoding="utf-8-sig")
    texte = telecharger(f"voices/{code}.csv")
    fichier.write_text(texte, encoding="utf-8-sig")
    return texte


def normaliser(phrase: str) -> str:
    """De quoi comparer deux phrases sans se faire piéger par la forme.

    EdgeTX écrit ses annonces pour le synthétiseur : minuscules, points pour
    les pauses, orthographe phonétique (« edge t x »). Deux annonces
    identiques après ce nettoyage sont, presque sûrement, une traduction
    oubliée.
    """
    return " ".join(phrase.lower().replace(".", " ").replace(",", " ")
                    .split())


def mesurer() -> list[dict]:
    # L'anglais sert de référence : une annonce identique à l'anglaise dans
    # une autre langue est une traduction oubliée, pas une coïncidence.
    anglais = {}
    try:
        for _, nom, phrase in lire_csv_complet(
                csv_d_une_langue("en-GB")):
            anglais.setdefault(nom, normaliser(phrase))
    except Exception:
        pass

    resultats = []
    for langue in LANGUES:
        try:
            morceaux = lire_csv_complet(csv_d_une_langue(
                langue.csv.split("/")[-1][:-4]))
        except Exception as erreur:                      # réseau, 404…
            resultats.append({"langue": langue, "erreur": str(erreur)[:60]})
            continue
        # Les 34 phrases candidates sont des annonces de RADIO : elles vivent
        # à la racine pour la plupart, pas dans SYSTEM. On cherche donc dans
        # tout le fichier — c'est le piège qui a faussé le premier relevé.
        noms = {nom for _, nom, _ in morceaux}
        presents = [c for c in CANDIDATES if c in noms]
        textes = {}
        for _, nom, phrase in morceaux:
            textes.setdefault(nom, normaliser(phrase))
        en_anglais = [] if langue.code == "en" else [
            c for c in presents
            if anglais.get(c) and textes.get(c) == anglais[c]]
        resultats.append({
            "langue": langue,
            "system": sum(1 for d, _, _ in morceaux if d == "SYSTEM"),
            "racine": sum(1 for d, _, _ in morceaux if d != "SYSTEM"),
            "couverts": len(presents),
            "manquants": [c for c in CANDIDATES if c not in noms],
            "en_anglais": en_anglais,
        })
    return resultats


def tableau(resultats: list[dict]) -> str:
    lignes = [
        "| langue | sons SYSTEM | sons de racine | sur 34 | en anglais | "
        "ce qui manque |",
        "|---|---|---|---|---|---|",
    ]
    for r in resultats:
        langue = r["langue"]
        if "erreur" in r:
            lignes.append(f"| {langue.nom} (`{langue.code}`) | — | — | — | — | "
                          f"téléchargement impossible : {r['erreur']} |")
            continue
        manquants = r["manquants"]
        apercu = "aucun" if not manquants else ", ".join(manquants[:6])
        if len(manquants) > 6:
            apercu += f" … (+{len(manquants) - 6})"
        restes = r["en_anglais"]
        marque = "—" if not restes else ", ".join(restes[:3])
        if len(restes) > 3:
            marque += f" … (+{len(restes) - 3})"
        lignes.append(f"| {langue.nom} (`{langue.code}`) | {r['system']} | "
                      f"{r['racine']} | {r['couverts']}/34 | {marque} | "
                      f"{apercu} |")
    return "\n".join(lignes)


def main() -> int:
    resultats = mesurer()
    texte = tableau(resultats)
    print(texte)
    entete = ("# Ce que chaque langue apporte — inventaire des sons système\n\n"
              "*Relevé le 29 octobre 2026 par `maquette/inventaire.py`, à "
              "partir des CSV du dépôt `EdgeTX/edgetx-sdcard-sounds`. Ne pas "
              "modifier à la main : relancer le script.*\n\n"
              "Deux comptes : le dossier `SYSTEM` (ce que Vox-Pack "
              "refabrique) et la **racine**. La racine n'est pas refabriquée "
              "(elle mélange les annonces officielles et les sons personnels "
              "de l'utilisateur, décision de Richard), mais c'est elle qui "
              "porte les annonces de la radio — `armed`, `gearup`, `attero`. "
              "Chercher `armed` dans `SYSTEM` ne le trouve pas : le premier "
              "relevé s'y est trompé.\n\n"
              "La colonne **en anglais** compte les annonces dont le texte est "
              "identique à l'anglais : ce sont des traductions oubliées chez "
              "EdgeTX, pas des coïncidences. Elles sont écrites pour le "
              "synthétiseur (minuscules, points pour les pauses, orthographe "
              "phonétique — « edge t x »), ce qui est normal ici.\n\n"
              "« sur 34 » mesure les phrases candidates de "
              "`docs/vox-pack-new.md` réellement présentes dans le CSV — c'est "
              "l'écart entre ce qu'on promet et ce qu'EdgeTX fournit.\n\n")
    Path(ICI.parent / "docs" / "langues-couverture.md").write_text(
        entete + texte + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
