# ============================================================
# Vox-Pack
# © 2026 ritchy-lab — licence MIT (voir le fichier LICENSE)
# made by ritchy
# ============================================================

import asyncio
import csv
import json
import os
import shutil
import string
import subprocess
import sys
import threading
import webbrowser
from tkinter import filedialog

import tkinter.font as tkfont

import customtkinter as ctk
from PIL import Image
import edge_tts

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Où l'application range la liste des phrases.
# L'application s'appelait RadioVox et écrivait dans « VoixEdgeTX » :
# au premier démarrage, on recopie l'ancienne liste (sans jamais la
# supprimer) pour que rien ne soit perdu.
ANCIEN_DIR = os.path.expanduser("~/Documents/VoixEdgeTX")
DATA_DIR = os.path.expanduser("~/Documents/Vox-Pack")
CSV_FILE = os.path.join(DATA_DIR, "liste_des_voix.csv")
VOLUME = "+50%"
AFCONVERT = "/usr/bin/afconvert"


def reprendre_ancienne_liste():
    """Recopie la liste de l'ancienne version, une seule fois."""
    ancien_csv = os.path.join(ANCIEN_DIR, "liste_des_voix.csv")
    if os.path.exists(ancien_csv) and not os.path.exists(CSV_FILE):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            shutil.copy2(ancien_csv, CSV_FILE)
        except OSError:
            pass  # tant pis : on repartira de la liste par défaut

# Chemin du logo. En version compilée, PyInstaller range les fichiers joints
# (le logo) dans un dossier temporaire : on regarde donc à plusieurs endroits.
DOSSIER_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def trouver_logo():
    pistes = []
    if getattr(sys, "frozen", False):
        pistes.append(getattr(sys, "_MEIPASS", ""))
        pistes.append(os.path.dirname(os.path.abspath(sys.executable)))
        pistes.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "..", "Resources"))
    pistes.append(DOSSIER_SCRIPT)
    for dossier in pistes:
        if dossier:
            chemin = os.path.join(dossier, "logo.png")
            if os.path.exists(chemin):
                return chemin
    return os.path.join(DOSSIER_SCRIPT, "logo.png")


LOGO_PATH = trouver_logo()

VOICES = {
    "Denise (Femme - Studio)": "fr-FR-DeniseNeural",
    "Ariane (Femme - Naturelle)": "fr-CH-ArianeNeural",
    "Henri (Homme - Posé)": "fr-FR-HenriNeural",
    "Fabrice (Homme - Dynamique)": "fr-CH-FabriceNeural",
}

LISTE_PAR_DEFAUT = [
    ("mot-arme", "Moteur armé"),
    ("mot-off", "Moteur coupé"),
    ("V-decol", "Volets de décollage"),
    ("V-atter", "Volets d'atterrissage"),
    ("train-so", "Train sorti"),
    ("train-re", "Train rentré"),
    ("chrono-d", "Chrono démarré"),
    ("chrono-a", "Chrono arrêté"),
    ("mv-norm", "Mode normal"),
    ("mv-grat", "Mode thermique"),
    ("mv-vite", "Mode vitesse"),
    ("mv-doco", "Mode décollage"),
    ("croc-act", "Crocodiles activés"),
    ("croc-des", "Crocodiles coupés"),
    ("crochet", "Largage remorque"),
    ("stab-off", "Stabilisation désactivée"),
    ("stab-act", "Stabilisation activée"),
    ("stab-aut", "Stabilisation automatique"),
    ("panique", "Panique"),
    ("gain-aug", "Gain augmenté"),
    ("gain-dim", "Gain diminué"),
    ("pv-atte", "Mode atterrissage"),
    ("accro", "Mode acrobatique"),
    ("aerofrei", "Aérofreins"),
    ("croisier", "Croisière"),
    ("decol", "Décollage"),
    ("atterro", "Atterrissage"),
    ("dr-hgh", "Grand débattement"),
    ("dr-med", "Débattement moyen"),
    ("dr-small", "Petit débattement"),
    ("flperon", "Flapperon"),
    ("lance", "Lancer"),
    ("lu-in", "Lumières allumées"),
    ("lu-out", "Lumières éteintes"),
    ("moyen", "Moyen"),
    ("eleve", "Élevé"),
    ("small", "Petit"),
    ("snap-fl", "Snapflap"),
    ("Stab-1", "Stabilité un"),
    ("Stab-2", "Stabilité deux"),
    ("TX-eleve", "Taux élevé"),
    ("TX-moyen", "Taux moyen"),
    ("TX-faibl", "Taux faible"),
    ("v-rentre", "Volet rentré"),
]

# Palette
BG_MAIN = "#000000"        # fond uni noir
BG_CARD = "#0F161C"
BG_ENTRY = "#1A2530"
BG_HEADER = "#14202B"
CYAN = "#00B8C5"
CYAN_DARK = "#00A8B8"
CYAN_HOVER = "#2A5A66"
CYAN_CLAIR = "#C1FEFF"     # survol : le texte et le cadre s'éclairent
LINK_COLOR = "#7FE0E8"     # liens cliquables (comme dans mes autres applis)
TEXT_WHITE = "#DBDBDB"
TEXT_GREY = "#8A9AA9"
TEXT_DIM = "#5A6A78"       # signature au repos

# Lien de soutien (fenêtre ouverte en cliquant sur la signature)
KO_FI_URL = "https://ko-fi.com/ritchy_lab"

# Largeur unique de tous les boutons (homogènes)
BTN_W = 170
BTN_H = 34

# ------------------------------------------------------------------
# Typographie — aucun gras dans la fenêtre principale : les tailles et les
# contrastes suffisent, et le rendu est plus léger.
# ------------------------------------------------------------------
TYPO_LISTE = 17          # les lignes de la liste (nom du fichier + phrase)
HAUTEUR_LIGNE = 40       # hauteur de ces cases (à agrandir avec la police)
TYPO_BOUTON = 16        # texte des boutons
TYPO_PETIT_BOUTON = 14  # petits boutons (Tout / Rien)

# Le logo a plus de poids visuel à gauche (les barres de voix) qu'à droite
# (les ondes fines) : centré au pixel près, le sous-titre paraît décalé vers
# la droite. On le décale donc légèrement vers la gauche, pour qu'il tombe
# sous le monogramme. Mettre 0 pour un centrage strictement mathématique.
DECALAGE_SOUS_TITRE = 8  # en pixels, vers la gauche

# Écart entre les lettres du sous-titre, en pixels. Tk ne sait pas espacer les
# lettres : le sous-titre est donc dessiné lettre par lettre (classe
# TexteEspace ci-dessous). 0 = écartement naturel de la police, 3 ou 4 = plus
# aéré, -1 = plus serré.
ESPACEMENT_SOUS_TITRE = 0

# Police du texte. La première de la liste que le système sait réellement
# utiliser est retenue au démarrage. Attention : « SF Pro Display » n'existe
# pas — sous ce nom, Tk prenait en silence la police système de macOS (et
# aurait pris n'importe quoi sous Windows).
POLICES_PREFEREES = [
    ".AppleSystemUIFont",   # police système de macOS (San Francisco)
    "Segoe UI",             # police système de Windows
    "Avenir Next",          # macOS
    "Helvetica Neue",
    "Arial",                # présente partout
]
FONT_MAIN = "Arial"         # valeur de départ, remplacée par choisir_police()


def choisir_police(candidats=None):
    """Retient la première police de la liste que le système sait utiliser.

    Tk ne refuse pas un nom de police inconnu : il en rend une autre sans rien
    dire. On vérifie donc ce qu'on obtient réellement.
    """
    global FONT_MAIN
    for nom in (candidats or POLICES_PREFEREES):
        try:
            if tkfont.Font(family=nom).actual("family") == nom:
                FONT_MAIN = nom
                break
        except Exception:
            continue
    return FONT_MAIN


# ------------------------------------------------------------------
# Règles de nommage des fichiers de voix
# ------------------------------------------------------------------
# EdgeTX lit le nom du fichier audio sur la carte SD : 8 caractères au
# maximum (6 sur les versions d'EdgeTX antérieures à la 2.11), sans accent,
# sans espace, et sans les caractères que le système de fichiers refuse.
LIMITE_NOM = 8
CARACTERES_AUTORISES = set(string.ascii_letters + string.digits + "-_")
ACCENTS = "éèêëàâäîïôöùûüçÉÈÊËÀÂÄÎÏÔÖÙÛÜÇ"
DANGER = "#FF6B6B"          # texte et bordure d'une case en erreur
BG_DANGER = "#3A1F22"       # fond d'une case en erreur
LARGEUR_MESSAGE = 175       # colonne des messages, à droite de chaque ligne


def probleme_nom(nom):
    """Renvoie None si le nom convient, sinon la raison, en clair."""
    if not nom:
        return "nom vide"
    if len(nom) > LIMITE_NOM:
        return f"{len(nom)} caractères (max {LIMITE_NOM})"
    if " " in nom or "\t" in nom:
        return "pas d'espace"
    mauvais = sorted({c for c in nom if c not in CARACTERES_AUTORISES})
    if mauvais:
        if any(c in ACCENTS for c in mauvais):
            return "pas d'accent"
        return f"caractère « {mauvais[0]} » interdit"
    return None


# ------------------------------------------------------------------
# Réglages de l'application (dernier dossier utilisé)
# ------------------------------------------------------------------
REGLAGES_FILE = os.path.join(DATA_DIR, "reglages.json")


def lire_reglages():
    try:
        with open(REGLAGES_FILE, "r", encoding="utf-8") as f:
            reglages = json.load(f)
        return reglages if isinstance(reglages, dict) else {}
    except Exception:
        return {}


def ecrire_reglages(reglages):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(REGLAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(reglages, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # des réglages, ce n'est pas vital : on n'alerte pas


def largeur_juste(valeurs, taille_police=13, marge=44):
    """Largeur d'un menu déroulant ajustée à son texte le plus long.

    La marge couvre la place de la flèche et les espaces intérieurs : sans
    elle, la flèche laisserait un grand vide après les noms les plus courts.
    """
    police = tkfont.Font(family=FONT_MAIN, size=taille_police)
    return max(police.measure(str(v)) for v in valeurs) + marge


# ------------------------------------------------------------------
# Barre de progression segmentée (Canvas) avec animation fluide
# ------------------------------------------------------------------
class SegmentedProgressBar(ctk.CTkFrame):
    def __init__(self, master, segments=32, height=22, **kwargs):
        super().__init__(master, fg_color="transparent", height=height, **kwargs)
        self.segments = segments
        self.progress = 0.0
        self.target = 0.0
        self._anim_running = False
        self._canvas = ctk.CTkCanvas(
            self, height=height, bg=BG_MAIN, highlightthickness=0
        )
        self._canvas.pack(fill="x", expand=True)
        self._canvas.bind("<Configure>", lambda e: self._redraw())

    def set(self, value):
        self.target = max(0.0, min(1.0, value))
        if not self._anim_running:
            self._anim_running = True
            self._animate()

    def reset(self):
        self.set(0.0)

    def _animate(self):
        diff = self.target - self.progress
        if abs(diff) < 0.005:
            self.progress = self.target
            self._redraw()
            self._anim_running = False
            return
        self.progress += diff * 0.18
        self._redraw()
        self.after(16, self._animate)

    def _redraw(self):
        c = self._canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10:
            return

        n = self.segments
        gap = 4
        seg_w = (w - gap * (n - 1)) / n
        radius = 3
        filled = int(self.progress * n)

        for i in range(n):
            x0 = i * (seg_w + gap)
            x1 = x0 + seg_w
            y0 = 4
            y1 = h - 4
            color = LINK_COLOR if i < filled else "#1E2A33"
            self._round_rect(c, x0, y0, x1, y1, radius, color)

        pct = int(round(self.progress * 100))
        c.create_text(
            w - 6, h // 2,
            text=f"{pct}%",
            fill=TEXT_WHITE,
            font=(FONT_MAIN, 13),
            anchor="e",
        )

    def _round_rect(self, canvas, x0, y0, x1, y1, r, color):
        canvas.create_oval(x0, y0, x0 + 2 * r, y0 + 2 * r, fill=color, outline=color)
        canvas.create_oval(x1 - 2 * r, y0, x1, y0 + 2 * r, fill=color, outline=color)
        canvas.create_oval(x0, y1 - 2 * r, x0 + 2 * r, y1, fill=color, outline=color)
        canvas.create_oval(x1 - 2 * r, y1 - 2 * r, x1, y1, fill=color, outline=color)
        canvas.create_rectangle(x0 + r, y0, x1 - r, y1, fill=color, outline=color)
        canvas.create_rectangle(x0, y0 + r, x1, y1 - r, fill=color, outline=color)


# ------------------------------------------------------------------
# Menu déroulant des voix
# ------------------------------------------------------------------
class MenuVoix(ctk.CTkComboBox):
    """Menu déroulant des voix, au filet complet et à la flèche bien à l'aise.

    customtkinter repeint le bord DROIT du menu avec la couleur du bloc de la
    flèche : au repos, mais aussi à chaque passage de la souris (sa méthode
    _on_leave s'en occupe sans condition). Comme ce bloc doit rester sombre
    pour ne plus voir de cyan derrière la flèche, le filet disparaîtrait à
    droite. On le rétablit donc après chaque repeinture.

    La flèche, elle, est collée au bord : on l'écarte vers la gauche.
    """

    MARGE_FLECHE = 6      # écart entre la flèche et le bord droit, en pixels

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)
        self._retablir_filet()
        # Le dessin replace la flèche à sa position d'origine : le décalage
        # appliqué ici ne s'accumule donc jamais.
        try:
            self._canvas.move("dropdown_arrow", -self.MARGE_FLECHE, 0)
        except Exception:
            pass

    def _on_enter(self, event=0):
        super()._on_enter(event)
        self._retablir_filet()

    def _on_leave(self, event=0):
        super()._on_leave(event)
        self._retablir_filet()

    def _retablir_filet(self):
        try:
            self._canvas.itemconfig(
                "border_parts_right", fill=CYAN, outline=CYAN)
        except Exception:
            pass  # si customtkinter change, on garde le menu tel quel


# ------------------------------------------------------------------
# Texte à écartement réglable
# ------------------------------------------------------------------
class TexteEspace(ctk.CTkCanvas):
    """Étiquette dont on règle l'écart entre les lettres.

    Tk ne sait pas espacer les lettres d'un texte : on dessine donc chaque
    lettre l'une après l'autre, à la distance voulue. L'écartement peut être
    positif (plus aéré) ou négatif (plus serré).
    """

    def __init__(self, master, texte, taille=16, espacement=0,
                 couleur=TEXT_WHITE, fond=BG_MAIN, **kwargs):
        police = tkfont.Font(family=FONT_MAIN, size=taille)
        mesures = [police.measure(lettre) for lettre in texte]
        naturel = police.measure(texte)
        # La somme des lettres est plus large que le texte entier : la police
        # resserre certaines paires. On répartit cette différence, pour qu'à
        # écartement 0 le texte occupe exactement sa largeur naturelle.
        correction = (sum(mesures) - naturel) / max(len(texte) - 1, 1)
        largeur = int(naturel + espacement * max(len(texte) - 1, 0))
        hauteur = police.metrics("linespace") + 6
        super().__init__(master, width=largeur, height=hauteur,
                         bg=fond, highlightthickness=0, **kwargs)
        self.police = police
        x = 0
        for lettre, mesure in zip(texte, mesures):
            self.create_text(x, hauteur // 2, text=lettre, anchor="w",
                             fill=couleur, font=police)
            x += mesure - correction + espacement


# ------------------------------------------------------------------
# Application
# ------------------------------------------------------------------
class VoxPackApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        choisir_police()

        self.title("Vox-Pack")
        self.geometry("1000x740")
        self.minsize(950, 600)
        self.resizable(True, True)
        self.configure(fg_color=BG_MAIN)

        self.output_dir = None
        self.lignes = []
        self._logo_image = None
        self._soutien = None
        self._reglages = lire_reglages()
        self._erreur_sauvegarde = False

        # ----- En-tête (logo + sous-titre) -----
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(18, 4))

        # Icône "?" en haut à droite (descendue)
        self.btn_aide = ctk.CTkButton(
            self.header,
            text="?",
            font=(FONT_MAIN, 20),
            width=30,
            height=30,
            corner_radius=15,
            fg_color="transparent",
            border_color=CYAN,
            border_width=1,
            text_color=CYAN,
            hover=False,          # au survol, le fond ne change pas (voir _survol)
            command=self._ouvrir_aide,
        )
        self._survol(self.btn_aide)
        self.btn_aide.place(relx=1.0, rely=0.0, anchor="ne", x=-15, y=30)

        # Logo
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                ratio = img.height / img.width
                new_w = 220
                new_h = int(new_w * ratio)
                self._logo_image = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(new_w, new_h)
                )
                ctk.CTkLabel(
                    self.header, image=self._logo_image, text=""
                ).pack(anchor="center", pady=(0, 4))
            except Exception:
                ctk.CTkLabel(
                    self.header,
                    text="Vox-Pack",
                    font=(FONT_MAIN, 32),
                    text_color=CYAN,
                ).pack(anchor="center")
        else:
            ctk.CTkLabel(
                self.header,
                text="Vox-Pack",
                font=(FONT_MAIN, 32),
                text_color=CYAN,
            ).pack(anchor="center")

        # Sous-titre (écartement réglable par ESPACEMENT_SOUS_TITRE)
        self.lbl_sub = TexteEspace(
            self.header,
            "Fait parler ta radio",
            taille=16,
            espacement=ESPACEMENT_SOUS_TITRE,
            couleur=LINK_COLOR,
        )
        # padx retire la place à droite : le texte se décale vers la gauche
        self.lbl_sub.pack(anchor="center",
                          padx=(0, DECALAGE_SOUS_TITRE * 2),
                          pady=(0, 10))

        # ----- Ligne unique : Voix + 3 boutons (centrée) -----
        row_all = ctk.CTkFrame(self, fg_color="transparent")
        row_all.pack(fill="x", padx=20, pady=(0, 10))

        inner_row = ctk.CTkFrame(row_all, fg_color="transparent")
        inner_row.pack(anchor="center")

        self.combo_voice = MenuVoix(
            inner_row,
            values=list(VOICES.keys()),
            # largeur calculée sur le nom le plus long : la flèche reste
            # collée au texte au lieu de laisser un grand vide
            width=largeur_juste(VOICES.keys()),
            font=(FONT_MAIN, 13),
            dropdown_font=(FONT_MAIN, 13),
            # Les coins arrondis se fondent dans le fond noir de la fenêtre :
            # sans cela, customtkinter laisse apparaître un rectangle sombre.
            bg_color=BG_MAIN,
            fg_color=BG_CARD,
            border_color=CYAN,
            border_width=1,
            button_color=BG_CARD,          # pas de bloc cyan derrière la flèche
            hover=False,                   # le fond ne change pas au survol
            text_color=TEXT_WHITE,
            dropdown_fg_color="#000000",   # liste ouverte : fond noir
            dropdown_text_color=TEXT_WHITE,
            dropdown_hover_color="#1A2530",
            corner_radius=17,
            height=BTN_H,
            state="readonly",
        )
        self.combo_voice.set("Denise (Femme - Studio)")
        self.combo_voice.pack(side="left", padx=(0, 12))

        self._btn(inner_row, "Ajouter", self.ajouter_ligne).pack(side="left", padx=5)
        self._btn(inner_row, "Supprimer", self.supprimer_selection).pack(side="left", padx=5)
        self.btn_apercu = self._btn(inner_row, "Écouter l'aperçu",
                                    self.ecouter_selection)
        self.btn_apercu.pack(side="left", padx=5)
        self._lecture = None
        self._apercu_no = 0

        # ----- En-tête du tableau -----
        row_head = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10)
        row_head.pack(fill="x", padx=20, pady=(4, 0))

        row_head.grid_columnconfigure(0, weight=0, minsize=40)
        row_head.grid_columnconfigure(1, weight=1, uniform="col")
        row_head.grid_columnconfigure(2, weight=1, uniform="col")

        ctk.CTkLabel(row_head, text="", width=40).grid(row=0, column=0, padx=4, pady=8)
        ctk.CTkLabel(
            row_head, text=f"Nom du fichier WAV (Max {LIMITE_NOM} car.)",
            font=(FONT_MAIN, 18, "normal"), text_color=TEXT_WHITE,
        ).grid(row=0, column=1, sticky="w", padx=8, pady=8)
        ctk.CTkLabel(
            row_head, text="Phrase à prononcer par la radiocommande",
            font=(FONT_MAIN, 18, "normal"), text_color=TEXT_WHITE,
        ).grid(row=0, column=2, sticky="w", padx=8, pady=8)
        row_head.grid_columnconfigure(3, weight=0, minsize=LARGEUR_MESSAGE)

        # ----- Zone liste défilante -----
        self.frame_table = ctk.CTkScrollableFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=10,
            scrollbar_button_color=CYAN_DARK,
            scrollbar_button_hover_color=CYAN,
        )
        self.frame_table.pack(fill="both", expand=True, padx=20, pady=(2, 10))
        self.frame_table.grid_columnconfigure(0, weight=0, minsize=40)
        self.frame_table.grid_columnconfigure(1, weight=1, uniform="col")
        self.frame_table.grid_columnconfigure(2, weight=1, uniform="col")
        self.frame_table.grid_columnconfigure(3, weight=0, minsize=LARGEUR_MESSAGE)

        # customtkinter ne fait défiler la liste que si le widget rapporté par
        # l'événement en fait partie. Sur macOS, cette identification n'est pas
        # fiable : après un clic, la molette se bloque. On reprend donc la
        # molette nous-mêmes, en regardant simplement où se trouve le curseur.
        self.frame_table._parent_canvas.unbind_all("<MouseWheel>")
        self.bind_all("<MouseWheel>", self._molette_liste, add="+")

        # ----- Bas : progression + boutons -----
        self.bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom.pack(fill="x", padx=20, pady=(0, 18))

        # Compteur de génération (« 3 fichiers sur 12 »). Toujours présent,
        # mais vide : la mise en page ne bouge pas quand il se remplit.
        self.lbl_compteur = ctk.CTkLabel(
            self.bottom, text="", font=(FONT_MAIN, 13), text_color=TEXT_GREY,
        )
        self.lbl_compteur.pack(fill="x", pady=(0, 4))

        self.progress = SegmentedProgressBar(self.bottom, segments=32, height=22)
        self.progress.pack(fill="x", pady=(0, 12))
        self.progress.set(0.0)

        # Conteneur centré
        center_frame = ctk.CTkFrame(self.bottom, fg_color="transparent")
        center_frame.pack(fill="x", expand=True)

        row_gen = ctk.CTkFrame(center_frame, fg_color="transparent")
        row_gen.pack(anchor="center")

        self._btn(row_gen, "Tout", self.tout_cocher, small=True).pack(side="left", padx=6)
        self._btn(row_gen, "Rien", self.rien_cocher, small=True).pack(side="left", padx=6)

        self.btn_letsgo = ctk.CTkButton(
            row_gen,
            text="Let's Go",
            font=(FONT_MAIN, 16, "bold"),
            width=180,
            height=44,
            corner_radius=22,
            fg_color="#00A8B8",
            hover_color="#00F0FF",
            text_color="#0A0F14",
            border_width=0,
            command=self.start_generation,
        )
        self.btn_letsgo.pack(side="left", padx=14)

        # ----- Signature (cliquable : ouvre la fenêtre de soutien) -----
        self.signature = ctk.CTkLabel(
            self.bottom,
            text="ritchy-lab",
            font=(FONT_MAIN, 12),
            text_color=TEXT_DIM,
            fg_color="transparent",
        )
        self.signature.place(relx=1.0, rely=1.0, anchor="se", x=-15, y=-10)
        self.signature.bind("<Button-1>", lambda e: self._ouvrir_soutien())
        self.signature.bind(
            "<Enter>", lambda e: self.signature.configure(text_color=CYAN))
        self.signature.bind(
            "<Leave>", lambda e: self.signature.configure(text_color=TEXT_DIM))

        # ----- Chargement -----
        reprendre_ancienne_liste()
        self.charger_liste()

    # ------------------------------------------------------------------
    # Style bouton commun
    # ------------------------------------------------------------------
    def _btn(self, parent, text, command, small=False, largeur=None):
        if small:
            w, h, f = 80, 30, TYPO_PETIT_BOUTON
        else:
            w, h, f = BTN_W, BTN_H, TYPO_BOUTON
        if largeur:
            w = largeur
        bouton = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            font=(FONT_MAIN, f),     # pas de gras, comme partout
            fg_color="transparent",
            border_color=CYAN,
            border_width=1,
            corner_radius=h // 2,
            text_color=CYAN,
            # hover=False : au survol, le fond du bouton ne change pas.
            hover=False,
            height=h,
            width=w,
        )
        self._survol(bouton)
        return bouton

    def _survol(self, bouton):
        """Au survol : seul le texte et le cadre s'éclairent, pas le fond."""
        bouton.bind("<Enter>", lambda e: bouton.configure(
            text_color=CYAN_CLAIR, border_color=CYAN_CLAIR))
        bouton.bind("<Leave>", lambda e: bouton.configure(
            text_color=CYAN, border_color=CYAN))

    def _ouvrir_lien(self, url):
        """Ouvre une adresse dans le navigateur."""
        webbrowser.open(url)

    # ------------------------------------------------------------------
    # Mini fenêtre de soutien (clic sur la signature)
    # ------------------------------------------------------------------
    def _ouvrir_soutien(self):
        if self._soutien is not None and self._soutien.winfo_exists():
            self._soutien.lift()
            self._soutien.focus_force()
            return

        popup = ctk.CTkToplevel(self)
        self._soutien = popup
        popup.title("Soutenir le projet")
        popup.resizable(False, False)
        popup.transient(self)
        popup.configure(fg_color=BG_MAIN)
        popup.bind("<Escape>", lambda e: popup.destroy())

        largeur = 380
        ctk.CTkLabel(
            popup, text="Mon application te sert ou te plaît ?",
            font=(FONT_MAIN, 16), text_color=TEXT_WHITE,
            wraplength=largeur - 50, justify="center",
        ).pack(padx=25, pady=(26, 6))

        cafe = ctk.CTkLabel(
            popup, text="Paye-moi un café  ☕",
            font=(FONT_MAIN, 16), text_color=LINK_COLOR,
        )
        cafe.pack()
        cafe.bind("<Button-1>", lambda e: self._ouvrir_lien(KO_FI_URL))

        boutons = ctk.CTkFrame(popup, fg_color="transparent")
        boutons.pack(pady=(24, 26))
        self._btn(
            boutons, "Oui",
            lambda: (self._ouvrir_lien(KO_FI_URL), popup.destroy()),
            largeur=96,
        ).pack(side="left", padx=7)
        self._btn(boutons, "Une prochaine fois", popup.destroy,
                  small=True, largeur=170).pack(side="left", padx=7)

        popup.update_idletasks()
        hauteur = popup.winfo_reqheight()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - largeur) // 2
        y = self.winfo_y() + (self.winfo_height() - hauteur) // 2
        popup.geometry(f"{largeur}x{hauteur}+{max(x, 0)}+{max(y, 0)}")
        popup.after(150, lambda: self._saisir_popup(popup))

    def _saisir_popup(self, popup):
        try:
            popup.grab_set()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Petites fenêtres de message
    # ------------------------------------------------------------------
    # macOS impose ses boîtes grises, avec l'icône de Python : hors sujet dans
    # une application soignée. On dessine donc les nôtres, aux couleurs de
    # Vox-Pack. La pastille est dessinée : aucune image à embarquer.
    ICONES = {
        "info":      ("i", CYAN),
        "succes":    ("✓", CYAN),
        "attention": ("!", "#FFB347"),
        "erreur":    ("×", "#FF6B6B"),
    }

    def _message(self, texte, icone="info", boutons=None,
                 titre="Vox-Pack", largeur=430):
        """Affiche un message. `boutons` : liste de (libellé, action)."""
        popup = ctk.CTkToplevel(self)
        popup.title(titre)
        popup.resizable(False, False)
        popup.transient(self)
        popup.configure(fg_color=BG_MAIN)
        popup.bind("<Escape>", lambda e: popup.destroy())

        symbole, couleur = self.ICONES.get(icone, self.ICONES["info"])

        pastille = ctk.CTkCanvas(popup, width=58, height=58,
                                 bg=BG_MAIN, highlightthickness=0)
        pastille.create_oval(4, 4, 54, 54, outline=couleur, width=2)
        pastille.create_text(29, 29, text=symbole, fill=couleur,
                             font=(FONT_MAIN, 26, "bold"))
        pastille.pack(pady=(26, 8))

        ctk.CTkLabel(
            popup, text=texte,
            font=(FONT_MAIN, 14), text_color=TEXT_WHITE,
            wraplength=largeur - 60, justify="center",
        ).pack(padx=30)

        rangee = ctk.CTkFrame(popup, fg_color="transparent")
        rangee.pack(pady=(22, 24))

        for libelle, action in (boutons or [("Compris", None)]):

            def cliquer(a=action):
                popup.destroy()
                if a:
                    a()

            self._btn(rangee, libelle, cliquer, largeur=150).pack(
                side="left", padx=6)

        popup.update_idletasks()
        hauteur = popup.winfo_reqheight()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - largeur) // 2
        y = self.winfo_y() + (self.winfo_height() - hauteur) // 2
        popup.geometry(f"{largeur}x{hauteur}+{max(x, 0)}+{max(y, 0)}")
        popup.lift()
        popup.focus_force()
        popup.after(150, lambda: self._saisir_popup(popup))

    def _ouvrir_dossier(self, chemin):
        """Ouvre un dossier dans le gestionnaire de fichiers du système."""
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", chemin], check=False)
            elif sys.platform.startswith("win"):
                os.startfile(chemin)
            else:
                subprocess.run(["xdg-open", chemin], check=False)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Fenêtre d'aide
    # ------------------------------------------------------------------
    def _ouvrir_aide(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Aide — Vox-Pack")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()
        popup.configure(fg_color=BG_MAIN)

        self.update_idletasks()
        w_popup, h_popup = 620, 660
        x = self.winfo_x() + (self.winfo_width() - w_popup) // 2
        y = self.winfo_y() + (self.winfo_height() - h_popup) // 2
        popup.geometry(f"{w_popup}x{h_popup}+{max(x, 0)}+{max(y, 0)}")

        frame = ctk.CTkScrollableFrame(
            popup,
            fg_color=BG_CARD,
            corner_radius=10,
            scrollbar_button_color=CYAN_DARK,
            scrollbar_button_hover_color=CYAN,
        )
        frame.pack(fill="both", expand=True, padx=15, pady=(15, 8))

        # Le logo en haut de l'aide
        self._logo_aide = None
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                ratio = img.height / img.width
                largeur_logo = 300
                self._logo_aide = ctk.CTkImage(
                    light_image=img, dark_image=img,
                    size=(largeur_logo, int(largeur_logo * ratio)),
                )
            except Exception:
                self._logo_aide = None

        contenu = [
            ("logo", ""),
            ("title", "Comment utiliser l'application"),
            ("space", ""),
            ("text", "1. Choisir une voix dans le menu déroulant."),
            ("space", ""),
            ("text", "2. Gérer la liste"),
            ("bullet", "Ajouter une ligne : bouton \"Ajouter\""),
            ("bullet", "Supprimer une ligne : cocher la ligne puis bouton \"Supprimer\""),
            ("bullet", "Modifier : taper directement dans les cases"),
            ("space", ""),
            ("warning", "⚠️  Le nom du fichier ne doit pas dépasser 8 caractères"),
            ("warning", "     et ne doit pas contenir d'accents ni d'espaces."),
            ("space", ""),
            ("text", "3. Cocher les lignes à générer"),
            ("bullet", "Bouton \"Tout\" pour tout cocher"),
            ("bullet", "Bouton \"Rien\" pour tout décocher"),
            ("bullet", "Une seule ligne : cocher juste celle-ci"),
            ("space", ""),
            ("text", "4. Écouter un aperçu"),
            ("bullet", "Cocher une ligne puis cliquer sur \"Écouter l'aperçu\"."),
            ("space", ""),
            ("text", "5. Générer les fichiers"),
            ("bullet", "Cliquer sur \"Let's Go\" puis choisir un dossier."),
            ("space", ""),
            ("title2", "💾  Sauvegarde automatique"),
            ("text", "Vos modifications sont enregistrées dans :"),
            ("code", "~/Documents/Vox-Pack/liste_des_voix.csv"),
            ("space", ""),
            ("title2", "♻️  Liste par défaut"),
            ("bullet", "Si vous supprimez TOUTE la liste, elle sera reconstruite"),
            ("bullet", "automatiquement au prochain démarrage (44 lignes)."),
            ("bullet", "Si vous gardez au moins 1 ligne, vous repartez de cette"),
            ("bullet", "base pour créer votre liste personnalisée."),
            ("space", ""),
            ("title2", "🎵  Format des fichiers"),
            ("text", "Les WAV générés sont au format EdgeTX :"),
            ("code", "16 bits, 32 kHz, mono."),
            ("space", ""),
            ("sep", ""),
            ("grand", "☕  Mon application te sert ou te plaît ?"),
            ("lien", "Paye-moi un café  ·  ko-fi.com/ritchy_lab"),
            ("space", ""),
            ("sep", ""),
            ("italic", "Créé avec un brainstorming avec une IA"),
        ]

        for kind, txt in contenu:
            if kind == "logo":
                if self._logo_aide is not None:
                    ctk.CTkLabel(
                        frame, image=self._logo_aide, text=""
                    ).pack(pady=(4, 8))
            elif kind == "space":
                ctk.CTkLabel(frame, text="", height=6).pack()
            elif kind == "title":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=(FONT_MAIN, 18),
                    text_color=CYAN, anchor="w", justify="left",
                ).pack(fill="x", pady=(4, 2))
            elif kind == "title2":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=(FONT_MAIN, 16),
                    text_color=CYAN, anchor="w", justify="left",
                ).pack(fill="x", pady=(6, 2))
            elif kind == "grand":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=(FONT_MAIN, 19),
                    text_color=CYAN, anchor="center", justify="center",
                    wraplength=470,
                ).pack(fill="x", pady=(2, 6))
            elif kind == "bullet":
                ctk.CTkLabel(
                    frame, text="    " + txt,
                    font=(FONT_MAIN, 14),
                    text_color=TEXT_WHITE, anchor="w", justify="left",
                ).pack(fill="x")
            elif kind == "warning":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=(FONT_MAIN, 14),
                    text_color="#FF6B6B", anchor="w", justify="left",
                ).pack(fill="x")
            elif kind == "code":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=("Menlo", 13),
                    text_color="#7FE0E8", anchor="w", justify="left",
                ).pack(fill="x", padx=(20, 0))
            elif kind == "italic":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=(FONT_MAIN, 13, "italic"),
                    text_color=TEXT_GREY, anchor="center", justify="center",
                ).pack(fill="x", pady=(6, 0))
            elif kind == "lien":
                lien = ctk.CTkLabel(
                    frame, text=txt,
                    font=(FONT_MAIN, 17),
                    text_color=LINK_COLOR, anchor="center",
                )
                lien.pack(fill="x")
                lien.bind("<Button-1>", lambda e: self._ouvrir_lien(KO_FI_URL))
                lien.bind(
                    "<Enter>", lambda e, w=lien: w.configure(text_color=CYAN))
                lien.bind(
                    "<Leave>", lambda e, w=lien: w.configure(text_color=LINK_COLOR))
            elif kind == "sep":
                ctk.CTkFrame(frame, height=1, fg_color="#2A3A48").pack(fill="x", pady=8)
            else:
                ctk.CTkLabel(
                    frame, text=txt,
                    font=(FONT_MAIN, 13),
                    text_color=TEXT_WHITE, anchor="w", justify="left",
                ).pack(fill="x")

        fermer = self._btn(popup, "Fermer", popup.destroy, largeur=140)
        fermer.configure(height=36, corner_radius=18)
        fermer.pack(pady=(0, 15))

    # ------------------------------------------------------------------
    # Gestion liste
    # ------------------------------------------------------------------
    def _curseur_dans_la_liste(self):
        """Le curseur de la souris est-il au-dessus de la liste ?"""
        try:
            curseur = self.winfo_containing(*self.winfo_pointerxy())
        except Exception:
            return False
        while curseur is not None:
            if curseur is self.frame_table or curseur is self.frame_table._parent_canvas:
                return True
            curseur = getattr(curseur, "master", None)
        return False

    def _molette_liste(self, event):
        """Fait défiler la liste à la molette, où que soit le curseur dedans."""
        if not self._curseur_dans_la_liste():
            return
        canvas = self.frame_table._parent_canvas
        if canvas.yview() == (0.0, 1.0):      # tout tient à l'écran
            return
        canvas.yview("scroll", -event.delta, "units")

    def charger_liste(self):
        for ligne in self.lignes:
            ligne["frame"].destroy()
        self.lignes.clear()

        contenu = []
        if os.path.exists(CSV_FILE):
            # Lecture par le module csv : il comprend aussi bien les anciens
            # fichiers (sans guillemets) que les nouveaux.
            with open(CSV_FILE, "r", encoding="utf-8", newline="") as f:
                for ligne_lue in csv.reader(f):
                    if len(ligne_lue) >= 2:
                        contenu.append((ligne_lue[0].strip(), ligne_lue[1].strip()))
                    elif len(ligne_lue) == 1 and ligne_lue[0].strip():
                        contenu.append((ligne_lue[0].strip(), ""))

        if not contenu:
            contenu = list(LISTE_PAR_DEFAUT)

        for nom, texte in contenu:
            self._ajouter_ligne_ui(nom, texte)

        self._ecrire_csv()

    def _ajouter_ligne_ui(self, nom, texte):
        idx = len(self.lignes)
        frame = ctk.CTkFrame(self.frame_table, fg_color="transparent")
        frame.grid(row=idx, column=0, columnspan=4, sticky="ew", pady=2)
        frame.grid_columnconfigure(0, weight=0, minsize=40)
        frame.grid_columnconfigure(1, weight=1, uniform="col")
        frame.grid_columnconfigure(2, weight=1, uniform="col")
        frame.grid_columnconfigure(3, weight=0, minsize=LARGEUR_MESSAGE)

        var_check = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(
            frame, text="", variable=var_check, width=24,
            checkbox_width=20, checkbox_height=20,
            fg_color=CYAN, hover_color=CYAN_DARK,
            border_color=CYAN, border_width=2, corner_radius=6,
        )
        chk.grid(row=0, column=0, padx=(4, 6), pady=4)

        entry_nom = ctk.CTkEntry(
            frame,
            font=(FONT_MAIN, TYPO_LISTE),
            fg_color=BG_ENTRY,
            border_color="#2A3A48",
            border_width=1,
            text_color=TEXT_WHITE,
            corner_radius=8,
            height=HAUTEUR_LIGNE,
        )
        entry_nom.insert(0, nom)
        entry_nom.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        entry_txt = ctk.CTkEntry(
            frame,
            font=(FONT_MAIN, TYPO_LISTE),
            fg_color=BG_ENTRY,
            border_color="#2A3A48",
            border_width=1,
            text_color=TEXT_WHITE,
            corner_radius=8,
            height=HAUTEUR_LIGNE,
        )
        entry_txt.insert(0, texte)
        entry_txt.grid(row=0, column=2, sticky="ew", padx=6, pady=4)

        # Message d'avertissement, à côté de la ligne (vide si tout va bien).
        # Il a une place réservée : rien ne bouge quand il apparaît.
        msg = ctk.CTkLabel(
            frame, text="", font=(FONT_MAIN, 12),
            text_color=DANGER, anchor="w", justify="left",
        )
        msg.grid(row=0, column=3, sticky="w", padx=(4, 2))

        for champ in (entry_nom, entry_txt):
            champ.bind("<KeyRelease>", lambda e: self._on_change())
            # Entrée crée la ligne suivante : on enchaîne les phrases sans
            # lâcher le clavier.
            champ.bind("<Return>", lambda e: self.ajouter_ligne())

        self.lignes.append({
            "frame": frame,
            "var_check": var_check,
            "entry_nom": entry_nom,
            "entry_txt": entry_txt,
            "msg": msg,
        })

    def ajouter_ligne(self):
        self._ajouter_ligne_ui("nouveau", "Texte à prononcer")
        self._on_change()
        # le curseur se place directement dans la nouvelle ligne, et on
        # descend jusqu'à elle
        self.lignes[-1]["entry_nom"].focus_set()
        self.frame_table._parent_canvas.yview_moveto(1.0)

    def _verifier_noms(self):
        """Colore en rouge les noms qui posent problème, signale les doublons."""
        vus = {}
        for i, ligne in enumerate(self.lignes, start=1):
            nom = ligne["entry_nom"].get().strip()
            souci = probleme_nom(nom)
            if souci is None:
                deja = vus.get(nom.lower())
                if deja:
                    souci = f"déjà utilisé (ligne {deja})"
                else:
                    vus[nom.lower()] = i
            if souci:
                ligne["entry_nom"].configure(
                    border_color=DANGER, fg_color=BG_DANGER)
                ligne["msg"].configure(text=souci)
            else:
                ligne["entry_nom"].configure(
                    border_color="#2A3A48", fg_color=BG_ENTRY)
                ligne["msg"].configure(text="")

    def supprimer_selection(self):
        cochees = [l for l in self.lignes if l["var_check"].get()]
        if not cochees:
            self._message("Cochez au moins une ligne à supprimer.",
                          icone="attention")
            return

        if len(cochees) == len(self.lignes):
            self._message(
                "Vous allez supprimer TOUTE la liste.\n\n"
                "Elle sera reconstruite automatiquement "
                "au prochain démarrage de l'application.\n\n"
                "Voulez-vous continuer ?",
                icone="attention",
                boutons=[("Supprimer", lambda: self._supprimer_lignes(cochees)),
                         ("Annuler", None)],
            )
            return

        self._supprimer_lignes(cochees)

    def _supprimer_lignes(self, cochees):
        for ligne in cochees:
            ligne["frame"].destroy()
            self.lignes.remove(ligne)
        for i, ligne in enumerate(self.lignes):
            ligne["frame"].grid_configure(row=i)
        self._on_change()

    def tout_cocher(self):
        for l in self.lignes:
            l["var_check"].set(True)

    def rien_cocher(self):
        for l in self.lignes:
            l["var_check"].set(False)

    def _on_change(self):
        self._verifier_noms()
        self._ecrire_csv()

    def _ecrire_csv(self):
        """Enregistre la liste, sans risque de la perdre.

        On écrit d'abord dans un fichier voisin, puis on remplace l'ancien :
        si quelque chose interrompt l'écriture (plantage, disque plein), la
        liste précédente reste intacte. Une copie .bak est conservée.
        """
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            temporaire = CSV_FILE + ".tmp"
            with open(temporaire, "w", encoding="utf-8", newline="") as f:
                ecrivain = csv.writer(f)
                for l in self.lignes:
                    nom = l["entry_nom"].get().strip()
                    texte = l["entry_txt"].get().strip()
                    if nom or texte:
                        ecrivain.writerow([nom, texte])
            if os.path.exists(CSV_FILE):
                shutil.copy2(CSV_FILE, CSV_FILE + ".bak")
            os.replace(temporaire, CSV_FILE)
            self._erreur_sauvegarde = False
        except Exception as e:
            # Une seule alerte par session : sinon chaque frappe en ouvrirait une
            if not self._erreur_sauvegarde:
                self._erreur_sauvegarde = True
                self.after(0, lambda err=e: self._message(
                    "La liste n'a pas pu être enregistrée.\n\n"
                    f"{err}\n\nVérifie l'espace libre de ton disque.",
                    icone="erreur"))

    # ------------------------------------------------------------------
    # Aperçu audio
    # ------------------------------------------------------------------
    def ecouter_selection(self):
        cochees = [l for l in self.lignes if l["var_check"].get()]
        if not cochees:
            self._message("Cochez une ligne à écouter.", icone="attention")
            return
        texte = cochees[0]["entry_txt"].get().strip()
        if not texte:
            return
        voice_id = VOICES.get(self.combo_voice.get(), "fr-FR-DeniseNeural")

        # Le bouton devient « Arrêter » : la lecture peut être coupée.
        self._apercu_no += 1
        numero = self._apercu_no
        self._lecture = None
        self.btn_apercu.configure(text="■  Arrêter", command=self.arreter_apercu)

        threading.Thread(
            target=lambda: asyncio.run(
                self._jouer_apercu(texte, voice_id, numero)),
            daemon=True,
        ).start()

    def arreter_apercu(self):
        """Coupe la lecture en cours."""
        lecture = self._lecture
        if lecture is not None:
            try:
                lecture.terminate()
            except Exception:
                pass
        self._fin_apercu()

    def _fin_apercu(self):
        """Le bouton redevient « Écouter l'aperçu »."""
        try:
            self.btn_apercu.configure(text="Écouter l'aperçu",
                                      command=self.ecouter_selection)
        except Exception:
            pass

    async def _jouer_apercu(self, texte, voice_id, numero):
        os.makedirs(DATA_DIR, exist_ok=True)
        # Un nom de fichier différent pour chaque aperçu : deux clics rapides
        # ne peuvent plus se supprimer mutuellement le fichier en cours.
        temp = os.path.join(DATA_DIR, f"apercu_{os.getpid()}_{numero}.mp3")
        try:
            communicate = edge_tts.Communicate(texte, voice_id, volume=VOLUME)
            await communicate.save(temp)
            lecture = subprocess.Popen(["/usr/bin/afplay", temp])
            self._lecture = lecture
            lecture.wait()
        except Exception as e:
            self.after(0, lambda err=e: self._message(
                f"L'aperçu n'a pas pu être joué.\n\n{err}", icone="erreur"))
        finally:
            if os.path.exists(temp):
                try:
                    os.remove(temp)
                except OSError:
                    pass
            self.after(0, self._fin_apercu)

    # ------------------------------------------------------------------
    # Génération
    # ------------------------------------------------------------------
    def start_generation(self):
        cochees = [l for l in self.lignes if l["var_check"].get()]
        if not cochees:
            self._message("Cochez au moins une ligne à générer.",
                          icone="attention")
            return

        taches = []
        refuses = []
        for l in cochees:
            nom = l["entry_nom"].get().strip()
            texte = l["entry_txt"].get().strip()
            souci = probleme_nom(nom)
            if souci:
                # un nom invalide donnerait un fichier que la radio ne lirait
                # pas : on le signale au lieu de le fabriquer pour rien
                refuses.append((nom or "(vide)", souci))
            elif texte:
                taches.append((nom, texte))
        if not taches:
            self._message(
                "Aucune ligne valide à générer.\n\n"
                "Il faut un nom de fichier correct ET une phrase.",
                icone="attention")
            return

        dossier = filedialog.askdirectory(
            title="Dossier de destination des WAV",
            initialdir=self._reglages.get("dernier_dossier")
            or os.path.expanduser("~"),
        )
        if not dossier:
            return
        self._reglages["dernier_dossier"] = dossier
        ecrire_reglages(self._reglages)

        if os.path.basename(dossier) == "Voix radio":
            self.output_dir = dossier
        else:
            self.output_dir = os.path.join(dossier, "Voix radio")

        voice_id = VOICES.get(self.combo_voice.get(), "fr-FR-DeniseNeural")

        self.btn_letsgo.configure(state="disabled", fg_color="#0A5C66")
        self.progress.set(0.0)

        threading.Thread(
            target=self._run_async_loop,
            args=(taches, voice_id, refuses),
            daemon=True,
        ).start()

    def _run_async_loop(self, taches, voice_id, refuses=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._generer(taches, voice_id, refuses))
        finally:
            loop.close()
            self.after(0, lambda: self.btn_letsgo.configure(state="normal", fg_color="#00A8B8"))

    async def _generer(self, taches, voice_id, refuses=None):
        os.makedirs(self.output_dir, exist_ok=True)
        total = len(taches)
        echecs = list(refuses or [])       # noms refusés avant même d'essayer
        nb_refuses = len(echecs)

        for idx, (nom, texte) in enumerate(taches):
            temp_mp3 = os.path.join(self.output_dir, f"{nom}_temp.mp3")
            final_wav = os.path.join(self.output_dir, f"{nom}.wav")
            try:
                communicate = edge_tts.Communicate(texte, voice_id, volume=VOLUME)
                await communicate.save(temp_mp3)
                subprocess.run(
                    [AFCONVERT, "-f", "WAVE", "-d", "LEI16@32000", "-c", "1", temp_mp3, final_wav],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                )
            except Exception as e:
                # On note l'échec et on passe à la ligne suivante : une phrase
                # qui rate ne doit pas priver l'utilisateur de toutes les autres.
                echecs.append((nom, str(e)[:120]))
            finally:
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)

            fait = idx + 1
            val = fait / total
            self.after(0, lambda v=val: self.progress.set(v))
            self.after(0, lambda f=fait, t=total, n=nom:
                       self.lbl_compteur.configure(
                           text=f"{f} fichier{'s' if f > 1 else ''} sur {t}"
                                f"  —  {n}"))

        await asyncio.sleep(0.5)
        self.after(0, lambda: self.progress.reset())
        self.after(0, lambda: self.lbl_compteur.configure(text=""))

        reussis = max(total - (len(echecs) - nb_refuses), 0)
        if echecs:
            detail = "\n".join(f"• {nom} : {raison}" for nom, raison in echecs[:6])
            if len(echecs) > 6:
                detail += f"\n• … et {len(echecs) - 6} autre(s)"
            self.after(0, lambda: self._message(
                f"{reussis} fichier{'s' if reussis > 1 else ''} créé"
                f"{'s' if reussis > 1 else ''} sur {total}.\n\n"
                f"{len(echecs)} problème{'s' if len(echecs) > 1 else ''} :\n{detail}",
                icone="erreur"))
        else:
            out = self.output_dir
            self.after(0, lambda: self._message(
                f"Vos voix sont prêtes.\n\n{out}",
                icone="succes",
                boutons=[("Ouvrir le dossier",
                          lambda: self._ouvrir_dossier(out)),
                         ("Fermer", None)]))


if __name__ == "__main__":
    app = VoxPackApp()
    app.mainloop()