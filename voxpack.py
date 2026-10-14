# ============================================================
# Vox-Pack
# © 2026 ritchy-lab — licence MIT (voir le fichier LICENSE)
# made by ritchy
# ============================================================

import asyncio
import os
import shutil
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
# Typographie
# ------------------------------------------------------------------
TYPO_LISTE = 16          # les lignes de la liste (nom du fichier + phrase)
HAUTEUR_LIGNE = 38       # hauteur de ces cases (à agrandir avec la police)

# Le logo a plus de poids visuel à gauche (les barres de voix) qu'à droite
# (les ondes fines) : centré au pixel près, le sous-titre paraît décalé vers
# la droite. On le décale donc légèrement vers la gauche, pour qu'il tombe
# sous le monogramme. Mettre 0 pour un centrage strictement mathématique.
DECALAGE_SOUS_TITRE = 8  # en pixels, vers la gauche


def largeur_juste(valeurs, taille_police=13, marge=44):
    """Largeur d'un menu déroulant ajustée à son texte le plus long.

    La marge couvre la place de la flèche et les espaces intérieurs : sans
    elle, la flèche laisserait un grand vide après les noms les plus courts.
    """
    police = tkfont.Font(family="SF Pro Display", size=taille_police)
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
            font=("SF Pro Display", 12, "bold"),
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
    """Menu déroulant dont le filet reste complet.

    customtkinter repeint le bord DROIT du menu avec la couleur du bloc de la
    flèche : au repos, mais aussi à chaque passage de la souris (sa méthode
    _on_leave s'en occupe sans condition). Comme ce bloc doit rester sombre
    pour ne plus voir de cyan derrière la flèche, le filet disparaîtrait à
    droite. On le rétablit donc après chaque repeinture.
    """

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)
        self._retablir_filet()

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
# Application
# ------------------------------------------------------------------
class VoxPackApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vox-Pack")
        self.geometry("1000x740")
        self.minsize(950, 600)
        self.resizable(True, True)
        self.configure(fg_color=BG_MAIN)

        self.output_dir = None
        self.lignes = []
        self._logo_image = None
        self._soutien = None

        # ----- En-tête (logo + sous-titre) -----
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(18, 4))

        # Icône "?" en haut à droite (descendue)
        self.btn_aide = ctk.CTkButton(
            self.header,
            text="?",
            font=("SF Pro Display", 20, "bold"),
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
                    font=("SF Pro Display", 32, "bold"),
                    text_color=CYAN,
                ).pack(anchor="center")
        else:
            ctk.CTkLabel(
                self.header,
                text="Vox-Pack",
                font=("SF Pro Display", 32, "bold"),
                text_color=CYAN,
            ).pack(anchor="center")

        # Sous-titre en cyan
        self.lbl_sub = ctk.CTkLabel(
            self.header,
            text="Fait parler ta radio",
            font=("SF Pro Display", 16),
            text_color=LINK_COLOR,
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
            font=("SF Pro Display", 13),
            dropdown_font=("SF Pro Display", 13),
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
        self._btn(inner_row, "Écouter l'aperçu", self.ecouter_selection).pack(side="left", padx=5)

        # ----- En-tête du tableau -----
        row_head = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10)
        row_head.pack(fill="x", padx=20, pady=(4, 0))

        row_head.grid_columnconfigure(0, weight=0, minsize=40)
        row_head.grid_columnconfigure(1, weight=1, uniform="col")
        row_head.grid_columnconfigure(2, weight=1, uniform="col")

        ctk.CTkLabel(row_head, text="", width=40).grid(row=0, column=0, padx=4, pady=8)
        ctk.CTkLabel(
            row_head, text="Nom du fichier WAV (Max 8 car.)",
            font=("SF Pro Display", 18, "normal"), text_color=TEXT_WHITE,
        ).grid(row=0, column=1, sticky="w", padx=8, pady=8)
        ctk.CTkLabel(
            row_head, text="Phrase à prononcer par la radiocommande",
            font=("SF Pro Display", 18, "normal"), text_color=TEXT_WHITE,
        ).grid(row=0, column=2, sticky="w", padx=8, pady=8)

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

        # customtkinter ne fait défiler la liste que si le widget rapporté par
        # l'événement en fait partie. Sur macOS, cette identification n'est pas
        # fiable : après un clic, la molette se bloque. On reprend donc la
        # molette nous-mêmes, en regardant simplement où se trouve le curseur.
        self.frame_table._parent_canvas.unbind_all("<MouseWheel>")
        self.bind_all("<MouseWheel>", self._molette_liste, add="+")

        # ----- Bas : progression + boutons -----
        self.bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom.pack(fill="x", padx=20, pady=(0, 18))

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
            font=("SF Pro Display", 15, "bold"),
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
            font=("SF Pro Display", 11),
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
            w, h, f = 80, 30, 12
        else:
            w, h, f = BTN_W, BTN_H, 13
        if largeur:
            w = largeur
        bouton = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            font=("SF Pro Display", f, "bold"),
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
            font=("SF Pro Display", 16), text_color=TEXT_WHITE,
            wraplength=largeur - 50, justify="center",
        ).pack(padx=25, pady=(26, 6))

        cafe = ctk.CTkLabel(
            popup, text="Paye-moi un café  ☕",
            font=("SF Pro Display", 16), text_color=LINK_COLOR,
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
                             font=("SF Pro Display", 26, "bold"))
        pastille.pack(pady=(26, 8))

        ctk.CTkLabel(
            popup, text=texte,
            font=("SF Pro Display", 14), text_color=TEXT_WHITE,
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

        contenu = [
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
            ("title2", "☕  Soutenir le projet"),
            ("text", "Mon application te sert ou te plaît ?"),
            ("lien", "Paye-moi un café  ·  ko-fi.com/ritchy_lab"),
            ("space", ""),
            ("sep", ""),
            ("italic", "Créé avec un brainstorming avec une IA"),
        ]

        for kind, txt in contenu:
            if kind == "space":
                ctk.CTkLabel(frame, text="", height=6).pack()
            elif kind == "title":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=("SF Pro Display", 15, "bold"),
                    text_color=CYAN, anchor="w", justify="left",
                ).pack(fill="x", pady=(4, 2))
            elif kind == "title2":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=("SF Pro Display", 14, "bold"),
                    text_color=CYAN, anchor="w", justify="left",
                ).pack(fill="x", pady=(6, 2))
            elif kind == "bullet":
                ctk.CTkLabel(
                    frame, text="    " + txt,
                    font=("SF Pro Display", 13),
                    text_color=TEXT_WHITE, anchor="w", justify="left",
                ).pack(fill="x")
            elif kind == "warning":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=("SF Pro Display", 13, "bold"),
                    text_color="#FF6B6B", anchor="w", justify="left",
                ).pack(fill="x")
            elif kind == "code":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=("Menlo", 12),
                    text_color="#7FE0E8", anchor="w", justify="left",
                ).pack(fill="x", padx=(20, 0))
            elif kind == "italic":
                ctk.CTkLabel(
                    frame, text=txt,
                    font=("SF Pro Display", 12, "italic"),
                    text_color=TEXT_GREY, anchor="center", justify="center",
                ).pack(fill="x", pady=(6, 0))
            elif kind == "lien":
                lien = ctk.CTkLabel(
                    frame, text=txt,
                    font=("SF Pro Display", 13),
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
                    font=("SF Pro Display", 13),
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
            with open(CSV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if "," in line:
                        nom, texte = line.strip().split(",", 1)
                        contenu.append((nom, texte))

        if not contenu:
            contenu = list(LISTE_PAR_DEFAUT)

        for nom, texte in contenu:
            self._ajouter_ligne_ui(nom, texte)

        self._ecrire_csv()

    def _ajouter_ligne_ui(self, nom, texte):
        idx = len(self.lignes)
        frame = ctk.CTkFrame(self.frame_table, fg_color="transparent")
        frame.grid(row=idx, column=0, columnspan=3, sticky="ew", pady=2)
        frame.grid_columnconfigure(0, weight=0, minsize=40)
        frame.grid_columnconfigure(1, weight=1, uniform="col")
        frame.grid_columnconfigure(2, weight=1, uniform="col")

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
            font=("SF Pro Display", TYPO_LISTE),
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
            font=("SF Pro Display", TYPO_LISTE),
            fg_color=BG_ENTRY,
            border_color="#2A3A48",
            border_width=1,
            text_color=TEXT_WHITE,
            corner_radius=8,
            height=HAUTEUR_LIGNE,
        )
        entry_txt.insert(0, texte)
        entry_txt.grid(row=0, column=2, sticky="ew", padx=6, pady=4)

        entry_nom.bind("<KeyRelease>", lambda e: self._on_change())
        entry_txt.bind("<KeyRelease>", lambda e: self._on_change())

        self.lignes.append({
            "frame": frame,
            "var_check": var_check,
            "entry_nom": entry_nom,
            "entry_txt": entry_txt,
        })

    def ajouter_ligne(self):
        self._ajouter_ligne_ui("nouveau", "Texte à prononcer")
        self._on_change()

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
        self._ecrire_csv()

    def _ecrire_csv(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(CSV_FILE, "w", encoding="utf-8") as f:
                for l in self.lignes:
                    nom = l["entry_nom"].get().strip()
                    texte = l["entry_txt"].get().strip()
                    if nom or texte:
                        f.write(f"{nom},{texte}\n")
        except Exception:
            pass

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
        threading.Thread(
            target=lambda: asyncio.run(self._jouer_apercu(texte, voice_id)),
            daemon=True,
        ).start()

    async def _jouer_apercu(self, texte, voice_id):
        os.makedirs(DATA_DIR, exist_ok=True)
        temp = os.path.join(DATA_DIR, "preview_temp.mp3")
        try:
            communicate = edge_tts.Communicate(texte, voice_id, volume=VOLUME)
            await communicate.save(temp)
            subprocess.run(["/usr/bin/afplay", temp])
        except Exception as e:
            self.after(0, lambda err=e: self._message(
                f"L'aperçu n'a pas pu être joué.\n\n{err}", icone="erreur"))
        finally:
            if os.path.exists(temp):
                os.remove(temp)

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
        for l in cochees:
            nom = l["entry_nom"].get().strip()
            texte = l["entry_txt"].get().strip()
            if nom and texte:
                taches.append((nom, texte))
        if not taches:
            self._message("Aucune ligne valide à générer : il faut un nom de "
                          "fichier ET une phrase.", icone="attention")
            return

        dossier = filedialog.askdirectory(title="Dossier de destination des WAV")
        if not dossier:
            return

        if os.path.basename(dossier) == "Voix radio":
            self.output_dir = dossier
        else:
            self.output_dir = os.path.join(dossier, "Voix radio")

        voice_id = VOICES.get(self.combo_voice.get(), "fr-FR-DeniseNeural")

        self.btn_letsgo.configure(state="disabled", fg_color="#0A5C66")
        self.progress.set(0.0)

        threading.Thread(
            target=self._run_async_loop,
            args=(taches, voice_id),
            daemon=True,
        ).start()

    def _run_async_loop(self, taches, voice_id):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._generer(taches, voice_id))
        finally:
            loop.close()
            self.after(0, lambda: self.btn_letsgo.configure(state="normal", fg_color="#00A8B8"))

    async def _generer(self, taches, voice_id):
        os.makedirs(self.output_dir, exist_ok=True)
        total = len(taches)
        erreur = None

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
                erreur = f"Problème avec {nom} : {e}"
                break
            finally:
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)

            val = (idx + 1) / total
            self.after(0, lambda v=val: self.progress.set(v))

        await asyncio.sleep(0.5)
        self.after(0, lambda: self.progress.reset())

        if erreur:
            self.after(0, lambda m=erreur: self._message(
                f"La génération s'est arrêtée.\n\n{m}\n\n"
                "Vérifie ta connexion Internet : les voix sont fabriquées "
                "par le service en ligne de Microsoft.",
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