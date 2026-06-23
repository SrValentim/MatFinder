# Tests

Automated test suite (pytest) for MatFinder's core logic — the parts that run
without the GUI.

## Running

```bash
python -m pip install -r requirements-dev.txt   # pytest
python -m pytest                                 # from the project root
```

Tests run headless (`QT_QPA_PLATFORM=offscreen`, set in `conftest.py`).

## What is covered

| File | Module under test |
|------|-------------------|
| `test_grupo_espacial.py` | space-group data table (230 groups) |
| `test_normalization.py` | `tools/xrd/normalization_dialog` (normalization math) |
| `test_background.py` | `tools/xrd/background_removal` (SNIP / arPLS / dispatch) |
| `test_xrd_math.py` | `tools/xrd/xrd_math_tools` (smoothing, peak detection) |
| `test_quimica.py` | `tools/calculator/quimica_calc` (molar mass, conversions) |
| `test_api_logic.py` | `core/api_logic._normalize_doi` (no network) |
| `test_translations.py` | `core/translator` (ptr) + translation-file integrity |
| `test_examples_data.py` | the sample data in [`../examples/`](../examples/) (CIFs + `.dat`) |

GUI dialogs/widgets are intentionally not unit-tested here; a headless smoke
check of the whole frozen app is available via `MatFinder.exe --selftest`
(see `build_tools/build_clean.py`).

## `manual/`

Older ad-hoc/visual scripts (require a display and manual inspection) live in
`manual/` and are **not** collected by pytest (`norecursedirs = manual`).
