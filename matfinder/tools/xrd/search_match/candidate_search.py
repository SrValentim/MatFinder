# -*- coding: utf-8 -*-
"""Busca de candidatos de fase (search-match, fase 2): consulta, simulação e pontuação."""

import logging
import time
from dataclasses import dataclass, field, fields

from .candidates import (
    ElementFilter, SearchCancelled, describe_error, fetch_cod_cifs, find_mp_api_key, group_duplicates,
    search_cod, search_mp,
)
from .scoring import ObservedPeaks, ScoreSettings, reference_pattern, score_candidate

logger = logging.getLogger(__name__)


@dataclass
class CandidateSearchSettings:
    use_cod: bool = True
    use_mp: bool = True
    mp_only_experimental: bool = True
    mp_max_e_above_hull: float = 0.2
    max_candidates: int = 300
    group_duplicates: bool = True
    score: ScoreSettings = field(default_factory=ScoreSettings)

    def to_dict(self):
        out = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "score"}
        out["score"] = self.score.to_dict()
        return out

    @classmethod
    def from_dict(cls, data):
        data = dict(data or {})
        score = ScoreSettings.from_dict(data.pop("score", None))
        known = {f.name for f in fields(cls)} - {"score"}
        return cls(score=score, **{k: v for k, v in data.items() if k in known})


@dataclass
class CandidateSearchResult:
    candidates: list            # representantes, do maior score para o menor
    all_candidates: list        # todos os candidatos pontuados
    errors: dict                # fonte -> mensagem de erro
    info: dict


def _prioritize(candidates, limit):
    """Se houver candidatos demais, fica com os mais prováveis (menos elementos, experimentais)."""
    if len(candidates) <= limit:
        return candidates, False
    ranked = sorted(candidates, key=lambda c: (len(c.elements), c.source == "MP" and bool(c.theoretical),
                                               c.source != "COD"))
    return ranked[:limit], True


def find_candidates(peaks, element_filter, wavelength, two_theta_range, settings=None, noise=None,
                    mp_api_key=None, progress=None, cancel=None, cod_session=None, mp_rester_factory=None):
    """Busca, simula e pontua candidatos para uma lista de picos.

    Args:
        peaks: picos observados (Peak da fase 1).
        element_filter: ElementFilter.
        wavelength: comprimento de onda (Kα1) em Å.
        two_theta_range: (mín, máx) de 2θ medidos.
        noise: ruído típico dos dados (limite de detecção das reflexões esperadas).

    Raises:
        ValueError: filtro inválido ou picos insuficientes.
        SearchCancelled: cancelado pelo usuário.
    """
    t0 = time.perf_counter()
    s = settings or CandidateSearchSettings()
    flt = element_filter if isinstance(element_filter, ElementFilter) else ElementFilter.from_dict(element_filter)
    problem = flt.validate()
    if problem:
        raise ValueError(problem)
    obs = ObservedPeaks.from_peaks(peaks, two_theta_range, noise)
    if len(obs) < 2:
        raise ValueError("São necessários pelo menos 2 picos cristalinos. Busque os picos antes.")
    if not wavelength:
        raise ValueError("Comprimento de onda inválido.")

    def report(fraction, stage):
        if progress:
            progress(fraction, stage)
        if cancel and cancel():
            raise SearchCancelled()

    errors, found = {}, []
    if s.use_cod:
        report(0.02, "consultando o COD")
        try:
            found += search_cod(flt, cancel=cancel, session=cod_session)
        except SearchCancelled:
            raise
        except Exception as exc:  # noqa: BLE001 - a outra fonte ainda pode responder
            logger.warning(f"Falha na consulta ao COD: {exc}")
            errors["COD"] = describe_error(exc)
    if s.use_mp:
        report(0.12, "consultando o Materials Project")
        key = mp_api_key or find_mp_api_key()
        if not key and mp_rester_factory is None:
            errors["MP"] = "Chave da API do Materials Project não configurada."
        else:
            try:
                found += search_mp(flt, key, s.mp_only_experimental, s.mp_max_e_above_hull,
                                   cancel=cancel, rester_factory=mp_rester_factory)
            except SearchCancelled:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Falha na consulta ao Materials Project: {exc}")
                errors["MP"] = describe_error(exc)

    candidates, truncated = _prioritize(found, s.max_candidates)
    report(0.25, "baixando estruturas")
    fetch_cod_cifs(candidates, progress=lambda f: report(0.25 + 0.3 * f, "baixando estruturas"),
                   cancel=cancel, session=cod_session)

    scored = []
    total = max(1, len(candidates))
    for i, cand in enumerate(candidates):
        report(0.55 + 0.43 * i / total, "simulando e pontuando")
        if not cand.cif:
            cand.error = cand.error or "sem CIF"
            continue
        try:
            ref = reference_pattern(cand.cif, wavelength, (obs.lo, obs.hi), s.score.min_ref_intensity)
            match = score_candidate(ref, obs, s.score, cand.source)
        except SearchCancelled:
            raise
        except Exception as exc:  # noqa: BLE001 - CIF problemático: o candidato fica de fora
            cand.error = describe_error(exc)
            continue
        cand.match = match
        cand.score = match.score
        cand.subscores = dict(match.subscores)
        scored.append(cand)

    scored.sort(key=lambda c: -c.score)
    representatives = group_duplicates(scored) if s.group_duplicates else list(scored)
    report(1.0, "concluído")
    info = {
        "n_found": len(found), "n_scored": len(scored), "n_groups": len(representatives),
        "truncated": truncated, "by_source": {src: sum(1 for c in scored if c.source == src) for src in ("COD", "MP")},
        "failed": sum(1 for c in candidates if c.error), "elapsed_s": time.perf_counter() - t0,
        "filter": flt.to_dict(), "settings": s.to_dict(),
    }
    return CandidateSearchResult(representatives, scored, errors, info)
