# Points à corriger

Liste de travail — établie à partir des remarques de Richard, complétée par
l'audit du code du 14 octobre 2026.

Légende : `[ ]` à faire · `[x]` fait

## Fait

- [x] **edge-tts renvoyait une erreur 403 : plus aucune voix générée.**
  Microsoft a durci son contrôle d'accès (le jeton `Sec-MS-GEC-Version`
  est passé de `1-` à `2-`). Correctif : `edge-tts` 7.3.1, désormais exigé
  dans `requirements.txt` et embarqué dans l'application.
- [x] **Nom** : « RadioVox » était déjà pris. L'application s'appelle
  **Vox-Pack**, avec son logo et son icône.
- [x] **Version et identifiant du paquet** : `com.ritchy-lab.vox-pack`, 1.0.
- [x] **Fenêtres de message** aux couleurs de l'application, à la place des
  boîtes grises de macOS.
- [x] **Apparence** : boutons en cyan, survol qui n'éclaire que le texte et le
  cadre, menu des voix au filet complet, liste ouverte sur fond noir,
  défilement à la molette fiabilisé, typographie sans gras.
- [x] **Signature cliquable** ouvrant la fenêtre de soutien (Ko-fi), lien de
  soutien dans l'aide et dans les README.
- [x] **Noms de fichiers vérifiés** : au-delà de 8 caractères, ou avec un
  accent, un espace ou un caractère interdit, la case passe en rouge et la
  raison s'affiche à côté de la ligne.
- [x] **Doublons signalés** : deux lignes au même nom, la seconde est marquée
  « déjà utilisé (ligne n) ».
- [x] **Enregistrement sûr de la liste** : écriture dans un fichier voisin puis
  remplacement (une interruption ne peut plus vider la liste), copie `.bak`
  conservée, et lecture par le module `csv` (une virgule dans une phrase ne
  casse plus rien).
- [x] **La génération ne s'arrête plus à la première erreur** : elle continue et
  affiche un bilan (réussis / problèmes). Les lignes au nom invalide sont
  refusées d'emblée, avec la raison.
- [x] **Compteur pendant la génération** — retiré : le texte (« 3 fichiers sur
  12 — mot-arme ») rognait la barre de leds, qui ne s'allumait donc pas
  jusqu'au bout. La barre occupe maintenant toute la largeur.
- [x] **Confort** : touche Entrée = nouvelle ligne, curseur placé sur la ligne
  créée, dernier dossier de destination mémorisé.
- [x] **Aperçu** : nom de fichier temporaire unique (deux clics rapides ne se
  gênent plus) et bouton qui devient « ■ Arrêter » pendant la lecture.

## Écarté (décisions de Richard)

- [x] ~~Prévenir avant d'écraser un fichier déjà présent~~ — non souhaité.
- [x] ~~Compteur de phrases cochées~~ — n'apporte que de l'information.
- [x] ~~Réglage 6 / 8 caractères~~ — limite fixe à 8, l'aide expliquera le cas
  des versions d'EdgeTX antérieures.

## À faire — mise en page (décidé le 15 octobre au soir)

Objectif : retrouver l'allure de la maquette (en-tête large et généreux,
liste plus courte, espacements réguliers).

- [ ] **Logo nettement plus grand**, comme sur la maquette : il y occupe
  environ les deux tiers de la largeur de la fenêtre (aujourd'hui 340 px
  sur 900, soit 38 %). Réglage unique : `LARGEUR_LOGO`.
- [ ] **Plus d'espace entre la ligne des boutons et la liste.**
- [ ] **« Baisser la fenêtre des listes »** — formulation exacte de Richard, à
  préciser : la liste commence plus bas (plus d'espace entre la rangée de
  boutons et le haut de la liste), ou bien la zone de liste est moins haute ?
- [ ] **Remonter la barre de progression** (la rapprocher du bas de la
  liste) : elle est aujourd'hui collée au bloc des boutons.
- [ ] **Harmoniser les espacements** : un même écart partout (en haut, en
  bas, entre les blocs), pour que l'ensemble soit régulier.

## Idées notées (pas décidées)

- **Version web du logiciel** *(idée de Richard, 15 octobre)* : une page dans le
  navigateur où l'on colle sa liste et où l'on récupère les fichiers WAV, sans
  rien installer. Le CSS des boutons néon mis de côté servirait alors
  directement. Rien n'est décidé : c'est noté pour ne pas l'oublier.

## À faire — reste du programme

- [ ] **Exporter / Importer une liste** dans un menu (même code pour macOS et
  Windows : barre de menus du système sur Mac, menu de fenêtre sur PC).
  Format : `nom,phrase` par ligne — c'est aussi le format d'export.
- [ ] **Version Windows** (`.exe`) construite automatiquement par GitHub
  Actions ; conversion audio 100 % Python (`soundfile` + `soxr`, déjà
  testée) à la place de `afconvert` ; police système selon la plateforme
  (déjà en place avec `POLICES_PREFEREES`).
- [ ] **Interface bilingue** français / anglais : textes à sortir du code,
  liste de phrases anglaise adaptée (pas une traduction mot à mot), voix
  anglaises.
- [ ] **Déclinaison simplifiée de l'icône** pour les petites tailles
  (16 et 32 px) : le dessin et le mot y deviennent illisibles.

