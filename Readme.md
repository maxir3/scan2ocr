# About

CLI toolset for scanning documents, converting them to black-and-white PDFs, and running OCR to produce searchable PDFs.

**`scan2file`** — Python 3 script. Drives a physical scanner via SANE, optimizes images via ImageMagick, and OCRs via pdfsandwich (tesseract). Supports single-page and multi-page mode with interactive preview.

# Dependencies

- `python3`
- `sane` / `scanimage` — scanner access
- `imagemagick` (IMv7, `magick`) — image conversion, B/W optimization, rotation
- `pdfsandwich` — OCR orchestrator (wraps tesseract)
- `tesseract` — OCR engine
- `feh`, `display`, `eog`, or `xdg-open` — image preview during scanning (first found is used)
- `python-prompt_toolkit` — live filename autocomplete (optional, falls back to readline)
- `chafa` — inline image page overview (optional, falls back to a character grid)
- `poppler` / `pdftotext` — text extraction for LLM suggestion (optional, `--llm` only)
- `ollama` — local LLM for filename suggestion (optional, `--llm` only)

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
--overview M  page overview: auto | graphics | text | off (default: auto)
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

With `chafa` installed **and** a terminal that speaks the kitty graphics protocol (ghostty) or sixel (foot), the overview is drawn as a real inline image instead — a labelled contact sheet built by `magick montage`. Alacritty supports neither protocol, so it gets the character grid above. Force either path with `--overview graphics` / `--overview text`.

## Filename prompt

When no `-o` is given, an interactive prompt appears before scanning. Start typing and matching PDF filenames from the current directory are suggested (substring match). Existing filenames are rejected live. Press Ctrl-C to abort.

With `--llm`, an additional rename prompt appears after OCR with a suggestion from the local ollama model based on the document content.

## Interactive scan flow

After each page is scanned, the image is shown in a viewer and a **single keypress** decides what happens — no Enter required. The prompt shows ink coverage, threshold and rotation:

```
Page 3/5 [12.4% ink, thr 65%, rot 90]
[Enter] keep  [n] rescan  [r] rotate  [t] threshold  [d] drop  [b] back  [q] done:
```

- **Enter** — keep page (multi-page: go to the next one)
- **r** — rotate 90° clockwise; repeat as needed
- **t** — change the B/W threshold for this page and re-render it
- **n** — rescan this page
- **d** — drop this page (multi-page only)
- **b** — go back to the previous page to fix it (multi-page only)
- **q** — abort (single-page) or keep this page and finish (multi-page)

Nearly empty pages are flagged with a blank-page warning, which makes discarding scanned backsides easy.

The raw scan is kept untouched and every preview is re-rendered from it, so rotation and threshold can be changed in any order and any number of times without quality loss.

On scanner error (e.g. feeder empty), the user is prompted to insert a document and retry.

# Known limitations

- OCR-only mode (`-m ocr`) not yet implemented
- ADF (automatic document feeder) multi-page not supported
- Configuration lives in the script header; see `TODO` for the config-file idea
