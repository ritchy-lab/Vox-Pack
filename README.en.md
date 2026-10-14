<img src="logo.png" alt="Vox-Pack" width="800">

🇫🇷 **[Version française](README.md)**

# Vox-Pack

**Make your radio talk.**

Vox-Pack builds the voice files your EdgeTX radio speaks during a flight:
"Engine armed", "Gear down", "Timer started"…

You type your phrases, pick a voice, and press **Let's Go**. The application
creates the files in the exact format EdgeTX expects (16-bit, 32 kHz, mono),
ready to copy onto the radio's SD card.

## How it works

1. **Pick a voice** from the drop-down menu (Denise, Ariane, Henri, Fabrice).
2. **Type your phrases.** The list comes pre-filled with 44 common
   announcements (engine, flaps, gear, timer, flight modes…). You can edit,
   add or remove any line.
3. **Tick** the lines you want, or click **Tout** (all).
4. **Press Let's Go** and choose a folder: the `.wav` files are created.

The **Écouter l'aperçu** button (preview) lets you hear a phrase before
generating anything.

Your list is saved automatically, so you find it again next time.

## What it produces

- **WAV PCM 16-bit, 32 kHz, mono** — the format EdgeTX reads.
- One file per phrase, named after the left-hand column
  (`mot-arme.wav`, `train-so.wav`…), inside a **Voix radio** sub-folder.
- ⚠️ File names must stay **short**: the allowed length depends on the radio
  (6 characters on most models, 8 on FrSky X9 series). Copy the folder onto the
  SD card, inside `SOUNDS/<language>/`.

## Requirements

- **macOS 11 or newer** (Apple Silicon). A Windows version is in preparation.
- **An Internet connection**: the voices are synthesised by Microsoft Edge's
  online service. The text of your phrases is therefore sent to Microsoft when
  you generate. Without a connection, no voice can be created.
- Python 3.10 or newer, only if you install from source.

## Installing from source

    python3.11 -m venv venv
    venv/bin/python -m pip install -r requirements.txt
    venv/bin/python voxpack.py

To build the macOS application (`Vox-Pack.app`) and its release zip:

    ./build.sh

The script builds in a temporary folder, clears the Finder attributes, signs
the bundle, creates the zip and then verifies it by extracting it — the recipe
that avoids the "application is damaged" warning.

## Where is my list stored?

    ~/Documents/Vox-Pack/liste_des_voix.csv

If you used the previous version (RadioVox), your list is picked up
automatically on first launch. The old folder is never deleted.

## Help

The application explains itself: click the **?** in the top right corner.

## Notes

- The voices come from the **edge-tts** service, which relies on Microsoft
  Edge's speech synthesis. Vox-Pack only converts them to the right format.
- Microsoft's service can change without notice: if generation suddenly stops
  with an error, it almost always means the `edge-tts` library needs updating
  (`pip install --upgrade edge-tts`).
- Vox-Pack is an **independent** tool. It is neither published nor endorsed by
  the EdgeTX team.

## Supporting the project

If this tool is useful to you, you can
[buy me a coffee ☕](https://ko-fi.com/ritchy_lab).

## Licence

MIT — see the [LICENSE](LICENSE) file.

---

made by ritchy
