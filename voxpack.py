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
    import soundfile as sf
    import soxr

    donnees, taux = sf.read(source_mp3, dtype="float32")
    if donnees.ndim > 1:                       # au cas où la voix serait stéréo
        donnees = donnees.mean(axis=1)
    cible = FORMAT_EDGETX[0]
    if taux != cible:
        donnees = soxr.resample(donnees, taux, cible, quality="VHQ")
    # Le format est dit explicitement : sans cela, soundfile le devine d'après
    # l'extension, et refuse tout ce qui ne finit pas par .wav. Or les sons
    # système s'écrivent d'abord en « 0000.wav.tmp » (le temporaire doit rester
    # sur le même disque pour os.replace). Avec un nom en .tmp, les 212 sons
    # échouaient sur PC — « No format specified and unable to get format from
    # file extension » — alors que macOS passait par afconvert, qui s'en moque.
    sf.write(destination_wav, donnees, cible, subtype="PCM_16", format="WAV")


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
        "ring": 0, "dry": 1.0, "echo": ()},
}


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


def ameliorer_niveau_wav(chemin):
    """Coupe les silences, limite et normalise un WAV EdgeTX.

    Coupe + gain +6 dB + limiteur à avance de 5 ms, puis normalisation.
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

# La langue de l'interface commande celle des voix : il n'y a donc que deux
# fichiers utiles. « en » correspond à en-GB, le paquet anglais d'EdgeTX (le
# dépôt ne se sert que de celui-là pour construire SOUNDS/en).
CSV_OFFICIEL = {"fr": "fr-FR", "en": "en-GB"}


def csv_officiel_sons_systeme(langue):
    """Télécharge la liste officielle et renvoie ses sons SYSTEM.

    Une copie est gardée dans les données de l'application : si GitHub ne
    répond pas, on repart de cette copie plutôt que de laisser l'utilisateur
    sans rien. Renvoie (lignes, langue, depuis_cache).
    """
    code = CSV_OFFICIEL.get(langue, "en-GB")
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
        return lignes, langue, True

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
    return lignes, langue, False


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
        if sys.platform == "darwin" and os.path.exists(AFPLAY):
            self._processus = subprocess.Popen(
                [AFPLAY, chemin],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        # Import paresseux : sur macOS, ces bibliothèques ne servent à rien.
        import soundfile as sf
        import sounddevice as sd

        donnees, taux = sf.read(chemin, dtype="float32")
        self._sd = sd
        sd.play(donnees, taux)

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
            + 50                      # rangée du bas (bouton « Let's Go »)
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

LANGUES = ["fr", "en"]


def langue_du_systeme():
    """Langue d'interface au tout premier lancement : celle du système.

    Seuls le français et l'anglais sont proposés. Toute autre langue donne
    l'anglais, qui a le plus de chances d'être comprise.

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
                trouve = re.search(r'[\(\s]"?([A-Za-z]{2,3})[-_"\s,)]',
                                   sortie.stdout)
                if trouve:
                    return "fr" if trouve.group(1).lower() == "fr" else "en"
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
        if (essai or "").lower().startswith("fr"):
            return "fr"
    return "en"


# Tous les textes de l'application, dans les deux langues. Les clés sont les
# mêmes dans les deux tables : c'est ce qui garantit qu'aucun texte n'est
# oublié d'un côté (voir cles_manquantes).
#
# Les champs entre accolades ({nom}, {max}…) sont remplis par t().
TEXTES = {
    "fr": {
        # ----- Boutons de la fenêtre principale -----
        "ajouter": "Ajouter",
        "supprimer": "Supprimer",
        "ecouter": "Écouter",
        "arreter": "■  Arrêter",
        "tout": "Tout",
        "rien": "Rien",
        "lets_go": "Let's Go",

        # ----- Colonnes de la liste -----
        "colonne_nom": "Nom du fichier WAV (Max {max} car.)",
        "colonne_phrase": "Phrase à prononcer par la radiocommande",

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

        # ----- Noms des langues -----
        "langue_fr": "Français",
        "langue_en": "English",

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
        "soutien_cafe": "Offre-moi un café  ☕",
        "soutien_oui": "Oui, avec plaisir !",
        "soutien_plus_tard": "Une prochaine fois",

        # ----- Fenêtre d'aide -----
        "titre_aide": "Aide — Vox-Pack",
        "aide_titre": "Comment utiliser l'application",
        # ----- 1. Voix -----
        "aide_1": "1. Choisissez une voix",
        "aide_1a":
            "Les voix proposées sont celles de la langue de l'application : "
            "{nfr} en français et {nen} en anglais. Le menu indique le genre "
            "et l'accent — « Denise (Femme - France) », « Ryan (Homme - "
            "Royaume-Uni) » — et la voix en cours est cochée.",
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
        "aide_nom1":
            "Le nom du fichier ne doit pas dépasser 8 caractères et ne doit "
            "contenir ni accent ni espace.",
        # ----- 3. Cocher -----
        "aide_3": "3. Cochez les lignes à générer",
        "aide_3a": "« Tout » coche toutes les lignes ; « Rien » les décoche.",
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
            "automatiquement au prochain démarrage ({n} lignes).",
        "aide_def5":
            "Chaque langue a SA liste : la française et l'anglaise sont "
            "indépendantes. Changer la langue dans le menu change donc aussi "
            "la liste, et votre travail de l'autre langue est conservé tel "
            "quel.",
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
            "Comptez environ 1,2 seconde par son, soit près de 4 minutes pour "
            "la liste française. Ce temps dépend de l'occupation du service "
            "de voix et de votre connexion Internet.",
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
        "aide_soutien": "☕  Mon application vous sert ou vous plaît ?",
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
        "aide_ecran": "Version {version} — écran {ecran} — fenêtre {fenetre}",
    },

    "en": {
        # ----- Main window buttons -----
        "ajouter": "Add",
        "supprimer": "Delete",
        "ecouter": "Listen",
        "arreter": "■  Stop",
        "tout": "All",
        "rien": "None",
        "lets_go": "Let's Go",

        # ----- List columns -----
        "colonne_nom": "WAV file name (max {max} char.)",
        "colonne_phrase": "Phrase to be spoken by the radio",

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

        # ----- Language names -----
        "langue_fr": "French",
        "langue_en": "English",

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
        "soutien_cafe": "Buy me a coffee  ☕",
        "soutien_oui": "Yes, with pleasure!",
        "soutien_plus_tard": "Maybe next time",

        # ----- Help window -----
        "titre_aide": "Help — Vox-Pack",
        "aide_titre": "How to use the application",
        # ----- 1. Voice -----
        "aide_1": "1. Choose a voice",
        "aide_1a":
            "The voices offered are those of the application's language: "
            "{nfr} in French and {nen} in English. The menu shows the gender "
            "and the accent — “Denise (Female - France)”, “Ryan (Male - "
            "United Kingdom)” — and the current voice is ticked.",
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
        "aide_nom1":
            "The file name must not be longer than 8 characters and must not "
            "contain accents or spaces.",
        # ----- 3. Tick -----
        "aide_3": "3. Tick the lines to generate",
        "aide_3a": "“All” ticks every line; “None” unticks them.",
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
            "the next time you start ({n} lines).",
        "aide_def5":
            "Each language has ITS OWN list: French and English are "
            "independent. Changing the language in the menu therefore also "
            "changes the list, and your work in the other language is kept "
            "as it is.",
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
            "Allow about 1.2 seconds per sound, i.e. nearly 4 minutes for the "
            "French list. This time depends on how busy the voice service is "
            "and on your Internet connection.",
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
        "aide_soutien": "☕  Do you find my application useful?",
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
        "aide_ecran": "Version {version} — screen {ecran} — window {fenetre}",
    },
}


def t(cle, **remplacements):
    """Texte de l'interface dans la langue courante.

    Si une clé manque, on renvoie la clé elle-même : cela se voit tout de
    suite à l'écran, et ça évite un plantage pour un simple mot oublié.
    """
    texte = TEXTES.get(LANGUE_UI, TEXTES["fr"]).get(cle, cle)
    return texte.format(**remplacements) if remplacements else texte


def definir_langue_ui(code):
    """Change la langue des textes (l'affichage est remis à jour ensuite par
    VoxPackApp._appliquer_langue)."""
    global LANGUE_UI
    if code in TEXTES:
        LANGUE_UI = code


def cles_manquantes():
    """Clés présentes dans une langue et pas dans l'autre.

    Sert de filet : une clé oubliée s'afficherait telle quelle à l'écran.
    """
    return sorted(set(TEXTES["fr"]) ^ set(TEXTES["en"]))


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
}

# Copie de secours : si le service retire toutes les voix d'une langue, on
# remet cette liste plutôt que de laisser un menu vide.
VOIX_ORIGINE = {code: list(voix) for code, voix in VOIX.items()}

# La voix choisie par l'équipe EdgeTX pour chaque langue : elle est marquée
# d'une étoile dans le sélecteur, pour que l'on sache laquelle reproduit les
# sons du constructeur.
VOIX_OFFICIELLES = {"fr-FR-DeniseNeural", "en-IE-EmilyNeural"}

# Réglages officiels de vitesse : EdgeTX ne fait pas parler toutes ses voix à
# la même allure. Emily, la voix anglaise officielle, parle 10 % plus vite.
REGLES_VOIX = {"en-IE-EmilyNeural": {"rate": "+10%"}}


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
                pitch=pitch or "+0Hz")
            await communicate.save(chemin)
            return
        except Exception as e:
            derniere = e
            if tentative == 0:
                await asyncio.sleep(0.8)
    raise derniere


def libelle_voix(entree, langue_ui=None):
    """Libellé affiché d'une voix : « Denise (Femme - France) ».

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
    libelle = (f"{prenom} ({table.get('genre_' + genre, genre)} - "
               f"{origine})")
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
    for entree in VOIX.get(code, []):
        for langue_ui in TEXTES:
            if libelle_voix(entree, langue_ui) == valeur:
                return entree[0]
    return None


def tous_les_libelles_voix():
    """Tous les libellés possibles, dans les deux langues d'interface.

    Sert à régler la largeur du menu déroulant une fois pour toutes : il ne
    doit pas changer de taille quand on passe d'une langue à l'autre.
    """
    return [libelle_voix(entree, langue_ui)
            for langue_ui in LANGUES
            for code in VOIX
            for entree in VOIX[code]]


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
}

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
HAUTEUR_FENETRE = 813

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

# Barre de progression : hauteur du bloc et épaisseur des leds
HAUTEUR_LEDS = 16
EPAISSEUR_LEDS = 6

# Durée, en secondes, pendant laquelle la barre reste complètement allumée
# avant de s'éteindre. Trop courte, on ne voit jamais la dernière led
# s'allumer (l'animation met un instant à la rejoindre).
PAUSE_LEDS = 0.8

# Menu. Le choix de langue y est entré, et il faut qu'il soit lisible :
# la police par défaut d'un menu Tk est minuscule sur Windows.
TYPO_MENU = 14            # texte des entrées du menu
TYPO_MENU_BOUTON = 26     # les trois barres qui ouvrent le menu (hors macOS)

# Largeur des textes de la fenêtre d'aide, pour qu'ils passent à la ligne au
# lieu d'être coupés au bord (la fenêtre fait 620 px, moins ses marges).
LARGEUR_TEXTE_AIDE = 530

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
LARGEUR_MESSAGE = 175       # colonne des messages, à droite de chaque ligne


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
        # Les leds gardent une épaisseur fixe et sont centrées dans le bloc :
        # c'est ce qui les rend fines quel que soit l'espace réservé.
        epaisseur = min(EPAISSEUR_LEDS, h - 2)
        radius = max(1, epaisseur // 2)
        filled = int(self.progress * n)
        # Les leds occupent TOUTE la largeur : c'est ce qui donne l'impression
        # qu'il manquait une led à la fin quand on réservait la place du
        # pourcentage. Le pourcentage a donc été retiré : les leds suffisent.
        seg_w = (w - gap * (n - 1)) / n

        for i in range(n):
            x0 = i * (seg_w + gap)
            x1 = x0 + seg_w
            y0 = (h - epaisseur) // 2
            y1 = y0 + epaisseur
            color = LINK_COLOR if i < filled else "#1E2A33"
            self._round_rect(c, x0, y0, x1, y1, radius, color)

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

    Plus utilisée depuis que le sous-titre « Fait parler ta radio » a été
    retiré de l'en-tête, mais conservée : elle servira pour un slogan
    ailleurs (fenêtre d'aide, à propos…).
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
        self._reglages = lire_reglages()
        # Effet robot mémorisé : 0 = aucun, 1 à 3 = Robot, 4 = HAL 9000.
        try:
            self._robot = int(self._reglages.get("robot", 0) or 0)
        except (TypeError, ValueError):
            self._robot = 0
        if self._robot not in ROBOTS:
            self._robot = 0
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
        # Variable des cases à cocher du menu Langue (une seule case cochée).
        self._var_langue_ui = ctk.StringVar(value=LANGUE_UI)

        # ----- En-tête (logo + sous-titre) -----
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(ESPACE_HAUT, 0))

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
        self.btn_aide.configure(cursor=CURSEUR_MAIN)
        self.btn_aide.place(relx=1.0, rely=0.0, anchor="ne", x=-15, y=30)

        # Bouton du menu, à gauche du « ? ». Sur macOS, le menu est dans la
        # barre du système : ce bouton n'existe pas.
        if not sys.platform == "darwin":
            self.btn_menu = ctk.CTkButton(
                self.header,
                text="≡",
                font=(FONT_MAIN, TYPO_MENU_BOUTON),
                width=36,
                height=int(36 * ECHELLE_UI),
                corner_radius=0,
                fg_color="transparent",
                border_width=0,          # c'est un menu, pas un bouton
                text_color=CYAN,
                hover=False,
                command=self._ouvrir_menu,
            )
            self._survol(self.btn_menu)
            self.btn_menu.configure(cursor=CURSEUR_MAIN)
            # Tout en haut à gauche, comme une entrée de barre de menus : le
            # « ? » garde la droite, et il n'y a rien à cet endroit.
            self.btn_menu.place(x=14, y=4, anchor="nw")

        # Logo
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                ratio = img.height / img.width
                new_w = self.largeur_logo
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
            ).pack(anchor="center", pady=(0, 4))

        # ----- Les quatre pastilles robot, à droite du logo -----
        # Aucune allumée = voix normale. Un clic choisit un preset ; un
        # second clic sur la même pastille revient à la normale.
        self.cadre_robot = ctk.CTkFrame(self.header, fg_color="transparent")
        # La rangée est remontée sous le « ? ». Sur un petit écran, le logo
        # est plus court : on la décale vers la gauche pour ne pas passer
        # sous le « ? » et on la remonte moins.
        petit = self.largeur_logo <= LARGEUR_LOGO_PETIT
        x_robot = -62 if petit else -15
        y_robot = 42 if petit else 130
        self.cadre_robot.place(relx=1.0, rely=0.0, anchor="ne",
                               x=x_robot, y=y_robot)
        self.lbl_robot = ctk.CTkLabel(
            self.cadre_robot, text="", font=(FONT_MAIN, 12),
            text_color=TEXT_GREY,
        )
        self.lbl_robot.pack(anchor="center")
        rangee_robot = ctk.CTkFrame(self.cadre_robot, fg_color="transparent")
        rangee_robot.pack(anchor="center", pady=(4, 0))
        self._boutons_robot = {}
        for numero in ROBOTS:
            bouton = ctk.CTkButton(
                rangee_robot, text="", width=22, height=22, corner_radius=11,
                fg_color="transparent", border_color=CYAN_DARK, border_width=1,
                hover=False, command=lambda n=numero: self._choisir_robot(n),
            )
            bouton.configure(cursor=CURSEUR_MAIN)
            bouton.pack(side="left", padx=4)
            bouton.bind("<Enter>", lambda e, n=numero: self._survol_robot(n))
            bouton.bind("<Leave>", lambda e: self._survol_robot(None))
            self._boutons_robot[numero] = bouton
        self._maj_robot()

        # ----- Ligne unique : Voix + 3 boutons (centrée) -----
        row_all = ctk.CTkFrame(self, fg_color="transparent")
        row_all.pack(fill="x", padx=20, pady=(ESPACE_LOGO_BOUTONS, 0))

        inner_row = ctk.CTkFrame(row_all, fg_color="transparent")
        inner_row.pack(anchor="center")

        self.combo_voice = MenuVoix(
            inner_row,
            values=[etiquette for etiquette, _id in voix_de_la_langue(self.langue)],
            # Largeur calculée sur le libellé le plus long, dans les deux
            # langues d'interface : le menu ne change donc pas de taille en
            # passant de l'une à l'autre, et la flèche reste collée au texte.
            width=largeur_juste(tous_les_libelles_voix()),
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
        self._remplir_voix()
        self.combo_voice.configure(command=self._voix_changee)
        self.combo_voice.pack(side="left", padx=(0, 12))

        self.btn_ajouter = self._btn(inner_row, t("ajouter"), self.ajouter_ligne)
        self.btn_ajouter.pack(side="left", padx=5)
        self.btn_supprimer = self._btn(inner_row, t("supprimer"),
                                       self.supprimer_selection)
        self.btn_supprimer.pack(side="left", padx=5)
        self.btn_apercu = self._btn(inner_row, t("ecouter"),
                                    self.ecouter_selection)
        self.btn_apercu.pack(side="left", padx=5)
        self._lecture = None
        self._apercu_no = 0

        # ----- En-tête du tableau -----
        row_head = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=10)
        row_head.pack(fill="x", padx=20, pady=(ESPACE_BOUTONS_LISTE, 0))

        row_head.grid_columnconfigure(0, weight=0, minsize=40)
        row_head.grid_columnconfigure(1, weight=1, uniform="col")
        row_head.grid_columnconfigure(2, weight=1, uniform="col")

        ctk.CTkLabel(row_head, text="", width=40).grid(row=0, column=0, padx=4, pady=8)
        self.lbl_col_nom = ctk.CTkLabel(
            row_head, text=t("colonne_nom", max=LIMITE_NOM),
            font=(FONT_MAIN, 18, "normal"), text_color=TEXT_WHITE,
        )
        self.lbl_col_nom.grid(row=0, column=1, sticky="w", padx=8, pady=8)
        self.lbl_col_phrase = ctk.CTkLabel(
            row_head, text=t("colonne_phrase"),
            font=(FONT_MAIN, 18, "normal"), text_color=TEXT_WHITE,
        )
        self.lbl_col_phrase.grid(row=0, column=2, sticky="w", padx=8, pady=8)
        row_head.grid_columnconfigure(3, weight=0)

        # ----- Zone liste défilante -----
        self.frame_table = ctk.CTkScrollableFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=10,
            scrollbar_button_color=CYAN_DARK,
            scrollbar_button_hover_color=CYAN,
        )
        # La liste est empilée EN DERNIER (voir plus bas, après le bloc du bas) :
        # c'est elle qui absorbe le rétrécissement de la fenêtre. Si on
        # l'empilait ici, c'est le bloc du bas qui serait rogné quand la
        # fenêtre devient trop petite — et les boutons disparaîtraient.
        self.frame_table.grid_columnconfigure(0, weight=0, minsize=40)
        self.frame_table.grid_columnconfigure(1, weight=1, uniform="col")
        self.frame_table.grid_columnconfigure(2, weight=1, uniform="col")
        self.frame_table.grid_columnconfigure(3, weight=0)

        # customtkinter ne fait défiler la liste que si le widget rapporté par
        # l'événement en fait partie. Sur macOS, cette identification n'est pas
        # fiable : après un clic, la molette se bloque. On reprend donc la
        # molette nous-mêmes, en regardant simplement où se trouve le curseur.
        self.frame_table._parent_canvas.unbind_all("<MouseWheel>")
        self.bind_all("<MouseWheel>", self._molette_liste, add="+")
        if sys.platform.startswith("linux"):
            # Sous Linux, la molette n'envoie pas <MouseWheel> mais Button-4/5.
            self.bind_all("<Button-4>", self._molette_liste, add="+")
            self.bind_all("<Button-5>", self._molette_liste, add="+")

        # ----- Bas : barre de leds, boutons -----
        # Empilé AVANT la liste : ainsi le bloc du bas garde toujours sa place,
        # même dans une fenêtre très basse (c'est la liste qui se réduit).
        self.bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom.pack(side="bottom", fill="x", padx=20,
                         pady=(ESPACE_LISTE_LEDS, ESPACE_BAS))

        # La barre de leds occupe toute la largeur : aucun texte ne vient la
        # rogner, elle s'allume donc jusqu'au bout.
        self.progress = SegmentedProgressBar(self.bottom, segments=32,
                                             height=HAUTEUR_LEDS)
        self.progress.pack(fill="x")
        self.progress.set(0.0)

        # Ligne du compteur, juste sous la barre de leds. Sa hauteur est fixée
        # au strict nécessaire : livrée à elle-même, elle réservait ~28 px dont
        # la moitié de vide. Sa place reste réservée en permanence, donc rien
        # ne bouge quand le texte apparaît. L'espace sous cette ligne, c'est
        # ESPACE_LEDS_BOUTONS.
        self.lbl_compteur = ctk.CTkLabel(
            self.bottom, text="", font=(FONT_MAIN, TYPO_INFO),
            text_color=TEXT_GREY, anchor="w", height=HAUTEUR_INFO,
        )
        self.lbl_compteur.pack(fill="x", pady=(0, ESPACE_LEDS_BOUTONS))

        # Conteneur centré
        center_frame = ctk.CTkFrame(self.bottom, fg_color="transparent")
        center_frame.pack(fill="x", expand=True)

        row_gen = ctk.CTkFrame(center_frame, fg_color="transparent")
        row_gen.pack(anchor="center")

        self.btn_tout = self._btn(row_gen, t("tout"), self.tout_cocher, small=True)
        self.btn_tout.pack(side="left", padx=6)
        self.btn_rien = self._btn(row_gen, t("rien"), self.rien_cocher, small=True)
        self.btn_rien.pack(side="left", padx=6)

        self.btn_letsgo = ctk.CTkButton(
            row_gen,
            text=t("lets_go"),
            font=(FONT_MAIN, 16, "bold"),
            width=180,
            height=38,
            corner_radius=19,
            fg_color="#04C3D4",
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
        self.signature.configure(cursor=CURSEUR_MAIN)
        self.signature.place(relx=1.0, rely=1.0, anchor="se", x=-15, y=-16)
        self.signature.bind("<Button-1>", lambda e: self._ouvrir_soutien())

        # Lien Ko-fi visible sous la signature.
        self.kofi = ctk.CTkLabel(
            self.bottom,
            text="☕ Ko-fi",
            font=(FONT_MAIN, 10),
            text_color=TEXT_DIM,
            fg_color="transparent",
            height=16,
            width=56,
        )
        self.kofi.configure(cursor=CURSEUR_MAIN)
        self.kofi.place(relx=1.0, rely=1.0, anchor="se", x=-15, y=-0)
        self.kofi.bind("<Button-1>", lambda e: self._ouvrir_lien(KO_FI_URL))
        self.kofi.bind("<Enter>",
                       lambda e: self.kofi.configure(text_color=CYAN))
        self.kofi.bind("<Leave>",
                       lambda e: self.kofi.configure(text_color=TEXT_DIM))
        self.signature.bind(
            "<Enter>", lambda e: self.signature.configure(text_color=CYAN))
        self.signature.bind(
            "<Leave>", lambda e: self.signature.configure(text_color=TEXT_DIM))
        self.signature.lift()

        # La liste est empilée en dernier, avec « expand » : elle prend toute la
        # place restante et se réduit la première si la fenêtre rapetisse.
        self.frame_table.pack(side="top", fill="both", expand=True,
                              padx=20, pady=(2, 0))

        # ----- Chargement -----
        reprendre_ancienne_liste()
        self.charger_liste()

        # On vérifie en arrière-plan que les voix proposées existent toujours
        # chez Microsoft (décalé : la fenêtre s'affiche d'abord).
        self.after(600, self._verifier_voix)
        # Vérification des mises à jour, décalée : elle ne doit ni bloquer ni
        # retarder l'affichage. Silencieuse si le réseau manque.
        self.after(2500, self._verifier_maj)

        self._poser_icone()
        self._construire_menu()

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
        fichier.add_command(label=t("menu_quitter"), command=self.destroy)
        barre.add_cascade(label=t("menu_fichier"), menu=fichier)
        self._menu_fichier = fichier
        if sys.platform == "darwin":
            self.configure(menu=barre)
        else:
            # Pas de barre dans la fenêtre : le menu s'ouvre à la demande.
            self.configure(menu="")

    def _ouvrir_menu(self, _evenement=None):
        """Ouvre le menu depuis le bouton « ☰ » (Windows, Linux)."""
        menu = getattr(self, "_menu_fichier", None)
        bouton = getattr(self, "btn_menu", None)
        if menu is None or bouton is None:
            return
        try:
            menu.tk_popup(bouton.winfo_rootx(),
                          bouton.winfo_rooty() + bouton.winfo_height())
        finally:
            menu.grab_release()

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
        self.btn_ajouter.configure(text=t("ajouter"))
        self.btn_supprimer.configure(text=t("supprimer"))
        # Le bouton d'aperçu peut être en train de lire : on ne remplace pas
        # « Arrêter » par « Écouter » sous les doigts de l'utilisateur.
        if self._lecture is None:
            self.btn_apercu.configure(text=t("ecouter"))
        else:
            self.btn_apercu.configure(text=t("arreter"))
        self.btn_tout.configure(text=t("tout"))
        self.btn_rien.configure(text=t("rien"))
        # Pendant la création des sons système, ce bouton sert d'« Arrêter » :
        # un changement de langue ne doit pas le rebaptiser « Let's Go ».
        self.btn_letsgo.configure(
            text=t("arreter") if self._sons_stop is not None else t("lets_go"))
        self._maj_robot()
        self.lbl_col_nom.configure(text=t("colonne_nom", max=LIMITE_NOM))
        self.lbl_col_phrase.configure(text=t("colonne_phrase"))
        # Les libellés des voix changent aussi (« Femme » devient « Female »),
        # et donc la largeur du menu.
        self.combo_voice.configure(width=largeur_juste(tous_les_libelles_voix()))
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
                    ecrivain.writerow([ligne["entry_nom"].get().strip(),
                                       ligne["entry_txt"].get().strip()])
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

        # Un en-tête est ignoré : c'est ce que produit l'export, dans l'une ou
        # l'autre langue (« nom » / « name »).
        if brut and brut[0][0].strip().lower() in ("nom", "name", "fichier",
                                                   "file"):
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
        self._supprimer_lignes(list(self.lignes))
        for nom, phrase in paires:
            self._ajouter_ligne_ui(nom, phrase)
        self._on_change()
        self.after_idle(
            lambda: self.frame_table._parent_canvas.yview_moveto(0.0))
        self._message(t("msg_import_ok", n=len(paires),
                        s="s" if len(paires) > 1 else ""), icone="succes")

    def charger_liste_defaut(self):
        """Remet la liste livrée avec l'application, dans la langue des voix.

        Nécessaire parce que la liste de l'utilisateur n'est JAMAIS remplacée
        par un simple changement de langue : ce serait perdre son travail sans
        prévenir. C'est donc une action explicite, avec confirmation.
        """
        defaut = LISTE_PAR_DEFAUT.get(self.langue, LISTE_PAR_DEFAUT["fr"])
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
    # Mini fenêtre de soutien (clic sur la signature)
    # ------------------------------------------------------------------
    def _ouvrir_soutien(self):
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
        popup.bind("<Escape>", lambda e: popup.destroy())

        largeur = LARGEUR_SOUTIEN
        ctk.CTkLabel(
            popup, text=t("soutien_question"),
            font=(FONT_MAIN, 16), text_color=TEXT_WHITE,
            wraplength=largeur - 50, justify="center",
        ).pack(padx=25, pady=(26, 6))

        cafe = ctk.CTkLabel(
            popup, text=t("soutien_cafe"),
            font=(FONT_MAIN, 16), text_color=LINK_COLOR,
        )
        cafe.pack()
        cafe.bind("<Button-1>", lambda e: self._ouvrir_lien(KO_FI_URL))

        boutons = ctk.CTkFrame(popup, fg_color="transparent")
        boutons.pack(pady=(24, 26))
        # Le « Oui » est nettement plus gros que l'autre : c'est le bouton
        # qu'on a envie de cliquer (léger avantage déloyal, assumé).
        oui = self._btn(
            boutons, t("soutien_oui"),
            lambda: (self._ouvrir_lien(KO_FI_URL), popup.destroy()),
            largeur=OUI_LARGEUR, hauteur=OUI_HAUTEUR, typo=OUI_TYPO,
        )
        oui.configure(fg_color="transparent", text_color=CYAN,
                      border_color=CYAN, corner_radius=OUI_HAUTEUR // 2,
                      hover_color=CYAN_DARK)
        oui.pack(side="left", padx=7)
        self._btn(boutons, t("soutien_plus_tard"), popup.destroy,
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

        # La fenêtre se resserre comme le reste de l'interface : sur un écran
        # court (ou à 150 % de mise à l'échelle), une alerte de 430 px paraît
        # énorme pour deux lignes de texte.
        cote = int(46 * ECHELLE_UI)
        marge = int(24 * ECHELLE_UI)

        # Et sa largeur suit le texte : mieux vaut une alerte étroite pour un
        # message court qu'une grande fenêtre à moitié vide. On garde toujours
        # de quoi loger les boutons.
        police = tkfont.Font(family=FONT_MAIN, size=TYPO_ALERTE)
        besoin = max((police.measure(ligne) for ligne in texte.split("\n")),
                     default=0) + 2 * marge
        nb_boutons = len(boutons or [(None, None)])
        besoin_boutons = nb_boutons * (int(150 * ECHELLE_UI)
                                       + int(12 * ECHELLE_UI))
        largeur = int(min(largeur * ECHELLE_UI,
                          max(besoin, besoin_boutons, int(320 * ECHELLE_UI))))

        pastille = ctk.CTkCanvas(popup, width=cote, height=cote,
                                 bg=BG_MAIN, highlightthickness=0)
        pastille.create_oval(3, 3, cote - 3, cote - 3, outline=couleur, width=2)
        pastille.create_text(cote // 2, cote // 2, text=symbole, fill=couleur,
                             font=(FONT_MAIN, int(24 * ECHELLE_UI), "bold"))
        pastille.pack(pady=(int(12 * ECHELLE_UI), 0))

        ctk.CTkLabel(
            popup, text=texte,
            font=(FONT_MAIN, TYPO_ALERTE), text_color=TEXT_WHITE,
            wraplength=largeur - int(50 * ECHELLE_UI), justify="center",
        ).pack(padx=marge)

        rangee = ctk.CTkFrame(popup, fg_color="transparent")
        # Marges resserrées : une alerte n'a pas besoin d'autant d'air, et sur
        # un écran court chaque pixel gagné compte.
        rangee.pack(pady=(int(10 * ECHELLE_UI), int(8 * ECHELLE_UI)))

        for libelle, action in (boutons or [(t("compris"), None)]):

            def cliquer(a=action):
                popup.destroy()
                if a:
                    a()

            self._btn(rangee, libelle, cliquer,
                      largeur=int(150 * ECHELLE_UI)).pack(
                side="left", padx=int(6 * ECHELLE_UI))

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
    def _voix_francaise(self):
        """Vrai si la voix utilisée est française (HAL ou voix du menu)."""
        if self._robot == 4:
            return self.langue == "fr"
        try:
            voix = identifiant_voix(self.langue, self.combo_voice.get())
        except Exception:
            return False
        return voix.startswith("fr-")

    def _robot_voice(self):
        """Voix imposée par HAL 9000 (None pour les autres presets)."""
        if self._robot != 4:
            return None
        return ("fr-FR-HenriNeural" if self.langue == "fr"
                else "en-US-ChristopherNeural")

    def _reglage_robot(self):
        """Réglage du preset, avec la variante française si elle existe."""
        reglage = ROBOTS.get(self._robot)
        if not reglage:
            return None
        if self._voix_francaise() and "fr" in reglage:
            return reglage["fr"]
        return reglage

    def _robot_pitch(self):
        """Hauteur à demander au service pour le preset choisi."""
        reglage = self._reglage_robot()
        return reglage.get("pitch") if reglage else None

    def _robot_rate(self):
        """Débit à demander au service pour le preset choisi."""
        reglage = self._reglage_robot()
        return reglage.get("rate") if reglage else None

    def _appliquer_robot(self, chemin):
        """Applique l'effet robot au WAV, si une pastille est allumée."""
        if self._robot in ROBOTS:
            langue = "fr" if self._voix_francaise() else "en"
            appliquer_effet_robot(chemin, self._robot, langue)

    def _maj_libelle_robot(self):
        if self._robot == 4:
            self.lbl_robot.configure(text="HAL 9000", text_color=CYAN)
        elif self._robot:
            self.lbl_robot.configure(text=f"Robot {self._robot}",
                                     text_color=CYAN)
        else:
            self.lbl_robot.configure(text=t("voix_normale"),
                                     text_color=CYAN)

    def _maj_robot(self):
        for numero, bouton in self._boutons_robot.items():
            actif = numero == self._robot
            bouton.configure(
                fg_color=CYAN if actif else "transparent",
                border_color=CYAN if actif else CYAN_DARK,
            )
        self._maj_libelle_robot()

    def _survol_robot(self, numero):
        """Affiche le nom de la pastille survolée au-dessus de la rangée."""
        if numero is None:
            self._maj_libelle_robot()
            for n, bouton in self._boutons_robot.items():
                if n != self._robot:
                    bouton.configure(border_color=CYAN_DARK)
        else:
            libelle = "HAL 9000" if numero == 4 else f"Robot {numero}"
            self.lbl_robot.configure(text=libelle, text_color=CYAN)
            for n, bouton in self._boutons_robot.items():
                if n != self._robot:
                    bouton.configure(
                        border_color=CYAN if n == numero else CYAN_DARK)

    def _choisir_robot(self, numero):
        """Allume un preset, ou l'éteint si c'est déjà le sien."""
        self._robot = 0 if self._robot == numero else numero
        self._reglages["robot"] = self._robot
        ecrire_reglages(self._reglages)
        self._maj_robot()

    def _ouvrir_aide(self):
        popup = ctk.CTkToplevel(self)
        popup.title(t("titre_aide"))
        popup.resizable(False, False)
        popup.transient(self)
        popup.configure(fg_color=BG_MAIN)

        self.update_idletasks()
        # La fenêtre d'aide ne doit jamais dépasser l'écran : sinon le bouton
        # « Fermer » passe sous la barre des tâches et devient inatteignable.
        # 160 px réservés : la barre des tâches et le Dock, pour que la fenêtre
        # ne vienne pas s'y coller.
        w_popup = min(620, self.winfo_screenwidth() - 80)
        h_popup = min(600, self.winfo_screenheight() - 160)
        x = self.winfo_x() + (self.winfo_width() - w_popup) // 2
        y = self.winfo_y() + (self.winfo_height() - h_popup) // 2
        popup.geometry(f"{w_popup}x{h_popup}+{max(x, 0)}+{max(y, 0)}")

        cadre = ctk.CTkFrame(popup, fg_color=BG_CARD, corner_radius=10)
        cadre.pack(fill="both", expand=True, padx=15, pady=(15, 8))

        # Une vraie zone de texte, et non des blocs empilés : c'est ce qui
        # permet un interligne franc (spacing2) et un espacement régulier
        # entre paragraphes (spacing3), tout en laissant le texte se couper
        # tout seul à la bonne largeur.
        zone = ctk.CTkTextbox(
            cadre, fg_color=BG_CARD, text_color=TEXT_WHITE,
            border_width=0, corner_radius=0, wrap="word",
            font=(FONT_MAIN, 14),
            scrollbar_button_color=CYAN_DARK,
            scrollbar_button_hover_color=CYAN,
        )
        zone.pack(fill="both", expand=True, padx=6, pady=6)
        texte = zone._textbox
        texte.configure(padx=12, pady=8, cursor="arrow",
                        selectbackground=CYAN_HOVER,
                        selectforeground=BG_MAIN)

        # Les styles. Les puces et les avertissements ont un retrait
        # (lmargin2) : quand ils passent à la ligne, la suite reste sous le
        # texte, pas sous la puce.
        styles = {
            "title": dict(font=(FONT_MAIN, 19), foreground=CYAN,
                          spacing1=6, spacing3=16),
            "head": dict(font=(FONT_MAIN, 17), foreground=CYAN,
                         spacing1=22, spacing3=8),
            "body": dict(font=(FONT_MAIN, 14), foreground=TEXT_WHITE,
                         spacing1=0, spacing2=8, spacing3=12),
            "bullet": dict(font=(FONT_MAIN, 14), foreground=TEXT_WHITE,
                           spacing1=0, spacing2=8, spacing3=10,
                           lmargin1=0, lmargin2=18),
            "warning": dict(font=(FONT_MAIN, 14), foreground="#FF6B6B",
                            spacing1=2, spacing2=8, spacing3=12,
                            lmargin1=0, lmargin2=26),
            "code": dict(font=("Menlo", 13), foreground=LINK_COLOR,
                         spacing1=2, spacing2=4, spacing3=14,
                         lmargin1=22, lmargin2=22),
            "sep": dict(font=(FONT_MAIN, 12), foreground=TEXT_DIM,
                        justify="center", spacing1=14, spacing3=14),
            "grand": dict(font=(FONT_MAIN, 18), foreground=CYAN,
                          justify="center", spacing1=4, spacing3=4),
            "lien": dict(font=(FONT_MAIN, 16), foreground=LINK_COLOR,
                         justify="center", spacing3=10),
            "petit": dict(font=(FONT_MAIN, 11), foreground=TEXT_DIM,
                          justify="center", spacing3=6),
            "italic": dict(font=(FONT_MAIN, 13, "italic"),
                           foreground=TEXT_GREY, justify="center",
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
                img = Image.open(LOGO_PATH)
                ratio = img.height / img.width
                largeur = self.largeur_logo
                img = img.resize((largeur, int(largeur * ratio)),
                                 Image.Resampling.LANCZOS)
                self._logo_aide = ImageTk.PhotoImage(img)
            except Exception:
                self._logo_aide = None

        # Le texte de l'aide, dans la langue de l'interface.
        contenu = [
            ("logo", ""),
            ("title", t("aide_titre")),
            ("space", ""),
            ("title2", t("aide_1")),
            ("text", t("aide_1a", nfr=len(VOIX["fr"]), nen=len(VOIX["en"]))),
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
                       n=len(LISTE_PAR_DEFAUT.get(self.langue,
                                                  LISTE_PAR_DEFAUT["fr"])))),
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
            ("grand", t("aide_soutien")),
            ("lien", t("aide_lien")),
            ("space", ""),
            ("sep", ""),
            ("petit", t("aide_ecran",
                        version=VERSION,
                        ecran=f"{self.winfo_screenwidth()} × {self.winfo_screenheight()}",
                        fenetre=f"{self.winfo_width()} × {self.winfo_height()}")),
            ("italic", t("aide_credits")),
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
            elif kind == "lien":
                texte.insert("end", txt + "\n", "lien")
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
        texte.tag_bind(
            "lien", "<Enter>",
            lambda e: (texte.tag_configure("lien", foreground=CYAN),
                       texte.configure(cursor=CURSEUR_MAIN)))
        texte.tag_bind(
            "lien", "<Leave>",
            lambda e: (texte.tag_configure("lien", foreground=LINK_COLOR),
                       texte.configure(cursor="arrow")))

        texte.configure(state="disabled")
        texte.yview_moveto(0.0)

        fermer = self._btn(popup, t("fermer"), popup.destroy, largeur=140)
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
        if getattr(event, "num", None) == 4:        # Linux : vers le haut
            unites = -1
        elif getattr(event, "num", None) == 5:      # Linux : vers le bas
            unites = 1
        elif sys.platform.startswith("win"):
            # Windows : 120 par cran de molette (macOS : de petites valeurs).
            unites = -int(event.delta / 6)
        else:
            # macOS : la valeur dépend de la vitesse du geste. Un geste rapide
            # envoie 20 ou 30 d'un coup ; à 8 px l'unité, la liste sautait
            # alors de 160 à 240 px, soit plusieurs lignes. On borne à 3
            # unités (24 px) par événement : le défilement reste rapide, mais
            # ne saute plus.
            unites = max(-3, min(3, -int(event.delta)))
        if unites:
            canvas.yview("scroll", unites, "units")

    def charger_liste(self):
        for ligne in self.lignes:
            ligne["frame"].destroy()
        self.lignes.clear()

        contenu = []
        fichier = chemin_liste(self.langue)
        if os.path.exists(fichier):
            # Lecture par le module csv : il comprend aussi bien les anciens
            # fichiers (sans guillemets) que les nouveaux.
            with open(fichier, "r", encoding="utf-8", newline="") as f:
                lignes_lues = list(csv.reader(f))
            # Un en-tête « nom,phrase » (nos fichiers exportés en ont un) est
            # ignoré : sinon il deviendrait une ligne de la liste.
            if lignes_lues and lignes_lues[0] \
                    and lignes_lues[0][0].strip().lower() in ("nom", "name", "fichier"):
                lignes_lues = lignes_lues[1:]
            for ligne_lue in lignes_lues:
                if len(ligne_lue) >= 2:
                    contenu.append((ligne_lue[0].strip(), ligne_lue[1].strip()))
                elif len(ligne_lue) == 1 and ligne_lue[0].strip():
                    contenu.append((ligne_lue[0].strip(), ""))

        if not contenu:
            # Liste reconstruite : celle de la langue des voix choisie.
            contenu = list(LISTE_PAR_DEFAUT.get(self.langue,
                                                LISTE_PAR_DEFAUT["fr"]))

        for nom, texte in contenu:
            self._ajouter_ligne_ui(nom, texte)

        # Les lignes sont nouvelles : l'ancre de sélection n'a plus de sens,
        # et les noms invalides doivent être signalés dès l'affichage.
        self._ancre_selection = None
        self._verifier_noms()
        self._ecrire_csv()

    def _ajouter_ligne_ui(self, nom, texte):
        idx = len(self.lignes)
        frame = ctk.CTkFrame(self.frame_table, fg_color="transparent")
        frame.grid(row=idx, column=0, columnspan=4, sticky="ew", pady=2)
        frame.grid_columnconfigure(0, weight=0, minsize=40)
        frame.grid_columnconfigure(1, weight=1, uniform="col")
        frame.grid_columnconfigure(2, weight=1, uniform="col")
        frame.grid_columnconfigure(3, weight=0)

        var_check = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(
            frame, text="", variable=var_check, width=24,
            checkbox_width=20, checkbox_height=20,
            fg_color=CYAN, hover_color=CYAN_DARK,
            border_color=CYAN, border_width=2, corner_radius=6,
        )
        chk.grid(row=0, column=0, padx=(4, 6), pady=4)
        # Clic sur la case, avec ou sans la touche Majuscule : Majuscule étend
        # la coche (ou la décoche) à toutes les lignes depuis la dernière
        # cliquée — comme dans le Finder.
        chk.bind("<Button-1>",
                 lambda e, v=var_check: self._clic_case(v, bool(e.state & 0x0001)),
                 add="+")

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
            frame, text="", font=(FONT_MAIN, TYPO_MESSAGE),
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
        self._ajouter_ligne_ui(t("nouvelle_ligne"), t("texte_a_dire"))
        self._on_change()
        # Le curseur se place dans la nouvelle ligne…
        self.lignes[-1]["entry_nom"].focus_set()
        # …et on descend jusqu'à elle. Le défilement est demandé « au repos » :
        # à cet instant, la nouvelle ligne n'a pas encore sa place calculée,
        # et on descendait donc trop haut (la ligne restait cachée).
        self.after_idle(
            lambda: self.frame_table._parent_canvas.yview_moveto(1.0))

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
        """Écrit une information dans la ligne, sous la barre de leds.

        Appelée depuis un fil de travail (génération, aperçu) : le changement
        d'affichage est donc confié à la boucle d'événements avec after().
        L'appel est protégé : si la fenêtre est en train de se fermer, on
        préfère perdre un message plutôt que de tuer le fil en cours.
        """
        try:
            self.after(0, lambda txt=texte: self.lbl_compteur.configure(text=txt))
        except Exception:
            pass

    def _clic_case(self, var, majuscule):
        """Clic sur une case à cocher, éventuellement avec la touche Majuscule.

        Sans Majuscule : on coche ou décoche cette ligne (comportement normal),
        et elle devient le point de départ d'une éventuelle extension.
        Avec Majuscule : on applique le nouvel état à TOUTES les lignes depuis
        la dernière cliquée jusqu'à celle-ci, en haut comme en bas.
        """
        # L'index est cherché ICI, au moment du clic : après une suppression,
        # un index retenu à la création de la ligne ne serait plus le bon.
        index = next((i for i, l in enumerate(self.lignes)
                      if l["var_check"] is var), None)
        if index is None:
            return
        etat = self.lignes[index]["var_check"].get()
        if majuscule and self._ancre_selection is not None \
                and self._ancre_selection < len(self.lignes):
            debut, fin = sorted((self._ancre_selection, index))
            for i in range(debut, fin + 1):
                self.lignes[i]["var_check"].set(etat)
        else:
            self._ancre_selection = index

    def _verifier_noms(self):
        """Colore en rouge les noms qui posent problème, signale les doublons."""
        vus = {}
        for i, ligne in enumerate(self.lignes, start=1):
            nom = ligne["entry_nom"].get().strip()
            souci = probleme_nom(nom)
            if souci is None:
                deja = vus.get(nom.lower())
                if deja:
                    souci = t("pb_doublon", n=deja)
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
        for ligne in cochees:
            ligne["frame"].destroy()
            self.lignes.remove(ligne)
        for i, ligne in enumerate(self.lignes):
            ligne["frame"].grid_configure(row=i)
        # les numéros de ligne ont changé : le point de départ n'est plus valable
        self._ancre_selection = None
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
            fichier = chemin_liste(self.langue)
            temporaire = fichier + ".tmp"
            with open(temporaire, "w", encoding="utf-8", newline="") as f:
                ecrivain = csv.writer(f)
                for l in self.lignes:
                    nom = l["entry_nom"].get().strip()
                    texte = l["entry_txt"].get().strip()
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
        cochees = [l for l in self.lignes if l["var_check"].get()]
        if not cochees:
            self._message(t("msg_ecouter_rien"), icone="attention")
            return
        textes = []
        for ligne in cochees:
            phrase = ligne["entry_txt"].get().strip()
            if phrase:
                textes.append((ligne["entry_nom"].get().strip(), phrase))
        if not textes:
            return
        voice_id = identifiant_voix(self.langue, self.combo_voice.get())

        # Le bouton devient « Arrêter » : la lecture peut être coupée.
        self._apercu_no += 1
        numero = self._apercu_no
        self._lecture = None
        self.btn_apercu.configure(text=t("arreter"), command=self.arreter_apercu)

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
            self.btn_apercu.configure(text=t("ecouter"),
                                      command=self.ecouter_selection)
        except Exception:
            pass

    async def _telecharger_voix(self, texte, voice_id, chemin):
        """Fabrique le fichier d'une phrase auprès du service de voix."""
        await sauver_voix(texte, voice_id, chemin,
                          pitch=self._robot_pitch(), rate=self._robot_rate())

    async def _jouer_apercu(self, textes, voice_id, numero):
        """Lit les phrases l'une après l'autre, sans temps mort.

        La voix de la phrase suivante est téléchargée PENDANT que la phrase en
        cours est lue. Sans cela, on entendait une pause entre chaque phrase :
        le temps d'aller chercher la voix chez Microsoft.
        """
        voice_id = self._robot_voice() or voice_id
        os.makedirs(DATA_DIR, exist_ok=True)
        total = len(textes)
        robot = self._robot

        # Un nom de fichier différent pour chaque phrase : deux aperçus rapides
        # ne peuvent plus se supprimer mutuellement le fichier en cours.
        def chemin(rang):
            return os.path.join(DATA_DIR,
                                f"apercu_{os.getpid()}_{numero}_{rang}.mp3")

        def chemin_wav(rang):
            return os.path.join(DATA_DIR,
                                f"apercu_{os.getpid()}_{numero}_{rang}.wav")

        tache = asyncio.create_task(
            self._telecharger_voix(textes[0][1], voice_id, chemin(1)))
        try:
            for rang, (nom, texte) in enumerate(textes, start=1):
                # « Arrêter » a incrémenté le numéro : on s'arrête là.
                if self._apercu_no != numero:
                    break
                self._dire(t("etat_ecoute", rang=rang, total=total, nom=nom))
                try:
                    await tache              # la voix de CETTE phrase
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
                        self._telecharger_voix(textes[rang][1], voice_id,
                                               chemin(rang + 1)))
                if self._apercu_no != numero:
                    break
                source = chemin(rang)
                wav = chemin_wav(rang)
                try:
                    convertir_en_wav(source, wav)
                    if robot:
                        appliquer_effet_robot(wav, robot, "fr" if voice_id.startswith("fr-") else "en")
                    ameliorer_niveau_wav(wav)
                    source = wav
                except Exception as e:
                    if self._apercu_no == numero:
                        self.after(0, lambda err=e: self._message(
                            t("msg_apercu_echec", err=err),
                            icone="erreur"))
                    break
                lecture = LectureAudio(source)
                self._lecture = lecture
                # On attend la fin de la lecture SANS bloquer la boucle : c'est
                # ce qui laisse le téléchargement de la suite avancer.
                await asyncio.to_thread(lecture.wait)
        finally:
            if not tache.done():
                tache.cancel()
            for rang in range(1, total + 1):
                for fichier in (chemin(rang), chemin_wav(rang)):
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
        cochees = [l for l in self.lignes if l["var_check"].get()]
        if not cochees:
            self._message(t("msg_generer_rien"), icone="attention")
            return

        taches = []
        refuses = []
        vus = {}
        for l in cochees:
            nom = l["entry_nom"].get().strip()
            texte = l["entry_txt"].get().strip()
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
            elif texte:
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

        self.btn_letsgo.configure(state="disabled", fg_color="#0A5C66")
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
            self.after(0, lambda: self.btn_letsgo.configure(state="normal", fg_color="#04C3D4"))

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
        reseau_suite = 0
        coupe_reseau = False

        self._dire(t("etat_recherche_service"))

        for idx, (nom, texte) in enumerate(taches):
            temp_mp3 = os.path.join(self.output_dir, f"{nom}_temp.mp3")
            final_wav = os.path.join(self.output_dir, f"{nom}.wav")
            fait = idx + 1
            try:
                self._dire(t("etat_recherche_voix", fait=fait, total=total,
                             nom=nom))
                await sauver_voix(texte, voice_id, temp_mp3,
                                  pitch=self._robot_pitch(), rate=self._robot_rate())
                self._dire(t("etat_generation_wav", fait=fait, total=total,
                             nom=nom))
                convertir_en_wav(temp_mp3, final_wav)
                self._appliquer_robot(final_wav)
                ameliorer_niveau_wav(final_wav)
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
            finally:
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)

            val = fait / total
            self.after(0, lambda v=val: self.progress.set(v))
            self._dire(t("etat_avance", fait=fait, total=total, nom=nom,
                         s="s" if fait > 1 else ""))

        # On laisse la barre complete visible : c'est le seul moment ou
        # l'on voit la derniere led allumee.
        await asyncio.sleep(PAUSE_LEDS)
        self.after(0, lambda: self.progress.reset())
        self._dire("")

        reussis = max(total - (len(echecs) - nb_refuses), 0)
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
            lignes, langue_csv, depuis_cache = csv_officiel_sons_systeme(
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
        self._sons_stop = threading.Event()
        self.btn_letsgo.configure(
            text=t("arreter"), command=self._arreter_sons_systeme,
            fg_color="#0A5C66")
        self.progress.set(0.0)
        self._dire(t("etat_recherche_service"))

        threading.Thread(
            target=self._lancer_sons_systeme,
            args=(taches, refuses, sortie, langue_csv, voice_id, depuis_cache),
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
            self.btn_letsgo.configure(state="disabled", fg_color="#0A5C66")
        except Exception:
            pass
        self._dire(t("etat_sons_arret"))

    def _lancer_sons_systeme(self, taches, refuses, sortie, langue_csv,
                             voice_id, depuis_cache=False):
        """Fil de travail : la boucle asyncio de la création des sons."""
        try:
            asyncio.run(self._generer_sons_systeme(
                taches, refuses, sortie, langue_csv, voice_id, depuis_cache))
        finally:
            try:
                self.after(0, self._fin_sons_systeme)
            except Exception:
                pass  # la fenêtre se ferme : tant pis pour le bouton

    def _fin_sons_systeme(self):
        """Le bouton redevient « Let's Go » une fois la génération terminée."""
        self._sons_stop = None
        self._genere = False
        try:
            self.btn_letsgo.configure(
                state="normal", text=t("lets_go"),
                command=self.start_generation, fg_color="#04C3D4")
        except Exception:
            pass

    async def _generer_sons_systeme(self, taches, refuses, sortie,
                                    langue_csv="", voice_id="",
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
                                      pitch=self._robot_pitch(), rate=self._robot_rate())
                    self._dire(t("etat_generation_wav", fait=traite,
                                 total=total, nom=nom))
                    convertir_en_wav(temp_mp3, temp_wav)
                    self._appliquer_robot(temp_wav)
                    ameliorer_niveau_wav(temp_wav)
                    os.replace(temp_wav, final_wav)
                    faits += 1
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
            if langue_csv:
                texte += "\n\n" + t("msg_sons_copier", langue=langue_csv)
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


if __name__ == "__main__":
    app = VoxPackApp()
    app.mainloop()