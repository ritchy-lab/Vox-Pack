# Points à corriger

Liste de travail — établie à partir des remarques de Richard, complétée par
l'audit du code du 14 octobre 2026.

Légende : `[ ]` à faire · `[x]` fait

## Fait

- [x] **edge-tts renvoyait une erreur 403 : plus aucune voix générée.**
  Microsoft a durci son contrôle d'accès (le jeton `Sec-MS-GEC-Version`
  est passé de `1-` à `2-`). Correctif : `edge-tts` 7.3.1 (sorti le
  13 octobre 2026), désormais exigé dans `requirements.txt` et embarqué
  dans l'application.
- [x] **Nom** : « RadioVox » était déjà pris (application App Store, Google
  Play, société française). L'application s'appelle **Vox-Pack**.
- [x] **Nouveau logo et nouvelle icône**, avec les dessins d'origine rangés
  dans `assets/sources/` et un script pour tout refabriquer.
- [x] **Version et identifiant du paquet** : `com.ritchy-lab.vox-pack`, 1.0
  (c'était `0.0.0` / `RadioVox`).
- [x] **Aide incohérente** : elle annonçait 45 lignes par défaut, alors que la
  liste en contient 44.
- [x] **Fenêtres de message** : les boîtes grises de macOS (avec l'icône de
  Python) sont remplacées par des fenêtres aux couleurs de l'application,
  avec une pastille dessinée (information, succès, avertissement, erreur).
- [x] **Erreur de génération** : le message explique maintenant la cause
  probable (connexion Internet) au lieu de l'erreur technique brute, et un
  bouton « Ouvrir le dossier » apparaît sur le message de succès.
- [x] **Apparence** : texte des boutons en cyan ; au survol, seuls le texte et
  le cadre s'éclairent (le fond ne bouge pas) ; filet du menu des voix
  complet ; menu recadré sur le nom le plus long ; liste ouverte sur fond
  noir ; défilement à la molette fiabilisé.
- [x] **Signature cliquable** ouvrant une fenêtre de soutien (Ko-fi), et lien
  de soutien dans l'aide et dans les README.

## Remarques de Richard (fichier « Bugs ou risques »)

- [ ] **1. Noms de fichiers non validés.** L'aide impose une longueur maximale,
  sans accents ni espaces, mais rien ne le vérifie. Un nom trop long, accentué
  ou contenant « / » produit un WAV inutilisable ou une erreur.
- [ ] **2. Noms en double.** Deux lignes avec le même nom : la seconde écrase la
  première, sans avertissement. Les WAV déjà présents dans le dossier de
  destination sont aussi écrasés sans prévenir.
- [ ] **3. Arrêt à la première erreur.** Une coupure Internet interrompt toute la
  génération au lieu de continuer avec les lignes suivantes.
- [ ] **4. Aperçu.** Le fichier temporaire `preview_temp.mp3` a un nom fixe : deux
  clics rapides créent une collision. Aucun moyen d'arrêter la lecture.
- [ ] **5. CSV réécrit à chaque frappe**, avec un `except: pass` qui masque toute
  erreur d'écriture. Un nom contenant une virgule casse le relais CSV
  (`split(",", 1)`).
- [ ] **6. Durée de génération inconnue** : la barre avance, mais rien n'indique
  combien de fichiers restent.

## Constats de l'audit (14 octobre 2026)

- [ ] **Longueur des noms : le chiffre dépend de la version d'EdgeTX**, pas du
  modèle de radio. D'après le code du firmware
  ([`dataconstants.h`](https://github.com/EdgeTX/edgetx/blob/main/radio/src/dataconstants.h)) :
  - EdgeTX **2.9 et 2.10** : 6 caractères sur les écrans couleur et les petits
    écrans noir et blanc, 8 sur les grands écrans noir et blanc (X9D, X9E) ;
  - EdgeTX **2.11 et 2.12** : **8 caractères partout**.
  L'aide annonce aujourd'hui une limite fixe. À remplacer par un réglage
  « ma radio : EdgeTX 2.11+ (8) / 2.10 ou avant (6) ».
- [ ] **Dépendance macOS exclusive : `afconvert`.** La conversion MP3 → WAV passe
  par un outil présent uniquement sur macOS (`/usr/bin/afconvert`), et l'aperçu
  par `/usr/bin/afplay`. C'est le principal obstacle à une version Windows.
  Solution testée et validée : conversion 100 % Python avec `soundfile` + `soxr`
  (résultat identique : même durée, même niveau sonore).
- [ ] **Police codée en dur : « SF Pro Display ».** Absente sous Windows, Tk
  bascule alors sur une police de remplacement au rendu inégal.
- [ ] **Interface uniquement en français**, textes écrits en dur dans le code.
- [ ] **L'aide ne dit pas qu'une connexion Internet est nécessaire**, ni que le
  texte des phrases est envoyé au service en ligne de Microsoft.

## À faire (nouveaux chantiers)

- [ ] Version Windows (`.exe`) construite automatiquement par GitHub Actions.
- [ ] Interface bilingue français / anglais, avec choix automatique selon la
  langue du système et sélecteur manuel dans l'application.
- [ ] Liste de phrases par défaut en anglais (adaptée aux pilotes anglophones,
  pas une traduction mot à mot).
- [ ] Voix anglaises en plus des voix françaises.
- [ ] Déclinaison simplifiée de l'icône pour les petites tailles (16 et 32 px) :
  le mot « VOX-PACK » y devient illisible.
