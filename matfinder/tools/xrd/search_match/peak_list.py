# -*- coding: utf-8 -*-
"""Lista de picos editável do PhaseDRX (modelo de dados, sem interface).

A lista guarda os picos de UM difratograma, separados dos dados: apagar um pico
nunca altera a curva medida. Picos detectados automaticamente têm origem
"auto"; os adicionados pelo usuário, "manual". Ao repetir a detecção:

- os picos manuais são mantidos;
- picos automáticos que o usuário apagou continuam apagados (posições
  "suprimidas"), até que ele peça para restaurá-los.

Tudo é serializável em JSON (``to_dict``/``from_dict``) para entrar no arquivo
de projeto e no histórico de desfazer/refazer do PhaseDRX.
"""

import csv
import hashlib
import math
import uuid
from dataclasses import dataclass, field, fields

import numpy as np

from .profiles import pv_area

KINDS = ("peak", "halo")
ORIGINS = ("auto", "manual")
_NAN = float("nan")


def _num(value):
    """Converte para float JSON-seguro: NaN/inf/None viram None."""
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _from_num(value):
    return _NAN if value is None else float(value)


def data_signature(two_theta, intensity):
    """Impressão digital dos dados, para saber se mudaram depois da detecção."""
    x = np.ascontiguousarray(np.asarray(two_theta, dtype=np.float32))
    y = np.ascontiguousarray(np.asarray(intensity, dtype=np.float32))
    digest = hashlib.sha1()
    digest.update(str(len(x)).encode())
    digest.update(x.tobytes())
    digest.update(y.tobytes())
    return digest.hexdigest()[:16]


@dataclass
class Peak:
    """Um pico (ou halo amorfo) ajustado por pseudo-Voigt."""

    two_theta: float
    height: float
    fwhm: float
    eta: float = 0.5
    asymmetry: float = 0.0
    area: float = _NAN
    background: float = 0.0
    two_theta_err: float = _NAN
    height_err: float = _NAN
    fwhm_err: float = _NAN
    area_err: float = _NAN
    significance: float = _NAN
    kind: str = "peak"
    origin: str = "auto"
    ka2: bool = False
    flags: list = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"Tipo de pico inválido: {self.kind!r}")
        if self.origin not in ORIGINS:
            raise ValueError(f"Origem de pico inválida: {self.origin!r}")
        if not math.isfinite(self.area):
            self.area = float(pv_area(self.height, self.fwhm, self.eta))
        self.flags = list(self.flags)

    def to_dict(self):
        out = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name in ("kind", "origin", "id"):
                out[f.name] = str(value)
            elif f.name == "ka2":
                out[f.name] = bool(value)
            elif f.name == "flags":
                out[f.name] = [str(v) for v in value]
            else:
                out[f.name] = _num(value)
        return out

    @classmethod
    def from_dict(cls, data):
        known = {f.name: f for f in fields(cls)}
        kwargs = {}
        for name, value in data.items():
            if name not in known:
                continue
            if name in ("kind", "origin", "id"):
                kwargs[name] = str(value)
            elif name == "ka2":
                kwargs[name] = bool(value)
            elif name == "flags":
                kwargs[name] = list(value or [])
            else:
                kwargs[name] = _from_num(value)
        return cls(**kwargs)


class PeakList:
    """Picos de um difratograma, com picos apagados lembrados e metadados da busca."""

    VERSION = 1

    def __init__(self, peaks=None, wavelength=None, settings=None, suppressed=None,
                 data_signature=None, noise_level=None, crystallinity=None):
        self.peaks = sorted(list(peaks or []), key=lambda p: p.two_theta)
        self.wavelength = wavelength          # Å usado para d (Kα1 ou personalizado)
        self.settings = dict(settings or {})  # parâmetros da última busca
        self.suppressed = [tuple(s) for s in (suppressed or [])]  # (2θ, tolerância)
        self.data_signature = data_signature
        self.noise_level = noise_level
        self.crystallinity = crystallinity

    # --- acesso -----------------------------------------------------------
    def __len__(self):
        return len(self.peaks)

    def __iter__(self):
        return iter(self.peaks)

    def get(self, peak_id):
        return next((p for p in self.peaks if p.id == peak_id), None)

    def counts(self):
        """(número de picos cristalinos, número de halos)."""
        halos = sum(1 for p in self.peaks if p.kind == "halo")
        return len(self.peaks) - halos, halos

    # --- edição -----------------------------------------------------------
    def add(self, peak):
        """Adiciona um pico. Se cair numa posição suprimida, a supressão é desfeita."""
        self.suppressed = [s for s in self.suppressed if abs(s[0] - peak.two_theta) > s[1]]
        self.peaks.append(peak)
        self.peaks.sort(key=lambda p: p.two_theta)
        return peak

    def remove(self, peak_ids):
        """Remove picos pelo id. Picos automáticos removidos ficam suprimidos."""
        ids = set(peak_ids)
        removed = [p for p in self.peaks if p.id in ids]
        self.peaks = [p for p in self.peaks if p.id not in ids]
        for p in removed:
            if p.origin == "auto":
                self.suppressed.append((p.two_theta, max(0.5 * p.fwhm, 0.01)))
        return removed

    def nearest(self, two_theta, max_distance=None):
        """Pico mais próximo de 2θ (ou None se estiver além de max_distance)."""
        if not self.peaks:
            return None
        best = min(self.peaks, key=lambda p: abs(p.two_theta - two_theta))
        if max_distance is not None and abs(best.two_theta - two_theta) > max_distance:
            return None
        return best

    def replace_auto(self, new_peaks):
        """Troca os picos automáticos pelos de uma nova busca, mantendo os manuais.

        Novos picos que caem numa posição suprimida, ou em cima de um pico manual,
        são descartados.
        """
        manual = [p for p in self.peaks if p.origin == "manual"]
        accepted = []
        for p in new_peaks:
            if any(abs(p.two_theta - s[0]) <= s[1] for s in self.suppressed):
                continue
            if any(abs(p.two_theta - m.two_theta) <= 0.5 * max(p.fwhm, m.fwhm) for m in manual):
                continue
            accepted.append(p)
        self.peaks = sorted(manual + accepted, key=lambda q: q.two_theta)
        return accepted

    def restore_suppressed(self):
        count = len(self.suppressed)
        self.suppressed = []
        return count

    # --- grandezas derivadas -----------------------------------------------
    def d_spacing(self, peak):
        """(d, erro de d) em Å pela lei de Bragg, ou (None, None) sem comprimento de onda."""
        if not self.wavelength or not math.isfinite(peak.two_theta) or peak.two_theta <= 0:
            return None, None
        theta = math.radians(peak.two_theta / 2.0)
        d = self.wavelength / (2.0 * math.sin(theta))
        if math.isfinite(peak.two_theta_err):
            d_err = d * abs(1.0 / math.tan(theta)) * math.radians(peak.two_theta_err / 2.0)
        else:
            d_err = None
        return d, d_err

    def relative_intensities(self):
        """Altura relativa (%) de cada pico cristalino, pelo maior deles."""
        crystalline = [p for p in self.peaks if p.kind == "peak"]
        top = max((p.height for p in crystalline), default=0.0)
        return {p.id: (100.0 * p.height / top if top > 0 else 0.0) for p in crystalline}

    def rows(self):
        """Linhas (dicionários) para tabela e CSV, em ordem de 2θ."""
        rel = self.relative_intensities()
        out = []
        for p in self.peaks:
            d, d_err = self.d_spacing(p)
            out.append({
                "id": p.id,
                "two_theta": p.two_theta,
                "two_theta_err": p.two_theta_err,
                "d": d,
                "d_err": d_err,
                "rel_intensity": rel.get(p.id),
                "height": p.height,
                "area": p.area,
                "fwhm": p.fwhm,
                "eta": p.eta,
                "significance": p.significance,
                "kind": p.kind,
                "origin": p.origin,
                "flags": ",".join(p.flags),
            })
        return out

    def write_csv(self, path):
        """Exporta a lista em CSV (vírgula como separador, ponto decimal)."""
        columns = ["two_theta_deg", "two_theta_err_deg", "d_A", "d_err_A", "rel_intensity_pct",
                   "height", "area", "fwhm_deg", "eta", "significance", "kind", "origin", "flags"]
        keys = ["two_theta", "two_theta_err", "d", "d_err", "rel_intensity", "height", "area",
                "fwhm", "eta", "significance", "kind", "origin", "flags"]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(columns)
            for row in self.rows():
                values = []
                for key in keys:
                    value = row[key]
                    if isinstance(value, float):
                        values.append("" if not math.isfinite(value) else f"{value:.6g}")
                    elif value is None:
                        values.append("")
                    else:
                        values.append(value)
                writer.writerow(values)

    # --- serialização --------------------------------------------------------
    def to_dict(self):
        return {
            "version": self.VERSION,
            "peaks": [p.to_dict() for p in self.peaks],
            "wavelength": _num(self.wavelength),
            "settings": dict(self.settings),
            "suppressed": [[_num(a), _num(b)] for a, b in self.suppressed],
            "data_signature": self.data_signature,
            "noise_level": _num(self.noise_level),
            "crystallinity": _num(self.crystallinity),
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls()
        return cls(
            peaks=[Peak.from_dict(p) for p in data.get("peaks", [])],
            wavelength=data.get("wavelength"),
            settings=data.get("settings") or {},
            suppressed=[(float(a), float(b)) for a, b in data.get("suppressed", [])
                        if a is not None and b is not None],
            data_signature=data.get("data_signature"),
            noise_level=data.get("noise_level"),
            crystallinity=data.get("crystallinity"),
        )
