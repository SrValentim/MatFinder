# MatFinder website — scope & what to fill in

This folder (`website/`) is the **documentation site**, built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and deployed
automatically to **GitHub Pages** on every push to `main` that touches `website/`.

- **Live URL:** https://srvalentim.github.io/MatFinder/
- **Deploy:** automatic, via `.github/workflows/deploy-docs.yml` (no manual step).

---

## Run / preview the site locally

```bash
# from the repository root
py -3.11 -m venv .venv-docs
.venv-docs\Scripts\python -m pip install -r website\requirements.txt
.venv-docs\Scripts\mkdocs serve -f website\mkdocs.yml
# open http://127.0.0.1:8000
```

`mkdocs serve` live-reloads as you edit. When it looks right, commit and push — the
site updates itself.

---

## Page map (the scope)

| Page | File | Status |
|------|------|--------|
| Home / landing | `docs/index.md` | Done — has the download button |
| Download & Install | `docs/install.md` | Done |
| Features | `docs/features.md` | Done — could add screenshots |
| Tutorials & Videos | `docs/tutorial.md` | **3 video slots waiting** |
| Examples | `docs/examples.md` | Done — add more datasets |
| How to cite | `docs/cite.md` | Done |
| FAQ | `docs/faq.md` | Done |

---

## What you provide

### 1. The 3 feature videos
Open `docs/tutorial.md`. There are three slots (Video 1, 2, 3), each with a note
explaining exactly what to record. To embed a video:

1. Upload to YouTube (an **Unlisted** video is fine).
2. Replace the placeholder note with:
   ```html
   <div class="video-wrapper" markdown>
   <iframe src="https://www.youtube-nocookie.com/embed/VIDEO_ID"
           title="MatFinder tutorial" allowfullscreen></iframe>
   </div>
   ```
3. Swap `VIDEO_ID` for the id in your `https://youtu.be/VIDEO_ID` link.

### 2. Test files / datasets
Put data under the repository's `examples/` folder, then describe the workflow in
`docs/examples.md`. The page already links to `examples/` on GitHub.

### 3. Tutorial text
The step-by-step text in `docs/tutorial.md` is a first draft — refine it to match
exactly what the app does.

### 4. Screenshots (optional but recommended)
Drop PNGs into `docs/assets/` and reference them, e.g. in `features.md`:
`![Main window](assets/screenshot-main.png)`.

---

## Notes

- **Download requires no registration** — buttons point to the public GitHub
  Releases page. Keep it that way.
- Primary language is **English**. Portuguese/German can be added later with the
  `mkdocs-static-i18n` plugin (the PT/DE READMEs are already a head start).
- The built site (`website/site/`) is git-ignored; CI builds it fresh each time.
