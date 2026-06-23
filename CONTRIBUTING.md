# Contributing to MatFinder

Thanks for your interest in improving MatFinder! Contributions of all kinds are
welcome: bug reports, feature ideas, documentation, translations and code.

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Report a bug** — open a [GitHub issue](https://github.com/SrValentim/MatFinder/issues).
- **Request a feature** — open an issue describing the use case.
- **Improve documentation** — README, this guide, the user-facing strings.
- **Add a translation** — see *Translations* below.
- **Submit code** — fix a bug or add a feature via a Pull Request.

## Reporting issues

When filing a bug, please include:

- your **OS** and version (e.g., Windows 11, Ubuntu 24.04, macOS 14);
- how you ran MatFinder (installer, portable `.zip`, or from source);
- the **MatFinder version** (`Help/About`, or the `VERSION` file);
- **steps to reproduce**, what you expected, and what happened;
- the log file **`matfinder.log`** (next to the executable, or in the writable
  data directory) — it usually pinpoints the problem.

## Getting support

Open a GitHub issue with the `question` label, or contact the maintainer
(see `matfinder/__init__.py` / `CITATION.cff`). There is no private support
channel — keeping questions public helps the next person.

## Development setup

MatFinder is pure Python (PySide6) and runs from source on **Windows, Linux and
macOS**. You need **Python 3.11 (64-bit)**.

```bash
git clone https://github.com/SrValentim/MatFinder.git
cd MatFinder

# create a virtual environment
python3.11 -m venv .venv          # Windows: py -3.11 -m venv .venv

# activate it
source .venv/bin/activate         # Windows: .venv\Scripts\activate

# install the pinned, reproducible dependencies
python -m pip install -r build_tools/requirements-build.lock.txt

# run it
python run_matfinder.py
```

- The Materials Project search needs a free API key (set it in
  *Settings > Materials Project Key...*). COD/OQMD/ROD work without a key.
- A headless self-check of imports: `python run_matfinder.py --selftest`.

## Building the Windows distributable

The packaged `.exe`/installer are Windows-only (PyInstaller + Inno Setup):

```bat
INSTALAR_REQUISITOS.bat        :: one-time: Python 3.11 + deps
COMPILAR.bat                   :: build -> dist\MatFinder\MatFinder.exe
```

See [`COMO_COMPILAR.md`](COMO_COMPILAR.md) for details. Running from source
(above) works on any platform and is all you need to develop or review.

## Coding guidelines

- Follow the style of the surrounding code (PEP 8, 4-space indentation).
- **Every user-facing string must be translatable.** Use `tr('dotted.key')`
  for the main system, or `ptr("Texto em português")` for the PhaseDRX/flat
  strings. Never hardcode a visible string without wrapping it.
- Keep file/data writes in the **writable data directory** (the app may be
  installed in a read-only location like `C:\Program Files`).
- Prefer cross-platform APIs (`os.path`, `QDesktopServices`, `pathlib`); guard
  any platform-specific call with `sys.platform`.
- A change should at least pass `python run_matfinder.py --selftest`.

## Testing

The core logic has an automated test suite (pytest):

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Tests run headless and live in [`tests/`](tests/) (see `tests/README.md`). They
also run in CI on every push/PR (`.github/workflows/tests.yml`). Please add or
update tests when you change core logic, and reuse the sample data in
[`examples/`](examples/) as fixtures when relevant.

## Translations

UI text lives in `matfinder/assets/translations/`:

- `pt_BR.json` / `en_US.json` / `de_DE.json` — the `tr()` system (dotted keys).
- `phasedrx_i18n.json` — flat map for `ptr()` (Portuguese text → en/de).
- `elements.json` — chemical element names per language.

Add the same key/entry to every language file. To bump the displayed version
everywhere, use `python version_manager.py --set X.Y.Z`.

## Pull request process

1. Fork the repository and create a branch: `git checkout -b feature/my-change`.
2. Make focused commits. We use [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat:`, `fix:`, `docs:`, `chore:`, `ci:`).
3. Make sure the app still runs and `--selftest` passes.
4. Open a Pull Request describing **what** and **why**.
5. For user-visible changes, add an entry under **[Não publicado]** in
   [`CHANGELOG.md`](CHANGELOG.md).

## Releases

Releases follow [Semantic Versioning](https://semver.org). The process (version
bump, build, installer, tag, GitHub Release) is documented in
[`CHANGELOG.md`](CHANGELOG.md). Published tags are immutable.

Thank you for helping make MatFinder better!
