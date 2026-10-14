# Points à corriger

Liste de travail — établie à partir des remarques de Richard, complétée par
l'audit du code du 14 octobre 2026.

Légende : `[ ]` à faire · `[x]` fait

## Déjà réglé

- [x] **edge-tts renvoie une erreur 403 : plus aucune voix générée.**
  Microsoft a durci son contrôle d'accès (le jeton `Sec-MS-GEC-Version`
  est passé de `1-` à `2-`). Correctif : `edge-tts` 7.3.1 (sorti le
  13 octobre 2026). Vérifié : la génération refonctionne.
  ⚠️ Le `.app` déjà construit dans `dist/` embarque encore la version 7.2.8,
  il doit être reconstruit.

## Remarques de Richard (fichier « Bugs ou risques »)

- [ ] **1. Noms de fichiers non validés.** L'aide impose 8 caractères max, sans
  accents ni espaces, mais rien ne le vérifie. Un nom trop long, accentué ou
  contenant « / » produit un WAV inutilisable ou une erreur.
- [ ] **2. Noms en double.** Deux lignes avec le même nom : la seconde écrase la
  première, sans avertissement. Les WAV déjà présents dans le dossier de
  destination sont aussi écrasés sans prévenir.
- [ ] **3. Arrêt à la première erreur.** Une coupure Internet interrompt toute la
  génération. edge-tts passe par un service en ligne de Microsoft : la connexion
  est obligatoire. L'application ne le dit pas, le message d'erreur est brut.
- [ ] **4. Aperçu.** Le fichier temporaire `preview_temp.mp3` a un nom fixe : deux
  clics rapides créent une collision (l'un supprime le fichier de l'autre).
  Aucun moyen d'arrêter la lecture en cours.
- [ ] **5. CSV réécrit à chaque frappe**, avec un `except: pass` qui masque toute
  erreur d'écriture. Un nom contenant une virgule casserait le relais CSV
  (`split(",", 1)`).
- [ ] **6. Aide incohérente.** Elle annonce 45 lignes par défaut, alors que
  `LISTE_PAR_DEFAUT` en contient 44.
- [ ] **7.** *(voir l'audit ci-dessous)*
- [ ] **8.** *(voir l'audit ci-dessous)*

## Constats de l'audit (14 octobre 2026)

- [ ] **Limite de longueur des noms : 6 caractères, pas 8.** La longueur
  autorisée dépend de la radio : 8 caractères seulement sur les FrSky série X9,
  **6 caractères sur toutes les autres** (RadioMaster TX16S, BetaFPV, Jumper…).
  Plus de la moitié de la liste par défaut fait 7 ou 8 caractères
  (`mot-arme`, `train-so`, `chrono-d`, `croact`…) et risque donc d'être refusée
  dans l'éditeur de la radio. Voir la discussion EdgeTX :
  <https://github.com/EdgeTX/edgetx/issues/3912>
- [ ] **Dépendance macOS exclusive : `afconvert`.** La conversion MP3 → WAV passe
  par un outil présent uniquement sur macOS (`/usr/bin/afconvert`), et l'aperçu
  par `/usr/bin/afplay`. C'est le principal obstacle à une version Windows.
  Solution testée et validée : conversion 100 % Python avec `soundfile` + `soxr`
  (résultat identique : même durée, même niveau sonore).
- [ ] **Police codée en dur : « SF Pro Display ».** Absente sous Windows, Tk
  bascule alors sur une police de remplacement au rendu inégal.
- [ ] **Interface uniquement en français**, textes écrits en dur dans le code.
- [ ] **Aucune version ni identifiant de bundle** dans le `.app`
  (`CFBundleShortVersionString = 0.0.0`, `CFBundleIdentifier = RadioVox`).
- [ ] **L'application n'annonce pas qu'une connexion Internet est nécessaire.**

## À faire (nouveaux chantiers)

- [ ] Version Windows (`.exe`) construite automatiquement par GitHub Actions.
- [ ] Interface bilingue français / anglais, avec choix automatique selon la
  langue du système et sélecteur manuel dans l'application.
- [ ] Liste de phrases par défaut en anglais (adaptée aux pilotes anglophones,
  pas une traduction mot à mot).
- [ ] Voix anglaises en plus des voix françaises.
- [ ] Nouveau nom (**VoxPack**) et nouveau logo.
