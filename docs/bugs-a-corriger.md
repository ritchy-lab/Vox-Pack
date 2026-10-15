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

### Mise en page (terminée le 15 octobre)

- [x] **Logo agrandi** : 400 px de large sur 194 de haut, réglable par la
  constante `LARGEUR_LOGO`.
- [x] **Espacements harmonisés** : six constantes nommées (`ESPACE_HAUT`,
  `ESPACE_LOGO_BOUTONS`, `ESPACE_BOUTONS_LISTE`, `ESPACE_LISTE_LEDS`,
  `ESPACE_LEDS_BOUTONS`, `ESPACE_BAS`).
- [x] **Cases de saisie affinées** (34 px) : **7 lignes visibles**.
- [x] **Barre de leds affinée** (16 px, segments de 6) et **sans texte** : elle
  s'allume jusqu'au bout. Durée d'affichage avant extinction réglable
  (`PAUSE_LEDS`).
- [x] **Les boutons du bas ne peuvent plus disparaître** quand la fenêtre
  rapetisse : le bloc du bas est posé en premier, c'est la liste qui se
  réduit.
- [x] **Fenêtre** : 820 × 795, ouverte **au centre** de l'écran, et réduite
  automatiquement si l'écran est plus petit.
- [x] **Ligne d'état** sous la barre de leds : étape en cours, puis compteur.
- [x] **Polices des textes d'information agrandies** : état et avertissements
  14, fenêtres d'alerte 16.

### Langues et voix (ajouté le 15 octobre)

- [x] **31 voix au lieu de 4** : 13 françaises (France, Suisse, Belgique,
  Québec) et 18 anglaises (États-Unis, Royaume-Uni). Les libellés indiquent
  **l'accent**, pas un adjectif marketing.
- [x] **Sélecteur de langue** : deux drapeaux posés dans le bandeau, au-dessus
  du menu des voix, sans décaler la mise en page. Le drapeau actif est net,
  l'autre est estompé et s'éclaire au survol.
- [x] **Mémoire** : la langue et la voix choisies sont retrouvées au
  démarrage, séparément pour chaque langue.
- [x] **Vérification des voix au démarrage** : une voix retirée par Microsoft
  disparaît du menu d'elle-même ; si la vérification échoue (pas de réseau),
  la liste de l'application est conservée.
- [x] **Messages d'erreur en français** (« pas de connexion Internet », « voix
  supprimée par le service : choisissez-en une autre »…) au lieu de codes
  techniques.

## Écarté (décisions de Richard)

- [x] ~~Prévenir avant d'écraser un fichier déjà présent~~ — non souhaité.
- [x] ~~Compteur de phrases cochées~~ — n'apporte que de l'information.
- [x] ~~Réglage 6 / 8 caractères~~ — limite fixe à 8, l'aide expliquera le cas
  des versions d'EdgeTX antérieures.

## Idées notées (pas décidées)

- **Version web du logiciel** *(idée de Richard, 15 octobre)* : une page dans le
  navigateur où l'on colle sa liste et où l'on récupère les fichiers WAV, sans
  rien installer. Le CSS des boutons néon mis de côté servirait alors
  directement. Rien n'est décidé : c'est noté pour ne pas l'oublier.

## À faire — reste du programme

- [ ] **Aide à compléter** : dire qu'une connexion Internet est nécessaire et
  que le texte des phrases est envoyé au service en ligne de Microsoft ;
  expliquer la limite de 6 caractères sur les EdgeTX antérieurs à la 2.11.
- [ ] **Exporter / Importer une liste** dans un menu (même code pour macOS et
  Windows : barre de menus du système sur Mac, menu de fenêtre sur PC).
  Format : `nom,phrase` par ligne — c'est aussi le format d'export.
- [ ] **Version Windows** (`.exe`) construite automatiquement par GitHub
  Actions ; conversion audio 100 % Python (`soundfile` + `soxr`, déjà
  testée) à la place de `afconvert` ; police système selon la plateforme
  (déjà en place avec `POLICES_PREFEREES`).
- [ ] **Interface en anglais** : les textes de la fenêtre à sortir du code, et
  une liste de phrases anglaise adaptée (pas une traduction mot à mot). Les
  voix anglaises, elles, sont déjà là.
- [ ] **Déclinaison simplifiée de l'icône** pour les petites tailles
  (16 et 32 px) : le dessin et le mot y deviennent illisibles.

