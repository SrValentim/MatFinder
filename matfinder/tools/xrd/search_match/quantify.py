# -*- coding: utf-8 -*-
"""Ferramentas quantitativas do search-match (fase 3).

- Score de perfil inteiro: o padrão simulado do candidato (larguras aprendidas
  dos dados, dubleto Kα2 quando houver) é ajustado ao sinal medido sem fundo.
  Funciona onde a lista de picos é pobre: dados ruidosos e picos largos.
- RIR calculado pela estrutura (I/I_coríndon) e fração em massa semiquantitativa.
"""

import hashlib
import json
import logging
import math
import os
import warnings
from dataclasses import dataclass

import numpy as np
from scipy.optimize import nnls

from matfinder.tools.xrd.emission_lines import same_d_two_theta
from .candidates import cache_dir
from .profiles import pv_shape

logger = logging.getLogger(__name__)


# =============================================================================
# Perfil inteiro
# =============================================================================

@dataclass
class ProfileContext:
    """Dados preparados para o score de perfil."""

    x: np.ndarray
    signal: np.ndarray          # dados menos o fundo
    weight: np.ndarray          # 1/σ²
    width: object               # função FWHM(2θ)
    wavelength_ka2_ratio: tuple = None  # (λ1, λ2, razão) quando os dados têm Kα2

    @property
    def noise_floor(self):
        return float(len(self.x))


def build_profile_context(two_theta, intensity, peaks, wavelength=None, wavelength_ka2=None, ka2_ratio=0.5,
                          background=None, noise=None):
    """Prepara o contexto de perfil a partir dos dados e da lista de picos."""
    from .peak_search import (FWHM_PER_SCALE, estimate_background, estimate_noise, fit_width_trend,
                              prepare_data)

    x, y, step, _ = prepare_data(two_theta, intensity)
    crystal = [p for p in peaks if p.kind == "peak"]
    widths = [p.fwhm for p in crystal] or [0.15]
    typical = float(np.median(widths))
    if noise is None or len(noise) != len(x):
        noise, _ = estimate_noise(y)
    if background is None or len(background) != len(x):
        half = float(np.clip(3.0 * typical, 0.6, 4.0)) / step
        mask = np.zeros(len(x), dtype=bool)
        for p in crystal:
            mask |= np.abs(x - p.two_theta) < 2.5 * p.fwhm
        background = estimate_background(y, half, max(1.0, 0.5 * typical / FWHM_PER_SCALE / step), mask)
    trend = fit_width_trend([(p.two_theta, p.fwhm, p.significance) for p in crystal], x[0], x[-1],
                            max(0.01, step), 3.0)
    if trend is None:
        width = lambda tt, w=max(typical, 2 * step): w  # noqa: E731
    else:
        width = trend
    doublet = (wavelength, wavelength_ka2, ka2_ratio) if wavelength and wavelength_ka2 else None
    return ProfileContext(x, y - background, 1.0 / np.maximum(np.asarray(noise, dtype=float), 1e-12) ** 2,
                          width, doublet)


def phase_profile(ctx, two_theta, intensity):
    """Perfil simulado (pseudo-Voigt, η = 0,5) das reflexões dadas, no eixo do contexto."""
    out = np.zeros(len(ctx.x))
    lines = [(float(t), float(i)) for t, i in zip(two_theta, intensity)]
    if ctx.wavelength_ka2_ratio:
        lam1, lam2, ratio = ctx.wavelength_ka2_ratio
        lines += [(float(same_d_two_theta(t, lam1, lam2)), ratio * i) for t, i in zip(two_theta, intensity)]
    for tt, inten in lines:
        if not np.isfinite(tt) or inten <= 0:
            continue
        w = ctx.width(tt)
        lo = np.searchsorted(ctx.x, tt - 8.0 * w)
        hi = np.searchsorted(ctx.x, tt + 8.0 * w)
        if hi > lo:
            out[lo:hi] += inten * pv_shape(ctx.x[lo:hi], tt, w, 0.5)
    return out


def fit_profiles(ctx, profiles, base=None):
    """Escalas (≥ 0) dos perfis por mínimos quadrados ponderados e a fração do sinal explicada.

    A fração é normalizada pelo nível de ruído: um modelo perfeito explica 1,0
    mesmo em dados ruidosos.
    """
    signal = ctx.signal if base is None else ctx.signal - base
    if not profiles:
        return np.zeros(0), 0.0, signal
    sw = np.sqrt(ctx.weight)
    design = np.column_stack([p * sw for p in profiles])
    scales, _ = nnls(design, signal * sw)
    model = sum(s * p for s, p in zip(scales, profiles))
    before = float(np.sum(ctx.weight * signal ** 2))
    after = float(np.sum(ctx.weight * (signal - model) ** 2))
    usable = max(before - ctx.noise_floor, 1e-9 * before, 1e-300)
    explained = float(np.clip((before - after) / usable, 0.0, 1.0))
    return scales, explained, signal - model


def profile_score(ctx, match, base=None):
    """Fração (0-1) do sinal (ou do resíduo, com ``base``) explicada pelo candidato."""
    if match is None or len(match.ref_two_theta) == 0:
        return 0.0, 0.0
    prof = phase_profile(ctx, match.ref_two_theta, match.ref_intensity)
    scales, explained, _ = fit_profiles(ctx, [prof], base=base)
    return explained, float(scales[0]) if len(scales) else 0.0


# =============================================================================
# RIR e semiquantitativa
# =============================================================================

_CORUNDUM = {}


def _corundum():
    from pymatgen.core import Lattice, Structure
    return Structure.from_spacegroup("R-3c", Lattice.hexagonal(4.7589, 12.991), ["Al", "O"],
                                     [[0.0, 0.0, 0.35216], [0.30624, 0.0, 0.25]])


def _strongest(structure, wavelength, lo, hi):
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pattern = XRDCalculator(wavelength=wavelength).get_pattern(structure, scaled=False, two_theta_range=(lo, hi))
    y = np.asarray(pattern.y, dtype=float)
    x = np.asarray(pattern.x, dtype=float)
    return x, y


def _max_two_theta(wavelength):
    return float(min(150.0, 2.0 * math.degrees(math.asin(min(1.0, wavelength / (2.0 * 0.6))))))


def rir_of(cif_text, wavelength, two_theta_range):
    """RIR (I/I_coríndon, picos mais fortes, misturas 1:1 em massa) calculado pela estrutura.

    Returns:
        dict(rir, inrange_fraction): inrange_fraction é a intensidade da linha mais
        forte DENTRO da faixa medida sobre a da linha mais forte em geral (a escala da
        referência é normalizada pela linha mais forte dentro da faixa).
    """
    lo, hi = float(two_theta_range[0]), float(two_theta_range[1])
    digest = hashlib.sha1(f"rir|{wavelength:.6f}|{lo:.2f}|{hi:.2f}|{cif_text}".encode("utf-8", "replace")).hexdigest()[:24]
    path = os.path.join(cache_dir("rir"), f"{digest}.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        pass
    from pymatgen.core import Structure
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        structure = Structure.from_str(cif_text, fmt="cif", primitive=True)
    top = _max_two_theta(wavelength)
    x, y = _strongest(structure, wavelength, 2.0, top)
    if len(y) == 0:
        raise ValueError("estrutura sem reflexões")
    inside = (x >= lo) & (x <= hi)
    vm = structure.volume * structure.composition.weight
    key = round(wavelength, 6)
    if key not in _CORUNDUM:
        cor = _corundum()
        _, yc = _strongest(cor, wavelength, 2.0, top)
        _CORUNDUM[key] = (float(np.max(yc)), cor.volume * cor.composition.weight)
    ic, vmc = _CORUNDUM[key]
    out = {"rir": float((np.max(y) / vm) / (ic / vmc)),
           "inrange_fraction": float(np.max(y[inside]) / np.max(y)) if inside.any() else 0.0}
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh)
    except OSError:
        pass
    return out


def semi_quant(scales, rir_infos):
    """Frações em massa (soma 1) pelo método RIR.

    scales: altura observada por unidade de intensidade de referência (0-100,
    normalizada pela linha mais forte dentro da faixa), uma por fase.
    """
    values = []
    for scale, info in zip(scales, rir_infos):
        if not info or info.get("rir", 0) <= 0 or info.get("inrange_fraction", 0) <= 0:
            values.append(np.nan)
            continue
        strongest_height = 100.0 * float(scale) / info["inrange_fraction"]
        values.append(strongest_height / info["rir"])
    arr = np.array(values, dtype=float)
    total = np.nansum(arr)
    if not np.isfinite(total) or total <= 0:
        return [None] * len(values)
    return [None if not np.isfinite(v) else float(v / total) for v in arr]
