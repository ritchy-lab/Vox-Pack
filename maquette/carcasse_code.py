"""Carcasse Vox-Pack dessinée en code (essai).

Même composition que l'export Pixelmator, mais tout est calculé : métal
brossé, chanfreins, arêtes, vis, plaques. Rien n'est peint à la main, donc
la taille est un paramètre — on rend net à 2× pour les écrans Retina.

Coordonnées écrites dans l'espace 1024 × 1024 de l'image de Richard.
"""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ICI = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(ICI, "..", "logo.png")
SORTIE = os.path.join(ICI, "carcasse-code.png")

BASE = 1024
SUR = 2                 # suréchantillonnage avant réduction
CIBLE = 1640            # 2 × 820 points

# Couleurs du métal
HAUT = (46, 59, 63)
BAS = (31, 41, 45)
PLAQUE = (52, 66, 70)
NOIR = (0, 4, 5)
CYAN = (15, 187, 208)
LIGNE_CLAIR = (110, 132, 136)
LIGNE_SOMBRE = (8, 14, 16)


def metal(w, h, haut=HAUT, bas=BAS, force=6.0):
    """Un dégradé vertical, brossé horizontalement."""
    y = np.linspace(0.0, 1.0, h)[:, None, None]
    fond = (np.array(haut)[None, None, :] * (1 - y)
            + np.array(bas)[None, None, :] * y)
    petit = np.random.normal(0, 1, (h, max(2, w // 12)))
    grain = Image.fromarray(((petit + 3) * 42).clip(0, 255).astype("uint8"))
    grain = np.array(grain.resize((w, h), Image.BILINEAR)).astype(float)
    grain = (grain - grain.mean()) / (grain.std() + 1e-6)
    image = fond + grain[:, :, None] * force
    return Image.fromarray(np.clip(image, 0, 255).astype("uint8"))


def chanfrein(x0, y0, x1, y1, c=0):
    """Les quatre coins d'un panneau, coupés à 45°."""
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def ombre(fond, points, echelle, flou=7, opacite=120):
    """Une ombre portée douce, pour que le panneau se décolle du fond."""
    calque = Image.new("RGBA", fond.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    d.polygon([((x + 4) * echelle, (y + 5) * echelle) for x, y in points],
              fill=(0, 0, 0, opacite))
    calque = calque.filter(ImageFilter.GaussianBlur(flou * echelle))
    return Image.alpha_composite(fond, calque)


def aretes(dessin, points, echelle, clair=LIGNE_CLAIR, sombre=LIGNE_SOMBRE):
    """Arêtes éclairées dessus et à gauche, sombres dessous et à droite."""
    w = max(1, int(echelle))
    xs = [p[0] * echelle for p in points]
    ys = [p[1] * echelle for p in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    dessin.line((x0 + w, y0 + w, x1 - w, y0 + w), fill=clair, width=w)
    dessin.line((x0 + w, y0 + w, x0 + w, y1 - w), fill=clair, width=w)
    dessin.line((x0, y1, x1, y1), fill=sombre, width=w)
    dessin.line((x1, y0, x1, y1), fill=sombre, width=w)


def dessiner(taille):
    """Rend la carcasse en `taille` × `taille` pixels."""
    echelle = taille / BASE
    s = lambda *points: [(x * echelle, y * echelle) for x, y in points]

    fond = metal(taille, taille).convert("RGBA")

    # --- le cadre : une bande de métal plus claire, avec ses arêtes -----
    cadre = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cadre)
    dc.polygon(s(*chanfrein(0, 0, 1024, 1024, 26)), fill=(255, 255, 255, 255))
    dc.polygon(s(*chanfrein(26, 26, 998, 998, 20)), fill=(0, 0, 0, 0))
    fond = Image.composite(metal(taille, taille, PLAQUE, (40, 52, 56)), fond, cadre.split()[3])

    dessin = ImageDraw.Draw(fond)
    w = max(1, int(echelle))

    # arête claire en haut du cadre, sombre en bas
    dessin.line(s((26, 27), (998, 27)), fill=LIGNE_CLAIR, width=w)
    dessin.line(s((27, 28), (27, 998)), fill=LIGNE_CLAIR, width=w)
    dessin.line(s((26, 997), (998, 997)), fill=LIGNE_SOMBRE, width=w)

    # --- la zone de travail, noire ------------------------------------
    dessin.rectangle(s((312, 168), (999, 838)), fill=NOIR)
    dessin.line(s((312, 168), (999, 168)), fill=(34, 44, 48), width=w)

    # --- le panneau de gauche, en relief ------------------------------
    points_panneau = chanfrein(44, 180, 310, 840, 10)
    fond = ombre(fond, points_panneau, echelle)
    panneau = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
    dp = ImageDraw.Draw(panneau)
    dp.polygon(s(*points_panneau), fill=(255, 255, 255, 255))
    fond = Image.composite(metal(taille, taille, (52, 66, 70), (39, 51, 56)),
                           fond, panneau.split()[3])
    dessin = ImageDraw.Draw(fond)
    dessin.polygon(s(*points_panneau), outline=(70, 86, 90), width=w)
    aretes(dessin, points_panneau, echelle)

    # --- la carte noire, avec son coin biaisé -------------------------
    carte = [(61, 361), (291 - 24, 361), (291, 361 + 24), (291, 790), (61, 790)]
    dessin.polygon(s(*carte), fill=NOIR)
    dessin.polygon(s(*carte), outline=(58, 72, 76), width=w)
    # le liseré cyan dans la coupe, juste à l'intérieur
    dessin.line(s((291 - 24, 363), (289, 361 + 24)), fill=CYAN, width=w * 2)
    dessin.line(s((289, 361 + 22), (289, 788)), fill=(24, 34, 38), width=w)

    # --- la plaque du logo, en haut -----------------------------------
    plaque_logo = chanfrein(300, 32, 724, 158, 14)
    fond = ombre(fond, plaque_logo, echelle, flou=8)
    dessin = ImageDraw.Draw(fond)
    dessin.polygon(s(*plaque_logo), fill=(11, 19, 21))
    dessin.polygon(s(*plaque_logo), outline=(52, 68, 72), width=w)

    # --- la plaque du haut à droite -----------------------------------
    dessin.polygon(s(*chanfrein(820, 30, 992, 158, 12)),
                   fill=(50, 64, 68))
    dessin.polygon(s(*chanfrein(820, 30, 992, 158, 12)),
                   outline=(86, 104, 108), width=w)
    aretes(dessin, chanfrein(820, 30, 992, 158, 12), echelle)
    # le trait cyan de son coin
    dessin.polygon(s((832, 38), (880, 38), (868, 48), (832, 48)), fill=CYAN)

    # --- le bandeau du bas --------------------------------------------
    bandeau = [(40, 845), (995, 845), (995, 945), (40, 945)]
    fond = ombre(fond, bandeau, echelle, flou=9)
    dessin = ImageDraw.Draw(fond)
    dessin.rectangle(s((40, 845), (995, 945)), fill=(48, 61, 65))
    aretes(dessin, bandeau, echelle, clair=(104, 122, 126))

    # la découpe du bas, dans le cadre
    dessin.polygon(s((356, 1002), (388, 980), (636, 980), (668, 1002)),
                   fill=(24, 33, 37))
    dessin.line(s((388, 980), (636, 980)), fill=(92, 108, 112), width=w)
    dessin.line(s((356, 1002), (388, 980)), fill=(70, 84, 88), width=w)
    dessin.line(s((636, 980), (668, 1002)), fill=(18, 26, 29), width=w)

    # --- les vis --------------------------------------------------------
    for x, y in ((30, 30), (994, 30), (30, 994), (994, 994),
                 (56, 192), (298, 192), (56, 828), (298, 828)):
        r = 5 * echelle
        dessin.ellipse((x * echelle - r, y * echelle - r,
                        x * echelle + r, y * echelle + r),
                       fill=(58, 72, 76), outline=(20, 28, 30), width=w)

    # --- le logo, avec son halo ----------------------------------------
    if os.path.exists(LOGO):
        logo = Image.open(LOGO).convert("RGBA")
        hauteur = int(118 * echelle)
        largeur = int(logo.width * hauteur / logo.height)
        logo = logo.resize((largeur, hauteur), Image.LANCZOS)
        gauche = int(512 * echelle - largeur / 2)
        haut = int(38 * echelle)
        halo = Image.new("RGBA", fond.size, (0, 0, 0, 0))
        halo.paste(logo, (gauche, haut), logo)
        lueur = halo.filter(ImageFilter.GaussianBlur(9 * echelle))
        teinte = Image.new("RGBA", fond.size, CYAN + (255,))
        lueur = Image.composite(teinte, Image.new("RGBA", fond.size, (0, 0, 0, 0)),
                                lueur.split()[3])
        lueur.putalpha(lueur.split()[3].point(lambda a: int(a * 0.55)))
        fond = Image.alpha_composite(fond, lueur)
        fond = Image.alpha_composite(fond, halo)

    return fond.convert("RGB")


if __name__ == "__main__":
    np.random.seed(4)
    grand = dessiner(BASE * SUR)
    final = grand.resize((CIBLE, CIBLE), Image.LANCZOS)
    final.save(SORTIE, optimize=True)
    print(SORTIE, final.size, os.path.getsize(SORTIE) // 1024, "ko")
