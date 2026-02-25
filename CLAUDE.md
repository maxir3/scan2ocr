# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A CLI toolset for scanning documents, converting them to black-and-white PDFs, and running OCR to produce searchable PDFs. There are two main scripts:

- **`scan2file`** — Python 3 script. Drives a physical scanner via SANE (`scanimage`), optimizes images (via ImageMagick `convert`), and OCRs via `pdfsandwich` (which wraps tesseract). Supports single-page and multi-page mode.
- **`ocrscript`** — Bash script. Takes existing image/PDF files, converts them to a B/W PDF via `merge2pdfbw`, then OCRs via `pdfsandwich`. Moves originals to an `erledigt/` subdirectory on success.
- **`ocrscript-convert`** — Older/simpler bash script that converts a directory of images to PDF and runs `pdfsandwich`. Largely superseded by `ocrscript`.

## External dependencies

- `sane` / `scanimage` — scanner access (scan2file only)
- `imagemagick` / `convert` — image format conversion and B/W threshold optimization
- `pdfsandwich` — OCR orchestrator (wraps tesseract); used by all scripts
- `merge2pdfbw` — merges images/PDFs into a single B/W PDF (ocrscript only); may live at `~/.bin/merge2pdfbw`
- `tesseract` — OCR engine (invoked by pdfsandwich)
- `stapler` — PDF manipulation (referenced in scan2file but currently unused/commented out)

## Configuration (scan2file)

At the top of `scan2file`, edit these variables before use:

```python
device = 'dsseries'          # SANE device name; run `scanimage -L` to find yours
AdditionalScanOptions = '--mode Gray'  # Gray | Lineart | Color
TempFormat = 'pnm'           # intermediate image format
SaveFormatScanOnly = 'pdf'
SaveFormatOCR = 'pdf'
```

## Usage

```bash
# Single page scan + OCR (German, default)
./scan2file -o OutputName

# Multi-page scan + OCR
./scan2file -o OutputName -mu

# Scan only (no OCR)
./scan2file -o OutputName -m scan

# OCR existing image/PDF files
./ocrscript file1.pdf file2.jpg ...
```

`ocrscript` tool paths can be overridden via env vars: `MERGE2PDFBW=/path/to/merge2pdfbw PDFSANDWICH=/path/to/pdfsandwich ./ocrscript ...`

## Pipeline overview

**scan2file (scanocr mode):**
1. `scanimage` → `TempFile.pnm`
2. ImageMagick `convert` with `-threshold 65%` → `TempFile.bw.pnm`
3. `convert *.bw.pnm` → `TempFile.merged.pdf`
4. `pdfsandwich -nopreproc -layout none -lang deu` → `Output.pdf`

**ocrscript:**
1. Copy inputs to tmpdir
2. `merge2pdfbw` on all inputs → `name.bw.pdf`
3. `pdfsandwich -quiet -layout none -unpo '' -lang deu` → `name.bw.ocr.pdf`
4. Move result to start directory; move originals to `erledigt/`

## Language codes

`scan2file` accepts `-l ger` (mapped internally to `deu` for tesseract/pdfsandwich). `ocrscript` hardcodes `deu`.

## Known limitations / TODO

- OCR-only mode (`-m ocr`) in scan2file is not implemented
- ADF (automatic document feeder) multi-page not supported
- Color preservation in multi-page scan mode has partial/broken logic
- `ocrscript-convert` is an older script, kept for reference
