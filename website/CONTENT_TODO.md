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

## Site structure (the scope)

| Section | Pages | File(s) |
|---|---|---|
| **Home** | landing + download | `docs/index.md` |
| **Overview** | Summary · What is MatFinder · Statement of need · Key features | `docs/overview/` |
| **Get Started** | Download & Install · Quick start | `docs/getting-started/` |
| **User Guide** | Database search · Analysis (PhaseDRX) · 3D viewer · Tools | `docs/guide/` |
| **Tutorials & Videos** | 3 video slots + steps | `docs/tutorial.md` |
| **Examples** | SmFeO₃ worked example | `docs/examples.md` |
| **Cite** | DOI + BibTeX | `docs/cite.md` |
| **FAQ** | help & troubleshooting | `docs/faq.md` |
| **About** | The project · License · Contributing | `docs/about/` |

The navigation is defined in `website/mkdocs.yml` (the `nav:` block). To add a page,
create the `.md` file and add it to `nav`.

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

### 3. Screenshots (recommended)
Drop PNGs into `docs/assets/` and reference them in the guide pages, e.g. in
`docs/guide/analysis.md`: `![PhaseDRX overlay](../assets/screenshot-overlay.png)`.
Good places: the analysis overlay, the 3D viewer, the main search window.

### 4. Refine the text
The User Guide and tutorials are a solid first draft — tweak wording to match exactly
what the app does as it evolves.

---

## Notes

- **Download requires no registration** — buttons point to the public GitHub
  Releases page. Keep it that way.
- Primary language is **English**. Portuguese/German can be added later with the
  `mkdocs-static-i18n` plugin (the PT/DE READMEs are already a head start).
- The built site (`website/site/`) is git-ignored; CI builds it fresh each time.
- Every internal link is checked at build time (`--strict`), so a broken link fails
  the deploy instead of shipping silently.
