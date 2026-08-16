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

# Page overview rendering (default: auto)
./scan2file -mu --overview text      # force the character grid
./scan2file -mu --overview off       # no overview at all
```

## Interactive scan flow

When no `-o` is given, an interactive filename prompt appears before scanning. It offers live autocomplete (substring match) from existing PDFs in the current directory and live validation (existing filenames and invalid names are rejected). Requires `python-prompt_toolkit`; falls back to readline otherwise.

After each page is scanned and optimized, the image is shown in a viewer and a **single keypress** (no Enter needed) is read. The prompt shows ink coverage, current threshold and rotation:

```
Page 3/5 [12.4% ink, thr 65%, rot 90]
[Enter] keep  [n] rescan  [r] rotate  [t] threshold  [d] drop  [b] back  [q] done:
```

- **Enter** — keep page (in multi-page mode: move to next page / scan a new one)
- **r** — rotate 90° clockwise; repeat as needed
- **t** — change the B/W threshold for this page and re-render
- **n** — rescan this page into the same slot
- **d** — drop this page (multi-page only)
- **b** — go back to the previous page to fix it (multi-page only, from page 2 on)
- **q** — abort (single-page) or keep this page and proceed to OCR (multi-page)

Pages whose ink coverage falls below `BlankInkPercent` are flagged with a blank-page warning before the prompt.

## Page overview

In multi-page mode, **o** shows all pages scanned so far, and the same overview appears automatically before the OCR run (the last chance to fix something before the expensive step):

```
[Enter] continue  [e] edit pages  [q] abort
```

`e` re-enters the page review starting at page 1. Two rendering paths, chosen by `--overview` (`auto` by default):

- **graphics** — `magick montage` builds a labelled contact sheet, piped to `chafa`. Used when `chafa` is installed *and* the terminal answers the capability probe. Real, readable thumbnails.
- **text** — a box grid drawn with `magick`-downscaled character thumbnails. Labels stay real text, which is why this is preferred over rasterizing the contact sheet when no graphics protocol is available.

Protocol detection sends a kitty graphics query followed by a DA1 request in one round trip (`detect_graphics_protocol`); terminals that ignore the first still answer the second. `sixel` is recognised via DA1 attribute `4`. The result is cached for the process.

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

## Known limitations / TODO

See `TODO` for the full list and deferred ideas.

- OCR-only mode (`-m ocr`) in scan2file is not implemented (exits with status 1)
- ADF (automatic document feeder) multi-page not supported
- Configuration still lives in the script header, not in a config file
