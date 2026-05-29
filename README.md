# minq-nhentai-sixel
A fork of the original `minq-nhentai` project, a terminal-based nhentai reader with added sixel support and an extensive refactoring.

## Notable changes

- Improved search UX. Multiple tags, artists and more can be scanned properly and fast, without risking rate-limiting.
- Reworked reader: supports thumbnail/full-page modes and background downloading.
- Upgraded the naive scraping approach to use of the official API. Hopefully this will keep working for longer thanks to that.
- Refactored from monolithic scripts into a package layout under `minq_nhentai/` (`app`, `models`, `scrape`, `ui`, `net`, etc.) for easier maintenance.
- Added compatibility fallback for some Debian environments where `img2sixel` cannot decode WebP directly, so now it gets translated into a png image then sent to img2sixel.
- Added `.gitignore` and `requirements.txt`. Because yes.

## Install
### TBD
