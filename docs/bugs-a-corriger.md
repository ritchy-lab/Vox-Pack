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

### Aide et gestion des listes (ajouté le 15 octobre)

- [x] **Aide complétée** : bloc « Connexion Internet nécessaire » (les voix
  viennent de Microsoft, le texte des phrases lui est envoyé, une voix retirée
  disparaît du menu) et bloc « Longueur des noms selon votre EdgeTX »
  (8 caractères à partir de la 2.11, 6 avant — 8 sur X9D et X9E).
- [x] **Menu « Fichier »** : *Exporter la liste…* (fichier `nom,phrase` avec
  en-tête) et *Importer une liste…* (confirmation avant remplacement,
  en-tête ignoré, ligne à une seule colonne acceptée).

### Anglais, et une liste par langue (16 octobre)

- [x] **Interface bilingue** : 145 textes dans chaque langue (`TEXTES`, `t()`),
  aucune clé manquante. La langue suit celle du système au premier lancement
  (les préférences de macOS, pas `LANG` : lancée depuis VS Code, elle aurait
  sinon basculé en anglais), puis se change dans le menu *Fichier → Langue*.
- [x] **Deux listes indépendantes**, une par langue, échangées par les
  drapeaux : travailler en anglais ne peut plus effacer la liste française.
- [x] **Liste de phrases anglaise** (44 lignes, noms ≤ 8 caractères).
- [x] **Menu *Fichier → Charger la liste par défaut*** : remet les phrases
  livrées avec l'application, dans la langue des voix, après confirmation.
- [x] **Voix mémorisée par identifiant technique**, et non par son libellé
  (qui contient « Femme » / « Female »). Les anciens réglages sont convertis
  tout seuls.
- [x] **Emma réparée** : `en-US-EmmaNeural` est listée par Microsoft mais ne
  renvoie plus aucun son. Remplacée par `en-US-EmmaMultilingualNeural`. Les
  31 voix ont été essayées une par une : les 30 autres fonctionnent.
- [x] **La voix choisie est cochée dans la liste déroulante** : on voit d'où
  l'on part quand on veut en changer.
- [x] **L'aperçu lit toutes les lignes cochées**, l'une après l'autre, et la
  voix suivante se télécharge pendant la lecture (plus de temps mort).
- [x] **« Arrêter » arrête vraiment** : avant, il coupait la phrase en cours
  mais enchaînait la suivante.
- [x] **La copie de secours ne peut plus être vidée** : elle n'est remplacée
  que si la liste actuelle contient quelque chose. C'est ce défaut qui a fait
  perdre une liste à Richard (récupérée depuis son export du Bureau).

### Version Windows (16 octobre)

- [x] **Conversion audio sans `afconvert`** : `soundfile` + `soxr` ailleurs que
  sur macOS. Résultat identique (32 kHz, mono, 16 bits, même nombre
  d'échantillons), vérifié sur une vraie phrase.
- [x] **Lecture du son sans `afplay`** : `soundfile` + `sounddevice` sur
  Windows, avec interruption immédiate. Sur macOS, `afplay` reste utilisé :
  l'application n'embarque donc pas ces bibliothèques.
- [x] **Recette de compilation multi-plateforme** : `.app` sur macOS, `.exe`
  en un seul fichier sur Windows, avec les bibliothèques natives
  (`libsndfile`, `PortAudio`).
- [x] **Icône de la fenêtre** posée au démarrage (sinon Windows affiche
  l'icône de Tk dans la barre des tâches) et **menu aux couleurs de
  l'application** là où le système l'honore.
- [x] **Fabrication automatique** : `.github/workflows/windows.yml` compile le
  `.exe` à chaque envoi et le dépose dans les artefacts de la page Actions.
- [x] **Famille d'icônes** : `icon.icns` et `icon.ico` contiennent le
  monogramme VP (16 à 64 px) **et** le dessin détaillé au-delà.

### Icônes et dossier de sortie (16 octobre, après-midi)

- **Le monogramme VP ne servait plus à rien de visible.** Le seuil était à
  64 px — exactement la taille de la vue par icônes du Finder : Richard voyait
  donc le monogramme là où il attendait son dessin, alors que le Dock (128 px)
  affichait le bon. Le monogramme ne sert plus que pour **16 et 32 px** ;
  partout ailleurs, c'est le dessin de Richard.
- **L'icône était trop petite sur PC** : le monogramme n'occupait que 69 % de
  son image, et Windows ne prévoit aucune grille (contrairement à Apple, qui
  impose 88 %). Le `.ico` est désormais **recadré au plus juste** ; le `.icns`
  garde la proportion d'Apple, monogramme compris.
- **Le dossier de sortie s'appelait « Voix radio », écrit en dur en français** :
  un utilisateur anglophone recevait un dossier au nom français. Il s'appelle
  maintenant **`Vox-Pack`** — un nom neutre, le même dans toutes les langues
  (le traduire l'aurait fait changer de nom en changeant de langue).

## Écarté (décisions de Richard)

- [x] ~~Prévenir avant d'écraser un fichier déjà présent~~ — non souhaité.
- [x] ~~Compteur de phrases cochées~~ — n'apporte que de l'information.
- [x] ~~Réglage 6 / 8 caractères~~ — limite fixe à 8, l'aide expliquera le cas
  des versions d'EdgeTX antérieures.
- [x] ~~Les deux drapeaux (langue des voix séparée de celle des textes)~~ —
  **supprimés le 16 octobre** : deux réglages là où un seul suffit. Il n'y a
  plus qu'une langue, celle de l'utilisateur, choisie dans le menu. Elle
  commande les textes, les voix **et** la liste de phrases. Cela supprime au
  passage un défaut : un utilisateur anglophone se retrouvait avec une
  interface anglaise et des voix françaises.
  **On garde en revanche les deux listes de phrases** (une par langue) : c'est
  la logique depuis le début, et passer d'une langue à l'autre ne fait rien
  perdre.

## Idées notées (pas décidées)

- **Version web du logiciel** *(idée de Richard, 15 octobre)* : une page dans le
  navigateur où l'on colle sa liste et où l'on récupère les fichiers WAV, sans
  rien installer. Le CSS des boutons néon mis de côté servirait alors
  directement. Rien n'est décidé : c'est noté pour ne pas l'oublier.

## Publier une version (fait le 16 octobre)

La fabrication est automatique : `.github/workflows/publier.yml` construit le
`.app` du Mac sur une machine macOS, le `.exe` du PC sur une machine Windows,
et les dépose tous les deux.

**Pour fabriquer sans rien publier** (pour vérifier) :

    onglet Actions -> « Publier une version » -> Run workflow
    les deux fichiers arrivent dans les artefacts de l'exécution

**Pour publier pour de bon** : créer une **étiquette de version** sur GitHub.

    GitHub -> Releases -> Draft a new release -> Choose a tag -> v1.0
    -> Publish release

La page « Releases » est alors créée avec les deux fichiers à télécharger, et
le texte de `docs/notes-de-version.md`. Le lien de téléchargement du README
pointe déjà dessus : il fonctionnera tout seul.

## Publié (16 octobre 2026)

**Vox-Pack 1.0 est en ligne** : https://github.com/ritchy-lab/Vox-Pack/releases

- `.zip` de 26,4 Mo pour macOS, `.exe` de 42 Mo pour Windows, tous les deux
  fabriqués par GitHub Actions à partir de l'étiquette
- le lien de téléchargement du README pointe dessus et fonctionne

**Ce qu'il a fallu apprendre** : GitHub met une majuscule toute seule dans son
champ d'étiquette (Richard a obtenu « V1.0 »), et un workflow qui n'écoute que
« v* » ne se déclenche pas — la page est alors publiée **sans aucun fichier**.
Le déclencheur accepte maintenant les deux, et un lancement à la main peut
viser une étiquette précise pour compléter une version déjà publiée.

## À faire — reste du programme

- [ ] *Optionnel* : **2 ou 3 captures d'écran** dans le README (Richard veut
  les faire lui-même).
- [ ] *Optionnel* : **l'annonce** (forum EdgeTX, RC Groups…). Richard préfère
  attendre de voir s'il y a des retours.
- [ ] *Optionnel* : la fenêtre de soutien a une largeur fixe (380 px), non
  adaptée aux écrans courts. Richard a dit de laisser tel quel.
- [ ] *Optionnel* : un certificat Apple (99 €/an) supprimerait l'avertissement
  au premier lancement sur Mac.

### Essayé et validé sur PC (16 octobre, soir)

Richard a installé le `.exe` sur un PC prêté (Windows, écran 1920 × 1080 réglé
à 150 %) et **n'a trouvé aucun problème** : taille de la fenêtre, alertes,
aide, menu Fichier, génération des fichiers `.wav` — tout fonctionne.

Seule remarque, **assumée par Richard** : la fenêtre de soutien (Ko-fi) n'a pas
été réduite sur écran court (largeur fixe de 380 px). À reprendre seulement si
elle le gêne un jour.

