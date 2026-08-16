# Tests

Runs the whole scan flow without a scanner. `scanimage`, `feh` and
`pdfsandwich` are replaced by the stubs in `fakebin/`, which are put in front
of `PATH`; test pages are rendered with `magick` and cached in
`$TMPDIR/scan2file-testpages`.

```bash
./tests/run          # everything
./tests/run -v       # print the transcript of failing scenarios
```

Exits non-zero if anything fails. Needs `magick` and `pdfinfo`; nothing else,
and no scanner.

## Why two ways of driving the script

**Pipe scenarios** feed keystrokes through stdin. Fast, and enough for flow,
filenames and page bookkeeping.

**Pty scenarios** run the script inside a real pseudo terminal and answer its
device-attributes query the way a terminal would. This is not redundant: with
a pipe, `sys.stdin.isatty()` is false, so raw-mode single-key reading, the
automatic terminal preview and the graphics protocol probe never execute. Two
bugs have already hidden in exactly those paths — pipe tests could not have
found either.

`harness.DA1_NO_GRAPHICS` answers like Alacritty (no sixel);
`harness.DA1_SIXEL` claims sixel support, which pushes the overview onto the
graphics path.

## What the scenarios protect

Beyond the obvious flow coverage, several scenarios exist because the bug they
describe actually happened:

- **spaces, dots and percent in the output name** — commands used to be built
  as strings and split again, and magick expands format specifiers in output
  *filenames*, turning `Rabatt 50%.pdf` into `Rabatt 50%-0.pdf`.
- **12 pages, back to page 1, rescan** — page files used to be found by
  globbing `prefix_1*`, which also matches `_10`.
- **thumbnail geometry** — the preview exists to show orientation and
  distortion, so it must letterbox instead of stretch. Measured on solid black
  pages, where the inked area is exactly the page. Reintroducing
  `-resize WxH!` makes the portrait and landscape cases fail, as it should.
- **viewer opened only on demand** — the image viewer must stay closed unless
  `v` is pressed (or `--overview off` is given).

## Adding a scenario

Append a `go(...)` call in `pipe_scenarios` or `pty_scenarios`. `expect` and
`reject` take regular expressions matched against the combined output;
`exit_code` checks the status. Keep the name a sentence describing the
guarantee, since that is what a failure prints.
