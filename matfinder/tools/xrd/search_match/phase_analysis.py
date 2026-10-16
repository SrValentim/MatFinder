# -*- coding: utf-8 -*-
"""Fases aceitas e reavaliação dos candidatos (search-match, fase 3).

Fluxo no estilo do HighScore: o usuário aceita um candidato; as escalas de todas
as fases aceitas são ajustadas juntas às alturas dos picos; o que cada pico ainda
tem de altura não explicada vira o "resíduo"; os demais candidatos são pontuados
de novo contra esse resíduo, com o zero do instrumento fixado pelas fases aceitas.
"""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.optimize import nnls

from .candidates import Candidate, _same_phase
from .scoring import score_candidate

logger = logging.getLogger(__name__)

PHASE_COLORS = ["#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#ff7f0e", "#7f7f7f"]
SCORE_MODES = ("auto", "peaks", "profile", "both")
PROFILE_TOP = 60  # o score de perfil é calculado para os melhores candidatos por picos


@dataclass
class AcceptedPhase:
    candidate: Candidate
    color: str
    scale: float = 0.0              # altura por unidade de intensidade de referência
    rir: dict = None                # {"rir", "inrange_fraction"}
    weight_fraction: float = None
    peaks_explained: int = 0
    shift_hint: float = None        # zero salvo no projeto (centro do alinhamento ao reabrir)

    def to_dict(self):
        c = self.candidate
        return {
            "source": c.source, "source_id": c.source_id, "formula": c.formula, "spacegroup": c.spacegroup,
            "sg_number": c.sg_number, "elements": list(c.elements), "cell": list(c.cell), "mineral": c.mineral,
            "cif": c.cif, "color": self.color, "score": float(c.score), "scale": float(self.scale),
            "rir": self.rir, "weight_fraction": self.weight_fraction,
            "shift": float(c.match.shift) if c.match is not None else self.shift_hint,
        }

    @classmethod
    def from_dict(cls, data):
        cand = Candidate(source=data["source"], source_id=data["source_id"], formula=data.get("formula", "?"),
                         elements=tuple(data.get("elements", [])), spacegroup=data.get("spacegroup", ""),
                         sg_number=int(data.get("sg_number") or 0), cell=tuple(data.get("cell", [])),
                         mineral=data.get("mineral", ""), cif=data.get("cif"), score=float(data.get("score", 0.0)))
        return cls(candidate=cand, color=data.get("color", PHASE_COLORS[0]), scale=float(data.get("scale", 0.0)),
                   rir=data.get("rir"), weight_fraction=data.get("weight_fraction"), shift_hint=data.get("shift"))


@dataclass
class IdentificationState:
    """Situação dos picos observados frente às fases aceitas."""

    explained: np.ndarray            # altura explicada de cada pico
    residual: np.ndarray             # altura ainda sem fase
    dominant: np.ndarray             # índice da fase que mais explica cada pico (-1 = nenhuma)
    unexplained: np.ndarray          # bool: pico (explicável) com mais da metade sem fase
    global_shift: float = None
    explained_fraction: float = 0.0  # fração da intensidade observada explicada pelo conjunto
    profile_base: np.ndarray = None  # soma dos perfis ajustados das fases aceitas (score de perfil)
    profile_explained: float = None  # fração do difratograma sem fundo explicada pelas fases aceitas


def next_color(accepted):
    used = {p.color for p in accepted}
    return next((c for c in PHASE_COLORS if c not in used), PHASE_COLORS[len(accepted) % len(PHASE_COLORS)])


def analyze(obs, accepted, profile_ctx=None):
    """Ajusta juntas as escalas das fases aceitas e calcula resíduo e atribuições."""
    n = len(obs)
    if not accepted or n == 0:
        return IdentificationState(np.zeros(n), obs.height.copy(), np.full(n, -1), obs.explainable.copy(), None,
                                   0.0, None)
    M = np.zeros((n, len(accepted)))
    for a, phase in enumerate(accepted):
        match = phase.candidate.match
        if match is None:
            continue
        for r, c, _ in match.pairs:
            M[c, a] += match.ref_intensity[r]
    scales, _ = nnls(M, obs.height) if M.any() else (np.zeros(len(accepted)), 0.0)
    contrib = M * scales[None, :]
    explained = contrib.sum(axis=1)
    dominant = np.where(explained > 0, np.argmax(contrib, axis=1), -1)
    residual = np.clip(obs.height - explained, 0.0, None)
    unexplained = obs.explainable & (residual > 0.5 * obs.height)
    for a, phase in enumerate(accepted):
        phase.scale = float(scales[a])
        phase.peaks_explained = int(np.sum(dominant == a))
    weights = np.array([max(p.scale, 0.0) * (1 + p.peaks_explained) for p in accepted])
    shifts = np.array([p.candidate.match.shift if p.candidate.match else 0.0 for p in accepted])
    global_shift = float(np.average(shifts, weights=weights)) if weights.sum() > 0 else float(np.mean(shifts))
    total = float(np.sum(obs.height[obs.explainable]))
    fraction = float(np.sum(np.minimum(explained, obs.height)[obs.explainable]) / total) if total > 0 else 0.0

    base = prof_explained = None
    if profile_ctx is not None:
        from .quantify import fit_profiles, phase_profile
        profiles = [phase_profile(profile_ctx, p.candidate.match.ref_two_theta, p.candidate.match.ref_intensity)
                    for p in accepted if p.candidate.match is not None]
        if profiles:
            prof_scales, prof_explained, _ = fit_profiles(profile_ctx, profiles)
            base = sum(s * prof for s, prof in zip(prof_scales, profiles))
    return IdentificationState(explained, residual, dominant, unexplained, global_shift, fraction, base,
                               prof_explained)


def peak_list_is_poor(obs):
    """Lista de picos pobre (poucos picos ou picos muito largos): o score de perfil ajuda."""
    return len(obs) < 8 or float(np.median(obs.fwhm)) > 0.35


def effective_mode(mode, obs, profile_ctx):
    if profile_ctx is None:
        return "peaks"
    if mode == "auto":
        return "both" if peak_list_is_poor(obs) else "peaks"
    return mode if mode in SCORE_MODES else "peaks"


def combine(peak_score, profile_explained, mode):
    if mode == "profile":
        return 100.0 * profile_explained
    if mode == "both":
        return float(np.sqrt(max(peak_score, 0.0) * 100.0 * max(profile_explained, 0.0)))
    return peak_score


def rescore(candidates, obs, accepted, settings, state=None, profile_ctx=None, mode="auto", cancel=None):
    """Pontua de novo os candidatos (exceto os aceitos e duplicatas deles) contra o resíduo.

    Cada candidato precisa ter ``reference`` (padrão de referência já simulado).

    Returns:
        (candidatos ordenados pelo score, modo efetivo usado)
    """
    state = state or analyze(obs, accepted, profile_ctx)
    accepted_keys = {p.candidate.key for p in accepted}
    use = effective_mode(mode, obs, profile_ctx)
    out = []
    for cand in candidates:
        if cancel and cancel():
            break
        if cand.key in accepted_keys or any(_same_phase(p.candidate, cand) for p in accepted):
            continue
        ref = getattr(cand, "reference", None)
        if ref is None:
            continue
        match = score_candidate(ref, obs, settings, cand.source,
                                residual=state.residual if accepted else None,
                                shift_center=state.global_shift if accepted else None)
        cand.match = match
        cand.peak_score = match.score
        cand.subscores = dict(match.subscores)
        cand.profile_explained = None
        cand.score = match.score
        out.append(cand)
    out.sort(key=lambda c: -c.score)
    if use != "peaks":
        from .quantify import profile_score
        for cand in out[:PROFILE_TOP]:
            explained, _ = profile_score(profile_ctx, cand.match, base=state.profile_base)
            cand.profile_explained = explained
            cand.score = combine(cand.peak_score, explained, use)
        tail = out[PROFILE_TOP:]
        for cand in tail:
            cand.score = combine(cand.peak_score, 0.0, use) if use == "profile" else cand.score * 0.5
        out.sort(key=lambda c: -c.score)
    return out, use


def quantify_accepted(accepted, wavelength, two_theta_range, obs):
    """RIR (calculado da estrutura) e frações em massa semiquantitativas das fases aceitas."""
    from .quantify import rir_of, semi_quant
    for phase in accepted:
        cand = phase.candidate
        if phase.rir is None and cand.cif:
            try:
                phase.rir = rir_of(cand.cif, wavelength, two_theta_range)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"RIR não calculado para {cand.label}: {exc}")
    fractions = semi_quant([p.scale for p in accepted], [p.rir for p in accepted])
    for phase, frac in zip(accepted, fractions):
        phase.weight_fraction = frac
    return accepted
