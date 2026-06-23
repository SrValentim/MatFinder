# -*- coding: utf-8 -*-
"""Configuração compartilhada da suíte de testes (pytest).

- Roda headless (QT_QPA_PLATFORM=offscreen) para não precisar de display.
- Garante a raiz do projeto no sys.path.
- Expõe os dados de exemplo (examples/) como fixtures.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402

EXAMPLES = os.path.join(ROOT, "examples")


@pytest.fixture(scope="session")
def examples_dir():
    return EXAMPLES


@pytest.fixture(scope="session")
def example_cifs():
    d = os.path.join(EXAMPLES, "cif")
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(".cif")]


@pytest.fixture(scope="session")
def example_dat():
    d = os.path.join(EXAMPLES, "experimental", "SmFeO3")
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(".dat")]
