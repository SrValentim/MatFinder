# -*- coding: utf-8 -*-
"""Pontuação de candidatos contra a lista de picos observada (search-match, fase 2).

Para cada candidato:

1. Simula as reflexões (Kα1) com o pymatgen, com cache em disco.
2. Junta reflexões mais próximas que a resolução dos dados.
3. Alinha zero (deslocamento global de 2θ) e escala isotrópica da rede por busca
   em grade vetorizada. Estruturas do Materials Project vêm de DFT (rede alguns
   por cento maior que a real), por isso aceitam uma faixa maior.
4. Casa reflexões e picos um a um (algoritmo húngaro) dentro de uma tolerância
   dada pela largura e pela incerteza de cada pico observado.
5. Calcula quatro notas de 0 a 1 e o score de 0 a 100 (média geométrica ponderada):
   - posições: quão perto cada reflexão casada fica do pico;
   - referência: fração da intensidade das reflexões ESPERADAS que foi achada
     (só conta reflexões cuja altura prevista passa do limite de detecção);
   - observado: fração da intensidade observada explicada pelo candidato;
   - intensidades: concordância entre alturas observadas e previstas, tolerante
     a orientação preferencial.
"""

import hashlib
import json
import logging
import math
import os
import warnings
from dataclasses import asdict, dataclass, field, fields

import numpy as np
from scipy.optimize import linear_sum_assignment

from .candidates import cache_dir

logger = logging.getLogger(__name__)
MAX_SITES = 600  # estruturas maiores (moléculas grandes) ficam de fora: lentas e fora do escopo


@dataclass
class ScoreSettings:
    shift_range: float = 0.10       # deslocamento de zero máximo (± graus)
    lattice_tol_exp: float = 0.006  # variação isotrópica da rede para estruturas experimentais (±)
    dft_min_scale: float = 0.99     # faixa da escala da rede para estruturas de DFT (Materials Project)
    dft_max_scale: float = 1.03
    w_positions: float = 0.30
    w_reference: float = 0.30
    w_observed: float = 0.25
    w_intensity: float = 0.15
    min_ref_intensity: float = 0.5  # % mínimo para uma reflexão entrar na conta
    detection_sigma: float = 3.0    # reflexão esperada se a altura prevista > este múltiplo do ruído

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (data or {}).items() if k in known})

    def scale_range(self, source):
        if source == "MP":
            return self.dft_min_scale, self.dft_max_scale
        return 1.0 - self.lattice_tol_exp, 1.0 + self.lattice_tol_exp


@dataclass
class ObservedPeaks:
    """Picos observados usados na pontuação (halos ficam de fora)."""

    two_theta: np.ndarray
    height: np.ndarray
    fwhm: np.ndarray
    sigma: np.ndarray
    explainable: np.ndarray     # False para picos marcados como possível Kβ
    noise: float = None
    lo: float = 0.0
    hi: float = 180.0

    def __len__(self):
        return len(self.two_theta)

    @property
    def tolerance(self):
        return np.maximum.reduce([0.35 * self.fwhm, 3.0 * np.nan_to_num(self.sigma, nan=0.0),
                                  np.full(len(self.fwhm), 0.03)])

    @classmethod
    def from_peaks(cls, peaks, two_theta_range=None, noise=None):
        crystal = sorted((p for p in peaks if p.kind == "peak"), key=lambda p: p.two_theta)
        tt = np.array([p.two_theta for p in crystal], dtype=float)
        if two_theta_range is None:
            lo, hi = (float(tt.min()) - 1.0, float(tt.max()) + 1.0) if len(tt) else (0.0, 180.0)
        else:
            lo, hi = map(float, two_theta_range)
        return cls(
            two_theta=tt,
            height=np.array([max(p.height, 1e-12) for p in crystal], dtype=float),
            fwhm=np.array([p.fwhm for p in crystal], dtype=float),
            sigma=np.array([p.two_theta_err for p in crystal], dtype=float),
            explainable=np.array(["kbeta" not in p.flags for p in crystal], dtype=bool),
            noise=noise, lo=lo, hi=hi,
        )


@dataclass
class ReferencePattern:
    two_theta: np.ndarray
    intensity: np.ndarray       # 0-100
    hkl: list = field(default_factory=list)


@dataclass
class MatchResult:
    score: float
    subscores: dict
    shift: float
    lattice_scale: float
    scale_factor: float          # altura observada por unidade de intensidade de referência
    ref_two_theta: np.ndarray    # posições previstas (já com zero e escala), reflexões agrupadas
    ref_intensity: np.ndarray
    ref_hkl: list
    expected: np.ndarray         # bool por reflexão agrupada
    pairs: list                  # (índice da reflexão, índice do pico observado, Δ2θ)
    lines_found: int
    lines_expected: int


def reference_pattern(cif_text, wavelength, two_theta_range, min_intensity=0.5, use_cache=True):
    """Reflexões (2θ, I 0-100, hkl) de uma estrutura no comprimento de onda dado."""
    lo, hi = float(two_theta_range[0]), float(two_theta_range[1])
    key_src = f"{wavelength:.6f}|{lo:.2f}|{hi:.2f}|{min_intensity}|{cif_text}"
    digest = hashlib.sha1(key_src.encode("utf-8", errors="replace")).hexdigest()[:24]
    path = os.path.join(cache_dir("patterns"), f"{digest}.json")
    if use_cache:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            return ReferencePattern(np.array(data["tt"]), np.array(data["i"]), data["hkl"])
        except (OSError, ValueError, KeyError):
            pass
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    from pymatgen.core import Structure

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        structure = Structure.from_str(cif_text, fmt="cif", primitive=True)
    if len(structure) > MAX_SITES:
        raise ValueError(f"estrutura com {len(structure)} sítios (limite {MAX_SITES})")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pattern = XRDCalculator(wavelength=wavelength).get_pattern(
            structure, scaled=True, two_theta_range=(max(0.5, lo - 1.0), min(179.0, hi + 1.0)))
    tt = np.asarray(pattern.x, dtype=float)
    inten = np.asarray(pattern.y, dtype=float)
    hkls = []
    for entry in pattern.hkls:
        try:
            hkls.append(" ".join(str(int(v)) for v in entry[0]["hkl"]))
        except (IndexError, KeyError, TypeError, ValueError):
            hkls.append("")
    keep = inten >= min_intensity
    ref = ReferencePattern(tt[keep], inten[keep], [h for h, k in zip(hkls, keep) if k])
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"tt": ref.two_theta.tolist(), "i": ref.intensity.tolist(), "hkl": ref.hkl}, fh)
    except OSError as exc:
        logger.debug(f"Padrão de referência não gravado no cache: {exc}")
    return ref


def merge_reflections(ref, resolution):
    """Junta reflexões mais próximas que a resolução (soma intensidades, posição ponderada)."""
    if len(ref.two_theta) == 0:
        return ref
    order = np.argsort(ref.two_theta)
    tt, inten = ref.two_theta[order], ref.intensity[order]
    hkl = [ref.hkl[i] if i < len(ref.hkl) else "" for i in order]
    out_tt, out_i, out_h = [], [], []
    start = 0
    for k in range(1, len(tt) + 1):
        if k == len(tt) or tt[k] - tt[k - 1] > resolution:
            w = inten[start:k]
            out_tt.append(float(np.sum(tt[start:k] * w) / np.sum(w)))
            out_i.append(float(np.sum(w)))
            strongest = start + int(np.argmax(w))
            out_h.append(hkl[strongest] + (" +" if k - start > 1 else ""))
            start = k
    return ReferencePattern(np.array(out_tt), np.array(out_i), out_h)


def _predict(two_theta, scale, shift):
    s = np.sin(np.radians(np.asarray(two_theta) / 2.0)) / scale
    return 2.0 * np.degrees(np.arcsin(np.clip(s, -1.0, 1.0))) + shift


def _nearest(sorted_obs, values):
    """Índice do pico observado mais próximo de cada valor."""
    idx = np.searchsorted(sorted_obs, values)
    idx = np.clip(idx, 1, max(1, len(sorted_obs) - 1)) if len(sorted_obs) > 1 else np.zeros_like(idx)
    if len(sorted_obs) == 1:
        return idx
    left = sorted_obs[idx - 1]
    right = sorted_obs[idx]
    return np.where(np.abs(values - left) <= np.abs(values - right), idx - 1, idx)


def align(ref_tt, ref_i, obs, shift_range, scale_range, shift_center=None):
    """Melhor (escala da rede, deslocamento de zero) por busca em grade vetorizada.

    Com shift_center (zero já determinado pelas fases aceitas), o deslocamento só
    varia ±0,02° em torno dele: o zero é do instrumento, comum a todas as fases.
    """
    if len(ref_tt) == 0 or len(obs) == 0:
        return 1.0, 0.0 if shift_center is None else float(shift_center)
    if shift_center is not None:
        shifts = float(shift_center) + np.arange(-0.02, 0.02 + 1e-9, 0.005)
        shift_range = 0.02
    else:
        shifts = np.arange(-shift_range, shift_range + 1e-9, 0.01) if shift_range > 0 else np.array([0.0])
    scales = np.arange(scale_range[0], scale_range[1] + 1e-9, 0.0005)
    if len(scales) == 0:
        scales = np.array([1.0])
    sin_th = np.sin(np.radians(ref_tt / 2.0))
    base = 2.0 * np.degrees(np.arcsin(np.clip(sin_th[None, :] / scales[:, None], -1.0, 1.0)))   # (S, R)
    pred = base[:, None, :] + shifts[None, :, None]                                             # (S, D, R)
    nearest = _nearest(obs.two_theta, pred.ravel())
    dist = np.abs(pred.ravel() - obs.two_theta[nearest]) / obs.tolerance[nearest]
    gain = (ref_i[None, None, :] * np.exp(-dist.reshape(pred.shape) ** 2)).sum(axis=2)          # (S, D)
    span = max(abs(scale_range[0] - 1.0), abs(scale_range[1] - 1.0), 1e-6)
    center = 0.0 if shift_center is None else float(shift_center)
    prior = 0.05 * float(np.sum(ref_i)) * (((scales[:, None] - 1.0) / span) ** 2
                                           + ((shifts[None, :] - center) / max(shift_range, 1e-6)) ** 2)
    k_s, k_d = np.unravel_index(int(np.argmax(gain - prior)), gain.shape)
    return float(scales[k_s]), float(shifts[k_d])


def score_candidate(ref, obs, settings=None, source="COD", residual=None, shift_center=None):
    """Pontua um padrão de referência contra os picos observados.

    Com ``residual`` (altura de cada pico ainda NÃO explicada pelas fases já
    aceitas), a nota "observado" e a concordância de intensidades usam só o que
    sobrou: um candidato que só repete picos já explicados não ganha pontos. As
    posições e as reflexões esperadas continuam contra todos os picos, porque um
    pico compartilhado entre duas fases continua existindo.
    """
    s = settings or ScoreSettings()
    inside = (ref.two_theta >= obs.lo - 2.0) & (ref.two_theta <= obs.hi + 2.0) & (ref.intensity >= s.min_ref_intensity)
    ref_in = ReferencePattern(ref.two_theta[inside], ref.intensity[inside],
                              [h for h, k in zip(ref.hkl, inside) if k] if ref.hkl else [])
    resolution = max(0.03, 0.3 * float(np.median(obs.fwhm))) if len(obs) else 0.05
    merged = merge_reflections(ref_in, resolution)

    strong = merged.intensity >= 2.0
    scale, shift = align(merged.two_theta[strong], merged.intensity[strong], obs, s.shift_range,
                         s.scale_range(source), shift_center)
    pred = _predict(merged.two_theta, scale, shift)
    in_range = (pred >= obs.lo) & (pred <= obs.hi)
    pred, inten = pred[in_range], merged.intensity[in_range]
    hkl = [h for h, k in zip(merged.hkl, in_range) if k] if merged.hkl else []

    empty = MatchResult(0.0, {"positions": 0.0, "reference": 0.0, "observed": 0.0, "intensity": 0.0},
                        shift, scale, 0.0, pred, inten, hkl, np.zeros(len(pred), bool), [], 0, 0)
    if len(pred) == 0 or len(obs) == 0:
        return empty

    tol = obs.tolerance
    delta = pred[:, None] - obs.two_theta[None, :]
    norm = np.abs(delta) / tol[None, :]
    cost = np.where(norm <= 1.0, norm ** 2, 1e6)
    rows, cols = linear_sum_assignment(cost)
    pairs = [(int(r), int(c), float(delta[r, c])) for r, c in zip(rows, cols) if cost[r, c] < 1e6]
    if not pairs:
        return empty

    if residual is not None:
        residual = np.clip(np.asarray(residual, dtype=float), 0.0, None)
        fresh = [(r, c, d) for r, c, d in pairs if residual[c] >= 0.25 * obs.height[c]]
    else:
        fresh = pairs
    target = residual if residual is not None else obs.height
    basis = fresh if fresh else pairs
    ratios = np.array([max(target[c], 1e-12) / inten[r] for r, c, _ in basis])
    k = float(np.median(ratios))
    if obs.noise:
        limit = s.detection_sigma * float(obs.noise)
    else:
        limit = 0.5 * float(np.min(obs.height))
    expected = k * inten >= limit
    matched_ref = np.zeros(len(pred), bool)
    matched_ref[[r for r, _, _ in pairs]] = True

    pos_w = np.array([inten[r] for r, _, _ in pairs])
    pos_q = np.array([math.exp(-(d / tol[c]) ** 2) for _, c, d in pairs])
    positions = float(np.sum(pos_w * pos_q) / np.sum(pos_w))
    exp_total = float(np.sum(inten[expected]))
    reference = float(np.sum(inten[expected & matched_ref]) / exp_total) if exp_total > 0 else 0.0
    explain = obs.explainable
    obs_total = float(np.sum(target[explain]))
    matched_obs = np.zeros(len(obs), bool)
    matched_obs[[c for _, c, _ in pairs]] = True
    observed = float(np.sum(target[explain & matched_obs]) / obs_total) if obs_total > 0 else 0.0
    agree, weights = [], []
    for r, c, _ in (fresh if residual is not None else pairs):
        if expected[r]:
            ratio = max(target[c], 1e-12) / (k * inten[r])
            agree.append(min(ratio, 1.0 / ratio))
            weights.append(inten[r])
    intensity = float(np.average(agree, weights=weights)) if agree else 0.0

    subs = {"positions": positions, "reference": reference, "observed": observed, "intensity": intensity}
    w = {"positions": s.w_positions, "reference": s.w_reference, "observed": s.w_observed, "intensity": s.w_intensity}
    total_w = sum(w.values()) or 1.0
    log_mean = sum(w[key] * math.log(max(subs[key], 0.02)) for key in subs) / total_w
    n_expected = int(np.sum(expected))
    confidence = min(1.0, math.sqrt(n_expected / 3.0)) if n_expected else 0.0
    score = 100.0 * confidence * math.exp(log_mean)
    return MatchResult(score, subs, shift, scale, k, pred, inten, hkl, expected, pairs,
                       int(np.sum(expected & matched_ref)), n_expected)
