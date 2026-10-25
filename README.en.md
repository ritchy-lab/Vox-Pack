<img src="assets/logo-fond-sombre.png" alt="Vox-Pack" width="760">

🇫🇷 **[Version française](README.md)** · 🇩🇪 **[Deutsche Fassung](README.de.md)**

# Vox-Pack

**Make your radio talk.**

Vox-Pack builds the voice files your EdgeTX radio speaks during a flight:
"Engine armed", "Gear down", "Timer started"…

You type your phrases, pick a voice, and press **Let's Go**. The application
creates the files in the exact format EdgeTX expects (16-bit, 32 kHz, mono),
ready to copy onto the radio's SD card.

## What it looks like

<img src="captures/fenetre-en.png" alt="The Vox-Pack window" width="820">

You write your phrases, pick a voice, tick the lines to generate, and press
**Let's Go**.

<img src="captures/voix-pretes-en.png" alt="Your voices are ready" width="520">

Two clicks later, a folder of `.wav` files ready for the radio. The app always
tells you **where** it wrote them, and **what may have failed**.

<img src="captures/aide-en.png" alt="Vox-Pack's help window" width="520">

And it explains itself: the **?** button in the top right corner opens this
help.

## How it works

1. **Pick a voice.** There are **30** of them: 11 in French (France,
   Switzerland, Belgium, Quebec) and 19 in English (United States, United
   Kingdom, Ireland). The menu shows the accent — "Denise (Female - France)",
   "Ryan (Male - United Kingdom)" — the current voice is ticked, and **★**
   marks EdgeTX's official voice (Denise in French, Emily in English).
2. **Type your phrases.** The list comes pre-filled with 44 common
   announcements (engine, flaps, gear, timer, flight modes…). You can edit,
   add or remove any line.
3. **Tick** the lines you want, or click **All**. To tick several at once:
   click the first box, then **Shift + click** on the last one.
4. **Press Let's Go** and choose a folder: the `.wav` files are created.

The **Listen** button plays **every ticked line**, one after another, before
you generate anything.

While generating, a **status line** — under the progress bar — tells you at
every moment what the application is doing: fetching the voice, then writing
the file.

Your list is saved automatically, so you find it again next time.

## EdgeTX system sounds

The **File → Create system sounds…** menu builds the **186 official SYSTEM
files** in French (**212** in English) with the chosen voice, in a `SYSTEM/`
folder to copy to the SD card. The list comes from the official EdgeTX
repository and is not modified; your phrases, list and settings are untouched.

## Robot voices and HAL 9000

On the right of the window, **three dots Robot 1 to 3 and the HAL 9000 dot** transform the
chosen voice. None lit: the normal voice. Click a dot, then **Listen**; click
the lit dot again to return to normal. The effect also applies to the list
files and the system sounds.

## Updates

At startup, the application quietly checks whether a newer version has been
published on the Releases page. If so, a small window offers to download it
straight to your Downloads folder, then opens the folder; otherwise nothing
appears. If you are offline, nothing happens.

## The application's language

The application comes **in French and in English**. It starts in the language
of your computer, and you can change it whenever you like in
**File → Language**.

That choice drives **all three at once**: the texts, the voices offered, and
the phrase list. And **each language keeps its own list**: you can work in
French, switch to English, then come back — **your work is still there**.

## What it produces

- **WAV PCM 16-bit, 32 kHz, mono** — the format EdgeTX reads.
- One file per phrase, named after the left-hand column
  (`mot-arme.wav`, `train-so.wav`…), inside a **Vox-Pack** sub-folder.
- ⚠️ File names are limited to **8 characters**, with no accent and no space
  (letters, digits, `-` and `_` only).
  On an **EdgeTX older than 2.11**, only **6 characters** are read on colour
  radios and small black-and-white radios — the X9D and X9E accept 8 even
  before that. **If in doubt, stay at 6 characters**: it will be read on every
  radio and every version.
- The files go into a folder that you then copy onto the SD card, inside
  `SOUNDS/en` (or `SOUNDS/fr`).

## Managing your list

The **File** menu lets you:

- **Export** your list to a file, to back it up or share it;
- **Import** an existing list: one name and one phrase per line, separated by
  a comma. The application asks for confirmation before replacing anything;
- **Load the default list**, the one shipped with the application, in the
  language of your voices.

## Requirements

- **macOS 11 or newer** (Apple Silicon) or **Windows 10 or newer**.
- **An Internet connection**: the voices are synthesised by Microsoft Edge's
  online service. The text of your phrases is therefore sent to Microsoft when
  you generate. Without a connection, no voice can be created.
- **The voices** come from the **Microsoft Edge service** via `edge-tts`
  (unofficial). Vox-Pack does not distribute the voices; the text is sent to
  Microsoft when you generate.
- Python 3.10 or newer, only if you install from source.

## Installing

### macOS

1. Download **`Vox-Pack.zip`** from the
   [Releases](https://github.com/ritchy-lab/Vox-Pack/releases) page and unzip it.
2. Drag **Vox-Pack.app** into your **Applications** folder.

3. **The very first time, macOS will refuse to open it**: the application does
   not come from the App Store and has no Apple certificate (it costs €99 a
   year). Two ways to allow it:

   **a) Right-click → Open** on the application, then confirm.
   *(On the most recent macOS versions, this no longer works.)*

   **b) System Settings → Privacy & Security**, scroll down to the message
   about **Vox-Pack**, then click **"Open Anyway"**. Confirm with your password
   or Touch ID.

   **This is a one-off.** After that, a normal double-click works.

<details>
<summary>If macOS claims the application is "damaged"</summary>

That message is misleading — nothing is broken. It is the consequence of not
having an Apple certificate. Open **Terminal**, paste this line, then start the
application again:

    xattr -dr com.apple.quarantine /Applications/Vox-Pack.app

</details>

### Windows

1. Download **`Vox-Pack.exe`** from the
   [Releases](https://github.com/ritchy-lab/Vox-Pack/releases) page.
2. Double-click it. Windows shows **"Windows protected your PC"**: click
   **More info**, then **Run anyway**.

   Again, this is because the application is not signed. It asks for no special
   rights: it simply creates the `.wav` files in the folder you choose.

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

    ~/Documents/Vox-Pack/liste_fr.csv     (French list)
    ~/Documents/Vox-Pack/liste_en.csv     (English list)

One list per language. If you used the previous version (RadioVox), your list
is picked up automatically as the French list on first launch. The old folder
is never deleted.

## Help

The application explains itself: click the **?** in the top right corner.

## Notes

- The voices come from the **edge-tts** service, which relies on Microsoft
  Edge's speech synthesis. Vox-Pack only converts them to the right format.
- On startup, the application **checks that the voices it offers still exist**
  at Microsoft's end, and drops the ones that have disappeared. If that check
  fails (no connection), the list is left untouched.
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
