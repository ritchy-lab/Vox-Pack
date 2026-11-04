"""L'écran tient-il quand le texte est plus gros ?

    python tests/v2_adaptation.py

La mise en page de la v2 est écrite en PIXELS (grille de 1024), alors que les
polices Tk sont en POINTS : Tk multiplie les points par son échelle. Sur ce
Mac, 1 point = 1 pixel ; sur un PC à 96 dpi, 1 point = 1,33 pixel ; à 120 dpi,
1,67. Le texte d'un PC est donc plus gros dans les mêmes cases — c'est le
risque qu'on ne voit pas en développant sur un Mac.

Le test vérifie trois choses, dans l'ordre :

1. **À l'échelle native**, aucun texte de `BoutonV2`, `EcranV2`,
   `TexteCarcasse` ou des titres ne dépasse sa case, dans les quatre langues
   qui ont les libellés les plus longs (français, allemand, russe, portugais),
   et aux trois tailles de fenêtre (820, 704, 640).
2. **La réduction automatique** : un bouton et un écran dessinés avec une
   police 1,6 fois trop grosse (ce que fait Windows à 120 dpi) réduisent leur
   texte pour le faire tenir. C'est la parade, et elle est éprouvée ici.
3. **La fenêtre tient sur l'écran** : sa hauteur, marges comprises, ne
   dépasse pas l'écran mesuré.

Les étiquettes ordinaires (tk.Label) s'élargissent quand la police grossit :
c'est signalé, mais ce n'est pas une erreur — elles chevaucheraient un champ
voisin plutôt que d'être coupées.

Chaque taille tourne dans son propre processus : un seul interpréteur Tk par
processus, sinon les `after` d'une fenêtre détruite polluent la suivante.
"""

import json
import os
import subprocess
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

FORMATS = (820, 704, 640)
LANGUES = ("fr", "de", "ru", "pt")
# Les mêmes textes que l'écran, pour éprouver la réduction automatique.
TEXTE_LONG = "ПРОСЛУШАТЬ"
TITRE_LONG = "УРОВЕНЬ ЗВУКА · 0 dB"


# ---------------------------------------------------------------------
# Le côté enfant : une taille de fenêtre, les textes et leurs cases
# ---------------------------------------------------------------------
def mesurer() -> dict:
    import tkinter as tk

    import customtkinter as ctk
    from PIL import Image

    import voxpack2

    app = voxpack2.VoxPackApp()
    app.withdraw()
    app.update()

    def debordements():
        trouves = []

        def parcourir(widget):
            for enfant in widget.winfo_children():
                yield enfant
                yield from parcourir(enfant)

        for widget in parcourir(app):
            try:
                largeur = widget.winfo_width()
            except tk.TclError:
                continue
            if largeur <= 1:
                continue
            if not isinstance(widget, tk.Canvas) or isinstance(
                    widget, ctk.CTkCanvas):
                continue
            for item in widget.find_all():
                if widget.type(item) != "text":
                    continue
                contenu = str(widget.itemcget(item, "text"))
                boite = widget.bbox(item)
                if contenu and boite and boite[2] > largeur + 1:
                    trouves.append({
                        "type": type(widget).__name__,
                        "texte": contenu[:40],
                        "depasse": boite[2] - largeur,
                    })
        return trouves

    par_langue = {}
    for code in LANGUES:
        if code != voxpack2.LANGUE_UI:
            app.changer_langue_ui(code)
        app.update()
        par_langue[code] = debordements()

    # La réduction automatique, à la taille de police de Windows 120 dpi.
    essais = []
    bouton = voxpack2.BoutonV2(
        app, TEXTE_LONG, 0, 0, app._pv(250), app._pv(56),
        fond=app.NOIR_V2, fonte=(voxpack2.FONT_MAIN, int(app._pv(22) * 1.6)))
    bouton.update()
    boite = bouton.bbox(bouton._texte)
    essais.append({
        "nom": "BoutonV2 réduit son texte",
        "ok": bool(boite) and boite[2] - boite[0] <= bouton._l - 8,
        "detail": f"{boite[2] - boite[0]} px pour {bouton._l} px" if boite else "",
    })

    bande = Image.new("RGB", (app._pv(230), app._pv(40)), (10, 20, 22))
    ecran = voxpack2.EcranV2(
        app, bande, TITRE_LONG,
        fonte=(voxpack2.FONT_MAIN, int(app._pv(15) * 1.6)))
    ecran.update()
    boite = ecran.bbox(ecran._item)
    essais.append({
        "nom": "EcranV2 réduit son texte",
        "ok": bool(boite) and boite[2] - boite[0] <= ecran._l - 8,
        "detail": f"{boite[2] - boite[0]} px pour {ecran._l} px" if boite else "",
    })

    # La taille que l'application choisirait d'elle-même sur cet écran.
    # (Ici VOXPACK_FORMAT force une taille pour éprouver les textes : ce
    # n'est pas la taille réelle de la fenêtre sur le poste.)
    force = os.environ.pop("VOXPACK_FORMAT", None)
    naturel = app._format_fenetre()
    if force is not None:
        os.environ["VOXPACK_FORMAT"] = force

    resultat = {
        "format": app._format,
        "naturel": naturel,
        "fenetre": app.geometry().split("+")[0],
        "ecran": [app.winfo_screenwidth(), app.winfo_screenheight()],
        "debordements": par_langue,
        "essais": essais,
    }
    app.destroy()
    return resultat


# ---------------------------------------------------------------------
# Le côté parent
# ---------------------------------------------------------------------
def lancer(format_, home):
    enfant = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--enfant", str(format_)],
        capture_output=True, text=True, timeout=180,
        env=dict(os.environ, HOME=home, USERPROFILE=home),
    )
    if enfant.returncode != 0:
        return {"erreur": (enfant.stderr.strip().splitlines() or
                           ["échec sans message"])[-1]}
    return json.loads(enfant.stdout.strip().splitlines()[-1])


def main() -> int:
    if "--enfant" in sys.argv:
        os.environ["VOXPACK_FORMAT"] = sys.argv[sys.argv.index("--enfant") + 1]
        print(json.dumps(mesurer(), ensure_ascii=False))
        return 0

    home = tempfile.mkdtemp(prefix="voxpack-adapte-")
    echecs = []
    for format_ in FORMATS:
        mesure = lancer(format_, home)
        if "erreur" in mesure:
            print(f"{format_} px : ERREUR {mesure['erreur']}")
            echecs.append(f"{format_} px : {mesure['erreur']}")
            continue

        total = 0
        for code, trouves in mesure["debordements"].items():
            total += len(trouves)
            if trouves:
                pire = max(trouves, key=lambda d: d["depasse"])
                echecs.append(
                    f"{format_} px [{code}] : {len(trouves)} texte(s) coupé(s), "
                    f"pire {pire['type']} « {pire['texte']} » +{pire['depasse']} px")
        print(f"{format_} px : {total} texte(s) coupé(s) dans les quatre langues")

        for essai in mesure["essais"]:
            print(f"    {'ok ' if essai['ok'] else 'ÉCHEC'} {essai['nom']}"
                  f" ({essai['detail']})")
            if not essai["ok"]:
                echecs.append(f"{format_} px : {essai['nom']}")

        # La fenêtre réelle est celle que l'application calcule pour cet
        # écran (VOXPACK_FORMAT ne sert qu'à mesurer les textes) : c'est elle
        # qui doit tenir, pas les tailles forcées par le test.
        if mesure["naturel"] > mesure["ecran"][1] - 24:
            echecs.append(
                f"la fenêtre calculée ({mesure['naturel']} px) dépasse "
                f"l'écran ({mesure['ecran'][1]} px)")

    print()
    if echecs:
        for echec in echecs:
            print("ÉCHEC", echec)
        return 1
    print("tout est vert : rien n'est coupé, la réduction fonctionne, "
          "la fenêtre tient")
    return 0


if __name__ == "__main__":
    sys.exit(main())
