"""Maquette Vox-Pack v2 — la carcasse, et de vrais widgets par-dessus.

Rien d'ici ne touche à l'application : c'est une fenêtre d'essai, à jeter ou
à promouvoir. L'image de fond (carcasse.png) donne le cadre, les plaques et
le logo ; tout ce qui se lit, se clique ou défile est du Tk ordinaire posé
aux coordonnées des zones libres de l'image.

Trois règles qui font la différence :

- aucun widget ne peint son propre rectangle sur l'habillage. Un texte posé
  sur le métal ou sur une plaque est dessiné sur un Canvas qui prend pour
  fond le morceau de carcasse correspondant : la texture passe dessous.
- le format est décidé une fois (FORMAT, à la fin). Les positions sont
  écrites dans les coordonnées de l'image 1024 × 1024, puis multipliées.
- deux familles, pas trois : la même sans pour tout le texte, et le mono
  uniquement pour les noms de fichiers, comme sur la planche de Richard.
"""

import asyncio
import csv
import ctypes
import ctypes.util
import json
import os
import queue
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from ctypes import byref, c_char_p, c_long, c_void_p

import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import filedialog

ICI = os.path.dirname(os.path.abspath(__file__))
# La maquette emprunte le moteur de la 1.5.1 (voix, WAV, robot, niveau) : il
# faut que le dossier du projet soit dans le chemin d'importation, même quand
# on lance le fichier depuis maquette/.
RACINE = os.path.dirname(ICI)
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)


def _chercher(*morceaux):
    """Où trouver un fichier livré avec l'application.

    Lancée depuis les sources, la maquette trouve ses images à côté d'elle.
    Compilée, PyInstaller les range dans un dossier temporaire
    (`sys._MEIPASS`) : c'est la même recherche que la 1.5.1, et sans elle
    l'application compilée ne retrouverait plus son propre fond.
    """
    pistes = []
    if getattr(sys, "frozen", False):
        pistes.append(getattr(sys, "_MEIPASS", ""))
        pistes.append(os.path.dirname(os.path.abspath(sys.executable)))
        pistes.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)),
                                   "..", "Resources"))
    pistes.extend([ICI, RACINE])
    for racine in pistes:
        if not racine:
            continue
        chemin = os.path.join(racine, *morceaux)
        if os.path.exists(chemin):
            return chemin
    return os.path.join(ICI, *morceaux)


CARCASSE = _chercher("carcasse.webp")
if not os.path.exists(CARCASSE):
    CARCASSE = _chercher("carcasse.png")
TASSE = _chercher("ko-fi.png")
# Où vivent les données de l'utilisateur. La maquette se sert chez elle ;
# l'application (voxpack2.py) partage le dossier de la 1.5.1 mais avec des
# fichiers à elle — on ne veut pas écraser les réglages de la 1.5.1, qui ne
# connaît pas les mêmes clés.
DONNEES = os.environ.get("VOXPACK_DATA") or ICI
PREFIXE = os.environ.get("VOXPACK_PREFIXE", "")
REGLAGES = os.path.join(DONNEES, PREFIXE + "reglages.json")
LISTES = os.path.join(DONNEES, PREFIXE + "listes.json")
SORTIES = os.path.join(DONNEES, "sorties")
POLICES = _chercher("polices")

# ------------------------------------------------------------------
# Zones libres de la carcasse (coordonnées de l'image 1024 × 1024)
# ------------------------------------------------------------------
Z_PANNEAU = (44, 180, 310, 840)     # panneau de gauche
Z_CARTE = (61, 361, 291, 790)       # carte noire, coin haut-droit biaisé
Z_LISTE = (324, 168, 999, 835)      # grande zone noire
Z_PLAQUE = (820, 30, 992, 158)      # plaque en haut à droite
Z_BANDE = (40, 845, 995, 945)       # bandeau métal du bas

# Le côté de la fenêtre, en pixels. Les positions s'écrivent dans l'espace
# 1024 × 1024 de l'image et se multiplient par k = FORMAT / 1024. La
# constante est ici, et non dans le `__main__`, pour que le module puisse
# être importé (essais, relevé de l'interface, intégration à l'application).
FORMAT = 820

# ------------------------------------------------------------------
# Couleurs relevées dans l'image
# ------------------------------------------------------------------
NOIR = "#000405"        # la zone de travail
CARTE = "#000000"       # la carte des réglages est noire
BANDE = "#2D3A3E"       # métal du bas
FACE = "#16262A"
SURVOL = "#24404A"
PRESSE = "#0C1618"
BORD = "#4C6469"
CLAIR = "#718B90"
SOMBRE = "#06100F"
ACCENT = "#0FBBD0"      # le cyan de la carcasse (0, 184, 208)
ACCENT_SOMBRE = "#0B4A55"
TEXTE = "#E9F4F6"
GRIS = "#7C959A"
RAYURE = "#0B1517"      # une ligne sur deux dans la liste

# Les noms de fichiers sont ceux d'EdgeTX, les phrases leur traduction.
PHRASES = [
    ("armed", "Moteur armé"),
    ("disarm", "Moteur désarmé"),
    ("batlow", "Batterie faible"),
    ("flaps1", "Volets position un"),
    ("gearup", "Train rentré"),
    ("geardn", "Train sorti"),
    ("thrcut", "Coupe des gaz"),
    ("timer1", "Chrono terminé"),
    ("acro", "Mode acrobatie"),
    ("stabon", "Stabilisateur enclenché"),
    ("flapup", "Volets rentrés"),
    ("flapdn", "Volets sortis"),
    ("engoff", "Moteur coupé"),
    ("hello", "Bonjour"),
]

# Les langues viennent de `langues.py`, une seule fois pour tout le fichier :
# quinze langues, leur nom natif, leur dossier SD, leur voix officielle et
# leur allure. Cette table est vérifiable contre la recette d'EdgeTX
# (`python -m voxpack_data.langues`) — ne pas la recopier ici.
from voxpack_data.langues import (LANGUES, PAR_CODE,  # noqa: E402
                                  liste_de_depart, langue as donner_langue,
                                  sons_systeme)
from voxpack_data.textes import TEXTES  # noqa: E402


def espacer(texte):
    """Capitales espacées — sauf pour les écritures qui n'ont pas d'espaces.

    Glisser une espace entre chaque signe transformerait 追加 en « 追 加 ».
    On garde donc les capitales, sans l'espacement, en japonais et en
    chinois.
    """
    texte = texte.upper()
    if any("\u3040" <= c <= "\u9fff" for c in texte):
        return texte
    return " ".join(texte)


def nom_voix(identifiant):
    """Le nom court d'une voix edge-tts : `fr-FR-DeniseNeural` → « Denise »."""
    return identifiant.split("-")[-1].replace("Neural", "")


# Les voix proposées pour chaque langue. Les trois langues historiques
# gardent les leurs ; les douze autres n'ont, pour l'instant, que la voix
# officielle d'EdgeTX — c'est déjà celle qui reproduit les sons du
# constructeur.
VOIX_PAR_LANGUE = {
    "fr": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural",
           "fr-CH-ArianeNeural", "fr-CH-FabriceNeural"],
    "en": ["en-IE-EmilyNeural", "en-US-AriaNeural",
           "en-US-GuyNeural", "en-GB-SoniaNeural"],
    "de": ["de-DE-KatjaNeural", "de-DE-ConradNeural",
           "de-DE-AmalaNeural", "de-DE-KillianNeural"],
}


def voix_de(code):
    """Les identifiants de voix proposés pour une langue."""
    langue = donner_langue(code)
    return VOIX_PAR_LANGUE.get(code, [langue.voix])


SANS = ("Avenir Next", "Segoe UI", "Helvetica Neue", "Helvetica", "Arial")
MONO = ("Share Tech Mono", "Menlo", "Consolas", "Courier New")


# ------------------------------------------------------------------
# Polices : chargées pour ce processus seulement, sans rien installer
# ------------------------------------------------------------------
def lire_reglages():
    """Les réglages de la dernière fois, ou un dictionnaire vide.

    Un fichier abîmé ne doit pas empêcher la fenêtre de s'ouvrir : on
    repart de zéro, silencieusement.
    """
    try:
        with open(REGLAGES, encoding="utf-8") as fichier:
            donnees = json.load(fichier)
        return donnees if isinstance(donnees, dict) else {}
    except Exception:
        return {}


def ecrire_reglages(donnees):
    """Écrit les réglages ; un échec d'écriture ne casse rien."""
    try:
        with open(REGLAGES, "w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier, ensure_ascii=False, indent=1)
    except Exception:
        pass


def lire_listes():
    """Les listes retouchées par langue, telles qu'on les a laissées."""
    try:
        with open(LISTES, encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except Exception:
        return {}
    if not isinstance(donnees, dict):
        return {}
    propres = {}
    for code, lignes in donnees.items():
        if isinstance(lignes, list):
            couples = [(str(nom), str(phrase))
                       for nom, phrase in (paire for paire in lignes
                                           if isinstance(paire, list)
                                           and len(paire) == 2)]
            if couples:
                propres[code] = couples
    return propres


def ecrire_listes(donnees):
    """Écrit les listes ; un échec d'écriture ne casse rien."""
    try:
        with open(LISTES, "w", encoding="utf-8") as fichier:
            json.dump(donnees, fichier, ensure_ascii=False, indent=1)
    except Exception:
        pass


def charger_polices():
    """Déclare les .ttf du dossier auprès de CoreText, à portée du processus."""
    if not os.path.isdir(POLICES):
        return
    try:
        ct = ctypes.CDLL(ctypes.util.find_library("CoreText"))
        cf = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))
    except Exception:
        return
    cf.CFURLCreateFromFileSystemRepresentation.restype = c_void_p
    cf.CFURLCreateFromFileSystemRepresentation.argtypes = [
        c_void_p, c_char_p, c_long, ctypes.c_bool]
    cf.CFRelease.argtypes = [c_void_p]
    ct.CTFontManagerRegisterFontsForURL.argtypes = [
        c_void_p, ctypes.c_uint32, ctypes.POINTER(c_void_p)]
    for nom in sorted(os.listdir(POLICES)):
        if not nom.lower().endswith((".ttf", ".otf")):
            continue
        chemin = os.path.abspath(os.path.join(POLICES, nom)).encode()
        url = cf.CFURLCreateFromFileSystemRepresentation(
            None, chemin, len(chemin), False)
        if url:
            err = c_void_p()
            ct.CTFontManagerRegisterFontsForURL(url, 1, byref(err))
            cf.CFRelease(url)


def premiere(disponibles, familles):
    for nom in familles:
        if nom in disponibles:
            return nom
    return maitresse


maitresse = "Helvetica"


def police(familles, taille, graisse="normal"):
    """La première famille installée, taille demandée, graisse demandée."""
    return (premiere(_familles(), familles), taille, graisse)


_CACHE = {}


def _familles():
    if "liste" not in _CACHE:
        _CACHE["liste"] = set(tkfont.families())
    return _CACHE["liste"]


def choisir_sans():
    """Fixe la famille par défaut pour toute la fenêtre (une seule)."""
    global maitresse
    maitresse = premiere(_familles(), SANS)
    return maitresse


def sans(taille, graisse="normal"):
    return (maitresse, taille, graisse)


def mono(taille, graisse="normal"):
    return police(MONO, taille, graisse)


ENTETES_CSV = ("nom", "name", "fichier", "nom_fichier", "nom du fichier")


def lire_liste_csv(chemin):
    """Une liste depuis un CSV : [(nom, phrase)].

    Même tolérance que la 1.5.1 : deux colonnes, avec ou sans en-tête, une
    ligne à moitié remplie gardée telle quelle.
    """
    lignes = []
    with open(chemin, encoding="utf-8-sig", newline="") as fichier:
        for morceaux in csv.reader(fichier):
            if not morceaux:
                continue
            nom = morceaux[0].strip()
            phrase = morceaux[1].strip() if len(morceaux) > 1 else ""
            if nom.lower() in ENTETES_CSV:
                continue
            if nom or phrase:
                lignes.append((nom, phrase))
    return lignes


def ecrire_liste_csv(chemin, lignes):
    """Écrit la liste en deux colonnes, sans en-tête : lisible par les deux."""
    with open(chemin, "w", encoding="utf-8", newline="") as fichier:
        ecrivain = csv.writer(fichier)
        for nom, phrase in lignes:
            if nom or phrase:
                ecrivain.writerow([nom, phrase])


def appliquer_niveau(chemin, decibels):
    """Applique un gain en dB au fichier terminé, sans dépasser 1,0.

    Séparé de la fenêtre pour pouvoir être appelé depuis un fil : il ne
    touche à aucun widget.
    """
    if not decibels:
        return
    import numpy as np
    import soundfile as sf

    echantillons, taux = sf.read(chemin, dtype="float32")
    gain = 10 ** (decibels / 20)
    echantillons = np.clip(echantillons * gain, -1.0, 1.0)
    sf.write(chemin, echantillons, taux, format="WAV", subtype="PCM_16")


# ------------------------------------------------------------------
# Texte posé à même la carcasse (pas de rectangle derrière)
# ------------------------------------------------------------------
class TexteFlottant(tk.Canvas):
    def __init__(self, parent, decor, x, y, texte, couleur, fonte, ancre="w",
                 survol=None, commande=None):
        super().__init__(parent, width=decor.width(), height=decor.height(),
                         bg=NOIR, highlightthickness=0, bd=0)
        self._photo = decor
        self.create_image(0, 0, image=decor, anchor="nw")
        largeur = decor.width()
        px = 0 if ancre == "w" else (largeur if ancre == "e" else largeur // 2)
        self._couleur = couleur
        self._survol = survol
        self._texte = self.create_text(px, decor.height() // 2, text=texte,
                                       fill=couleur, font=fonte, anchor=ancre)
        if survol:
            self.bind("<Enter>", lambda e: self.itemconfig(self._texte, fill=self._survol))
            self.bind("<Leave>", lambda e: self.itemconfig(self._texte, fill=self._couleur))
            self.configure(cursor="pointinghand")
        if commande:
            self.bind("<Button-1>", lambda e: commande())
        self.place(x=x, y=y)

    def dire(self, texte):
        self.itemconfig(self._texte, text=texte)


# ------------------------------------------------------------------
# Bouton à coin biaisé
# ------------------------------------------------------------------
class Bouton(tk.Canvas):
    """Un bouton dessiné : coin haut-droit coupé à 45°.

    Deux allures. Pleine (Let's Go) : face teintée, filet cyan, texte blanc.
    Contour (les outils) : pas de fond, filet clair, capitales espacées et
    une icône tracée à droite — les icônes sont dessinées, pas tapées, pour
    ne dépendre d'aucun glyphe.

    `decor` (un morceau de la carcasse) sert de fond au Canvas : le métal
    passe dessous et le bouton ne se découpe pas dans un rectangle plat.
    """

    def __init__(self, parent, texte, x, y, largeur, hauteur, decor=None,
                 fond=CARTE, face=FACE, couleur_texte=TEXTE, biseau=10,
                 fonte=None, commande=None, plein=False, contour=False,
                 icone=None, espace=False):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond,
                         highlightthickness=0, bd=0)
        self.place(x=x, y=y)
        self._commande = commande
        if contour:
            self._face = ""
            self._survol = "#123338"
        else:
            self._face = ACCENT_SOMBRE if plein else face
            self._survol = "#1AA9C0" if plein else "#1B3B44"
        self._bord = "#3E5559" if contour else (ACCENT if plein else BORD)
        self._bord_survol = ACCENT
        c, l, h = biseau, largeur, hauteur
        if decor is not None:
            self._photo = decor
            self.create_image(0, 0, image=decor, anchor="nw")
        self._forme = self.create_polygon(
            1, h - c, c, h - 1, l - 1, h - 1, l - 1, c, l - c, 1, 1, 1,
            fill=self._face, outline=self._bord, width=1)
        if not contour:
            self.create_line(2, h - c, 2, 2, l - c, 2, fill=CLAIR, width=1)
            self.create_line(l - 2, c, l - 2, h - 2, c, h - 2,
                             fill=SOMBRE, width=1)
        # Une coupe haut-droit, une coupe bas-gauche : la même arête cyan
        # sur les deux, ça fait la symétrie.
        self.create_line(l - c, 1, l - 1, c, fill=ACCENT,
                         width=1 if contour else 2)
        self.create_line(1, h - c, c, h - 1, fill=ACCENT,
                         width=1 if contour else 2)
        self._espace = espace
        if espace:
            texte = espacer(texte)
        self._cx, self._cy = l / 2, h / 2
        self._texte = self.create_text(self._cx, self._cy, text=texte,
                                       fill=couleur_texte, font=fonte)
        if icone:
            self._dessiner_icone(icone, l - 17, h / 2)
        self._pointer_dedans = False
        self.bind("<Enter>", self._entrer)
        self.bind("<Leave>", self._sortir)
        self.bind("<ButtonPress-1>", self._enfoncer)
        self.bind("<ButtonRelease-1>", self._relacher)

        # Le bouton s'inscrit auprès de la fenêtre : elle vérifiera son
        # survol à intervalle régulier, pour ne plus dépendre des événements
        # d'entrée et de sortie, qui se perdent parfois.
        fenetre = parent.winfo_toplevel()
        if hasattr(fenetre, "_boutons"):
            fenetre._boutons.append(self)

    def dire(self, texte):
        """Change le libellé, en gardant l'espacement des capitales."""
        if self._espace:
            texte = espacer(texte)
        self.itemconfig(self._texte, text=texte)
        self.coords(self._texte, self._cx, self._cy)

    def _dessiner_icone(self, forme, x, y):
        if forme == "plus":
            self.create_line(x - 6, y, x + 6, y, fill=GRIS)
            self.create_line(x, y - 6, x, y + 6, fill=GRIS)
        elif forme == "moins":
            self.create_line(x - 6, y, x + 6, y, fill=GRIS)
        elif forme == "lecture":
            self.create_polygon(x - 5, y - 6, x - 5, y + 6, x + 6, y,
                                fill=GRIS, outline="")

    def _entrer(self, _event=None):
        self._pointer_dedans = True
        self.itemconfig(self._forme, fill=self._survol,
                        outline=self._bord_survol)
        self.coords(self._texte, self._cx, self._cy)

    def _sortir(self, _event=None):
        # L'état est remis à plat dans tous les cas : même si le clic s'est
        # terminé ailleurs, le bouton ne reste pas allumé.
        self._pointer_dedans = False
        self.itemconfig(self._forme, fill=self._face, outline=self._bord)
        self.coords(self._texte, self._cx, self._cy)

    def _enfoncer(self, _event):
        self.itemconfig(self._forme, fill=PRESSE)
        self.coords(self._texte, self._cx, self._cy + 1)

    def _relacher(self, _event):
        self.coords(self._texte, self._cx, self._cy)
        if self._pointer_dedans:
            self._entrer()
        else:
            self._sortir()
        if self._commande:
            self._commande()




# ------------------------------------------------------------------
# Une case à cocher posée sur la carcasse
# ------------------------------------------------------------------
class CaseACocher(tk.Canvas):
    def __init__(self, parent, decor, x, y, largeur, hauteur, texte, fonte,
                 commande=None, couleur=None):
        super().__init__(parent, width=largeur, height=hauteur, bg=NOIR,
                         highlightthickness=0, bd=0)
        self.place(x=x, y=y)
        self._photo = decor
        self.create_image(0, 0, image=decor, anchor="nw")
        self._commande = commande
        cote = hauteur * 0.5
        haut = (hauteur - cote) / 2
        self._carre = self.create_rectangle(2, haut, 2 + cote, haut + cote,
                                            outline="#3A5A5E", width=1)
        self._couleur = couleur or TEXTE
        self._texte = self.create_text(2 + cote + 9, hauteur / 2, text=texte,
                                       fill=self._couleur, font=fonte, anchor="w")
        self._coche = None
        self._fait = False
        self.configure(cursor="pointinghand")
        self.bind("<Button-1>", self._basculer)
        self.bind("<Enter>", lambda e: self.itemconfig(self._texte, fill=ACCENT))
        self.bind("<Leave>", lambda e: self.itemconfig(
            self._texte, fill=self._couleur))

    def _basculer(self, _event=None):
        self._fait = not self._fait
        if self._fait:
            cote = self.coords(self._carre)
            g, h, d, b = cote[0], cote[1], cote[2], cote[3]
            self._coche = self.create_line(
                g + 4, h + (b - h) / 2, g + (d - g) * 0.45, b - 4,
                d - 3, h + 3, fill=ACCENT, width=2)
            self.itemconfig(self._carre, outline=ACCENT)
        else:
            if self._coche:
                self.delete(self._coche)
                self._coche = None
            self.itemconfig(self._carre, outline="#3A5A5E")
        if self._commande:
            self._commande()


# ------------------------------------------------------------------
# Une petite fenêtre par-dessus l'application
# ------------------------------------------------------------------
class Feuille(ctk.CTkToplevel):
    def __init__(self, parent, titre, largeur, hauteur):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color="#0A1416")
        self.corps = tk.Frame(self, bg="#0A1416",
                              highlightbackground="#4C6469",
                              highlightthickness=1)
        self.corps.pack(fill="both", expand=True)

        haut = tk.Frame(self.corps, bg="#0A1416", height=44)
        haut.pack(fill="x")
        haut.pack_propagate(False)
        tk.Label(haut, text=titre, bg="#0A1416", fg=ACCENT,
                 font=sans(13)).pack(side="left", padx=16)
        croix = tk.Label(haut, text="×", bg="#0A1416", fg=GRIS,
                         font=sans(18), cursor="pointinghand")
        croix.pack(side="right", padx=14)
        croix.bind("<Button-1>", lambda e: self.fermer())
        tk.Frame(self.corps, bg="#1B3336", height=1).pack(fill="x", padx=12)

        self.contenu = tk.Frame(self.corps, bg="#0A1416")
        self.contenu.pack(fill="both", expand=True, padx=16, pady=12)

        x = parent.winfo_rootx() + (parent.winfo_width() - largeur) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - hauteur) // 2
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        self.transient(parent)
        self.lift()
        self.bind("<Escape>", lambda e: self.fermer())
        # La feuille peut être détruite avant que ce minuteur passe (on
        # ferme l'application depuis la fenêtre de soutien) : on protège.
        self.after(50, self._prendre_focus)

    def _prendre_focus(self):
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def fermer(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


class FenetreLangues(Feuille):
    """Le choix de la langue des sons, en grille."""

    def __init__(self, parent, code_courant, choisie):
        super().__init__(parent, parent.mot("titre_langues").upper(), 620, 460)
        self._choisie = choisie

        grille = tk.Frame(self.contenu, bg="#0A1416")
        grille.pack(fill="both", expand=True)
        for colonne in range(3):
            grille.grid_columnconfigure(colonne, weight=1, uniform="langue")

        # Le nom s'écrit dans la langue elle-même : un Japonais qui ouvre cette
        # fenêtre doit y reconnaître la sienne, quelle que soit la langue de
        # l'interface. C'est aussi quinze traductions de moins.
        for i, langue in enumerate(LANGUES):
            ici = langue.code == code_courant
            cellule = tk.Frame(grille, bg="#0D1A1C", cursor="pointinghand",
                               highlightthickness=1,
                               highlightbackground="#1B3336")
            cellule.grid(row=i // 3, column=i % 3, sticky="nsew", padx=3, pady=3)
            if ici:
                cellule.configure(highlightbackground=ACCENT)

            titre = tk.Label(cellule, text=langue.nom, bg="#0D1A1C",
                             fg=ACCENT if ici else TEXTE,
                             font=sans(13), anchor="w")
            titre.pack(fill="x", padx=10, pady=(7, 0))
            detail = tk.Label(cellule, text=langue.phrase(),
                              bg="#0D1A1C", fg=GRIS, font=sans(10), anchor="w")
            detail.pack(fill="x", padx=10, pady=(0, 7))

            for morceau in (cellule, titre, detail):
                morceau.bind("<Enter>", lambda e, c=cellule: c.configure(bg="#14313A"))
                morceau.bind("<Leave>", lambda e, c=cellule: c.configure(bg="#0D1A1C"))
                morceau.bind("<Button-1>",
                             lambda e, c=langue.code: self._prendre(c))

    def _prendre(self, code):
        self._choisie(code)
        self.fermer()


class FenetreSysteme(Feuille):
    """Créer les sons système de la langue, pour de vrai.

    Même mécanique que la fenêtre principale : le travail se fait dans un
    fil, les nouvelles passent par une file, la fenêtre lit à intervalle
    court. On peut arrêter en route ; les fichiers déjà faits restent.

    Les sons viennent du CSV officiel de la langue (dossier `SYSTEM`
    seulement) : c'est la liste d'EdgeTX, téléchargée à l'usage.
    """

    def __init__(self, parent, code):
        self.langue = donner_langue(code)
        self.voix = getattr(parent, "_voix_id", self.langue.voix)
        self.allure = getattr(parent, "_vitesse", None)
        self.allure = self.allure._valeur if self.allure else self.langue.pour_cent
        super().__init__(parent, parent.mot("titre_sons").upper(), 520, 300)
        self._mot = parent.mot
        self._en_cours = False
        self._arret = False
        self._faits = 0
        self._total = 0
        # Le dossier choisi par l'utilisateur, sinon celui de la maquette.
        self.dossier = os.path.join(parent._dossier_sortie(),
                                    "systeme-" + self.langue.code)
        cible = os.path.join(self.dossier, "SYSTEM")

        t = self.contenu
        tk.Label(t, text=self._mot("creer_titre", langue=self.langue.nom),
                 bg="#0A1416", fg=TEXTE, font=sans(14),
                 anchor="w").pack(fill="x")
        tk.Label(t, text=self._mot("creer_detail", dossier=self.langue.dossier),
                 bg="#0A1416", fg=GRIS, font=sans(11),
                 anchor="w").pack(fill="x", pady=(2, 12))

        tk.Label(t, text=self._mot("dossier_sortie"), bg="#0A1416", fg=GRIS,
                 font=sans(10), anchor="w").pack(fill="x")
        champ = tk.Entry(t, bg=NOIR, fg=TEXTE, font=sans(11), relief="flat",
                         insertbackground=TEXTE)
        champ.insert(0, cible)
        champ.configure(state="readonly", readonlybackground=NOIR)
        champ.pack(fill="x", ipady=6, pady=(4, 10))

        self._etat = tk.Label(t, text="", bg="#0A1416", fg=GRIS,
                              font=sans(11), anchor="w")
        self._etat.pack(fill="x", pady=(0, 8))

        bas = tk.Frame(t, bg="#0A1416")
        bas.pack(fill="x", side="bottom")
        tk.Label(bas, text=self._mot("annuler"), bg="#0A1416", fg=GRIS,
                 font=sans(12), cursor="pointinghand").pack(side="right",
                                                            padx=12)
        self._bouton = tk.Label(bas, text=self._mot("creer_fichiers"),
                                bg="#0B4A55", fg=TEXTE, font=sans(12),
                                padx=14, pady=6, cursor="pointinghand")
        self._bouton.pack(side="right")
        self._bouton.bind("<Button-1>", self._creer)

    # -- la fabrication ------------------------------------------------
    def _creer(self, _event=None):
        if self._en_cours:
            self._arret = True
            self._etat.configure(text=self._mot("arreter") + "…")
            return
        self._en_cours = True
        self._arret = False
        self._faits = 0
        self._file = queue.Queue()
        self._etat.configure(text=self._mot("preparation"))
        threading.Thread(target=self._fabriquer, daemon=True).start()
        self.after(120, self._surveiller)

    def _fabriquer(self):
        import voxpack as moteur

        try:
            sons = sons_systeme(self.langue)
        except Exception as erreur:
            self._file.put(("erreur", str(erreur)[:100]))
            return
        os.makedirs(os.path.join(self.dossier, "SYSTEM"), exist_ok=True)
        total = len(sons)
        self._file.put(("total", total))
        allure = 1 + self.allure / 100
        d_affilee = 0
        for numero, (nom, phrase) in enumerate(sons, start=1):
            if self._arret:
                break
            self._file.put(("etape", numero, total, phrase))
            try:
                mp3 = os.path.join(self.dossier, ".%s.mp3" % nom)
                wav = os.path.join(self.dossier, ".%s.wav.tmp" % nom)
                asyncio.run(moteur.sauver_voix(
                    phrase, self.voix, mp3,
                    rate=("+" if allure >= 1 else "-")
                         + "%d%%" % abs(round((allure - 1) * 100)),
                    pitch=self.langue.hauteur or "+0Hz"))
                moteur.convertir_en_wav(mp3, wav)
                os.remove(mp3)
                moteur.ameliorer_niveau_wav(wav)
                # Temporaire puis déplacement : jamais de WAV tronqué.
                os.replace(wav, os.path.join(self.dossier, "SYSTEM",
                                             nom + ".wav"))
                self._faits += 1
                d_affilee = 0
            except Exception as erreur:
                d_affilee += 1
                self._file.put(("erreur", "%s : %s" % (nom, str(erreur)[:60])))
                if d_affilee >= 3:
                    break
        self._file.put(("fini", self._faits, total))

    def _surveiller(self):
        try:
            while True:
                nouvelle = self._file.get_nowait()
                genre = nouvelle[0]
                if genre == "total":
                    self._total = nouvelle[1]
                elif genre == "etape":
                    _, numero, total, phrase = nouvelle
                    self._etat.configure(text=self._mot(
                        "fabrication", i=numero, n=total, phrase=phrase))
                elif genre == "erreur":
                    self._etat.configure(text=nouvelle[1])
                elif genre == "fini":
                    _, faits, total = nouvelle
                    self._en_cours = False
                    if faits == total:
                        self._etat.configure(text=self._mot("termine", n=faits))
                    else:
                        # Un échec ne doit pas être effacé par la fin : on
                        # garde le dernier message, qui dit ce qui a coincé.
                        self._etat.configure(
                            text="%d / %d — %s" % (faits, total, self._etat.cget("text")))
                    self._bouton.configure(text=self._mot("creer_fichiers"))
                    return
        except queue.Empty:
            pass
        if self._en_cours:
            self.after(120, self._surveiller)

    def fermer(self):
        self._arret = True
        super().fermer()


KO_FI = "https://ko-fi.com/ritchy_lab"
SITE = "https://ritchy-lab.github.io/"


class FenetreSoutien(Feuille):
    """La petite fenêtre de soutien, à la fermeture.

    Elle tutoie volontairement en français, alors que le reste de
    l'application vouvoie : c'est un choix de Richard, ne pas l'aligner.
    « Offre-moi un café » ouvre Ko-fi **et** arrête les questions ;
    « Ne plus demander » les arrête sans ouvrir ; « Pas maintenant » ne
    retient rien, on la reverra.
    """

    def __init__(self, parent, apres):
        super().__init__(parent, parent.mot("soutien_titre").upper(), 460, 250)
        self.app = parent
        self._apres = apres
        t = self.contenu

        tk.Label(t, text=parent.mot("soutien_texte"), bg="#0A1416", fg=TEXTE,
                 font=sans(13), wraplength=420, justify="left",
                 anchor="w").pack(fill="x", pady=(2, 14))

        bas = tk.Frame(t, bg="#0A1416")
        bas.pack(fill="x", side="bottom")
        for texte, action, principal in (
                (parent.mot("soutien_cafe"), self._cafe, True),
                (parent.mot("soutien_jamais"), self._jamais, False),
                (parent.mot("soutien_non"), self._plus_tard, False)):
            if principal:
                etiquette = tk.Label(bas, text=texte, bg="#0B4A55", fg=TEXTE,
                                     font=sans(12), padx=14, pady=7,
                                     cursor="pointinghand")
            else:
                etiquette = tk.Label(bas, text=texte, bg="#0A1416", fg=GRIS,
                                     font=sans(11), cursor="pointinghand")
            etiquette.pack(side="right", padx=10)
            etiquette.bind("<Button-1>", lambda e, a=action: a())

    def _cafe(self):
        import webbrowser
        webbrowser.open(KO_FI)
        self._jamais()

    def _jamais(self):
        self.app._reglages["soutien_ne_plus"] = True
        ecrire_reglages(self.app._reglages)
        self._plus_tard()

    def _plus_tard(self):
        self.fermer()
        self._apres()


class FenetreMiseAJour(Feuille):
    """Annonce une version plus récente : télécharger, ou plus tard.

    Comme dans la 1.5.1, elle s'ouvre **une fois au démarrage**, et elle est
    silencieuse hors ligne : pas de fenêtre d'erreur, on réessaiera demain.
    """

    def __init__(self, parent, nouvelle, actuelle, page):
        super().__init__(parent, parent.mot("maj_titre").upper(), 480, 230)
        self._page = page
        t = self.contenu
        tk.Label(t, text=parent.mot("maj_texte", nouvelle=nouvelle,
                                    actuelle=actuelle),
                 bg="#0A1416", fg=TEXTE, font=sans(13), wraplength=430,
                 justify="left", anchor="w").pack(fill="x", pady=(2, 16))

        bas = tk.Frame(t, bg="#0A1416")
        bas.pack(fill="x", side="bottom")
        telecharger = tk.Label(bas, text=parent.mot("maj_telecharger"),
                               bg="#0B4A55", fg=TEXTE, font=sans(12),
                               padx=14, pady=7, cursor="pointinghand")
        telecharger.pack(side="right")
        telecharger.bind("<Button-1>", lambda e: self._telecharger())
        plus_tard = tk.Label(bas, text=parent.mot("maj_plus_tard"),
                             bg="#0A1416", fg=GRIS, font=sans(11),
                             cursor="pointinghand")
        plus_tard.pack(side="right", padx=12)
        plus_tard.bind("<Button-1>", lambda e: self.fermer())

    def _telecharger(self):
        import webbrowser
        webbrowser.open(self._page)
        self.fermer()


class FenetreAide(Feuille):
    """L'aide courte de la v2 : cinq phrases, pas un manuel.

    Elle dit ce que fait chaque commande et la seule contrainte qu'on ne
    devine pas — les huit caractères du nom de fichier. Le reste, la 1.5.1
    le racontait longuement ; ici, c'est une maquette.
    """

    def __init__(self, parent):
        super().__init__(parent, parent.mot("aide_titre").upper(), 560, 420)
        texte = tk.Text(self.contenu, bg="#0A1416", fg=TEXTE, font=sans(12),
                        wrap="word", bd=0, highlightthickness=0, cursor="arrow",
                        spacing1=2, spacing3=14, padx=2)
        for numero in range(1, 6):
            texte.insert("end", "—   " + parent.mot("aide_%d" % numero) + "\n")
        texte.configure(state="disabled")
        texte.pack(fill="both", expand=True)


# ------------------------------------------------------------------
# Barre fine : progression, et niveau du son
# ------------------------------------------------------------------
class Barre(tk.Canvas):
    """Une barre fine. En mode `degrade`, elle passe du cyan au rouge : le
    niveau du son se lit d'un coup d'œil, et le bout de la barre vire au
    rouge quand on approche du maximum."""

    CYAN = (15, 187, 208)
    JAUNE = (233, 190, 62)
    ROUGE = (214, 62, 52)

    def __init__(self, parent, decor, x, y, largeur, hauteur, fond=BANDE,
                 valeur=0.5, degrade=False):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond,
                         highlightthickness=0, bd=0)
        self.place(x=x, y=y)
        self._l, self._h = largeur, hauteur
        self._degrade = degrade
        self._photo = decor
        self.create_image(0, 0, image=decor, anchor="nw")
        self.create_rectangle(0, 0, largeur - 1, hauteur - 1,
                              outline="#33545A", width=1, fill="#0B1417")
        self._morceaux = []
        self.remplir(valeur)

    def _couleur(self, fraction):
        a, b = self.CYAN, self.JAUNE
        if fraction > 0.6:
            a, b = self.JAUNE, self.ROUGE
            fraction = (fraction - 0.6) / 0.4
        else:
            fraction = fraction / 0.6
        return "#%02X%02X%02X" % tuple(
            int(a[i] + (b[i] - a[i]) * fraction) for i in range(3))

    def remplir(self, valeur):
        valeur = max(0.0, min(1.0, valeur))
        for morceau in self._morceaux:
            self.delete(morceau)
        self._morceaux = []
        largeur = int((self._l - 2) * valeur)
        if self._degrade:
            for i in range(largeur):
                couleur = self._couleur(i / max(1, self._l - 2))
                self._morceaux.append(self.create_line(
                    1 + i, 1, 1 + i, self._h - 1, fill=couleur))
        elif largeur >= 3:
            # Une jauge pleine, avec une arête claire en haut, une sombre en
            # bas et une tête plus vive : trois traits, et elle prend du relief.
            fin = largeur
            self._morceaux.append(self.create_rectangle(
                1, 1, fin, self._h - 1, outline="", fill="#2FD3E2"))
            self._morceaux.append(self.create_line(
                1, 1, fin - 1, 1, fill="#9BEDF4"))
            self._morceaux.append(self.create_line(
                1, self._h - 2, fin - 1, self._h - 2, fill="#087A86"))
            self._morceaux.append(self.create_line(
                fin - 1, 2, fin - 1, self._h - 2, fill="#D6FBFF"))
        else:
            self._morceaux.append(self.create_rectangle(
                1, 1, max(2, largeur), self._h - 1, outline="",
                fill="#2FD3E2"))


# ------------------------------------------------------------------
# Curseur de niveau : on tire vers la gauche pour baisser, vers la
# droite pour monter. Le milieu, c'est 0 dB — le fichier tel quel.
# ------------------------------------------------------------------
CYAN_VIF = (15, 187, 208)
JAUNE_VIF = (233, 190, 62)
ROUGE_VIF = (214, 62, 52)
BAISSE = "#1B6C79"      # le cyan éteint, pour les valeurs négatives


def melange(c1, c2, fraction):
    return "#%02X%02X%02X" % tuple(
        int(c1[i] + (c2[i] - c1[i]) * fraction) for i in range(3))


def couleur_gain(fraction):
    """Du cyan au rouge en passant par le jaune, selon la valeur absolue."""
    if fraction <= 0.6:
        return melange(CYAN_VIF, JAUNE_VIF, fraction / 0.6)
    return melange(JAUNE_VIF, ROUGE_VIF, (fraction - 0.6) / 0.4)


class Curseur(tk.Canvas):
    def __init__(self, parent, decor, x, y, largeur, hauteur, fond=CARTE,
                 mini=-12, maxi=12, valeur=0, commande=None, degrade=True):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond,
                         highlightthickness=0, bd=0)
        self.place(x=x, y=y)
        self._l, self._h = largeur, hauteur
        self._mini, self._maxi = mini, maxi
        self._commande = commande
        self._photo = decor
        self.create_image(0, 0, image=decor, anchor="nw")

        self._degrade = degrade
        self._marge = largeur * 0.07
        milieu = hauteur / 2
        self._milieu = milieu
        self._demi_piste = 3

        # La piste garde le dégradé cyan → jaune → rouge : le sens et la
        # zone dangereuse se lisent sans bouger le curseur. On la dessine
        # une fois, atténuée, puis on rallume le trajet parcouru.
        self._piste = []
        for i in range(int(self._marge), int(largeur - self._marge) + 1):
            self._piste.append(self.create_line(
                i, milieu - self._demi_piste, i, milieu + self._demi_piste,
                fill=self._attenue(self._teinte(i))))

        # Le relief de la piste : une arête claire dessus, une sombre dessous.
        self.create_line(self._marge, milieu - self._demi_piste,
                         largeur - self._marge, milieu - self._demi_piste,
                         fill="#6E8A8F")
        self.create_line(self._marge, milieu + self._demi_piste,
                         largeur - self._marge, milieu + self._demi_piste,
                         fill="#08110F")

        centre = self._x_pour(0)
        self.create_line(centre, milieu - 11, centre, milieu + 11,
                         fill="#4E6E74", width=1)

        # La poignée a l'allure des boutons : face sombre, filet clair,
        # deux coupes biaisées — et elle ne change pas de couleur.
        self._parcouru = []
        self._poignee = self.create_polygon(
            0, 0, fill="#2A3C41", outline="#5E7A7F", width=1)
        self._dessus = self.create_rectangle(0, 0, 0, 0, fill="#4E666C",
                                             outline="")
        self._arete_haut = self.create_line(0, 0, 0, 0, fill="#8FB3B8")
        self._arete_bas = self.create_line(0, 0, 0, 0, fill="#0A1315")
        self._coin_haut = self.create_line(0, 0, 0, 0, fill=ACCENT)
        self._coin_bas = self.create_line(0, 0, 0, 0, fill=ACCENT)
        # La main blanche de macOS, celle de la version 1.
        self.configure(cursor="pointinghand")
        self.bind("<Button-1>", self._clic)
        self.bind("<B1-Motion>", self._glisser)
        self._valeur = None
        self.regler(valeur, prevenir=False)

    def _teinte(self, x):
        if not self._degrade:
            return "#4FD8E6"
        part = (x - self._marge) / (self._l - 2 * self._marge)
        return couleur_gain(max(0.0, min(1.0, part)))

    @staticmethod
    def _attenue(couleur):
        """La même teinte, atténuée : la piste reste lisible sans crier."""
        r = int(couleur[1:3], 16) * 0.8
        v = int(couleur[3:5], 16) * 0.8
        b = int(couleur[5:7], 16) * 0.8
        return "#%02X%02X%02X" % (int(r), int(v), int(b))

    def _x_pour(self, valeur):
        part = (valeur - self._mini) / (self._maxi - self._mini)
        return self._marge + part * (self._l - 2 * self._marge)

    def _valeur_pour(self, x):
        part = (x - self._marge) / (self._l - 2 * self._marge)
        valeur = self._mini + part * (self._maxi - self._mini)
        return max(self._mini, min(self._maxi, round(valeur)))

    def regler(self, valeur, prevenir=True):
        valeur = max(self._mini, min(self._maxi, valeur))
        if valeur == self._valeur:
            return
        self._valeur = valeur
        x = self._x_pour(valeur)
        centre = self._x_pour(0)
        milieu = self._milieu

        # On rallume le trajet parcouru depuis 0 dB, dans la teinte de la
        # piste : le curseur se pose sur une couleur, il ne l'invente pas.
        for trait in self._parcouru:
            self.delete(trait)
        self._parcouru = []
        for i in range(int(min(x, centre)), int(max(x, centre)) + 1):
            self._parcouru.append(self.create_line(
                i, milieu - self._demi_piste, i, milieu + self._demi_piste,
                fill=self._teinte(i)))

        y, d, h, c = milieu, 6, 10, 4
        self.coords(self._poignee,
                    x - d, y - h, x + d - c, y - h, x + d, y - h + c,
                    x + d, y + h, x - d, y + h, x - d, y + h - c)
        self.coords(self._coin_haut, x + d - c, y - h, x + d, y - h + c)
        self.coords(self._coin_bas, x - d, y + h - c, x - d + c, y + h)
        self.coords(self._dessus, x - d + 1, y - h + 1, x + d - c, y - h + 4)
        self.coords(self._arete_haut, x - d + 1, y - h + 1, x + d - c - 1, y - h + 1)
        self.coords(self._arete_bas, x - d + 1, y + h - 1, x + d - 1, y + h - 1)
        for item in (self._poignee, self._dessus, self._coin_haut,
                     self._coin_bas):
            self.tag_raise(item)
        if prevenir and self._commande:
            self._commande(valeur)

    def _clic(self, evenement):
        self.regler(self._valeur_pour(evenement.x))

    def _glisser(self, evenement):
        self.regler(self._valeur_pour(evenement.x))


# ------------------------------------------------------------------
class Maquette(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.suivant = None
        self.title("Vox-Pack — maquette v2")
        self.configure(fg_color=NOIR)
        choisir_sans()

        self._listes_editees = lire_listes()
        self._ligne_active = 0
        self._reglages = lire_reglages()
        self._langue = self._reglages.get("langue", "fr")
        if self._langue not in PAR_CODE:
            self._langue = "fr"
        self._pret = False
        self._soutien_ouvert = False
        self._boutons = []
        self.k = FORMAT / 1024
        self.largeur = FORMAT
        x = (self.winfo_screenwidth() - FORMAT) // 2
        y = max(20, (self.winfo_screenheight() - FORMAT) // 2 - 10)
        self.geometry(f"{FORMAT}x{FORMAT}+{x}+{y}")
        # La fenêtre peut être reposée par le système : on la recale une fois
        # affichée, sinon le bas passe sous l'écran.
        self.after(80, lambda: self.geometry(f"+{x}+{y}"))
        self.resizable(False, False)
        # Pas de barre de titre : c'est l'habillage qui fait la fenêtre.
        # Tk refuse alors la réduction (macOS ne minimise pas une fenêtre
        # sans cadre) ; le bouton jaune n'a donc rien à faire.
        self.overrideredirect(True)
        self.lift()
        self.attributes("-topmost", True)
        self.after(1200, lambda: self.attributes("-topmost", False))
        self.focus_force()

        self._construire()
        self._pret = True
        self.after(300, self._veiller_survol)

    def _veiller_survol(self):
        """Vérifie le survol des boutons, sans dépendre des événements Tk."""
        x, y = self.winfo_pointerxy()
        for bouton in list(self._boutons):
            if not bouton.winfo_exists():
                continue
            dedans = (bouton.winfo_rootx() <= x < bouton.winfo_rootx() + bouton.winfo_width()
                      and bouton.winfo_rooty() <= y < bouton.winfo_rooty() + bouton.winfo_height())
            if dedans != bouton._pointer_dedans:
                bouton._entrer() if dedans else bouton._sortir()
        self.after(220, self._veiller_survol)

    def _construire(self):
        """Dessine tout le contenu, à l'échelle courante."""
        self._boutons = []
        self._poser_carcasse()
        self._panneau()
        self._carte()
        self._liste()
        self._bandeau()
        self._plaque()
        self._fenetre()

    # -- la molette, quand le pointeur est au-dessus de la liste -------
    def _molette(self, evenement):
        """Un cran de molette = un dixième de la hauteur visible.

        On ne demande pas « une unité » à Tk : selon la plateforme elle vaut
        dix pour cent ou la moitié de la liste. On calcule la fraction.
        """
        toile = self._liste_cadre._parent_canvas
        haut, bas = toile.yview()
        hauteur = bas - haut
        cran = hauteur * 0.1
        sens = -1 if evenement.delta > 0 else 1
        toile.yview_moveto(max(0.0, min(1.0 - hauteur, haut + sens * cran)))
        return "break"

    # -- déplacement de la fenêtre sans barre de titre ----------------
    def _prendre(self, evenement):
        self._dx = evenement.x_root - self.winfo_x()
        self._dy = evenement.y_root - self.winfo_y()

    def _tirer(self, evenement):
        self.geometry(f"+{evenement.x_root - self._dx}+{evenement.y_root - self._dy}")

    # -- outils ------------------------------------------------------
    def t(self, valeur):
        return max(1, int(round(valeur * self.k)))

    def mot(self, cle, **valeurs):
        """Le texte de l'interface, dans la langue courante.

        Esquisse seulement : l'application, elle, part de ses tables
        fusionnées (1.5.1 + lots) et de son `t()`. Ici, un trou dans une
        langue retombe sur l'anglais, puis sur le français, puis sur la clé.
        """
        morceau = (TEXTES.get(self._langue, {}).get(cle)
                   or TEXTES["en"].get(cle)
                   or TEXTES["fr"].get(cle)
                   or cle)
        try:
            return morceau.format(**valeurs)
        except (KeyError, IndexError):
            return morceau

    def decor(self, x, y, l, h):
        g, ht = self.t(x), self.t(y)
        return ImageTk.PhotoImage(
            self.fond_image.crop((g, ht, g + self.t(l), ht + self.t(h))))

    def texte(self, x, y, l, h, contenu, couleur, fonte, ancre="w",
              survol=None, commande=None):
        return TexteFlottant(self, self.decor(x, y, l, h), self.t(x), self.t(y),
                             contenu, couleur, fonte, ancre, survol, commande)

    def _poser_carcasse(self):
        image = Image.open(CARCASSE)
        if self.k != 1:
            image = image.resize((FORMAT, FORMAT), Image.LANCZOS)
        self.fond_image = image
        self.photo = ImageTk.PhotoImage(image)
        fond = tk.Label(self, image=self.photo, bd=0, highlightthickness=0)
        fond.place(x=0, y=0, width=FORMAT, height=FORMAT)
        fond.bind("<ButtonPress-1>", self._prendre)
        fond.bind("<B1-Motion>", self._tirer)
        self.bind("<Escape>", lambda e: self.destroy())

    # -- les trois pastilles en haut à gauche, l'aide en bas à droite --
    def _fenetre(self):
        """Deux pastilles, à leur place d'origine : fermer, agrandir.

        Les mesures sont celles d'Apple — 12 points de diamètre, 8 points
        d'écart, 20 points du bord — mais remises là où elles étaient.
        """
        t = self.t
        decor = self.decor(64, 34, 120, 44)
        ligne = tk.Canvas(self, width=decor.width(), height=decor.height(),
                          bg=BANDE, highlightthickness=0, bd=0)
        self._decor_fenetre = decor
        ligne.create_image(0, 0, image=decor, anchor="nw")

        rayon = t(8)
        for i, (couleur, action) in enumerate(
                (("#E2564B", self._fermer), ("#5FC47F", self._agrandir))):
            cx = t(20) + i * t(30)
            cercle = ligne.create_oval(cx - rayon, t(18) - rayon,
                                       cx + rayon, t(18) + rayon,
                                       fill=couleur, outline="")
            ligne.tag_bind(cercle, "<Button-1>", lambda e, a=action: a())
        ligne.place(x=t(64), y=t(34))

        # La case « Son système », juste au-dessus de LANGUE.
        CaseACocher(self, self.decor(64, 110, 200, 36), t(64), t(110),
                    t(200), t(36), self.mot("sons_system"), sans(t(17)),
                    commande=self._ouvrir_systeme, couleur=ACCENT)

        # L'aide a pris la place des pastilles : en bas à droite.
        # Le menu et l'aide, en bas à droite : deux carrés jumeaux.
        self._bouton_menu()
        Bouton(self, "?", t(930), t(912), t(42), t(42),
               decor=self.decor(930, 912, 42, 42), fond=BANDE,
               couleur_texte=TEXTE, fonte=sans(t(24), "bold"), biseau=9,
               commande=self._ouvrir_aide)

    def _bouton_menu(self):
        """Trois traits : le menu de l'application, dessiné, pas tapé."""
        t = self.t
        decor = self.decor(872, 912, 42, 42)
        canevas = tk.Canvas(self, width=decor.width(), height=decor.height(),
                            bg=BANDE, highlightthickness=0, bd=0)
        self._decor_menu = decor
        canevas.create_image(0, 0, image=decor, anchor="nw")
        largeur = t(7)
        cx = cy = decor.width() / 2
        for rang in (-1, 0, 1):
            canevas.create_line(cx - largeur, cy + rang * t(3.2),
                                cx + largeur, cy + rang * t(3.2),
                                fill=TEXTE, width=1.5)
        canevas.configure(cursor="pointinghand")
        canevas.bind("<Button-1>", lambda e: self._ouvrir_menu())
        canevas.place(x=t(872), y=t(912))

    def _ouvrir_menu(self):
        """Un panneau posé dans la fenêtre, comme le menu des voix.

        Pas de menu système : la fenêtre n'a pas de barre de titre.
        """
        if getattr(self, "_menu_outils", None):
            self._fermer_menus()
            return
        t = self.t
        entrees = [
            (self.mot("menu_importer"), self._importer_liste),
            (self.mot("menu_exporter"), self._exporter_liste),
            (self.mot("menu_sortie"), self._choisir_sortie),
            (self.mot("menu_dossier"), self._ouvrir_sorties),
            (self.mot("aide_titre"), self._ouvrir_aide),
            (self.mot("menu_quitter"), self._fermer),
        ]
        hauteur = len(entrees) * 34 + 8
        menu = tk.Frame(self, bg="#0A1416", highlightbackground="#3E5559",
                        highlightthickness=1)
        menu.place(x=t(560), y=t(912) - t(hauteur) - t(6),
                   width=t(378), height=t(hauteur))
        for texte, action in entrees:
            ligne = tk.Label(menu, text=texte, bg="#0A1416", fg=TEXTE,
                             anchor="w", font=sans(t(15)), padx=t(12),
                             cursor="pointinghand")
            ligne.pack(fill="x", pady=1)
            ligne.bind("<Enter>", lambda e, l=ligne: l.configure(bg="#14313A"))
            ligne.bind("<Leave>", lambda e, l=ligne: l.configure(bg="#0A1416"))
            ligne.bind("<Button-1>", lambda e, a=action: (self._fermer_menus(), a()))
        self._menu_outils = menu

    def _fermer_menus(self, _event=None):
        menu = getattr(self, "_menu_outils", None)
        if menu and menu.winfo_exists():
            menu.destroy()
        self._menu_outils = None

    def _importer_liste(self, chemin=None):
        """Remplace la liste par un CSV choisi."""
        if chemin is None:
            chemin = filedialog.askopenfilename(
                title=self.mot("menu_importer"),
                filetypes=[("CSV", "*.csv"), ("Tous les fichiers", "*.*")])
        if not chemin:
            return
        try:
            lignes = lire_liste_csv(chemin)
        except Exception as erreur:
            self._message.dire(str(erreur)[:60])
            return
        if not lignes:
            return
        self._phrases = lignes
        self._ligne_active = 0
        self._remplir_liste()
        self._colorer()
        self._compteur.dire(f"0 / {len(self._lignes_a_fabriquer())}")
        self._message.dire(self.mot("liste_importee", n=len(lignes)))

    def _exporter_liste(self, chemin=None):
        """Écrit la liste courante dans un CSV, telle qu'elle est à l'écran."""
        if chemin is None:
            chemin = filedialog.asksaveasfilename(
                title=self.mot("menu_exporter"), defaultextension=".csv",
                initialfile=f"liste_{self._langue}.csv",
                filetypes=[("CSV", "*.csv")])
        if not chemin:
            return
        try:
            ecrire_liste_csv(chemin, self._lire_liste())
        except Exception as erreur:
            self._message.dire(str(erreur)[:60])
            return
        self._message.dire(self.mot("liste_exportee"))

    def _dossier_sortie(self):
        """Le dossier où écrit l'application, choisi par l'utilisateur."""
        choisi = self._reglages.get("sortie")
        if choisi and os.path.isdir(choisi):
            return choisi
        return SORTIES

    def _choisir_sortie(self):
        """Demande un dossier et le retient pour les prochaines fois."""
        dossier = filedialog.askdirectory(title=self.mot("menu_sortie"))
        if not dossier:
            return
        os.makedirs(dossier, exist_ok=True)
        self._reglages["sortie"] = dossier
        ecrire_reglages(self._reglages)

    def _ouvrir_sorties(self):
        """Montre le dossier où les fichiers ont été écrits."""
        try:
            os.makedirs(SORTIES, exist_ok=True)
            import subprocess
            subprocess.Popen(["open", SORTIES])
        except Exception:
            pass

    def _ouvrir_site(self):
        """La signature ouvre le site des trois applications."""
        import webbrowser
        webbrowser.open(SITE)

    def _ouvrir_soutien(self):
        """Le lien Ko-fi ouvre la petite fenêtre, pas le navigateur.

        Décision de la 1.5.1 : c'est la fenêtre qui propose ensuite Ko-fi.
        """
        self._soutien_ouvert = True
        FenetreSoutien(self, self.destroy)

    def _ouvrir_aide(self):
        FenetreAide(self)

    def _memoriser_liste(self):
        """Retient la liste retouchée — et rien si elle est restée d'origine.

        Garder une copie fidèle de la liste d'EdgeTX empêcherait de profiter
        de ses corrections : on n'enregistre donc que ce qui a été changé.
        """
        if not getattr(self, "_entrees_nom", None):
            return
        code = self._langue
        retouchee = self._lire_liste()
        if retouchee == list(self._liste_officielle(code)):
            self._listes_editees.pop(code, None)
        else:
            self._listes_editees[code] = retouchee
        ecrire_listes({c: [list(paire) for paire in lignes]
                       for c, lignes in self._listes_editees.items()})

    def _enregistrer(self):
        """Retient l'état courant pour la prochaine ouverture."""
        if not getattr(self, "_pret", False):
            return          # pendant la construction, rien n'est choisi
        ecrire_reglages({
            "langue": self._langue,
            "voix": getattr(self, "_voix_id", ""),
            "vitesse": self._vitesse._valeur,
            "niveau": self._niveau._valeur,
            "robot": self._choisir_robot_numero(),
        })

    def _choisir_robot_numero(self):
        """Le numéro du robot coché (1 à 4) ; 0 si aucun."""
        for i, case in enumerate(self._robots):
            if case.get():
                return i + 1
        return 0

    def _fermer(self):
        """Ferme, en passant par la fenêtre de soutien.

        Le bouton rouge, le menu et Échap passent tous par ici. Si Richard
        a dit « ne plus demander », on ferme directement ; si la fenêtre est
        déjà ouverte, inutile de la montrer deux fois.
        """
        self._enregistrer()
        self._memoriser_liste()
        if self._reglages.get("soutien_ne_plus") or self._soutien_ouvert:
            self.destroy()
            return
        self._soutien_ouvert = True
        FenetreSoutien(self, self.destroy)

    def _agrandir(self):
        """Agrandit ou rapetisse : on redessine tout, à la même place.

        Détruire la fenêtre pour en ouvrir une autre ne marche pas — Tk ne
        recrée pas proprement un interpréteur après coup. On vide donc le
        contenu et on le redessine à la nouvelle échelle.
        """
        global FORMAT
        FORMAT = 1000 if self.largeur < 1000 else 820
        self.k = FORMAT / 1024
        if self._attente:
            self.after_cancel(self._attente)
            self._attente = None
        for enfant in self.winfo_children():
            enfant.destroy()
        self.largeur = FORMAT
        self.geometry(f"{FORMAT}x{FORMAT}+{self.winfo_rootx()}+{self.winfo_rooty()}")
        self._construire()

    # -- colonne de gauche : langue et voix ---------------------------
    def _panneau(self):
        t = self.t
        self.texte(64, 196, 230, 22, self.mot("langue").upper(), ACCENT,
                   sans(t(15)))
        self._langue_affichee = self._champ(
            64, 222, donner_langue(self._langue).nom, self._ouvrir_langues)

        self.texte(64, 274, 230, 22, self.mot("voix").upper(), ACCENT,
                   sans(t(15)))
        self._voix_id = self._reglages.get("voix") or ""
        if self._voix_id not in voix_de(self._langue):
            self._voix_id = donner_langue(self._langue).voix
        self._voix_affichee = self._champ(
            64, 300, nom_voix(self._voix_id), self._ouvrir_voix,
            fleche=False)

    def _champ(self, x, y, valeur, action=None, fleche=True):
        """Un écran : fond noir, la valeur à gauche, un triangle cyan à droite.

        Sans triangle, toute la zone reste cliquable : pour la voix, le nom
        peut être long, et une flèche finirait par passer dessus.
        """
        t = self.t
        cadre = tk.Frame(self, bg=NOIR)
        cadre.place(x=t(x), y=t(y), width=t(230), height=t(40))
        texte = tk.Label(cadre, text=valeur, bg=NOIR, fg=TEXTE, anchor="w",
                         font=sans(t(17)))
        texte.place(x=t(12), y=0, relheight=1)

        morceaux = [cadre, texte]
        if fleche:
            triangle = tk.Canvas(cadre, width=t(14), height=t(10), bg=NOIR,
                                 highlightthickness=0, bd=0)
            triangle.place(relx=1.0, x=-t(14), rely=0.5, anchor="e")
            triangle.create_polygon(0, 0, t(14), 0, t(7), t(10),
                                    fill=ACCENT, outline="")
            morceaux.append(triangle)
        if action:
            for morceau in morceaux:
                morceau.bind("<Button-1>", lambda e: action())
                morceau.configure(cursor="pointinghand")
        return texte

    def _ouvrir_voix(self):
        """Un menu posé dans la fenêtre, sous le champ : on choisit, il part.

        Une fenêtre à part serait plus pratique à coder mais elle se bat
        avec la fenêtre sans cadre ; ici, le menu n'est qu'un cadre posé
        par-dessus les autres, donc il n'y a rien à ordonner.
        """
        if getattr(self, "_menu_voix", None):
            self._menu_voix.destroy()
            self._menu_voix = None
            return

        t = self.t
        menu = tk.Frame(self, bg="#0A1416", highlightbackground="#3E5559",
                        highlightthickness=1)
        identifiants = voix_de(self._langue)
        menu.place(x=t(64), y=t(344), width=t(230),
                   height=t(len(identifiants) * 28 + 8))
        choisie = self._voix_affichee.cget("text")
        for valeur in (nom_voix(v) for v in identifiants):
            ligne = tk.Label(menu, text=valeur, bg="#0A1416",
                             fg=ACCENT if valeur == choisie else TEXTE,
                             anchor="w", font=sans(t(15)), padx=t(12),
                             cursor="pointinghand")
            ligne.pack(fill="x", pady=1)
            ligne.bind("<Enter>", lambda e, l=ligne: l.configure(bg="#14313A"))
            ligne.bind("<Leave>", lambda e, l=ligne: l.configure(bg="#0A1416"))
            ligne.bind("<Button-1>",
                       lambda e, v=valeur: self._voix_prise(v))
        self._menu_voix = menu

    def _voix_prise(self, valeur):
        for identifiant in voix_de(self._langue):
            if nom_voix(identifiant) == valeur:
                self._voix_id = identifiant
                break
        self._voix_affichee.configure(text=valeur)
        self._fermer_menu()
        self._enregistrer()

    def _fermer_menu(self, _event=None):
        menu = getattr(self, "_menu_voix", None)
        if menu and menu.winfo_exists():
            menu.destroy()
        self._menu_voix = None

    def _clic_ailleurs(self, _event=None):
        """Un clic ailleurs referme les menus ouverts — sans rien bloquer."""
        self._fermer_menu()
        self._fermer_menus()

    def _voix_choisie(self, valeur):
        self._voix_affichee.configure(text=valeur)

    def _ouvrir_systeme(self):
        FenetreSysteme(self, self._langue)

    def _ouvrir_langues(self):
        FenetreLangues(self, self._langue, self._langue_choisie)

    def _langue_choisie(self, code):
        """On choisit une langue : sa voix officielle et son allure suivent.

        EdgeTX ne fait pas parler toutes ses voix à la même vitesse — Emily
        10 % plus vite, Sofie 10 % plus lentement. C'est le point de départ
        du curseur, Richard peut ensuite s'en écarter.
        """
        if code not in PAR_CODE:
            return
        if getattr(self, "_entrees_nom", None):
            # Ce que Richard a tapé reste avec la langue qu'il quittait.
            self._memoriser_liste()
        langue = donner_langue(code)
        self._langue = code
        self._ligne_active = 0
        # Toute l'interface change de langue, pas seulement la liste : on
        # redessine sur place, comme pour l'agrandissement.
        self._redessiner()
        self._voix_id = langue.voix
        self._voix_affichee.configure(text=nom_voix(self._voix_id))
        self._vitesse.regler(langue.pour_cent)
        self._enregistrer()

    def _redessiner(self):
        """Recrée tout le contenu à la même place, sans rouvrir la fenêtre.

        Le niveau du son est un réglage de l'utilisateur : il survit au
        changement de langue. Les autres valeurs sont reposées par
        l'appelant, parce qu'elles dépendent de la langue.
        """
        if getattr(self, "_attente", None):
            self.after_cancel(self._attente)
            self._attente = None
        niveau = self._niveau._valeur if hasattr(self, "_niveau") else 0
        for enfant in self.winfo_children():
            enfant.destroy()
        self._construire()
        self._niveau.regler(niveau)

    # -- carte noire : niveau, robot, puis les trois outils -----------
    def _carte(self):
        t = self.t
        self._titre_niveau = self.texte(
            61, 372, 230, 22, self.mot("niveau").upper() + " · 0 dB", ACCENT,
            sans(t(15)), ancre="center")

        # Un curseur, plus de boutons : on tire vers la gauche pour baisser
        # le fichier, vers la droite pour le monter. Le milieu, c'est 0 dB.
        self._niveau = Curseur(
            self, self.decor(78, 400, 198, 34), t(78), t(400), t(198), t(34),
            fond=CARTE, mini=-12, maxi=12,
            valeur=int(self._reglages.get("niveau", 0)),
            commande=self._niveau_change)
        self._niveau_change(self._niveau._valeur)

        self._titre_vitesse = self.texte(
            61, 442, 230, 22, self.mot("vitesse").upper() + " · 0 %", ACCENT,
            sans(t(15)), ancre="center")
        self._vitesse = Curseur(
            self, self.decor(78, 466, 198, 34), t(78), t(466), t(198), t(34),
            fond=CARTE, mini=-20, maxi=20,
            valeur=int(self._reglages.get("vitesse",
                                          donner_langue(self._langue).pour_cent)),
            commande=self._vitesse_change, degrade=False)
        self._vitesse_change(self._vitesse._valeur)

        self.texte(61, 508, 230, 22, self.mot("robot").upper(), ACCENT,
                   sans(t(15)), ancre="center")

        # Quatre cases, les mêmes que dans la liste : une seule cochée.
        self._robots = []
        for i in range(4):
            case = ctk.CTkCheckBox(
                self, text="", width=t(24), height=t(24),
                checkbox_width=t(20), checkbox_height=t(20), corner_radius=0,
                border_width=1, border_color="#3A5A5E", fg_color=ACCENT,
                bg_color=CARTE, hover_color=ACCENT, checkmark_color=NOIR,
                font=sans(t(12)), command=self._choisir_robot)
            case.place(x=t(92 + i * 50), y=t(534))
            self._robots.append(case)
        robot = int(self._reglages.get("robot", 1))
        self._robots[min(max(robot, 1), 4) - 1].select()

        tk.Frame(self, bg="#1B2F33", height=1).place(
            x=t(78), y=t(574), width=t(196), height=1)

        for i, (texte, icone) in enumerate(
                ((self.mot("ajouter"), "plus"),
                 (self.mot("supprimer"), "moins"),
                 (self.mot("ecouter"), "lecture"))):
            y = 592 + i * 66
            action = {"plus": self._ajouter_ligne,
                      "moins": self._supprimer_ligne,
                      "lecture": self._ecouter}[icone]
            bouton = Bouton(self, texte, t(78), t(y), t(198), t(50),
                            decor=self.decor(78, y, 198, 50), fond=CARTE,
                            contour=True, couleur_texte=TEXTE, biseau=10,
                            icone=icone, espace=True, fonte=sans(t(16)),
                            commande=action)
            if icone == "lecture":
                self._bouton_ecouter = bouton

    def _vitesse_change(self, valeur):
        self._enregistrer()
        titre = self.mot("vitesse").upper()
        if valeur == 0:
            texte = f"{titre} · 0 %"
        else:
            signe = "+" if valeur > 0 else "−"
            texte = f"{titre} · {signe}{abs(valeur)} %"
        self._titre_vitesse.dire(texte)

    def _niveau_change(self, valeur):
        self._enregistrer()
        titre = self.mot("niveau").upper()
        if valeur == 0:
            texte = f"{titre} · 0 dB"
        else:
            signe = "+" if valeur > 0 else "−"
            texte = f"{titre} · {signe}{abs(valeur)} dB"
        self._titre_niveau.dire(texte)

    def _choisir_robot(self, i):
        """Une seule case cochée : les autres se décochent."""
        if self._robots[i].get():
            for j, autre in enumerate(self._robots):
                if j != i:
                    autre.deselect()
        else:
            self._robots[i].select()
        self._enregistrer()

    # -- liste des phrases, sur noir ----------------------------------
    def _liste(self):
        t = self.t
        self._cases = []

        self._toutes = ctk.CTkCheckBox(
            self, text="", width=t(24), height=t(24),
            checkbox_width=t(20), checkbox_height=t(20), corner_radius=0,
            border_width=1, border_color="#3A5A5E", fg_color=ACCENT,
            bg_color=NOIR, hover_color=ACCENT, checkmark_color=NOIR,
            font=sans(t(12)), command=self._basculer_tout)
        self._toutes.place(x=t(346), y=t(215))

        self.texte(378, 200, 180, 42, self.mot("nom").upper(), TEXTE,
                   sans(t(24)))
        self.texte(566, 200, 380, 42, self.mot("phrase").upper(), TEXTE,
                   sans(t(24)))
        # Le trait cyan entre l'en-tête et la liste.
        tk.Frame(self, bg=ACCENT, height=1).place(
            x=t(340), y=t(247), width=t(645), height=1)
        # Le trait vertical entre la colonne du nom et celle de la phrase.
        tk.Frame(self, bg="#17343A", width=1).place(
            x=t(552), y=t(214), width=1, height=t(32))

        liste = ctk.CTkScrollableFrame(
            self, fg_color=NOIR, corner_radius=0,
            width=t(638), height=t(532),
            scrollbar_button_color="#183335",
            scrollbar_button_hover_color=ACCENT)
        liste.place(x=t(340), y=t(256))
        self._liste_cadre = liste
        liste.bind("<MouseWheel>", self._molette, add="+")
        liste._parent_canvas.bind("<MouseWheel>", self._molette, add="+")
        liste.grid_columnconfigure(0, weight=1)

        self._phrases = self._phrases_de_la_langue()
        self._remplir_liste()
        self._coins()

    def _liste_officielle(self, code):
        """Les annonces d'EdgeTX pour cette langue, téléchargées une fois."""
        if not hasattr(self, "_phrases_chargees"):
            self._phrases_chargees = {}
        if code not in self._phrases_chargees:
            try:
                trouvees = liste_de_depart(donner_langue(code))
            except Exception:
                trouvees = []
            if not trouvees:
                # La maquette, elle, montre ses quatorze phrases d'exemple :
                # c'est une démonstration. L'application, non — afficher des
                # phrases d'exemple comme si c'étaient les annonces
                # officielles serait un mensonge, et Richard les fabriquerait.
                trouvees = list(PHRASES) if DONNEES == ICI else []
                if not trouvees:
                    # La ligne de message n'existe pas encore : la liste se
                    # construit avant le bandeau du bas.
                    self._liste_indisponible = True
            self._phrases_chargees[code] = trouvees
        return self._phrases_chargees[code]

    def _phrases_de_la_langue(self):
        """Les annonces officielles de la langue, ou la démo si rien ne vient.

        La maquette doit s'ouvrir même sans réseau : dans ce cas elle garde
        ses quatorze phrases d'exemple, et le dit par le compteur.
        """
        if self._langue in self._listes_editees:
            return self._listes_editees[self._langue]
        return self._liste_officielle(self._langue)

    def _remplir_liste(self):
        """Remplit (ou remplit à nouveau) les lignes de la liste."""
        t = self.t
        liste = self._liste_cadre
        self._cases = []
        self._entrees_nom = []
        self._entrees_phrase = []
        for enfant in liste.winfo_children():
            enfant.destroy()

        self._rangees = []
        self._fonds = []
        for i, (nom, phrase) in enumerate(self._phrases):
            fond = RAYURE if i % 2 else NOIR
            if i == self._ligne_active:
                fond = SURVOL
            rangee = ctk.CTkFrame(liste, fg_color=fond, corner_radius=0,
                                  height=t(76))
            rangee.grid(row=i, column=0, sticky="ew")
            rangee.grid_columnconfigure(3, weight=1)

            case = ctk.CTkCheckBox(
                rangee, text="", width=t(24), height=t(24),
                checkbox_width=t(20), checkbox_height=t(20),
                corner_radius=0, border_width=1, border_color="#3A5A5E",
                fg_color=ACCENT, bg_color=fond, hover_color=ACCENT,
                checkmark_color=NOIR, font=sans(t(12)))
            case.grid(row=0, column=0, padx=(t(6), t(12)), pady=t(18))
            self._cases.append(case)

            nom_champ = ctk.CTkEntry(
                rangee, width=t(150), height=t(34), fg_color=fond,
                border_width=0, corner_radius=0, text_color=ACCENT,
                font=sans(t(21)))
            nom_champ.grid(row=0, column=1, padx=(0, t(18)), sticky="w")
            nom_champ.insert(0, nom)
            self._entrees_nom.append(nom_champ)

            tk.Frame(rangee, bg="#17343A", width=1).grid(
                row=0, column=2, sticky="ns", pady=t(16))

            champ = ctk.CTkEntry(
                rangee, height=t(34), fg_color=fond, border_width=0,
                corner_radius=0, text_color=TEXTE, font=sans(t(21)))
            champ.grid(row=0, column=3, sticky="ew", padx=(t(16), t(12)))
            champ.insert(0, phrase)
            self._entrees_phrase.append(champ)

            tk.Frame(rangee, bg="#16262A", height=1).grid(
                row=1, column=0, columnspan=4, sticky="ew")

            for morceau in (rangee, case, nom_champ, champ):
                morceau.bind("<MouseWheel>", self._molette, add="+")
            # Cliquer sur la ligne la choisit ; entrer dans un champ aussi,
            # sans redessiner, pour ne pas voler le curseur d'édition.
            index = i
            rangee.bind("<Button-1>", lambda e, i=index: self._activer(i), add="+")
            for champ_ in (nom_champ, champ):
                champ_.bind("<FocusIn>",
                            lambda e, i=index: self._activer(i, redessiner=False),
                            add="+")
            self._rangees.append(rangee)
            self._fonds.append(RAYURE if i % 2 else NOIR)


    def _lire_liste(self):
        """Ce qu'il y a dans les champs, tel que l'utilisateur l'a laissé."""
        return [(nom.get(), phrase.get())
                for nom, phrase in zip(self._entrees_nom, self._entrees_phrase)]

    def _activer(self, index, redessiner=True):
        """Choisit une ligne pour Ajouter, Supprimer et Écouter."""
        if index == self._ligne_active and redessiner:
            return
        self._ligne_active = index
        if not redessiner:
            # On arrive dans un champ : on recolore seulement, sinon le
            # redessin volerait le curseur d'édition.
            self._colorer()
            return
        self._phrases = self._lire_liste()
        self._remplir_liste()

    def _colorer(self):
        """La ligne choisie s'éclaire ; les autres reprennent leur rayure."""
        for i, rangee in enumerate(getattr(self, "_rangees", [])):
            fond = SURVOL if i == self._ligne_active else self._fonds[i]
            rangee.configure(fg_color=fond)
            self._entrees_nom[i].configure(fg_color=fond)
            self._entrees_phrase[i].configure(fg_color=fond)

    def _ajouter_ligne(self):
        """Ajoute une ligne vide après celle qui est choisie."""
        self._phrases = self._lire_liste()
        place = min(self._ligne_active + 1, len(self._phrases))
        self._phrases.insert(place, ("", ""))
        self._ligne_active = place
        self._remplir_liste()
        self._entrees_nom[place].focus_set()
        self._compteur.dire(f"0 / {len(self._lignes_a_fabriquer())}")

    def _supprimer_ligne(self):
        """Retire la ligne choisie (la dernière jamais)."""
        if len(self._phrases) <= 1:
            return
        self._phrases = self._lire_liste()
        self._phrases.pop(self._ligne_active)
        self._ligne_active = min(self._ligne_active, len(self._phrases) - 1)
        self._remplir_liste()
        self._compteur.dire(f"0 / {len(self._lignes_a_fabriquer())}")

    def _basculer_tout(self):
        """La case de l'en-tête coche ou décoche toute la liste."""
        coche = bool(self._toutes.get())
        for case in self._cases:
            case.select() if coche else case.deselect()

    def _coins(self):
        """Quatre équerres, une par coin, chacune tournée vers l'intérieur.

        Le trait suit les deux bords qui se rejoignent : rien à retourner,
        chaque coin a son orientation.
        """
        coins = (
            (328, 190, ((2, 18), (2, 2), (18, 2))),      # haut-gauche
            (960, 190, ((2, 2), (18, 2), (18, 18))),     # haut-droite
            (328, 794, ((2, 2), (2, 18), (18, 18))),     # bas-gauche
            (960, 794, ((2, 18), (18, 18), (18, 2))),    # bas-droite
        )
        for x, y, points in coins:
            coin = tk.Canvas(self, width=self.t(20), height=self.t(20),
                             bg=NOIR, highlightthickness=0, bd=0)
            coin.place(x=self.t(x), y=self.t(y))
            plat = [c for point in points for c in (self.t(point[0]),
                                                   self.t(point[1]))]
            coin.create_line(*plat, fill=ACCENT, width=1)

    # -- bandeau du bas : Let's Go, la progression, le compteur -------
    def _bandeau(self):
        t = self.t
        Bouton(self, self.mot("lets_go"), t(60), t(862), t(250), t(56),
               decor=self.decor(60, 862, 250, 56), fond=BANDE,
               fonte=sans(t(22)), biseau=16, plein=True,
               commande=self._lancer_generation)
        self._jauge = Barre(self, self.decor(340, 872, 570, 7), t(340), t(872),
                            t(570), t(7), fond=BANDE, valeur=0.0)
        # Le compteur finit sur le bord droit de la liste.
        self._compteur = self.texte(905, 866, 80, 22, f"0 / {len(self._phrases)}", GRIS,
                                    sans(t(14)), ancre="e")
        self._message = self.texte(340, 898, 560, 24,
                                   self.mot("liste_indisponible")
                                   if getattr(self, "_liste_indisponible", False)
                                   else self.mot("pret"),
                                   GRIS, sans(t(13)))
        self._etape = 0
        self._attente = None

    # -- la génération, pour de vrai ---------------------------------
    def _lignes_a_fabriquer(self):
        """Les lignes cochées, avec les textes tels qu'ils sont à l'écran.

        Si rien n'est coché, on prend tout : sur une maquette, « Let's Go »
        sans rien cocher doit faire quelque chose de visible plutôt que de
        rester muet.
        """
        choisies = []
        completes = []
        for i, case in enumerate(self._cases):
            nom = self._entrees_nom[i].get().strip()
            phrase = self._entrees_phrase[i].get().strip()
            if not nom or not phrase:
                continue          # une ligne à moitié remplie ne se fabrique pas
            completes.append((nom, phrase))
            if case.get():
                choisies.append((nom, phrase))
        return choisies or completes

    def _lancer_generation(self):
        """Fabrique les fichiers, dans un fil, sans figer la fenêtre.

        Tk n'aime pas être appelé depuis un fil : le fil pose ses nouvelles
        dans une file, et la fenêtre la lit à intervalle court (même
        mécanique que la 1.5.1).
        """
        if getattr(self, "_fil", None) and self._fil.is_alive():
            return
        if self._attente:
            self.after_cancel(self._attente)
            self._attente = None

        lignes = self._lignes_a_fabriquer()
        # Tout ce qui se lit dans des widgets est lu ICI, dans le fil
        # principal : un fil n'a pas le droit de toucher à Tk.
        reglages = {
            "voix": self._voix_id,
            "allure": 1 + self._vitesse._valeur / 100,
            "hauteur": donner_langue(self._langue).hauteur,
            "robot": self._robot_choisi(),
            "niveau": self._niveau._valeur,
            "langue": self._langue,
            "dossier": self._dossier_sortie(),
        }
        self._file_attente = queue.Queue()
        self._jauge.remplir(0.0)
        self._compteur.dire(f"0 / {len(lignes)}")
        self._message.dire(self.mot("preparation"))
        self._fil = threading.Thread(target=self._fabriquer,
                                     args=(lignes, reglages), daemon=True)
        self._fil.start()
        self._attente = self.after(80, self._suivre_generation)

    def _fabriquer(self, lignes, reglages):
        """Le travail, dans le fil : voix, WAV, robot, niveau, écriture.

        Tout ce qui vient de l'interface est déjà dans `reglages` : ce fil
        ne lit aucun widget (c'est la règle de la 1.5.1, et la seule qui
        évite les plantages bizarres).
        """
        import voxpack as moteur

        langue = donner_langue(reglages["langue"])
        voix = reglages["voix"]
        allure = reglages["allure"]
        dossier = os.path.join(reglages["dossier"], langue.code)
        os.makedirs(dossier, exist_ok=True)
        total = len(lignes)
        faits = 0
        erreurs = 0
        for numero, (nom, phrase) in enumerate(lignes, start=1):
            self._file_attente.put(("etape", numero, total, phrase))
            try:
                mp3 = os.path.join(dossier, f".{nom}.mp3")
                # On fabrique sous un nom temporaire puis on déplace :
                # fermer la fenêtre en cours de route ne doit pas laisser
                # un WAV tronqué sous son vrai nom (leçon de la 1.5.1).
                wav = os.path.join(dossier, f".{nom}.wav.tmp")
                asyncio.run(moteur.sauver_voix(
                    phrase, voix, mp3,
                    rate=f"{'+' if allure >= 1 else '-'}"
                         f"{abs(round((allure - 1) * 100))}%",
                    pitch=reglages["hauteur"] or "+0Hz"))
                moteur.convertir_en_wav(mp3, wav)
                os.remove(mp3)
                if reglages["robot"]:
                    moteur.appliquer_effet_robot(wav, reglages["robot"])
                moteur.ameliorer_niveau_wav(wav)
                appliquer_niveau(wav, reglages["niveau"])
                os.replace(wav, os.path.join(dossier, f"{nom}.wav"))
                faits += 1
                erreurs = 0
            except Exception as erreur:
                erreurs += 1
                self._file_attente.put(("erreur", nom, str(erreur)[:80]))
                if erreurs >= 3:
                    self._file_attente.put(("arret", faits))
                    return
        self._file_attente.put(("fini", faits, dossier))

    def _robot_choisi(self):
        """Le numéro du robot coché (1 à 4), ou 0 si aucun."""
        return self._choisir_robot_numero()

    def _ecouter(self):
        """Fait entendre une phrase avec la voix et les réglages choisis.

        Un appui pendant que ça travaille arrête : la fabrication peut
        durer une seconde, et sans cet état explicite un second appui
        lançait une seconde fabrication au lieu d'arrêter la première.
        """
        if getattr(self, "_apercu_en_cours", False):
            self._arret_apercu = True
            if getattr(self, "_lecteur", None):
                self._lecteur.terminate()
                self._lecteur = None
            self._apercu_en_cours = False
            self._bouton_ecouter.dire(self.mot("ecouter"))
            self._message.dire(self.mot("pret"))
            return
        phrase = self._phrase_a_ecouter()
        if not phrase:
            return
        reglages = {
            "voix": self._voix_id,
            "allure": 1 + self._vitesse._valeur / 100,
            "hauteur": donner_langue(self._langue).hauteur,
            "robot": self._robot_choisi(),
            "niveau": self._niveau._valeur,
        }
        self._apercu_en_cours = True
        self._arret_apercu = False
        self._bouton_ecouter.dire(self.mot("arreter"))
        self._message.dire(self.mot("fabrication", i=1, n=1, phrase=phrase))
        self._file_apercu = queue.Queue()
        threading.Thread(target=self._jouer, args=(phrase, reglages),
                         daemon=True).start()
        self.after(150, self._surveiller_apercu)

    def _phrase_a_ecouter(self):
        """La phrase de la ligne choisie — c'est ce qu'on vient de taper."""
        if self._entrees_phrase:
            phrase = self._entrees_phrase[self._ligne_active].get().strip()
            if phrase:
                return phrase
        for entree in self._entrees_phrase:
            if entree.get().strip():
                return entree.get().strip()
        return ""

    def _jouer(self, phrase, reglages):
        """Fabrique et joue, dans un fil ; ne touche jamais à Tk."""
        import subprocess
        import tempfile

        import voxpack as moteur

        dossier = tempfile.mkdtemp(prefix="voxpack-apercu-")
        chemin = os.path.join(dossier, "apercu.wav")
        try:
            mp3 = chemin + ".mp3"
            allure = reglages["allure"]
            asyncio.run(moteur.sauver_voix(
                phrase, reglages["voix"], mp3,
                rate=("+" if allure >= 1 else "-")
                     + "%d%%" % abs(round((allure - 1) * 100)),
                pitch=reglages["hauteur"] or "+0Hz"))
            moteur.convertir_en_wav(mp3, chemin)
            os.remove(mp3)
            if reglages["robot"]:
                moteur.appliquer_effet_robot(chemin, reglages["robot"])
            moteur.ameliorer_niveau_wav(chemin)
            appliquer_niveau(chemin, reglages["niveau"])
            if self._arret_apercu:
                return          # on a appuyé sur « Arrêter » entre-temps
            self._file_apercu.put(("lecture", chemin))
            self._lecteur = subprocess.Popen(["afplay", chemin])
            self._lecteur.wait()
        except Exception as erreur:
            self._file_apercu.put(("erreur", str(erreur)[:80]))
        finally:
            self._file_apercu.put(("fin", None))

    def _surveiller_apercu(self):
        """La fenêtre lit ce que le fil a posé, jamais l'inverse."""
        try:
            while True:
                genre, detail = self._file_apercu.get_nowait()
                if genre == "erreur":
                    self._message.dire(detail)
                elif genre == "fin":
                    self._lecteur = None
                    self._apercu_en_cours = False
                    self._bouton_ecouter.dire(self.mot("ecouter"))
                    self._message.dire(self.mot("pret"))
                    return
        except queue.Empty:
            pass
        self.after(150, self._surveiller_apercu)

    def _suivre_generation(self):
        """Ce que la fenêtre apprend du fil, à intervalle court."""
        self._attente = None
        while True:
            try:
                nouvelle = self._file_attente.get_nowait()
            except queue.Empty:
                break
            genre = nouvelle[0]
            if genre == "etape":
                _, numero, total, phrase = nouvelle
                self._jauge.remplir(numero / total)
                self._compteur.dire(f"{numero - 1} / {total}")
                self._message.dire(self.mot("recherche", i=numero,
                                            n=total, phrase=phrase))
            elif genre == "erreur":
                _, nom, detail = nouvelle
                self._message.dire(f"{nom} : {detail}")
            elif genre == "arret":
                _, faits = nouvelle
                self._message.dire(self.mot("termine", n=faits))
                self._compteur.dire(f"{faits} / {faits}")
                return
            elif genre == "fini":
                _, faits, dossier = nouvelle
                self._jauge.remplir(1.0)
                self._compteur.dire(f"{faits} / {faits}")
                self._message.dire(self.mot("termine", n=faits))
                print("fichiers écrits dans", dossier, flush=True)
                return
        self._attente = self.after(80, self._suivre_generation)

    # -- plaque du haut à droite : signature et café, centrés ---------
    def _plaque(self):
        t = self.t
        self.texte(820, 58, 172, 26, "ritchy-lab", ACCENT,
                   sans(t(18)), ancre="center", survol="#7FF0FC",
                   commande=self._ouvrir_site)

        decor = self.decor(820, 88, 172, 36)
        ligne = tk.Canvas(self, width=decor.width(), height=decor.height(),
                          bg=NOIR, highlightthickness=0, bd=0)
        self._decor_tasse = decor
        ligne.create_image(0, 0, image=decor, anchor="nw")

        tasse = Image.open(TASSE)
        hauteur = t(26)
        largeur = int(tasse.width * hauteur / tasse.height)
        self._tasse = ImageTk.PhotoImage(tasse.resize((largeur, hauteur)))
        fonte = sans(t(18))
        largeur_mot = tkfont.Font(font=fonte).measure("ko-fi")
        total = largeur + t(8) + largeur_mot
        gauche = (decor.width() - total) // 2
        ligne.create_image(gauche, decor.height() // 2,
                           image=self._tasse, anchor="w")
        mot = ligne.create_text(gauche + largeur + t(8), decor.height() // 2,
                                text="ko-fi", fill=ACCENT, font=fonte,
                                anchor="w")
        ligne.configure(cursor="pointinghand")
        ligne.bind("<Enter>", lambda e: ligne.itemconfig(mot, fill="#7FF0FC"))
        ligne.bind("<Leave>", lambda e: ligne.itemconfig(mot, fill=ACCENT))
        ligne.bind("<Button-1>", lambda e: self._ouvrir_soutien())
        ligne.place(x=t(820), y=t(88))


if __name__ == "__main__":
    charger_polices()
    Maquette().mainloop()
