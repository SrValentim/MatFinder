# -*- coding: utf-8 -*-
"""Perfis de pico usados no ajuste: pseudo-Voigt com assimetria (split).

O perfil é parametrizado pela ALTURA no centro (valor máximo), pela FWHM média
w e pela mistura η (0 = gaussiana, 1 = lorentziana). A assimetria a divide a
largura em w·(1 - a) à esquerda e w·(1 + a) à direita do centro, o que absorve
a assimetria instrumental de ângulos baixos sem criar "ombros" falsos. Como a
média das duas meias-larguras é w, a área não depende de a.
"""

import numpy as np

LN2 = np.log(2.0)
# Área de um perfil com altura 1 e FWHM 1.
GAUSS_AREA = 0.5 * np.sqrt(np.pi / LN2)   # ≈ 1.0645
LORENTZ_AREA = np.pi / 2.0                # ≈ 1.5708


def pv_shape(x, center, fwhm, eta, asym=0.0):
    """Pseudo-Voigt (split) com altura 1 no centro."""
    x = np.asarray(x, dtype=float)
    width = np.where(x < center, fwhm * (1.0 - asym), fwhm * (1.0 + asym))
    u = (x - center) / width
    u2 = u * u
    return eta / (1.0 + 4.0 * u2) + (1.0 - eta) * np.exp(-4.0 * LN2 * u2)


def area_factor(eta):
    """Área por unidade de altura e de FWHM para a mistura η."""
    return eta * LORENTZ_AREA + (1.0 - eta) * GAUSS_AREA


def pv_area(height, fwhm, eta):
    """Área integrada de uma pseudo-Voigt (com ou sem assimetria)."""
    return height * fwhm * area_factor(eta)
