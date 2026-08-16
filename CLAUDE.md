# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A CLI toolset for scanning documents, converting them to black-and-white PDFs, and running OCR to produce searchable PDFs. There are two main scripts:

- **`scan2file`** — Python 3 script. Drives a physical scanner via SANE (`scanimage`), optimizes images (via ImageMagick `magick`), and OCRs via `pdfsandwich` (which wraps tesseract). Supports single-page and multi-page mode.
- **`ocrscript`** — Bash script. Takes existing image/PDF files, converts them to a B/W PDF via `merge2pdfbw`, then OCRs via `pdfsandwich`. Moves originals to an `erledigt/` subdirectory on success.

## External dependencies

- `sane` / `scanimage` — scanner access (scan2file only)
- `imagemagick` / `magick` — image format conversion, B/W threshold optimization, and rotation (`mogrify`); requires IMv7
- `feh`, `display`, `eog`, or `xdg-open` — image preview during scanning (first found is used)
- `pdfsandwich` — OCR orchestrator (wraps tesseract); used by all scripts
- `merge2pdfbw` — merges images/PDFs into a single B/W PDF (ocrscript only); may live at `~/.bin/merge2pdfbw`
- `tesseract` — OCR engine (invoked by pdfsandwich)
- `python-prompt_toolkit` — live autocomplete in filename prompt (optional; falls back to readline)
- `chafa` — inline image page overview (optional; falls back to a character grid). Only produces a real image when the terminal speaks the kitty graphics protocol (ghostty) or sixel (foot); Alacritty supports neither.
- `poppler` / `pdftotext` — text extraction for LLM filename suggestion (optional, `--llm` only)
- `ollama` — local LLM for filename suggestion (optional, `--llm` only); default model: `mistral`

## Configuration (scan2file)

At the top of `scan2file`, edit these variables before use:

```python
device = 'dsseries'          # SANE device name; run `scanimage -L` to find yours
AdditionalScanOptions = '--mode Gray'  # Gray | Lineart | Color
TempFormat = 'pnm'           # intermediate image format
SaveFormatScanOnly = 'pdf'
SaveFormatOCR = 'pdf'
OllamaModel = 'mistral'      # ollama model for --llm; set to '' to disable
Threshold = 65               # default B/W threshold in percent; override with -t
BlankInkPercent = 0.1        # pages below this ink coverage are flagged as blank
OverviewMode = 'text'        # default for --overview: auto|graphics|window|text|off
```

Moving this into `~/.config/scan2file.conf` is a deferred idea — see `TODO`.

## Usage

```bash
# Single page scan + OCR — filename prompted interactively before scanning
./scan2file

# With explicit output name (skips filename prompt)
./scan2file -o OutputName

# Multi-page scan + OCR
./scan2file -mu
./scan2file -o OutputName -mu

# Scan only (no OCR)
./scan2file -m scan

# With LLM filename suggestion after OCR (requires ollama)
./scan2file --llm

# Custom B/W threshold, straighten skewed pages, crop borders
./scan2file -t 55
./scan2file --deskew          # ~4s extra per page
./scan2file --trim            # aggressive: removes all white margin

# Keep intermediate files for debugging
./scan2file --keep-temp

# Page overview rendering (default: OverviewMode, shipped as auto)
./scan2file -mu --overview window    # contact sheet in the image viewer
./scan2file -mu --overview text      # force the character grid
./scan2file -mu --overview off       # no overview at all
```

## Interactive scan flow

When no `-o` is given, an interactive filename prompt appears before scanning. It offers live autocomplete (substring match) from existing PDFs in the current directory and live validation (existing filenames and invalid names are rejected). Requires `python-prompt_toolkit`; falls back to readline otherwise.

After each page is scanned and optimized, the page is drawn **in the terminal** — in single- and multi-page mode alike — and a **single keypress** (no Enter needed) is read. The image viewer is not opened automatically; `v` opens it when a closer look is needed. The prompt shows ink coverage, current threshold and rotation:

```
  ┌──────────────────────────────┐
  │            Page 3/5          │
  ├──────────────────────────────┤
  │        (page thumbnail)      │
  └──────────────────────────────┘
Page 3/5 [12.4% ink, thr 65%, rot 90]
[Enter] keep  [v] view  [n] rescan  [r] rotate  [t] threshold  [d] drop  [b] back  [q] done:
```

- **Enter** — keep page (in multi-page mode: move to next page / scan a new one)
- **v** — open the full-size page in the image viewer; it stays open, so rotating while looking at it works
- **r** — rotate 90° clockwise; repeat as needed
- **t** — change the B/W threshold for this page and re-render
- **n** — rescan this page into the same slot
- **d** — drop this page (multi-page only)
- **b** — go back to the previous page to fix it (multi-page only, from page 2 on)
- **q** — abort (single-page) or keep this page and proceed to OCR (multi-page)

Thumbnails are **fitted and letterboxed, never stretched** (`-resize` + `-extent`, not `-resize …!`). That is the whole point of the preview: a rotated page shows up as a landscape band, and distortion is visible instead of being normalised away. A half-block cell holds 1×2 pixels and displays roughly square, so the pixel grid is `cols × rows*2` — which is why the overview tile is 26×18 for A4 (26/36 ≈ 0.72 ≈ 210/297) rather than 26×14.

With `--overview off` there is no terminal preview, so the viewer opens automatically as it did before.

Pages whose ink coverage falls below `BlankInkPercent` are flagged with a blank-page warning before the prompt.

## Page overview

In multi-page mode, **o** shows all pages scanned so far, and the same overview appears automatically before the OCR run (the last chance to fix something before the expensive step):

```
[Enter] continue  [e] edit pages  [q] abort
```

`e` re-enters the page review starting at page 1. After **o**, the single-page viewer stays closed until the user dismisses the overview — otherwise it would pop straight back over it (`want_viewer` in `review_page`).

Three rendering paths, chosen by `--overview`, whose default is the `OverviewMode` config variable:

- **graphics** — `magick montage` builds a labelled contact sheet, piped to `chafa`. Used when `chafa` is installed *and* the terminal answers the capability probe. Real thumbnails inside the terminal.
- **window** — the same contact sheet, opened in the image viewer (`feh` etc.). Real thumbnails in *any* terminal, at the cost of a window. This is the option for Alacritty, which supports no graphics protocol.
- **text** — a box grid drawn with `magick`-downscaled character thumbnails. Labels stay real text, which is why this is preferred over rasterizing the contact sheet into character art.

`auto` walks these in order: **graphics** (terminal can show pixels) → **window** (an image viewer exists) → **text**. Opening a viewer in `auto` is deliberate: the script already opens one for every page, and character art is the weakest of the three. `--overview text` insists on staying inside the terminal.

Protocol detection sends a kitty graphics query followed by a DA1 request in one round trip (`detect_graphics_protocol`); terminals that ignore the first still answer the second. `sixel` is recognised via DA1 attribute `4`. The result is cached for the process.

Two traps worth remembering here:

- **chafa cannot read PNM.** Its loaders are AVIF, GIF, HEIF, JPEG, JXL, PNG, QOI, SVG, TIFF, WebP, XWD — the page previews are PNM, so everything goes through `magick montage … png:-` first.
- **Never hand magick a user-controlled output path.** It expands format specifiers in output *filenames*: `-o "Rabatt 50%"` produced `Rabatt 50%-0.pdf`. All magick writes go through `magick_write()`, which takes `<format>:-`, captures stdout and writes the file from Python.

The raw scan is never modified. Every preview is re-rendered from it with the pipeline `deskew → threshold → trim → rotate`, so rotation and threshold can be changed in any order without loss.

On scanner error (e.g. feeder empty), temp files are cleaned up and the user is prompted to insert a document and retry. Temp files are removed on exit via `atexit` regardless of how the script terminates, unless `--keep-temp` is given. Output filename and size are printed on completion.

## Pipeline overview

**scan2file (scanocr mode):**
1. `scanimage` → `<prefix>_NNN.pnm` (raw, never modified)
2. `magick` with optional `-deskew`, `-threshold 65%`, optional `-trim`, optional `-rotate` → `<prefix>_NNN.prep.pnm`
3. `magick <all prep files>` → `<prefix>.merged.pdf`
4. `pdfsandwich -nopreproc -layout none -nthreads 1 -lang deu` → `Output.pdf`

Each page gets a unique, never-reused numeric id; page order lives in the page list, not in the filenames. Commands are built as argv lists, so paths with spaces work.

**ocrscript:**
1. Copy inputs to tmpdir
2. `merge2pdfbw` on all inputs → `name.bw.pdf`
3. `pdfsandwich -quiet -layout none -unpo '' -lang deu` → `name.bw.ocr.pdf`
4. Move result to start directory; move originals to `erledigt/`

## Language codes

`scan2file` accepts `-l ger` (mapped internally to `deu` for tesseract/pdfsandwich). `ocrscript` hardcodes `deu`.

## Tests

`./tests/run` exercises the whole scan flow without a scanner — `scanimage`,
`feh` and `pdfsandwich` are stubbed in `tests/fakebin/`. Run it after touching
`scan2file`; it exits non-zero on failure.

Scenarios run twice over, through pipes **and** through a real pseudo terminal.
The pty half is not redundant: with a pipe `sys.stdin.isatty()` is false, so
raw-mode key reading, the automatic terminal preview and the graphics protocol
probe never execute. See `tests/README.md`.

## Known limitations / TODO

See `TODO` for the full list and deferred ideas.

- OCR-only mode (`-m ocr`) in scan2file is not implemented (exits with status 1)
- ADF (automatic document feeder) multi-page not supported
- Configuration still lives in the script header, not in a config file
