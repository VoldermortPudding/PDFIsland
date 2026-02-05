# PDFIsland 🏝️📄

Welcome to **PDFIsland**, a beginner-friendly PDF reader powered by **PDFium** (via `pypdfium2`).

This starter app includes:

- Open local PDF files
- Previous/next page navigation
- Zoom in / zoom out
- Single-page and double-page mode
- Adjustable color settings:
  - Brightness
  - Contrast
  - Saturation
  - Optional invert colors (great for dark-ish viewing)

---

## Why this stack?

You asked to use PDFium, and `pypdfium2` is a nice Python wrapper around PDFium.
With `PySide6`, we can quickly build a desktop UI that is easy to understand and extend.

---

## 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2) Run the app

```bash
python app.py
```

---

## Controls overview

- **Open PDF**: Pick a `.pdf` file from your computer
- **◀ Prev / Next ▶**: Move through pages
- **Zoom slider**: 25% to 400%
- **Single / Double**: Toggle 1-page or 2-page view
- **Brightness / Contrast / Saturation** sliders: tune the look
- **Invert colors**: quick color inversion toggle
- **Reset colors**: return color sliders + invert to defaults

---

## How rendering works (simple version)

1. PDF pages are rendered by **PDFium** (`pypdfium2`) into bitmap images.
2. Images are converted into Pillow format.
3. Color adjustments are applied.
4. Final image(s) are shown in the PySide UI.

---

## Newbie-friendly next ideas

- Add **fit-to-width / fit-to-page** buttons
- Add keyboard shortcuts (e.g., arrows for pages)
- Add bookmarks and table-of-contents panel
- Save and restore UI preferences
- Add page thumbnails sidebar

Have fun building PDFIsland 🌊
