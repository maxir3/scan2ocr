# About

CLI toolset for scanning documents, converting them to black-and-white PDFs, and running OCR to produce searchable PDFs.

**`scan2file`** — Python 3 script. Drives a physical scanner via SANE, optimizes images via ImageMagick, and OCRs via pdfsandwich (tesseract). Supports single-page and multi-page mode with interactive preview.

# Dependencies

Required:

- `python3` — standard library only, no `pip install` needed
- `sane` / `scanimage` — scanner access
- `imagemagick` (IMv7, `magick`) — image conversion, B/W optimization, rotation
- `pdfsandwich` — OCR orchestrator (wraps tesseract)
- `tesseract` — OCR engine, plus the language data for the documents you scan (`tesseract-data-deu` for the default `-l ger`)

Optional:

- `feh`, `display`, `eog`, or `xdg-open` — full-size page view with `v` (first found is used)
- `python-prompt_toolkit` — live filename autocomplete (falls back to readline)
- `chafa` — real page images inside the terminal (falls back to a character grid)
- `poppler` — `pdftotext` for `--llm`; `pdfseparate` / `pdfunite` for `merge2pdfbw`
- `ollama` — local LLM for filename suggestions (`--llm` only, see below)

## Installing on Arch Linux

```bash
sudo pacman -S --needed python sane imagemagick tesseract tesseract-data-deu
sudo pacman -S --needed feh python-prompt_toolkit chafa poppler ollama   # optional
yay -S pdfsandwich   # from the AUR, with the AUR helper of your choice
```

For other OCR languages install `tesseract-data-<lang>`, e.g. `tesseract-data-eng`.

## LLM filename suggestion (optional)

`--llm` is a convenience, not a requirement. `scan2file` does not call the
`ollama` program; it talks to the ollama server over HTTP at
`localhost:11434`. So the server has to be running and the model pulled:

```bash
sudo systemctl enable --now ollama
ollama pull mistral          # or whatever OllamaModel is set to
```

If the server is not running, the step is skipped silently and the file keeps
its name. If the server runs but the request fails (e.g. the model is not
pulled), a one-line message says so. `OllamaModel = ''` disables it entirely.

# Configuration

At the top of `scan2file`, edit these variables:

```python
device = 'dsseries'           # SANE device name; run `scanimage -L` to find yours
AdditionalScanOptions = '--mode Gray'  # Gray | Lineart | Color
TempFormat = 'pnm'            # intermediate image format
SaveFormatScanOnly = 'pdf'
SaveFormatOCR = 'pdf'
OllamaModel = 'mistral'       # ollama model for --llm; set to '' to disable
Threshold = 65                # default B/W threshold in percent; override with -t
BlankInkPercent = 0.1         # pages below this ink coverage are flagged as blank
OverviewMode = 'auto'         # default for --overview: auto|graphics|window|text|off
```

# Usage

```bash
# Single page scan + OCR — filename prompted interactively before scanning
./scan2file

# With explicit output name (skips filename prompt)
./scan2file -o OutputName

# Multi-page scan + OCR
./scan2file -mu
./scan2file -o OutputName -mu

# Scan only, no OCR
./scan2file -m scan

# With LLM filename suggestion after OCR (requires ollama)
./scan2file --llm

# Options
-r 300        resolution in dpi (default: 300)
-l ger        OCR language (default: ger → deu/German)
-c            preserve colors (skip B/W optimization)
-t 65         B/W threshold in percent (default: 65)
--deskew      straighten skewed pages (~4s extra per page)
--trim        crop the border around the page content (aggressive)
--no-progress hide scan progress
--keep-temp   keep intermediate files for debugging
--overview M  page overview: auto | graphics | window | text | off
--probe-terminal  report what this terminal can draw, then exit
```

## Page overview

In multi-page mode, **o** shows all pages scanned so far, and the same overview appears automatically before OCR starts:

```
  ┌──────────────────────────┐  ┌──────────────────────────┐
  │          Page 1          │  │          Page 2          │
  ├──────────────────────────┤  ├──────────────────────────┤
  │  -@*%#**%+@#. @.         │  │                          │
  │   -:::. . ::  .          │  │                          │
  │  :*++++++++++++++++++*-  │  │        .:-==-:.          │
  │                          │  │                          │
  ├──────────────────────────┤  ├──────────────────────────┤
  │         6.3% ink         │  │          blank?          │
  └──────────────────────────┘  └──────────────────────────┘

[Enter] continue  [e] edit pages  [q] abort
```

Three ways to draw it, selected with `--overview` (default: the `OverviewMode` config variable):

| Mode | What you get | Requirement |
|---|---|---|
| `graphics` | Real thumbnails inline in the terminal | `chafa` **and** a terminal with the kitty graphics protocol (ghostty) or sixel (foot) |
| `window` | Real thumbnails as a contact sheet in the image viewer | an image viewer (`feh` etc.) — works in **any** terminal, including Alacritty |
| `text` | The character grid above | nothing |

The default is `auto`, which tries `graphics` → `window` → `text`. In **foot** (sixel) or **ghostty** (kitty protocol) you get real images inside the terminal — for the per-page preview as well as the overview. In a terminal that supports neither, the overview falls back to the image viewer and the page preview to character art. `--overview text` keeps everything as character art; `OverviewMode` at the top of the script sets the default permanently.

Not sure what your terminal can do?

```bash
./scan2file --probe-terminal
```

`--overview off` disables the terminal preview entirely; the image viewer then opens automatically for each page, as it did before.

## Filename prompt

When no `-o` is given, an interactive prompt appears before scanning. Start typing and matching PDF filenames from the current directory are suggested (substring match). Existing filenames are rejected live. Press Ctrl-C to abort.

With `--llm`, an additional rename prompt appears after OCR with a suggestion from the local ollama model based on the document content.

## Interactive scan flow

After each page is scanned, it is drawn **in the terminal** — single- and multi-page alike — and a **single keypress** decides what happens, no Enter required. No image viewer opens unless you ask for it with `v`. The prompt shows ink coverage, threshold and rotation:

```
Page 3/5 [12.4% ink, thr 65%, rot 90]
[Enter] keep  [v] view  [n] rescan  [r] rotate  [t] threshold  [d] drop  [b] back  [q] done:
```

- **Enter** — keep page (multi-page: go to the next one)
- **v** — open the full-size page in the image viewer (stays open while you rotate)
- **r** — rotate 90° clockwise; repeat as needed
- **t** — change the B/W threshold for this page and re-render it
- **n** — rescan this page
- **d** — drop this page (multi-page only)
- **b** — go back to the previous page to fix it (multi-page only)
- **q** — abort (single-page) or keep this page and finish (multi-page)

Nearly empty pages are flagged with a blank-page warning, which makes discarding scanned backsides easy.

Thumbnails are fitted, never stretched, so a rotated page appears as a landscape band and a distorted scan looks distorted. That is what the preview is for — checking orientation at a glance, not reading the document.

The raw scan is kept untouched and every preview is re-rendered from it, so rotation and threshold can be changed in any order and any number of times without quality loss.

On scanner error (e.g. feeder empty), the user is prompted to insert a document and retry.

# merge2pdfbw

Merges images and PDFs into one black-and-white PDF, `<first-input>.bw.pdf`
next to the first input:

```bash
./merge2pdfbw scan1.jpg scan2.png letter.pdf     # -> scan1.bw.pdf
THRESHOLD=55% DEFAULT_DPI=300 ./merge2pdfbw photo.jpg
```

Each page keeps its own resolution; images without a usable one (phone photos
often claim 72 dpi) are treated as `DEFAULT_DPI`. Needs ImageMagick and poppler.

# Tests

```bash
./tests/run
```

Runs the whole scan flow without a scanner (stubs for `scanimage`, `feh` and
`pdfsandwich`). See `tests/README.md`.

# Known limitations

- OCR-only mode (`-m ocr`) not yet implemented
- ADF (automatic document feeder) multi-page not supported
- Configuration lives in the script header; see `TODO` for the config-file idea
