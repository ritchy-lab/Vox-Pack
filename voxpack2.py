# ============================================================
# Vox-Pack
# © 2026 ritchy-lab — licence MIT (voir le fichier LICENSE)
# made by ritchy
# ============================================================

import asyncio
import csv
import io
import json
import locale
import os
import queue
import re
import shutil
import ssl
import string
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import wave
import webbrowser
from tkinter import filedialog, Menu

import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk
from PIL import Image, ImageTk
import certifi
import edge_tts

from version import VERSION

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")
# La mise en page est en pixels (grille de 1024, voir _pv) : customtkinter ne
# doit PAS appliquer sa propre échelle DPI par-dessus. Sinon, sous Windows à
# 125 % ou 150 %, chaque widget CTk (liste, champs, cases) est 1,25 ou 1,5
# fois plus grand que la case dessinée — la liste débordait sur le bandeau
# « Let's Go ». Sur macOS, l'échelle vaut déjà 1 : rien ne change.
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)
# Posé avant la première fenêtre : customtkinter ne rend plus le facteur DPI
# du moniteur, et le processus reste « sans conscience DPI » — Windows
# agrandit alors la fenêtre d'un bloc (1,25 ou 1,5), au lieu de laisser
# l'application dessiner une petite fenêtre au pixel près. C'est ce qui rend
# l'écran trop petit sur un portable en 150 %.
ctk.deactivate_automatic_dpi_awareness()

# Où l'application range la liste des phrases.
# L'application s'appelait RadioVox et écrivait dans « VoixEdgeTX » :
# au premier démarrage, on recopie l'ancienne liste (sans jamais la
# supprimer) pour que rien ne soit perdu.
ANCIEN_DIR = os.path.expanduser("~/Documents/VoixEdgeTX")
DATA_DIR = os.path.expanduser("~/Documents/Vox-Pack")
CSV_FILE = os.path.join(DATA_DIR, "liste_des_voix.csv")
VOLUME = "+50%"
AFCONVERT = "/usr/bin/afconvert"        # macOS : présent d'origine, très rapide
AFPLAY = "/usr/bin/afplay"              # macOS : lecture d'un son
FORMAT_EDGETX = (32000, 1)             # 32 kHz, mono (ce que lit la radio)

# Nom du sous-dossier où sont rangés les fichiers générés. Volontairement
# neutre : dans la langue de l'utilisateur, il changerait de nom quand on
# change de langue, et on ne saurait plus où sont ses fichiers.
DOSSIER_SORTIE = "Vox-Pack"


def chemin_lisible(chemin):
    """Raccourcit le début du chemin : le dossier personnel devient « ~ ».

    Sans cela, « /Users/nom/Documents/mes voix radio/Vox-Pack » est
    trop large pour la fenêtre de fin de génération, et Tk le coupe n'importe
    où — au milieu d'un mot, ce qui rend le chemin illisible. Avec « ~ », il
    reste court, et le nom de l'utilisateur ne s'étale pas sur les captures
    d'écran.
    """
    if not chemin:
        return chemin
    personnel = os.path.expanduser("~")
    if chemin == personnel:
        return "~"
    if chemin.startswith(personnel + os.sep):
        return "~" + chemin[len(personnel):]
    return chemin


def relacher_souris():
    """Rend la capture de souris au système (Windows).

    Tk prend une capture implicite au clic. Si la fenêtre qui l'a reçue est
    détruite pendant ce clic — la croix de l'aide, le choix d'une langue —
    Windows peut la conserver : l'application reçoit alors des mouvements
    « bouton enfoncé » alors que le bouton est relâché, et sa fenêtre suit la
    souris jusqu'au clic suivant. C'est intermittent, selon l'endroit exact
    où le clic tombe. ReleaseCapture remet la capture à zéro.
    """
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.user32.ReleaseCapture()
        except Exception:
            pass


def bouton_enfonce():
    """Le bouton gauche est-il réellement enfoncé ?

    L'état porté par un événement peut mentir quand une capture est restée
    accrochée après la destruction d'une fenêtre sans cadre ; l'API système,
    elle, dit la vérité. C'est ce qui empêche la fenêtre principale de suivre
    la souris alors que le bouton est relâché.

    - Windows : GetKeyState ;
    - macOS : NSEvent.pressedMouseButtons() (PyObjC est déjà là pour le
      sélecteur de dossier) ;
    - ailleurs : on fait confiance à Tk.
    """
    if sys.platform.startswith("win"):
        try:
            import ctypes
            return bool(ctypes.windll.user32.GetKeyState(0x01) & 0x8000)
        except Exception:
            return True
    if sys.platform == "darwin":
        try:
            from AppKit import NSEvent
            return bool(NSEvent.pressedMouseButtons() & 1)
        except Exception:
            return True
    return True


def application_activee(fenetre):
    """Cette application est-elle celle du premier plan ?

    Sert à refermer le menu et la fenêtre des langues quand on clique dans
    une autre application : une fenêtre sans cadre ne reçoit pas toujours
    l'avis « tu as perdu le clavier » de Tk. Sur un système où la question
    n'a pas de réponse simple, on répond « oui » : mieux vaut un menu qui
    reste ouvert qu'un menu qui se referme sous les doigts.
    """
    if sys.platform == "darwin":
        try:
            from AppKit import NSApp
            return bool(NSApp.isActive())
        except Exception:
            return True
    if sys.platform.startswith("win"):
        try:
            import ctypes
            # winfo_id() est la fenêtre Tk ; GetAncestor(GA_ROOT) remonte à
            # celle que Windows considère comme la fenêtre de l'application.
            utilisateur = ctypes.windll.user32
            racine = utilisateur.GetAncestor(fenetre.winfo_id(), 2)
            return utilisateur.GetForegroundWindow() in (racine,
                                                         fenetre.winfo_id())
        except Exception:
            return True
    return True


def convertir_en_wav(source_mp3, destination_wav):
    """Convertit un MP3 en WAV 16 bits, 32 kHz, mono (le format EdgeTX).

    Sur macOS, on passe par afconvert : il est présent d'origine et très
    rapide. Ailleurs (Windows), on fait tout en Python avec soundfile et
    soxr — même résultat, aucun outil externe à installer.
    """
    if sys.platform == "darwin" and os.path.exists(AFCONVERT):
        subprocess.run(
            [AFCONVERT, "-f", "WAVE", "-d", "LEI16@32000", "-c", "1",
             source_mp3, destination_wav],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )
        return

    # Import paresseux : sur macOS, soundfile et soxr ne sont même pas
    # nécessaires, et l'application démarre donc sans eux.
    import numpy as np
    import soundfile as sf

    donnees, taux = sf.read(source_mp3, dtype="float32")
    if donnees.ndim > 1:                       # au cas où la voix serait stéréo
        donnees = donnees.mean(axis=1)
    cible = FORMAT_EDGETX[0]
    if taux != cible:
        try:
            import soxr
            donnees = soxr.resample(donnees, taux, cible, quality="VHQ")
        except Exception:
            # soxr est une extension native : sur un Windows où sa DLL ne se
            # charge pas (« DLL load failed »), l'aperçu entier échouait. Une
            # interpolation linéaire suffit pour une annonce parlée, et elle
            # n'empêche pas de générer les fichiers.
            n = int(round(len(donnees) * cible / taux))
            donnees = np.interp(
                np.linspace(0, len(donnees) - 1, n),
                np.arange(len(donnees)),
                donnees).astype("float32")
    # Le format est dit explicitement : sans cela, soundfile le devine d'après
    # l'extension, et refuse tout ce qui ne finit pas par .wav. Or les sons
    # système s'écrivent d'abord en « 0000.wav.tmp » (le temporaire doit rester
    # sur le même disque pour os.replace). Avec un nom en .tmp, les 212 sons
    # échouaient sur PC — « No format specified and unable to get format from
    # file extension » — alors que macOS passait par afconvert, qui s'en moque.
    sf.write(destination_wav, donnees, cible, subtype="PCM_16", format="WAV")


# ------------------------------------------------------------------
# Trace temporaire : qui a le clavier quand une alerte s'ouvre ?
# ------------------------------------------------------------------
# Posée le 5 novembre pour comprendre pourquoi Échap n'arrivait pas
# jusqu'aux fenêtres d'alerte. À retirer une fois la cause trouvée.
TRACE_ECHAP = "/tmp/voxpack-echap.log"


def _trace_echap(quoi):
    try:
        from AppKit import NSApp
        actif = NSApp.isActive()
        fenetre = NSApp.keyWindow()
        taille = ((round(fenetre.frame().size.width),
                   round(fenetre.frame().size.height)) if fenetre else None)
    except Exception:
        actif, taille = "?", None
    try:
        with open(TRACE_ECHAP, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {quoi:24} "
                    f"actif={actif} fenetre_active={taille}\n")
    except OSError:
        pass


# ------------------------------------------------------------------
# Voix de robot
# ------------------------------------------------------------------
# Quatre presets appliqués à la voix choisie. L'interface ne montre que
# « Robot 1 » à « Robot 3 » et « HAL 9000 » : c'est l'oreille qui choisit.
# Rangés du plus grave au plus aigu (les réglages sont ceux de Richard).
ROBOTS = {
    1: {"pitch": "-30Hz", "ring": 52, "dry": 0.40,
        "echo": ((0.025, 0.30), (0.050, 0.15))},
    2: {"pitch": None, "ring": 55, "dry": 0.18,
        "echo": ((0.025, 0.35), (0.050, 0.20))},
    3: {"pitch": "+40Hz", "ring": 60, "dry": 0.18,
        "echo": ((0.025, 0.35), (0.050, 0.20))},
    4: {"pitch": "-4Hz", "rate": "+6%", "hal": "en",
        "fr": {"pitch": "-10Hz", "rate": "-25%", "hal": "fr"},
        "de": {"pitch": "-8Hz", "rate": "-15%", "hal": "de"},
        "ring": 0, "dry": 1.0, "echo": ()},
}

# La voix que HAL 9000 impose, par langue. HAL n'a pas encore de voix
# allemande de cinéma : Conrad fait l'affaire en attendant (Richard, le
# 25 octobre 2026). Le réglage allemand est provisoire, à écouter.
VOIX_ROBOT = {"fr": "fr-FR-HenriNeural", "en": "en-US-ChristopherNeural",
              "de": "de-DE-ConradNeural"}


def appliquer_effet_robot(chemin, numero, langue="en"):
    """Applique un preset robot à un WAV EdgeTX (32 kHz, mono, 16 bits).

    Le fichier est réécrit dans un temporaire puis remplacé : une panne ne
    peut pas laisser un WAV tronqué que la radio tenterait de lire.
    """
    reglage = ROBOTS.get(numero)
    if not reglage:
        return
    import numpy as np

    with wave.open(chemin, "rb") as w:
        if (w.getframerate() != FORMAT_EDGETX[0] or w.getnchannels() != 1
                or w.getsampwidth() != 2):
            return
        sr = w.getframerate()
        brut = w.readframes(w.getnframes())
    if len(brut) < 4:
        return
    x = np.frombuffer(brut, dtype="<i2").astype(np.float32) / 32768.0

    if reglage.get("hal"):
        def lfilter(b, a, sig):
            y = np.zeros_like(sig)
            x1 = x2 = y1 = y2 = 0.0
            for i, v in enumerate(sig):
                out = (b[0] * v + b[1] * x1 + b[2] * x2
                       - a[1] * y1 - a[2] * y2)
                x2, x1 = x1, v
                y2, y1 = y1, out
                y[i] = out
            return y

        def biquad(kind, f0, gain=0.0, Q=0.707):
            w0 = 2 * np.pi * f0 / sr
            al = np.sin(w0) / (2 * Q)
            c = np.cos(w0)
            if kind == "hp":
                b = np.array([(1 + c) / 2, -(1 + c), (1 + c) / 2])
                a = np.array([1 + al, -2 * c, 1 - al])
            elif kind == "lp":
                b = np.array([(1 - c) / 2, 1 - c, (1 - c) / 2])
                a = np.array([1 + al, -2 * c, 1 - al])
            elif kind == "peak":
                A = 10 ** (gain / 40)
                b = np.array([1 + al * A, -2 * c, 1 - al * A])
                a = np.array([1 + al / A, -2 * c, 1 - al / A])
            elif kind == "highshelf":
                A = 10 ** (gain / 40)
                sh = 2 * np.sqrt(A) * al
                b = np.array([
                    A * ((A + 1) + (A - 1) * c + sh),
                    -2 * A * ((A - 1) + (A + 1) * c),
                    A * ((A + 1) + (A - 1) * c - sh),
                ])
                a = np.array([
                    (A + 1) - (A - 1) * c + sh,
                    2 * ((A - 1) - (A + 1) * c),
                    (A + 1) - (A - 1) * c - sh,
                ])
            else:  # lowshelf
                A = 10 ** (gain / 40)
                sh = 2 * np.sqrt(A) * al
                b = np.array([
                    A * ((A + 1) - (A - 1) * c + sh),
                    2 * A * ((A - 1) - (A + 1) * c),
                    A * ((A + 1) - (A - 1) * c - sh),
                ])
                a = np.array([
                    (A + 1) + (A - 1) * c + sh,
                    -2 * ((A - 1) + (A + 1) * c),
                    (A + 1) + (A - 1) * c - sh,
                ])
            return b / a[0], a / a[0]

        # Effet « haut-parleur carton » + léger écho, commun aux deux langues.
        y = lfilter(*biquad("hp", 300), x)
        y = lfilter(*biquad("peak", 950, 6.0), y)
        y = lfilter(*biquad("peak", 1800, 3.0), y)
        y = lfilter(*biquad("lp", 3200), y)
        n = int(0.0025 * sr)
        y[n:] += 0.18 * y[:-n]
        y = np.tanh(1.4 * y) / np.tanh(1.4)
        melange = y.copy()
        for delai, gain in ((0.030, 0.15), (0.060, 0.08)):
            n = int(delai * sr)
            melange[n:] += gain * y[:-n]
        y = melange
        pic = np.max(np.abs(y)) or 1.0
        y = 0.95 * y / pic
        temporaire = chemin + ".robot"
        try:
            with wave.open(temporaire, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sr)
                w.writeframes(
                    (np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
            os.replace(temporaire, chemin)
        finally:
            if os.path.exists(temporaire):
                try:
                    os.remove(temporaire)
                except OSError:
                    pass
        return

    def passe_haut(sig, fc):
        n = max(1, int(sr / fc))
        return sig - np.convolve(sig, np.ones(n) / n, mode="same")

    def passe_bas(sig, fc):
        n = max(1, int(sr / fc))
        return np.convolve(sig, np.ones(n) / n, mode="same")

    t = np.arange(len(x)) / sr
    melange = (reglage["dry"] * x
               + (1 - reglage["dry"]) * x
               * np.sin(2 * np.pi * reglage["ring"] * t))
    melange = passe_bas(passe_haut(melange, 200), 5200)
    sortie = melange.copy()
    for secondes, gain in reglage["echo"]:
        n = int(secondes * sr)
        sortie[n:] += gain * melange[:-n]
    pic = np.max(np.abs(sortie)) or 1.0
    sortie = 0.92 * sortie / pic

    temporaire = chemin + ".robot"
    try:
        with wave.open(temporaire, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(
                (np.clip(sortie, -1, 1) * 32767).astype("<i2").tobytes())
        os.replace(temporaire, chemin)
    finally:
        if os.path.exists(temporaire):
            try:
                os.remove(temporaire)
            except OSError:
                pass


# Quart de seconde de silence gardé APRÈS le dernier échantillon audible.
# Sans lui, la coupe s'arrêtait 50 ms après la fin du son : à l'écoute, la
# dernière consonne (« d » de « armed », « s » de « flaps ») s'entend coupée,
# et deux annonces jouées à la suite se collent. Repères mesurés le
# 28 octobre 2026 : notre fichier finissait 50 ms après le dernier son, les
# sons officiels d'EdgeTX gardent environ 850 ms. (Voir le point 6 dans
# ameliorer_niveau_wav.)
QUEUE_FIN = 0.250


def ameliorer_niveau_wav(chemin):
    """Coupe les silences, limite et normalise un WAV EdgeTX.

    Coupe + gain +6 dB + limiteur à avance de 5 ms, puis normalisation, et
    un quart de seconde de silence après le dernier son (QUEUE_FIN).
    Pas de compression par blocs, pas de tanh : le limiteur seul donne le
    niveau, sans le clic du compresseur.
    """
    import numpy as np
    from numpy.lib.stride_tricks import sliding_window_view

    with wave.open(chemin, "rb") as w:
        if (w.getframerate() != FORMAT_EDGETX[0] or w.getnchannels() != 1
                or w.getsampwidth() != 2):
            return
        sr = w.getframerate()
        brut = w.readframes(w.getnframes())
    if len(brut) < 64:
        return
    x = np.frombuffer(brut, dtype="<i2").astype(np.float32) / 32768.0

    # 1. Silences au début et à la fin.
    #
    # Le seuil était à −46 dBFS, et c'est trop haut : une fin de mot ne
    # s'arrête pas net, elle s'éteint. Le gain qui suit (+6 dB puis
    # normalisation) remontait cette fin à −43 dBFS, donc un fichier qui se
    # termine en pleine parole. Signalé le 22 octobre 2026. Seuil à −50 dBFS.
    #
    # La marge est plus large à la fin qu'au début (50 ms contre 20) : c'est
    # la fin qui s'entend. Un fondu de sortie ferme le fichier juste après
    # (point 5). Ces 30 ms de plus ne nous ramènent pas aux fichiers d'avant :
    # on reste à 822 ms de moyenne contre 1 932 ms sans traitement.
    actifs = np.where(np.abs(x) > 0.003)[0]
    if len(actifs):
        debut = max(0, actifs[0] - int(0.020 * sr))
        fin = min(len(x), actifs[-1] + int(0.050 * sr))
        x = x[debut:fin].copy()
    if len(x) < 64:
        return

    # 2. Gain d'entrée +6 dB.
    x = x * (10 ** (6.0 / 20.0))

    # 3. Limiteur à gain avec avance de 5 ms (pas de tanh, pas de blocs).
    avance = max(1, int(0.005 * sr))
    besoin = np.minimum(1.0, 0.99 / (np.abs(x) + 1e-9))
    pad_gain = np.pad(besoin, (0, avance), constant_values=1.0)
    gain = sliding_window_view(pad_gain, avance + 1).min(axis=1)
    gain = np.minimum(
        gain, np.convolve(gain, np.ones(5) / 5, mode="same"))
    x = x * gain

    # 4. Normalisation au pic 1,0.
    pic = np.max(np.abs(x))
    if pic > 0:
        x *= 1.0 / pic

    # 5. Fondu de sortie de 10 ms. Après la normalisation, la fin du fichier
    #    touche encore à −36 dBFS : la radio s'arrête en pleine parole. Dix
    #    millisecondes suffisent à supprimer le claquement, sans qu'on entende
    #    la voix disparaître.
    fondu = max(1, int(0.010 * sr))
    if len(x) > fondu:
        x[-fondu:] *= np.linspace(1.0, 0.0, fondu)

    # 6. Quart de seconde de silence après le dernier son.
    #
    # Le point 1 ne laisse que 50 ms entre le dernier échantillon audible et
    # la fin du fichier. C'est trop peu : à l'écoute, le son semble s'arrêter
    # net, et la dernière consonne — le « d » de « motor armed », le « s » de
    # « takeoff flaps » — s'entend coupée. Signalé de nouveau le 28 octobre
    # 2026, sur la 1.5 : le traitement n'avait pas changé depuis la 1.4.4,
    # c'est la marge qui restait trop serrée.
    #
    # Mesuré : sur « Motor armed », le fichier finissait 50 ms après le dernier
    # échantillon audible, à −78 dBFS — rien ne manquait au signal, c'est le
    # temps laissé après le son qui était trop court. Les sons officiels
    # d'EdgeTX gardent, eux, environ 850 ms.
    #
    # Le quart de seconde est COMPLÉTÉ avec du silence, pas pris sur la suite
    # du fichier : la queue fait donc exactement 250 ms, quelle que soit la
    # voix et même pour une phrase fabriquée en plusieurs morceaux (dont les
    # bords sont coupés à 50 ms avant collage). Le fichier reste court :
    # environ 1,05 s de moyenne, contre 1,93 s sans traitement.
    actifs = np.where(np.abs(x) > 0.003)[0]
    if len(actifs):
        manque = int(QUEUE_FIN * sr) - (len(x) - actifs[-1] - 1)
        if manque > 0:
            x = np.concatenate((x, np.zeros(manque, dtype=x.dtype)))

    temporaire = chemin + ".niveau"
    try:
        with wave.open(temporaire, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(
                (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
        os.replace(temporaire, chemin)
    finally:
        if os.path.exists(temporaire):
            try:
                os.remove(temporaire)
            except OSError:
                pass


def appliquer_niveau(chemin, decibels):
    """Monte ou baisse le fichier terminé, sans jamais saturer.

    Appelé APRÈS ameliorer_niveau_wav, qui normalise au pic : c'est le
    réglage de Richard (le curseur NIVEAU), pas le traitement de la 1.5.1.

    Un simple gain écrêtait : à +6 dB, un fichier déjà au pic saturait.
    On passe donc par le même limiteur à avance de 5 ms que le traitement
    de la 1.5.1 — le niveau monte, les crêtes sont retenues, le son ne
    casse pas. C'est une compression douce, pas un volume plus fort brut.
    """
    if not decibels:
        return
    import numpy as np
    from numpy.lib.stride_tricks import sliding_window_view

    with wave.open(chemin, "rb") as w:
        if (w.getframerate() != FORMAT_EDGETX[0] or w.getnchannels() != 1
                or w.getsampwidth() != 2):
            return
        sr = w.getframerate()
        brut = w.readframes(w.getnframes())
    if len(brut) < 2:
        return
    x = np.frombuffer(brut, dtype="<i2").astype(np.float32) / 32768.0
    x = x * (10 ** (decibels / 20.0))
    # Limiteur à avance de 5 ms : aucune crête ne dépasse 0,99.
    avance = max(1, int(0.005 * sr))
    besoin = np.minimum(1.0, 0.99 / (np.abs(x) + 1e-9))
    pad = np.pad(besoin, (0, avance), constant_values=1.0)
    gain = sliding_window_view(pad, avance + 1).min(axis=1)
    gain = np.minimum(gain, np.convolve(gain, np.ones(5) / 5, mode="same"))
    x = np.clip(x * gain, -1.0, 1.0)
    temporaire = chemin + ".niveau"
    try:
        with wave.open(temporaire, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes((x * 32767).astype("<i2").tobytes())
        os.replace(temporaire, chemin)
    finally:
        if os.path.exists(temporaire):
            try:
                os.remove(temporaire)
            except OSError:
                pass


def lire_lignes_csv(fichier):
    """Lit un CSV dont le séparateur est la virgule ou le point-virgule.

    Excel en version française enregistre avec « ; » : sans cette détection,
    toute la ligne devenait le nom du fichier. Le séparateur est choisi sur
    la première ligne non vide.
    """
    texte = fichier.read()
    premiere = next((l for l in texte.splitlines() if l.strip()), "")
    separateur = ";" if premiere.count(";") > premiere.count(",") else ","
    return [l for l in csv.reader(io.StringIO(texte, newline=""),
                                  delimiter=separateur)
            if l and any(c.strip() for c in l)]


def chemin_liste(langue):
    """Fichier de la liste d'une langue.

    Chaque langue a SA liste : on peut travailler en français sans risquer
    d'effacer la liste anglaise, et inversement. C'était le défaut d'une liste
    unique — Richard a perdu une liste en essayant l'anglais.
    """
    return os.path.join(DATA_DIR, f"liste_{langue}.csv")


# ------------------------------------------------------------------
# Sons système d'EdgeTX
# ------------------------------------------------------------------
# La liste officielle des sons est tenue par l'équipe EdgeTX :
#
#     https://github.com/EdgeTX/edgetx-sdcard-sounds  (dossier voices/)
#
# C'est ELLE que Vox-Pack utilise, et pas le fichier de la carte SD : il n'y
# a pas besoin de brancher la carte, et la liste est toujours à jour. Le
# fichier est téléchargé chez EdgeTX au moment de l'usage, puis lu. Rien n'est
# embarqué dans Vox-Pack (le dépôt EdgeTX est en GPL, Vox-Pack en MIT) : c'est
# le fichier d'EdgeTX, récupéré à la demande de l'utilisateur, comme s'il le
# téléchargeait lui-même. Ne jamais en mettre une copie dans le dépôt.
#
# Le fichier officiel se présente ainsi (six colonnes, virgules) :
#
#     "String ID","Source text","Translation","Context","Path","Filename"
#     "1","0","0","","SYSTEM","0000.wav"
#
# La phrase est « Translation », le nom est « Filename », et « Path » vaut
# SYSTEM ou rien (racine de la langue). Le CSV livré sur la carte, lui, tient
# en trois colonnes séparées par « ; » :
#
#     SOUNDS/fr/SYSTEM;0000.wav;0
#
# On sait lire les deux (utile pour les copies gardées en secours).
#
# On ne garde QUE les lignes du dossier SYSTEM (décision de Richard) : la
# racine mélange des sons officiels (armé, altitude, modes de vol…) et les sons
# personnels de l'utilisateur, qu'on ne veut pas refabriquer.
URL_CSV_OFFICIEL = ("https://raw.githubusercontent.com/EdgeTX/"
                    "edgetx-sdcard-sounds/master/voices/{}.csv")

# La langue de l'interface commande celle des voix : il y a donc un fichier
# utile par langue. Les quinze langues ont leur propre CSV et leur propre
# dossier SD dans `voxpack_data.langues` ; on les lit là plutôt que de tenir
# ici une seconde table qui finirait par diverger. Le portugais est le piège :
# la voix officielle est brésilienne (pt-BR-Francisca) alors que le fichier
# du dépôt s'appelle pt-PT.csv.
def csv_et_dossier(langue):
    """Le code du CSV officiel et le dossier SD d'une langue.

    Renvoie (« ja-JP », « jp ») pour le japonais, (« cs-CZ », « cz ») pour le
    tchèque, (« uk-UA », « ua-ostap ») pour l'ukrainien. Un code inconnu
    retombe sur le français, comme le reste de l'application.
    """
    from voxpack_data import langues as _table
    entree = _table.PAR_CODE.get(langue, _table.PAR_CODE["fr"])
    code = os.path.splitext(entree.csv.rsplit("/", 1)[-1])[0]
    return code, entree.dossier


def csv_officiel_sons_systeme(langue):
    """Télécharge la liste officielle et renvoie ses sons SYSTEM.

    Une copie est gardée dans les données de l'application : si GitHub ne
    répond pas, on repart de cette copie plutôt que de laisser l'utilisateur
    sans rien. Renvoie (lignes, dossier_sd, depuis_cache).
    """
    code, dossier = csv_et_dossier(langue)
    cache = os.path.join(DATA_DIR, f"sons-systeme-{code}.csv")
    try:
        # Même trousseau de certificats qu'edge-tts (certifi) : dans
        # l'application compilée, les chemins de macOS ou de Windows ne sont
        # pas fiables. C'est ce qui fait marcher le téléchargement partout.
        contexte = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(URL_CSV_OFFICIEL.format(code),
                                    timeout=15, context=contexte) as reponse:
            texte = reponse.read().decode("utf-8-sig")
        lignes, _ = _filtrer_sons_systeme(
            lire_lignes_csv(io.StringIO(texte)), langue)
        if not lignes:
            raise ValueError("le fichier reçu ne contient aucun son système")
    except Exception:
        if not os.path.exists(cache):
            raise
        lignes, _ = lire_csv_sons_systeme(cache, langue)
        if not lignes:
            raise
        return lignes, dossier, True

    # La copie n'est écrite qu'une fois le fichier reconnu valable : une page
    # d'erreur de GitHub ne peut pas remplacer la bonne copie.
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        temporaire = cache + ".tmp"
        with open(temporaire, "w", encoding="utf-8", newline="") as fichier:
            fichier.write(texte)
        os.replace(temporaire, cache)
    except OSError:
        pass  # une copie de secours, ce n'est pas vital
    return lignes, dossier, False


def lire_csv_sons_systeme(chemin, langue=None):
    """Lit un CSV de sons système (format officiel ou format carte).

    Renvoie (lignes, langue) : lignes = [(nom, phrase)] et langue déduite du
    chemin si le fichier la contient (« fr » pour « SOUNDS/fr/SYSTEM »), sinon
    celle qu'on lui donne.
    """
    try:
        with open(chemin, encoding="utf-8-sig") as fichier:
            return _filtrer_sons_systeme(lire_lignes_csv(fichier), langue)
    except UnicodeDecodeError:
        # Un CSV préparé sous Windows peut être en Latin-1 : les accents ne
        # sont alors pas lisibles en UTF-8, mais le fichier reste exploitable.
        with open(chemin, encoding="latin-1") as fichier:
            return _filtrer_sons_systeme(lire_lignes_csv(fichier), langue)


def _filtrer_sons_systeme(morceaux, langue=None):
    """Garde les lignes du dossier SYSTEM, et rien d'autre."""
    lignes = []
    langues = {}
    if not morceaux:
        return lignes, langue or ""

    # Les deux formats se reconnaissent à leur en-tête. On lit les colonnes
    # par leur NOM pour le fichier officiel : l'ordre pourrait changer.
    entete = [c.strip().lower() for c in morceaux[0]]
    officiel = all(c in entete for c in ("translation", "path", "filename"))
    if officiel:
        i_phrase = entete.index("translation")
        i_dossier = entete.index("path")
        i_nom = entete.index("filename")
        debut = 1
    else:
        i_dossier, i_nom, i_phrase = 0, 1, 2
        debut = 0

    for colonnes in morceaux[debut:]:
        # Une phrase peut manquer : la ligne ne sert alors à rien.
        if len(colonnes) < max(i_dossier, i_nom, i_phrase) + 1:
            continue
        dossier = colonnes[i_dossier].strip().replace("\\", "/").rstrip("/")
        if officiel:
            # Path vaut « SYSTEM » ou rien (racine).
            if dossier.upper() != "SYSTEM":
                continue
        elif not dossier.upper().endswith("/SYSTEM"):
            continue
        nom = colonnes[i_nom].strip()
        if nom.lower().endswith(".wav"):
            nom = nom[:-4]
        phrase = colonnes[i_phrase].strip()
        if not nom or not phrase:
            continue
        lignes.append((nom, phrase))
        if not officiel:
            # La langue se lit dans le chemin, pas dans une liste écrite en
            # dur : une carte en allemand, en japonais… marche pareil.
            parties = [p for p in dossier.split("/") if p]
            if len(parties) >= 2:
                langues[parties[-2]] = langues.get(parties[-2], 0) + 1

    if officiel:
        return lignes, langue or ""
    detectee = max(langues, key=langues.get) if langues else ""
    return lignes, detectee or (langue or "")


def trier_sons_systeme(lignes):
    """Écarte les noms que la radio ne lirait pas, et les doublons.

    Renvoie (taches, refuses) : taches = [(nom, phrase)] à fabriquer,
    refuses = [(nom, raison)] à signaler. On ne s'arrête jamais au premier
    problème : un seul nom fautif ne doit pas priver l'utilisateur de tous
    les autres sons.
    """
    taches, refuses, vus = [], [], {}
    for rang, (nom, phrase) in enumerate(lignes, start=1):
        souci = probleme_nom(nom)
        if souci is None:
            # Deux lignes au même nom : la seconde écraserait la première en
            # silence. Majuscules ignorées, comme sur le disque d'un Mac.
            deja = vus.get(nom.lower())
            if deja:
                souci = t("pb_doublon", n=deja)
            else:
                vus[nom.lower()] = rang
        if souci:
            refuses.append((nom or t("pb_vide"), souci))
        elif phrase:
            taches.append((nom, phrase))
    return taches, refuses


# ------------------------------------------------------------------
# Lecture d'un son
# ------------------------------------------------------------------
class LectureAudio:
    """Joue un fichier sonore, et permet de l'interrompre.

    Même interface qu'un subprocess.Popen — wait() et terminate() — pour que
    le reste du code n'ait pas à savoir COMMENT on joue le son :
      * macOS : afplay, présent d'origine ;
      * ailleurs : soundfile lit le fichier, sounddevice le joue.
    """

    def __init__(self, chemin):
        self._processus = None
        self._sd = None
        self._arret = threading.Event()
        # Renseigné si le son n'a pas pu démarrer (pas de carte son, pilote
        # absent…) : l'appelant peut alors le dire, au lieu de laisser le
        # bouton « Arrêter » allumé sans rien qui joue.
        self.erreur = None
        if sys.platform == "darwin" and os.path.exists(AFPLAY):
            self._processus = subprocess.Popen(
                [AFPLAY, chemin],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        # Import paresseux : sur macOS, ces bibliothèques ne servent à rien.
        import soundfile as sf
        import sounddevice as sd

        try:
            donnees, taux = sf.read(chemin, dtype="float32")
            self._sd = sd
            sd.play(donnees, taux)
        except Exception as e:
            self.erreur = e
            self._sd = None

    def wait(self):
        """Attend la fin de la lecture (interruptible par terminate)."""
        if self._processus is not None:
            self._processus.wait()
            return
        # sd.wait() attend que le périphérique ait réellement joué tout ce
        # qu'on lui a donné. L'ancienne boucle sortait dès que le flux
        # n'était plus « actif », puis appelait sd.stop() : or le pilote
        # Windows garde un tampon de 50 à 200 ms, et cette coupure tronquait
        # la fin de la phrase — à l'ÉCOUTE seulement, le fichier écrit étant
        # intact. Signalé par un utilisateur le 22 octobre 2026, et cohérent
        # avec ce que Richard entend : son Mac ne coupe pas (afplay attend la
        # fin), son PC si.
        # terminate() appelle sd.stop() depuis l'autre fil : c'est ce qui
        # débloque cet appel quand on appuie sur « Arrêter ».
        if self._sd is None:            # le son n'a pas démarré : rien à attendre
            return
        try:
            if self._sd.get_stream() is None:
                return
            self._sd.wait()
        except Exception:
            pass

    def terminate(self):
        """Coupe la lecture tout de suite."""
        self._arret.set()
        if self._processus is not None:
            try:
                self._processus.terminate()
            except Exception:
                pass
            return
        try:
            self._sd.stop()
        except Exception:
            pass


def reprendre_ancienne_liste():
    """Récupère les listes des versions précédentes, une seule fois."""
    ancien_csv = os.path.join(ANCIEN_DIR, "liste_des_voix.csv")
    if os.path.exists(ancien_csv) and not os.path.exists(CSV_FILE):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            shutil.copy2(ancien_csv, CSV_FILE)
        except OSError:
            pass  # tant pis : on repartira de la liste par défaut
    # Une seule liste existait avant : elle devient la liste française, pour
    # ne pas perdre le travail déjà fait.
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(CSV_FILE) and not os.path.exists(chemin_liste("fr")):
            shutil.copy2(CSV_FILE, chemin_liste("fr"))
    except OSError:
        pass

# Chemin du logo. En version compilée, PyInstaller range les fichiers joints
# (le logo) dans un dossier temporaire : on regarde donc à plusieurs endroits.
DOSSIER_SCRIPT = os.path.dirname(os.path.abspath(__file__))


# Ce que la fenêtre occupe en hauteur EN DEHORS de la liste : les marges, la
# rangée de boutons, l'en-tête du tableau, la ligne d'état et les boutons du
# bas. Sert à décider de la taille du logo sur un petit écran (voir
# VoxPackApp._taille_logo).
def place_hors_liste():
    return (ESPACE_HAUT + ESPACE_LOGO_BOUTONS + BTN_H + ESPACE_BOUTONS_LISTE
            + 40                      # en-tête du tableau : Nom / Phrase
            + ESPACE_LISTE_LEDS + HAUTEUR_INFO + ESPACE_LEDS_BOUTONS
            + 66                      # rangée du bas + les liens empilés
            + ESPACE_BAS + 26)        # marges internes de la liste


def geometrie_fenetre(ecran_large, ecran_haut):
    """Taille de la fenêtre et du logo, adaptées à l'écran.

    Sur un écran confortable, l'application garde exactement l'allure pour
    laquelle elle a été dessinée. Sur un écran court, elle devient plus
    compacte : un logo modeste et moins de lignes, mais des lignes lisibles.
    Une fenêtre qui remplit tout l'écran avec sept lignes tassées n'aide
    personne.
    """
    confortable = ecran_haut >= ECRAN_CONFORTABLE
    lignes = LIGNES_GRAND_ECRAN if confortable else LIGNES_PETIT_ECRAN
    logo = LARGEUR_LOGO if confortable else LARGEUR_LOGO_PETIT

    largeur = min(LARGEUR_FENETRE, ecran_large - 40)
    # + 4 : la petite marge sous le logo. + 40 : on ne colle pas la liste aux
    # boutons du bas.
    hauteur_voulue = (place_hors_liste() + int(logo / 2.06) + 4
                      + lignes * (HAUTEUR_LIGNE + 10) + 40)
    marge = 60 if sys.platform.startswith("win") else 100
    hauteur = min(HAUTEUR_FENETRE, hauteur_voulue, ecran_haut - marge)
    return largeur, max(hauteur, 380), logo


def trouver_ressource(*morceaux):
    """Chemin d'un fichier livré avec l'application (logo, icône…).

    En version compilée, PyInstaller range ces fichiers dans un dossier
    temporaire (sys._MEIPASS) ; lancée depuis le code source, l'application
    les trouve simplement à côté d'elle.
    """
    pistes = []
    if getattr(sys, "frozen", False):
        pistes.append(getattr(sys, "_MEIPASS", ""))
        pistes.append(os.path.dirname(os.path.abspath(sys.executable)))
        pistes.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)),
                                   "..", "Resources"))
    pistes.append(DOSSIER_SCRIPT)
    for dossier in pistes:
        if dossier:
            chemin = os.path.join(dossier, *morceaux)
            if os.path.exists(chemin):
                return chemin
    return os.path.join(DOSSIER_SCRIPT, *morceaux)


def trouver_logo():
    return trouver_ressource("logo.png")


LOGO_PATH = trouver_logo()
# Le bandeau de la v2, pour la fenêtre d'aide ; à défaut, l'ancien logo.
LOGO_AIDE_PATH = trouver_ressource("bandeau-vp2.webp")
if not os.path.exists(LOGO_AIDE_PATH):
    LOGO_AIDE_PATH = LOGO_PATH

# ------------------------------------------------------------------
# Langues
# ------------------------------------------------------------------
# UNE seule langue, LANGUE_UI, pour toute l'application. Elle commande :
#
#   - les TEXTES (boutons, menus, aide, alertes), par TEXTES et t() ;
#   - les VOIX proposées (VOIX[LANGUE_UI]) ;
#   - la LISTE de phrases (liste_fr.csv ou liste_en.csv, et la liste par
#     défaut de cette langue).
#
# Elle suit celle du système au premier lancement, puis se change dans le menu
# Fichier > Langue. La propriété VoxPackApp.langue renvoie LANGUE_UI : le code
# qui parlait de « la langue des voix » suit donc l'interface sans réécriture.
#
# Avoir une seule langue évite un mélange absurde : une interface anglaise
# avec des voix et une liste françaises.
LANGUE_UI = "fr"

LANGUES = ["fr", "en", "de"]


def code_langue_systeme(valeur):
    """Code Vox-Pack d'un code de langue du système.

    « fr-FR » et « fr_FR.UTF-8 » donnent « fr » ; « zh-Hans » et « zh-CN »
    donnent « cn », « zh-TW »/« zh-Hant » donnent « tw », « zh-HK » donne
    « hk ». Renvoie None si la langue n'est pas l'une des quinze.
    """
    texte = str(valeur or "").strip().lower().replace("_", "-")
    if not texte:
        return None
    if texte.startswith("zh"):
        if "hk" in texte or "mo" in texte:
            return "hk"
        if "tw" in texte or "hant" in texte:
            return "tw"
        return "cn"
    debut = texte[:2]
    if debut in ("fr", "en", "de", "es", "it", "pt", "ru", "sv",
                 "uk", "cs", "da", "ja"):
        return debut
    return None


def langue_du_systeme():
    """Langue d'interface au tout premier lancement : celle du système.

    Les quinze langues de l'application sont reconnues. Toute autre langue
    donne l'anglais, qui a le plus de chances d'être comprise.

    Attention : lancée depuis un terminal ou un éditeur, l'application hérite
    d'un LANG qui vaut souvent « C.UTF-8 » même sur un Mac en français. Sous
    macOS, la langue réellement choisie par l'utilisateur se lit donc dans les
    préférences du système, et non dans les variables d'environnement : sans
    cela, Richard aurait vu l'application en anglais chez lui.
    """
    essais = []
    if sys.platform == "darwin":
        # La langue d'interface choisie par l'utilisateur est la première de
        # AppleLanguages ; AppleLocale ne donne que la région (un Mac en
        # français avec une région étrangère passerait en anglais).
        try:
            sortie = subprocess.run(["defaults", "read", "-g", "AppleLanguages"],
                                    capture_output=True, text=True, timeout=5)
            if sortie.returncode == 0:
                for valeur in re.findall(r'"([^"]+)"', sortie.stdout):
                    code = code_langue_systeme(valeur)
                    if code:
                        return code
        except Exception:
            pass
        try:
            sortie = subprocess.run(["defaults", "read", "-g", "AppleLocale"],
                                    capture_output=True, text=True, timeout=5)
            if sortie.returncode == 0:
                essais.append(sortie.stdout.strip())
        except Exception:
            pass
    for fonction in (locale.getlocale, getattr(locale, "getdefaultlocale", None)):
        if fonction is None:
            continue
        try:
            valeur = fonction()
            essais.append(valeur[0] if isinstance(valeur, tuple) else valeur)
        except Exception:
            pass
    essais.append(os.environ.get("LANG", ""))
    essais.append(os.environ.get("LC_ALL", ""))
    for essai in essais:
        code = code_langue_systeme(essai)
        if code:
            return code
    return "en"


# Tous les textes de l'application, dans les trois langues. Les clés sont les
# mêmes dans les trois tables : c'est ce qui garantit qu'aucun texte n'est
# oublié d'un côté (voir cles_manquantes).
#
# Les champs entre accolades ({nom}, {max}…) sont remplis par t().
TEXTES = {
    "fr": {
        # ----- Titres du panneau (écran de la maquette) -----
        "langue": "Langue",
        "voix": "Voix",
        "niveau": "Niveau",
        "allure": "Vitesse",
        "robot": "Robot",
        "nom": "Nom",
        "phrase": "Phrase",
        # ----- Boutons de la fenêtre principale -----
        "ajouter": "Ajouter",
        "supprimer": "Supprimer",
        "ecouter": "Écouter",
        "arreter": "■  Arrêter",
        "tout": "Tout",
        "rien": "Rien",
        "lets_go": "Let's Go",

        # ----- Colonnes de la liste -----

        # ----- Voix : genre et accent -----
        "genre_f": "Femme",
        "genre_h": "Homme",
        "genre_e": "Enfant",
        "accent_france": "France",
        "accent_suisse": "Suisse",
        "accent_belgique": "Belgique",
        "accent_quebec": "Québec",
        "accent_usa": "USA",
        "accent_uk": "Royaume-Uni",
        "accent_irlande": "Irlande",
        "accent_allemagne": "Allemagne",

        # ----- Noms des langues -----
        "langue_fr": "Français",
        "langue_en": "English",
        "langue_de": "Deutsch",

        # ----- Ligne d'état (sous la barre de leds) -----
        "etat_recherche_service": "Recherche des voix sur le service TTS…",
        "etat_recherche_voix": "Recherche de la voix ({fait}/{total}) — {nom}…",
        "etat_generation_wav":
            "Génération du fichier WAV ({fait}/{total}) — {nom}…",
        "etat_avance": "{fait} fichier{s} sur {total}  —  {nom}",
        "etat_voix_retirees":
            "{n} voix retirée{s} par le service — liste mise à jour",
        "etat_voix_remises": "Voix indisponibles : liste remise par défaut",
        "etat_langue_voix": "Langue : {langue} — {n} voix disponibles",
        "etat_sons_arret": "Arrêt demandé — fin du fichier en cours…",
        "etat_csv_telechargement":
            "Téléchargement de la liste officielle EdgeTX…",

        # ----- Noms de fichiers refusés -----
        "pb_vide": "nom vide",
        "pb_long": "{n} caractères (max {max})",
        "pb_espace": "pas d'espace",
        "pb_accent": "pas d'accent",
        "pb_caractere": "caractère « {c} » interdit",
        "pb_doublon": "déjà utilisé (ligne {n})",

        # ----- Ligne ajoutée à la main -----
        "nouvelle_ligne": "nouveau",
        "texte_a_dire": "Texte à prononcer",

        # ----- Pannes du service de voix -----
        "err_refus": "service refusé (voix indisponible ou mise à jour à faire)",
        "err_voix_absente":
            "voix supprimée par le service : choisissez-en une autre",
        "err_lent": "le service n'a pas répondu à temps (connexion lente ?)",
        "err_illisible":
            "Le service de voix a renvoyé une réponse illisible. "
            "Réessayez dans un instant.",
        "err_muet":
            "Le service de voix a renvoyé un son vide : la phrase n'a pas "
            "été prononcée. Réessayez, ou changez la phrase.",
        "err_reseau": "pas de connexion Internet",
        "err_reseau_detail":
            "Impossible de joindre le service de voix Microsoft. Vérifie ta "
            "connexion Internet (VPN, pare-feu, DNS), puis réessaie.",
        "msg_reseau_coupe":
            "Connexion Internet interrompue : la génération a été arrêtée. "
            "Vérifie ta connexion, puis relance.",

        # ----- Menu -----
        "menu_fichier": "Fichier",
        "menu_exporter": "Exporter la liste…",
        "menu_importer": "Importer une liste…",
        "menu_defaut": "Charger la liste par défaut",
        "menu_sons_systeme": "Créer les sons système…",
        "menu_quitter": "Quitter",
        "menu_langue": "Langue",

        # ----- Exporter / Importer -----
        "titre_export": "Exporter la liste",
        "titre_import": "Importer une liste",
        "titre_dossier": "Dossier de destination des WAV",
        "titre_dossier_systeme": "Dossier où créer le dossier SYSTEM",
        "nom_export": "ma-liste-vox-pack.csv",
        "type_csv": "Fichier CSV",
        "type_txt": "Fichier texte",
        "type_tous": "Tous les fichiers",
        "entete_nom": "nom",
        "entete_phrase": "phrase",
        "msg_export_echec": "L'export a échoué.\n\n{err}",
        "msg_export_ok": "{n} ligne{s} exportée{s} dans :\n\n{chemin}",
        "msg_import_illisible": "Impossible de lire ce fichier.\n\n{err}",
        "msg_import_vide": "Ce fichier ne contient aucune ligne.",
        "msg_import_confirmer":
            "Remplacer la liste actuelle ({avant} ligne{s1}) par ces "
            "{apres} ligne{s2} ?",
        "msg_import_oui": "Oui, remplacer",
        "question_defaut":
            "Remplacer votre liste par les {n} phrases "
            "{langue} livrées avec l'application ?",
        "oui_remplacer": "Oui, remplacer",
        "adjectif_fr": "françaises",
        "adjectif_en": "anglaises",
        "adjectif_de": "allemandes",
        "msg_import_ok": "{n} ligne{s} importée{s}.",
        "msg_csv_aucun_systeme":
            "La liste officielle d'EdgeTX ne contient aucun son système.\n\n"
            "Réessayez plus tard : le fichier a peut-être changé.",
        "msg_csv_officiel_echec":
            "La liste officielle d'EdgeTX n'a pas pu être téléchargée.\n\n"
            "Vérifiez la connexion Internet, puis réessayez.\n\n{err}",

        # ----- Boutons et messages courants -----
        "annuler": "Annuler",
        "compris": "Compris",
        "fermer": "Fermer",
        "choisir": "Choisir",
        "voix_normale": "Voix normale",
        "ouvrir_dossier": "Ouvrir le dossier",
        "btn_supprimer": "Supprimer",

        # ----- Suppression, aperçu, génération -----
        "msg_supprimer_rien": "Cochez au moins une ligne à supprimer.",
        "msg_supprimer_tout":
            "Vous allez supprimer TOUTE la liste.\n\n"
            "Elle sera reconstruite automatiquement "
            "au prochain démarrage de l'application.\n\n"
            "Voulez-vous continuer ?",
        "msg_ecouter_rien": "Cochez une ligne à écouter.",
        "etat_ecoute": "Écoute {rang}/{total} — {nom}",
        "msg_apercu_echec": "L'aperçu n'a pas pu être joué.\n\n{err}",
        "msg_audio_absent":
            "Aucune sortie audio sur cet ordinateur : l'aperçu ne peut pas "
            "être joué. Les fichiers sont fabriqués normalement.",
        "msg_generer_rien": "Cochez au moins une ligne à générer.",
        "msg_generer_aucune":
            "Aucune ligne valide à générer.\n\n"
            "Il faut un nom de fichier correct ET une phrase.",
        "msg_genere_deja":
            "Une génération est déjà en cours.\n\n"
            "Attendez qu'elle se termine.",
        "msg_sauvegarde_echec":
            "La liste n'a pas pu être enregistrée.\n\n"
            "{err}\n\n"
            "Un autre programme utilise peut-être ce fichier (antivirus, "
            "OneDrive), ou Windows protège le dossier Documents : dans "
            "Sécurité Windows → « Contrôle des dossiers », autorise Vox-Pack.",
        "msg_bilan_echecs":
            "{reussis} fichier{s1} créé{s1} sur {total}.\n\n"
            "{problemes} problème{s2} :\n{detail}",
        "msg_autres": "• … et {n} autre(s)",
        "msg_succes": "Vos voix sont prêtes.\n\n{dossier}",
        "msg_sons_succes":
            "{n} fichier{s} système créé{s} dans :\n\n{dossier}",
        "msg_sons_copier":
            "Copiez ce dossier SYSTEM dans SOUNDS/{langue}/ de votre carte, "
            "en remplaçant l'ancien.",
        "msg_sons_bilan":
            "{reussis} fichier{s1} système créé{s1} sur {total}.\n\n"
            "{problemes} problème{s2} :\n{detail}",
        "msg_sons_problemes": "{problemes} problème{s2} :\n{detail}",
        "msg_sons_arrete":
            "Génération arrêtée.\n\n{n} fichier{s} créé{s} dans :\n\n{dossier}",
        "msg_sons_cache":
            "Liste officielle non téléchargée : la copie enregistrée "
            "a été utilisée.",
        "msg_dossier_echec":
            "Impossible de créer le dossier de destination.\n\n{err}",

        # ----- Fenêtre de soutien -----
        "titre_soutien": "Soutenir le projet",
        "soutien_question": "Mon application te sert ou te plaît ?",
        "soutien_cafe": "Offre-moi un café",
        "soutien_oui": "Oui, avec plaisir !",
        "soutien_plus_tard": "Une prochaine fois",
        "soutien_ne_plus": "Ne plus demander",

        # ----- Fenêtre d'aide -----
        "titre_aide": "Aide — Vox-Pack",
        "aide_titre": "Comment utiliser l'application",
        # ----- 1. Voix -----
        "aide_1": "1. Choisissez une voix",
        "aide_1a":
            "L'application existe en quinze langues ; au premier lancement, "
            "elle s'ouvre dans celle du système. Les voix proposées sont "
            "celles de la langue choisie, et la voix en cours est cochée. "
            "Vous pouvez changer de langue dans le menu.",
        "aide_officielle":
            "La ★ marque la voix officielle d'EdgeTX pour cette langue : même "
            "voix et même vitesse que sur la radio.",
        "aide_robot_titre": "🤖  Voix de robot",
        "aide_robot1":
            "À droite de la fenêtre, quatre pastilles : Robot 1 à 3 et HAL 9000. "
            "HAL 9000 impose sa propre voix, indépendamment du menu. "
            "Aucune cochée : la voix normale.",
        "aide_robot2":
            "Cliquez une pastille, puis « Écouter » : l'effet s'applique à la "
            "voix choisie. Recliquez la pastille allumée pour revenir à la "
            "normale.",
        "aide_robot3":
            "L'effet s'applique aussi aux fichiers de la liste et aux sons "
            "système.",
        "aide_1b":
            "Pour changer de langue : menu « Fichier », puis « Langue ». Les "
            "textes, les voix et la liste changent ensemble, et votre voix "
            "est retrouvée au prochain démarrage.",
        # ----- 2. Liste -----
        "aide_2": "2. Gérez la liste",
        "aide_2a":
            "« Ajouter » crée une ligne ; « Supprimer » efface les lignes "
            "cochées.",
        "aide_2b": "Modifiez une ligne en tapant directement dans ses cases.",
        "aide_2c":
            "Pour cocher plusieurs lignes d'un coup : cliquez sur la "
            "première case, puis Majuscule + clic sur la dernière.",
        "aide_2d":
            "Pour laisser un silence, tapez un « > » ou plus dans la phrase : "
            "chaque « > » vaut une demi-seconde. « Moteur armé >> Moteur "
            "coupé » laisse une seconde entre les deux, et « >>> Moteur armé "
            "» retarde l'annonce d'une seconde et demie. Dix secondes au "
            "maximum.",
        "aide_nom1":
            "Le nom du fichier ne doit pas dépasser 8 caractères et ne doit "
            "contenir ni accent ni espace.",
        # ----- 3. Cocher -----
        "aide_3": "3. Cochez les lignes à générer",
        "aide_3a": "La case de l'en-tête coche toutes les lignes ; la décocher les décoche toutes.",
        "aide_3b": "Pour une seule ligne, cochez uniquement celle-ci.",
        # ----- 4. Écouter -----
        "aide_4": "4. Écoutez un aperçu",
        "aide_4a":
            "Cochez une ou plusieurs lignes, puis cliquez sur « Écouter » : "
            "elles sont lues l'une après l'autre.",
        # ----- 5. Générer -----
        "aide_5": "5. Générez les fichiers",
        "aide_5a": "Cliquez sur « Let's Go », puis choisissez un dossier.",
        "aide_5b":
            "Sous la barre de leds, une ligne indique à chaque instant ce que "
            "fait l'application : recherche de la voix, puis génération du "
            "fichier WAV.",
        # ----- Niveau et vitesse -----
        "aide_6_titre": "6. Réglez le niveau et la vitesse",
        "aide_6a":
            "Le curseur NIVEAU va de −6 à +6 dB : il rend le fichier plus "
            "fort ou plus doux, sans jamais saturer. À 0 dB, rien n'est "
            "modifié.",
        "aide_6b":
            "Le curseur VITESSE règle le débit de la voix. Le cran du milieu "
            "retient 0 %, et un double-clic sur la piste y revient. Les deux "
            "réglages s'appliquent à l'aperçu, aux fichiers et aux sons "
            "système.",
        # ----- Internet -----
        "aide_net_titre": "🌐  Connexion Internet nécessaire",
        "aide_net1":
            "Les voix ne sont pas dans l'application : elles viennent du "
            "service de synthèse vocale de Microsoft. Une connexion Internet "
            "est donc indispensable pour générer les fichiers.",
        "aide_net4":
            "Le texte de vos phrases est envoyé à Microsoft pour être "
            "prononcé : n'y mettez rien de confidentiel.",
        "aide_net6": "Sans Internet, l'application vous le dira clairement.",
        "aide_net7":
            "Si une voix n'existe plus chez Microsoft, elle disparaît toute "
            "seule du menu au démarrage de l'application.",
        # ----- Sauvegarde -----
        "aide_sauv_titre": "💾  Sauvegarde automatique",
        "aide_sauv1": "Vos modifications sont enregistrées dans :",
        # ----- Liste par défaut -----
        "aide_def_titre": "♻️  Liste par défaut",
        "aide_def1":
            "Si vous supprimez TOUTE la liste, elle sera reconstruite "
            "automatiquement au prochain démarrage.",
        "aide_def5":
            "Chaque langue a SA liste. Changer la langue dans le menu change "
            "donc aussi la liste, et votre travail de l'autre langue est "
            "conservé tel quel.",
        "aide_def3":
            "Si vous gardez au moins 1 ligne, vous repartez de cette base "
            "pour créer votre liste personnalisée.",
        # ----- Export / import -----
        "aide_exp_titre": "📂  Exporter / Importer une liste",
        "aide_exp1":
            "Le menu « Fichier » se trouve dans la barre de menus du système "
            "sur Mac, et en haut de la fenêtre sur PC.",
        "aide_exp3":
            "« Exporter la liste… » enregistre la liste pour la sauvegarder "
            "ou la partager.",
        "aide_exp4":
            "« Importer une liste… » remplace la liste actuelle par un "
            "fichier : un nom et une phrase par ligne, séparés par une "
            "virgule. L'application demande confirmation.",
        # ----- Sons système -----
        "aide_sys_titre": "📻  Créer les sons système de la radio",
        "aide_sys1": "Le menu « Fichier » propose « Créer les sons système… ».",
        "aide_sys2":
            "L'application télécharge la liste officielle d'EdgeTX, refait "
            "les sons SYSTEM avec la voix choisie en haut de la fenêtre, et "
            "crée un dossier SYSTEM/ dans le dossier que vous indiquez.",
        "aide_sys3":
            "Le temps dépend de l'occupation du service de voix et de votre "
            "connexion Internet.",
        "aide_sys4":
            "Pendant l'opération, « Let's Go » devient « ■ Arrêter » : le "
            "fichier en cours se termine, et les fichiers déjà créés restent.",
        "aide_sys5":
            "Ensuite, copiez le dossier SYSTEM/ dans SOUNDS/<langue>/ de "
            "votre carte SD, en remplaçant l'ancien. Vos sons personnels et "
            "ceux des scripts ne sont pas touchés.",
        # ----- Longueur des noms -----
        "aide_edge_titre": "📏  Longueur des noms selon votre EdgeTX",
        "aide_edge1":
            "La radiocommande lit le nom du fichier : il ne doit pas être "
            "trop long, sinon elle ne le trouve pas.",
        "aide_edge3":
            "EdgeTX 2.11 et plus récent : 8 caractères, sur toutes les radios.",
        "aide_edge5":
            "EdgeTX 2.10 et plus ancien : 6 caractères sur les radios couleur "
            "et les petites radios noir et blanc. Les X9D et X9E acceptent "
            "8 caractères.",
        "aide_edge8":
            "En cas de doute, restez à 6 caractères : ils seront lus sur "
            "toutes les radios et toutes les versions.",
        # ----- Format -----
        "aide_fmt_titre": "🎵  Format des fichiers",
        "aide_fmt1": "Les WAV générés sont au format EdgeTX :",
        "aide_fmt2": "16 bits, 32 kHz, mono.",
        # ----- Bas de page -----
        "aide_soutien": "Mon application vous sert ou vous plaît ?",
        "aide_lien": "Offrez-moi un café  ·  ko-fi.com/ritchy_lab",
        "aide_maj_titre": "🔄  Mises à jour",
        "aide_maj":
            "Les nouvelles versions sont publiées sur la page Releases. "
            "L'application vérifie automatiquement au démarrage : si une "
            "version plus récente existe, une petite fenêtre vous propose "
            "de la télécharger dans votre dossier Téléchargements.",
        "maj_titre": "Mise à jour disponible",
        "maj_texte":
            "La version {version} est disponible.\n"
            "Vous utilisez la version {actuelle}.",
        "maj_telecharger": "Télécharger",
        "maj_plus_tard": "Plus tard",
        "maj_telechargement": "Téléchargement…",
        "maj_telecharge_mac":
            "Téléchargé dans :\n{chemin}\n\n"
            "Ouvre le dossier, puis remplace l'ancienne application par "
            "la nouvelle.",
        "maj_telecharge_win":
            "Téléchargé dans :\n{chemin}\n\n"
            "Ferme Vox-Pack, puis lance le nouveau fichier.",
        "maj_ouvrir_dossier": "Ouvrir le dossier",
        "maj_page": "Voir la page",
        "maj_fermer": "Fermer",
        "maj_echec":
            "Le téléchargement a échoué. Tu peux ouvrir la page Releases.",
        "aide_github":
            "Nouvelles versions  ·  github.com/ritchy-lab/Vox-Pack/releases",
        "aide_credits": "Créé avec un brainstorming avec une IA",
        "aide_merci": "Merci à Ralf pour la traduction allemande.",
        "aide_ecran": "Version {version} — écran {ecran} — fenêtre {fenetre}",
    },

    "en": {
        # ----- Panel titles (mockup screen) -----
        "langue": "Language",
        "voix": "Voice",
        "niveau": "Level",
        "allure": "Speed",
        "robot": "Robot",
        "nom": "Name",
        "phrase": "Phrase",
        "sons_systeme": "System sounds",
        # ----- Main window buttons -----
        "ajouter": "Add",
        "supprimer": "Delete",
        "ecouter": "Listen",
        "arreter": "■  Stop",
        "tout": "All",
        "rien": "None",
        "lets_go": "Let's Go",

        # ----- List columns -----

        # ----- Voices: gender and accent -----
        "genre_f": "Female",
        "genre_h": "Male",
        "genre_e": "Child",
        "accent_france": "France",
        "accent_suisse": "Switzerland",
        "accent_belgique": "Belgium",
        "accent_quebec": "Quebec",
        "accent_usa": "USA",
        "accent_uk": "United Kingdom",
        "accent_irlande": "Ireland",
        "accent_allemagne": "Germany",

        # ----- Language names -----
        "langue_fr": "French",
        "langue_en": "English",
        "langue_de": "German",

        # ----- Status line (under the LED bar) -----
        "etat_recherche_service": "Looking for voices on the TTS service…",
        "etat_recherche_voix": "Fetching voice ({fait}/{total}) — {nom}…",
        "etat_generation_wav": "Building WAV file ({fait}/{total}) — {nom}…",
        "etat_avance": "{fait} file{s} of {total}  —  {nom}",
        "etat_voix_retirees":
            "{n} voice{s} removed by the service — list updated",
        "etat_voix_remises": "Voices unavailable: list reset to default",
        "etat_langue_voix": "Language: {langue} — {n} voices available",
        "etat_sons_arret": "Stop requested — finishing the current file…",
        "etat_csv_telechargement":
            "Downloading the official EdgeTX list…",

        # ----- Rejected file names -----
        "pb_vide": "empty name",
        "pb_long": "{n} characters (max {max})",
        "pb_espace": "no spaces allowed",
        "pb_accent": "no accents allowed",
        "pb_caractere": "character \"{c}\" not allowed",
        "pb_doublon": "already used (line {n})",

        # ----- Line added by hand -----
        "nouvelle_ligne": "new",
        "texte_a_dire": "Text to be spoken",

        # ----- Voice service failures -----
        "err_refus": "service refused (voice unavailable, or update needed)",
        "err_voix_absente": "voice removed by the service: pick another one",
        "err_lent": "the service did not answer in time (slow connection?)",
        "err_illisible":
            "The voice service returned an unreadable response. "
            "Try again in a moment.",
        "err_muet":
            "The voice service returned an empty sound: the phrase was not "
            "spoken. Try again, or change the phrase.",
        "err_reseau": "no Internet connection",
        "err_reseau_detail":
            "Cannot reach Microsoft's voice service. Check your Internet "
            "connection (VPN, firewall, DNS), then try again.",
        "msg_reseau_coupe":
            "Internet connection lost: generation was stopped. Check your "
            "connection, then try again.",

        # ----- Menu -----
        "menu_fichier": "File",
        "menu_exporter": "Export list…",
        "menu_importer": "Import a list…",
        "menu_defaut": "Load the default list",
        "menu_sons_systeme": "Create the system sounds…",
        "menu_quitter": "Quit",
        "menu_langue": "Language",

        # ----- Export / Import -----
        "titre_export": "Export the list",
        "titre_import": "Import a list",
        "titre_dossier": "Folder for the generated WAV files",
        "titre_dossier_systeme": "Folder where the SYSTEM folder will be created",
        "nom_export": "my-vox-pack-list.csv",
        "type_csv": "CSV file",
        "type_txt": "Text file",
        "type_tous": "All files",
        "entete_nom": "name",
        "entete_phrase": "phrase",
        "msg_export_echec": "The export failed.\n\n{err}",
        "msg_export_ok": "{n} line{s} exported to:\n\n{chemin}",
        "msg_import_illisible": "This file cannot be read.\n\n{err}",
        "msg_import_vide": "This file contains no line.",
        "msg_import_confirmer":
            "Replace the current list ({avant} line{s1}) with these "
            "{apres} line{s2}?",
        "msg_import_oui": "Yes, replace",
        "question_defaut":
            "Replace your list with the {n} {langue} phrases "
            "shipped with the application?",
        "oui_remplacer": "Yes, replace",
        "adjectif_fr": "French",
        "adjectif_en": "English",
        "adjectif_de": "German",
        "msg_import_ok": "{n} line{s} imported.",
        "msg_csv_aucun_systeme":
            "The official EdgeTX list contains no system sound.\n\n"
            "Try again later: the file may have changed.",
        "msg_csv_officiel_echec":
            "The official EdgeTX list could not be downloaded.\n\n"
            "Check the Internet connection, then try again.\n\n{err}",

        # ----- Common buttons and messages -----
        "annuler": "Cancel",
        "compris": "Got it",
        "fermer": "Close",
        "choisir": "Choose",
        "voix_normale": "Normal voice",
        "ouvrir_dossier": "Open the folder",
        "btn_supprimer": "Delete",

        # ----- Deleting, preview, generation -----
        "msg_supprimer_rien": "Tick at least one line to delete.",
        "msg_supprimer_tout":
            "You are about to delete the WHOLE list.\n\n"
            "It will be rebuilt automatically the next time the application "
            "starts.\n\n"
            "Do you want to continue?",
        "msg_ecouter_rien": "Tick a line to listen to.",
        "etat_ecoute": "Playing {rang}/{total} — {nom}",
        "msg_apercu_echec": "The preview could not be played.\n\n{err}",
        "msg_audio_absent":
            "No audio output on this computer: the preview cannot be played. "
            "Files are still generated.",
        "msg_generer_rien": "Tick at least one line to generate.",
        "msg_generer_aucune":
            "No valid line to generate.\n\n"
            "Each line needs a correct file name AND a phrase.",
        "msg_genere_deja":
            "A generation is already running.\n\n"
            "Wait for it to finish.",
        "msg_sauvegarde_echec":
            "The list could not be saved.\n\n"
            "{err}\n\n"
            "Another program may be using this file (antivirus, OneDrive), "
            "or Windows is protecting the Documents folder: in Windows "
            "Security → \"Controlled folder access\", allow Vox-Pack.",
        "msg_bilan_echecs":
            "{reussis} file{s1} created out of {total}.\n\n"
            "{problemes} problem{s2}:\n{detail}",
        "msg_autres": "• … and {n} more",
        "msg_succes": "Your voices are ready.\n\n{dossier}",
        "msg_sons_succes": "{n} system file{s} created in:\n\n{dossier}",
        "msg_sons_copier":
            "Copy this SYSTEM folder into SOUNDS/{langue}/ on your card, "
            "replacing the old one.",
        "msg_sons_bilan":
            "{reussis} system file{s1} created out of {total}.\n\n"
            "{problemes} problem{s2}:\n{detail}",
        "msg_sons_problemes": "{problemes} problem{s2}:\n{detail}",
        "msg_sons_arrete":
            "Generation stopped.\n\n{n} file{s} created in:\n\n{dossier}",
        "msg_sons_cache":
            "Official list not downloaded: the saved copy was used.",
        "msg_dossier_echec":
            "The destination folder could not be created.\n\n{err}",

        # ----- Support window -----
        "titre_soutien": "Support the project",
        "soutien_question": "Do you find my application useful?",
        "soutien_cafe": "Buy me a coffee",
        "soutien_oui": "Yes, with pleasure!",
        "soutien_plus_tard": "Maybe next time",
        "soutien_ne_plus": "Don't ask again",

        # ----- Help window -----
        "titre_aide": "Help — Vox-Pack",
        "aide_titre": "How to use the application",
        # ----- 1. Voice -----
        "aide_1": "1. Choose a voice",
        "aide_1a":
            "The application is available in fifteen languages; on first "
            "launch it opens in the system language. The voices offered are "
            "those of the chosen language, and the current voice is ticked. "
            "You can change the language from the menu.",
        "aide_officielle":
            "The ★ marks EdgeTX's official voice for that language: same "
            "voice and same speed as on the radio.",
        "aide_robot_titre": "🤖  Robot voices",
        "aide_robot1":
            "On the right of the window, four dots: Robot 1 to 3 and HAL 9000. "
            "HAL 9000 uses its own voice, regardless of the menu. "
            "None ticked: the normal voice.",
        "aide_robot2":
            "Click a dot, then “Listen”: the effect applies to the chosen "
            "voice. Click the lit dot again to return to normal.",
        "aide_robot3":
            "The effect also applies to the list files and the system "
            "sounds.",
        "aide_1b":
            "To change language: the “File” menu, then “Language”. Texts, "
            "voices and the list change together, and your voice is "
            "remembered the next time you start.",
        # ----- 2. List -----
        "aide_2": "2. Manage the list",
        "aide_2a": "“Add” creates a line; “Delete” removes the ticked lines.",
        "aide_2b": "Edit a line by typing directly in its boxes.",
        "aide_2c":
            "To tick several lines at once: click the first box, then Shift + "
            "click the last one.",
        "aide_2d":
            "To leave a silence, type one “>” sign or more in the phrase: "
            "each “>” is half a second. “Motor armed >> Motor off” leaves a "
            "second between the two, and “>>> Motor armed” delays the "
            "announcement by a second and a half. Ten seconds at most.",
        "aide_nom1":
            "The file name must not be longer than 8 characters and must not "
            "contain accents or spaces.",
        # ----- 3. Tick -----
        "aide_3": "3. Tick the lines to generate",
        "aide_3a": "The box in the header ticks every line; unticking it clears them all.",
        "aide_3b": "For a single line, tick just that one.",
        # ----- 4. Listen -----
        "aide_4": "4. Listen to a preview",
        "aide_4a":
            "Tick one or more lines, then click “Listen”: they are played "
            "one after another.",
        # ----- 5. Generate -----
        "aide_5": "5. Generate the files",
        "aide_5a": "Click “Let's Go”, then choose a folder.",
        "aide_5b":
            "Under the LED bar, a line tells you at every moment what the "
            "application is doing: fetching the voice, then building the WAV "
            "file.",
        # ----- Level and speed -----
        "aide_6_titre": "6. Set the level and the speed",
        "aide_6a":
            "The LEVEL slider goes from −6 to +6 dB: it makes the file "
            "louder or softer without ever clipping. At 0 dB, nothing is "
            "changed.",
        "aide_6b":
            "The SPEED slider sets the voice rate. The middle notch holds "
            "0 %, and double-clicking the track returns to it. Both settings "
            "apply to the preview, the files and the system sounds.",
        # ----- Internet -----
        "aide_net_titre": "🌐  Internet connection required",
        "aide_net1":
            "The voices are not inside the application: they come from "
            "Microsoft's speech service. An Internet connection is therefore "
            "essential to generate the files.",
        "aide_net4":
            "The text of your phrases is sent to Microsoft in order to be "
            "spoken: keep it free of anything private.",
        "aide_net6": "Without Internet, the application will tell you clearly.",
        "aide_net7":
            "If a voice no longer exists at Microsoft, it disappears from the "
            "menu by itself when the application starts.",
        # ----- Saving -----
        "aide_sauv_titre": "💾  Automatic saving",
        "aide_sauv1": "Your changes are saved in:",
        # ----- Default list -----
        "aide_def_titre": "♻️  Default list",
        "aide_def1":
            "If you delete the WHOLE list, it will be rebuilt automatically "
            "the next time you start.",
        "aide_def5":
            "Each language has ITS OWN list. Changing the language in the "
            "menu therefore also changes the list, and your work in the other "
            "language is kept as it is.",
        "aide_def3":
            "If you keep at least 1 line, you start from that base to build "
            "your own list.",
        # ----- Export / import -----
        "aide_exp_titre": "📂  Exporting / Importing a list",
        "aide_exp1":
            "The “File” menu is in the system menu bar on Mac, and at the top "
            "of the window on PC.",
        "aide_exp3":
            "“Export list…” saves the list so you can keep it or share it.",
        "aide_exp4":
            "“Import a list…” replaces the current list with a file: one "
            "name and one phrase per line, separated by a comma. The "
            "application asks for confirmation.",
        # ----- System sounds -----
        "aide_sys_titre": "📻  Create the radio's system sounds",
        "aide_sys1": "The “File” menu offers “Create the system sounds…”.",
        "aide_sys2":
            "The application downloads EdgeTX's official list, rebuilds the "
            "SYSTEM sounds with the voice chosen at the top of the window, "
            "and creates a SYSTEM/ folder inside the folder you choose.",
        "aide_sys3":
            "The time depends on how busy the voice service is and on your "
            "Internet connection.",
        "aide_sys4":
            "While it runs, “Let's Go” becomes “■ Stop”: the current file "
            "finishes, and the files already created stay.",
        "aide_sys5":
            "Then copy the SYSTEM/ folder into SOUNDS/<language>/ on your SD "
            "card, replacing the old one. Your personal sounds and the script "
            "sounds are not touched.",
        # ----- Name length -----
        "aide_edge_titre": "📏  Name length according to your EdgeTX",
        "aide_edge1":
            "The radio reads the file name: it must not be too long, "
            "otherwise it will not find it.",
        "aide_edge3": "EdgeTX 2.11 and newer: 8 characters, on every radio.",
        "aide_edge5":
            "EdgeTX 2.10 and older: 6 characters on colour radios and small "
            "black-and-white radios. The X9D and X9E accept 8 characters.",
        "aide_edge8":
            "If in doubt, stay at 6 characters: they will be read on every "
            "radio and every version.",
        # ----- Format -----
        "aide_fmt_titre": "🎵  File format",
        "aide_fmt1": "The generated WAV files use the EdgeTX format:",
        "aide_fmt2": "16-bit, 32 kHz, mono.",
        # ----- Footer -----
        "aide_soutien": "Do you find my application useful?",
        "aide_lien": "Buy me a coffee  ·  ko-fi.com/ritchy_lab",
        "aide_maj_titre": "🔄  Updates",
        "aide_maj":
            "New versions are published on the Releases page. The application "
            "checks automatically at startup: if a newer version exists, a "
            "small window offers to download it to your Downloads folder.",
        "maj_titre": "Update available",
        "maj_texte":
            "Version {version} is available.\n"
            "You are using version {actuelle}.",
        "maj_telecharger": "Download",
        "maj_plus_tard": "Later",
        "maj_telechargement": "Downloading…",
        "maj_telecharge_mac":
            "Downloaded to:\n{chemin}\n\n"
            "Open the folder, then replace the old application with the "
            "new one.",
        "maj_telecharge_win":
            "Downloaded to:\n{chemin}\n\n"
            "Close Vox-Pack, then run the new file.",
        "maj_ouvrir_dossier": "Open folder",
        "maj_page": "See the page",
        "maj_fermer": "Close",
        "maj_echec":
            "The download failed. You can open the Releases page.",
        "aide_github":
            "New versions  ·  github.com/ritchy-lab/Vox-Pack/releases",
        "aide_credits": "Created with AI brainstorming",
        "aide_merci": "Thanks to Ralf for the German translation.",
        "aide_ecran": "Version {version} — screen {ecran} — window {fenetre}",
    },
}


# ------------------------------------------------------------------
# Allemand
# ------------------------------------------------------------------
# Corrigé par Ralf (RWR) le 24 octobre 2026 sur les 88 textes qu'il a
# relus : vocabulaire « Ansage » pour ce que la radio prononce, et
# « Vox-Pack » plutôt que « die Anwendung ». Les 91 autres étaient déjà
# cohérents et n'ont pas été touchés (décision de Richard).
TEXTES["de"] = {
        # ----- Boutons de la fenêtre principale -----
        "ajouter": "Hinzufügen",
        "supprimer": "Löschen",
        "ecouter": "Anhören",
        "arreter": "■  Stopp",
        "tout": "Alle",
        "rien": "Keine",
        "lets_go": "Let's Go",
        # ----- Colonnes de la liste -----
        # ----- Voix : genre et accent -----
        "genre_f": "Weiblich",
        "genre_h": "Männlich",
        "genre_e": "Kind",
        "accent_france": "Frankreich",
        "accent_suisse": "Schweiz",
        "accent_belgique": "Belgien",
        "accent_quebec": "Québec",
        "accent_usa": "USA",
        "accent_uk": "Großbritannien",
        "accent_irlande": "Irland",
        "accent_allemagne": "Deutschland",
        # ----- Titres du panneau (écran de la maquette) -----
        "langue": "Sprache",
        "voix": "Stimme",
        "niveau": "Niveau",
        "allure": "Tempo",
        "robot": "Roboter",
        "nom": "Name",
        "phrase": "Spruch",
        "sons_systeme": "Systemtöne",
        # ----- Noms des langues -----
        "langue_fr": "Französisch",
        "langue_en": "Englisch",
        "langue_de": "Deutsch",
        # ----- Ligne d'état (sous la barre de leds) -----
        "etat_recherche_service": "Suche Stimmen beim TTS-Dienst…",
        "etat_recherche_voix": "Stimme wird geladen ({fait}/{total}) — {nom}…",
        "etat_generation_wav": "WAV-Datei wird erzeugt ({fait}/{total}) — {nom}…",
        "etat_avance": "{fait} von {total} Dateien — {nom}",
        "etat_voix_retirees": "{n} Stimme(n) vom Dienst entfernt — Liste aktualisiert",
        "etat_voix_remises": "Stimmen nicht verfügbar: Liste auf Standard zurückgesetzt",
        "etat_langue_voix": "Sprache: {langue} — {n} Stimmen verfügbar",
        "etat_sons_arret": "Stopp angefordert — aktuelle Datei wird beendet…",
        "etat_csv_telechargement": "Offizielle EdgeTX-Liste wird geladen…",
        # ----- Noms de fichiers refusés -----
        "pb_vide": "leerer Name",
        "pb_long": "{n} Zeichen (max. {max})",
        "pb_espace": "keine Leerzeichen erlaubt",
        "pb_accent": "keine Akzente erlaubt",
        "pb_caractere": "Zeichen „{c}“ nicht erlaubt",
        "pb_doublon": "bereits verwendet (Zeile {n})",
        # ----- Ligne ajoutée à la main -----
        "nouvelle_ligne": "neu",
        "texte_a_dire": "Zu sprechender Text",
        # ----- Pannes du service de voix -----
        "err_refus": "Dienst abgelehnt (Stimme nicht verfügbar oder Update nötig)",
        "err_voix_absente": "Stimme vom Dienst entfernt: bitte eine andere wählen",
        "err_lent": "Dienst hat nicht rechtzeitig geantwortet (langsame Verbindung?)",
        "err_illisible": "Der Sprachdienst hat eine unlesbare Antwort geliefert. Bitte gleich noch einmal versuchen.",
        "err_muet": "Der Sprachdienst hat einen leeren Ton geliefert: Der Satz wurde nicht gesprochen. Versuchen Sie es erneut oder ändern Sie den Satz.",
        "err_reseau": "keine Internetverbindung",
        "err_reseau_detail": "Der Sprachdienst von Microsoft ist nicht erreichbar. Prüfen Sie Ihre Internetverbindung (VPN, Firewall, DNS) und versuchen Sie es erneut.",
        "msg_reseau_coupe": "Internetverbindung verloren: Die Erzeugung wurde gestoppt. Prüfen Sie die Verbindung und versuchen Sie es erneut.",
        # ----- Menu -----
        "menu_fichier": "Datei",
        "menu_exporter": "Liste exportieren…",
        "menu_importer": "Liste importieren…",
        "menu_defaut": "Standardliste laden",
        "menu_sons_systeme": "System-Ansagen erzeugen…",
        "menu_quitter": "Beenden",
        "menu_langue": "Sprache",
        # ----- Exporter / Importer -----
        "titre_export": "Liste exportieren",
        "titre_import": "Liste importieren",
        "titre_dossier": "Ordner für die erzeugten WAV-Dateien",
        "titre_dossier_systeme": "Ordner, in dem der SYSTEM-Ordner erstellt wird",
        "nom_export": "meine-vox-pack-liste.csv",
        "type_csv": "CSV-Datei",
        "type_txt": "Textdatei",
        "type_tous": "Alle Dateien",
        "entete_nom": "Name",
        "entete_phrase": "Ansage",
        "msg_export_echec": "Der Export ist fehlgeschlagen.\n\n{err}",
        "msg_export_ok": "{n} Zeile(n) exportiert nach:\n\n{chemin}",
        "msg_import_illisible": "Diese Datei kann nicht gelesen werden.\n\n{err}",
        "msg_import_vide": "Diese Datei enthält keine Zeile.",
        "msg_import_confirmer": "Aktuelle Liste ({avant} Zeile(n)) durch diese {apres} Zeile(n) ersetzen?",
        "msg_import_oui": "Ja, ersetzen",
        "question_defaut": "Ihre Liste durch die {n} mitgelieferten Ansagen auf {langue} ersetzen?",
        "oui_remplacer": "Ja, ersetzen",
        "adjectif_fr": "Französisch",
        "adjectif_en": "Englisch",
        "adjectif_de": "Deutsch",
        "msg_import_ok": "{n} Zeile(n) importiert.",
        "msg_csv_aucun_systeme": "Die offizielle EdgeTX-Liste enthält keine System-Ansage.\n\nVersuchen Sie es später erneut: Die Datei wurde vielleicht geändert.",
        "msg_csv_officiel_echec": "Die offizielle EdgeTX-Liste konnte nicht geladen werden.\n\nPrüfen Sie die Internetverbindung und versuchen Sie es erneut.\n\n{err}",
        # ----- Boutons et messages courants -----
        "annuler": "Abbrechen",
        "compris": "Verstanden",
        "fermer": "Schließen",
        "choisir": "Auswählen",
        "voix_normale": "Normale Stimme",
        "ouvrir_dossier": "Ordner öffnen",
        "btn_supprimer": "Löschen",
        # ----- Suppression, aperçu, génération -----
        "msg_supprimer_rien": "Markieren Sie mindestens eine Zeile zum Löschen.",
        "msg_supprimer_tout": "Sie sind dabei, die GANZE Liste zu löschen.\n\nSie wird beim nächsten Start der Anwendung automatisch neu erstellt.\n\nMöchten Sie fortfahren?",
        "msg_ecouter_rien": "Markieren Sie eine Zeile zum Anhören.",
        "etat_ecoute": "Wiedergabe {rang}/{total} — {nom}",
        "msg_apercu_echec": "Die Vorschau konnte nicht abgespielt werden.\n\n{err}",
        "msg_audio_absent":
            "Keine Audioausgabe auf diesem Rechner: die Vorschau kann nicht "
            "abgespielt werden. Die Dateien werden trotzdem erstellt.",
        "msg_generer_rien": "Markieren Sie mindestens eine Zeile zum Erzeugen.",
        "msg_generer_aucune": "Keine gültige Zeile zum Erzeugen.\n\nJede Zeile braucht einen korrekten Dateinamen UND einen Ansage-Text.",
        "msg_genere_deja": "Es läuft bereits eine Erzeugung.\n\nWarten Sie, bis sie beendet ist.",
        "msg_sauvegarde_echec": "Die Liste konnte nicht gespeichert werden.\n\n{err}\n\nEin anderes Programm verwendet die Datei vielleicht (Antivirus, OneDrive), oder Windows schützt den Ordner „Dokumente“: Erlauben Sie Vox-Pack unter Windows-Sicherheit → „Überwachter Ordnerzugriff“.",
        "msg_bilan_echecs": "{reussis} von {total} Datei(en) erstellt.\n\n{problemes} Problem(e):\n{detail}",
        "msg_autres": "• … und {n} weitere",
        "msg_succes": "Ihre Stimmen sind fertig.\n\n{dossier}",
        "msg_sons_succes": "{n} Systemdatei(en) erstellt in:\n\n{dossier}",
        "msg_sons_copier": "Kopieren Sie diesen SYSTEM-Ordner nach SOUNDS/{langue}/ auf Ihrer Karte und ersetzen Sie den alten.",
        "msg_sons_bilan": "{reussis} von {total} Systemdatei(en) erstellt.\n\n{problemes} Problem(e):\n{detail}",
        "msg_sons_problemes": "{problemes} Problem(e):\n{detail}",
        "msg_sons_arrete": "Erzeugung gestoppt.\n\n{n} Datei(en) erstellt in:\n\n{dossier}",
        "msg_sons_cache": "Offizielle Liste nicht geladen: Die gespeicherte Kopie wurde verwendet.",
        "msg_dossier_echec": "Der Zielordner konnte nicht erstellt werden.\n\n{err}",
        # ----- Fenêtre de soutien -----
        "titre_soutien": "Unterstützen Sie das Projekt",
        "soutien_question": "Finden Sie meine Anwendung nützlich?",
        "soutien_cafe": "Kaufen Sie mir einen Kaffee",
        "soutien_oui": "Ja, sehr gerne!",
        "soutien_plus_tard": "Vielleicht nächstes Mal",
        "soutien_ne_plus": "Nicht mehr fragen",
        # ----- Fenêtre d'aide -----
        "titre_aide": "Hilfe — Vox-Pack",
        "aide_titre": "So bedienen Sie Vox-Pack",
        # ----- 1. Voix -----
        "aide_1": "1. Stimme wählen",
        "aide_1a": "Die Anwendung gibt es in fünfzehn Sprachen; beim ersten Start öffnet sie sich in der Systemsprache. Das Menü bietet die Stimmen der gewählten Sprache, und die aktuelle Stimme ist markiert. Die Sprache lässt sich im Menü ändern.",
        "aide_officielle": "Der ★ kennzeichnet die offizielle EdgeTX-Stimme dieser Sprache: gleiche Stimme und gleiches Tempo wie auf der Fernsteuerung.",
        "aide_robot_titre": "🤖  Roboterstimmen",
        "aide_robot1": "Rechts im Fenster vier Punkte: Roboter 1 bis 3 und HAL 9000. HAL 9000 nutzt seine eigene Stimme, unabhängig vom Menü. Kein Punkt markiert: die normale Stimme.",
        "aide_robot2": "Klicken Sie auf einen Punkt und dann auf „Anhören“: Der Effekt gilt für die gewählte Stimme. Klicken Sie erneut auf den leuchtenden Punkt, um zur normalen Stimme zurückzukehren.",
        "aide_robot3": "Der Effekt gilt auch für die Listendateien und die System-Ansagen.",
        "aide_1b": "Zum Sprachwechsel: Menü „Datei“, dann „Sprache“. Texte, Stimmen und Liste ändern sich gemeinsam, und Ihre Stimme wird beim nächsten Start wiederverwendet.",
        # ----- 2. Liste -----
        "aide_2": "2. Liste verwalten",
        "aide_2a": "„Hinzufügen“ erstellt eine Zeile; „Löschen“ entfernt die markierten Zeilen.",
        "aide_2b": "Bearbeiten Sie eine Zeile, indem Sie direkt in ihre Felder tippen.",
        "aide_2c": "Mehrere Zeilen auf einmal markieren: Klicken Sie auf das erste Kästchen, dann mit Umschalt + Klick auf das letzte.",
        "aide_2d": "Für eine Pause tippen Sie ein „>“ oder mehr in den Satz: jedes „>“ zählt eine halbe Sekunde. „Motor an >> Motor aus“ lässt eine Sekunde zwischen beiden, und „>>> Motor an“ verzögert die Ansage um eineinhalb Sekunden. Höchstens zehn Sekunden.",
        "aide_nom1": "Der Dateiname darf höchstens 8 Zeichen lang sein und keine Akzente oder Leerzeichen enthalten.",
        # ----- 3. Cocher -----
        "aide_3": "3. Zeilen zum Erzeugen markieren",
        "aide_3a": "Das Kästchen in der Kopfzeile markiert alle Zeilen; wird der Haken entfernt, sind alle wieder frei.",
        "aide_3b": "Für eine einzelne Zeile nur diese markieren.",
        # ----- 4. Écouter -----
        "aide_4": "4. Auswahl anhören",
        "aide_4a": "Markieren Sie eine oder mehrere Zeilen und klicken Sie auf „Anhören“: Sie werden nacheinander abgespielt.",
        # ----- 5. Générer -----
        "aide_5": "5. Dateien erzeugen",
        "aide_5a": "Klicken Sie auf „Let's Go“ und wählen Sie einen Ordner.",
        "aide_5b": "Unter der LED-Leiste zeigt eine Zeile jederzeit, was Vox-Pack gerade tut: Stimme laden, dann WAV-Datei erzeugen.",
        # ----- Pegel und Tempo -----
        "aide_6_titre": "6. Pegel und Tempo einstellen",
        "aide_6a":
            "Der PEGEL-Regler geht von −6 bis +6 dB: Er macht die Datei "
            "lauter oder leiser, ohne je zu übersteuern. Bei 0 dB wird nichts "
            "geändert.",
        "aide_6b":
            "Der TEMPO-Regler bestimmt die Sprechgeschwindigkeit. Die "
            "mittlere Rastung hält 0 %, ein Doppelklick auf die Spur kehrt "
            "dorthin zurück. Beide Einstellungen gelten für die Vorschau, die "
            "Dateien und die System-Ansagen.",
        # ----- Internet -----
        "aide_net_titre": "🌐  Internetverbindung erforderlich",
        "aide_net1": "Die Stimmen sind nicht in Vox-Pack enthalten: Sie kommen vom Sprachdienst von Microsoft. Eine Internetverbindung ist daher zum Erzeugen der Dateien unerlässlich.",
        "aide_net4": "Der Text Ihrer Sätze wird an Microsoft gesendet, um gesprochen zu werden: Halten Sie ihn frei von Privatem.",
        "aide_net6": "Ohne Internet sagt Ihnen die Anwendung das deutlich.",
        "aide_net7": "Existiert eine Stimme bei Microsoft nicht mehr, verschwindet sie beim Start von Vox-Pack von selbst aus dem Menü.",
        # ----- Sauvegarde -----
        "aide_sauv_titre": "💾  Automatisches Speichern",
        "aide_sauv1": "Ihre Änderungen werden gespeichert in:",
        # ----- Liste par défaut -----
        "aide_def_titre": "♻️  Standardliste",
        "aide_def1": "Wenn Sie die GANZE Liste löschen, wird sie beim nächsten Start automatisch neu erstellt.",
        "aide_def5": "Jede Sprache hat IHRE EIGENE Liste. Ein Sprachwechsel im Menü wechselt daher auch die Liste, und Ihre Arbeit in der anderen Sprache bleibt unverändert.",
        "aide_def3": "Wenn Sie mindestens 1 Zeile behalten, bauen Sie Ihre eigene Liste mit deren Einstellungen auf.",
        # ----- Export / import -----
        "aide_exp_titre": "📂  Liste exportieren / importieren",
        "aide_exp1": "Das Menü „Datei“ liegt auf dem Mac in der Systemmenüleiste, auf dem PC oben im Fenster.",
        "aide_exp3": "„Liste exportieren…“ speichert die Liste, damit Sie sie aufbewahren oder weitergeben können.",
        "aide_exp4": "„Liste importieren…“ ersetzt die aktuelle Liste durch eine Datei: ein Name und eine Ansage pro Zeile, durch ein Komma getrennt. Vox-Pack fragt vorher nach.",
        # ----- Sons système -----
        "aide_sys_titre": "📻  System-Ansagen der Fernsteuerung erzeugen",
        "aide_sys1": "Das Menü „Datei“ bietet „System-Ansagen erzeugen…“.",
        "aide_sys2": "Vox-Pack lädt die offizielle Liste von EdgeTX, erzeugt die SYSTEM-Ansagen mit der oben gewählten Stimme neu und legt im gewählten Ordner einen SYSTEM-Ordner an.",
        "aide_sys3": "Die Zeit hängt von der Auslastung des Sprachdienstes und Ihrer Internetverbindung ab.",
        "aide_sys4": "Während des Laufs wird aus „Let's Go“ ein „■ Stopp“: Die aktuelle Datei wird beendet, die bereits erzeugten Dateien bleiben erhalten.",
        "aide_sys5": "Kopieren Sie anschließend den SYSTEM-Ordner nach SOUNDS/<Sprache>/ auf Ihrer SD-Karte. Dabei ersetzen Sie den alten. Ihre eigenen Ansagen und die Skript-Ansagen bleiben unberührt.",
        # ----- Longueur des noms -----
        "aide_edge_titre": "📏  Namenslänge je nach EdgeTX-Version",
        "aide_edge1": "Die Fernsteuerung liest den Dateinamen: Er darf nicht zu lang sein, sonst findet sie die Datei nicht.",
        "aide_edge3": "EdgeTX 2.11 und neuer: 8 Zeichen, auf jeder Fernsteuerung.",
        "aide_edge5": "EdgeTX 2.10 und älter: 6 Zeichen bei Farb-Fernsteuerungen und kleinen Schwarz-Weiß-Geräten. X9D und X9E akzeptieren 8 Zeichen.",
        "aide_edge8": "Im Zweifel bei 6 Zeichen bleiben: Sie werden auf jeder Fernsteuerung und in jeder Version gelesen.",
        # ----- Format -----
        "aide_fmt_titre": "🎵  Dateiformat",
        "aide_fmt1": "Die erzeugten WAV-Dateien haben das EdgeTX-Format:",
        "aide_fmt2": "16 Bit, 32 kHz, mono.",
        # ----- Bas de page -----
        "aide_soutien": "Finden Sie meine Anwendung nützlich?",
        "aide_lien": "Kaufen Sie mir einen Kaffee  ·  ko-fi.com/ritchy_lab",
        "aide_maj_titre": "🔄  Updates",
        "aide_maj": "Neue Versionen erscheinen auf der Releases-Seite. Vox-Pack prüft beim Start automatisch: Gibt es eine neuere Version, bietet ein kleines Fenster den Download in Ihren Downloads-Ordner an.",
        "maj_titre": "Update verfügbar",
        "maj_texte": "Version {version} ist verfügbar.\nSie verwenden Version {actuelle}.",
        "maj_telecharger": "Herunterladen",
        "maj_plus_tard": "Später",
        "maj_telechargement": "Wird heruntergeladen…",
        "maj_telecharge_mac": "Heruntergeladen nach:\n{chemin}\n\nÖffnen Sie den Ordner und ersetzen Sie die alte Anwendung durch die neue.",
        "maj_telecharge_win": "Heruntergeladen nach:\n{chemin}\n\nSchließen Sie Vox-Pack und starten Sie dann die neue Datei.",
        "maj_ouvrir_dossier": "Ordner öffnen",
        "maj_page": "Seite ansehen",
        "maj_fermer": "Schließen",
        "maj_echec": "Der Download ist fehlgeschlagen. Sie können die Releases-Seite öffnen.",
        "aide_github": "Neue Versionen  ·  github.com/ritchy-lab/Vox-Pack/releases",
        "aide_credits": "Mit KI-Unterstützung erstellt",
        "aide_merci": "Danke an Ralf für die deutsche Übersetzung.",
        "aide_ecran": "Version {version} — Bildschirm {ecran} — Fenster {fenetre}",
}


def t(cle, **remplacements):
    """Texte de l'interface dans la langue courante.

    Si une clé manque, on retombe sur l'anglais puis sur le français : les
    quinze langues n'ont pas encore toutes les clés de la 1.5.1, et un mot
    anglais vaut mieux que « etat_recherche_service » à l'écran. En dernier
    recours, la clé elle-même.
    """
    texte = TEXTES.get(LANGUE_UI, {}).get(cle)
    if texte is None:
        texte = TEXTES.get("en", {}).get(cle)
    if texte is None:
        texte = TEXTES.get("fr", {}).get(cle, cle)
    return texte.format(**remplacements) if remplacements else texte


def definir_langue_ui(code):
    """Change la langue des textes (l'affichage est remis à jour ensuite par
    VoxPackApp._appliquer_langue)."""
    global LANGUE_UI
    if code in TEXTES:
        LANGUE_UI = code


def cles_manquantes():
    """Clés présentes dans une langue et pas dans une autre.

    Sert de filet : une clé oubliée s'afficherait telle quelle à l'écran.
    La comparaison se fait avec le français, langue de référence, mais
    couvre les trois tables.
    """
    reference = set(TEXTES["fr"])
    ecarts = set()
    for table in TEXTES.values():
        ecarts |= reference ^ set(table)
    return sorted(ecarts)


def entetes_nom_connues():
    """Tous les libellés d'en-tête « nom » que Vox-Pack peut exporter.

    L'export écrit un en-tête traduit (« nom », « name », « nombre »,
    « název », « 名前 »…). L'import doit donc le reconnaître dans les quinze
    langues, sinon il le transforme en première ligne de la liste.
    """
    noms = {"nom", "name", "fichier", "file", "nom_fichier"}
    for table in TEXTES.values():
        valeur = str(table.get("entete_nom", "") or "").strip().lower()
        if valeur:
            noms.add(valeur)
    return noms


def est_entete(ligne):
    """Vrai si cette ligne CSV est l'en-tête d'un fichier exporté."""
    if not ligne:
        return False
    return str(ligne[0]).strip().lower() in entetes_nom_connues()


# ------------------------------------------------------------------
# Voix proposées
# ------------------------------------------------------------------
# (identifiant technique, prénom, genre, accent)
#
#   genre  : "f" femme, "h" homme, "e" enfant
#   accent : clé de traduction, qui commence par « accent_ » dans TEXTES
#
# Ces données sont volontairement séparées du libellé affiché : celui-ci
# contient « Femme » / « Homme », qui change avec la langue de l'interface.
# Une voix mémorisée doit rester reconnaissable même si l'interface change :
# c'est donc l'identifiant technique qu'on enregistre dans les réglages.
VOIX = {
    "fr": [
        # France
        ("fr-FR-DeniseNeural", "Denise", "f", "france"),
        ("fr-FR-HenriNeural", "Henri", "h", "france"),
        ("fr-FR-EloiseNeural", "Eloise", "e", "france"),
        # Suisse
        ("fr-CH-ArianeNeural", "Ariane", "f", "suisse"),
        ("fr-CH-FabriceNeural", "Fabrice", "h", "suisse"),
        # Belgique
        ("fr-BE-CharlineNeural", "Charline", "f", "belgique"),
        ("fr-BE-GerardNeural", "Gerard", "h", "belgique"),
        # Québec
        ("fr-CA-SylvieNeural", "Sylvie", "f", "quebec"),
        ("fr-CA-AntoineNeural", "Antoine", "h", "quebec"),
        ("fr-CA-JeanNeural", "Jean", "h", "quebec"),
        ("fr-CA-ThierryNeural", "Thierry", "h", "quebec"),
    ],
    "en": [
        # États-Unis
        ("en-US-AriaNeural", "Aria", "f", "usa"),
        ("en-US-GuyNeural", "Guy", "h", "usa"),
        ("en-US-JennyNeural", "Jenny", "f", "usa"),
        ("en-US-ChristopherNeural", "Christopher", "h", "usa"),
        ("en-US-MichelleNeural", "Michelle", "f", "usa"),
        ("en-US-EricNeural", "Eric", "h", "usa"),
        ("en-US-AvaNeural", "Ava", "f", "usa"),
        ("en-US-AndrewNeural", "Andrew", "h", "usa"),
        ("en-US-EmmaMultilingualNeural", "Emma", "f", "usa"),
        ("en-US-BrianNeural", "Brian", "h", "usa"),
        ("en-US-RogerNeural", "Roger", "h", "usa"),
        ("en-US-SteffanNeural", "Steffan", "h", "usa"),
        ("en-US-AnaNeural", "Ana", "e", "usa"),
        # Irlande — la voix officielle d'EdgeTX pour l'anglais
        ("en-IE-EmilyNeural", "Emily", "f", "irlande"),
        # Royaume-Uni
        ("en-GB-SoniaNeural", "Sonia", "f", "uk"),
        ("en-GB-RyanNeural", "Ryan", "h", "uk"),
        ("en-GB-LibbyNeural", "Libby", "f", "uk"),
        ("en-GB-MaisieNeural", "Maisie", "e", "uk"),
        ("en-GB-ThomasNeural", "Thomas", "h", "uk"),
    ],
    "de": [
        # Allemagne — Katja est la voix officielle d'EdgeTX pour l'allemand
        ("de-DE-KatjaNeural", "Katja", "f", "allemagne"),
        ("de-DE-ConradNeural", "Conrad", "h", "allemagne"),
        ("de-DE-AmalaNeural", "Amala", "f", "allemagne"),
        ("de-DE-KillianNeural", "Killian", "h", "allemagne"),
    ],
}

# Copie de secours : si le service retire toutes les voix d'une langue, on
# remet cette liste plutôt que de laisser un menu vide.
VOIX_ORIGINE = {code: list(voix) for code, voix in VOIX.items()}

# La voix choisie par l'équipe EdgeTX pour chaque langue : elle est marquée
# d'une étoile dans le sélecteur, pour que l'on sache laquelle reproduit les
# sons du constructeur.
VOIX_OFFICIELLES = {"fr-FR-DeniseNeural", "en-IE-EmilyNeural",
                    "de-DE-KatjaNeural"}

# Réglages officiels de vitesse : EdgeTX ne fait pas parler toutes ses voix à
# la même allure. Emily, la voix anglaise officielle, parle 10 % plus vite.
# Katja (allemand) garde l'allure normale, comme dans la recette d'EdgeTX.
REGLES_VOIX = {"en-IE-EmilyNeural": {"rate": "+10%"}}


# ------------------------------------------------------------------
# Les quinze langues
# ------------------------------------------------------------------
# Les langues et les textes sont des données de l'application : ils vivent
# dans le paquet `voxpack_data`, importé comme n'importe quel module. Plus de
# dossier « maquette » à joindre à la compilation, plus de chemin ajouté à
# `sys.path`, et plus de repli silencieux à trois langues : si le paquet
# manque, l'application refuse de démarrer au lieu de mentir à moitié.
from voxpack_data import langues as _langues
from voxpack_data import textes as _textes
from voxpack_data.aide import AVERTISSEMENT_AIDE

_LANGUES_TABLE = _langues.LANGUES
_TEXTES_TABLE = _textes.TEXTES

# Les voix supplémentaires par langue (hors officielle et hors multilingue).
_VOIX_EN_PLUS = {
    "cs": [("cs-CZ-AntoninNeural", "Antonin", "h")],
    "da": [("da-DK-JeppeNeural", "Jeppe", "h")],
    "es": [("es-ES-XimenaNeural", "Ximena", "f"),
           ("es-ES-AlvaroNeural", "Alvaro", "h")],
    "it": [("it-IT-IsabellaNeural", "Isabella", "f"),
           ("it-IT-DiegoNeural", "Diego", "h")],
    "ja": [("ja-JP-KeitaNeural", "Keita", "h")],
    "pt": [("pt-BR-AntonioNeural", "Antonio", "h", "pt-br"),
           ("pt-PT-RaquelNeural", "Raquel", "f", "pt-pt"),
           ("pt-PT-DuarteNeural", "Duarte", "h", "pt-pt")],
    "ru": [("ru-RU-DmitryNeural", "Dmitry", "h")],
    "sv": [("sv-SE-MattiasNeural", "Mattias", "h")],
    "uk": [("uk-UA-PolinaNeural", "Polina", "f")],
    "cn": [("zh-CN-XiaoyiNeural", "Xiaoyi", "f"),
           ("zh-CN-YunjianNeural", "Yunjian", "h"),
           ("zh-CN-YunxiNeural", "Yunxi", "h"),
           ("zh-CN-YunxiaNeural", "Yunxia", "h"),
           ("zh-CN-YunyangNeural", "Yunyang", "h")],
    "tw": [("zh-TW-HsiaoYuNeural", "HsiaoYu", "f"),
           ("zh-TW-YunJheNeural", "YunJhe", "h")],
    "hk": [("zh-HK-HiuMaanNeural", "HiuMaan", "f"),
           ("zh-HK-WanLungNeural", "WanLung", "h")],
}

if _LANGUES_TABLE:
    LANGUES = [langue.code for langue in _LANGUES_TABLE]
    # Les textes de la maquette ne remplacent pas ceux de la 1.5.1 : ils
    # comblent les trous. Deux clés ont changé de nom en passant à l'écran.
    _RENOMMEES = {"vitesse": "allure", "sons_system": "sons_systeme"}
    for code, table in _TEXTES_TABLE.items():
        cible = TEXTES.setdefault(code, {})
        for cle, texte in table.items():
            cible.setdefault(_RENOMMEES.get(cle, cle), texte)
    for langue in _LANGUES_TABLE:
        # Le nom natif et l'adjectif, dans toutes les langues d'interface ;
        # l'étiquette de la voix officielle (« Nanami (日本語) »).
        for table in TEXTES.values():
            table.setdefault("langue_" + langue.code, langue.nom)
            table.setdefault("adjectif_" + langue.code, langue.nom)
            table.setdefault("accent_" + langue.dossier, langue.nom)
        # La voix officielle d'EdgeTX d'abord, puis les autres voix du
        # service pour la même langue (jamais les « Multilingue » : elles
        # devinent la langue de chaque mot et se trompent sur certains).
        if langue.code not in VOIX:
            genre = "h" if langue.code == "uk" else "f"
            accent = "pt-br" if langue.code == "pt" else langue.dossier
            VOIX[langue.code] = [(langue.voix, langue.voix_nom, genre,
                                  accent)]
            for entree in _VOIX_EN_PLUS.get(langue.code, ()):
                identifiant, prenom, genre_voix = entree[:3]
                accent_voix = entree[3] if len(entree) > 3 else langue.dossier
                VOIX[langue.code].append(
                    (identifiant, prenom, genre_voix, accent_voix))
        if langue.vitesse != 1.0:
            REGLES_VOIX.setdefault(langue.voix, {})["rate"] = (
                f"{langue.pour_cent:+d}%")
        # L'allure ne suffit pas : la recette d'EdgeTX donne aussi une
        # hauteur pour certaines voix (le suédois est à -10 Hz). Sans elle,
        # la voix « officielle » ne sonne pas comme sur la radio.
        if langue.hauteur:
            REGLES_VOIX.setdefault(langue.voix, {})["pitch"] = langue.hauteur
        VOIX_OFFICIELLES.add(langue.voix)
    # Le portugais a deux accents dans le service : on le dit, plutôt que
    # d'afficher quatre fois « Português ». Le pays seul, dans chaque langue.
    _ACCENTS_PT = {
        "fr": ("Brésil", "Portugal"), "en": ("Brazil", "Portugal"),
        "de": ("Brasilien", "Portugal"), "es": ("Brasil", "Portugal"),
        "it": ("Brasile", "Portogallo"), "pt": ("Brasil", "Portugal"),
        "ru": ("Бразилия", "Португалия"), "sv": ("Brasilien", "Portugal"),
        "uk": ("Бразилія", "Португалія"), "cs": ("Brazílie", "Portugalsko"),
        "da": ("Brasilien", "Portugal"), "ja": ("ブラジル", "ポルトガル"),
        "cn": ("巴西", "葡萄牙"), "tw": ("巴西", "葡萄牙"),
        "hk": ("巴西", "葡萄牙"),
    }
    for _code, (_bresil, _portugal) in _ACCENTS_PT.items():
        if _code in TEXTES:
            TEXTES[_code]["accent_pt-br"] = _bresil
            TEXTES[_code]["accent_pt-pt"] = _portugal
    VOIX_ORIGINE = {code: list(voix) for code, voix in VOIX.items()}
else:                                  # paquet absent : mieux vaut échouer
    raise RuntimeError(                # que d'afficher trois langues en croyant
        "voxpack_data est absent : l'installation est incomplète.")  # en avoir 15


def reglage_voix(voice_id):
    """Réglages edge-tts (vitesse…) pour coller à la voix officielle."""
    return REGLES_VOIX.get(voice_id, {})


# Marque la voix actuellement choisie dans la liste déroulante : sans
# elle, on ne sait plus d'où l'on part quand on veut changer de voix.
MARQUE_VOIX = "✓  "


async def sauver_voix(texte, voice_id, chemin, pitch=None, rate=None):
    """Fabrique le MP3, avec un second essai si le service répond mal.

    Le service de Microsoft renvoie parfois une réponse tronquée ou
    illisible ; un nouvel essai suffit presque toujours.
    """
    derniere = None
    for tentative in range(2):
        try:
            regle = reglage_voix(voice_id)
            communicate = edge_tts.Communicate(
                texte, voice_id, volume=VOLUME,
                rate=rate or regle.get("rate", "+0%"),
                # Un pitch demandé (robot) passe avant la hauteur officielle
                # de la voix ; sinon on applique celle de la recette EdgeTX.
                pitch=pitch or regle.get("pitch") or "+0Hz")
            await communicate.save(chemin)
            return
        except Exception as e:
            derniere = e
            if tentative == 0:
                await asyncio.sleep(0.8)
    raise derniere


# ------------------------------------------------------------------
# Silences dans une phrase
# ------------------------------------------------------------------
# Un « > » ou plus, dans la phrase, marque une pause : chaque « > » vaut
# une demi-seconde, donc « >> » vaut une seconde et « >>> » une seconde et
# demie. On n'a pas choisi « + » : il apparaît légitimement dans une phrase
# (« Klappen +10 Grad », « Kanal + 2 ») et le signe disparaîtrait sans
# prévenir, alors que « > » ne s'écrit jamais dans une annonce.
#
# Ces silences sont posés APRÈS ameliorer_niveau_wav. Ce traitement coupe
# les silences du début et de la fin de chaque fichier (c'est ce qui a
# raccourci les annonces en 1.4.4) : posé avant, le silence d'attente
# disparaîtrait. Mesuré le 25 octobre 2026 — deux secondes ajoutées avant
# le traitement, il ne restait que la voix.
DUREE_SIGNE = 0.5         # secondes par « > »
SILENCE_MAX = 10.0        # plafond d'une pause, en secondes
MOTIF_SILENCE = re.compile(r">+")


def decouper_phrase(texte):
    """Découpe une phrase en morceaux : (« texte », …) ou (« silence », s).

    « Motor an >>> Motor aus » donne le texte, une seconde et demie de
    silence, puis le texte. Les morceaux de texte vides sont ignorés.
    """
    texte = texte or ""
    morceaux, position = [], 0
    for trouve in MOTIF_SILENCE.finditer(texte):
        avant = texte[position:trouve.start()].strip()
        if avant:
            morceaux.append(("texte", avant))
        morceaux.append(
            ("silence", min(len(trouve.group()) * DUREE_SIGNE, SILENCE_MAX)))
        position = trouve.end()
    reste = texte[position:].strip()
    if reste:
        morceaux.append(("texte", reste))
    return morceaux


def phrase_sans_silences(texte):
    """La phrase débarrassée de ses marqueurs : vide s'il n'y a rien à dire."""
    return " ".join(valeur for genre, valeur in decouper_phrase(texte)
                    if genre == "texte")


def _effacer(*chemins):
    """Supprime des fichiers temporaires sans jamais faire échouer l'appel."""
    for chemin in chemins:
        try:
            os.remove(chemin)
        except OSError:
            pass


def _lire_pcm(chemin):
    """Contenu brut d'un WAV EdgeTX, format vérifié."""
    with wave.open(chemin, "rb") as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (
                FORMAT_EDGETX[0], 1, 2):
            raise ValueError("format inattendu dans le WAV")
        return w.readframes(w.getnframes())


def _pcm_sans_bords(brut, sr=FORMAT_EDGETX[0]):
    """Retire les silences du début et de la fin d'un PCM 16 bits mono.

    Mêmes seuil et marges que ameliorer_niveau_wav. C'est indispensable
    avant de coller deux morceaux : le service ajoute près d'une seconde de
    silence après chaque phrase, et cette seconde s'ajouterait à la pause
    demandée (mesuré le 25 octobre : 2,5 s au lieu de 1,5 s).
    """
    import numpy as np

    x = np.frombuffer(brut, dtype="<i2")
    actifs = np.where(np.abs(x.astype(np.int32)) > 98)[0]   # ≈ −50 dBFS
    if not len(actifs):
        return brut
    debut = max(0, actifs[0] - int(0.020 * sr))
    fin = min(len(x), actifs[-1] + int(0.050 * sr))
    return x[debut:fin].tobytes()


def _ecrire_pcm(chemin, brut, sr=FORMAT_EDGETX[0]):
    """Écrit un WAV EdgeTX par un temporaire, puis le met en place."""
    temporaire = chemin + ".tmp"
    try:
        with wave.open(temporaire, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(brut)
        os.replace(temporaire, chemin)
    finally:
        _effacer(temporaire)


def wav_a_du_son(chemin):
    """Vrai si le WAV contient au moins un échantillon non nul.

    Un service de voix peut répondre « 200 » et livrer un fichier muet :
    voix retirée du catalogue, phrase faite de caractères qu'il ignore. Le
    fichier a alors la bonne taille et le bon format — il est simplement
    silencieux. Sans ce contrôle, il était compté comme un succès, et la
    radio jouait le silence.
    """
    try:
        with wave.open(chemin, "rb") as w:
            if w.getnframes() <= 0:
                return False
            brut = w.readframes(w.getnframes())
    except (wave.Error, OSError):
        return False
    return any(brut)


async def fabriquer_wav(texte, voice_id, destination, pitch=None, rate=None,
                        robot=0, langue_effet="en", niveau=0, annoncer=None):
    """Fabrique le WAV d'une phrase, silences compris.

    Sans marqueur — le cas de presque toutes les phrases — le chemin est
    celui d'avant, au détail près : un MP3, une conversion, l'effet, le
    niveau. Avec des marqueurs, chaque morceau de texte est demandé
    séparément, les morceaux sont collés, puis le niveau est appliqué et les
    silences des bords sont posés en dernier : c'est le seul ordre où une
    attente devant l'annonce survit au traitement.
    """
    morceaux = decouper_phrase(texte)
    if not any(genre == "texte" for genre, _ in morceaux):
        raise ValueError("phrase sans texte")

    if len(morceaux) == 1 and morceaux[0][0] == "texte":
        mp3 = destination + ".voix.mp3"
        # Tout le traitement se fait dans un temporaire du même dossier, et
        # le fichier final n'apparaît qu'à la fin. Une conversion interrompue
        # (disque plein, service qui coupe) ne peut donc pas laisser un WAV
        # tronqué que la radio tenterait de lire.
        temporaire = destination + ".final.tmp"
        try:
            await sauver_voix(morceaux[0][1], voice_id, mp3,
                              pitch=pitch, rate=rate)
            if annoncer:
                annoncer()
            convertir_en_wav(mp3, temporaire)
            if robot:
                appliquer_effet_robot(temporaire, robot, langue_effet)
            ameliorer_niveau_wav(temporaire)
            appliquer_niveau(temporaire, niveau)
            if not wav_a_du_son(temporaire):
                raise ValueError(t("err_muet"))
            os.replace(temporaire, destination)
        finally:
            _effacer(mp3, temporaire)
        return

    sr = FORMAT_EDGETX[0]
    parties = {}
    for rang, (genre, valeur) in enumerate(morceaux):
        if genre != "texte":
            continue
        mp3 = f"{destination}.partie{rang}.mp3"
        wav = f"{destination}.partie{rang}.wav"
        try:
            await sauver_voix(valeur, voice_id, mp3, pitch=pitch, rate=rate)
            if annoncer:
                annoncer()
                annoncer = None            # une fois suffit
            convertir_en_wav(mp3, wav)
            parties[rang] = _pcm_sans_bords(_lire_pcm(wav))
        finally:
            _effacer(mp3, wav)

    premier = next(i for i, (g, _) in enumerate(morceaux) if g == "texte")
    dernier = max(i for i, (g, _) in enumerate(morceaux) if g == "texte")
    avant = sum(v for g, v in morceaux[:premier] if g == "silence")
    apres = sum(v for g, v in morceaux[dernier + 1:] if g == "silence")
    # La queue de 250 ms que le traitement du niveau pose après le dernier son
    # compte dans la pause demandée : « Motor armed >>> » laisse bien 1,5 s de
    # silence, et non 1,75 s.
    apres = max(0.0, apres - QUEUE_FIN)

    joint = bytearray()
    for rang in range(premier, dernier + 1):
        genre, valeur = morceaux[rang]
        if genre == "texte":
            joint += parties[rang]
        else:
            joint += b"\x00\x00" * int(valeur * sr)

    # Même règle que pour une phrase simple : on assemble et on traite dans
    # un temporaire, puis on remplace le fichier final d'un seul coup.
    temporaire = destination + ".final.tmp"
    try:
        _ecrire_pcm(temporaire, bytes(joint), sr)

        if robot:
            appliquer_effet_robot(temporaire, robot, langue_effet)
        ameliorer_niveau_wav(temporaire)
        appliquer_niveau(temporaire, niveau)

        if avant or apres:
            brut = _lire_pcm(temporaire)
            _ecrire_pcm(temporaire,
                        b"\x00\x00" * int(avant * sr) + brut
                        + b"\x00\x00" * int(apres * sr), sr)
        if not wav_a_du_son(temporaire):
            raise ValueError(t("err_muet"))
        os.replace(temporaire, destination)
    finally:
        _effacer(temporaire)


def libelle_voix(entree, langue_ui=None, avec_genre=False):
    """Libellé affiché d'une voix : « Denise (France) ».

    Le prénom dit déjà le genre (« Denise », « Henri ») : on ne répète plus
    « Femme » ou « Homme », qui allongeait le libellé pour rien. Le paramètre
    `avec_genre` garde l'ancien format, pour retrouver une voix mémorisée par
    une version précédente.

    On peut demander le libellé dans une autre langue que la langue courante :
    c'est ainsi qu'on calcule la largeur du menu une fois pour toutes.
    """
    _identifiant, prenom, genre, accent = entree
    table = TEXTES.get(langue_ui or LANGUE_UI, TEXTES["fr"])
    # Ces voix devinent la langue de chaque mot : sur une phrase française,
    # un mot anglais peut sortir avec l'accent anglais. Autant le dire, et
    # remplacer l'accent annoncé (« France ») par la vraie nature de la voix :
    # prétendre qu'elle est « de France » serait faux.
    if "Multilingual" in _identifiant:
        origine = table.get("voix_multilingue", "Multilingue")
    else:
        origine = table.get('accent_' + accent, accent)
    # Les noms chinois sont déjà entre parenthèses (« 中文（简体） ») :
    # « Xiaoxiao (中文（简体）) » faisait des parenthèses imbriquées.
    if "（" in origine or "）" in origine:
        origine = origine.replace("（", " · ").replace("）", "").strip()
    if avec_genre:
        libelle = (f"{prenom} ({table.get('genre_' + genre, genre)} - "
                   f"{origine})")
    else:
        libelle = f"{prenom} ({origine})"
    if _identifiant in VOIX_OFFICIELLES:
        libelle += "  ★"
    return libelle


def voix_de_la_langue(code):
    """Liste [(libellé affiché, identifiant technique)] des voix d'une langue."""
    return [(libelle_voix(entree), entree[0]) for entree in VOIX.get(code, [])]


def identifiant_voix(code, libelle):
    """Identifiant technique d'une voix, à partir de son libellé affiché.

    Si le libellé est inconnu (réglages d'une version précédente, libellé
    traduit entre-temps…), on retombe sur la première voix de la langue.
    """
    libelle = (libelle or "").replace(MARQUE_VOIX, "").strip()
    for etiquette, identifiant in voix_de_la_langue(code):
        if etiquette == libelle:
            return identifiant
    return VOIX[code][0][0] if VOIX.get(code) else ""


def identifiant_par_libelle(code, valeur):
    """Retrouve une voix à partir d'un ancien libellé enregistré.

    Les versions précédentes mémorisaient le libellé affiché
    (« Sylvie (Femme - Québec) »). On le cherche dans les deux langues
    d'interface, pour que les réglages existants ne soient pas perdus.
    Renvoie None si on ne reconnaît rien.
    """
    valeur = str(valeur or "").replace("★", "").strip()
    for entree in VOIX.get(code, []):
        for langue_ui in TEXTES:
            if (libelle_voix(entree, langue_ui) == valeur
                    or libelle_voix(entree, langue_ui, avec_genre=True)
                    == valeur):
                return entree[0]
    return None


# ------------------------------------------------------------------
# Listes de phrases proposées
# ------------------------------------------------------------------
# Elles suivent la langue des VOIX : des phrases françaises avec les voix
# françaises, des phrases anglaises avec les voix anglaises. Les noms de
# fichiers sont en minuscules, sans accent et font 8 caractères au maximum :
# c'est la limite lue par les radiocommandes.
LISTE_PAR_DEFAUT = {
    "fr": [
        ("mot-arme", "Moteur armé"),
        ("mot-off", "Moteur coupé"),
        ("V-decol", "Volets de décollage"),
        ("V-atter", "Volets d'atterrissage"),
        ("v-rentre", "Volet rentré"),
        ("train-so", "Train sorti"),
        ("train-re", "Train rentré"),
        ("chrono-d", "Chrono démarré"),
        ("chrono-a", "Chrono arrêté"),
        ("mv-norm", "Mode normal"),
        ("mv-grat", "Mode thermique"),
        ("mv-vite", "Mode vitesse"),
        ("mv-deco", "Mode décollage"),
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
    ],
    "en": [
        ("armed", "Motor armed"),
        ("disarmed", "Motor disarmed"),
        ("flaps-tk", "Takeoff flaps"),
        ("flap-ldg", "Landing flaps"),
        ("flap-up", "Flaps up"),
        ("gear-dn", "Gear down"),
        ("gear-up", "Gear up"),
        ("timer-on", "Timer started"),
        ("timr-off", "Timer stopped"),
        ("mode-nrm", "Normal mode"),
        ("mode-th", "Thermal mode"),
        ("mode-spd", "Speed mode"),
        ("mode-tko", "Takeoff mode"),
        ("crow-act", "Crow enabled"),
        ("crow-dis", "Crow disabled"),
        ("tow-drop", "Tow released"),
        ("stab-off", "Stabilization off"),
        ("stab-on", "Stabilization on"),
        ("stab-aut", "Auto stabilization"),
        ("panic", "Panic"),
        ("gain-up", "Gain increased"),
        ("gain-dn", "Gain decreased"),
        ("landing", "Landing mode"),
        ("acro", "Acrobatic mode"),
        ("airbrake", "Airbrakes"),
        ("cruise", "Cruise"),
        ("takeoff", "Takeoff"),
        ("land", "Landing"),
        ("rate-hi", "High rates"),
        ("rate-mid", "Medium rates"),
        ("rate-low", "Low rates"),
        ("flaperon", "Flaperon"),
        ("launch", "Launch"),
        ("lgt-on", "Lights on"),
        ("lgt-off", "Lights off"),
        ("medium", "Medium"),
        ("high", "High"),
        ("low", "Low"),
        ("snapflap", "Snapflap"),
        ("stab-1", "Stability one"),
        ("stab-2", "Stability two"),
        ("tx-hi", "High rate"),
        ("tx-mid", "Medium rate"),
        ("tx-lo", "Low rate"),
    ],
    "de": [
        # 13 noms officiels du jeu allemand d'EdgeTX (traduction identique au
        # mot près) ; les autres sont nos noms, comme pour la liste française,
        # qui est entièrement la nôtre.
        ("engon", "Motor an"),
        ("engoff", "Motor aus"),
        ("gearup", "Fahrwerk eingefahren"),
        ("geardn", "Fahrwerk ausgefahren"),
        ("flapup", "Klappen eingefahren"),
        ("flapdn", "Klappen ausgefahren"),
        ("crowon", "Butterfly ein"),
        ("crowof", "Butterfly aus"),
        ("lnding", "Lande-Modus"),
        ("fm-nrm", "Normal-Modus"),
        ("fm-thm", "Thermik-Modus"),
        ("fm-spd", "Geschwindigkeits-Modus"),
        ("acro", "Akro-Modus"),
        ("abscfrei", "Schleppkupplung offen"),
        ("gross", "Großer Ausschlag"),
        ("mittel", "Mittlerer Ausschlag"),
        ("klein", "Kleiner Ausschlag"),
        ("flperon", "Flapperon"),
        ("snapflap", "Snapflap"),
        ("luftbrem", "Luftbremsen"),
        ("panik", "Panik"),
        ("timer-st", "Timer gestartet"),
        ("timer-sp", "Timer gestoppt"),
        ("timovr1", "Timer eins abgelaufen"),
        ("timovr2", "Timer zwei abgelaufen"),
        ("stab-an", "Stabilisierung an"),
        ("stabauto", "Automatische Stabilisierung"),
        ("stab-aus", "Stabilisierung aus"),
    ],
}

# Les listes de base des douze nouvelles langues : un CSV par langue dans
# voxpack_data/listes-base/ (nom;phrase), tiré du CSV officiel d'EdgeTX et
# complété par traduction quand l'annonce manquait. Ce sont des fichiers du
# paquet, pas un prototype : à joindre à la compilation (voir Vox-Pack.spec).
_DOSSIER_BASES = trouver_ressource("voxpack_data", "listes-base")
if os.path.isdir(_DOSSIER_BASES):
    for _code in LANGUES:
        _chemin = os.path.join(_DOSSIER_BASES, _code + ".csv")
        if _code in LISTE_PAR_DEFAUT or not os.path.exists(_chemin):
            continue
        _lignes = []
        with open(_chemin, encoding="utf-8", newline="") as _f:
            for _morceaux in csv.reader(_f, delimiter=";"):
                if len(_morceaux) >= 2 and _morceaux[0].strip():
                    _lignes.append((_morceaux[0].strip(),
                                    _morceaux[1].strip()))
        if _lignes:
            LISTE_PAR_DEFAUT[_code] = _lignes

# Palette
BG_MAIN = "#000000"        # fond uni noir
CYAN = "#00B8C5"
CYAN_DARK = "#00A8B8"
CYAN_HOVER = "#2A5A66"
CYAN_CLAIR = "#C1FEFF"     # survol : le texte et le cadre s'éclairent
LINK_COLOR = "#7FE0E8"     # liens cliquables (comme dans mes autres applis)
TEXT_WHITE = "#DBDBDB"
TEXT_GREY = "#8A9AA9"

# Signature : la page des applications de Richard. Le soutien s'ouvre par le
# lien Ko-fi, juste en dessous.
URL_SITE = "https://ritchy-lab.github.io/"
KO_FI_URL = "https://ko-fi.com/ritchy_lab"
URL_RELEASES = "https://github.com/ritchy-lab/Vox-Pack/releases"


def derniere_version_publiee():
    """Dernière version publiée sur GitHub, ou None si indisponible."""
    try:
        requete = urllib.request.Request(
            "https://api.github.com/repos/ritchy-lab/Vox-Pack/releases/latest",
            headers={"User-Agent": f"Vox-Pack/{VERSION}",
                     "Accept": "application/vnd.github+json"})
        contexte = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(requete, timeout=6,
                                    context=contexte) as reponse:
            donnees = json.load(reponse)
        etiquette = str(donnees.get("tag_name", "")).strip()
        if not etiquette:
            return None
        assets = []
        for element in donnees.get("assets", []) or []:
            nom = str(element.get("name", ""))
            url = str(element.get("browser_download_url", ""))
            if nom and url:
                assets.append({"name": nom, "url": url})
        return {"tag": etiquette, "assets": assets}
    except Exception:
        # Hors ligne, API limitée, dépôt injoignable : on ne dérange pas.
        return None


def version_plus_recente(etiquette, actuelle=VERSION):
    """Vrai si l'étiquette (V1.4) est plus récente que la version actuelle."""
    def morceaux(v):
        return tuple(int(n) for n in re.findall(r"\d+", v))
    return morceaux(etiquette) > morceaux(actuelle)


def version_de_reference():
    """Version à laquelle se comparer au démarrage.

    Normalement celle du programme. La variable d'environnement
    VOXPACK_MAJ_TEST permet de regarder la fenêtre « Mise à jour disponible »
    sans publier une version plus récente — elle est sinon presque impossible
    à voir, puisque la nouvelle version la fait disparaître :

        VOXPACK_MAJ_TEST=1.0 venv/bin/python voxpack.py
    """
    return os.environ.get("VOXPACK_MAJ_TEST") or VERSION


def choisir_asset(assets):
    """Choisit le fichier à télécharger pour ce système."""
    if sys.platform == "darwin":
        extension = ".zip"
    elif sys.platform.startswith("win"):
        extension = ".exe"
    else:
        return None
    for asset in assets or []:
        if str(asset.get("name", "")).lower().endswith(extension):
            return asset
    return None

# Largeur unique de tous les boutons (homogènes)
BTN_W = 170
BTN_H = 34

# ------------------------------------------------------------------
# Typographie — aucun gras dans la fenêtre principale : les tailles et les
# contrastes suffisent, et le rendu est plus léger.
# ------------------------------------------------------------------
TYPO_LISTE = 17          # les lignes de la liste (nom du fichier + phrase)
HAUTEUR_LIGNE = 34       # hauteur de ces cases (7 lignes visibles)
TYPO_BOUTON = 16        # texte des boutons
TYPO_PETIT_BOUTON = 14  # petits boutons (Tout / Rien)

# Les deux textes d'information de la fenêtre
TYPO_INFO = 12          # la ligne d'état, sous la barre de leds
HAUTEUR_INFO = 16       # sa hauteur (doit contenir la police ci-dessus)
TYPO_MESSAGE = 14       # les avertissements, à droite des lignes
TYPO_ALERTE = 18        # le texte des fenêtres d'alerte

# ------------------------------------------------------------------
# Échelle de l'interface
# ------------------------------------------------------------------
# Sur un écran de 1280 x 720 (un portable 1080 réglé à 150 %), la fenêtre
# tient, mais une typographie prévue pour un grand écran paraît énorme : on
# resserre alors polices et espacements, plutôt que de sacrifier des lignes.
#
# Sur un écran confortable, rien ne change : l'application garde exactement
# l'allure pour laquelle elle a été dessinée.
ECHELLE_UI = 1.0

# Les constantes que l'échelle ajuste.
NOMS_ECHELLE = ("TYPO_LISTE", "HAUTEUR_LIGNE", "TYPO_BOUTON", "TYPO_PETIT_BOUTON",
                "TYPO_INFO", "HAUTEUR_INFO", "TYPO_MESSAGE", "TYPO_ALERTE",
                "TYPO_MENU", "TYPO_MENU_BOUTON",
                "ESPACE_HAUT", "ESPACE_LOGO_BOUTONS", "ESPACE_BOUTONS_LISTE",
                "ESPACE_LISTE_LEDS", "ESPACE_LEDS_BOUTONS", "ESPACE_BAS",
                "BTN_H", "BTN_W")

# Les valeurs d'origine, retenues une fois pour toutes à la fin des constantes
# (voir plus bas). L'échelle peut ainsi être recalculée autant de fois qu'on
# veut, sans que les réductions s'additionnent : c'est le genre de piège qui
# fait qu'une interface devient minuscule après deux appels.
VALEURS_ORIGINE = {}


def regler_echelle(hauteur_ecran):
    """Ajuste la typographie et les espacements à la place disponible."""
    global ECHELLE_UI

    ECHELLE_UI = 1.0 if hauteur_ecran >= ECRAN_CONFORTABLE else 0.9

    for nom in NOMS_ECHELLE:
        base = VALEURS_ORIGINE[nom]
        # Les hauteurs gardent un plancher : en dessous, le texte est rogné.
        plancher = 0.6 if nom.startswith(("TYPO", "HAUTEUR")) else 0
        globals()[nom] = max(int(round(base * ECHELLE_UI)), int(base * plancher))
    # Les espacements pairs donnent un rendu plus net.
    globals()["HAUTEUR_LIGNE"] = max(globals()["HAUTEUR_LIGNE"], 24)


# ------------------------------------------------------------------
# Mise en page
# ------------------------------------------------------------------
# Taille souhaitée de la fenêtre. Elle se réduit automatiquement si l'écran
# est plus petit (voir VoxPackApp.__init__).
LARGEUR_FENETRE = 820
HAUTEUR_FENETRE = 829

# Fenêtre « Mise à jour disponible ». Les textes s'enroulent à LARGEUR_TEXTE :
# la fenêtre doit donc être plus large que ça, sinon le texte est coupé au lieu
# de passer à la ligne. La fenêtre est ensuite redimensionnée sur son contenu,
# à chaque fois que le texte change (voir VoxPackApp._ajuster_maj).
LARGEUR_TEXTE_MAJ = 420
MARGE_MAJ = 24
LARGEUR_MAJ = LARGEUR_TEXTE_MAJ + 2 * MARGE_MAJ

# Écran « confortable » : au-delà de cette hauteur, l'application garde son
# allure d'origine. En dessous (portable 1080 réglé à 150 % : Windows annonce
# alors 1280 x 720), elle se resserre : logo plus modeste et moins de lignes,
# mais des lignes bien lisibles.
ECRAN_CONFORTABLE = 900
LIGNES_GRAND_ECRAN = 7
LIGNES_PETIT_ECRAN = 5
LARGEUR_LOGO_PETIT = 220

# Largeur du logo dans l'en-tête, en pixels. Le dessin fait 1344 x 652, soit
# un rapport de 2,06 : 460 px de large donnent 223 px de haut.
LARGEUR_LOGO = 400

# Espacements verticaux, du haut vers le bas. C'est ici qu'on règle
# l'harmonie de la fenêtre.
ESPACE_HAUT = 14            # haut de la fenêtre -> logo
ESPACE_LOGO_BOUTONS = 10    # logo -> rangée de boutons
ESPACE_BOUTONS_LISTE = 24   # rangée de boutons -> en-tête du tableau
ESPACE_LISTE_LEDS = 16      # liste -> compteur et barre de leds
ESPACE_LEDS_BOUTONS = 0    # barre de leds -> rangée du bas
ESPACE_BAS = 18             # rangée du bas -> bas de la fenêtre

# Durée, en secondes, pendant laquelle la barre reste complètement allumée
# avant de s'éteindre. Trop courte, on ne voit jamais la dernière led
# s'allumer (l'animation met un instant à la rejoindre).
PAUSE_LEDS = 0.8

# Menu. Le choix de langue y est entré, et il faut qu'il soit lisible :
# la police par défaut d'un menu Tk est minuscule sur Windows.
TYPO_MENU = 14            # texte des entrées du menu
TYPO_MENU_BOUTON = 26     # les trois barres qui ouvrent le menu (hors macOS)

# Curseur « main » pour les éléments cliquables. Tk accepte les deux noms sans
# se plaindre, mais n'affiche la bonne main que si le nom correspond au
# système : pointinghand est celui de macOS, hand2 celui de Windows/X11.
CURSEUR_MAIN = "pointinghand" if sys.platform == "darwin" else "hand2"


# Fenêtre de soutien : largeur de départ. Elle s'élargit si les boutons
# demandent plus de place (voir _ouvrir_soutien).
LARGEUR_SOUTIEN = 380

# Le bouton « Oui » de la fenêtre de soutien : largeur, hauteur, police et
# arrondi. L'arrondi doit valoir environ la moitié de la hauteur, sinon le
# bouton perd sa forme de « gélule ».
OUI_LARGEUR = 140
OUI_HAUTEUR = 40
OUI_TYPO = 18

# Fin des constantes : on retient leurs valeurs d'origine pour l'échelle.
VALEURS_ORIGINE.update({nom: globals()[nom] for nom in NOMS_ECHELLE})

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


def raison_lisible(erreur):
    """Traduit une erreur technique en explication courte, dans la langue de
    l'interface.

    Le service de voix peut refuser l'accès, retirer une voix ou ne pas
    répondre : mieux vaut le dire clairement que d'afficher « 403 ».
    """
    texte = str(erreur)
    bas = texte.lower()
    if "403" in texte or "forbidden" in bas:
        return t("err_refus")
    if "404" in texte or "not found" in bas or "no audio" in bas:
        return t("err_voix_absente")
    if "timeout" in bas or "timed out" in bas:
        return t("err_lent")
    if any(mot in bas for mot in ("decompress", "incorrect header", "zlib")):
        return t("err_illisible")
    if any(mot in bas for mot in ("connection", "network", "getaddrinfo",
                                  "unreachable", "ssl", "certificate")):
        return t("err_reseau")
    return texte[:120]


def probleme_nom(nom):
    """Renvoie None si le nom convient, sinon la raison, en clair."""
    if not nom:
        return t("pb_vide")
    if len(nom) > LIMITE_NOM:
        return t("pb_long", n=len(nom), max=LIMITE_NOM)
    if " " in nom or "\t" in nom:
        return t("pb_espace")
    mauvais = sorted({c for c in nom if c not in CARACTERES_AUTORISES})
    if mauvais:
        if any(c in ACCENTS for c in mauvais):
            return t("pb_accent")
        return t("pb_caractere", c=mauvais[0])
    return None


# ------------------------------------------------------------------
# Réglages de l'application (dernier dossier utilisé)
# ------------------------------------------------------------------
REGLAGES_FILE = os.path.join(DATA_DIR, "reglages.json")


def lire_reglages():
    try:
        with open(REGLAGES_FILE, "r", encoding="utf-8") as f:
            reglages = json.load(f)
    except Exception:
        return {}
    return _reglages_surs(reglages)


def _reglages_surs(reglages):
    """Ne garde que les réglages dont le type est celui qu'on écrit.

    Un fichier modifié à la main, ou écrit par une version qui rangeait
    autrement, ne doit jamais empêcher la fenêtre de s'ouvrir : un « voix »
    qui n'était pas un dictionnaire faisait planter l'application au
    démarrage, avant même le premier pixel (voir _remplir_voix).
    """
    if not isinstance(reglages, dict):
        return {}
    propres = {}
    langue = reglages.get("langue_ui")
    if isinstance(langue, str) and langue in TEXTES:
        propres["langue_ui"] = langue
    voix = reglages.get("voix")
    if isinstance(voix, dict):
        propres["voix"] = {
            code: valeur for code, valeur in voix.items()
            if isinstance(code, str) and isinstance(valeur, str)}
    for cle in ("niveau", "allure", "robot"):
        valeur = reglages.get(cle)
        if isinstance(valeur, int) and not isinstance(valeur, bool):
            propres[cle] = valeur
    for cle in ("dernier_dossier", "dernier_dossier_systeme"):
        valeur = reglages.get(cle)
        if isinstance(valeur, str) and valeur:
            propres[cle] = valeur
    soutien = reglages.get("soutien_fermeture")
    if isinstance(soutien, bool):
        propres["soutien_fermeture"] = soutien
    return propres


def ecrire_reglages(reglages):
    """Écrit les réglages d'un seul coup : temporaire, puis remplacement.

    Une écriture interrompue (disque plein, arrêt brutal) laissait un JSON
    tronqué. Au lancement suivant, lire_reglages le rejetait : langue,
    voix, dernier dossier et réglages des curseurs repartaient aux valeurs
    par défaut, sans un mot.
    """
    temporaire = REGLAGES_FILE + ".tmp"
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(temporaire, "w", encoding="utf-8") as f:
            json.dump(reglages, f, ensure_ascii=False, indent=2)
        os.replace(temporaire, REGLAGES_FILE)
    except Exception:
        try:
            os.remove(temporaire)
        except OSError:
            pass
        # des réglages, ce n'est pas vital : on n'alerte pas


# ------------------------------------------------------------------
# Texte posé sur la carcasse (aucun rectangle noir derrière)
# ------------------------------------------------------------------
class TexteCarcasse(tk.Canvas):
    """Un texte dont le fond est un morceau de l'image.

    `configure(text=...)` remplace le texte, pour que le moteur puisse écrire
    dedans comme dans une étiquette ordinaire (le compteur du bas).
    """

    def __init__(self, parent, bande, texte, couleur, fonte, ancre="w"):
        photo = ImageTk.PhotoImage(bande)
        super().__init__(parent, width=bande.width, height=bande.height,
                         highlightthickness=0, bd=0)
        self._photo = photo
        self.create_image(0, 0, image=photo, anchor="nw")
        if ancre == "w":
            x = 0
        elif ancre == "center":
            x = bande.width // 2
        else:
            x = bande.width
        self._item = self.create_text(
            x, bande.height // 2,
            text=texte, fill=couleur, anchor=ancre, font=fonte)

    def configure(self, **options):
        if hasattr(self, "_item"):
            texte = options.pop("text", None)
            if texte is not None:
                self.itemconfigure(self._item, text=texte)
        if options:
            tk.Canvas.configure(self, **options)


# ------------------------------------------------------------------
# Le champ LANGUE : un petit écran, pas un menu
# ------------------------------------------------------------------
class EcranV2(tk.Canvas):
    """Un affichage : cadre de métal, verre teinté, balayage, texte allumé.

    La langue ne se choisit plus en cliquant ce champ (c'est le menu qui
    ouvre la fenêtre des langues). Pour qu'on ne cherche pas un menu
    derrière, il est dessiné comme un petit écran : un cadre avec son creux,
    une lueur en haut du verre, des traits de balayage, et le nom écrit dans
    le cyan clair d'un affichage. Il ne réagit pas à la souris.
    """

    CADRE = "#16272B"
    BORD_CLAIR = "#35565D"
    BORD_SOMBRE = "#0A1416"
    VERRE_HAUT = (9, 42, 48)
    VERRE_BAS = (2, 12, 13)
    BALAYAGE = "#0A2C31"
    LUEUR = ("#2A7F8A", "#155059", "#0B3136")
    TEXTE = "#6FE7F5"
    OMBRE = "#022226"

    def __init__(self, parent, bande, texte, couleur=None, fonte=None,
                 ancre="center", cadre=3):
        photo = ImageTk.PhotoImage(bande)
        super().__init__(parent, width=bande.width, height=bande.height,
                         highlightthickness=0, bd=0)
        self._photo = photo
        self.create_image(0, 0, image=photo, anchor="nw")
        self._l, self._h = bande.width, bande.height
        self._texte = str(texte)
        self._couleur = couleur or self.TEXTE
        self._ancre = ancre
        self._cadre = max(1, cadre)
        self._fonte = fonte
        self._dessiner()
        # Le texte est posé deux fois : son ombre d'un pixel, puis lui. C'est
        # ce qui donne l'impression de pixels allumés plutôt que d'une ligne
        # écrite à la peinture.
        x = self._cadre + 5 if ancre == "w" else self._l // 2
        self._x, self._y = x, self._h // 2
        self._ombre = self.create_text(
            x + 1, self._y + 1, text=self._texte,
            fill=self.OMBRE, font=fonte, anchor=ancre)
        self._item = self.create_text(
            x, self._y, text=self._texte,
            fill=self._couleur, font=fonte, anchor=ancre)
        self._ajuster_fonte()

    def _dessiner(self):
        l, h, b = self._l, self._h, self._cadre
        # Le cadre : un liseré clair en haut, sombre en bas, et son creux.
        self.create_rectangle(0, 0, l - 1, h - 1, fill=self.CADRE,
                              outline=self.BORD_SOMBRE)
        self.create_line(1, 1, l - 2, 1, fill=self.BORD_CLAIR)
        self.create_line(1, h - 2, l - 2, h - 2, fill=self.BORD_SOMBRE)
        self.create_rectangle(b - 1, b - 1, l - b, h - b,
                              fill="#000000", outline="")
        # Le verre, du haut vers le bas : plus clair en haut, comme un écran
        # éclairé par le dessus.
        for y in range(b, h - b):
            part = (y - b) / max(1, h - 2 * b - 1)
            self.create_line(
                b, y, l - 1 - b, y,
                fill=self._melange(self.VERRE_HAUT, self.VERRE_BAS,
                                   part ** 1.1))
        # La lueur du haut : trois traits de plus en plus sombres.
        for i, couleur in enumerate(self.LUEUR):
            self.create_line(b, b + i, l - 1 - b, b + i, fill=couleur)
        # Le balayage : un trait sur trois, un peu plus clair que le verre.
        for y in range(b + 3, h - b, 3):
            self.create_line(b, y, l - 1 - b, y, fill=self.BALAYAGE)
        self.create_line(b, h - 1 - b, l - 1 - b, h - 1 - b,
                         fill="#020D0D")

    def _ajuster_fonte(self):
        """Réduit la police tant que le texte dépasse l'écran dessiné."""
        if not self._fonte or len(self._fonte) < 2:
            return
        famille, taille = self._fonte[0], self._fonte[1]
        largeur = self._l - 2 * self._cadre - 6
        while taille > 6:
            for item in (self._item, self._ombre):
                self.itemconfig(item, font=(famille, taille))
            boite = self.bbox(self._item)
            if boite and boite[2] - boite[0] <= largeur:
                return
            taille -= 1

    @staticmethod
    def _melange(c1, c2, part):
        return "#%02X%02X%02X" % tuple(
            int(c1[i] + (c2[i] - c1[i]) * part) for i in range(3))

    def configure(self, **options):
        texte = options.pop("text", None)
        if texte is not None and hasattr(self, "_item"):
            self._texte = str(texte)
            self.itemconfigure(self._item, text=self._texte)
            self.itemconfigure(self._ombre, text=self._texte)
            self._ajuster_fonte()
        if options:
            tk.Canvas.configure(self, **options)

    def cget(self, option):
        if option == "text":
            return self._texte
        return tk.Canvas.cget(self, option)


# ------------------------------------------------------------------
# Le voyant des sons système : une lentille rouge dans son logement
# ------------------------------------------------------------------
VOYANT_ROUGE = {
    "allume": "#FF3B30", "eteint": "#671712", "halo": "#7E1F19",
    "etincelle": "#FFF0EE", "etincelle_eteinte": "#671712",
}
VOYANT_CYAN = {
    "allume": "#22D3E6", "eteint": "#0B3B42", "halo": "#0F7F8B",
    "etincelle": "#EAFFFF", "etincelle_eteinte": "#1E5B62",
}


class VoyantV2(tk.Canvas):
    """Un voyant : éteint, une lentille sombre ; allumé, il rougeoie.

    Il s'allume quand la création des sons système démarre, et s'éteint
    quand elle est finie. Pendant le travail, il bat : on voit que ça
    avance même quand la fenêtre est passée derrière une autre.
    """

    ALLUME = "#FF3B30"
    ETEINT = "#671712"
    HALO = "#7E1F19"
    ETINCELLE = "#FFF0EE"
    ETINCELLE_ETEINTE = "#671712"
    LOGEMENT = "#2A3A3E"

    def __init__(self, parent, cote, fond, couleurs=None):
        super().__init__(parent, width=cote, height=cote, bg=fond,
                         highlightthickness=0, bd=0)
        # Rouge par défaut (le voyant SYSTEM) ; le cyan sert aux robots.
        self._c = dict(VOYANT_ROUGE, **(couleurs or {}))
        self._allume = False
        self._clignote = False
        self._visible = True
        self._attente = None
        milieu = cote / 2
        rayon = cote * 0.30
        # Le logement, puis le halo (caché), puis la lentille et son reflet.
        self.create_oval(0, 0, cote - 1, cote - 1, outline=self.LOGEMENT)
        self._halo = self.create_oval(
            milieu - rayon - 1.5, milieu - rayon - 1.5,
            milieu + rayon + 1.5, milieu + rayon + 1.5,
            outline=self._c["halo"], state="hidden")
        self._lentille = self.create_oval(
            milieu - rayon, milieu - rayon, milieu + rayon, milieu + rayon,
            fill=self._c["eteint"], outline="#000000")
        self._etincelle = self.create_oval(
            milieu - rayon * 0.50, milieu - rayon * 0.62,
            milieu - rayon * 0.12, milieu - rayon * 0.24,
            fill=self._c["etincelle_eteinte"], outline="")

    def _peindre(self):
        allume = self._allume and self._visible
        self.itemconfigure(
            self._lentille,
            fill=self._c["allume"] if allume else self._c["eteint"])
        self.itemconfigure(
            self._etincelle,
            fill=(self._c["etincelle"] if allume
                  else self._c["etincelle_eteinte"]))
        self.itemconfigure(self._halo,
                           state="normal" if allume else "hidden")

    def allumer(self):
        self._allume = True
        self._peindre()

    def eteindre(self):
        self._allume = False
        self.clignoter(False)

    def clignoter(self, actif=True):
        """Fait battre le voyant (ou l'arrête et le laisse allumé)."""
        self._clignote = actif
        if self._attente is not None:
            try:
                self.after_cancel(self._attente)
            except Exception:
                pass
            self._attente = None
        self._visible = True
        self._peindre()
        if actif:
            try:
                self._attente = self.after(450, self._battre)
            except Exception:
                self._attente = None

    def _battre(self):
        self._attente = None
        if not self._clignote:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self._visible = not self._visible
        self._peindre()
        try:
            self._attente = self.after(450, self._battre)
        except Exception:
            self._attente = None


# ------------------------------------------------------------------
# Barre de progression de la maquette : un trait, pas des points
# ------------------------------------------------------------------
class BarreV2(tk.Canvas):
    """La fente de progression, avec des ronds allumés dedans.

    L'ordre de dessin vient de Richard (4 novembre au soir), et c'est lui qui
    donne le relief :

    1. le fond de la fente, très sombre ;
    2. les ronds, espacés, sur toute la largeur ;
    3. la fente et ses deux traits PAR-DESSUS — le trait noir du haut et le
       trait clair du bas passent devant la rangée et la coupent. Dessinés
       avant, les ronds paraissaient posés sur le métal au lieu d'être
       dedans.

    Seuls les ronds de la partie faite sont rouges : le reste de la fente
    reste vide, pas une rangée de trous gris. Les ronds sont espacés et le
    nombre est calculé pour que la rangée finisse sur un rond entier : c'est
    ce qui supprime les crans en bout de fente.
    """

    # La couleur réglée par Richard le 4 novembre à 19 h 16.
    JAUGE = "#FF0D00"
    CREUX = "#040B0C"      # le fond de la fente
    OMBRE = "#24383C"      # le trait clair du bas
    NOIR = "#000000"       # le trait noir du haut
    ESPACE = 2             # pixels entre deux ronds

    def __init__(self, parent, largeur, hauteur, fond, commande=None):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond,
                         highlightthickness=0, bd=0)
        self._largeur = largeur
        self._hauteur = hauteur
        self._commande = commande
        self._valeur = 0.0
        self._cible = 0.0
        self._debut = 0.0
        self._t0 = time.time()
        self._anim = False
        self._allumes = 0

        # 1. Le fond de la fente.
        self.create_rectangle(0, 0, largeur, hauteur, fill=self.CREUX,
                              outline="")
        # 2. Les ronds.
        self._ronds = []
        self._creer_ronds()
        # 3. La fente par-dessus : ses deux traits coupent la rangée.
        self.create_line(0, 0, largeur, 0, fill=self.NOIR)
        self.create_line(0, hauteur - 1, largeur, hauteur - 1,
                         fill=self.OMBRE)

    def _creer_ronds(self):
        """Crée la rangée, une fois pour toutes.

        Les ronds sont posés ENTRE les deux traits, avec la MÊME marge
        entière au-dessus et au-dessous. Un rond à un pixel des bords se
        lisait comme un tiret coupé par les traits ; c'est la marge qui
        donne des ronds, et c'est elle aussi qui les centre.

        La marge doit être un nombre entier de pixels : avec une fente de
        6 px et un rond de 5, il resterait un demi-pixel en haut et en bas,
        et Tk arrondit — le rond paraissait décalé d'un pixel. On garde donc
        toujours deux pixels d'écart entre le rond et la hauteur de la
        fente. Pour des ronds plus gros, il faut une fente plus haute :
        7 px donnent des ronds de 5.

        L'entraxe est réparti sur toute la largeur, de sorte que la rangée
        se termine sur un rond entier et non sur une moitié.
        """
        diametre = max(2, self._hauteur - 2)
        pas = diametre + self.ESPACE
        nombre = max(1, int(self._largeur / pas))
        pas = self._largeur / nombre
        rayon = diametre / 2
        haut = (self._hauteur - diametre) // 2
        for i in range(nombre):
            centre = pas * (i + 0.5)
            self._ronds.append(self.create_oval(
                centre - rayon, haut, centre + rayon, haut + diametre,
                fill=self.CREUX, outline=""))

    def set(self, valeur):
        self._cible = max(0.0, min(1.0, float(valeur)))
        # On repart de la valeur affichée : la jauge rejoint sa cible en un
        # temps fixe (450 ms), quelle que soit la distance. Une approche
        # proportionnelle n'atteignait jamais le bout.
        self._debut = self._valeur
        self._t0 = time.time()
        if not self._anim:
            self._anim = True
            self._pas()

    def _pas(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        part = min(1.0, (time.time() - self._t0) / 0.45)
        douceur = 1 - (1 - part) ** 3
        self._valeur = self._debut + (self._cible - self._debut) * douceur
        if part >= 1.0:
            self._valeur = self._cible
            self._anim = False
            self._dessiner()
            return
        self._dessiner()
        self.after(25, self._pas)

    def _dessiner(self):
        """Allume les ronds de la partie faite, éteint les autres."""
        allumes = int(round(len(self._ronds) * self._valeur))
        if self._valeur >= 1.0:
            allumes = len(self._ronds)
        # Seuls les ronds qui changent d'état sont repeints : la jauge
        # avance de quelques ronds par image, pas de la rangée entière.
        debut = min(self._allumes, allumes)
        fin = max(self._allumes, allumes)
        for i in range(debut, fin):
            self.itemconfigure(
                self._ronds[i],
                fill=self.JAUGE if i < allumes else self.CREUX)
        self._allumes = allumes
        if self._commande:
            try:
                self._commande(self._valeur)
            except Exception:
                pass

    def reset(self):
        """Redescend doucement, mais pas tout de suite.

        Le moteur appelle reset() juste après le dernier set(1.0) : sans cette
        pause, la jauge n'a pas le temps d'atteindre le bout et retombe avant
        — c'est ce qui donnait l'impression qu'elle s'arrêtait avant la fin.
        """
        def redescendre():
            try:
                self.set(0.0)
            except Exception:
                pass

        try:
            self.after(900, redescendre)
        except Exception:
            pass


# ------------------------------------------------------------------
# Curseur des réglages : un creux, une jauge, un bouton
# ------------------------------------------------------------------
class CurseurV2(tk.Canvas):
    """Le curseur de la maquette : piste en dégradé, poignée biseautée.

    La piste va du cyan au jaune puis au rouge : le sens et la zone forte se
    lisent sans bouger le curseur. Le trajet parcouru depuis 0 se rallume.
    """

    CYAN = (15, 187, 208)
    JAUNE = (233, 190, 62)
    ROUGE = (214, 62, 52)

    def __init__(self, parent, largeur, hauteur, fond, mini, maxi, valeur,
                 commande=None, degrade=True):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond,
                         highlightthickness=0, bd=0, cursor=CURSEUR_MAIN)
        self._l, self._h = largeur, hauteur
        self._mini, self._maxi = mini, maxi
        self._commande = commande
        self._degrade = degrade
        self._marge = largeur * 0.07
        milieu = hauteur / 2
        self._milieu = milieu
        self._demi = 3
        self._piste = []
        for i in range(int(self._marge), int(largeur - self._marge) + 1):
            self._piste.append(self.create_line(
                i, milieu - self._demi, i, milieu + self._demi,
                fill=self._attenue(self._teinte(i))))
        self.create_line(self._marge, milieu - self._demi,
                         largeur - self._marge, milieu - self._demi,
                         fill="#6E8A8F")
        self.create_line(self._marge, milieu + self._demi,
                         largeur - self._marge, milieu + self._demi,
                         fill="#08110F")
        centre = self._x_pour(0)
        # Le cran du milieu : un trait clair qui marque le 0 (0 dB ou 0 %).
        self._cran = self.create_line(
            centre, milieu - 10, centre, milieu + 10, fill="#A7C4C9", width=1)

        self._parcouru = []
        self._poignee = self.create_polygon(
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            fill="#2A3C41", outline="#5E7A7F", width=1)
        self._dessus = self.create_rectangle(0, 0, 0, 0, fill="#4E666C",
                                             outline="")
        self._arete_haut = self.create_line(0, 0, 0, 0, fill="#8FB3B8")
        self._arete_bas = self.create_line(0, 0, 0, 0, fill="#08110F")
        self._coin_haut = self.create_line(0, 0, 0, 0, fill="#0FBBD0")
        self._coin_bas = self.create_line(0, 0, 0, 0, fill="#0FBBD0")
        self.bind("<Button-1>", self._clic)
        self.bind("<B1-Motion>", self._clic)
        self.bind("<Double-Button-1>", self._reinitialiser)
        self._valeur = None
        self.regler(valeur, prevenir=False)

    # -- couleurs -----------------------------------------------------
    @staticmethod
    def _melange(c1, c2, fraction):
        return "#%02X%02X%02X" % tuple(
            int(c1[i] + (c2[i] - c1[i]) * fraction) for i in range(3))

    def _teinte(self, x):
        if not self._degrade:
            return "#4FD8E6"
        part = (x - self._marge) / (self._l - 2 * self._marge)
        return self._gain(max(0.0, min(1.0, part)))

    def _gain(self, fraction):
        if fraction <= 0.6:
            return self._melange(self.CYAN, self.JAUNE, fraction / 0.6)
        return self._melange(self.JAUNE, self.ROUGE,
                             (fraction - 0.6) / 0.4)

    @staticmethod
    def _attenue(couleur):
        r = int(couleur[1:3], 16) * 0.9
        v = int(couleur[3:5], 16) * 0.9
        b = int(couleur[5:7], 16) * 0.9
        return "#%02X%02X%02X" % (int(r), int(v), int(b))

    @staticmethod
    def _eclairci(couleur, part):
        """La même teinte, tirée vers le blanc : le trajet parcouru s'allume."""
        canaux = [int(couleur[i:i + 2], 16) for i in (1, 3, 5)]
        return "#%02X%02X%02X" % tuple(
            int(c + (255 - c) * part) for c in canaux)

    # -- géométrie ----------------------------------------------------
    def _x_pour(self, valeur):
        part = (valeur - self._mini) / (self._maxi - self._mini)
        return self._marge + part * (self._l - 2 * self._marge)

    def _valeur_pour(self, x):
        part = (x - self._marge) / (self._l - 2 * self._marge)
        valeur = self._mini + part * (self._maxi - self._mini)
        valeur = max(self._mini, min(self._maxi, round(valeur)))
        # Le cran du milieu retient le curseur : à deux pour cent de la
        # course, on retombe sur 0. C'est ce qui permet de viser 0 % sans
        # se battre avec la souris.
        if self._mini < 0 < self._maxi:
            if abs(valeur) <= (self._maxi - self._mini) * 0.02:
                return 0
        return valeur

    def _reinitialiser(self, _evenement=None):
        """Double-clic sur la piste : retour au cran du milieu (0 dB, 0 %)."""
        self.regler(0)

    def regler(self, valeur, prevenir=True):
        valeur = max(self._mini, min(self._maxi, valeur))
        if valeur == self._valeur:
            return
        self._valeur = valeur
        x = self._x_pour(valeur)
        centre = self._x_pour(0)
        milieu = self._milieu
        for trait in self._parcouru:
            self.delete(trait)
        self._parcouru = []
        for i in range(int(min(x, centre)), int(max(x, centre)) + 1):
            self._parcouru.append(self.create_line(
                i, milieu - self._demi, i, milieu + self._demi,
                fill=self._eclairci(self._teinte(i), 0.25)))
        self.tag_raise(self._cran)
        y, d, h, c = milieu, 6, 10, 4
        self.coords(self._poignee,
                    x - d, y - h, x + d - c, y - h, x + d, y - h + c,
                    x + d, y + h, x - d, y + h, x - d, y + h - c)
        self.coords(self._coin_haut, x + d - c, y - h, x + d, y - h + c)
        self.coords(self._coin_bas, x - d, y + h - c, x - d + c, y + h)
        self.coords(self._dessus, x - d + 1, y - h + 1, x + d - c, y - h + 4)
        self.coords(self._arete_haut, x - d + 1, y - h + 1,
                    x + d - c - 1, y - h + 1)
        self.coords(self._arete_bas, x - d + 1, y + h - 1,
                    x + d - 1, y + h - 1)
        for item in (self._poignee, self._dessus, self._coin_haut,
                     self._coin_bas):
            self.tag_raise(item)
        if prevenir and self._commande:
            self._commande(valeur)

    def _clic(self, evenement):
        self.regler(self._valeur_pour(evenement.x))


# ------------------------------------------------------------------
# Bouton dessiné de la maquette : coin coupé, icône tracée, survol
# ------------------------------------------------------------------
def espacer_v2(texte):
    """Capitales espacées — sauf pour les écritures qui n'ont pas d'espaces."""
    texte = str(texte).upper()
    if any("\u3040" <= c <= "\u9fff" for c in texte):
        return texte
    return " ".join(texte)


class BoutonV2(tk.Canvas):
    """Un bouton dessiné : coin haut-droit coupé à 45°, comme la maquette.

    Il accepte `configure(text=…)`, `configure(command=…)`,
    `configure(state=…)` et `configure(fg_color=…)` : le moteur de la 1.5.1
    parle aux boutons comme avant, sans qu'une ligne de règle change.
    """

    # Les icônes (+ − ▶ ■) : grises au repos, blanches au survol — le cyan
    # se perdait sur la face du bouton. Le + et le − sont tracés plus épais.
    ICONE_REPOS = "#7C959A"
    ICONE_SURVOL = "#FFFFFF"
    ICONE_EPAIS = 2
    def __init__(self, parent, texte, x, y, largeur, hauteur, decor=None,
                 fond="#000000", face="#16262A", couleur_texte="#E9F4F6",
                 biseau=10, fonte=None, commande=None, plein=False,
                 contour=False, icone=None, espace=False):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond,
                         highlightthickness=0, bd=0, cursor=CURSEUR_MAIN,
                         takefocus=0)
        self.place(x=x, y=y)
        self._commande = commande
        self._actif = True
        self._plein = plein
        self._contour = contour
        self._espace = espace
        self._face_repos = "#0B2E36" if plein else face
        self._face = self._face_repos
        self._survol = "#12414C" if plein else "#1B3B44"
        self._bord = "#3E5559" if contour else ("#0FBBD0" if plein else "#4C6469")
        self._bord_survol = "#0FBBD0"
        if decor is not None:
            self._photo = decor
            self.create_image(0, 0, image=decor, anchor="nw")
        c, l, h = biseau, largeur, hauteur
        self._forme = self.create_polygon(
            1, h - c, c, h - 1, l - 1, h - 1, l - 1, c, l - c, 1, 1, 1,
            fill=self._face, outline=self._bord, width=1)
        self.create_line(l - c, 1, l - 1, c, fill="#0FBBD0", width=1)
        self.create_line(1, h - c, c, h - 1, fill="#0FBBD0", width=1)
        self._l, self._h = l, h
        self._cx, self._cy = l / 2, h / 2
        self._texte_brut = texte
        self._fonte = fonte
        self._texte = self.create_text(
            self._cx, self._cy, text=espacer_v2(texte) if espace else texte,
            fill=couleur_texte, font=fonte)
        self._icone = icone
        self._icone_items = []
        if icone:
            self._dessiner_icone(icone, l - 17, h / 2)
        self._decalage = 0
        self._ajuster_fonte()
        self._placer_texte()
        self._pointer_dedans = False
        # Vrai seulement si l'appui a commencé SUR ce bouton : sans cela, un
        # relâchement de souris venu d'ailleurs (le panneau des voix qui se
        # referme, par exemple) déclenchait l'action du bouton situé dessous.
        self._enfonce = False
        self.bind("<Enter>", self._entrer)
        self.bind("<Leave>", self._sortir)
        self.bind("<ButtonPress-1>", self._enfoncer)
        self.bind("<ButtonRelease-1>", self._relacher)

    def dire(self, texte, arret=None):
        self._texte_brut = texte
        # « ■  Arrêter » : le carré devient l'icône dessinée, à la place du
        # triangle, au lieu d'être un caractère posé devant le mot. `arret`
        # permet de le demander sans dépendre du caractère « ■ » : les douze
        # nouvelles langues n'ont pas ce caractère dans leur traduction.
        if arret is None:
            arret = "■" in str(texte)
        propre = str(texte).replace("■", "").strip()
        self.itemconfig(self._texte,
                        text=espacer_v2(propre) if self._espace else propre)
        self._dessiner_icone("stop" if arret else self._icone,
                             self._l - 17, self._h / 2)
        self._ajuster_fonte()
        self._placer_texte()

    def _ajuster_fonte(self):
        """Réduit la police tant que le texte dépasse la largeur du bouton.

        Sur un PC à 125 % ou 150 %, Tk rend les tailles en points 1,33 ou
        1,67 fois plus grandes, alors que le bouton garde sa largeur en
        pixels : « SUPPRIMER » ou « ПРОСЛУШАТЬ » sortaient de la forme. On
        préfère un mot un peu plus petit à un mot coupé.
        """
        if not self._fonte or len(self._fonte) < 2:
            return
        famille, taille = self._fonte[0], self._fonte[1]
        # L'icône occupe le bord droit (~24 px) : le texte doit s'arrêter
        # avant, sinon _placer_texte le décale à gauche et le début du mot
        # sort du bouton — « SUPPRIMER » devenait « JPPRIMER » sous Windows.
        limite = self._l - 10 - (24 if self._icone_items else 0)
        while taille > 7:
            self.itemconfig(self._texte, font=(famille, taille))
            boite = self.bbox(self._texte)
            if boite and boite[2] - boite[0] <= limite:
                return
            taille -= 1

    def _placer_texte(self):
        """Centre le texte ; le décale à gauche si l'icône le toucherait.

        À 820 px la place suffit toujours ; sur un écran plus court, la
        fenêtre rétrécit et « SUPPRIMER — » venait toucher son icône.
        """
        self.coords(self._texte, self._cx, self._cy)
        self._decalage = 0
        if not self._icone_items:
            return
        boite = self.bbox(self._texte)
        icone = self.bbox(self._icone_items[0])
        if boite is None or icone is None:
            return
        debord = boite[2] + 4 - icone[0]
        if debord > 0:
            self._decalage = debord
            self.coords(self._texte, self._cx - debord, self._cy)

    def cget(self, option):
        if option == "text":
            return getattr(self, "_texte_brut", "")
        return tk.Canvas.cget(self, option)

    def configure(self, **options):
        if hasattr(self, "_forme"):
            texte = options.pop("text", None)
            if texte is not None:
                self.dire(texte)
            commande = options.pop("command", None)
            if commande is not None:
                self._commande = commande
            etat = options.pop("state", None)
            if etat is not None:
                self._actif = etat != "disabled"
                if self._actif:
                    self._face = self._face_repos
                self.itemconfig(self._forme, fill=self._face)
            couleur = options.pop("fg_color", None)
            if couleur is not None and etat is None:
                self._face_repos = couleur
                self._face = couleur
                self.itemconfig(self._forme, fill=couleur)
        if options:
            tk.Canvas.configure(self, **options)

    def _dessiner_icone(self, forme, x, y):
        for item in getattr(self, "_icone_items", ()):
            self.delete(item)
        self._icone_items = []
        if not forme:
            return
        couleur = self.ICONE_REPOS
        if forme == "plus":
            self._icone_items.append(
                self.create_line(x - 6, y, x + 6, y, fill=couleur,
                                 width=self.ICONE_EPAIS))
            self._icone_items.append(
                self.create_line(x, y - 6, x, y + 6, fill=couleur,
                                 width=self.ICONE_EPAIS))
        elif forme == "moins":
            self._icone_items.append(
                self.create_line(x - 6, y, x + 6, y, fill=couleur,
                                 width=self.ICONE_EPAIS))
        elif forme == "lecture":
            self._icone_items.append(
                self.create_polygon(x - 5, y - 6, x - 5, y + 6, x + 6, y,
                                    fill=couleur, outline=""))
        elif forme == "stop":
            self._icone_items.append(
                self.create_rectangle(x - 5, y - 5, x + 5, y + 5,
                                      fill=couleur, outline=""))
        if getattr(self, "_pointer_dedans", False):
            self._peindre_icones(self.ICONE_SURVOL)

    def _peindre_icones(self, couleur):
        for item in self._icone_items:
            self.itemconfig(item, fill=couleur)

    def _entrer(self, _event=None):
        if not self._actif:
            return
        self._pointer_dedans = True
        self.itemconfig(self._forme, fill=self._survol,
                        outline=self._bord_survol)
        self._peindre_icones(self.ICONE_SURVOL)

    def _sortir(self, _event=None):
        self._pointer_dedans = False
        self.itemconfig(self._forme, fill=self._face, outline=self._bord)
        self._peindre_icones(self.ICONE_REPOS)

    def _enfoncer(self, _event):
        if not self._actif:
            return
        self._enfonce = True
        self.itemconfig(self._forme, fill="#0C1618")
        self.coords(self._texte, self._cx - self._decalage,
                    self._cy + 1)

    def _relacher(self, _event):
        self.coords(self._texte, self._cx - self._decalage, self._cy)
        if not self._actif or not self._enfonce:
            self._enfonce = False
            return
        self._enfonce = False
        if self._pointer_dedans:
            self._entrer()
        else:
            self._sortir()
        if self._commande:
            self._commande()


# ------------------------------------------------------------------
# Champ VOIX : le nom, et la liste qui s'ouvre dessous
# ------------------------------------------------------------------
class ChampVoixV2(tk.Frame):
    """Le champ VOIX de la maquette : le nom seul, sans flèche.

    Le menu déroulant de customtkinter réservait la place de sa flèche, ce
    qui coupait la fin du nom et son étoile. Ce champ prend toute la largeur
    et parle au moteur comme l'ancien : get(), set(), configure(values=…).
    """

    def __init__(self, parent, largeur, hauteur, fond, texte, commande=None,
                 couleur="#E9F4F6", fonte=None):
        super().__init__(parent, width=largeur, height=hauteur, bg=fond,
                         highlightthickness=0, bd=0, cursor=CURSEUR_MAIN)
        self._fond = fond
        self._commande = commande
        self._valeurs = []
        self._courant = texte
        self._fonte = fonte
        self._couleur = couleur
        self._panneau = None
        self._label = tk.Label(self, text=texte, bg=fond, fg=couleur,
                               anchor="center", font=fonte)
        self._label.place(x=0, y=0, relwidth=1, relheight=1)
        self._label.bind("<Button-1>", self._clic)
        self.bind("<Button-1>", self._clic)

    def get(self):
        return self._courant

    def set(self, valeur):
        texte = str(valeur)
        if MARQUE_VOIX:
            texte = texte.replace(MARQUE_VOIX, "")
        self._courant = texte.strip()
        self._label.configure(text=self._courant)

    def configure(self, **options):
        if not hasattr(self, "_label"):
            return tk.Frame.configure(self, **options)
        valeurs = options.pop("values", None)
        if valeurs is not None:
            self._valeurs = list(valeurs)
        commande = options.pop("command", None)
        if commande is not None:
            self._commande = commande
        for inutile in ("width", "height", "fg_color", "state"):
            options.pop(inutile, None)
        if options:
            tk.Frame.configure(self, **options)

    def fermer(self):
        panneau = self._panneau
        self._panneau = None
        if panneau is not None and panneau.winfo_exists():
            panneau.destroy()

    def _clic(self, _evenement=None):
        if self._panneau is not None:
            self.fermer()
            return "break"
        if not self._valeurs:
            return "break"
        parent = self.winfo_toplevel()
        panneau = tk.Frame(parent, bg="#0A1416",
                           highlightbackground="#3E5559",
                           highlightthickness=1)
        for valeur in self._valeurs:
            ligne = tk.Label(panneau, text=valeur, bg="#0A1416",
                             fg=self._couleur, anchor="w", padx=12, pady=4,
                             font=self._fonte, cursor=CURSEUR_MAIN)
            ligne.pack(fill="x")
            ligne.bind("<Enter>", lambda e, l=ligne: l.configure(bg="#14313A"))
            ligne.bind("<Leave>", lambda e, l=ligne: l.configure(bg="#0A1416"))
            ligne.bind("<Button-1>", lambda e, v=valeur: self._prendre(v))
        panneau.place(x=self.winfo_x(),
                      y=self.winfo_y() + self.winfo_height() + 2)
        self._panneau = panneau
        # Pas de grab : le panneau se referme au premier clic ailleurs, et ce
        # clic fait ce qu'il a à faire — comme un menu normal. Le grab, lui,
        # obligeait à choisir une voix avant de pouvoir toucher à autre chose.
        panneau.bind("<Button-1>", self._hors_panneau)
        return "break"

    def _hors_panneau(self, _evenement=None):
        self.fermer()
        return "break"

    def _prendre(self, valeur):
        self.fermer()
        self.set(valeur)
        if self._commande:
            self._commande()
        return "break"


# ------------------------------------------------------------------
# Le choix de la langue — la fenêtre de la maquette
# ------------------------------------------------------------------
class FenetreLanguesV2(tk.Toplevel):
    """Les quinze langues, en grille, comme dans la maquette.

    Chaque cellule montre le nom natif et la voix officielle, avec son
    étoile ; la langue courante est encadrée. Un clic choisit et referme.
    """

    FOND = "#0A1416"
    BORD = "#4C6469"
    CELLULE = "#0D1A1C"
    TRAIT = "#1B3336"
    SURVOL = "#14313A"
    ACCENT = "#0FBBD0"
    TEXTE = "#E9F4F6"
    GRIS = "#7C959A"
    LARGEUR = 680
    HAUTEUR = 540

    def __init__(self, parent, code_courant, choisie):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=self.FOND)
        self._choisie = choisie
        # La fenêtre principale peut être réduite (648 px sur un portable) :
        # cette fenêtre-ci suit la même échelle, sinon elle est plus large que
        # l'application qui l'ouvre. 820 est la taille de référence du dessin.
        facteur = parent._format / 820
        largeur = max(420, round(self.LARGEUR * facteur))
        hauteur = max(340, round(self.HAUTEUR * facteur))

        def police(taille):
            return (FONT_MAIN, max(8, round(taille * facteur)))

        corps = tk.Frame(self, bg=self.FOND, highlightbackground=self.BORD,
                         highlightthickness=1)
        corps.pack(fill="both", expand=True)

        haut = tk.Frame(corps, bg=self.FOND, height=max(34, round(50 * facteur)))
        haut.pack(fill="x")
        haut.pack_propagate(False)
        tk.Label(haut, text=t("titre_langues").upper(), bg=self.FOND,
                 fg=self.ACCENT, font=police(16)).pack(side="left",
                                                           padx=18)
        croix = tk.Label(haut, text="×", bg=self.FOND, fg=self.GRIS,
                         font=police(22), cursor=CURSEUR_MAIN)
        croix.pack(side="right", padx=16)
        croix.bind("<Button-1>", lambda e: self.fermer())
        tk.Frame(corps, bg=self.TRAIT, height=1).pack(fill="x", padx=12)

        contenu = tk.Frame(corps, bg=self.FOND)
        contenu.pack(fill="both", expand=True, padx=16, pady=14)
        for colonne in range(3):
            contenu.grid_columnconfigure(colonne, weight=1, uniform="langue")
        for ligne in range(5):
            contenu.grid_rowconfigure(ligne, weight=1)

        self._cellules = []
        self._survollee = None
        for i, langue in enumerate(_LANGUES_TABLE):
            ici = langue.code == code_courant
            bord = self.ACCENT if ici else self.TRAIT
            cellule = tk.Frame(
                contenu, bg=self.CELLULE, cursor=CURSEUR_MAIN,
                highlightthickness=2, highlightbackground=bord)
            cellule.grid(row=i // 3, column=i % 3, sticky="nsew",
                         padx=3, pady=3)
            titre = tk.Label(cellule, text=langue.nom, bg=self.CELLULE,
                             fg=self.ACCENT if ici else self.TEXTE,
                             font=police(17), anchor="w")
            titre.pack(fill="x", padx=11, pady=(8, 0))
            # La voix officielle, avec son étoile : le dossier SD n'a rien à
            # faire ici, il n'apprend rien à celui qui choisit une langue.
            detail = tk.Label(cellule, text=f"{langue.voix_nom}  ★",
                              bg=self.CELLULE, fg=self.GRIS,
                              font=police(13), anchor="w")
            detail.pack(fill="x", padx=11, pady=(0, 8))
            self._cellules.append((cellule, titre, detail, bord))
            for morceau in (cellule, titre, detail):
                morceau.bind("<Button-1>",
                             lambda e, c=langue.code: self._prendre(c))

        x = parent.winfo_rootx() + (parent.winfo_width() - largeur) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - hauteur) // 2
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        self.transient(parent)
        self.lift()
        self.bind("<Escape>", lambda e: self.fermer())
        self.after(50, self._prendre_focus)
        self.after(150, self._veiller_survol)

    def _veiller_survol(self):
        """Le survol, vérifié à intervalle régulier.

        Sur macOS, les événements d'entrée et de sortie de Tk se perdent
        parfois dans une fenêtre sans cadre : la maquette a le même garde-fou
        pour ses boutons.
        """
        try:
            if not self.winfo_exists():
                return
            x, y = self.winfo_pointerxy()
            self._montrer_survol(self._indice_sous(x, y))
        except tk.TclError:
            return
        self.after(150, self._veiller_survol)

    def _indice_sous(self, x, y):
        for i, (cellule, _titre, _detail, _bord) in enumerate(self._cellules):
            gx, gy = cellule.winfo_rootx(), cellule.winfo_rooty()
            if (gx <= x < gx + cellule.winfo_width()
                    and gy <= y < gy + cellule.winfo_height()):
                return i
        return None

    def _montrer_survol(self, indice):
        if indice == self._survollee:
            return
        self._survollee = indice
        self._peindre()

    def _peindre(self):
        """Couleurs des cellules : le survol, puis la langue courante.

        Il n'y a plus de liseré blanc : il marquait la cellule sous le
        clavier, et le parcours au clavier a été retiré le 4 novembre au
        soir. Il restait affiché en permanence sur la langue courante, même
        quand on survolait une autre cellule. La langue courante se
        distingue par son cadre cyan, posé à la création.
        """
        for i, (cellule, titre, detail, bord) in enumerate(self._cellules):
            morceaux = (cellule, titre, detail)
            if i == self._survollee:
                self._colorer(morceaux, self.SURVOL, self.ACCENT)
                titre.configure(fg=self.TEXTE)
            else:
                self._colorer(morceaux, self.CELLULE, bord)
                titre.configure(fg=self.ACCENT if bord == self.ACCENT
                                else self.TEXTE)

    # -- le clavier ---------------------------------------------------
    @staticmethod
    def _colorer(morceaux, couleur, bord):
        cellule, titre, detail = morceaux
        for morceau in morceaux:
            morceau.configure(bg=couleur)
        cellule.configure(highlightbackground=bord)

    def _prendre_focus(self):
        """Prend le clavier, pour qu'Échap ferme la fenêtre.

        Pas de grab : un clic dans l'application referme la fenêtre et fait
        ce qu'il a à faire, comme un menu. Une fenêtre sans cadre, elle, ne
        prend pas le clavier toute seule ; sans lui, Échap ne la fermerait
        pas.
        """
        self.focus_force()

    def fermer(self, reprendre_focus=True):
        """Ferme la fenêtre sans laisser l'application « collée » à la souris.

        Détruire une fenêtre depuis son propre clic peut laisser Tk avec un
        appui encore actif : l'application suivait alors la souris jusqu'au
        clic suivant. On remet l'état de déplacement à zéro et on détruit au
        repos, puis on rend le clavier à l'application — sauf quand on ferme
        parce qu'on est passé dans une autre application (`reprendre_focus`
        à Faux) : on ne va pas lui reprendre le clavier.
        """
        parent = self.master
        try:
            parent._deplacement = None
        except AttributeError:
            pass

        def _finir():
            try:
                self.destroy()
            except tk.TclError:
                pass
            relacher_souris()
            if not reprendre_focus:
                return
            try:
                parent.focus_force()
            except tk.TclError:
                pass

        parent.after_idle(_finir)

    def _prendre(self, code):
        self._choisie(code)
        self.fermer()


# ------------------------------------------------------------------
# Application
# ------------------------------------------------------------------
class VoxPackApp(ctk.CTk):
    def __init__(self):
        super().__init__()


        choisir_police()
        # Avant de créer le moindre élément : l'interface s'adapte à la place
        # disponible (voir regler_echelle).
        regler_echelle(self.winfo_screenheight())

        self.title("Vox-Pack")
        # La fenêtre s'ouvre à sa taille idéale, mais se réduit si l'écran est
        # plus petit : sur un portable 1280 x 800, une fenêtre de 820 px de
        # haut mettrait le bouton « Let's Go » sous le bord de l'écran.
        # Marge réservée à la barre de titre et à celle du système. macOS en
        # réclame une centaine de pixels ; Windows se contente de soixante, et
        # cette différence vaut deux lignes visibles — d'autant que sur un
        # écran à 150 % de mise à l'échelle, Windows n'annonce que 720 pixels
        # de haut pour un écran 1080.
        largeur, hauteur, self.largeur_logo = geometrie_fenetre(
            self.winfo_screenwidth(), self.winfo_screenheight())
        # On centre la fenêtre sur l'écran. Le décalage vers le haut tient
        # compte de la barre de menus de macOS, qui mange une trentaine de
        # pixels : sans lui, la fenêtre paraît trop basse.
        ecran_l = self.winfo_screenwidth()
        ecran_h = self.winfo_screenheight()
        x = max((ecran_l - largeur) // 2, 0)
        # On garde le bas de la fenêtre à sa place : les 18 px ajoutés
        # servent uniquement au lien Ko-fi sous la signature.
        y = max((ecran_h - hauteur) // 2 - 15 - 9, 0)
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        self.minsize(min(LARGEUR_FENETRE, largeur), min(620, hauteur))
        self.resizable(True, True)

        # Fermeture : le bouton rouge, le menu Quitter et Cmd+Q passent tous
        # par _fermer, sinon la fenêtre de soutien apparaîtrait au hasard.
        self.protocol("WM_DELETE_WINDOW", self._fermer)
        if sys.platform == "darwin":
            try:
                self.createcommand("::tk::mac::Quit", self._fermer)
            except Exception:
                pass
        self.configure(fg_color=BG_MAIN)

        self.output_dir = None
        self.lignes = []
        # Vrai tant qu'une génération tourne (liste ou sons système) : le menu
        # permet de lancer les sons système même quand « Let's Go » est
        # désactivé, deux générations ne doivent pas se mélanger.
        self._genere = False
        # Drapeau d'arrêt de la génération des sons système : None quand rien
        # ne tourne (voir creer_sons_systeme).
        self._sons_stop = None
        self._logo_image = None
        self._soutien = None
        # Alertes ouvertes, de la plus ancienne à la plus récente : Échap
        # referme la dernière (voir _fermer_derniere_alerte).
        self._alertes = []
        self._reglages = lire_reglages()
        # Écriture différée des réglages : un curseur qui glisse ne doit pas
        # écrire le fichier à chaque pixel (voir _reglages_bientot).
        self._reglages_attente = None
        # Effet robot mémorisé : 0 = aucun, 1 à 3 = Robot, 4 = HAL 9000.
        try:
            self._robot = int(self._reglages.get("robot", 0) or 0)
        except (TypeError, ValueError):
            self._robot = 0
        if self._robot not in ROBOTS:
            self._robot = 0
        # Les deux réglages ajoutés à la 1.5.1 : le niveau du son et l'allure.
        # Ils vivent dans les réglages, comme la voix et le robot.
        try:
            self._niveau = int(self._reglages.get("niveau", 0) or 0)
        except (TypeError, ValueError):
            self._niveau = 0
        self._niveau = max(-6, min(6, self._niveau))
        try:
            self._allure = int(self._reglages.get("allure", 0) or 0)
        except (TypeError, ValueError):
            self._allure = 0
        # Le curseur va de -100 à +100 : on garde la même borne en relecture,
        # sinon une allure réglée à 80 % revient à 50 % au redémarrage.
        self._allure = max(-100, min(100, self._allure))
        self._maj_version = None
        self._erreur_sauvegarde = False
        # Fichiers dont la copie de secours (.bak) a déjà été faite pendant
        # cette session (voir _ecrire_csv).
        self._bak_faits = set()
        # Dernière ligne cochée à la souris : sert de point de départ quand on
        # étend la sélection avec la touche Majuscule.
        self._ancre_selection = None
        # UNE seule langue : celle de l'interface. Elle commande les textes,
        # les voix ET la liste de phrases. Au premier lancement c'est celle du
        # système ; ensuite, celle que l'utilisateur a choisie dans le menu.
        # Elle doit être fixée AVANT de créer les widgets, puisqu'ils sont
        # construits avec t().
        if "langue_ui" not in self._reglages:
            # Premier lancement : on retient la langue devinée, pour que le
            # choix soit stable même si le système change de langue ensuite.
            self._reglages["langue_ui"] = langue_du_systeme()
            ecrire_reglages(self._reglages)
        definir_langue_ui(self._reglages["langue_ui"])
        # Les variables Tk (cases à cocher) sont gardées ici jusqu'à la
        # fermeture. Abandonnées au ramasse-miettes, l'une d'elles pouvait
        # être détruite depuis le fil réseau — et Tk supporte mal d'être
        # appelé ailleurs que dans le fil principal. C'est le
        # « Variable.__del__ … main thread is not in main loop » vu sur le PC
        # le 3 novembre, juste avant qu'une aide ne s'ouvre vide.
        self._variables = []
        # Variable des cases à cocher du menu Langue (une seule case cochée).
        self._var_langue_ui = ctk.StringVar(value=LANGUE_UI)
        self._variables.append(self._var_langue_ui)


        # ----- L'écran de la maquette (voir docs/v2-passation.md, §8) -----
        self._construire_ecran_v2()

        # ----- Chargement -----
        reprendre_ancienne_liste()
        self.charger_liste()
        # Les titres NOM et PHRASE se calent sur les champs une fois posés.
        self.after(200, self._aligner_entetes_v2)

        # On vérifie en arrière-plan que les voix proposées existent toujours
        # chez Microsoft (décalé : la fenêtre s'affiche d'abord).
        self.after(600, self._verifier_voix)
        # Vérification des mises à jour, décalée : elle ne doit ni bloquer ni
        # retarder l'affichage. Silencieuse si le réseau manque.
        self.after(2500, self._verifier_maj)

        self._poser_icone()
        self._construire_menu()
        # Habillage v2 : la fenêtre de la maquette (sans barre de titre),
        # posée sur la 1.5.1 intacte. Voir docs/v2-passation.md, §7 et §8.
        self._habiller_fenetre()

    # ------------------------------------------------------------------
    # Menu : exporter / importer une liste, et langue de l'interface
    # ------------------------------------------------------------------
    @property
    def langue(self):
        """La langue de travail : une seule, celle de l'interface.

        Tout le code qui lit self.langue (voix, listes, libellés) suit donc
        l'interface, sans avoir à être réécrit.
        """
        return LANGUE_UI

    def _poser_icone(self):
        """Donne son icône à la fenêtre.

        Sans cela, Windows affiche l'icône de Tk dans la barre des tâches,
        même quand l'exécutable a la bonne icône. Sur macOS, l'icône vient de
        l'application elle-même : cet appel n'y change rien.
        """
        try:
            if sys.platform.startswith("win"):
                ico = trouver_ressource("icon.ico")
                if os.path.exists(ico):
                    self.iconbitmap(ico)
                    return
            from tkinter import PhotoImage

            png = trouver_ressource("icon.png")
            if os.path.exists(png):
                # On garde une référence : sans elle, Tk oublie l'image.
                self._icone_fenetre = PhotoImage(file=png)
                self.iconphoto(True, self._icone_fenetre)
        except Exception:
            pass  # une icône, ce n'est pas vital

    def _construire_menu(self):
        """Menu « Fichier ».

        Sur macOS, il vit dans la barre de menus du système : c'est là que les
        Mac l'attendent, et il n'occupe aucune place dans la fenêtre.

        Sur Windows, une barre de menus dessinée par Tk prend de la hauteur et
        reste blanche quoi qu'on fasse : on l'ouvre donc depuis un petit
        bouton, comme le « ? ». Le menu déroulant, lui, prend nos couleurs.

        Le menu est reconstruit à chaque changement de langue : Tk ne sait pas
        traduire un menu déjà posé.
        """
        style = {}
        if not sys.platform == "darwin":
            # La police par défaut d'un menu Tk est minuscule sur Windows :
            # sans cela, les entrées sont illisibles.
            style = dict(background=BG_MAIN, foreground=TEXT_WHITE,
                         activebackground=CYAN, activeforeground=BG_MAIN,
                         borderwidth=0, relief="flat",
                         font=(FONT_MAIN, TYPO_MENU))
        barre = Menu(self, **style)
        fichier = Menu(barre, tearoff=0, **style)

        # La langue en premier : c'est le réglage le plus important, puisque
        # c'est elle qui commande les textes, les voix ET la liste.
        langue = Menu(fichier, tearoff=0, **style)
        for code in LANGUES:
            langue.add_radiobutton(
                label=t("langue_" + code),
                value=code, variable=self._var_langue_ui,
                command=lambda c=code: self.changer_langue_ui(c),
            )
        fichier.add_cascade(label=t("menu_langue"), menu=langue)
        fichier.add_separator()
        fichier.add_command(label=t("menu_exporter"),
                            command=self.exporter_liste)
        fichier.add_command(label=t("menu_importer"),
                            command=self.importer_liste)
        fichier.add_command(label=t("menu_defaut"),
                            command=self.charger_liste_defaut)
        fichier.add_command(label=t("menu_sons_systeme"),
                            command=self.creer_sons_systeme)
        fichier.add_separator()
        fichier.add_command(label=t("menu_quitter"), command=self._fermer)
        barre.add_cascade(label=t("menu_fichier"), menu=fichier)
        self._menu_fichier = fichier
        if sys.platform == "darwin":
            self.configure(menu=barre)
        else:
            # Pas de barre dans la fenêtre : le menu s'ouvre à la demande.
            self.configure(menu="")

    def changer_langue_ui(self, code):
        """Change la langue de travail : textes, voix, liste de phrases, menu.

        C'est le SEUL endroit qui change de langue. L'application n'en connaît
        qu'une : celle de l'interface. Un utilisateur anglophone a donc une
        interface anglaise ET des voix anglaises ET la liste anglaise — jamais
        un mélange.
        """
        if code not in TEXTES or code == LANGUE_UI:
            return
        # On range d'abord ce qui appartient à la langue que l'on quitte :
        # la voix choisie et la liste de phrases.
        self._memoriser_voix()
        self._ecrire_csv()
        # Puis on change de langue, et on remet tout en place.
        definir_langue_ui(code)
        self._reglages["langue_ui"] = code
        ecrire_reglages(self._reglages)
        self._appliquer_langue()      # textes, menu, boutons, liste des voix
        self.charger_liste()          # la liste de phrases de cette langue
        self._dire(t("etat_langue_voix", langue=t("langue_" + code),
                     n=len(VOIX.get(code, ()))))

    def _appliquer_langue(self):
        """Redonne leur texte à tous les éléments déjà affichés.

        Sans cela, changer de langue obligerait à fermer et rouvrir
        l'application : les widgets gardent le texte de leur création.
        """
        self._construire_menu()
        self._var_langue_ui.set(LANGUE_UI)
        champ = getattr(self, "_champ_langue", None)
        if champ is not None and champ.winfo_exists():
            champ.configure(text=t("langue_" + LANGUE_UI))
        # Les deux titres fixes du panneau : ils étaient restés en français
        # dans les captures anglaises et allemandes de la v2.
        for nom, cle in (("_titre_langue", "langue"),
                         ("_titre_voix", "voix")):
            titre = getattr(self, nom, None)
            if titre is not None:
                titre.itemconfigure(titre._item, text=t(cle).upper())
        if hasattr(self, "_titre_niveau"):
            self._maj_titres_v2()
        self.btn_ajouter.configure(text=t("ajouter"))
        self.btn_supprimer.configure(text=t("supprimer"))
        # Le bouton d'aperçu peut être en train de lire : on ne remplace pas
        # « Arrêter » par « Écouter » sous les doigts de l'utilisateur.
        if self._lecture is None:
            self.btn_apercu.dire(t("ecouter"), arret=False)
        else:
            self.btn_apercu.dire(t("arreter"), arret=True)
        # Pendant la création des sons système, ce bouton sert d'« Arrêter » :
        # un changement de langue ne doit pas le rebaptiser « Let's Go ».
        en_arret = self._sons_stop is not None
        self.btn_letsgo.dire(
            t("arreter") if en_arret else t("lets_go"), arret=en_arret)
        self._maj_robot()
        self.lbl_col_nom.configure(text=t("nom").upper())
        self.lbl_col_phrase.configure(text=t("phrase").upper())
        # Les libellés des voix changent aussi (« Femme » devient « Female »),
        # et donc la largeur du menu — au champ du panneau, pas à l'ancienne.
        self.combo_voice.configure(width=self._pv(230))
        self._remplir_voix()
        # Les avertissements des lignes (« 8 caractères (max 8) »…)
        self._verifier_noms()
        self._dire("")

    def exporter_liste(self):
        """Écrit la liste actuelle dans un fichier choisi (nom,phrase)."""
        chemin = filedialog.asksaveasfilename(
            parent=self, title=t("titre_export"),
            defaultextension=".csv", initialfile=t("nom_export"),
            filetypes=[(t("type_csv"), "*.csv"), (t("type_tous"), "*.*")],
        )
        if not chemin:
            return
        try:
            with open(chemin, "w", encoding="utf-8", newline="") as f:
                ecrivain = csv.writer(f)
                # Un en-tête lisible : Excel s'y retrouve, et l'import sait
                # le reconnaître pour ne pas le prendre pour une phrase.
                ecrivain.writerow([t("entete_nom"), t("entete_phrase")])
                for ligne in self.lignes:
                    ecrivain.writerow([ligne["nom"].strip(),
                                       ligne["texte"].strip()])
        except Exception as e:
            self._message(t("msg_export_echec", err=e), icone="erreur")
            return
        nombre = len(self.lignes)
        self._message(t("msg_export_ok", n=nombre, chemin=chemin,
                        s="s" if nombre > 1 else ""), icone="succes")

    def importer_liste(self):
        """Remplace la liste par celle d'un fichier choisi."""
        chemin = filedialog.askopenfilename(
            parent=self, title=t("titre_import"),
            filetypes=[(t("type_csv"), "*.csv"), (t("type_txt"), "*.txt"),
                       (t("type_tous"), "*.*")],
        )
        if not chemin:
            return
        try:
            with open(chemin, encoding="utf-8-sig") as f:
                brut = lire_lignes_csv(f)
        except Exception as e:
            self._message(t("msg_import_illisible", err=e), icone="erreur")
            return

        # Un en-tête est ignoré : c'est ce que produit l'export, dans
        # n'importe laquelle des quinze langues (« nom », « nombre »,
        # « název », « 名前 »…).
        if brut and est_entete(brut[0]):
            brut = brut[1:]
        if not brut:
            self._message(t("msg_import_vide"), icone="attention")
            return

        paires = []
        for morceaux in brut:
            nom = morceaux[0].strip()
            # Une seule colonne : on reprend le nom comme phrase de départ,
            # à corriger ensuite dans la liste.
            phrase = morceaux[1].strip() if len(morceaux) > 1 else nom
            paires.append((nom, phrase))

        en_place = len(self.lignes)
        self._message(
            t("msg_import_confirmer", avant=en_place,
              s1="s" if en_place > 1 else "",
              apres=len(paires), s2="s" if len(paires) > 1 else ""),
            icone="attention",
            boutons=[(t("msg_import_oui"),
                      lambda: self._appliquer_import(paires)),
                     (t("annuler"), None)])

    def _appliquer_import(self, paires):
        """Vide la liste et la remplace par les lignes importées."""
        if self._edition is not None:
            self._valider_edition()
        self.lignes.clear()
        for nom, phrase in paires:
            self._ajouter_ligne_ui(nom, phrase)
        self._ancre_selection = None
        self._verifier_noms(redessiner=False)
        self._dessiner_liste()
        self._on_change()
        self._maj_total_liste()
        self.after_idle(lambda: self._toile.yview_moveto(0.0))
        self._message(t("msg_import_ok", n=len(paires),
                        s="s" if len(paires) > 1 else ""), icone="succes")

    def charger_liste_defaut(self):
        """Remet la liste livrée avec l'application, dans la langue des voix.

        Nécessaire parce que la liste de l'utilisateur n'est JAMAIS remplacée
        par un simple changement de langue : ce serait perdre son travail sans
        prévenir. C'est donc une action explicite, avec confirmation.
        """
        defaut = LISTE_PAR_DEFAUT.get(self.langue, [])
        self._message(
            t("question_defaut", n=len(defaut),
              langue=t("adjectif_" + self.langue)),
            icone="attention",
            boutons=[(t("oui_remplacer"), lambda: self._appliquer_import(list(defaut))),
                     (t("annuler"), None)])

    # ------------------------------------------------------------------
    # Style bouton commun
    # ------------------------------------------------------------------
    def _btn(self, parent, text, command, small=False, largeur=None,
             hauteur=None, typo=None):
        if small:
            w, h, f = 80, 30, TYPO_PETIT_BOUTON
        else:
            w, h, f = BTN_W, BTN_H, TYPO_BOUTON
        if largeur:
            w = largeur
        if hauteur:
            h = hauteur
        if typo:
            f = typo
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

    def _verifier_maj(self):
        """Cherche la dernière version publiée sans bloquer la fenêtre."""
        resultat = queue.Queue()

        def travail():
            try:
                resultat.put(derniere_version_publiee())
            except Exception:
                resultat.put(None)

        threading.Thread(target=travail, daemon=True).start()
        self._attendre_maj(resultat)

    def _attendre_maj(self, resultat):
        """Vient chercher le résultat dès qu'il est prêt (sans bloquer)."""
        try:
            infos = resultat.get_nowait()
        except queue.Empty:
            self.after(150, lambda: self._attendre_maj(resultat))
            return
        if infos and version_plus_recente(infos["tag"], version_de_reference()):
            self._afficher_maj(infos)

    def _afficher_maj(self, infos):
        """Petite fenêtre au démarrage : une version plus récente existe."""
        version = str(infos.get("tag", "")).lstrip("vV")
        self._maj_version = version
        self._maj_infos = infos
        if getattr(self, "_popup_maj", None) is not None \
                and self._popup_maj.winfo_exists():
            self._popup_maj.lift()
            return

        popup = ctk.CTkToplevel(self)
        self._popup_maj = popup
        popup.title(t("maj_titre"))
        popup.configure(fg_color=BG_MAIN)
        popup.resizable(False, False)
        popup.transient(self)
        popup.protocol("WM_DELETE_WINDOW", popup.destroy)
        # Échap ferme la fenêtre, comme partout ailleurs (équivaut à « Plus tard »).
        popup.bind("<Escape>", lambda e: popup.destroy())

        cadre = ctk.CTkFrame(popup, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=MARGE_MAJ, pady=20)
        ctk.CTkLabel(
            cadre, text=t("maj_titre"), font=(FONT_MAIN, 20),
            text_color=CYAN, anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            cadre, text=t("maj_texte", version=version,
                          actuelle=version_de_reference()),
            font=(FONT_MAIN, 14), text_color=TEXT_WHITE,
            justify="left", anchor="w", wraplength=LARGEUR_TEXTE_MAJ,
        ).pack(fill="x", pady=(10, 0))
        statut = ctk.CTkLabel(
            cadre, text="", font=(FONT_MAIN, 12), text_color=TEXT_GREY,
            justify="left", anchor="w", wraplength=LARGEUR_TEXTE_MAJ,
        )
        statut.pack(fill="x", pady=(8, 0))

        boutons = ctk.CTkFrame(cadre, fg_color="transparent")
        boutons.pack(side="bottom", fill="x", pady=(14, 0))
        btn_telecharger = ctk.CTkButton(
            boutons, text=t("maj_telecharger"), font=(FONT_MAIN, 14),
            height=34, corner_radius=17, fg_color=CYAN,
            hover_color=CYAN_CLAIR, text_color=BG_MAIN,
        )
        btn_telecharger.pack(side="right")
        btn_plus_tard = ctk.CTkButton(
            boutons, text=t("maj_plus_tard"), font=(FONT_MAIN, 14),
            height=34, corner_radius=17, fg_color="transparent",
            border_color=CYAN, border_width=1, text_color=CYAN,
            hover_color=CYAN_HOVER, command=popup.destroy,
        )
        btn_plus_tard.pack(side="right", padx=(0, 10))

        def telecharger():
            asset = choisir_asset(infos.get("assets", []))
            if asset is None:
                self._ouvrir_lien(URL_RELEASES)
                popup.destroy()
                return
            btn_telecharger.configure(
                state="disabled", text=t("maj_telechargement"))
            btn_plus_tard.configure(state="disabled")
            statut.configure(text=t("maj_telechargement"))
            self._ajuster_maj(popup)
            self._telecharger_asset(popup, asset, version, statut,
                                    btn_telecharger, btn_plus_tard)

        # Taille demandée par le contenu, pas une grande fenêtre vide.
        self._ajuster_maj(popup)

        btn_telecharger.configure(command=telecharger)
        # Pas de grab_set : la popup ne bloque pas la fenêtre principale, donc
        # macOS n'affiche plus le curseur « interdit » sur les champs.
        popup.after(150, popup.focus_force)
        popup.after(200, popup.lift)

    def _ajuster_maj(self, popup):
        """Redimensionne la fenêtre de mise à jour sur son contenu, et la recentre.

        Appelée à chaque changement de texte : après le téléchargement, la
        fenêtre affiche le dossier et les boutons changent de libellé. Sans ce
        recalcul, le texte sortait par la droite et les boutons passaient sous
        la fenêtre (vu par Richard le 22 octobre).
        """
        try:
            if not popup.winfo_exists():
                return
        except Exception:
            return
        popup.update_idletasks()
        largeur = max(LARGEUR_MAJ, popup.winfo_reqwidth())
        hauteur = popup.winfo_reqheight()
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - largeur) // 2
        y = self.winfo_rooty() + (self.winfo_height() - hauteur) // 2
        x = max(20, min(x, self.winfo_screenwidth() - largeur - 20))
        y = max(20, min(y, self.winfo_screenheight() - hauteur - 60))
        popup.geometry(f"{largeur}x{hauteur}+{x}+{y}")

    def _telecharger_asset(self, popup, asset, version, statut,
                           btn_telecharger, btn_plus_tard):
        """Télécharge le fichier de la version, puis ouvre son dossier."""
        resultat = queue.Queue()

        def travail():
            try:
                dossier = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(dossier, exist_ok=True)
                extension = os.path.splitext(asset["name"])[1] or ""
                chemin = os.path.join(
                    dossier, f"Vox-Pack-{version}{extension}")
                contexte = ssl.create_default_context(cafile=certifi.where())
                with urllib.request.urlopen(
                        asset["url"], timeout=60,
                        context=contexte) as reponse, \
                        open(chemin, "wb") as sortie:
                    shutil.copyfileobj(reponse, sortie)
                if sys.platform == "darwin" and extension.lower() == ".zip":
                    extrait = os.path.join(dossier, f"Vox-Pack-{version}")
                    os.makedirs(extrait, exist_ok=True)
                    subprocess.run(["ditto", "-x", "-k", chemin, extrait],
                                   check=True, capture_output=True)
                    chemin = extrait
                resultat.put(("ok", chemin))
            except Exception:
                resultat.put(("erreur", None))

        threading.Thread(target=travail, daemon=True).start()

        def suivi():
            try:
                if not popup.winfo_exists():
                    return
            except Exception:
                return
            try:
                etat, chemin = resultat.get_nowait()
            except queue.Empty:
                popup.after(150, suivi)
                return
            if etat == "ok":
                self._maj_prete(popup, chemin, statut, btn_telecharger,
                                btn_plus_tard)
            else:
                self._maj_echouee(popup, statut, btn_telecharger,
                                  btn_plus_tard)

        popup.after(150, suivi)

    def _maj_prete(self, popup, chemin, statut, btn_telecharger,
                   btn_plus_tard):
        try:
            if not popup.winfo_exists():
                return
        except Exception:
            return
        cle = ("maj_telecharge_mac" if sys.platform == "darwin"
               else "maj_telecharge_win")
        statut.configure(text=t(cle, chemin=chemin), text_color=TEXT_WHITE)
        btn_telecharger.configure(
            state="normal", text=t("maj_ouvrir_dossier"),
            command=lambda: self._reveler(chemin))
        btn_plus_tard.configure(
            state="normal", text=t("maj_fermer"),
            command=popup.destroy)
        # Le dossier affiché et les nouveaux libellés prennent plus de place.
        self._ajuster_maj(popup)

    def _maj_echouee(self, popup, statut, btn_telecharger, btn_plus_tard):
        try:
            if not popup.winfo_exists():
                return
        except Exception:
            return
        statut.configure(text=t("maj_echec"), text_color=DANGER)
        btn_telecharger.configure(
            state="normal", text=t("maj_page"),
            command=lambda: (self._ouvrir_lien(URL_RELEASES),
                             popup.destroy()))
        btn_plus_tard.configure(
            state="normal", text=t("maj_fermer"),
            command=popup.destroy)
        self._ajuster_maj(popup)

    def _reveler(self, chemin):
        """Ouvre le dossier du fichier téléchargé."""
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", chemin])
            elif sys.platform.startswith("win"):
                subprocess.Popen(["explorer", "/select,", chemin])
            else:
                webbrowser.open(f"file://{chemin}")
        except Exception:
            pass

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
    # Mini fenêtre de soutien (clic sur le logo Ko-fi)
    # ------------------------------------------------------------------
    def _fermer(self):
        """Fermeture demandée : un dernier mot, puis on quitte.

        Le bouton rouge de la fenêtre, Fichier > Quitter et Cmd+Q passent
        tous par ici. Si la fenêtre de soutien est déjà ouverte, inutile de
        la montrer une seconde fois : l'utilisateur vient de la voir.
        """
        if self._soutien is not None and self._soutien.winfo_exists():
            self._quitter()
            return
        if self._reglages.get("soutien_fermeture", True):
            self._ouvrir_soutien(fermeture=True)
            return
        self._quitter()

    def _quitter(self):
        """Quitte pour de bon, sans perdre la liste ni les réglages."""
        try:
            self._valider_edition()
        except Exception:
            pass
        try:
            self._ecrire_csv()
        except Exception:
            pass
        try:
            ecrire_reglages(self._reglages)
        except Exception:
            pass
        # On relâche les variables Tk ici, dans le fil principal.
        self._variables.clear()
        self.destroy()

    def _ouvrir_soutien(self, fermeture=False):
        """La petite fenêtre de soutien.

        Ouverte par le lien « Ko-fi » (fermeture=False), ou par la fermeture
        de l'application (fermeture=True) : dans ce cas elle propose en plus de
        ne plus jamais reposer la question.
        """
        if self._soutien is not None and self._soutien.winfo_exists():
            self._soutien.lift()
            self._soutien.focus_force()
            return

        popup = ctk.CTkToplevel(self)
        self._soutien = popup
        popup.title(t("titre_soutien"))
        popup.resizable(False, False)
        popup.transient(self)
        popup.configure(fg_color=BG_MAIN)

        # Ce que fait « Une prochaine fois » : refermer, ou quitter si c'est la
        # fermeture de l'application qui a ouvert cette fenêtre. La case cochée
        # est retenue pour de bon dans les réglages.
        def fin(demander_encore=None):
            if fermeture:
                if demander_encore is None:
                    demander_encore = not bool(var.get()) if var else True
                self._reglages["soutien_fermeture"] = demander_encore
            try:
                popup.destroy()
            except Exception:
                pass
            if fermeture:
                self._quitter()

        popup.protocol("WM_DELETE_WINDOW", lambda: fin())
        popup.bind("<Escape>", lambda e: fin())

        largeur = LARGEUR_SOUTIEN
        ctk.CTkLabel(
            popup, text=t("soutien_question"),
            font=(FONT_MAIN, 16), text_color=TEXT_WHITE,
            wraplength=largeur - 50, justify="center",
        ).pack(padx=25, pady=(26, 6))

        # Le logo Ko-fi remplace l'émoji ☕, comme dans l'aide et le bas de
        # page : la taille d'un émoji dépend de la police du système.
        if getattr(self, "_image_kofi_fenetre", None) is None:
            try:
                self._image_kofi_fenetre = ctk.CTkImage(
                    light_image=Image.open(trouver_ressource("ko-fi.png")),
                    dark_image=Image.open(trouver_ressource("ko-fi.png")),
                    size=(30, 24))
            except Exception:
                self._image_kofi_fenetre = None
        cafe = ctk.CTkLabel(
            popup, text=t("soutien_cafe"),
            image=self._image_kofi_fenetre, compound="left",
            font=(FONT_MAIN, 16), text_color=LINK_COLOR,
        )
        cafe.pack()
        cafe.bind("<Button-1>", lambda e: self._ouvrir_lien(KO_FI_URL))

        # La case n'apparaît que sur la fermeture : c'est la porte de sortie de
        # ceux que la question agace.
        var = None
        if fermeture:
            var = ctk.BooleanVar(value=False)
            self._variables.append(var)
            ctk.CTkCheckBox(
                popup, text=t("soutien_ne_plus"), variable=var,
                font=(FONT_MAIN, 12), text_color=TEXT_GREY,
                fg_color=CYAN, hover_color=CYAN_DARK,
                border_color=CYAN_DARK, checkmark_color=BG_MAIN,
                corner_radius=4,
            ).pack(pady=(14, 0))

        boutons = ctk.CTkFrame(popup, fg_color="transparent")
        boutons.pack(pady=(20, 26))
        # Le « Oui » est nettement plus gros que l'autre : c'est le bouton
        # qu'on a envie de cliquer (léger avantage déloyal, assumé).
        oui = self._btn(
            boutons, t("soutien_oui"),
            lambda: (self._ouvrir_lien(KO_FI_URL), fin(False)),
            largeur=OUI_LARGEUR, hauteur=OUI_HAUTEUR, typo=OUI_TYPO,
        )
        oui.configure(fg_color="transparent", text_color=CYAN,
                      border_color=CYAN, corner_radius=OUI_HAUTEUR // 2,
                      hover_color=CYAN_DARK)
        oui.pack(side="left", padx=7)
        self._btn(boutons, t("soutien_plus_tard"), fin,
                  small=True, largeur=150).pack(side="left", padx=7)

        popup.update_idletasks()
        # La largeur s'adapte au contenu : si on agrandit le bouton « Oui »,
        # la fenêtre s'élargit toute seule au lieu de rogner les boutons.
        largeur = max(LARGEUR_SOUTIEN, popup.winfo_reqwidth())
        hauteur = popup.winfo_reqheight()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - largeur) // 2
        y = self.winfo_y() + (self.winfo_height() - hauteur) // 2
        popup.geometry(f"{largeur}x{hauteur}+{max(x, 0)}+{max(y, 0)}")
        popup.lift()

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
        """Affiche un message dans la présentation de l'écran v2.

        Sans barre de titre, fond sombre, cadre gris, boutons à coin coupé :
        une alerte doit ressembler au reste de l'application, pas à une
        fenêtre du système.
        """
        symbole, couleur = self.ICONES.get(icone, self.ICONES["info"])
        boutons = boutons or [(t("compris"), None)]
        # Règle de la 1.5 : le nom propre ne s'étale pas dans les chemins
        # affichés — le dossier personnel devient « ~ ».
        personnel = os.path.expanduser("~")
        texte = str(texte).replace(personnel + os.sep, "~" + os.sep)
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg="#0A1416")

        corps = tk.Frame(popup, bg="#0A1416",
                         highlightbackground="#4C6469",
                         highlightthickness=1)
        corps.pack(fill="both", expand=True)

        haut = tk.Frame(corps, bg="#0A1416", height=38)
        haut.pack(fill="x")
        haut.pack_propagate(False)
        tk.Label(haut, text="VOX-PACK", bg="#0A1416", fg="#0FBBD0",
                 font=(FONT_MAIN, 12)).pack(side="left", padx=14)
        croix = tk.Label(haut, text="×", bg="#0A1416", fg="#7C959A",
                         font=(FONT_MAIN, 18), cursor=CURSEUR_MAIN)
        croix.pack(side="right", padx=12)
        croix.bind("<Button-1>", lambda e: self._fermer_alerte(popup))
        tk.Frame(corps, bg="#1B3336", height=1).pack(fill="x")

        # La largeur suit le texte et le nombre de boutons, sans dépasser
        # celle que l'appelant a demandée.
        police = tkfont.Font(family=FONT_MAIN, size=15)
        besoin = max((police.measure(ligne) for ligne in texte.split("\n")),
                     default=0) + 72
        rangee_largeur = len(boutons) * 150 + (len(boutons) - 1) * 12
        largeur = int(min(largeur, max(besoin, rangee_largeur + 44, 360)))

        pastille = tk.Canvas(corps, width=52, height=52, bg="#0A1416",
                             highlightthickness=0)
        pastille.create_oval(3, 3, 49, 49, outline=couleur, width=2)
        pastille.create_text(26, 26, text=symbole, fill=couleur,
                             font=(FONT_MAIN, 24, "bold"))
        pastille.pack(pady=(16, 0))

        tk.Label(corps, text=texte, bg="#0A1416", fg="#E9F4F6",
                 font=(FONT_MAIN, 15), wraplength=largeur - 60,
                 justify="center").pack(padx=22, pady=(10, 0))

        rangee = tk.Frame(corps, bg="#0A1416", width=rangee_largeur,
                          height=42)
        rangee.pack(pady=(18, 16))
        rangee.pack_propagate(False)
        for i, (libelle, action) in enumerate(boutons):
            def cliquer(a=action, p=popup):
                self._fermer_alerte(p)
                if a:
                    a()

            BoutonV2(rangee, libelle, i * 162, 0, 150, 42,
                     fond="#0A1416", contour=True, biseau=8,
                     fonte=(FONT_MAIN, 15), commande=cliquer)

        popup.update_idletasks()
        hauteur = popup.winfo_reqheight()
        x = self.winfo_rootx() + (self.winfo_width() - largeur) // 2
        y = self.winfo_rooty() + (self.winfo_height() - hauteur) // 2
        popup.geometry(f"{largeur}x{hauteur}+{max(x, 0)}+{max(y, 0)}")
        popup.transient(self)
        popup.lift()
        self._alertes.append(popup)
        _trace_echap("alerte ouverte")
        # L'application est parfois passée derrière pendant une longue
        # génération : l'alerte s'affiche alors sans que le clavier lui
        # revienne, et Échap reste sans effet. On repasse devant, mais
        # seulement si l'on n'y est plus (ne pas voler le clavier à
        # quelqu'un qui travaille dans une autre application pour une
        # alerte qu'il n'a pas demandée).
        if sys.platform == "darwin":
            try:
                from AppKit import NSApp
                if not NSApp.isActive():
                    NSApp.activateIgnoringOtherApps_(True)
                    # La fenêtre principale d'abord, l'alerte ensuite : sans
                    # cela, l'alerte peut rester derrière celle de l'autre
                    # application qui vient d'être quittée.
                    self.lift()
                    popup.lift()
            except Exception:
                pass
        # Le clavier RESTE à la fenêtre principale. C'est contre-intuitif,
        # mais c'est la seule façon qui marche : une fenêtre sans cadre ne
        # peut pas devenir « fenêtre active » sur macOS, et la lui demander
        # retire le clavier à la fenêtre principale. Plus aucune touche
        # n'arrive alors — Échap compris — jusqu'au clic suivant dans
        # l'application. C'est exactement ce que Richard a décrit le
        # 5 novembre : « il faut cliquer dans la fenêtre principale, et
        # après Échap fonctionne ».
        #
        # L'alerte n'a pas besoin du clavier : elle n'a que des boutons, et
        # c'est la fenêtre principale qui referme l'alerte la plus récente
        # (voir _echapper).
        popup.after(60, self._rendre_le_clavier)
        popup.bind("<Escape>", lambda e: (_trace_echap("ECHAP sur l'alerte"),
                                          self._fermer_alerte(popup)))
        popup.after(120, lambda: self._prendre_grab(popup))

    def _rendre_le_clavier(self):
        """Redonne le clavier à la fenêtre principale, une alerte ouverte.

        Le 5 novembre, la trace a montré le vrai problème : au moment où
        l'alerte s'ouvre, macOS n'a plus AUCUNE fenêtre active
        (`keyWindow = None`). L'application est active, mais aucune de ses
        fenêtres ne reçoit le clavier — et Échap part dans le vide jusqu'au
        clic suivant. `focus_force()` ne suffit pas : Tk le croit déjà
        focalisé et ne redemande rien à macOS.

        On redemande donc explicitement à macOS de rendre la fenêtre
        principale active, puis on remet l'alerte au-dessus d'elle.
        """
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        try:
            self.focus_force()
        except tk.TclError:
            pass
        if sys.platform == "darwin":
            try:
                from AppKit import NSApp
                if NSApp.keyWindow() is None:
                    self.lift()
                    for fenetre in NSApp.windows():
                        if (fenetre.isVisible()
                                and round(fenetre.frame().size.width)
                                == self._format):
                            fenetre.makeKeyWindow()
                            break
                    # La fenêtre principale vient de repasser devant :
                    # l'alerte doit rester au-dessus d'elle.
                    if self._alertes:
                        self._alertes[-1].lift()
            except Exception:
                pass
        _trace_echap("clavier rendu")

    def _fermer_derniere_alerte(self):
        """Referme l'alerte la plus récente, si elle est encore ouverte.

        C'est le chemin NORMAL d'Échap : le clavier reste à la fenêtre
        principale (voir _message), donc l'alerte ne reçoit pas la touche
        elle-même. Renvoie True si une alerte a été fermée.
        """
        while self._alertes:
            popup = self._alertes[-1]
            if popup.winfo_exists():
                self._fermer_alerte(popup)
                return True
            self._alertes.pop()
        return False

    @staticmethod
    def _prendre_grab(popup):
        try:
            popup.grab_set()
        except tk.TclError:
            pass

    def _fermer_alerte(self, popup):
        try:
            popup.grab_release()
        except tk.TclError:
            pass
        if popup in self._alertes:
            self._alertes.remove(popup)
        relacher_souris()

        def finir():
            try:
                popup.destroy()
            except tk.TclError:
                pass
            # La petite fenêtre avait le clavier : détruite, elle
            # l'emporterait avec elle. On le rend à l'application, sinon
            # plus aucune cellule ne s'ouvre au clavier après une alerte.
            try:
                self.focus_force()
            except tk.TclError:
                pass

        popup.after_idle(finir)

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

    def _choisir_dossier(self, titre, initialdir=None):
        """Demande un dossier d'arrivée.

        Sur macOS, Tk affiche un sélecteur de dossier dont le bouton est écrit
        « Choose » en dur, même quand le reste est traduit. On affiche donc le
        MÊME panneau que « Importer une liste » (NSOpenPanel), en feuille
        attachée à la fenêtre : bouton « Choisir », « Annuler », « Nouveau
        dossier » et barre latérale, tout dans la langue du Mac.

        Ailleurs (Windows), le sélecteur de Tk est déjà traduit par le système :
        on le garde.
        """
        if sys.platform != "darwin":
            return filedialog.askdirectory(parent=self, title=titre,
                                           initialdir=initialdir)

        try:
            from AppKit import NSOpenPanel, NSApp, NSURL
        except Exception:
            # PyObjC absent (vieux paquet, exécution depuis les sources) :
            # on retombe sur le sélecteur de Tk, quitte à afficher « Choose ».
            return filedialog.askdirectory(parent=self, title=titre,
                                           initialdir=initialdir)

        panneau = NSOpenPanel.openPanel()
        panneau.setCanChooseFiles_(False)
        panneau.setCanChooseDirectories_(True)
        panneau.setCanCreateDirectories_(True)
        panneau.setAllowsMultipleSelection_(False)
        panneau.setPrompt_(t("choisir"))
        panneau.setMessage_(titre)
        if initialdir and os.path.isdir(os.path.expanduser(initialdir)):
            panneau.setDirectoryURL_(NSURL.fileURLWithPath_(
                os.path.abspath(os.path.expanduser(initialdir))))

        # La fenêtre Tk est une NSWindow : la feuille s'y accroche comme pour
        # l'import d'une liste.
        self.lift()
        self.update_idletasks()
        fenetre = NSApp.keyWindow() or NSApp.mainWindow()
        if fenetre is None:
            # Cas rare (application non active) : panneau seul, plutôt que rien.
            return self._chemin_panneau(panneau, panneau.runModal())

        etat = {"fini": False, "chemin": ""}

        def termine(reponse):
            etat["chemin"] = self._chemin_panneau(panneau, reponse)
            etat["fini"] = True

        panneau.beginSheetModalForWindow_completionHandler_(fenetre, termine)
        # On fait tourner la boucle Tk pendant que la feuille est ouverte :
        # l'application reste vivante, et la feuille se ferme normalement.
        while not etat["fini"]:
            try:
                self.update()
            except Exception:
                return ""       # fenêtre en cours de fermeture
            time.sleep(0.02)
        return etat["chemin"]

    @staticmethod
    def _chemin_panneau(panneau, reponse):
        """Chemin choisi dans un NSOpenPanel (1 = OK, 0 = annulé)."""
        if reponse == 1:
            url = panneau.URL()
            if url is not None and url.path():
                return os.path.normpath(url.path())
        return ""

    # ------------------------------------------------------------------
    # Fenêtre d'aide
    # ------------------------------------------------------------------
    def _variante_robot(self):
        """Variante de l'effet selon la langue : « fr », « de » ou « en ».

        C'est elle qui choisit la voix de HAL 9000 et son réglage. HAL n'a
        pas encore de voix allemande de cinéma : Conrad fait l'affaire en
        attendant (décision de Richard, 25 octobre 2026).
        """
        if self._robot == 4:
            return self.langue if self.langue in VOIX_ROBOT else "en"
        try:
            voix = identifiant_voix(self.langue, self.combo_voice.get())
        except Exception:
            return "en"
        return ("fr" if voix.startswith("fr-")
                else "de" if voix.startswith("de-") else "en")

    def _robot_voice(self):
        """Voix imposée par HAL 9000 (None pour les autres presets)."""
        if self._robot != 4:
            return None
        return VOIX_ROBOT[self._variante_robot()]

    def _reglage_robot(self):
        """Réglage du preset, avec la variante de la langue si elle existe."""
        reglage = ROBOTS.get(self._robot)
        if not reglage:
            return None
        return reglage.get(self._variante_robot(), reglage)

    def _robot_pitch(self):
        """Hauteur à demander au service pour le preset choisi."""
        reglage = self._reglage_robot()
        return reglage.get("pitch") if reglage else None

    def _robot_rate(self):
        """Débit à demander au service pour le preset choisi."""
        reglage = self._reglage_robot()
        return reglage.get("rate") if reglage else None

    def _rate_effectif(self, voice_id):
        """Le débit demandé au service : celui de la voix, plus l'allure.

        Chaque langue a son débit officiel (l'anglais parle 10 % plus vite,
        le suédois 10 % plus lentement) et le robot a le sien. Le curseur
        ALLURE ajoute des points de pourcentage à ce débit de départ, sans
        jamais dépasser ce que le service accepte.
        """
        base = self._robot_rate() or reglage_voix(voice_id).get("rate", "+0%")
        allure = int(getattr(self, "_allure", 0) or 0)
        if not allure:
            return base
        try:
            pour_cent = int(str(base).strip().replace("%", ""))
        except (TypeError, ValueError):
            pour_cent = 0
        total = max(-100, min(100, pour_cent + allure))
        return f"{total:+d}%"

    def _appliquer_robot(self, chemin):
        """Applique l'effet robot au WAV, si une pastille est allumée."""
        if self._robot in ROBOTS:
            appliquer_effet_robot(chemin, self._robot, self._variante_robot())

    def _maj_libelle_robot(self):
        if self._robot == 4:
            self.lbl_robot.configure(text="HAL 9000", text_color=CYAN)
        elif self._robot:
            self.lbl_robot.configure(text=f"Robot {self._robot}",
                                     text_color=CYAN)
        else:
            self.lbl_robot.configure(text=t("voix_normale"),
                                     text_color=CYAN)

    def _peindre_robots(self):
        """Le robot choisi allume son voyant ; les autres restent éteints."""
        for numero, led in self._boutons_robot.items():
            if numero == self._robot:
                led.allumer()
            else:
                led.eteindre()

    def _maj_robot(self):
        self._peindre_robots()
        self._maj_libelle_robot()

    def _survol_robot(self, numero):
        """Allume la pastille survolée et affiche son nom au-dessus."""
        self._robot_survole = numero
        if numero is None:
            self._maj_libelle_robot()
        else:
            libelle = "HAL 9000" if numero == 4 else f"Robot {numero}"
            self.lbl_robot.configure(text=libelle, text_color=CYAN)
        self._peindre_robots()

    def _veiller_survol_robot(self):
        """Le survol des quatre carrés, vérifié par sondage.

        Comme ailleurs sur macOS, les <Enter>/<Leave> de Tk se perdent dans
        une fenêtre sans cadre : on interroge la position du pointeur.
        """
        try:
            if not self.winfo_exists():
                return
            x, y = self.winfo_pointerxy()
            trouve = None
            for numero, bouton in self._boutons_robot.items():
                gx, gy = bouton.winfo_rootx(), bouton.winfo_rooty()
                if (gx <= x < gx + bouton.winfo_width()
                        and gy <= y < gy + bouton.winfo_height()):
                    trouve = numero
                    break
            if trouve != self._robot_survole:
                self._robot_survole = trouve
                self._survol_robot(trouve)
        except tk.TclError:
            return
        self.after(150, self._veiller_survol_robot)

    def _choisir_robot(self, numero):
        """Allume un preset, ou l'éteint si c'est déjà le sien."""
        self._robot = 0 if self._robot == numero else numero
        self._reglages["robot"] = self._robot
        ecrire_reglages(self._reglages)
        self._maj_robot()

    def _ouvrir_aide(self):
        # L'aide au style de l'écran : sans barre de titre, fond sombre,
        # cadre gris, logo en tête et bouton Fermer à coin coupé.
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg="#0A1416")

        def fermer_aide(_evenement=None):
            """Ferme l'aide sans laisser la fenêtre principale « collée ».

            Détruire la fenêtre depuis son propre clic laisse Tk avec un
            appui encore actif : la fenêtre principale suivait ensuite la
            souris jusqu'au clic suivant. On remet l'état de déplacement à
            zéro, on rend le grab s'il y en a un, et on détruit au repos.
            """
            self._deplacement = None
            try:
                popup.grab_release()
            except tk.TclError:
                pass
            relacher_souris()
            popup.after_idle(lambda: (relacher_souris(), popup.destroy()))

        popup.bind("<Escape>", fermer_aide)
        popup.bind("<ButtonRelease-1>",
                   lambda e: setattr(self, "_deplacement", None))

        self.update_idletasks()
        # Elle ne doit jamais dépasser l'écran : sinon le bouton « Fermer »
        # passe sous la barre des tâches et devient inatteignable. 160 px
        # réservés pour la barre des tâches et le Dock.
        w_popup = min(620, self.winfo_screenwidth() - 80)
        h_popup = min(660, self.winfo_screenheight() - 160)
        x = self.winfo_x() + (self.winfo_width() - w_popup) // 2
        y = self.winfo_y() + (self.winfo_height() - h_popup) // 2
        popup.geometry(f"{w_popup}x{h_popup}+{max(x, 0)}+{max(y, 0)}")

        corps = tk.Frame(popup, bg="#0A1416",
                         highlightbackground="#4C6469",
                         highlightthickness=1)
        corps.pack(fill="both", expand=True)

        haut = tk.Frame(corps, bg="#0A1416", height=40)
        haut.pack(fill="x")
        haut.pack_propagate(False)
        titre = tk.Label(haut, text=t("titre_aide").upper(), bg="#0A1416",
                         fg="#0FBBD0", font=(FONT_MAIN, 13))
        titre.pack(side="left", padx=16)
        croix = tk.Label(haut, text="×", bg="#0A1416", fg="#7C959A",
                         font=(FONT_MAIN, 20), cursor=CURSEUR_MAIN)
        croix.pack(side="right", padx=14)
        croix.bind("<Button-1>", fermer_aide)
        tk.Frame(corps, bg="#1B3336", height=1).pack(fill="x")

        cadre = tk.Frame(corps, bg="#0A1416")
        cadre.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        # Une vraie zone de texte, et non des blocs empilés : c'est ce qui
        # permet un interligne franc (spacing2) et un espacement régulier
        # entre paragraphes (spacing3), tout en laissant le texte se couper
        # tout seul à la bonne largeur.
        zone = ctk.CTkTextbox(
            cadre, fg_color="#0A1416", bg_color="#0A1416",
            text_color="#E9F4F6",
            border_width=0, corner_radius=0, wrap="word",
            font=(FONT_MAIN, 14),
            scrollbar_button_color="#183335",
            scrollbar_button_hover_color="#0FBBD0",
        )
        zone.pack(fill="both", expand=True)
        texte = zone._textbox
        texte.configure(padx=14, pady=6, cursor="arrow",
                        selectbackground="#0B4A55",
                        selectforeground="#FFFFFF")

        # Les styles. Les puces et les avertissements ont un retrait
        # (lmargin2) : quand ils passent à la ligne, la suite reste sous le
        # texte, pas sous la puce.
        styles = {
            "title": dict(font=(FONT_MAIN, 19), foreground="#0FBBD0",
                          spacing1=6, spacing3=16),
            "head": dict(font=(FONT_MAIN, 17), foreground="#0FBBD0",
                         spacing1=22, spacing3=8),
            "body": dict(font=(FONT_MAIN, 14), foreground="#E9F4F6",
                         spacing1=0, spacing2=8, spacing3=12),
            "bullet": dict(font=(FONT_MAIN, 14), foreground="#E9F4F6",
                           spacing1=0, spacing2=8, spacing3=10,
                           lmargin1=0, lmargin2=18),
            "warning": dict(font=(FONT_MAIN, 14), foreground="#FF6B6B",
                            spacing1=2, spacing2=8, spacing3=12,
                            lmargin1=0, lmargin2=26),
            "code": dict(font=("Menlo", 13), foreground=LINK_COLOR,
                         spacing1=2, spacing2=4, spacing3=14,
                         lmargin1=22, lmargin2=22),
            "sep": dict(font=(FONT_MAIN, 12), foreground="#7C959A",
                        justify="center", spacing1=14, spacing3=14),
            "grand": dict(font=(FONT_MAIN, 18), foreground="#0FBBD0",
                          justify="center", spacing1=4, spacing3=4),
            "lien": dict(font=(FONT_MAIN, 16), foreground=LINK_COLOR,
                         justify="center", spacing3=10),
            "petit": dict(font=(FONT_MAIN, 11), foreground="#7C959A",
                          justify="center", spacing3=6),
            "italic": dict(font=(FONT_MAIN, 13, "italic"),
                           foreground="#7C959A", justify="center",
                           spacing3=6),
            "logo": dict(justify="center", spacing3=12),
        }
        for nom, options in styles.items():
            texte.tag_configure(nom, **options)

        # Le logo en tête : il fait partie du texte, donc il défile avec le
        # reste (comme avant) au lieu de rester collé en haut.
        self._logo_aide = None
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_AIDE_PATH)
                ratio = img.height / img.width
                largeur = self.largeur_logo
                img = img.resize((largeur, int(largeur * ratio)),
                                 Image.Resampling.LANCZOS)
                self._logo_aide = ImageTk.PhotoImage(img)
            except Exception:
                self._logo_aide = None

        # La petite tasse Ko-fi, pour la ligne de soutien : même image que le
        # lien du bas de page, à la taille du texte de l'aide.
        self._logo_kofi_aide = None
        chemin_kofi = trouver_ressource("ko-fi.png")
        if os.path.exists(chemin_kofi):
            try:
                img = Image.open(chemin_kofi)
                ratio = img.height / img.width
                hauteur = 26
                img = img.resize((int(hauteur / ratio), hauteur),
                                 Image.Resampling.LANCZOS)
                self._logo_kofi_aide = ImageTk.PhotoImage(img)
            except Exception:
                self._logo_kofi_aide = None

        # Le texte de l'aide, dans la langue de l'interface.
        contenu = [
            ("logo", ""),
            ("title", t("aide_titre")),
            ("space", ""),
            ("title2", t("aide_1")),
        ]
        # Trois aides n'ont pas été relues par un natif : on le dit au début,
        # dans la langue concernée, plutôt que de laisser croire le contraire.
        if LANGUE_UI in AVERTISSEMENT_AIDE:
            contenu[2:2] = [("warning", AVERTISSEMENT_AIDE[LANGUE_UI]),
                            ("space", "")]
        contenu += [
            ("text", t("aide_1a", nfr=len(VOIX["fr"]), nen=len(VOIX["en"]),
                       nde=len(VOIX["de"]))),
            ("bullet", t("aide_officielle")),
            ("text", t("aide_1b")),
            ("space", ""),
            ("title2", t("aide_robot_titre")),
            ("text", t("aide_robot1")),
            ("text", t("aide_robot2")),
            ("text", t("aide_robot3")),
            ("space", ""),
            ("title2", t("aide_2")),
            ("bullet", t("aide_2a")),
            ("bullet", t("aide_2b")),
            ("bullet", t("aide_2c")),
            ("text", t("aide_2d")),
            ("space", ""),
            ("warning", t("aide_nom1")),
            ("space", ""),
            ("title2", t("aide_3")),
            ("bullet", t("aide_3a")),
            ("bullet", t("aide_3b")),
            ("space", ""),
            ("title2", t("aide_4")),
            ("text", t("aide_4a")),
            ("space", ""),
            ("title2", t("aide_5")),
            ("text", t("aide_5a")),
            ("text", t("aide_5b")),
            ("space", ""),
            ("title2", t("aide_6_titre")),
            ("text", t("aide_6a")),
            ("text", t("aide_6b")),
            ("space", ""),
            ("title2", t("aide_net_titre")),
            ("text", t("aide_net1")),
            ("space", ""),
            ("warning", t("aide_net4")),
            ("space", ""),
            ("bullet", t("aide_net6")),
            ("bullet", t("aide_net7")),
            ("space", ""),
            ("title2", t("aide_sauv_titre")),
            ("text", t("aide_sauv1")),
            ("code", f"~/Documents/Vox-Pack/liste_{self.langue}.csv"),
            ("space", ""),
            ("title2", t("aide_def_titre")),
            ("text", t("aide_def1",
                       n=len(LISTE_PAR_DEFAUT.get(self.langue, [])))),
            ("text", t("aide_def5")),
            ("text", t("aide_def3")),
            ("space", ""),
            ("title2", t("aide_exp_titre")),
            ("text", t("aide_exp1")),
            ("bullet", t("aide_exp3")),
            ("bullet", t("aide_exp4")),
            ("space", ""),
            ("title2", t("aide_sys_titre")),
            ("text", t("aide_sys1")),
            ("text", t("aide_sys2")),
            ("text", t("aide_sys3")),
            ("text", t("aide_sys4")),
            ("text", t("aide_sys5")),
            ("space", ""),
            ("title2", t("aide_edge_titre")),
            ("text", t("aide_edge1")),
            ("space", ""),
            ("bullet", t("aide_edge3")),
            ("bullet", t("aide_edge5")),
            ("space", ""),
            ("warning", t("aide_edge8")),
            ("space", ""),
            ("title2", t("aide_fmt_titre")),
            ("text", t("aide_fmt1")),
            ("code", t("aide_fmt2")),
            ("space", ""),
            ("space", ""),
            ("title2", t("aide_maj_titre")),
            ("text", t("aide_maj")),
            ("lien_github", t("aide_github")),
            ("space", ""),
            ("sep", ""),
            ("grand_logo", t("aide_soutien")),
            ("lien", t("aide_lien")),
            ("space", ""),
            ("sep", ""),
            ("petit", t("aide_ecran",
                        version=VERSION,
                        ecran=f"{self.winfo_screenwidth()} × {self.winfo_screenheight()}",
                        fenetre=f"{self.winfo_width()} × {self.winfo_height()}")),
            ("italic", t("aide_credits")),
            ("italic", t("aide_merci")),
        ]

        for kind, txt in contenu:
            if kind == "logo":
                if self._logo_aide is not None:
                    # Un espace porte le style « logo » sur la ligne, pour que
                    # l'image soit centrée.
                    texte.insert("end", " ", "logo")
                    texte.image_create("end", image=self._logo_aide,
                                       padx=0, pady=4)
                    texte.insert("end", "\n", "logo")
            elif kind == "space":
                continue          # l'espacement est dans les styles
            elif kind == "title":
                texte.insert("end", txt + "\n", "title")
            elif kind == "title2":
                texte.insert("end", txt + "\n", "head")
            elif kind == "bullet":
                texte.insert("end", "•  " + txt + "\n", "bullet")
            elif kind == "warning":
                texte.insert("end", "⚠️  " + txt + "\n", "warning")
            elif kind == "text":
                texte.insert("end", txt + "\n", "body")
            elif kind == "code":
                texte.insert("end", txt + "\n", "code")
            elif kind == "sep":
                texte.insert("end", "─" * 36 + "\n", "sep")
            elif kind == "grand":
                texte.insert("end", txt + "\n", "grand")
            elif kind == "grand_logo":
                if self._logo_kofi_aide is not None:
                    texte.image_create("end", image=self._logo_kofi_aide,
                                       align="center")
                    texte.insert("end", "  ", "grand")
                texte.insert("end", txt + "\n", "grand")
            elif kind == "lien":
                texte.insert("end", txt + "\n", ("lien", "lien_kofi"))
            elif kind == "lien_github":
                texte.insert("end", txt + "\n", ("lien", "lien_github"))
            elif kind == "petit":
                texte.insert("end", txt + "\n", "petit")
            elif kind == "italic":
                texte.insert("end", txt + "\n", "italic")

        # Le lien de soutien reste cliquable, comme avant. On regarde le tag
        # sous le curseur au moment du clic : plus fiable qu'un tag_bind sur
        # un texte en lecture seule.
        def clic_lien(event):
            tags = texte.tag_names(texte.index(f"@{event.x},{event.y}"))
            if "lien_github" in tags:
                self._ouvrir_lien(URL_RELEASES)
            elif "lien" in tags:
                self._ouvrir_lien(KO_FI_URL)

        texte.bind("<Button-1>", clic_lien, add="+")
        # Chaque lien a SON tag de survol : avec un tag commun, éclairer un
        # lien éclairait aussi l'autre (les deux lignes sont voisines).
        for tag in ("lien_kofi", "lien_github"):
            texte.tag_bind(
                tag, "<Enter>",
                lambda e, t=tag: (texte.tag_configure(t, foreground=CYAN),
                                  texte.configure(cursor=CURSEUR_MAIN)))
            texte.tag_bind(
                tag, "<Leave>",
                lambda e, t=tag: (texte.tag_configure(t, foreground=LINK_COLOR),
                                  texte.configure(cursor="arrow")))

        texte.configure(state="disabled")
        texte.yview_moveto(0.0)

        bas = tk.Frame(corps, bg="#0A1416", height=58)
        bas.pack(fill="x", side="bottom")
        bas.pack_propagate(False)
        fermer = BoutonV2(bas, t("fermer"), 0, 0, 150, 40,
                          fond="#0A1416", contour=True, biseau=8,
                          fonte=(FONT_MAIN, 15), commande=fermer_aide)
        fermer.place_configure(relx=0.5, rely=0.5, anchor="center")

        # On peut déplacer l'aide pour regarder l'application derrière :
        # elle se tire par son en-tête.
        deplacement = {"dx": 0, "dy": 0}

        def prendre(e):
            deplacement["dx"] = e.x_root - popup.winfo_x()
            deplacement["dy"] = e.y_root - popup.winfo_y()

        def tirer(e):
            popup.geometry(f"+{e.x_root - deplacement['dx']}"
                           f"+{e.y_root - deplacement['dy']}")

        for morceau in (haut, titre):
            morceau.bind("<Button-1>", prendre)
            morceau.bind("<B1-Motion>", tirer)

        popup.transient(self)
        popup.lift()
        popup.focus_force()

    # ------------------------------------------------------------------
    # Gestion liste
    # ------------------------------------------------------------------
    def _rang_sous(self, evenement):
        """La ligne sous la souris, d'après la position dans le canevas."""
        return int(self._toile.canvasy(evenement.y) // self._hauteur_ligne)

    def _clic_liste(self, evenement):
        """Un clic dans la liste : la case se coche, la cellule s'ouvre."""
        self._toile.focus_set()
        rang = self._rang_sous(evenement)
        if rang < 0 or rang >= len(self.lignes):
            return
        x = self._toile.canvasx(evenement.x)
        marge = self._pv(4)
        if self._x_case - marge <= x <= self._x_case_fin + marge:
            self._clic_case(rang)
        elif x < self._x_sep:
            self._editer_ligne(rang, 0)
        else:
            self._editer_ligne(rang, 1)

    def _clic_case_maj(self, evenement):
        """Maj+clic sur une case : toute la plage, depuis la dernière cliquée."""
        rang = self._rang_sous(evenement)
        x = self._toile.canvasx(evenement.x)
        marge = self._pv(4)
        if self._x_case - marge <= x <= self._x_case_fin + marge:
            self._clic_case(rang, majuscule=True)

    def _maj_barre_liste(self, premier, dernier):
        """Place le pouce de la barre, au prorata de ce qui est visible."""
        p = self._pv
        haut = float(premier)
        bas = float(dernier)
        hauteur = max(1, self._hauteur_liste)
        y0 = haut * hauteur
        y1 = max(bas * hauteur, y0 + p(24))
        self._barre.coords(self._pouce, 0, y0, p(6), min(y1, hauteur))

    def _glisser_barre(self, evenement):
        """Un clic ou un glissement dans la barre amène la liste là."""
        hauteur = max(1, self._barre.winfo_height())
        self._toile.yview_moveto(max(0.0, min(1.0, evenement.y / hauteur)))
        return "break"

    def _molette_liste(self, evenement):
        """La molette de la liste : un cran de 46 px, sans rien perdre.

        L'ancienne version demandait au système quel widget se trouvait sous
        la souris À CHAQUE ÉVÉNEMENT. Ici c'est inutile — le canevas reçoit
        l'événement lui-même — et cela coûtait un aller-retour système par
        cran, dans le fil principal.

        Les petites valeurs d'un trackpad ne sont plus jetées : leur reste
        est reporté au cran suivant. L'ancien « int(delta / 6) » ramenait à
        zéro tout delta inférieur à 6, donc la plupart des événements d'un
        trackpad ne faisaient rien du tout.
        """
        if getattr(evenement, "num", None) == 4:      # Linux : vers le haut
            pixels = -self._pas_molette
        elif getattr(evenement, "num", None) == 5:    # Linux : vers le bas
            pixels = self._pas_molette
        else:
            delta = getattr(evenement, "delta", 0)
            if not delta:
                return "break"
            if sys.platform.startswith("win"):
                # Un cran de molette vaut 120.
                brut = -delta * self._pas_molette / 120.0
            else:
                # macOS : le delta dépend de la vitesse du geste (1 à 10).
                brut = -delta * self._pas_molette / 12.0
            # Un geste très rapide ne doit pas sauter la liste entière.
            brut = max(-3 * self._pas_molette,
                       min(3 * self._pas_molette, brut))
            self._reste_molette += brut
            pixels = int(self._reste_molette)
            self._reste_molette -= pixels
        if pixels:
            self._toile.yview_scroll(pixels, "units")
        return "break"

    def charger_liste(self):
        """Reconstruit la liste de la langue courante, puis la dessine."""
        if self._edition is not None:
            self._valider_edition()
        self.lignes.clear()
        contenu = []
        fichier = chemin_liste(self.langue)
        if os.path.exists(fichier):
            lignes_lues = self._lire_liste(fichier)
            # Un en-tête « nom,phrase » (nos fichiers exportés en ont un) est
            # ignoré : sinon il deviendrait une ligne de la liste. Le libellé
            # dépend de la langue dans laquelle l'export a été fait.
            if lignes_lues and est_entete(lignes_lues[0]):
                lignes_lues = lignes_lues[1:]
            for ligne_lue in lignes_lues:
                if len(ligne_lue) >= 2:
                    contenu.append((ligne_lue[0].strip(), ligne_lue[1].strip()))
                elif len(ligne_lue) == 1 and ligne_lue[0].strip():
                    contenu.append((ligne_lue[0].strip(), ""))

        if not contenu:
            # Liste reconstruite : celle de la langue des voix choisie.
            contenu = list(LISTE_PAR_DEFAUT.get(self.langue, []))

        for nom, texte in contenu:
            self._ajouter_ligne_ui(nom, texte)

        # Les lignes sont nouvelles : l'ancre de sélection n'a plus de sens,
        # et les noms invalides doivent être signalés dès l'affichage.
        self._ancre_selection = None
        self._verifier_noms(redessiner=False)
        self._dessiner_liste()
        self._toile.yview_moveto(0.0)
        self._ecrire_csv()
        self._maj_total_liste()

    @staticmethod
    def _lire_liste(fichier):
        """Lit le CSV de la liste, en UTF-8 puis en Latin-1.

        Un fichier réenregistré par un tableur peut être en Latin-1 : les
        accents y sont valides, seul l'UTF-8 les refuse. Sans ce repli, la
        lecture levait une exception au démarrage et l'application ne
        s'ouvrait pas du tout — pas même une fenêtre vide, pas même un
        message.

        La lecture passe par lire_lignes_csv, qui reconnaît aussi le
        point-virgule : un tableur français enregistre ainsi, et toute la
        ligne devenait sinon le nom du fichier. Un fichier vraiment
        illisible donne une liste vide, et l'appelant charge alors la liste
        de la langue. Enfin, un fichier avec un en-tête « nom,phrase »
        exporté par l'application est accepté : l'en-tête est retiré par
        l'appelant.
        """
        for encodage in ("utf-8-sig", "latin-1"):
            try:
                with open(fichier, "r", encoding=encodage, newline="") as f:
                    return lire_lignes_csv(f)
            except UnicodeDecodeError:
                continue
            except OSError:
                return []
        return []

    def _ajouter_ligne_ui(self, nom, texte):
        """Ajoute une ligne au modèle. Le dessin vient après, en un bloc.

        C'est le cœur du changement du 4 novembre : une ligne n'est plus une
        rangée de widgets, c'est une donnée. Dessiner quarante-quatre lignes
        prend quelques millisecondes au lieu d'une seconde sur un PC.
        """
        self.lignes.append({"nom": nom, "texte": texte, "coche": False,
                            "souci": ""})
        return len(self.lignes) - 1

    # -- le dessin de la liste -----------------------------------------
    def _dessiner_liste(self):
        """(Re)dessine toutes les lignes sur le canevas de la liste."""
        if self._edition is not None:
            self._valider_edition()
        haut = self._toile.yview()[0]
        self._toile.delete("ligne")
        for rang in range(len(self.lignes)):
            self._dessiner_ligne(rang)
        self._total_liste = max(1, len(self.lignes) * self._hauteur_ligne)
        self._toile.configure(
            scrollregion=(0, 0, self._largeur_liste, self._total_liste))
        if haut:
            self._toile.yview_moveto(haut)

    def _dessiner_ligne(self, rang):
        """Dessine une ligne : fond, case, nom, trait, phrase, message."""
        ligne = self.lignes[rang]
        t = self._toile
        p = self._pv
        etiquettes = ("ligne", "l%d" % rang)
        t.delete("l%d" % rang)
        y = rang * self._hauteur_ligne
        bas = y + self._hauteur_ligne
        fond = self.RAYURE_V2 if rang % 2 else self.NOIR_V2

        t.create_rectangle(0, y, self._largeur_liste, bas, fill=fond,
                           outline="", tags=etiquettes)
        # La case : un carré, rempli d'accent quand la ligne est cochée.
        t.create_rectangle(self._x_case, y + p(11), self._x_case_fin,
                           y + p(31), outline=self.BORD_V2, width=1,
                           fill=self.ACCENT_V2 if ligne["coche"] else fond,
                           tags=etiquettes)
        if ligne["coche"]:
            t.create_line(
                self._x_case + p(5), y + p(21),
                self._x_case + p(9), y + p(25),
                self._x_case + p(17), y + p(15),
                fill=self.NOIR_V2, width=2, tags=etiquettes)
        # Le nom : rouge quand il empêcherait la fabrication du fichier.
        couleur = DANGER if ligne["souci"] else self.ACCENT_V2
        t.create_text(self._x_nom, y + self._hauteur_ligne // 2,
                      text=self._couper(ligne["nom"],
                                        self._x_nom_fin - self._x_nom,
                                        self._police_liste),
                      anchor="w", fill=couleur, font=self._police_liste,
                      tags=etiquettes)
        t.create_line(self._x_sep, y + p(2), self._x_sep, bas - p(2),
                      fill="#17343A", tags=etiquettes)
        # Le message d'avertissement se pose à droite, dans la place laissée
        # par la phrase : rien ne bouge, ni la ligne, ni la colonne.
        limite = self._x_droite
        if ligne["souci"]:
            largeur = self._police_souci.measure(ligne["souci"])
            t.create_text(self._x_droite, y + self._hauteur_ligne // 2,
                          text=ligne["souci"], anchor="e", fill=DANGER,
                          font=self._police_souci, tags=etiquettes)
            limite = self._x_droite - largeur - p(10)
        t.create_text(self._x_phrase, y + self._hauteur_ligne // 2,
                      text=self._couper(ligne["texte"],
                                        limite - self._x_phrase,
                                        self._police_liste),
                      anchor="w", fill=self.TEXTE_V2,
                      font=self._police_liste, tags=etiquettes)
        # Le trait de séparation est posé SUR le bas de la ligne, pour ne pas
        # lui prendre un pixel de hauteur.
        t.create_line(0, bas - 1, self._largeur_liste, bas - 1,
                      fill="#16262A", tags=etiquettes)

    def _couper(self, texte, largeur, police):
        """Le texte raccourci pour tenir dans la colonne, avec un « … ».

        Recherche dichotomique : mesurer chaque lettre une à une coûtait plus
        cher que tout le reste du dessin sur une phrase longue.
        """
        if largeur <= 0:
            return ""
        if police.measure(texte) <= largeur:
            return texte
        bas, haut = 0, len(texte)
        while bas < haut:
            milieu = (bas + haut + 1) // 2
            if police.measure(texte[:milieu] + "…") <= largeur:
                bas = milieu
            else:
                haut = milieu - 1
        return (texte[:bas] + "…") if bas else "…"

    # -- le clavier dans la liste --------------------------------------
    # -- le clavier et l'édition dans la liste --------------------------
    def _boite_ligne(self, rang, colonne):
        """Position et taille de la cellule éditable, dans le canevas."""
        p = self._pv
        y = rang * self._hauteur_ligne
        marge = p(2)
        if colonne == 0:
            return (self._x_nom, y + marge,
                    self._x_sep - self._x_nom - p(6),
                    self._hauteur_ligne - 2 * marge)
        return (self._x_phrase, y + marge,
                self._x_droite - self._x_phrase,
                self._hauteur_ligne - 2 * marge)

    def _editer_ligne(self, rang, colonne):
        """Ouvre un VRAI champ sur une cellule, et un seul.

        C'est le principe de la liste dessinée : quarante-quatre lignes de
        texte, et un champ là où l'on écrit. Le champ est un objet du canevas,
        donc il suit le défilement tout seul.
        """
        self._valider_edition()
        if rang < 0 or rang >= len(self.lignes):
            return
        x, y, largeur, hauteur = self._boite_ligne(rang, colonne)
        fond = self.RAYURE_V2 if rang % 2 else self.NOIR_V2
        entree = tk.Entry(
            self._toile, bd=0, relief="flat", highlightthickness=1,
            highlightbackground=self.ACCENT_V2,
            highlightcolor=self.ACCENT_V2, bg=fond,
            fg=self.ACCENT_V2 if colonne == 0 else self.TEXTE_V2,
            insertbackground=self.TEXTE_V2, font=self._police_liste)
        entree.insert(0, self.lignes[rang]["nom" if colonne == 0 else "texte"])
        self._toile.create_window(
            x, y, anchor="nw", window=entree, width=largeur, height=hauteur,
            tags=("ligne", "edition"))
        entree.bind("<Return>", self._entree_puis_ligne)
        entree.bind("<Escape>", self._echapper_liste)
        entree.bind("<FocusOut>", lambda e: self._valider_edition())
        self._edition = (rang, colonne, entree)
        entree.focus_set()
        try:
            # « focus_force » passe même si la fenêtre n'est pas encore la
            # fenêtre active du système : c'est le cas sous Windows quand on
            # vient de cliquer sur un bouton dessiné. Sans lui, le champ
            # s'affichait mais ne recevait aucune touche.
            entree.focus_force()
        except tk.TclError:
            pass
        entree.icursor("end")
        self._montrer_ligne(rang)

    def _entree_puis_ligne(self, _evenement=None):
        """Entrée dans un champ : on valide, et on enchaîne une ligne."""
        self._valider_edition()
        self.ajouter_ligne()
        return "break"

    def _valider_edition(self):
        """Écrit ce que le champ contient dans le modèle, et referme le champ."""
        if self._edition is None:
            return
        rang, colonne, entree = self._edition
        self._edition = None          # avant destroy : FocusOut repasserait ici
        try:
            valeur = entree.get()
        except tk.TclError:
            entree.destroy()
            self._toile.delete("edition")
            return
        self._rendre_le_focus()
        entree.destroy()
        self._toile.delete("edition")
        # La ligne a pu disparaître entre l'ouverture du champ et sa
        # fermeture (suppression, import, changement de langue) : on écrit
        # seulement si elle existe encore.
        if 0 <= rang < len(self.lignes):
            self.lignes[rang]["nom" if colonne == 0 else "texte"] = valeur
            self._on_change()

    def _rendre_le_focus(self):
        """Rend le focus au canevas avant de détruire un champ.

        Détruire le widget qui a le focus laissait, sous Windows, le clavier
        dans le vide : plus aucun champ ne s'ouvrait ensuite.
        """
        try:
            self._toile.focus_set()
        except tk.TclError:
            pass

    def _annuler_edition(self):
        """Échap dans un champ : on jette la saisie, sans rien enregistrer."""
        if self._edition is None:
            return
        _, _, entree = self._edition
        self._edition = None
        self._rendre_le_focus()
        entree.destroy()
        self._toile.delete("edition")

    def _echapper_liste(self, _evenement=None):
        """Échap dans un champ : on jette la saisie, et on referme les menus."""
        self._annuler_edition()
        self._echapper()
        return "break"

    def _montrer_ligne(self, rang):
        """Fait défiler la liste pour que la ligne active reste visible.

        Sans cela, Tab descendait dans des lignes que l'on ne voyait plus :
        le focus continuait sous le bord de la liste, et l'on tapait à
        l'aveugle.
        """
        toile = getattr(self, "_toile", None)
        if toile is None or not toile.winfo_ismapped() \
                or toile.winfo_height() <= 1:
            return
        y = rang * self._hauteur_ligne
        haut = toile.canvasy(0)
        marge = self._pv(14)
        if y < haut + marge:
            cible = y - marge
        elif y + self._hauteur_ligne > haut + toile.winfo_height() - marge:
            cible = y + self._hauteur_ligne - toile.winfo_height() + marge
        else:
            return
        total = max(1, len(self.lignes) * self._hauteur_ligne)
        toile.yview_moveto(max(0.0, min(1.0, cible / total)))

    def ajouter_ligne(self):
        rang = self._ajouter_ligne_ui(t("nouvelle_ligne"), t("texte_a_dire"))
        # La ligne ajoutée est active d'office : cochée, prête à être tapée.
        self.lignes[rang]["coche"] = True
        self._verifier_noms(redessiner=False)
        self._dessiner_liste()
        self._on_change()
        self._maj_total_liste()
        self._sync_toutes_v2()
        # La liste descend jusqu'à la nouvelle ligne, PUIS le champ s'ouvre
        # dessus : ouvrir d'abord faisait défiler ensuite, et le champ
        # pouvait se retrouver hors de la vue ou perdre le focus en route.
        def ouvrir():
            self._toile.yview_moveto(1.0)
            self.update_idletasks()
            self._editer_ligne(rang, 0)

        self.after_idle(ouvrir)

    def _remplir_voix(self):
        """Remplit le menu des voix avec celles de la langue courante.

        On retrouve la voix utilisée la dernière fois dans cette langue, et on
        la retrouve par son IDENTIFIANT technique (« fr-FR-DeniseNeural ») :
        le libellé contient « Femme » ou « Female », qui change avec la langue
        de l'interface. Le choix français et le choix anglais sont mémorisés
        séparément.
        """
        libelles = [etiquette for etiquette, _id in voix_de_la_langue(self.langue)]
        self.combo_voice.configure(values=libelles)
        souvenue = self._reglages.get("voix", {}).get(self.langue)
        # Réglages d'une version précédente : c'est le LIBELLÉ qui était
        # enregistré (« Sylvie (Femme - Québec) ») et non l'identifiant. On le
        # convertit une bonne fois, pour que Richard ne perde pas sa voix.
        if souvenue and not any(i == souvenue
                                for _e, i in voix_de_la_langue(self.langue)):
            converti = identifiant_par_libelle(self.langue, souvenue)
            if converti:
                souvenue = converti
                self._reglages.setdefault("voix", {})[self.langue] = converti
                ecrire_reglages(self._reglages)
        etiquette = libelles[0] if libelles else ""
        for propose, identifiant in voix_de_la_langue(self.langue):
            if identifiant == souvenue:
                etiquette = propose
                break
        # On pose d'abord la voix retrouvée, PUIS on place la coche : la coche
        # se déduit de la voix affichée, elle ne peut pas la précéder.
        self.combo_voice.set(etiquette)
        self._maj_marque_voix()

    # ------------------------------------------------------------------
    # Vérification des voix (en arrière-plan)
    # ------------------------------------------------------------------
    def _verifier_voix(self):
        """Demande à Microsoft la liste des voix réellement disponibles.

        Si une voix proposée par l'application a disparu du service, elle est
        retirée du menu. Si la vérification échoue (pas d'Internet), on ne
        touche à rien : la liste de l'application reste utilisable.

        Le fil de travail ne touche JAMAIS à l'interface (Tkinter n'aime pas
        ça) : il dépose son résultat dans une file, que l'on vient lire depuis
        le fil principal.
        """
        resultat = queue.Queue()

        def travail():
            try:
                disponibles = {v["ShortName"]
                               for v in asyncio.run(edge_tts.list_voices())}
            except Exception:
                resultat.put(None)          # pas de réseau : on garde la liste
            else:
                resultat.put(disponibles)

        threading.Thread(target=travail, daemon=True).start()
        self._attendre_voix(resultat)

    def _attendre_voix(self, resultat):
        """Vient chercher le résultat dès qu'il est prêt (sans bloquer)."""
        try:
            disponibles = resultat.get_nowait()
        except queue.Empty:
            self.after(150, lambda: self._attendre_voix(resultat))
            return
        if disponibles:
            self._retirer_voix_absentes(disponibles)

    def _retirer_voix_absentes(self, disponibles):
        """Retire du menu les voix que le service ne propose plus."""
        retirees = []
        for code, voix in VOIX.items():
            gardees = [entree for entree in voix if entree[0] in disponibles]
            if len(gardees) != len(voix):
                retirees += [f"{e[1]} ({e[3]})" for e in voix
                             if e[0] not in disponibles]
                VOIX[code] = gardees
        if not retirees:
            return
        # Une langue ne doit jamais se retrouver sans aucune voix : si le
        # service a retiré tout un lot (panne passagère ?), on remet la liste
        # d'origine plutôt que de laisser un menu vide.
        remises = [code for code, voix in VOIX.items() if not voix]
        for code in remises:
            VOIX[code] = list(VOIX_ORIGINE[code])
        self._remplir_voix()
        if remises:
            self._dire(t("etat_voix_remises"))
        else:
            self._dire(t("etat_voix_retirees", n=len(retirees),
                         s="s" if len(retirees) > 1 else ""))

    def _voix_changee(self, _valeur=None):
        """L'utilisateur a choisi une autre voix.

        On la mémorise ET on déplace la coche de la liste : sans ce second
        point, la coche restait sur l'ancienne voix et on ne savait plus
        laquelle était active.
        """
        self._memoriser_voix()
        self._sauver_reglages()
        self._maj_marque_voix()

    def _maj_marque_voix(self):
        """Place la coche de la liste sur la voix actuellement choisie.

        La coche n'existe que dans la liste déroulante : la case fermée
        affiche, elle, le libellé propre.
        """
        courante = identifiant_voix(self.langue, self.combo_voice.get())
        marques = []
        for etiquette, identifiant in voix_de_la_langue(self.langue):
            marques.append((MARQUE_VOIX + etiquette)
                           if identifiant == courante else etiquette)
        self.combo_voice.configure(values=marques)
        for etiquette, identifiant in voix_de_la_langue(self.langue):
            if identifiant == courante:
                # La case fermée montre le nom et son étoile, rien d'autre.
                self.combo_voice.set(etiquette)
                break

    def _memoriser_voix(self):
        """Retient la voix choisie, par son identifiant technique.

        On n'enregistre pas le libellé (« Denise (Femme - France) ») : il
        contient « Femme », qui devient « Female » en anglais. L'identifiant,
        lui, ne change jamais.
        """
        identifiant = identifiant_voix(self.langue, self.combo_voice.get())
        if identifiant:
            self._reglages.setdefault("voix", {})[self.langue] = identifiant

    def _sauver_reglages(self):
        """Enregistre les réglages. Une seule langue : langue_ui."""
        self._reglages["langue_ui"] = LANGUE_UI
        ecrire_reglages(self._reglages)

    def _dire(self, texte):
        """Écrit une information dans la ligne, sous la barre de progression.

        Appelée depuis un fil de travail (génération, aperçu) : le changement
        d'affichage est donc confié à la boucle d'événements avec after().
        L'appel est protégé : si la fenêtre est en train de se fermer, on
        préfère perdre un message plutôt que de tuer le fil en cours.
        """
        def ecrire(txt=texte):
            self.lbl_etat.configure(text=txt or "waiting...")

        try:
            self.after(0, ecrire)
        except Exception:
            pass

    def _clic_case(self, rang, majuscule=False):
        """Clic sur une case : cette ligne, ou toute une plage avec Majuscule.

        Avec Majuscule, on applique le nouvel état à TOUTES les lignes depuis
        la dernière cliquée jusqu'à celle-ci, en haut comme en bas — comme
        dans le Finder.
        """
        if rang < 0 or rang >= len(self.lignes):
            return
        etat = not self.lignes[rang]["coche"]
        if majuscule and self._ancre_selection is not None \
                and self._ancre_selection < len(self.lignes):
            debut, fin = sorted((self._ancre_selection, rang))
        else:
            debut, fin = rang, rang
            self._ancre_selection = rang
        for i in range(debut, fin + 1):
            self.lignes[i]["coche"] = etat
            self._dessiner_ligne(i)
        self._sync_toutes_v2()
        self._maj_total_liste()

    def _verifier_noms(self, redessiner=True):
        """Colore en rouge les noms qui posent problème, signale les doublons."""
        avant = [ligne["souci"] for ligne in self.lignes]
        vus = {}
        for i, ligne in enumerate(self.lignes, start=1):
            nom = ligne["nom"].strip()
            souci = probleme_nom(nom)
            if souci is None:
                deja = vus.get(nom.lower())
                if deja:
                    souci = t("pb_doublon", n=deja)
                else:
                    vus[nom.lower()] = i
            ligne["souci"] = souci or ""
        if redessiner:
            # Seules les lignes qui changent d'état sont redessinées : une
            # frappe ne doit pas repeindre les quarante-quatre.
            for i, ligne in enumerate(self.lignes):
                if i < len(avant) and avant[i] != ligne["souci"]:
                    self._dessiner_ligne(i)

    def supprimer_selection(self):
        cochees = [l for l in self.lignes if l["coche"]]
        if not cochees:
            self._message(t("msg_supprimer_rien"), icone="attention")
            return

        if len(cochees) == len(self.lignes):
            self._message(
                t("msg_supprimer_tout"),
                icone="attention",
                boutons=[(t("btn_supprimer"),
                          lambda: self._supprimer_lignes(cochees)),
                         (t("annuler"), None)],
            )
            return

        self._supprimer_lignes(cochees)

    def _supprimer_lignes(self, cochees):
        if self._edition is not None:
            self._valider_edition()
        for ligne in list(cochees):
            if ligne in self.lignes:
                self.lignes.remove(ligne)
        # les numéros de ligne ont changé : le point de départ n'est plus valable
        self._ancre_selection = None
        self._verifier_noms(redessiner=False)
        self._dessiner_liste()
        self._on_change()
        self._maj_total_liste()

    def tout_cocher(self):
        for ligne in self.lignes:
            ligne["coche"] = True
        self._dessiner_liste()
        self._sync_toutes_v2()

    def rien_cocher(self):
        for ligne in self.lignes:
            ligne["coche"] = False
        self._dessiner_liste()
        self._sync_toutes_v2()

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
            fichier = chemin_liste(self.langue)
            temporaire = fichier + ".tmp"
            with open(temporaire, "w", encoding="utf-8", newline="") as f:
                ecrivain = csv.writer(f)
                for l in self.lignes:
                    nom = l["nom"].strip()
                    texte = l["texte"].strip()
                    if nom or texte:
                        ecrivain.writerow([nom, texte])
            # La copie de secours est faite UNE fois par session et par liste,
            # avant la première écriture : elle garde la liste telle qu'elle
            # était à l'ouverture. Rafraîchie à chaque frappe, elle ne
            # contenait que l'état d'une frappe plus tôt, et vider la liste
            # effaçait aussi la dernière sauvegarde utile.
            if fichier not in self._bak_faits:
                self._bak_faits.add(fichier)
                if os.path.exists(fichier) and os.path.getsize(fichier) > 0:
                    shutil.copy2(fichier, fichier + ".bak")
            # Windows refuse parfois le renommage pendant quelques dixièmes de
            # seconde : l'antivirus vient de lire le fichier temporaire, ou
            # OneDrive le synchronise. Deux essais de plus règlent ce cas.
            # Après un échec déjà signalé, on n'insiste plus : cette fonction
            # tourne à chaque frappe, et une attente répétée rendrait la saisie
            # pâteuse.
            essais = 1 if self._erreur_sauvegarde else 3
            for essai in range(essais):
                try:
                    os.replace(temporaire, fichier)
                    break
                except OSError:
                    if essai == essais - 1:
                        raise
                    time.sleep(0.1)
            self._erreur_sauvegarde = False
        except Exception as e:
            # Une seule alerte par session : sinon chaque frappe en ouvrirait une
            if not self._erreur_sauvegarde:
                self._erreur_sauvegarde = True
                self.after(0, lambda err=e: self._message(
                    t("msg_sauvegarde_echec", err=err), icone="erreur"))

    # ------------------------------------------------------------------
    # Aperçu audio
    # ------------------------------------------------------------------
    def ecouter_selection(self):
        """Écoute les lignes cochées, l'une après l'autre.

        Comme « Supprimer » et « Let's Go », l'aperçu agit sur TOUTES les
        lignes cochées : c'est ce que l'utilisateur attend, et cela permet de
        vérifier un lot entier avant de le générer.
        """
        cochees = [l for l in self.lignes if l["coche"]]
        if not cochees:
            self._message(t("msg_ecouter_rien"), icone="attention")
            return
        textes = []
        for ligne in cochees:
            phrase = ligne["texte"].strip()
            if phrase:
                textes.append((ligne["nom"].strip(), phrase))
        if not textes:
            return
        voice_id = identifiant_voix(self.langue, self.combo_voice.get())

        # Le bouton devient « Arrêter » : la lecture peut être coupée.
        self._apercu_no += 1
        numero = self._apercu_no
        self._lecture = None
        self.btn_apercu.dire(t("arreter"), arret=True)
        self.btn_apercu.configure(command=self.arreter_apercu)

        threading.Thread(
            target=lambda: asyncio.run(
                self._jouer_apercu(textes, voice_id, numero)),
            daemon=True,
        ).start()

    def arreter_apercu(self):
        """Coupe la lecture, et empêche la phrase suivante de démarrer.

        Incrémenter le numéro d'aperçu est indispensable : sans cela on coupait
        bien la phrase en cours, mais la boucle enchaînait aussitôt la
        suivante — « Arrêter » servait alors de bouton « Suivant ».
        """
        self._apercu_no += 1
        lecture = self._lecture
        if lecture is not None:
            try:
                lecture.terminate()
            except Exception:
                pass
        self._fin_apercu()
        self._dire("")

    def _fin_apercu(self):
        """Le bouton redevient « Écouter »."""
        # L'aperçu est fini : sans ça, un changement de langue croit encore
        # qu'une lecture est en cours et affiche « Arrêter ».
        self._lecture = None
        try:
            self.btn_apercu.dire(t("ecouter"), arret=False)
            self.btn_apercu.configure(command=self.ecouter_selection)
            # L'aspect suit de nouveau le pointeur : le bouton ne peut plus
            # rester dans un état intermédiaire (survol de la lecture).
            if getattr(self.btn_apercu, "_pointer_dedans", False):
                self.btn_apercu._entrer()
            else:
                self.btn_apercu._sortir()
        except Exception:
            pass

    def _langue_effet(self, voice_id):
        """Langue de la voix utilisée, pour les variantes de l'effet robot."""
        return ("fr" if voice_id.startswith("fr-")
                else "de" if voice_id.startswith("de-") else "en")

    async def _fabriquer_apercu(self, texte, voice_id, wav):
        """Fabrique le WAV d'aperçu d'une phrase, silences compris."""
        await fabriquer_wav(texte, voice_id, wav,
                            pitch=self._robot_pitch(),
                            rate=self._rate_effectif(voice_id),
                            robot=self._robot,
                            langue_effet=self._langue_effet(voice_id),
                            niveau=self._niveau)

    async def _jouer_apercu(self, textes, voice_id, numero):
        """Lit les phrases l'une après l'autre, sans temps mort.

        Le WAV de la phrase suivante est fabriqué PENDANT que la phrase en
        cours est lue. Sans cela, on entendait une pause entre chaque phrase :
        le temps d'aller chercher la voix chez Microsoft.
        """
        voice_id = self._robot_voice() or voice_id
        os.makedirs(DATA_DIR, exist_ok=True)
        total = len(textes)

        # Un nom de fichier différent pour chaque phrase : deux aperçus rapides
        # ne peuvent plus se supprimer mutuellement le fichier en cours.
        def chemin_wav(rang):
            return os.path.join(DATA_DIR,
                                f"apercu_{os.getpid()}_{numero}_{rang}.wav")

        tache = asyncio.create_task(
            self._fabriquer_apercu(textes[0][1], voice_id, chemin_wav(1)))
        try:
            for rang, (nom, texte) in enumerate(textes, start=1):
                # « Arrêter » a incrémenté le numéro : on s'arrête là.
                if self._apercu_no != numero:
                    break
                self._dire(t("etat_ecoute", rang=rang, total=total, nom=nom))
                try:
                    await tache              # le WAV de CETTE phrase
                except Exception as e:
                    if self._apercu_no == numero:
                        raison = raison_lisible(e)
                        if raison == t("err_reseau"):
                            raison = t("err_reseau_detail")
                        self.after(0, lambda r=raison: self._message(
                            t("msg_apercu_echec", err=r), icone="erreur"))
                    break
                # Pendant la lecture qui suit, la phrase suivante se prépare.
                if rang < total:
                    tache = asyncio.create_task(
                        self._fabriquer_apercu(textes[rang][1], voice_id,
                                               chemin_wav(rang + 1)))
                if self._apercu_no != numero:
                    break
                source = chemin_wav(rang)
                lecture = LectureAudio(source)
                self._lecture = lecture
                if lecture.erreur is not None:
                    if self._apercu_no == numero:
                        self.after(0, lambda: self._message(
                            t("msg_audio_absent"), icone="attention"))
                    break
                # On attend la fin de la lecture SANS bloquer la boucle : c'est
                # ce qui laisse le téléchargement de la suite avancer.
                await asyncio.to_thread(lecture.wait)
        finally:
            if not tache.done():
                tache.cancel()
            for rang in range(1, total + 1):
                fichier = chemin_wav(rang)
                if os.path.exists(fichier):
                    try:
                        os.remove(fichier)
                    except OSError:
                        pass
        if self._apercu_no != numero:
            # « Arrêter » a déjà tout remis en place, ou un autre aperçu a
            # pris le relais : ne pas toucher à son bouton ni à son message.
            return
        try:
            self.after(0, self._fin_apercu)
        except Exception:
            # La fenêtre se ferme : tant pis pour le bouton, l'important est
            # que le fil se termine proprement.
            pass
        self._dire("")

    # ------------------------------------------------------------------
    # Génération
    # ------------------------------------------------------------------
    def start_generation(self):
        if self._genere:
            self._message(t("msg_genere_deja"), icone="attention")
            return
        cochees = [l for l in self.lignes if l["coche"]]
        if not cochees:
            self._message(t("msg_generer_rien"), icone="attention")
            return

        taches = []
        refuses = []
        vus = {}
        for l in cochees:
            nom = l["nom"].strip()
            texte = l["texte"].strip()
            souci = probleme_nom(nom)
            if souci is None:
                # Deux lignes au même nom (majuscules ignorées, comme sur le
                # disque d'un Mac ou d'un PC) : la seconde écraserait la
                # première en silence.
                deja = vus.get(nom.lower())
                if deja:
                    souci = t("pb_doublon", n=deja)
                else:
                    vus[nom.lower()] = self.lignes.index(l) + 1
            if souci:
                # un nom invalide donnerait un fichier que la radio ne lirait
                # pas : on le signale au lieu de le fabriquer pour rien
                refuses.append((nom or t("pb_vide"), souci))
            elif phrase_sans_silences(texte):
                taches.append((nom, texte))
        if not taches:
            self._message(t("msg_generer_aucune"), icone="attention")
            return

        dossier = self._choisir_dossier(
            t("titre_dossier"),
            self._reglages.get("dernier_dossier") or os.path.expanduser("~"),
        )
        if not dossier:
            return
        self._reglages["dernier_dossier"] = dossier
        ecrire_reglages(self._reglages)

        # Si l'utilisateur a déjà choisi le sous-dossier lui-même, on n'en
        # crée pas un deuxième à l'intérieur.
        if os.path.basename(dossier) == DOSSIER_SORTIE:
            self.output_dir = dossier
        else:
            self.output_dir = os.path.join(dossier, DOSSIER_SORTIE)

        voice_id = identifiant_voix(self.langue, self.combo_voice.get())

        self.btn_letsgo.configure(state="disabled", fg_color="#083137")
        self._genere = True
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
            self._genere = False
            try:
                # On ne lit plus les BooleanVar Tk depuis ce fil : la remise
                # en place se fait sur le fil principal (voir _apres_generation).
                self.after(0, self._apres_generation)
            except Exception:
                pass  # la fenêtre se ferme : tant pis pour le bouton

    def _apres_generation(self):
        """Remet le bouton et le compteur en place, sur le fil principal.

        La barre redescend d'elle-même et le compteur la suit : il revient
        donc à « 0 / ce qui reste coché ».
        """
        self._genere = False
        self._total_v2 = self._total_a_faire()
        try:
            self.btn_letsgo.configure(state="normal", fg_color="#0B2E36")
        except Exception:
            pass

    async def _generer(self, taches, voice_id, refuses=None):
        voice_id = self._robot_voice() or voice_id
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError as e:
            self._dire("")
            self.after(0, lambda err=e: self._message(
                t("msg_dossier_echec", err=err), icone="erreur"))
            return
        total = len(taches)
        echecs = list(refuses or [])       # noms refusés avant même d'essayer
        nb_refuses = len(echecs)
        faits = 0                          # succès réels, pas « non échoués »
        reseau_suite = 0
        coupe_reseau = False

        self._dire(t("etat_recherche_service"))

        for idx, (nom, texte) in enumerate(taches):
            final_wav = os.path.join(self.output_dir, f"{nom}.wav")
            fait = idx + 1
            try:
                self._dire(t("etat_recherche_voix", fait=fait, total=total,
                             nom=nom))
                await fabriquer_wav(
                    texte, voice_id, final_wav,
                    pitch=self._robot_pitch(),
                    rate=self._rate_effectif(voice_id),
                    robot=self._robot,
                    langue_effet=self._langue_effet(voice_id),
                    niveau=self._niveau,
                    annoncer=lambda: self._dire(
                        t("etat_generation_wav", fait=fait, total=total,
                          nom=nom)))
                faits += 1
                # Un succès remet le compteur à zéro : la coupure ne doit
                # être déclarée qu'après trois échecs CONSÉCUTIFS. Sans cela,
                # trois accrocs dispersés dans une longue série finissaient
                # par arrêter une génération qui allait très bien.
                reseau_suite = 0
            except Exception as e:
                # On note l'échec et on passe à la ligne suivante : une phrase
                # qui rate ne doit pas priver l'utilisateur de toutes les autres.
                raison = raison_lisible(e)
                echecs.append((nom, raison))
                if raison == t("err_reseau"):
                    reseau_suite += 1
                    if reseau_suite >= 3:
                        coupe_reseau = True
                        break
                else:
                    reseau_suite = 0

            val = fait / total
            self.after(0, lambda v=val: self.progress.set(v))
            self._dire(t("etat_avance", fait=fait, total=total, nom=nom,
                         s="s" if fait > 1 else ""))

        # On laisse la barre complète visible avant qu'elle redescende :
        # c'est le seul moment où l'on voit la dernière led allumée.
        await asyncio.sleep(PAUSE_LEDS)
        self.after(0, lambda: self.progress.reset())
        self._dire("")

        reussis = faits
        if echecs:
            detail = "\n".join(f"• {nom} : {raison}" for nom, raison in echecs[:6])
            if len(echecs) > 6:
                detail += "\n" + t("msg_autres", n=len(echecs) - 6)
            if coupe_reseau:
                detail = t("msg_reseau_coupe") + "\n" + detail
            self.after(0, lambda: self._message(
                t("msg_bilan_echecs", reussis=reussis,
                  s1="s" if reussis > 1 else "", total=total + nb_refuses,
                  problemes=len(echecs), s2="s" if len(echecs) > 1 else "",
                  detail=detail),
                icone="erreur"))
        else:
            out = self.output_dir
            self.after(0, lambda: self._message(
                t("msg_succes", dossier=chemin_lisible(out)),
                icone="succes",
                boutons=[(t("ouvrir_dossier"),
                          lambda: self._ouvrir_dossier(out)),
                         (t("fermer"), None)]))

    # ------------------------------------------------------------------
    # Sons système d'EdgeTX
    # ------------------------------------------------------------------
    def creer_sons_systeme(self):
        """Refabrique les sons système de la radio avec la voix choisie.

        Le circuit est volontairement SÉPARÉ de la liste : il lit la liste
        officielle, écrit des fichiers, et « self.lignes » n'est jamais touché.
        Richard a déjà perdu une liste une fois ; l'opération ne doit pas
        pouvoir la mettre en danger.

        La source est la liste officielle d'EdgeTX (voices/fr-FR.csv ou
        voices/en-GB.csv), téléchargée au moment de l'usage : plus besoin de
        brancher la carte, et la liste est à jour. Rien n'est embarqué dans
        Vox-Pack. La voix est celle déjà choisie dans la fenêtre.
        """
        if self._genere:
            self._message(t("msg_genere_deja"), icone="attention")
            return

        # La ligne d'état prévient pendant le téléchargement (moins d'une
        # seconde en temps normal) : sans elle, on croirait que rien ne se
        # passe. update_idletasks() la fait s'afficher tout de suite.
        self._dire(t("etat_csv_telechargement"))
        self.update_idletasks()
        try:
            lignes, dossier_sd, depuis_cache = csv_officiel_sons_systeme(
                self.langue)
        except Exception as e:
            self._dire("")
            self._message(
                t("msg_csv_officiel_echec", err=str(e)[:160]), icone="erreur")
            return
        if not lignes:
            self._dire("")
            self._message(t("msg_csv_aucun_systeme"), icone="attention")
            return

        taches, refuses = trier_sons_systeme(lignes)
        self._dire("")
        if not taches:
            # Tous les noms ont été refusés : autant le dire tout de suite,
            # avec les raisons, plutôt que de créer un dossier vide.
            detail = "\n".join(f"• {nom} : {raison}"
                               for nom, raison in refuses[:6])
            if len(refuses) > 6:
                detail += "\n" + t("msg_autres", n=len(refuses) - 6)
            self._message(
                t("msg_sons_bilan", reussis=0, s1="",
                  total=len(refuses), problemes=len(refuses),
                  s2="s" if len(refuses) > 1 else "", detail=detail),
                icone="erreur")
            return

        dossier = self._choisir_dossier(
            t("titre_dossier_systeme"),
            self._reglages.get("dernier_dossier_systeme")
            or self._reglages.get("dernier_dossier")
            or os.path.expanduser("~"),
        )
        if not dossier:
            self._dire("")
            return
        self._reglages["dernier_dossier_systeme"] = dossier
        ecrire_reglages(self._reglages)

        # On n'écrit jamais à la racine du dossier choisi : les sons système
        # doivent arriver dans SYSTEM/, sinon la radio ne les trouvera pas. Et
        # si l'utilisateur a déjà choisi un dossier nommé SYSTEM, on n'en crée
        # pas un deuxième à l'intérieur.
        if os.path.basename(dossier.rstrip("/\\")).upper() == "SYSTEM":
            sortie = dossier
        else:
            sortie = os.path.join(dossier, "SYSTEM")

        voice_id = identifiant_voix(self.langue, self.combo_voice.get())

        # Le bouton « Let's Go » devient « Arrêter » : des centaines de
        # fichiers, c'est plusieurs minutes, et on doit pouvoir renoncer.
        self._genere = True
        self._total_v2 = len(taches)
        self._sons_stop = threading.Event()
        self.btn_letsgo.dire(t("arreter"), arret=True)
        self.btn_letsgo.configure(
            command=self._arreter_sons_systeme, fg_color="#083137")
        self.progress.set(0.0)
        self._dire(t("etat_recherche_service"))
        # Le voyant s'allume et bat tant que ça travaille ; il s'éteindra
        # dans _fin_sons_systeme, que l'on arrête ou que ça se termine.
        self._voyant_systeme.allumer()
        self._voyant_systeme.clignoter(True)

        threading.Thread(
            target=self._lancer_sons_systeme,
            args=(taches, refuses, sortie, dossier_sd, voice_id, depuis_cache),
            daemon=True,
        ).start()

    def _arreter_sons_systeme(self):
        """Demande l'arrêt : le fichier en cours se termine, puis on s'arrête.

        On ne coupe pas le téléchargement au milieu d'un fichier : un WAV
        tronqué serait pire qu'un fichier de plus. Les fichiers déjà écrits,
        eux, restent en place.
        """
        stop = self._sons_stop
        if stop is not None:
            stop.set()
        try:
            self.btn_letsgo.configure(state="disabled", fg_color="#083137")
        except Exception:
            pass
        self._dire(t("etat_sons_arret"))

    def _lancer_sons_systeme(self, taches, refuses, sortie, dossier_sd,
                             voice_id, depuis_cache=False):
        """Fil de travail : la boucle asyncio de la création des sons."""
        try:
            asyncio.run(self._generer_sons_systeme(
                taches, refuses, sortie, dossier_sd, voice_id, depuis_cache))
        finally:
            try:
                self.after(0, self._fin_sons_systeme)
            except Exception:
                pass  # la fenêtre se ferme : tant pis pour le bouton

    def _fin_sons_systeme(self):
        """Le bouton redevient « Let's Go » une fois la génération terminée."""
        self._voyant_systeme.eteindre()
        self._sons_stop = None
        self._genere = False
        self._total_v2 = self._total_a_faire()
        try:
            self.btn_letsgo.dire(t("lets_go"), arret=False)
            self.btn_letsgo.configure(
                state="normal", command=self._lancer_generation_v2,
                fg_color="#0B2E36")
        except Exception:
            pass

    async def _generer_sons_systeme(self, taches, refuses, sortie,
                                    dossier_sd="", voice_id="",
                                    depuis_cache=False):
        """Fabrique un WAV par ligne du CSV, dans <dossier>/SYSTEM/.

        Même pipeline que la génération normale (edge-tts puis conversion),
        mais la liste affichée n'est jamais lue ni modifiée.
        """
        voice_id = self._robot_voice() or voice_id
        try:
            os.makedirs(sortie, exist_ok=True)
        except OSError as e:
            self._dire("")
            self.after(0, lambda err=e: self._message(
                t("msg_dossier_echec", err=err), icone="erreur"))
            return

        total = len(taches)
        echecs = list(refuses or [])       # noms refusés avant même d'essayer
        nb_refuses = len(echecs)
        faits = 0
        arrete = False

        # Le MP3 de travail vit dans le dossier temporaire du système ; le WAV
        # est construit directement dans le dossier de destination. Ainsi le
        # remplacement final reste sur le même disque (Windows échoue avec
        # WinError 17 quand la sortie est sur D: et le temporaire sur C:).
        travail = tempfile.mkdtemp(prefix="vox-pack-sons-")
        reseau_suite = 0
        coupe_reseau = False
        try:
            for idx, (nom, phrase) in enumerate(taches):
                stop = self._sons_stop
                if stop is not None and stop.is_set():
                    arrete = True
                    break
                temp_mp3 = os.path.join(travail, f"{idx}.mp3")
                final_wav = os.path.join(sortie, f"{nom}.wav")
                temp_wav = final_wav + ".tmp"
                traite = idx + 1
                try:
                    self._dire(t("etat_recherche_voix", fait=traite,
                                 total=total, nom=nom))
                    # Même volume que la génération normale : c'est le réglage
                    # validé sur la radio.
                    await sauver_voix(phrase, voice_id, temp_mp3,
                                      pitch=self._robot_pitch(),
                                      rate=self._rate_effectif(voice_id))
                    self._dire(t("etat_generation_wav", fait=traite,
                                 total=total, nom=nom))
                    convertir_en_wav(temp_mp3, temp_wav)
                    self._appliquer_robot(temp_wav)
                    ameliorer_niveau_wav(temp_wav)
                    appliquer_niveau(temp_wav, self._niveau)
                    os.replace(temp_wav, final_wav)
                    faits += 1
                    reseau_suite = 0
                except Exception as e:
                    # Une phrase qui rate ne doit pas priver des 188 autres,
                    # sauf si le réseau est coupé : là, inutile d'insister.
                    raison = raison_lisible(e)
                    echecs.append((nom, raison))
                    if raison == t("err_reseau"):
                        reseau_suite += 1
                        if reseau_suite >= 3:
                            coupe_reseau = True
                            break
                    else:
                        reseau_suite = 0
                finally:
                    for reste in (temp_mp3, temp_wav):
                        try:
                            os.remove(reste)
                        except OSError:
                            pass

                self.after(0, lambda v=traite / total: self.progress.set(v))
                # Arrêt demandé : on garde « Arrêt demandé… » à l'écran plutôt
                # que d'afficher gaiement une progression.
                if stop is not None and stop.is_set():
                    arrete = True
                    break
                self._dire(t("etat_avance", fait=traite, total=total, nom=nom,
                             s="s" if traite > 1 else ""))
        finally:
            shutil.rmtree(travail, ignore_errors=True)

        # On laisse la barre complète visible, comme la génération normale.
        await asyncio.sleep(PAUSE_LEDS)
        self.after(0, lambda: self.progress.reset())
        self._dire("")

        sortie_texte = chemin_lisible(sortie)
        detail = "\n".join(f"• {nom} : {raison}"
                           for nom, raison in echecs[:6])
        if len(echecs) > 6:
            detail += "\n" + t("msg_autres", n=len(echecs) - 6)
        if coupe_reseau:
            detail = t("msg_reseau_coupe") + "\n" + detail

        if arrete:
            texte = t("msg_sons_arrete", n=faits,
                      s="s" if faits > 1 else "", dossier=sortie_texte)
            if echecs:
                texte += "\n\n" + t("msg_sons_problemes",
                                    problemes=len(echecs),
                                    s2="s" if len(echecs) > 1 else "",
                                    detail=detail)
            icone = "attention"
        elif echecs:
            texte = t("msg_sons_bilan", reussis=faits,
                      s1="s" if faits > 1 else "",
                      total=total + nb_refuses,
                      problemes=len(echecs),
                      s2="s" if len(echecs) > 1 else "",
                      detail=detail)
            icone = "erreur"
        else:
            texte = t("msg_sons_succes", n=faits,
                      s="s" if faits > 1 else "", dossier=sortie_texte)
            if dossier_sd:
                texte += "\n\n" + t("msg_sons_copier", langue=dossier_sd)
            icone = "succes"

        if depuis_cache:
            # Dire la vérité : la liste n'a pas pu être rafraîchie, on a
            # travaillé sur la copie enregistrée lors d'un précédent essai.
            texte += "\n\n" + t("msg_sons_cache")

        self.after(0, lambda: self._message(
            texte, icone=icone,
            boutons=[(t("ouvrir_dossier"),
                      lambda: self._ouvrir_dossier(sortie)),
                     (t("fermer"), None)]))


    # ------------------------------------------------------------------
    # L'écran de la maquette (étape 2)
    # ------------------------------------------------------------------
    # Les cotes sont celles de maquette/apercu.py, écrites dans l'espace
    # 1024 × 1024 de la carcasse, puis multipliées par la taille de la
    # fenêtre / 1024 (820 px, ou moins sur un écran court). Les objets sont
    # les mêmes qu'avant (combo_voice, btn_ajouter, lignes…) : le moteur ne
    # voit pas la différence.
    NOIR_V2 = "#000405"
    RAYURE_V2 = "#0B1517"
    ACCENT_V2 = "#0FBBD0"
    TEXTE_V2 = "#E9F4F6"
    GRIS_V2 = "#7C959A"
    CARTE_V2 = "#000000"
    BORD_V2 = "#3A5A5E"
    # La couleur d'un carré à cocher quand la souris le survole. Celle de la
    # maquette (ACCENT) : le carré se remplit de cyan, comme s'il était coché.
    # Une seule constante pour les deux cases (lignes, en-tête).
    SURVOL_CASE_V2 = ACCENT_V2

    def _pv(self, valeur):
        """Une cote de l'image 1024 × 1024, en pixels de la fenêtre."""
        return max(1, int(round(valeur * (self._format / 1024))))

    def _couleur_v2(self, x, y):
        """La couleur de la carcasse à cet endroit, pour un widget qui s'y pose."""
        g = min(self._pv(x), self._format - 1)
        ht = min(self._pv(y), self._format - 1)
        r, v, b = self._fond_image.getpixel((g, ht))[:3]
        return f"#{r:02x}{v:02x}{b:02x}"

    def _image_v2(self, x, y, l, h):
        """Un morceau de carcasse, pour poser un texte sans rectangle noir."""
        g, ht = self._pv(x), self._pv(y)
        bande = self._fond_image.crop((g, ht, g + self._pv(l), ht + self._pv(h)))
        photo = ImageTk.PhotoImage(bande)
        canevas = tk.Canvas(self, width=bande.width, height=bande.height,
                            highlightthickness=0, bd=0)
        canevas.create_image(0, 0, image=photo, anchor="nw")
        canevas.photo = photo
        canevas.place(x=g, y=ht)
        return canevas

    def _decor_v2(self, x, y, l, h):
        """Un morceau de carcasse, prêt à servir de fond à un bouton."""
        bande = self._fond_image.crop((self._pv(x), self._pv(y),
                                       self._pv(x + l), self._pv(y + h)))
        return ImageTk.PhotoImage(bande)

    def _texte_v2(self, x, y, l, h, contenu, couleur, taille, ancre="w"):
        canevas = self._image_v2(x, y, l, h)
        item = canevas.create_text(
            0 if ancre == "w" else canevas.winfo_reqwidth() // 2,
            self._pv(h) // 2, text=contenu, fill=couleur, anchor=ancre,
            font=(FONT_MAIN, taille))
        # Même précaution que pour les boutons : un titre long (russe,
        # portugais) ou une échelle Windows plus grande ne doit pas sortir de
        # la case. On baisse la taille jusqu'à ce qu'il tienne.
        while taille > 7:
            boite = canevas.bbox(item)
            if boite and boite[2] - boite[0] <= canevas.winfo_reqwidth() - 2:
                break
            taille -= 1
            canevas.itemconfigure(item, font=(FONT_MAIN, taille))
        # Les titres fixes (LANGUE, VOIX) doivent pouvoir être retraduits
        # quand on change de langue : on garde de quoi les retrouver.
        canevas._item = item
        return canevas

    def _format_fenetre(self):
        """La taille de la fenêtre : 820, ou moins si l'écran est court.

        Tout l'écran est coté sur un carré de 1024 ; on garde donc un carré,
        à l'échelle qui tient sur l'écran. C'est ce que faisait la 1.5.1 en
        réduisant la fenêtre sur un portable ; sans cela, « Let's Go » et
        le « ? » passaient sous le bord, et il fallait une pastille pour
        changer de taille. On ne descend jamais sous 640 px : en dessous,
        les textes deviendraient illisibles.

        `VOXPACK_FORMAT` force la taille (par exemple 704), pour voir
        l'écran d'un portable sans toucher à la résolution du sien.
        """
        force = os.environ.get("VOXPACK_FORMAT", "").strip()
        if force.isdigit():
            return int(max(640, min(1024, int(force))))
        marge = 96 if sys.platform == "darwin" else 72
        dispo = min(self.winfo_screenheight() - marge,
                    self.winfo_screenwidth() - 40)
        return int(max(640, min(820, dispo)))

    def _charger_carcasse(self):
        """Le fond dessiné de l'écran, ou un fond uni s'il manque.

        La carcasse est une image livrée avec l'application, pas une donnée
        vitale : si elle manque (paquet incomplet, fichier abîmé), on ouvre
        quand même, sur un fond uni. On perd la texture, aucun texte ; une
        exception au démarrage, elle, ne laisserait rien du tout.
        """
        chemin = trouver_ressource("carcasse.webp")
        try:
            image = Image.open(chemin)
            image.load()
            if image.size != (self._format, self._format):
                image = image.resize((self._format, self._format),
                                     Image.LANCZOS)
            self._carcasse = chemin
            return image
        except Exception:
            self._carcasse = None
            return Image.new("RGB", (self._format, self._format), "#0A1214")

    def _construire_ecran_v2(self):
        # Windows : Tk rend les polices en points (1 pt = 1,33 px à 96 dpi,
        # 2 px à 150 %), alors que toute la mise en page est en pixels. Sans
        # cela, le texte est 1,5 à 2 fois trop gros pour sa case et déborde.
        # On aligne les points sur les pixels, comme sur le Mac.
        if sys.platform.startswith("win"):
            try:
                self.tk.call("tk", "scaling", 1.0)
            except tk.TclError:
                pass

        # Pour éprouver l'écran comme sur un autre système, cette variable
        # force l'échelle (voir tests/v2_adaptation.py). Elle passe après le
        # réglage Windows, donc elle peut le remplacer.
        echelle = os.environ.get("VOXPACK_ECHELLE", "").strip()
        if echelle:
            try:
                self.tk.call("tk", "scaling", float(echelle))
            except (tk.TclError, ValueError):
                pass

        # La maquette n'a qu'une police : Avenir Next. La 1.5.1 prend celle
        # du système (San Francisco), plus épaisse aux petites tailles — c'est
        # ce qui donnait l'impression de gras. On reprend celle de la maquette.
        choisir_police(["Avenir Next", "Helvetica Neue", "Arial"])
        self._lecture = None
        self._apercu_no = 0
        self._format = self._format_fenetre()
        # La fenêtre principale a posé un minsize pour la 1.5.1 : sans le
        # reprendre, elle garderait 820 de large et la carcasse réduite
        # laisserait une bande noire à droite.
        self.minsize(self._format, self._format)
        self.resizable(False, False)
        ecran_l, ecran_h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{self._format}x{self._format}"
                      f"+{max((ecran_l - self._format) // 2, 0)}"
                      f"+{max((ecran_h - self._format) // 2 - 15, 0)}")

        image = self._charger_carcasse()
        self._fond_image = image
        self._fond_photo = ImageTk.PhotoImage(image)
        self._fond = tk.Label(self, image=self._fond_photo, bd=0,
                              highlightthickness=0)
        self._fond.place(x=0, y=0, width=self._format, height=self._format)
        self._fond.lower()
        self.configure(fg_color=self.NOIR_V2)

        self._poser_panneau_v2()
        self._poser_liste_v2()
        self._poser_bandeau_v2()
        self._poser_coin_v2()

        self._robot_survole = None
        self.after(150, self._veiller_survol_robot)

    # -- le panneau de gauche -----------------------------------------
    def _ouvrir_langues_v2(self):
        """La fenêtre de choix des langues, comme dans la maquette."""
        fenetre = getattr(self, "_fenetre_langues", None)
        if fenetre is not None and fenetre.winfo_exists():
            fenetre.lift()
            return
        self._fenetre_langues = FenetreLanguesV2(
            self, LANGUE_UI, self._choisir_langue_v2)
        self._surveiller_activation()

    def _choisir_langue_v2(self, code):
        if code != LANGUE_UI:
            self.changer_langue_ui(code)

    def _aligner_entetes_v2(self, essai=0):
        """Les titres NOM et PHRASE, calés sur les colonnes dessinées.

        Ils étaient mesurés sur les champs, parce que les champs décidaient de
        leur place. Les colonnes sont maintenant fixes : les titres le sont
        aussi. La mesure ne sert plus qu'à centrer la case « tout cocher » sur
        la ligne des titres.
        """
        if not hasattr(self, "_toile"):
            return
        p = self._pv
        self.lbl_col_nom.place(x=p(340 + 40), y=p(200))
        self.lbl_col_phrase.place(x=p(340 + 257), y=p(200))
        self._trait_colonnes.place(x=p(340 + 241), y=p(214))
        self.update_idletasks()
        titre = self.lbl_col_nom
        centre = titre.winfo_y() + titre.winfo_height() // 2
        self._toutes_v2.place(
            x=p(346),
            y=centre - self._toutes_v2.winfo_reqheight() // 2)

    def _niveau_change(self, valeur):
        self._niveau = int(valeur)
        self._reglages["niveau"] = self._niveau
        self._reglages_bientot()
        self._maj_titres_v2()

    def _allure_change(self, valeur):
        self._allure = int(valeur)
        self._reglages["allure"] = self._allure
        self._reglages_bientot()
        self._maj_titres_v2()

    def _reglages_bientot(self):
        """Programme l'écriture des réglages dans un instant.

        Les curseurs appellent leur commande à chaque pas : écrire le fichier
        chaque fois faisait des dizaines d'écritures pendant un glissement.
        On attend une demi-seconde sans mouvement ; la valeur, elle, est déjà
        à jour en mémoire pour tout le reste du programme.
        """
        if self._reglages_attente is not None:
            try:
                self.after_cancel(self._reglages_attente)
            except Exception:
                pass
        self._reglages_attente = self.after(
            500, self._ecrire_reglages_maintenant)

    def _ecrire_reglages_maintenant(self):
        self._reglages_attente = None
        ecrire_reglages(self._reglages)

    def _maj_titres_v2(self):
        """Les deux titres du panneau : « NIVEAU · −3 dB », « ALLURE · +5 % »."""
        def valeur_texte(valeur, unite):
            if valeur == 0:
                return f"0 {unite}"
            signe = "+" if valeur > 0 else "−"
            return f"{signe}{abs(valeur)} {unite}"

        self._titre_niveau.configure(
            text=f"{t('niveau').upper()} · {valeur_texte(self._niveau, 'dB')}")
        self._titre_allure.configure(
            text=f"{t('allure').upper()} · {valeur_texte(self._allure, '%')}")

    def _poser_panneau_v2(self):
        p = self._pv
        # Le voyant des sons système, au-dessus de LANGUE comme la case de la
        # maquette. Il n'agit pas : la création se lance par le menu, et le
        # voyant dit seulement où en est le travail. Le mot « System » est
        # celui du dossier de la carte, le même dans toutes les langues
        # (vérifié sur le CSV chinois : Path = SYSTEM).
        self._voyant_systeme = VoyantV2(
            self, max(14, p(22)), self._couleur_v2(64, 109))
        self._voyant_systeme.place(x=p(64), y=p(109))
        self._texte_v2(92, 108, 200, 24, "SYSTEM", self.ACCENT_V2, p(17))

        self._titre_langue = self._texte_v2(
            64, 196, 230, 22, t("langue").upper(),
            self.ACCENT_V2, p(15))
        # La langue ne s'ouvre pas d'ici : on en change par le menu de la
        # fenêtre (entrée « Langue »). Le champ est donc dessiné comme un
        # petit écran — verre, balayage, texte allumé — pour qu'on n'attende
        # pas un menu derrière lui.
        bande_langue = self._fond_image.crop(
            (p(64), p(222), p(64) + p(230), p(222) + p(40)))
        self._champ_langue = EcranV2(
            self, bande_langue, t("langue_" + LANGUE_UI),
            fonte=(FONT_MAIN, p(17)))
        self._champ_langue.place(x=p(64), y=p(222))

        self._titre_voix = self._texte_v2(
            64, 274, 230, 22, t("voix").upper(),
            self.ACCENT_V2, p(15))
        premier = voix_de_la_langue(self.langue)
        self.combo_voice = ChampVoixV2(
            self, p(230), p(40), self.NOIR_V2,
            premier[0][0] if premier else "",
            commande=self._voix_changee,
            couleur=self.TEXTE_V2, fonte=(FONT_MAIN, p(17)))
        self.combo_voice.place(x=p(64), y=p(300))
        self.combo_voice.configure(
            values=[etiquette for etiquette, _id in premier])
        self._remplir_voix()

        # La carte noire des réglages (61, 361) → (291, 790) est déjà dans la
        # carcasse, avec son coin haut-droit coupé à 45° et son liseré cyan.
        # On ne peint plus de rectangle par-dessus : il écrasait ce dessin.

        # NIVEAU : le curseur du son. Le titre est posé sur un morceau de
        # carcasse — un fond noir uni recouvrirait le biseau du coin.
        bande_niveau = self._fond_image.crop(
            (p(61), p(370), p(61) + p(230), p(370) + p(22)))
        self._titre_niveau = TexteCarcasse(
            self, bande_niveau, "", self.ACCENT_V2, (FONT_MAIN, p(15)),
            ancre="center")
        self._titre_niveau.place(x=p(61), y=p(370))
        self._niveau_v2 = CurseurV2(
            self, p(198), p(34), self.CARTE_V2, -6, 6, self._niveau,
            commande=self._niveau_change)
        self._niveau_v2.place(x=p(78), y=p(398))

        # ALLURE : la vitesse de la voix.
        self._titre_allure = tk.Label(
            self, bg=self.CARTE_V2, fg=self.ACCENT_V2,
            font=(FONT_MAIN, p(15)), anchor="center")
        self._titre_allure.place(x=p(61), y=p(440), width=p(230))
        self._allure_v2 = CurseurV2(
            self, p(198), p(34), self.CARTE_V2, -100, 100, self._allure,
            commande=self._allure_change, degrade=False)
        self._allure_v2.place(x=p(78), y=p(466))

        self.cadre_robot = tk.Frame(self, bg=self.CARTE_V2)
        self.cadre_robot.place(x=p(61), y=p(504), width=p(230), height=p(62))
        self.lbl_robot = ctk.CTkLabel(self.cadre_robot, text="",
                                      bg_color=self.CARTE_V2,
                                      text_color=self.GRIS_V2,
                                      font=(FONT_MAIN, p(15)))
        self.lbl_robot.pack()
        # Les quatre cases s'alignent sur la largeur des boutons (78 → 276).
        self._boutons_robot = {}
        # Alignées sur la piste des curseurs (qui a une marge de 7 %), pas
        # sur le bord des boutons.
        marge = p(198) * 0.07
        gauche = p(78) + marge
        droite = p(78) + p(198) - marge
        ecart = (droite - gauche - p(20)) / 3
        cote = max(12, p(22))
        for i, numero in enumerate(ROBOTS):
            # Quatre voyants comme celui de SYSTEM : cyan pour les robots,
            # rouge pour HAL 9000. Éteints au repos, allumés sur le choix.
            led = VoyantV2(
                self, cote, self.CARTE_V2,
                couleurs=(VOYANT_ROUGE if numero == 4 else VOYANT_CYAN))
            centre = gauche + i * ecart + p(20) / 2
            led.place(x=round(centre - cote / 2),
                      y=round(p(546) + p(20) / 2 - cote / 2))
            led.configure(cursor=CURSEUR_MAIN)
            led.bind("<Button-1>",
                     lambda e, n=numero: self._choisir_robot(n))
            self._boutons_robot[numero] = led
        self._maj_robot()
        self._maj_titres_v2()

        tk.Frame(self, bg="#1B2F33", height=1).place(
            x=p(78), y=p(574), width=p(196), height=1)

        for i, (libelle, action, icone) in enumerate((
                (t("ajouter"), self.ajouter_ligne, "plus"),
                (t("supprimer"), self.supprimer_selection, "moins"),
                (t("ecouter"), self.ecouter_selection, "lecture"))):
            bouton = BoutonV2(
                self, libelle, p(78), p(592 + i * 66), p(198), p(50),
                fond=self.CARTE_V2, contour=True, espace=True, icone=icone,
                biseau=p(10), fonte=(FONT_MAIN, p(16)), commande=action)
            if i == 0:
                self.btn_ajouter = bouton
            elif i == 1:
                self.btn_supprimer = bouton
            else:
                self.btn_apercu = bouton

    # -- la liste ------------------------------------------------------
    def _poser_liste_v2(self):
        p = self._pv
        self.lbl_col_nom = tk.Label(
            self, text=t("nom").upper(), bg=self.NOIR_V2,
            fg=self.TEXTE_V2, anchor="w", font=(FONT_MAIN, p(20)))
        self.lbl_col_nom.place(x=p(378), y=p(200))
        self.lbl_col_phrase = tk.Label(
            self, text=t("phrase").upper(), bg=self.NOIR_V2,
            fg=self.TEXTE_V2, anchor="w", font=(FONT_MAIN, p(20)))
        self.lbl_col_phrase.place(x=p(566), y=p(200))

        # Le trait cyan sous l'en-tête et le trait vertical des deux colonnes.
        tk.Frame(self, bg=self.ACCENT_V2).place(
            x=p(340), y=p(247), width=p(645), height=1)
        self._trait_colonnes = tk.Frame(self, bg="#17343A", width=1)
        self._trait_colonnes.place(x=p(552), y=p(214), width=1, height=p(32))

        # Les quatre équerres aux coins de la liste.
        for x, y, points in (
                (328, 190, ((2, 18), (2, 2), (18, 2))),
                (960, 190, ((2, 2), (18, 2), (18, 18))),
                (328, 794, ((2, 2), (2, 18), (18, 18))),
                (960, 794, ((2, 18), (18, 18), (18, 2)))):
            coin = self._image_v2(x, y, 20, 20)
            coin.create_line(*[c for point in points
                               for c in (p(point[0]), p(point[1]))],
                             fill=self.ACCENT_V2, width=1)
            coin.place(x=p(x), y=p(y))

        # La liste est un canevas : les lignes sont dessinées, pas
        # construites. Un seul objet du canevas est un vrai widget — le champ
        # de la cellule en cours d'édition (voir _editer_ligne).
        self._largeur_liste = p(638)
        self._hauteur_liste = p(538)
        self._hauteur_ligne = p(46)
        self._x_case = p(6)
        self._x_case_fin = p(30)
        self._x_nom = p(40)
        self._x_nom_fin = p(236)
        self._x_sep = p(241)
        self._x_phrase = p(257)
        self._x_droite = p(616)
        self._pas_molette = p(46)          # une ligne par cran
        self._reste_molette = 0.0
        self._edition = None
        self._total_liste = 0
        self._police_liste = tkfont.Font(family=FONT_MAIN, size=p(21))
        self._police_souci = tkfont.Font(family=FONT_MAIN, size=p(12))

        self._toile = tk.Canvas(
            self, bg=self.NOIR_V2, highlightthickness=0,
            width=self._largeur_liste, height=self._hauteur_liste,
            yscrollincrement=1, takefocus=0)
        self._toile.place(x=p(340), y=p(256))
        # La barre est dessinée elle aussi : la barre de customtkinter
        # apparaissait comme un trait clair, et le pouce ne suivait pas le
        # pouce du canevas.
        self._barre = tk.Canvas(
            self, width=p(8), height=self._hauteur_liste, bg=self.NOIR_V2,
            highlightthickness=0, cursor=CURSEUR_MAIN)
        self._barre.place(x=p(340 + 630), y=p(256))
        self._pouce = self._barre.create_rectangle(
            0, 0, p(6), p(40), fill="#183335", outline="")
        self._toile.configure(yscrollcommand=self._maj_barre_liste)
        self._barre.bind("<Button-1>", self._glisser_barre)
        self._barre.bind("<B1-Motion>", self._glisser_barre)

        self._toile.bind("<Button-1>", self._clic_liste)
        self._toile.bind("<Shift-Button-1>", self._clic_case_maj)
        self._toile.bind("<MouseWheel>", self._molette_liste)
        self._toile.bind("<Button-4>", self._molette_liste)
        self._toile.bind("<Button-5>", self._molette_liste)
        # Plus de parcours au clavier dans la liste (décision de Richard,
        # 4 novembre au soir) : la souris ouvre le champ, et rien d'autre.

        # La case de l'en-tête coche ou décoche toute la liste, comme dans
        # la maquette. Les boutons « Tout » et « Rien » de la 1.5.1 ne sont
        # plus affichés : la case appelle les mêmes méthodes.
        self._toutes_v2 = ctk.CTkCheckBox(
            self, text="", width=p(24), height=p(24),
            checkbox_width=p(20), checkbox_height=p(20), corner_radius=0,
            border_width=1, border_color=self.BORD_V2,
            fg_color=self.ACCENT_V2, hover_color=self.SURVOL_CASE_V2,
            checkmark_color=self.NOIR_V2, bg_color=self.NOIR_V2,
            command=self._basculer_tout_v2)
        self._toutes_v2.place(x=p(346), y=p(199))

    def _basculer_tout_v2(self):
        """La case de l'en-tête : tout cocher, ou tout décocher."""
        if self._toutes_v2.get():
            self.tout_cocher()
        else:
            self.rien_cocher()

    def _sync_toutes_v2(self):
        """L'en-tête suit les cases : cochée seulement si tout l'est."""
        case = getattr(self, "_toutes_v2", None)
        if case is None or not case.winfo_exists():
            return
        if self.lignes and all(l["coche"] for l in self.lignes):
            case.select()
        else:
            case.deselect()
        self._maj_total_liste()

    # -- le bandeau du bas --------------------------------------------
    def _poser_bandeau_v2(self):
        p = self._pv
        self.btn_letsgo = BoutonV2(
            self, t("lets_go"), p(60), p(862), p(250), p(56),
            decor=self._decor_v2(60, 862, 250, 56),
            fond=self._couleur_v2(60, 862), plein=True, biseau=p(16),
            fonte=(FONT_MAIN, p(22)), commande=self._lancer_generation_v2)

        self._total_v2 = 0
        self.progress = BarreV2(self, largeur=p(560), hauteur=p(8),
                                fond=self._couleur_v2(340, 872),
                                commande=self._maj_compteur_v2)
        self.progress.place(x=p(340), y=p(866))
        self.progress.set(0.0)

        # Le compteur, à droite de la barre : « 0 / 44 ».
        bande = self._fond_image.crop(
            (p(905), p(858), p(985), p(892)))
        self.lbl_compteur = TexteCarcasse(self, bande, "", self.GRIS_V2,
                                          (FONT_MAIN, p(14)), ancre="e")
        self.lbl_compteur.place(x=p(905), y=p(858))

        # Le message de génération, sous la barre : un second petit écran,
        # comme celui de la langue. Au repos, il affiche « waiting... ».
        bande_etat = self._fond_image.crop(
            (p(340), p(876), p(900), p(906)))
        self.lbl_etat = EcranV2(
            self, bande_etat, "waiting...", fonte=(FONT_MAIN, p(12)),
            ancre="w", cadre=2)
        self.lbl_etat.place(x=p(340), y=p(876))

    def _maj_compteur_v2(self, valeur=0.0):
        """Tient le compteur à jour : « faits / à faire »."""
        total = getattr(self, "_total_v2", 0)
        if not total:
            self._ecrire_compteur(0, 0)
            return
        self._ecrire_compteur(
            int(round(max(0.0, min(1.0, valeur)) * total)), total)

    def _ecrire_compteur(self, fait, total):
        try:
            self.lbl_compteur.configure(text=f"{fait} / {total}")
        except Exception:
            pass

    def _total_a_faire(self):
        """Le nombre de fichiers à faire : les lignes cochées, et rien d'autre."""
        return sum(1 for ligne in self.lignes if ligne["coche"])

    def _maj_total_liste(self):
        """« À faire » suit les cases : cocher, décocher, charger, importer.

        Rien de coché, rien à faire : « 0 / 0 ». Pendant un travail, c'est
        lui qui commande la progression : on n'y touche pas.
        """
        if getattr(self, "_genere", False):
            return
        self._total_v2 = self._total_a_faire()
        try:
            self.progress.set(0.0)
        except Exception:
            pass
        self._maj_compteur_v2(0.0)

    def _lancer_generation_v2(self):
        """Le Let's Go de l'écran : il compte les lignes, puis lance le moteur."""
        cochees = [l for l in self.lignes if l["coche"]]
        self._total_v2 = len(cochees)
        self.start_generation()
        if not self._genere:
            # Dossier annulé, ou rien à fabriquer : on revient au total.
            self._maj_total_liste()

    # -- les coins : ?, signature, ko-fi ------------------------------
    def _poser_coin_v2(self):
        p = self._pv
        self.btn_aide = BoutonV2(
            self, "?", p(930), p(912), p(42), p(42),
            fond=self._couleur_v2(930, 912), contour=True, biseau=p(8),
            fonte=(FONT_MAIN, p(20)), commande=self._ouvrir_aide)

        # La signature et le ko-fi, centrés dans la case de la plaque.
        self.signature = self._image_v2(820, 56, 172, 30)
        self._item_signature = self.signature.create_text(
            p(172) // 2, p(30) // 2, text="ritchy-lab", fill=self.ACCENT_V2,
            anchor="center", font=(FONT_MAIN, p(21)))
        self.signature.configure(cursor=CURSEUR_MAIN)
        # Le même survol que le ko-fi : le mot s'éclaire.
        self.signature.bind(
            "<Enter>", lambda e: self.signature.itemconfigure(
                self._item_signature, fill=CYAN_CLAIR))
        self.signature.bind(
            "<Leave>", lambda e: self.signature.itemconfigure(
                self._item_signature, fill=self.ACCENT_V2))
        self.signature.bind(
            "<Button-1>",
            self._clic_sans_glisser(lambda: self._ouvrir_lien(URL_SITE)))

        self.kofi = self._image_v2(820, 88, 172, 36)
        self.kofi.configure(cursor=CURSEUR_MAIN)
        fonte = (FONT_MAIN, p(21))
        hauteur = p(22)
        largeur = 0
        self._tasse_v2 = None
        self._tasse_survol_v2 = None
        try:
            tasse = Image.open(trouver_ressource("ko-fi.png"))
            largeur = int(tasse.width * hauteur / tasse.height)
            self._tasse_v2 = ImageTk.PhotoImage(
                tasse.resize((largeur, hauteur)))
        except Exception:
            largeur = 0
        # Le survol : la même tasse, le cœur orange. Même largeur que la
        # tasse normale pour que le mot « ko-fi » ne bouge pas d'un pixel.
        if largeur:
            try:
                survol = Image.open(trouver_ressource("ko-fi-survol.png"))
                self._tasse_survol_v2 = ImageTk.PhotoImage(
                    survol.resize((largeur, hauteur)))
            except Exception:
                pass
        largeur_mot = tkfont.Font(font=fonte).measure("ko-fi")
        total = largeur + (p(8) if largeur else 0) + largeur_mot
        gauche = (p(172) - total) // 2
        self._item_tasse = None
        if largeur:
            self._item_tasse = self.kofi.create_image(
                gauche, p(18), image=self._tasse_v2, anchor="w")
            gauche += largeur + p(8)
        self._item_mot = self.kofi.create_text(
            gauche, p(18), text="ko-fi", fill=self.ACCENT_V2, anchor="w",
            font=fonte)

        def survoler(_evenement):
            if self._tasse_survol_v2 is not None:
                self.kofi.itemconfigure(self._item_tasse,
                                        image=self._tasse_survol_v2)
            self.kofi.itemconfigure(self._item_mot, fill=CYAN_CLAIR)

        def quitter(_evenement):
            if self._tasse_v2 is not None:
                self.kofi.itemconfigure(self._item_tasse,
                                        image=self._tasse_v2)
            self.kofi.itemconfigure(self._item_mot, fill=self.ACCENT_V2)

        self.kofi.bind("<Enter>", survoler)
        self.kofi.bind("<Leave>", quitter)
        self.kofi.bind("<Button-1>", self._clic_sans_glisser(
            self._ouvrir_soutien))


    # ------------------------------------------------------------------
    # Habillage v2 — étape 1 : la fenêtre
    # ------------------------------------------------------------------
    # Rien du moteur n'est réécrit ici. On ne change que la fenêtre : plus de
    # barre de titre, une pastille de fermeture, le déplacement en tirant le
    # fond, et le menu à l'intérieur. Les commandes sont exactement celles de
    # _menu_fichier (voir docs/v2-passation.md, §7 et §8).
    PANNEAU_FOND = "#0A1416"
    PANNEAU_BORD = "#3E5559"
    PANNEAU_SURVOL = "#14313A"

    def _habiller_fenetre(self):
        self._menu_habillage = None
        self._deplacement = None

        # Pas de withdraw() ici : c'est lui qui empêchait la fenêtre de
        # devenir la fenêtre active (donc de recevoir le clavier). Tk recrée
        # la fenêtre sans cadre quand on bascule overrideredirect.
        self.overrideredirect(True)
        if sys.platform == "darwin":
            # Une fenêtre sans barre de titre ne peut pas devenir la fenêtre
            # active : le clavier n'arrive alors dans aucun champ, et il est
            # impossible d'écrire une phrase. Le style « plain » de Tk règle
            # cela ; sans lui, la liste se remplit mais ne se corrige pas.
            try:
                self.tk.call("::tk::unsupported::MacWindowStyle",
                             "style", self._w, "plain", "none")
            except Exception:
                pass
        self.lift()
        if sys.platform == "darwin":
            try:
                from AppKit import NSApp
                NSApp.activateIgnoringOtherApps_(True)
            except Exception:
                pass
        try:
            self.attributes("-topmost", True)
            self.after(1200, self._relacher_topmost)
        except Exception:
            pass
        self.focus_force()

        self._poser_pastille()
        self._poser_bouton_menu()

        # Le fond de la fenêtre sert de poignée : on ne déplace que si le
        # clic ne tombe pas sur un champ, un bouton ou la liste.
        self.bind("<ButtonPress-1>", self._prendre_fenetre, add="+")
        self.bind("<B1-Motion>", self._tirer_fenetre, add="+")
        self.bind("<ButtonRelease-1>", self._relacher_fenetre, add="+")
        self.bind("<Motion>", self._survol_sans_bouton, add="+")
        self.bind("<FocusIn>",
                  lambda e: setattr(self, "_deplacement", None), add="+")
        self.bind("<Escape>", self._echapper, add="+")
        # Deux touches seulement : haut et bas font défiler la liste d'une
        # ligne. Le reste du parcours clavier est retiré (décision de
        # Richard, 4 novembre au soir).
        self.bind("<Up>", lambda e: self._fleche_liste(-1), add="+")
        self.bind("<Down>", lambda e: self._fleche_liste(1), add="+")

    def _relacher_topmost(self):
        try:
            self.attributes("-topmost", False)
        except Exception:
            pass

    def _poser_pastille(self):
        """La pastille rouge de fermeture, en creux dans le métal.

        Elle est alignée sur le voyant « System » (même bord gauche), et
        dessinée avec un anneau sombre, une ombre en haut et une lumière en
        bas : elle paraît enfoncée dans la carcasse.
        """
        cote = max(12, self._pv(20))
        pastille = tk.Canvas(self, width=cote, height=cote,
                             bg=self._couleur_v2(64, 45),
                             highlightthickness=0, bd=0, cursor=CURSEUR_MAIN)
        pastille.create_oval(0, 0, cote, cote, fill="#2B0D0B", outline="")
        face = pastille.create_oval(1, 1, cote - 1, cote - 1,
                                    fill="#A9352E", outline="")
        pastille.create_arc(1, 1, cote - 1, cote - 1, start=20, extent=140,
                            style="arc", outline="#5E1B17", width=1)
        pastille.create_arc(1, 1, cote - 1, cote - 1, start=200, extent=140,
                            style="arc", outline="#D25850", width=1)

        def fermer(_evenement):
            self._fermer()
            return "break"

        pastille.bind("<Button-1>", fermer)
        pastille.bind("<Enter>",
                      lambda e: pastille.itemconfigure(face, fill="#FF3B30"))
        pastille.bind("<Leave>",
                      lambda e: pastille.itemconfigure(face, fill="#A9352E"))
        pastille.place(x=self._pv(64), y=self._pv(45))
        self._pastille = pastille

    def _poser_bouton_menu(self):
        """Le menu, dans la fenêtre : trois traits, comme sur la maquette."""
        p = self._pv
        # Les trois traits, juste à droite de la pastille rouge, comme le
        # second bouton de la maquette.
        cote = max(14, self._pv(22))
        canevas = tk.Canvas(self, width=cote, height=cote,
                            bg=self._couleur_v2(104, 45),
                            highlightthickness=0, bd=0, cursor=CURSEUR_MAIN,
                            takefocus=0)
        milieu = cote / 2
        # Les trois traits : un peu plus écartés qu'avant (3,2 px les
        # serraient trop), pour qu'on lise un menu et non un pointillé.
        largeur = cote * 0.33
        pas = cote * 0.255
        traits = []
        for rang in (-1, 0, 1):
            traits.append(canevas.create_line(
                milieu - largeur, milieu + rang * pas,
                milieu + largeur, milieu + rang * pas,
                fill=self.TEXTE_V2, width=1.5))
        canevas.bind("<Button-1>", self._clic_bouton_menu)
        canevas.place(x=self._pv(105), y=self._pv(44))
        self._bouton_menu = canevas

    def _clic_bouton_menu(self, _evenement=None):
        self._ouvrir_menu_fenetre()
        return "break"

    def _ouvrir_menu_fenetre(self):
        """Ouvre (ou referme) le menu posé dans la fenêtre."""
        if self._menu_habillage is not None:
            self._fermer_menus()
            return
        # Le bouton du menu ne laisse pas passer le clic (il renvoie
        # « break » pour ne pas déplacer la fenêtre) : c'est donc ici qu'on
        # referme la fenêtre des langues si elle est restée ouverte.
        self._fermer_langues()
        entrees = [
            (t("menu_langue"), self._ouvrir_langues_v2),
            None,
            (t("menu_exporter"), self.exporter_liste),
            (t("menu_importer"), self.importer_liste),
            (t("menu_defaut"), self.charger_liste_defaut),
            (t("menu_sons_systeme"), self.creer_sons_systeme),
            None,
            (t("aide_titre"), self._ouvrir_aide),
            (t("menu_quitter"), self._fermer),
        ]
        panneau = tk.Frame(self, bg=self.PANNEAU_FOND,
                           highlightbackground=self.PANNEAU_BORD,
                           highlightthickness=1)
        lignes = []
        for entree in entrees:
            if entree is None:
                tk.Frame(panneau, bg=self.PANNEAU_BORD, height=1).pack(
                    fill="x", pady=3)
                continue
            libelle, action = entree
            ligne = tk.Label(panneau, text=libelle, bg=self.PANNEAU_FOND,
                             fg=TEXT_WHITE, anchor="w", padx=14, pady=6,
                             font=(FONT_MAIN, max(11, self._pv(17))),
                             cursor=CURSEUR_MAIN, takefocus=0)
            ligne.pack(fill="x")
            ligne.bind("<Enter>",
                       lambda e, l=ligne: l.configure(bg=self.PANNEAU_SURVOL))
            ligne.bind("<Leave>",
                       lambda e, l=ligne: l.configure(bg=self.PANNEAU_FOND))
            ligne.bind("<Button-1>",
                       lambda e, a=action: self._choisir_menu(a))
            lignes.append(ligne)
        panneau.place(x=self._pv(17), y=self._pv(55))
        self._menu_habillage = panneau
        self._menu_lignes = lignes
        self._surveiller_activation()

    def _choisir_menu(self, action):
        self._fermer_menus()
        action()
        return "break"

    def _fermer_menus(self):
        """Referme le menu : un clic à côté ne doit jamais le laisser ouvert."""
        champ = getattr(self, "combo_voice", None)
        if champ is not None and hasattr(champ, "fermer"):
            champ.fermer()
        panneau = self._menu_habillage
        self._menu_habillage = None
        self._menu_lignes = []
        if panneau is not None and panneau.winfo_exists():
            panneau.destroy()

    def _fermer_langues(self):
        """Referme la fenêtre des langues si elle est ouverte ; dit si oui.

        Elle n'a plus de grab : c'est ce clic-là, ou Échap, qui la referme.
        """
        fenetre = getattr(self, "_fenetre_langues", None)
        if fenetre is not None and fenetre.winfo_exists():
            fenetre.fermer()
            return True
        return False

    def _fleche_liste(self, sens):
        """Les flèches haut et bas : une ligne de liste en plus ou en moins.

        Elles ne font rien pendant une saisie : dans un champ, les flèches
        déplacent le curseur de texte, et c'est ce qu'on attend.
        """
        focus = self.focus_get()
        if self._edition is not None or isinstance(focus, (tk.Entry, tk.Text)):
            return
        self._toile.yview_scroll(sens * self._hauteur_ligne, "units")
        return "break"

    def _echapper(self, _evenement=None):
        """Échap : referme l'alerte ouverte, puis la fenêtre des langues, puis les menus.

        L'alerte passe en premier : c'est la fenêtre du dessus, et c'est
        celle qu'on veut voir disparaître. Si elle n'a pas réussi à prendre
        le clavier (fenêtre sans cadre), c'est ce chemin-là qui la ferme.
        """
        _trace_echap("ECHAP recu")
        if self._fermer_derniere_alerte():
            return "break"
        if self._fermer_langues():
            return "break"
        self._fermer_menus()

    # -- quand on passe dans une autre application ---------------------
    def _surveiller_activation(self):
        """Veille sur le passage au second plan tant qu'un menu est ouvert.

        Le clic qui vient d'ouvrir le menu n'a pas encore rendu l'application
        active sur macOS : le premier contrôle attend donc un instant.
        """
        if getattr(self, "_veille_active", False):
            return
        self._veille_active = True
        self.after(400, self._veiller_activation)

    def _veiller_activation(self):
        try:
            fenetre = getattr(self, "_fenetre_langues", None)
            ouvert = (self._menu_habillage is not None
                      or (fenetre is not None and fenetre.winfo_exists()))
            if not ouvert:
                self._veille_active = False
                return
            if not application_activee(self):
                # On est passé dans une autre application : le menu et la
                # fenêtre des langues appartiennent à celle-ci, ils partent
                # avec elle. Pas de focus_force au retour : on ne reprend pas
                # la main sur l'application où l'on vient de cliquer.
                self._fermer_menus()
                fenetre = getattr(self, "_fenetre_langues", None)
                if fenetre is not None and fenetre.winfo_exists():
                    fenetre.fermer(reprendre_focus=False)
                self._veille_active = False
                return
        except tk.TclError:
            self._veille_active = False
            return
        self.after(300, self._veiller_activation)

    @staticmethod
    def _clic_sans_glisser(action):
        """Un lien : il agit, et l'appui ne déplace pas la fenêtre.

        Le binding de déplacement est posé sur la fenêtre et reçoit aussi les
        clics des enfants ; en renvoyant « break », on l'empêche de s'armer.
        """
        def cliquer(_evenement):
            action()
            return "break"

        return cliquer

    # -- déplacement de la fenêtre sans barre de titre -----------------
    def _interactif(self, widget):
        """Vrai si le clic vise un contrôle (champ, bouton, liste…).

        Les widgets dessinés en font partie : le binding de déplacement est
        posé sur la fenêtre et reçoit aussi les clics de ses enfants ; sans
        eux, appuyer sur « Let's Go » ou sur « Ajouter » armait le
        déplacement, et la fenêtre suivait la souris pendant le clic.
        """
        classes = (ctk.CTkButton, ctk.CTkEntry, ctk.CTkComboBox,
                   ctk.CTkCheckBox, ctk.CTkScrollableFrame, ctk.CTkScrollbar,
                   tk.Entry, tk.Text, tk.Scrollbar, tk.Listbox,
                   CurseurV2, BoutonV2, ChampVoixV2, BarreV2, TexteCarcasse,
                   EcranV2, VoyantV2)
        noeud = widget
        toile = getattr(self, "_toile", None)
        while noeud is not None and noeud is not self:
            if noeud is toile or isinstance(noeud, classes):
                return True
            noeud = getattr(noeud, "master", None)
        return False

    def _prendre_fenetre(self, evenement):
        self._fermer_menus()
        # La fenêtre des langues se referme comme un menu : au premier clic
        # ailleurs, et ce clic fait ce qu'il a à faire.
        self._fermer_langues()
        self._deplacement = None
        if self._interactif(evenement.widget):
            return
        self._deplacement = (evenement.x_root - self.winfo_x(),
                             evenement.y_root - self.winfo_y())

    def _tirer_fenetre(self, evenement):
        # Sans bouton enfoncé (relâchement perdu, fenêtre détruite sous le
        # clic), on ne déplace pas : c'est ce qui laissait l'application
        # collée à la souris après la fermeture de l'aide.
        if not (evenement.state & 0x0100) or not bouton_enfonce():
            self._deplacement = None
            return
        if self._deplacement is None:
            return
        dx, dy = self._deplacement
        self.geometry(f"+{evenement.x_root - dx}+{evenement.y_root - dy}")

    def _relacher_fenetre(self, _evenement=None):
        self._deplacement = None

    def _survol_sans_bouton(self, _evenement=None):
        """Un survol sans bouton enfoncé solde un déplacement resté armé."""
        if self._deplacement is not None and not bouton_enfonce():
            self._deplacement = None


if __name__ == "__main__":
    app = VoxPackApp()
    app.mainloop()