# About

This is a small cli-only python program to scan mainly documents with one or many pages, optimize them (black/white), put them together in a pdf and do an optical character recognition (OCR). The result is a as-small-as-possible pdf file which is full-text searchable and ready to be put in a digital archive.

# Dependencies

You will need the following additional software:

* python3
* sane (scanning)
* tesseract (ocr)
* stapler (pdf manipulation tool)
* python-pyparallel (parallel processing)
* imagemagick (optimization black/white)

# Configuration Options

## device

execute *scanimage -L* (sane package) in a shell. Sample output:
 
	device `v4l:/dev/video2' is a Noname Integrated Camera: Integrated I virtual device
	device `v4l:/dev/video0' is a Noname Integrated Camera: Integrated C virtual device
	device `dsseries:usb:0x04F9:0x60E0' is a BROTHER DS-620 sheetfed scanner

The third one is my main scanner (dsseries ... BROTHER ...). In my case I would use **dsseries** as device.

## AdditionalScanOptions

You can use everything sane (scanimage) supports. Default is:

	--mode Gray #Gray (a!) | Lineart | Color

change this to *Color* if you want to scan something which is not black/white only. *Lineart* is another option intended for black/white documents, but *Gray* works better for me.

## SaveFormatScanOnly and SaveFormatOCR

**pdf** should be fine for most cases.

## TempFormat

**pnm** should be fine for most cases.

# Usage

Just download, make executable, set the basic configuration options (*device*) and execute in a shell.

## Options:

*to be contined*

## Examples

### Single A4 page

	./scan2file -o Output

Will scan a single page, optimize it to black/white, ocr and safe as Output.pdf in the current directory.

### Multiple Pages

	./scan2file -o Output -mu

Will first ask for the number of pages, then scan everything and after that optimize and ocr the whole multi-page pdf

# File formats used

* tiff:	scanned raw data
* pnm:	temporary files and image type converted into the final pdf document
* djvu: disabled for the moment

# Known Problems / Todo

* automate Gray/Color scan option depending on the --color argument
* multiple pages using ADF (feeder) scanner
* tackle down some problems, left-over temp files, etc
* make sure PDF/A format is used everywhere
