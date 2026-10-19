# Demande : générer les sons système d'EdgeTX

*Note prise le 18 octobre 2026, pour ne rien perdre. **Codé le 18 octobre au
soir** : voir « Réalisé » en fin de note. La source est la liste officielle
d'EdgeTX (voir « Source changée ») ; il reste à l'essayer dans l'application.*

## La demande

Posée sur RCGroups, dans le fil officiel « Official EdgeTX Discussion Thread »,
par **3djc**, présenté comme **« Former ETX and OTX dev »** — un ancien
développeur d'EdgeTX et d'OpenTX, c'est-à-dire l'auteur probable des fichiers
CSV ci-dessous.

> « it would be nice to have automated support for the system sound, so that
> the same voice is used accros the radio. csv for those can be found here :
> https://github.com/EdgeTX/edgetx-sdcard-sounds »

**Le moyen demandé** : générer les **sons système** de la radio.
**Le but** : qu'une **seule voix** soit utilisée partout dans la radio.

C'est différent — et plus fort — que « faire ressembler nos fichiers à ceux
d'EdgeTX » : 3djc veut **garder le choix de la voix** et que **tout** parle
avec elle, y compris les sons système.

## Le format des fichiers d'EdgeTX

Dépôt : `https://github.com/EdgeTX/edgetx-sdcard-sounds`
Fichiers : `voices/fr-FR.csv`, `voices/en-GB.csv`, … (18 langues)

```
"String ID","Source text","Translation","Context","Path","Filename"
"1","0","0","","SYSTEM","0000.wav"
"568","wings folded","wings folded","","","vgfldd.wav"
```

- **568 lignes** (dont un en-tête), **6 colonnes**
- **colonne 3 « Translation »** → la phrase à prononcer
- **colonne 6 « Filename »** → le nom du fichier (sans `.wav`)
- séparateur virgule, guillemets → notre `lire_lignes_csv()` le lit déjà,
  mais il faudra un **import dédié** : l'import actuel prend les colonnes 1 et 2,
  ce qui donnerait « String ID » et « Source text » — faux.

## Les voix officielles (dans `voice_generation_config.py`)

Chaque langue a **sa** voix, choisie par l'équipe EdgeTX — et parfois une
vitesse ou une hauteur particulières :

| langue | voix | réglage |
|---|---|---|
| français | `fr-FR-DeniseNeural` | — *(déjà notre défaut)* |
| anglais | `en-IE-EmilyNeural` | **vitesse 1.10** |
| allemand | `de-DE-KatjaNeural` | — |
| italien | `it-IT-ElsaNeural` | — |
| espagnol | `es-ES-ElviraNeural` | — |
| portugais | `pt-BR-FranciscaNeural` | — *(voix brésilienne)* |
| russe | `ru-RU-SvetlanaNeural` | — |
| suédois | `sv-SE-SofieNeural` | **hauteur −10 %, vitesse 0.9** |
| ukrainien | `uk-UA-OstapNeural` | — |
| tchèque | `cs-CZ-VlastaNeural` | — |
| danois | `da-DK-ChristelNeural` | — |
| japonais | `ja-JP-NanamiNeural` | — |
| chinois (mandarin) | `zh-CN-XiaoxiaoNeural` | — |
| chinois (Taïwan) | `zh-TW-HsiaoChenNeural` | — |
| chinois (Canton) | `zh-HK-HiuGaaiNeural` | vitesse 0.9 |

Variantes existantes : anglais Libby / Ryan / Guy / Michelle / Sara, espagnol
chilien, ukrainien Polina.

Ils utilisent **Azure** — le même service qu'`edge-tts`. Nos fichiers peuvent
donc être **identiques** aux leurs.

## ⚠️ La licence : GPL-2.0

Le dépôt est en **GNU GPL v2**, Vox-Pack en **MIT**.

- **Copier leurs CSV ou leurs sons dans Vox-Pack** → impossible sans passer
  Vox-Pack en GPL.
- **Lire un CSV que l'utilisateur fournit lui-même** → autorisé, et c'est ce
  que fait Vox-Pack aujourd'hui.
- **La solution retenue** : l'utilisateur télécharge son CSV chez EdgeTX et
  l'importe. Nous n'embarquons **rien** de chez eux.

> **Depuis le 18 octobre au soir**, c'est l'application qui va chercher le
> fichier officiel chez EdgeTX, au moment de l'usage (voir « Source changée »).
> Le principe ne change pas : **rien n'est embarqué** dans Vox-Pack, et le
> fichier reste chez l'utilisateur. Ne jamais en mettre une copie dans le
> dépôt.

Question posée à 3djc dans le fil, en même temps que la réponse à sa demande.

## Ce que contient la carte de Richard (relevé le 18 octobre)

```
SOUNDS/en/SYSTEM   213 fichiers        SOUNDS/en/SCRIPTS   3
SOUNDS/fr/SYSTEM   189 fichiers        SOUNDS/fr/SCRIPTS   3
```

- **Le pack français est incomplet de 24 sons** : EdgeTX a ajouté des sons en
  anglais, la traduction n'a pas suivi. **Vox-Pack pourrait les compléter.**
- **Les noms sont identiques d'une langue à l'autre** (`0000.wav`, …) : seule
  la phrase change. On peut donc croiser le dossier de la carte avec le CSV.
- **Ailleurs sur la carte** : `WIDGETS/Flights/` (8 sons du widget, à ne pas
  toucher), `SCRIPTS/TOOLS/*INUTILE/` (un vieil outil Lua), et
  `Speech tools/` (l'outil d'un module vocal CI-03T, sans rapport).
- Sa carte est **en 2.10** alors que sa radio est en **2.12.4** : les sons
  officiels sont en retard, il va télécharger une carte à jour.

## La piste retenue (à valider par Richard)

1. **Lire le dossier `SYSTEM/`** de la carte, pas supposer un nombre fixe —
   il change à chaque version (189 → 213 → …).
2. **Croiser avec le CSV** pour retrouver la phrase de chaque nom.
3. **Générer** avec la voix choisie par l'utilisateur — et proposer
   **de compléter** les sons manquants de la langue.
4. **Ajouter la vitesse** (`rate` d'`edge-tts`) pour reproduire les réglages
   officiels — et une entrée « comme la radio » dans la liste des voix.
5. **Limite de 8 caractères** pour le nom des fichiers (6 avant EdgeTX 2.11).

## Ce qui n'est pas fait

- **Aucune ligne de code** n'a été écrite pour cette fonctionnalité.
- Le plan détaillé, l'ordre des étapes et les tests restent à faire.
- On attend la réponse de 3djc (conventions à respecter, licence).

## 🔑 Découverte du 18 octobre : le CSV est SUR la carte

Dans `SOUNDS/<langue>/SYSTEM/` se trouve un fichier CSV livré avec la carte :

```
SOUNDS/fr/SYSTEM/fr-FR-taranis.csv    224 lignes
SOUNDS/en/SYSTEM/en-US-taranis.csv    245 lignes
```

Format : **trois colonnes séparées par des points-virgules**

```
SOUNDS/fr/SYSTEM;0000.wav;0
SOUNDS/fr;fm-thl.wav;mode de vol thermique gauche
   ↑ dossier        ↑ fichier   ↑ phrase à prononcer
```

- Le compte s'explique : 224 = 189 (SYSTEM) + 35 (racine de la langue)
- **Le CSV est donc plus complet que les fichiers présents** : il liste
  **ce qui devrait exister**, y compris les sons manquants
- Notre `lire_lignes_csv()` gère déjà le séparateur « ; »

**Conséquence majeure** : **plus besoin de télécharger quoi que ce soit, et
plus de question de licence** — Vox-Pack lit **le fichier de l'utilisateur**,
comme n'importe quel CSV qu'il importe déjà.

Et générer **toutes les lignes du CSV** complète le pack : les 24 sons
manquants en français seraient créés.

### Où vont les fichiers

| colonne 1 du CSV | où écrire |
|---|---|
| `SOUNDS/fr/SYSTEM` | dans `SYSTEM/` du dossier de sortie |
| `SOUNDS/fr` | à la racine du dossier de sortie |

Les sons **personnels** de l'utilisateur (`attero.wav`, `motact.wav`…) sont à
la racine de la langue et **ne figurent pas** dans le CSV : ils ne seraient
donc pas touchés.

## Décisions de Richard (18 octobre)

**La source est le CSV du dossier `SYSTEM` de la carte de l'utilisateur** —
c'est-à-dire `SOUNDS/<langue>/SYSTEM/<langue>-taranis.csv`. Aucun
téléchargement, aucune question de licence : c'est **son** fichier.

> **Remplacé le 18 octobre au soir** : la source est désormais la **liste
> officielle d'EdgeTX**, téléchargée par l'application (voir « Source
> changée » plus bas). Tout le reste de cette section reste vrai, en
> particulier : **seuls les sons du dossier SYSTEM** sont générés.

**On génère tout ce que le CSV liste**, et rien d'autre. La colonne 1 dit dans
quel dossier écrire :

| colonne 1 | destination |
|---|---|
| `SOUNDS/fr/SYSTEM` | `SYSTEM/` du dossier de sortie |
| `SOUNDS/fr` | racine du dossier de sortie |

**Hors périmètre** (décidé par Richard) :

- les sons des **SCRIPTS** (Betaflight, INAV…) — pas utilisés dans la radio
- les sons des **widgets** (`WIDGETS/Flights/`)
- les 155 fichiers aux **noms de nombres** (`1008001424.wav`…) : ce sont des
  sons générés par les scripts, absents du CSV
- le dossier `Speech tools` (module vocal CI-03T, sans rapport)

**Chiffres relevés** (croisement du CSV du dépôt et du pack 2.12.3) :

| | CSV du dépôt | pack 2.12.3 | noms manquants |
|---|---|---|---|
| français | 235 | 233 | 2 (`auro`, `lowbat`) |
| anglais | 568 | 723 | 0 ✓ |

Le CSV du dépôt **correspond exactement** au pack ✓ — c'est donc une référence
fiable. Le pack français d'EdgeTX reste très en retard (235 noms contre 568) :
**333 sons ne sont pas traduits**, ce n'est pas le travail de Vox-Pack.

## Correction (18 octobre, après-midi)

Richard a raison : **seuls les sons du dossier `SYSTEM` sont concernés**. Les
autres fichiers (la racine de la langue, les scripts, les widgets) ne sont
**pas** le sujet — ce sont les fichiers personnels de l'utilisateur, qu'il crée
avec sa propre liste.

Le CSV ne sert donc qu'à **une seule chose** : refabriquer **les mêmes fichiers
système**, avec **la voix choisie**.

### Le déroulé retenu — une entrée de menu

```
Menu → « Créer les sons système… »

1. choisir le CSV      SOUNDS/<langue>/SYSTEM/<langue>-taranis.csv
2. la voix             celle déjà sélectionnée dans la fenêtre
3. le dossier d'arrivée il crée un sous-dossier SYSTEM/
4. Let's Go            186 fichiers, tous avec cette voix
```

Puis l'utilisateur copie `SYSTEM/` dans `SOUNDS/<langue>/` de sa carte.

### ⚠️ La précaution essentielle

**Ne jamais toucher à la liste de l'utilisateur.** Le circuit est séparé : on
lit un CSV, on écrit des fichiers, la liste affichée ne bouge pas.

Richard a déjà perdu une liste une fois — on ne recommence pas.

## Source changée (18 octobre, soir) : la liste officielle d'EdgeTX

Richard le dit franchement : **le CSV n'existe que sur sa carte**. Il faudrait
donc la brancher pour le lire, et ce fichier n'est pas forcément à jour (sa
carte est en 2.10). **Décision : Vox-Pack utilise la liste officielle du dépôt
EdgeTX**, téléchargée au moment de l'usage.

- adresse : `github.com/EdgeTX/edgetx-sdcard-sounds` ;
  `voices/fr-FR.csv` pour le français, `voices/en-GB.csv` pour l'anglais (le
  dépôt ne construit `SOUNDS/en` qu'avec en-GB) ;
- **rien n'est embarqué dans Vox-Pack** : le fichier est récupéré chez EdgeTX,
  à la demande de l'utilisateur, et reste chez lui. C'est ce qui permet de
  garder la licence MIT (le dépôt EdgeTX est en GPL) — ne jamais en mettre une
  copie dans le dépôt Vox-Pack ;
- une copie est gardée dans `~/Documents/Vox-Pack/sons-systeme-*.csv` : si
  GitHub ne répond pas, on repart de cette copie, et le bilan le dit ;
- le fichier officiel a **six colonnes** : `Translation` (la phrase), `Path`
  (`SYSTEM`, ou vide pour la racine), `Filename` (le nom). On lit les colonnes
  **par leur nom**, et on filtre sur `Path = SYSTEM` ;
- le dialogue « choisir le CSV » disparaît : on ne choisit plus que le dossier
  d'arrivée.

**Le périmètre ne change pas** : SYSTEM seulement (choix de Richard, 18
octobre). Les chiffres du fichier officiel :

| | SYSTEM | racine | total |
|---|---|---|---|
| français | **186** | 49 (dont 1 sans traduction) | 235 |
| anglais | **212** | 356 | 568 |

Les 49 sons de la racine française sont bien des sons **officiels** (`armed`,
`disarm`, `alt`, `trnon`, `attero`…), pas des sons personnels : ils restent
hors périmètre pour l'instant. `attero.wav` figure d'ailleurs dans la liste
officielle, contrairement à ce que disait la note du 18 octobre.

## Plan d'implémentation (à exécuter dans une session neuve)

*Écrit avant le changement de source : l'étape 1 (choisir le CSV) n'existe
plus, voir « Source changée » ci-dessus. Tout le reste s'applique.*

**Principe** : rien en dur. Le CSV, la voix et le dossier viennent de
l'utilisateur ; seuls le filtrage et l'écriture sont dans le code.

### 1. Entrée de menu

Dans `_construire_menu()`, après « Charger la liste par défaut » :

- FR : « Créer les sons système… »
- EN : « Create the system sounds… »

Nouvelle clé de traduction `menu_sons_systeme` dans `TEXTES["fr"]` et `["en"]`.

### 2. Le circuit (une méthode nouvelle, à côté de `start_generation`)

`creer_sons_systeme()` :

1. `filedialog.askopenfilename` — filtré sur `*.csv`, titre explicite.
   L'utilisateur choisit `SOUNDS/<langue>/SYSTEM/<langue>-taranis.csv`.
2. `filedialog.askdirectory` — le dossier d'arrivée. On écrit dans un
   sous-dossier `SYSTEM/` créé dedans (jamais à la racine du dossier choisi).
3. La voix est **celle déjà sélectionnée** dans `combo_voice` — rien à choisir.
4. Lancement dans un fil, comme `start_generation`, avec la barre de
   progression et la ligne d'état.

### 3. Lecture du CSV

- Séparateur : `;` (réutiliser `lire_lignes_csv`, qui le détecte).
- **Garder uniquement les lignes dont la colonne 1 finit par `/SYSTEM`**.
  Les lignes de la racine (`SOUNDS/fr;fm-thl.wav;…`) sont **ignorées**.
- Nom du fichier = colonne 2 sans `.wav`. Phrase = colonne 3.
- Vérifier `probleme_nom()` sur chaque nom ; signaler les refusés, ne pas
  interrompre le reste.

### 4. Écriture

- Un `.wav` par ligne, même pipeline que `_generer` (`convertir_en_wav`).
- Les fichiers vont dans `<dossier choisi>/SYSTEM/`.
- **Ne pas toucher** à `self.lignes`, ni au CSV de l'utilisateur, ni à ses
  réglages. Le circuit est autonome.
- À la fin : un bilan (« N fichiers créés dans SYSTEM/ ») + un bouton
  « Ouvrir le dossier ».

### 5. Points à trancher pendant le développement

- **La durée** : 186 fichiers × ~1 s = ~4 minutes. La temporisation actuelle
  (par ligne) est peut-être trop lente ; prévoir un mode sans pause.
  → **Mesuré le 18 octobre** sur 8 vrais sons, avec le circuit de
  l'application : 0,8 à 2,2 s par fichier, **1,2 s en moyenne**. Donc
  **≈ 3 min 40 s pour les 186 sons français** (≈ 4 min pour les 212 anglais).
  Il n'y a aucune pause entre les fichiers : rien à changer.
- **La reprise** : si l'utilisateur annule, les fichiers déjà écrits restent.
  Faut-il un bouton « Annuler » propre ?
- **Les doublons** : le CSV ne devrait pas en contenir, mais vérifier.

### 6. Tests

- Le CSV de la carte 2.10 (`fr-FR-taranis.csv`, 224 lignes) → 189 fichiers
  attendus dans `SYSTEM/`.
- Aucune modification de la liste affichée après l'opération.
- Le format des fichiers produits : 32 kHz, mono, PCM 16 bits.
- Lancer aussi avec `en-US-taranis.csv` (245 lignes).
- Vérifier avec un CSV vide et un CSV sans ligne `/SYSTEM`.

## Réalisé (18 octobre, soir)

*Le code est écrit et vérifié avec le vrai fichier officiel ; il reste à
l'essayer dans l'application, puis à copier le dossier sur la carte.*

- **Entrée de menu** *Fichier → « Créer les sons système… »*, dans les deux
  langues (sans « avec ma voix » : la voix est celle déjà choisie).
- **La liste officielle est téléchargée** au moment de l'usage (`fr-FR.csv` ou
  `en-GB.csv`) : on ne choisit plus que le dossier d'arrivée, et la voix est
  celle déjà sélectionnée.
- **Seules les lignes `Path = SYSTEM`** sont générées (186 en français, 212 en
  anglais). Les lignes de la racine sont ignorées, comme décidé.
- Les fichiers vont dans `<dossier choisi>/SYSTEM/` ; si l'utilisateur a
  lui-même choisi un dossier nommé `SYSTEM`, on n'en crée pas un deuxième.
- Les noms sont vérifiés (`probleme_nom`) et les **doublons** signalés : les
  noms fautifs sont refusés, les autres continuent. Bilan à la fin, avec les
  raisons et un bouton « Ouvrir le dossier ».
- **La fenêtre d'aide** a un bloc « Créer les sons système » : la démarche, le
  temps (≈ 1,2 s par son, ~4 min), le bouton Arrêter et la copie sur la carte.
- **Les voix officielles d'EdgeTX** sont marquées **★** dans le sélecteur :
  Denise pour le français (déjà là) et **Emily** (`en-IE-EmilyNeural`, ajoutée)
  pour l'anglais. L'anglais est réglé à **+10 %** de vitesse, comme EdgeTX ;
  l'aide explique l'étoile.
- **`self.lignes` n'est jamais lue ni modifiée** : la liste de l'utilisateur
  ne bouge pas, pas plus que sa voix et sa langue (on retient seulement le
  dernier dossier choisi, comme pour « Let's Go »).
- Le bouton « Let's Go » devient **« ■ Arrêter »** pendant l'opération : le
  fichier en cours se termine, les fichiers déjà écrits restent.
- Les MP3 de travail vivent dans le dossier temporaire du système, et le WAV
  n'est posé dans `SYSTEM/` **qu'une fois complet** : aucune carte SD ne
  reçoit de fichier tronqué.

### Essais faits (18 octobre)

- Vrai fichier officiel téléchargé : **186 sons SYSTEM en français**, **212 en
  anglais**, lignes de la racine ignorées.
- Copie de secours : après une panne réseau simulée, les 186 sons sont relus
  depuis la copie, et le bilan le dit ; sans copie, l'application affiche un
  message clair.
- Format officiel à six colonnes (colonnes lues par leur nom, ordre
  indifférent), traduction vide ignorée ; format carte à trois colonnes
  toujours lisible.
- CSV vide, CSV sans ligne `/SYSTEM`, en-tête, BOM, chemin Windows, `.WAV`
  majuscule, Latin-1 : rien de cassé.
- Noms refusés (trop long, accent, espace) et doublons : signalés, les noms
  valides continuent.
- **Vraie génération de deux sons** : 32 kHz, mono, PCM 16 bits.
- Arrêt en cours de route, panne de conversion : pas de fichier tronqué, pas
  de temporaire laissé derrière.
- Bilan quand un fichier échoue : les autres sont créés.
- Interface essayée en **français et en anglais** avec des dialogues simulés :
  l'entrée de menu est là, le bouton redevient « Let's Go », la liste affichée
  (45 lignes en français, 44 en anglais) ne bouge pas.

### Reste à faire

- **Essayer dans l'application** : les 186 fichiers doivent apparaître dans
  `SYSTEM/`, puis être copiés sur la carte (`SOUNDS/fr/SYSTEM/`).
- **La racine reste hors périmètre** (choix de Richard, 18 octobre au soir),
  même si ses 49 sons français sont officiels. À rouvrir si l'on veut vraiment
  « une seule voix partout ».
- Publier (numéro de version à décider).
