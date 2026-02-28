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
-p            show scan progress
```

## Filename prompt

When no `-o` is given, an interactive prompt appears before scanning. Start typing and matching PDF filenames from the current directory are suggested (substring match). Existing filenames are rejected live. Press Ctrl-C to abort.

With `--llm`, an additional rename prompt appears after OCR with a suggestion from the local ollama model based on the document content.

## Interactive scan flow

After each page is scanned, the image is shown in a viewer:

- **Enter** — keep page (multi-page: scan next)
- **r** — rotate 90° clockwise, reopen viewer; repeat as needed
- **n** — discard and rescan
- **q** — abort (single-page) or finish and OCR (multi-page)

On scanner error (e.g. feeder empty), the user is prompted to insert a document and retry.

# Known limitations

- OCR-only mode (`-m ocr`) not yet implemented
- ADF (automatic document feeder) multi-page not supported
