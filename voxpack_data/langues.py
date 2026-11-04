"""Les langues d'EdgeTX — source unique pour la v2.

Une ligne par langue, et rien d'autre : le nom natif (pour le sélecteur), le
dossier SD où EdgeTX range les sons, la voix officielle de l'équipe EdgeTX,
son allure, et le CSV du dépôt `edgetx-sdcard-sounds`.

D'où viennent ces valeurs, et pourquoi on ne les invente pas :

- la recette officielle (`voice_generation_config.py`, dépôt
  `EdgeTX/edgetx-sdcard-sounds`) donne la voix, le dossier et l'allure ;
- les pièges de nommage y sont réels : le tchèque est en `cz`, le suédois en
  `se`, le japonais en `jp`, l'ukrainien en `ua-ostap`, et le portugais se
  dit avec la voix **brésilienne** (`pt-BR-FranciscaNeural`) alors que le CSV
  s'appelle `pt-PT.csv` ;
- le danois est `da_DK.csv`, avec un **souligné** — le seul du lot.

Le module sait se revérifier : `python -m voxpack_data.langues` retélécharge la
recette et compare, ligne à ligne. C'est ce qui empêche la table de vieillir
en silence.
"""

from __future__ import annotations

import csv
import io
import re
import sys
import urllib.request
from dataclasses import dataclass

RECETTE = ("https://raw.githubusercontent.com/EdgeTX/edgetx-sdcard-sounds"
           "/master/voice_generation_config.py")
DEPOT = ("https://raw.githubusercontent.com/EdgeTX/edgetx-sdcard-sounds"
         "/master/")


@dataclass(frozen=True)
class Langue:
    """Une langue de sons, telle qu'EdgeTX la publie."""

    code: str          # identifiant interne, stable ("fr", "cn")
    nom: str           # nom natif, affiché tel quel ("Français", "日本語")
    dossier: str       # dossier SD ("fr", "cz", "ua-ostap")
    voix: str          # voix officielle edge-tts
    voix_nom: str      # son nom court ("Denise")
    csv: str           # fichier du dépôt ("voices/fr-FR.csv")
    vitesse: float = 1.0    # allure officielle (1.10 = +10 %)
    hauteur: str = ""       # décalage officiel, forme edge-tts ("-10Hz")

    @property
    def pour_cent(self) -> int:
        """L'allure officielle, en pour cent, pour le curseur VITESSE."""
        return round((self.vitesse - 1.0) * 100)

    def phrase(self) -> str:
        """La ligne du sélecteur : `/SOUNDS/hk · HiuGaai`."""
        return f"/SOUNDS/{self.dossier} · {self.voix_nom}"


# Quinze langues : toutes celles de la recette, moins l'espagnol du Chili
# (`es_cl-catalina`), écarté par Richard le 29 octobre. L'ukrainien n'apparaît
# qu'une fois, avec la voix d'Ostap ; Polina reste disponible comme voix
# secondaire, mais elle ne change ni le dossier ni le CSV.
LANGUES: tuple[Langue, ...] = (
    Langue("cs", "Čeština", "cz", "cs-CZ-VlastaNeural", "Vlasta",
           "voices/cs-CZ.csv"),
    Langue("da", "Dansk", "da", "da-DK-ChristelNeural", "Christel",
           "voices/da_DK.csv"),
    Langue("de", "Deutsch", "de", "de-DE-KatjaNeural", "Katja",
           "voices/de-DE.csv"),
    Langue("en", "English", "en", "en-IE-EmilyNeural", "Emily",
           "voices/en-GB.csv", vitesse=1.10),
    Langue("es", "Español", "es", "es-ES-ElviraNeural", "Elvira",
           "voices/es-ES.csv"),
    Langue("fr", "Français", "fr", "fr-FR-DeniseNeural", "Denise",
           "voices/fr-FR.csv"),
    Langue("it", "Italiano", "it", "it-IT-ElsaNeural", "Elsa",
           "voices/it-IT.csv"),
    Langue("ja", "日本語", "jp", "ja-JP-NanamiNeural", "Nanami",
           "voices/ja-JP.csv"),
    Langue("pt", "Português", "pt", "pt-BR-FranciscaNeural", "Francisca",
           "voices/pt-PT.csv"),
    Langue("ru", "Русский", "ru", "ru-RU-SvetlanaNeural", "Svetlana",
           "voices/ru-RU.csv"),
    Langue("sv", "Svenska", "se", "sv-SE-SofieNeural", "Sofie",
           "voices/sv-SE.csv", vitesse=0.9, hauteur="-10Hz"),
    Langue("uk", "Українська", "ua-ostap", "uk-UA-OstapNeural", "Ostap",
           "voices/uk-UA.csv"),
    Langue("cn", "中文（简体）", "cn", "zh-CN-XiaoxiaoNeural", "Xiaoxiao",
           "voices/zh-CN.csv"),
    Langue("tw", "中文（繁體）", "tw", "zh-TW-HsiaoChenNeural", "HsiaoChen",
           "voices/zh-TW.csv"),
    Langue("hk", "粵語（香港）", "hk", "zh-HK-HiuGaaiNeural", "HiuGaai",
           "voices/zh-HK.csv", vitesse=0.9),
)

# Les dossiers de la recette qu'on ne prend pas, avec la raison. Sans cette
# liste, la vérification signalerait éternellement les mêmes sept lignes, et
# on ne verrait plus les vrais écarts.
IGNORES = {
    "es_cl-catalina": "écarté par Richard le 29 octobre (espagnol du Chili)",
    "ua-polina": "seconde voix ukrainienne ; le dossier officiel est ua-ostap",
    "en_gb-libby": "voix anglaise alternative ; le dossier officiel est en",
    "en_gb-ryan": "voix anglaise alternative ; le dossier officiel est en",
    "en_us-guy": "voix américaine alternative ; le dossier officiel est en",
    "en_us-michelle": "voix américaine alternative ; le dossier officiel est en",
    "en_us-sara": "voix américaine alternative ; le dossier officiel est en",
}

PAR_CODE = {langue.code: langue for langue in LANGUES}
PAR_DOSSIER = {langue.dossier: langue for langue in LANGUES}
VOIX_OFFICIELLES = {langue.voix: langue.code for langue in LANGUES}


def langue(code: str) -> Langue:
    """La langue demandée ; le français si le code est inconnu.

    Un code inconnu peut venir d'un `reglages.json` écrit par une version
    plus récente : mieux vaut retomber sur le français que de planter au
    démarrage.
    """
    return PAR_CODE.get(code, PAR_CODE["fr"])


def dossiers() -> set[str]:
    return {langue.dossier for langue in LANGUES}


# ---------------------------------------------------------------------
# Les sons système officiels
# ---------------------------------------------------------------------
def lire_csv_complet(texte: str) -> list[tuple[str, str, str]]:
    """Tout le CSV officiel : [(dossier, nom, phrase)].

    Le dossier vaut `SYSTEM` ou `""` (la racine). Les deux comptent : les
    annonces de la radio sont à la racine (`armed`, `gearup`, `attero`…), les
    sons de l'interface dans `SYSTEM`. C'est un piège du fichier — on croit
    chercher `armed` dans `SYSTEM`, et il n'y est pas.
    """
    lignes = list(csv.reader(io.StringIO(texte, newline="")))
    if not lignes:
        return []
    entete = [c.strip().lower() for c in lignes[0]]
    if not all(c in entete for c in ("translation", "path", "filename")):
        return []
    i_phrase = entete.index("translation")
    i_dossier = entete.index("path")
    i_nom = entete.index("filename")
    sons = []
    for colonnes in lignes[1:]:
        if len(colonnes) <= max(i_phrase, i_dossier, i_nom):
            continue
        nom = colonnes[i_nom].strip()
        phrase = colonnes[i_phrase].strip()
        if nom.lower().endswith(".wav"):
            nom = nom[:-4]
        if nom and phrase:
            sons.append((colonnes[i_dossier].strip().upper(), nom, phrase))
    return sons


def lire_csv_officiel(texte: str) -> list[tuple[str, str]]:
    """Les seuls sons du dossier SYSTEM : [(nom, phrase)].

    C'est ce que l'application refabrique (« Créer les sons système ») : la
    racine mélange les annonces officielles et les sons personnels de
    l'utilisateur (décision de Richard, reprise de la 1.5.1).
    """
    return [(nom, phrase) for dossier, nom, phrase in lire_csv_complet(texte)
            if dossier == "SYSTEM"]


def telecharger(chemin_relatif: str, delai: int = 20,
                age_max: int = 7 * 24 * 3600) -> str:
    """Le fichier du dépôt EdgeTX, en texte, avec une copie de secours.

    `certifi` fournit le trousseau de certificats, comme dans la 1.5.1 :
    sans lui, urllib refuse le HTTPS sur un Python installé par Homebrew.

    Une copie est gardée une semaine : changer de langue dans l'interface ne
    doit pas relancer un téléchargement à chaque clic. Si le réseau est
    coupé, on se rabat sur la copie, même vieille — mieux vaut une liste
    d'hier que pas de liste du tout.
    """
    import ssl
    import tempfile
    import time
    from pathlib import Path

    dossier = Path(tempfile.gettempdir()) / "voxpack-remote"
    dossier.mkdir(parents=True, exist_ok=True)
    copie = dossier / chemin_relatif.replace("/", "_")
    age = time.time() - copie.stat().st_mtime if copie.exists() else None
    if age is not None and age < age_max:
        return copie.read_text(encoding="utf-8-sig")

    try:
        import certifi
        contexte = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        contexte = ssl.create_default_context()
    try:
        with urllib.request.urlopen(DEPOT + chemin_relatif, timeout=delai,
                                    context=contexte) as reponse:
            texte = reponse.read().decode("utf-8-sig")
    except Exception:
        if copie.exists():
            return copie.read_text(encoding="utf-8-sig")
        raise
    copie.write_text(texte, encoding="utf-8-sig")
    return texte


# Les annonces qui nous intéressent, dans l'ordre où un modéliste les
# cherche : armement, train, volets, chrono, modes de vol, batterie.
# C'est notre choix éditorial — les phrases, elles, viennent d'EdgeTX.
PHRASES_UTILES = [
    "armed", "disarm", "gearup", "geardn", "flapup", "flapdn", "attero",
    "engoff", "midtrim", "maxtrim", "mintrim", "timovr1", "timovr2",
    "timovr3", "spdmod", "thmmod", "nrmmod", "lnding", "acro", "lvlmod",
    "fm-1", "fm-2", "fm-3", "fm-pwr", "fm-lnd", "fm-spd", "fm-nrm",
    "fm-crs", "fm-acr", "lowbatt", "inactiv", "hello", "trnon", "trnoff",
]


def liste_de_depart(langue: Langue) -> list[tuple[str, str]]:
    """Les annonces officielles d'une langue : [(nom, phrase)].

    Sert de liste de départ à l'application dans la langue choisie. On ne
    garde que les annonces de **racine** : ce sont les messages de la radio
    (« moteur armé », « train rentré »), pas les sons de l'interface.

    Rien n'est embarqué : les phrases sont sous GPL chez EdgeTX, Vox-Pack est
    en MIT. On les lit donc à l'usage, comme le fait la 1.5.1 — et le nom de
    fichier officiel (`armed`, `timovr1`…) tient toujours en huit caractères,
    la limite de l'écran de la radio.
    """
    morceaux = lire_csv_complet(telecharger(langue.csv))
    # Les deux dossiers comptent : `hello` (« Bienvenue sur EdgeTX ») est un
    # son de SYSTEM, la plupart des autres sont à la racine. Quand un nom
    # existe dans les deux, la racine l'emporte — c'est l'annonce de la radio.
    phrases = {}
    for dossier, nom, phrase in morceaux:
        if dossier != "SYSTEM" or nom not in phrases:
            phrases[nom] = phrase
    return [(nom, phrases[nom]) for nom in PHRASES_UTILES if nom in phrases]


def sons_systeme(langue: Langue) -> list[tuple[str, str]]:
    """Télécharge la liste officielle d'une langue et rend ses sons SYSTEM."""
    return lire_csv_officiel(telecharger(langue.csv))


# ---------------------------------------------------------------------
# La vérification
# ---------------------------------------------------------------------
def lire_recette(texte: str) -> dict[str, dict]:
    """Extrait de la recette les tâches de voix Azure, par dossier SD.

    On ne lit que la forme qui nous intéresse — `AzureVoiceJob(csv, voix,
    dossier, pitch=…, rate=…)` — et on ignore les tâches `SCRIPTS`, qui
    servent les scripts embarqués et non les sons de la radio.
    """
    taches = {}
    motif = re.compile(r"AzureVoiceJob\((.*?)\)\s*,", re.S)
    for brute in motif.findall(texte):
        morceaux = dict(re.findall(r'(\w+)=("[^"]*"|[\d.]+)', brute))
        args = re.findall(r'"([^"]*)"', brute)
        if len(args) < 3:
            continue
        csv, voix, dossier = args[0], args[1], args[2]
        if dossier.endswith("/SCRIPTS") or dossier == "SCRIPTS":
            continue
        taches[dossier] = {
            "voix": voix,
            "csv": csv.lstrip("./"),
            "rate": morceaux.get("rate", "").strip('"'),
            "pitch": morceaux.get("pitch", "").strip('"'),
        }
    return taches


def verifier(taches: dict[str, dict]) -> list[str]:
    """Compare la table à la recette. Rend la liste des désaccords."""
    ecarts = []
    for langue_ in LANGUES:
        officielle = taches.get(langue_.dossier)
        if officielle is None:
            ecarts.append(f"{langue_.code} : dossier « {langue_.dossier} » "
                          f"absent de la recette")
            continue
        if officielle["voix"] != langue_.voix:
            ecarts.append(f"{langue_.code} : voix {officielle['voix']} "
                          f"dans la recette, {langue_.voix} ici")
        if officielle["csv"] != langue_.csv:
            ecarts.append(f"{langue_.code} : CSV {officielle['csv']} "
                          f"dans la recette, {langue_.csv} ici")
        rate = officielle["rate"]
        if rate and abs(float(rate) - langue_.vitesse) > 0.001:
            ecarts.append(f"{langue_.code} : allure {rate} dans la recette, "
                          f"{langue_.vitesse} ici")
        pitch = officielle["pitch"]
        if pitch and pitch.replace("dn", "-").replace("%", "Hz") != langue_.hauteur:
            ecarts.append(f"{langue_.code} : hauteur {pitch} dans la recette, "
                          f"{langue_.hauteur or 'aucune'} ici")
    connus = set(PAR_DOSSIER) | set(IGNORES)
    for dossier in sorted(set(taches) - connus):
        ecarts.append(f"dossier « {dossier} » dans la recette, absent de la table")
    return ecarts


def main() -> int:
    with urllib.request.urlopen(RECETTE, timeout=20) as reponse:
        texte = reponse.read().decode()
    taches = lire_recette(texte)
    ecarts = verifier(taches)
    print(f"{len(taches)} dossiers dans la recette, {len(LANGUES)} langues dans "
          f"la table, {len(IGNORES)} dossiers écartés volontairement")
    if not ecarts:
        print("aucun écart : la table est à jour")
        return 0
    for ecart in ecarts:
        print("  écart :", ecart)
    return 1


if __name__ == "__main__":
    sys.exit(main())
