<!--
Ce fichier EST le texte de la page « Releases » : il est repris tel quel par le
robot de publication, et il est bilingue parce que la page n'a qu'une zone de
texte. Tout ce qui s'écrit ici est donc visible du public — d'où ce commentaire
HTML, invisible pour les visiteurs, pour laisser les consignes aux auteurs.
Ne pas remettre de titre « page de version » : la page en a déjà un.
-->

Fait parler ta radiocommande.

Vox-Pack fabrique les fichiers de voix que ta radio EdgeTX prononce pendant le
vol : « Moteur armé », « Train sorti », « Chrono démarré »…

## Nouveautés de la 1.5.1

- **La fin des phrases n'est plus coupée, pour de bon.** Chaque son garde
  maintenant **un quart de seconde de silence** après le dernier mot. La 1.5
  n'en laissait que 50 ms : la dernière consonne — le « d » de « motor armed »,
  le « s » de « takeoff flaps » — s'entendait s'arrêter net, et deux annonces
  jouées à la suite se collaient l'une à l'autre.
- **Rien d'autre ne change** : même voix, même format, même niveau. Les
  fichiers s'allongent d'environ 0,2 s (≈ 1 s de moyenne au lieu de 0,8 s).
  Les fichiers déjà fabriqués ne changent pas : il faut les régénérer.

## Nouveautés de la 1.5.0

- **L'allemand arrive.** L'application parle désormais trois langues : français,
  anglais et allemand. L'interface, l'aide, les messages et la liste changent
  ensemble, et chaque langue garde sa propre liste. Quatre voix allemandes :
  **Katja** (★, la voix officielle d'EdgeTX), Conrad, Amala et Killian — soit
  **34 voix** au total — et **211 sons système** officiels en allemand. Merci à
  **Ralf** pour la traduction et la relecture.
- **Des silences dans vos phrases.** Un « > » vaut une demi-seconde :
  « Motor an >> Motor aus » laisse une seconde entre les deux, et
  « >>> Motor an » retarde l'annonce d'une seconde et demie. Dix secondes au
  maximum. Utile pour retarder une annonce, ou pour détacher deux informations.
- **Une petite fenêtre à la fermeture.** En quittant l'application, une fenêtre
  discrète vous invitera à soutenir le projet — uniquement si vous en avez
  envie. Cochez **« Ne plus demander »** et elle disparaît définitivement.
  Envie d'y revenir un jour ? Le lien Ko-fi reste sous la signature.

## Nouveautés de la 1.4.4

- **La fin des phrases n'est plus coupée.** L'application arrêtait chaque son
  une fraction de seconde avant la fin. Sur les versions précédentes, un peu de
  silence en fin de fichier le cachait ; les fichiers récents sont plus serrés,
  alors ça s'entendait. Le son va maintenant jusqu'au bout, et les fichiers se
  terminent plus doucement.
- Rien d'autre ne change : même voix, même format, mêmes réglages.

## Nouveautés de la 1.4.3

- **Enregistrer la liste, même quand Windows s'y oppose** : un antivirus, OneDrive
  ou la protection « Contrôle des dossiers » de Windows peut refuser la
  réécriture du fichier de liste. L'application réessaie maintenant trois fois,
  et le message dit la vraie cause — avant, il parlait d'espace disque, ce qui
  envoyait sur une fausse piste.
- **Fenêtre « Mise à jour disponible »** : le texte et les boutons ne sortent
  plus de la fenêtre. Elle se redimensionne sur son contenu.

## Nouveautés de la 1.4.2

- **Correction Windows, la vraie** : depuis la 1.4.1, la génération des **sons
  système** échouait **en entier** sur PC (« 0 fichier créé sur 212 »). Le
  fichier temporaire porte un nom en `.tmp`, et la bibliothèque d'écriture
  devinait le format d'après ce nom : elle refusait. Le format est maintenant
  annoncé explicitement. La correction de la 1.4.1 (dossier de sortie sur un
  autre disque) reste en place.
- **Bouton « Écouter »** : après un changement de langue, il redevient
  « Écouter » au lieu de rester sur « Arrêter ».
- **Connexion Internet** : un message clair quand le service de voix est
  injoignable, au lieu d'une erreur technique. Et si le réseau tombe vraiment,
  la génération s'arrête après **trois échecs d'affilée** au lieu d'empiler
  des centaines d'erreurs.
- **Lien ☕ Ko-fi** sous la signature, en bas à droite de la fenêtre.

## Nouveautés de la 1.4.1

- **Correction Windows** : la génération des **sons système** fonctionne
  maintenant quand le dossier de sortie est sur un autre disque que le dossier
  temporaire (par exemple `D:`). Le WAV est construit dans le dossier de
  destination, puis renommé sur place.
- **HAL 9000** : à la demande générale, une voix **librement inspirée de HAL
  9000** a été ajoutée. Elle est construite avec les voix disponibles dans
  l'application (service Microsoft Edge), qui ne permettent pas de reproduire
  la voix du film : ce n'est pas la voix officielle, mais une inspiration.
  En anglais, Christopher (débit +6 %, pitch −4 Hz) ; en français, Henri
  (débit −25 %, pitch −10 Hz). Les deux passent par l'effet **carton + léger
  écho**. **HAL impose sa propre voix**, indépendamment du menu.

## Nouveautés de la 1.4

- **Des fichiers plus forts et plus courts** : les silences sont coupés et le
  niveau est monté au maximum propre, avec un limiteur — comme les sons
  officiels de la radio, sans le clic de l'ancien compresseur.
- **L'aperçu** applique le même traitement : ce que tu entends est ce qui sera
  écrit sur la carte.
- La coupe et le niveau s'appliquent à la **liste**, aux **sons système** et à
  l'**aperçu**.

## Nouveautés de la 1.3

- **Les fichiers son système d'EdgeTX** — la grande nouveauté : les **186
  annonces SYSTEM** françaises (**212** en anglais) en un clic, avec la voix
  choisie, dans un dossier `SYSTEM/` prêt pour la carte SD.
- **Pour le fun** : la possibilité de créer des **voix de robot**, avec
  quatre pastilles Robot 1 à 4 (aucune allumée = voix normale).
- **Mises à jour** : vérification automatique au démarrage, avec une petite
  fenêtre pour télécharger la nouvelle version.
- Aide remaniée, voix officielles Denise et Emily (★), choix du dossier
  macOS natif.

## À télécharger

- **macOS** : `Vox-Pack.zip` — à décompresser, puis glisser l'application dans
  ton dossier Applications.
- **Windows** : `Vox-Pack.exe` — à lancer directement, rien à installer.

**Au tout premier lancement**, ton système affichera un avertissement
(l'application n'a pas de certificat payant) : les deux clics à faire sont
expliqués dans le [README](https://github.com/ritchy-lab/Vox-Pack#installation).

## Ce qu'il faut savoir

- **Une connexion Internet est nécessaire** : les voix sont synthétisées par le
  service de Microsoft Edge. Le texte de tes phrases lui est envoyé au moment
  de la génération.
- **Les voix** viennent du **service Microsoft Edge** via `edge-tts` (non
  officiel). Vox-Pack ne distribue pas les voix ; le texte est envoyé à
  Microsoft au moment de la génération.
- L'application existe **en français, en anglais et en allemand** (menu
  Fichier → Langue).
- Les fichiers produits sont au format exact attendu par EdgeTX :
  **WAV, 16 bits, 32 kHz, mono**.

---

**Tout est expliqué dans le
[README](https://github.com/ritchy-lab/Vox-Pack)** : comment ça marche, où sont
rangés tes fichiers, et comment les copier sur la carte SD de ta radio.

## English

Speak up your radio.

Vox-Pack builds the voice files your EdgeTX radio speaks during flight:
"Motor armed", "Gear down", "Timer started"…

## What's new in 1.5.1

- **The end of a phrase is no longer cut off — for good.** Every sound now
  keeps **a quarter of a second of silence** after the last word. 1.5 left only
  50 ms: the final consonant — the "d" of "motor armed", the "s" of "takeoff
  flaps" — stopped short, and two announcements played back to back ran into
  each other.
- **Nothing else changes**: same voices, same format, same level. Files are
  about 0.2 s longer (≈ 1 s on average instead of 0.8 s). Files already made
  are unchanged: generate them again to benefit.

## What's new in 1.5.0

- **German is here.** The application now speaks three languages: French,
  English and German. The interface, help, messages and list all change
  together, and each language keeps its own list. Four German voices: **Katja**
  (★, EdgeTX's official voice), Conrad, Amala and Killian — **34 voices** in
  total — plus **211 official German system sounds**. Thanks to **Ralf** for the
  translation and the proofreading.
- **Silences in your phrases.** A ">" is half a second: "Motor an >> Motor aus"
  leaves one second between the two, and ">>> Motor an" delays the announcement
  by a second and a half. Ten seconds at most. Handy to delay an announcement,
  or to separate two pieces of information.
- **A small window on exit.** When you quit the application, a discreet window
  invites you to support the project — only if you feel like it. Tick
  **"Don't ask again"** and it disappears for good. Changed your mind? The Ko-fi
  link stays under the signature.

## What's new in 1.4.4

- **The end of a phrase is no longer cut off.** The app stopped each sound a
  fraction of a second before the end. In earlier versions a little silence at
  the end of the file hid it; recent files are tighter, so you could hear it.
  The sound now plays to the very end, and files finish more gently.
- Nothing else changes: same voices, same format, same settings.

## What's new in 1.4.3

- **Saving the list, even when Windows says no**: an antivirus, OneDrive or
  Windows' "Controlled folder access" can refuse to let the list file be
  rewritten. The app now retries three times, and the message gives the real
  cause — before, it mentioned disk space, which sent people down the wrong
  path.
- **"Update available" window**: the text and the buttons no longer spill out
  of the window. It resizes to fit its content.

## What's new in 1.4.2

- **Windows fix, the real one**: since 1.4.1, **system sound** generation failed
  **completely** on Windows ("0 file created out of 212"). The temporary file
  has a `.tmp` name, and the writing library guessed the format from that name:
  it refused. The format is now stated explicitly. The 1.4.1 fix (output folder
  on another drive) stays in place.
- **"Listen" button**: after a language change, it goes back to "Listen"
  instead of staying on "Stop".
- **Internet connection**: a clear message when the voice service cannot be
  reached, instead of a technical error. And if the network really drops,
  generation stops after **three failures in a row** instead of piling up
  hundreds of errors.
- **☕ Ko-fi link** under the signature, bottom right of the window.

## What's new in 1.4.1

- **Windows fix**: **system sound** generation now works when the output
  folder is on a different drive from the temporary folder (e.g., `D:`). The
  WAV is built in the destination folder, then renamed in place.
- **HAL 9000**: by popular request, a voice **freely inspired by HAL 9000**
  has been added. It is built from the voices available in the app (Microsoft
  Edge service), which cannot reproduce the film voice: it is not the official
  voice, but an inspiration. In English, Christopher (+6% rate, −4 Hz pitch,
  gentle EQ); in French, Henri (−25% rate, +30 Hz pitch, clear EQ).
  **HAL forces its own voice**, regardless of the menu.

## What's new in 1.4

- **Louder, shorter files**: silences are trimmed and the level is pushed to
  its clean maximum with a limiter — like the radio's official sounds, without
  the click of the old compressor.
- **The preview** applies the same processing: what you hear is what gets
  written to the card.
- Trimming and levelling apply to the **list**, the **system sounds** and the
  **preview**.

## What's new in 1.3

- **EdgeTX system sound files** — the big one: all **186 French SYSTEM
  files** (**212** in English) in one click, with the chosen voice, in a
  `SYSTEM/` folder ready for the SD card.
- **Just for fun**: the ability to create **robot voices**, with four dots
  Robot 1 to 4 (none lit = normal voice).
- **Updates**: automatic check at startup, with a small window to download
  the new version.
- Reworked help, official Denise and Emily voices (★), native macOS folder
  picker.


### What to download

- **macOS**: `Vox-Pack.zip` — unzip it, then drag the app into your Applications
  folder.
- **Windows**: `Vox-Pack.exe` — just run it, nothing to install.

**The very first time**, your system will show a warning (the app has no paid
certificate): the two clicks to make are explained in the
[README](https://github.com/ritchy-lab/Vox-Pack#installation).

### Good to know

- **An Internet connection is required**: the voices are synthesised by
  Microsoft Edge's service. The text of your phrases is sent to it when you
  generate.
- **The voices** come from the **Microsoft Edge service** via `edge-tts`
  (unofficial). Vox-Pack does not distribute the voices; the text is sent to
  Microsoft when you generate.
- The app comes **in French, English and German** (File → Language menu).
- The files it produces are exactly what EdgeTX expects:
  **WAV, 16-bit, 32 kHz, mono**.

---

**Everything is explained in the
[README](https://github.com/ritchy-lab/Vox-Pack)** (English version:
[README.en.md](https://github.com/ritchy-lab/Vox-Pack/blob/main/README.en.md),
German: [README.de.md](https://github.com/ritchy-lab/Vox-Pack/blob/main/README.de.md)).
