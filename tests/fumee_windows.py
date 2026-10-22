"""Vérifications rapides du code, sur la machine Windows du robot.

Les trois cas ci-dessous ont échoué chez des utilisateurs en octobre 2026, et
aucun ne se voyait sur le Mac de Richard : ils tournent donc avant la
fabrication, et avant la publication. Si l'un casse, rien n'est publié.

    python tests/fumee_windows.py

Ce fichier ne fait PAS partie de l'application : il n'est ni importé par elle,
ni embarqué dans le .exe. Il n'ajoute aucun octet pour l'utilisateur.
"""

import os
import sys
import tempfile
import wave

import numpy as np

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

import voxpack                                    # noqa: E402  (après le chemin)

ECHECS = []


def verifier(condition, message):
    if condition:
        print(f"    ok    {message}")
    else:
        print(f"    ÉCHEC {message}")
        ECHECS.append(message)


def ecrire_wav(chemin, donnees, taux=32000):
    with wave.open(chemin, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taux)
        w.writeframes(
            (np.clip(donnees, -1, 1) * 32767).astype("<i2").tobytes())


def lire_wav(chemin):
    with wave.open(chemin) as w:
        return (w.getframerate(), w.getnchannels(), w.getsampwidth(),
                np.frombuffer(w.readframes(w.getnframes()),
                              dtype="<i2").astype(np.float32) / 32768.0)


def ton(sr, duree, amplitude=0.3, frequence=440.0):
    t = np.arange(int(duree * sr)) / sr
    return amplitude * np.sin(2 * np.pi * frequence * t)


def test_conversion_nom_temporaire(dossier):
    """La 1.4.1 écrivait les sons système en « 0000.wav.tmp ».

    Sur PC, soundfile devinait le format d'après l'extension et refusait : les
    212 sons échouaient. Sur Mac, afconvert s'en moquait, d'où le bug invisible.
    """
    print("1. conversion vers un nom en .tmp (le bug des 212 sons système)")
    source = os.path.join(dossier, "source.wav")
    ecrire_wav(source, ton(24000, 0.3), 24000)
    cible = os.path.join(dossier, "son.wav.tmp")
    try:
        voxpack.convertir_en_wav(source, cible)
    except Exception as e:
        verifier(False, f"la conversion en .tmp n'a pas levé d'erreur ({e})")
        return
    verifier(os.path.exists(cible), "le fichier en .tmp existe")
    if os.path.exists(cible):
        taux, canaux, octets, _ = lire_wav(cible)
        verifier((taux, canaux, octets) == (32000, 1, 2),
                 "format EdgeTX : 32 kHz, mono, 16 bits")


def test_traitement_niveau(dossier):
    """Coupe des silences, limiteur, normalisation, fondu de sortie."""
    print("2. traitement du niveau (silence coupé, parole gardée, fin douce)")
    sr = 32000
    chemin = os.path.join(dossier, "niveau.wav")
    x = np.concatenate([ton(sr, 0.4), np.zeros(int(0.6 * sr))])
    ecrire_wav(chemin, x, sr)
    voxpack.ameliorer_niveau_wav(chemin)
    taux, canaux, octets, y = lire_wav(chemin)
    verifier((taux, canaux, octets) == (32000, 1, 2), "format conservé")
    verifier(len(y) < len(x), "le silence de la fin est bien coupé")
    verifier(len(y) > int(0.35 * sr), "la phrase elle-même n'est pas coupée")
    verifier(float(np.max(np.abs(y))) > 0.95, "le niveau est monté au maximum")
    fin = float(np.max(np.abs(y[-int(0.02 * sr):])))
    niveau_fin = 20 * np.log10(fin + 1e-12)
    verifier(niveau_fin < -40,
             f"le fichier se termine en douceur ({niveau_fin:.0f} dBFS)")


class Champ:
    """Imite une case de saisie de l'interface, pour tester hors interface."""

    def __init__(self, valeur):
        self.valeur = valeur

    def get(self):
        return self.valeur


def test_enregistrement_liste(dossier):
    """Temporaire + renommage, avec les trois essais (WinError 5)."""
    print("3. enregistrement de la liste (temporaire, renommage, essais)")
    ancien = voxpack.DATA_DIR
    voxpack.DATA_DIR = dossier

    class Faux:
        langue = "en"

        def __init__(self):
            self.lignes = [{"entry_nom": Champ("armed"),
                            "entry_txt": Champ("Armed")}]
            self._bak_faits = set()
            self._erreur_sauvegarde = False
            self.alertes = 0

        def after(self, delai, fonction):
            self.alertes += 1

    faux = Faux()
    try:
        voxpack.VoxPackApp._ecrire_csv(faux)
        fichier = voxpack.chemin_liste("en")
        verifier(os.path.exists(fichier), "le fichier de liste est écrit")
        if os.path.exists(fichier):
            with open(fichier, encoding="utf-8") as f:
                contenu = f.read()
            verifier("armed" in contenu, "la ligne y est bien")
        verifier(not faux._erreur_sauvegarde, "aucune erreur signalée")
        verifier(not os.path.exists(fichier + ".tmp"),
                 "aucun temporaire laissé derrière")
    finally:
        voxpack.DATA_DIR = ancien


def main():
    print(f"Vérifications sur {sys.platform} — Vox-Pack {voxpack.VERSION}\n")
    with tempfile.TemporaryDirectory() as dossier:
        test_conversion_nom_temporaire(dossier)
        test_traitement_niveau(dossier)
        test_enregistrement_liste(dossier)
    print()
    if ECHECS:
        print(f"{len(ECHECS)} vérification(s) en échec : rien ne doit être publié.")
        return 1
    print("Tout est vert : le code Windows fait ce qu'on attend de lui.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
