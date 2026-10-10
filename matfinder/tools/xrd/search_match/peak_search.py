# -*- coding: utf-8 -*-
"""Busca robusta de picos em difratogramas de pó (fase 1 do search-match do PhaseDRX).

Etapas:

1. Limpeza: ordena 2θ, descarta NaN, reamostra passo irregular e troca spikes de
   um ponto pela mediana local.
2. Ruído: σ(2θ) por estatística de Poisson quando os dados são contagens; senão,
   um modelo empírico σ² = a + b·I estimado pela segunda diferença.
3. Detecção multiescala: Laplaciano da gaussiana normalizado (a "segunda
   derivada suavizada" em várias larguras). O ruído de cada escala é calibrado
   empiricamente LONGE dos picos (funciona em dados suavizados e em padrões
   densos). Máximos que persistem entre escalas formam cristas; cada crista
   significativa vira um candidato com posição, largura e significância.
4. Fundo: SNIP sobre os dados suavizados, bordas extrapoladas por retas robustas
   e deslocamento residual corrigido nas regiões sem picos.
5. Ajuste em duas passadas: a primeira aprende a tendência da largura com 2θ
   (Caglioti) a partir dos picos isolados; a segunda ajusta cada grupo de picos
   sobrepostos por pseudo-Voigt assimétrica (com dubleto Kα2 opcional) usando
   essa tendência como restrição suave, com seleção de modelo (BIC) para ombros
   escondidos e poda de componentes não significativos.
6. Classificação: componentes muito largos viram halo amorfo; o índice de
   cristalinidade é a fração da área em picos cristalinos.
"""

import logging
import math
import time
from dataclasses import asdict, dataclass, field, fields

import numpy as np
from scipy import ndimage, signal
from scipy.optimize import least_squares, nnls

from matfinder.tools.xrd.emission_lines import same_d_two_theta
from .peak_list import Peak
from .profiles import GAUSS_AREA, LN2, LORENTZ_AREA, area_factor, pv_shape

logger = logging.getLogger(__name__)

# Para uma gaussiana de desvio s0, o LoG normalizado (σ²·∇²) tem resposta máxima
# na escala σ* = √2·s0, com valor 2/(3√3) ≈ 0,385 da altura. Logo FWHM ≈ 1,665·σ*.
FWHM_PER_SCALE = 2.0 * math.sqrt(2.0 * math.log(2.0)) / math.sqrt(2.0)
LOG_PEAK_RESPONSE = 2.0 / (3.0 * math.sqrt(3.0))


class SearchCancelled(Exception):
    """A busca foi cancelada pelo usuário."""


@dataclass
class PeakSearchSettings:
    """Parâmetros da busca. Os valores padrão servem para a maioria dos dados de laboratório."""

    sensitivity: float = 4.0        # limiar de detecção, em desvios-padrão do ruído
    min_fwhm: float = 0.02          # menor FWHM aceita (graus)
    max_fwhm: float = 2.0           # maior FWHM de pico cristalino (graus)
    broad_mode: bool = False        # picos largos / material amorfo
    broad_max_fwhm: float = 15.0    # maior FWHM no modo largo (graus)
    halo_min_fwhm: float = 2.0      # a partir desta FWHM o componente é halo amorfo
    background_window: float = 0.0  # meia-janela do SNIP (graus); 0 = automática
    min_ridge_scales: int = 3       # persistência mínima da crista entre escalas
    ka2: bool = True                # modelar o dubleto Kα1 + Kα2
    ka2_ratio: float = 0.5          # intensidade de Kα2 relativa a Kα1
    fit_profiles: bool = True       # refinar por ajuste de perfil
    width_prior: bool = True        # usar a tendência de largura (Caglioti) no ajuste
    width_tolerance: float = 0.35   # desvio típico aceito da tendência (fração, em log)
    remove_spikes: bool = True
    max_extra_components: int = 3   # ombros adicionados por grupo
    flag_kbeta: bool = True         # marcar picos que podem ser Kβ de outro pico

    def effective_max_fwhm(self):
        return self.broad_max_fwhm if self.broad_mode else self.max_fwhm

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (data or {}).items() if k in known})


PRESETS = {
    "standard": PeakSearchSettings(),
    "noisy": PeakSearchSettings(sensitivity=3.0, min_ridge_scales=4),
    "broad": PeakSearchSettings(broad_mode=True),
}


@dataclass
class PeakSearchResult:
    peaks: list
    two_theta: np.ndarray
    intensity: np.ndarray
    background: np.ndarray
    model: np.ndarray
    noise: np.ndarray
    crystallinity: float = None
    info: dict = field(default_factory=dict)


# =============================================================================
# Preparação dos dados
# =============================================================================

def prepare_data(two_theta, intensity):
    """Ordena, remove NaN/duplicatas e, se o passo for irregular, reamostra.

    Returns:
        (x, y, step, resampled)
    """
    x = np.asarray(two_theta, dtype=float).ravel()
    y = np.asarray(intensity, dtype=float).ravel()
    n = min(len(x), len(y))
    x, y = x[:n], y[:n]
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 2:
        return x, y, 0.0, False
    order = np.argsort(x, kind="stable")
    x, y = x[order], y[order]
    if np.any(np.diff(x) <= 0):
        ux, inverse = np.unique(x, return_inverse=True)
        y = np.bincount(inverse, weights=y) / np.bincount(inverse)
        x = ux
    steps = np.diff(x)
    step = float(np.median(steps))
    resampled = False
    if step > 0 and np.max(np.abs(steps - step)) > 0.05 * step:
        grid = np.arange(x[0], x[-1] + 0.5 * step, step)
        y = np.interp(grid, x, y)
        x = grid
        resampled = True
    return x, y, step, resampled


def _looks_like_counts(y):
    if len(y) == 0 or np.min(y) < 0 or np.max(y) < 20:
        return False
    return np.mean(np.abs(y - np.round(y)) < 1e-6) > 0.98


def estimate_noise(y, counts=None):
    """Desvio-padrão do ruído em cada ponto.

    Usa Poisson (σ = √I) quando os dados parecem contagens brutas e o ruído
    observado confirma isso; caso contrário, ajusta σ² = a + b·I aos desvios da
    segunda diferença, agrupados por nível de intensidade.

    Returns:
        (sigma, is_poisson)
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    level = ndimage.uniform_filter1d(y, size=7, mode="nearest")
    d2 = np.empty(n)
    d2[1:-1] = (y[:-2] - 2.0 * y[1:-1] + y[2:]) / math.sqrt(6.0)
    d2[0], d2[-1] = d2[1], d2[-2]

    order = np.argsort(level)
    n_bins = int(np.clip(n // 150, 3, 25))
    groups = np.array_split(order, n_bins)
    lv = np.array([np.median(level[g]) for g in groups])
    sd = np.array([1.4826 * np.median(np.abs(d2[g] - np.median(d2[g]))) for g in groups])
    k = max(2, int(round(0.6 * n_bins)))  # grupos dominados pelo fundo

    if counts is None:
        counts = _looks_like_counts(y)
    if counts:
        ratio = np.median(sd[:k] / np.sqrt(np.maximum(lv[:k], 1.0)))
        if 0.6 <= ratio <= 1.7:
            return np.sqrt(np.maximum(level, 1.0)), True

    base = lv[0]
    design = np.column_stack([np.ones(k), np.maximum(lv[:k] - base, 0.0)])
    coef, _ = nnls(design, sd[:k] ** 2)
    var = coef[0] + coef[1] * np.maximum(level - base, 0.0)
    scale = max(np.max(np.abs(y)), 1e-300)
    floor = max(0.25 * float(np.median(sd[:k])) ** 2, (1e-9 * scale) ** 2)
    return np.sqrt(np.maximum(var, floor)), False


def remove_spikes(y, sigma, threshold=6.0):
    """Troca spikes de um ponto (raios cósmicos, falhas do detector) pela mediana local.

    Um pico físico ocupa vários pontos; um spike sobe sozinho, com os vizinhos
    no nível da mediana.

    Returns:
        (y_limpo, número_de_spikes)
    """
    y = np.asarray(y, dtype=float)
    if len(y) < 7:
        return y.copy(), 0
    med = ndimage.median_filter(y, size=5, mode="nearest")
    excess = (y - med) / sigma
    left = np.r_[0.0, (y[:-1] - med[1:]) / sigma[1:]]
    right = np.r_[(y[1:] - med[:-1]) / sigma[:-1], 0.0]
    spikes = (excess > threshold) & (left < threshold / 3.0) & (right < threshold / 3.0)
    spikes[[0, -1]] = False
    out = y.copy()
    out[spikes] = med[spikes]
    return out, int(spikes.sum())


# =============================================================================
# Fundo
# =============================================================================

def _edge_line(v, idx):
    """Reta robusta (assimétrica) sob os pontos v[idx]: ignora picos acima dela."""
    t = idx.astype(float)
    vals = v[idx]
    mask = np.ones(len(idx), dtype=bool)
    coef = np.polyfit(t, vals, 1)
    for _ in range(10):
        coef = np.polyfit(t[mask], vals[mask], 1)
        res = vals - np.polyval(coef, t)
        spread = 1.4826 * np.median(np.abs(res[mask] - np.median(res[mask]))) + 1e-12
        new_mask = res < 2.0 * spread
        if new_mask.sum() < 5 or np.array_equal(new_mask, mask):
            break
        mask = new_mask
    return coef


def snip_background(y, half_window, lls=True, smooth=True):
    """Fundo por SNIP (Ryan et al., 1988) com meia-janela em pontos.

    As bordas são estendidas por retas robustas antes do recorte, para que o
    algoritmo não iguale o fundo aos dados (e apague picos) perto das bordas.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    m = int(max(1, min(half_window, 4 * n)))
    offset = min(0.0, float(np.min(y)))
    yy = y - offset
    scale = 1.0
    if lls:
        top = float(np.max(yy))
        if 0 < top < 1e3:
            scale = 1e3 / top  # a transformação LLS espera magnitudes de contagem
        v = np.log(np.log(np.sqrt(yy * scale + 1.0) + 1.0) + 1.0)
    else:
        v = yy.copy()

    edge = int(min(max(3 * m, 30), max(5, n // 3)))  # trecho longo: um pico na borda não puxa a reta
    left_coef = _edge_line(v, np.arange(edge))
    right_coef = _edge_line(v, np.arange(n - edge, n))
    pad_left = np.polyval(left_coef, np.arange(-m, 0, dtype=float))
    pad_right = np.polyval(right_coef, np.arange(n, n + m, dtype=float))
    p = np.concatenate([pad_left, v, pad_right])
    for i in range(1, m + 1):
        np.minimum(p[i:-i], 0.5 * (p[:-2 * i] + p[2 * i:]), out=p[i:-i])
    bg_v = p[m:m + n]
    if smooth and m >= 8:
        bg_v = ndimage.gaussian_filter1d(bg_v, sigma=m / 8.0, mode="nearest")

    if lls:
        bg = (np.exp(np.exp(bg_v) - 1.0) - 1.0) ** 2 - 1.0
        bg = bg / scale
    else:
        bg = bg_v
    return bg + offset


def estimate_background(y, half_window, smooth_sigma=0.0, peak_mask=None):
    """Fundo robusto para dados ruidosos.

    O SNIP recorta em direção aos mínimos: com ruído alto ele fica alguns σ
    abaixo da linha de base real. Por isso (1) o SNIP roda sobre os dados
    suavizados e (2) o deslocamento que sobra é medido nas regiões sem picos
    (mediana móvel de dados - fundo) e somado ao fundo.

    Args:
        half_window: meia-janela do SNIP em pontos.
        smooth_sigma: suavização gaussiana (pontos) aplicada antes do SNIP.
        peak_mask: True nos pontos ocupados por picos (fora da correção).
    """
    y = np.asarray(y, dtype=float)
    ys = ndimage.gaussian_filter1d(y, smooth_sigma, mode="nearest") if smooth_sigma > 0 else y
    bg = snip_background(ys, half_window)
    if peak_mask is None:
        return bg
    free = np.nonzero(~np.asarray(peak_mask, dtype=bool))[0]
    if len(free) < max(20, len(y) // 10):
        return bg
    resid = y[free] - bg[free]
    size = int(min(len(free), max(11, 2 * int(half_window))))
    size -= 1 - size % 2  # tamanho ímpar
    med = ndimage.median_filter(resid, size=max(3, size), mode="nearest")
    corr = np.interp(np.arange(len(y)), free, med)
    corr = ndimage.gaussian_filter1d(corr, max(1.0, half_window / 2.0), mode="nearest")
    return bg + corr


# =============================================================================
# Detecção multiescala (cristas do LoG normalizado)
# =============================================================================

def _robust_scale(z, clip=3.5, iterations=5):
    v = z[np.isfinite(z)]
    if v.size == 0:
        return 1.0
    for _ in range(iterations):
        med = np.median(v)
        mad = 1.4826 * np.median(np.abs(v - med))
        if mad <= 0:
            break
        keep = np.abs(v - med) < clip * mad
        if keep.all() or keep.sum() < 10:
            break
        v = v[keep]
    s = 1.4826 * np.median(np.abs(v - np.median(v)))
    return float(np.clip(s, 0.5, 50.0)) if s > 0 else 1.0


def _scales(step, n, min_fwhm, max_fwhm, ratio=1.2):
    s_min = max(0.7, min_fwhm / FWHM_PER_SCALE / step)
    s_max = max(2.0 * s_min, max_fwhm / FWHM_PER_SCALE / step)
    s_max = min(s_max, max(2.0 * s_min, n / 6.0))
    count = int(math.ceil(math.log(s_max / s_min) / math.log(ratio))) + 1
    return s_min * ratio ** np.arange(count)


def _log_kernel(s):
    half = int(math.ceil(4.0 * s)) + 1
    impulse = np.zeros(2 * half + 1)
    impulse[half] = 1.0
    return -(s * s) * ndimage.gaussian_laplace(impulse, s, mode="constant"), half


def scale_space(y, sigma, scales):
    """Respostas R (LoG normalizado) e significâncias brutas Z (R / ruído teórico).

    O ruído teórico propaga σ(2θ) pelo filtro de cada escala. A calibração
    empírica (função calibrate) corrige ruído correlacionado e σ mal estimado.
    """
    n = len(y)
    var = sigma ** 2
    R = np.empty((len(scales), n))
    Z = np.empty((len(scales), n))
    for k, s in enumerate(scales):
        r = -(s * s) * ndimage.gaussian_laplace(y, s, mode="reflect")
        kernel, half = _log_kernel(s)
        k2 = kernel * kernel
        padded = np.pad(var, half, mode="edge")
        if k2.size > 64:
            conv = signal.fftconvolve(padded, k2, mode="valid")
        else:
            conv = np.convolve(padded, k2, mode="valid")
        noise = np.sqrt(np.maximum(conv[:n], 1e-300))
        R[k] = r
        Z[k] = r / noise
    return R, Z


def calibrate(Z, scales, cap=None, exclude=None, fallback=None):
    """Fator de ruído de cada escala: desvio robusto de Z (1 = ruído branco com σ correto).

    Com exclude = [(índice, escala), ...], mede só longe desses picos, para que
    picos largos e densos não sejam confundidos com ruído nas escalas grandes.
    """
    K, n = Z.shape
    out = np.ones(K)
    for k in range(K):
        if exclude:
            mask = np.ones(n, dtype=bool)
            for i, s_c in exclude:
                reach = int(math.ceil(3.0 * s_c + 3.0 * scales[k]))
                mask[max(0, i - reach):i + reach + 1] = False
            if mask.sum() >= max(50, n // 10):
                c = _robust_scale(Z[k][mask])
            else:
                c = fallback[k] if fallback is not None else _robust_scale(Z[k])
        else:
            c = _robust_scale(Z[k])
        out[k] = min(c, cap) if cap is not None else c
    return out


def _scale_choice(rs, zs, threshold):
    """Escala natural da crista: máximo corrente da resposta até ela cair claramente.

    A resposta do LoG normalizado é máxima na escala natural do pico; a
    significância continua subindo em escalas maiores (o ruído cai com a média),
    então escolher pela significância inflaria a largura e fundiria vizinhos.
    """
    # Só escalas em que o pico domina o ruído: metade da significância máxima da crista.
    idx = np.nonzero(zs >= max(0.5 * threshold, 0.5 * float(np.max(zs))))[0]
    if len(idx) == 0:
        return int(np.argmax(rs))
    best = int(idx[0])
    for b in idx[1:]:
        if rs[b] > rs[best]:
            best = int(b)
        elif rs[b] < 0.85 * rs[best]:
            break  # a resposta já caiu: passamos da escala natural do pico
    return best


def ridge_candidates(R, Z, scales, threshold, min_len, reject_top=True):
    """Liga máximos locais entre escalas vizinhas e devolve as cristas significativas.

    Com reject_top, cristas cuja escala natural é a maior escala calculada são
    descartadas: a feição é mais larga que o permitido (fundo ou halo).
    """
    K = R.shape[0]
    finished, active = [], []
    for k in range(K):
        r = R[k]
        is_max = (r[1:-1] > r[:-2]) & (r[1:-1] >= r[2:]) & (r[1:-1] > 0)
        idx = np.nonzero(is_max)[0] + 1
        tol = max(2.0, float(scales[k]))
        pairs = []
        if len(idx):
            for a, ridge in enumerate(active):
                pos = int(np.searchsorted(idx, ridge["last"]))
                for j in (pos - 1, pos):
                    if 0 <= j < len(idx):
                        dist = abs(int(idx[j]) - ridge["last"])
                        if dist <= tol:
                            pairs.append((dist, a, j))
        pairs.sort()
        used_r, used_m, new_active = set(), set(), []
        for dist, a, j in pairs:
            if a in used_r or j in used_m:
                continue
            used_r.add(a)
            used_m.add(j)
            ridge = active[a]
            ridge["points"].append((k, int(idx[j])))
            ridge["last"] = int(idx[j])
            ridge["gap"] = 0
            new_active.append(ridge)
        for a, ridge in enumerate(active):
            if a in used_r:
                continue
            if ridge["gap"] < 1:  # tolera uma escala sem máximo
                ridge["gap"] += 1
                new_active.append(ridge)
            else:
                finished.append(ridge)
        for j, i in enumerate(idx):
            if j not in used_m:
                new_active.append({"points": [(k, int(i))], "last": int(i), "gap": 0})
        active = new_active
    finished.extend(active)

    candidates = []
    for ridge in finished:
        pts = ridge["points"]
        reaches_top = pts[-1][0] >= K - 1
        if len(pts) < min_len and not (reaches_top and len(pts) >= max(2, min_len - 1)):
            continue
        ks = np.array([p[0] for p in pts])
        ii = np.array([p[1] for p in pts])
        zs = Z[ks, ii]
        rs = R[ks, ii]
        z_max = float(np.max(zs))
        if z_max < threshold:
            continue
        best = _scale_choice(rs, zs, threshold)
        if reject_top and ks[best] >= K - 1:
            continue
        candidates.append({"k": int(ks[best]), "i": int(ii[best]), "z": z_max,
                           "r": float(rs[best]), "ridge_len": len(pts)})
    return candidates


# =============================================================================
# Tendência da largura com 2θ (Caglioti)
# =============================================================================

class WidthTrend:
    """FWHM(2θ) pela função de Caglioti: FWHM² = U·tan²θ + V·tanθ + W, limitada a [lo, hi]."""

    def __init__(self, U, V, W, lo, hi):
        self.U, self.V, self.W = float(U), float(V), float(W)
        self.lo, self.hi = float(lo), float(hi)

    def __call__(self, two_theta):
        t = math.tan(math.radians(float(two_theta) / 2.0))
        w2 = self.U * t * t + self.V * t + self.W
        return float(np.clip(math.sqrt(max(w2, self.lo ** 2)), self.lo, self.hi))

    def to_dict(self):
        return {"U": self.U, "V": self.V, "W": self.W, "lo": self.lo, "hi": self.hi}


def fit_width_trend(points, x0, x1, min_fwhm, max_fwhm, min_significance=5.0):
    """Ajusta a tendência de largura a pontos (2θ, fwhm, significância).

    Usa só picos significativos e descarta iterativamente os que fogem da
    tendência (±50%). Com poucos pontos, devolve uma largura constante.
    """
    pts = [(c, w, s) for c, w, s in points
           if np.isfinite(w) and w > 0 and np.isfinite(s) and s >= min_significance]
    if not pts:
        return None
    c = np.array([p[0] for p in pts])
    w = np.array([p[1] for p in pts])
    sig = np.array([p[2] for p in pts])
    lo = max(min_fwhm, 0.5 * float(np.min(w)))
    hi = min(max_fwhm, 2.0 * float(np.max(w)))
    if len(pts) < 3:
        return None  # poucos picos isolados: um pico fundido distorceria a tendência
    constant = WidthTrend(0.0, 0.0, float(np.median(w)) ** 2, lo, hi)
    if len(pts) < 5:
        return constant
    t = np.tan(np.radians(c / 2.0))
    A = np.column_stack([t * t, t, np.ones_like(t)])
    b = w * w
    weight = np.sqrt(np.minimum(sig, 50.0))
    keep = np.ones(len(c), dtype=bool)
    coef = None
    for _ in range(6):
        if keep.sum() < 4:
            break
        coef, *_ = np.linalg.lstsq(A[keep] * weight[keep, None], b[keep] * weight[keep], rcond=None)
        pred = np.sqrt(np.maximum(A @ coef, 1e-12))
        new_keep = np.abs(np.log(w / pred)) < 0.4
        if np.array_equal(new_keep, keep):
            break
        keep = new_keep
    if coef is None:
        return constant
    tg = np.tan(np.radians(np.linspace(x0, x1, 200) / 2.0))
    w2 = coef[0] * tg * tg + coef[1] * tg + coef[2]
    if np.any(w2 <= lo ** 2):
        return constant
    return WidthTrend(coef[0], coef[1], coef[2], lo, hi)


# =============================================================================
# Ajuste de perfil por grupos
# =============================================================================

def _pv_terms(x, c, w, eta, asym):
    """Pseudo-Voigt (split) e as derivadas usadas no Jacobiano analítico."""
    left = x < c
    ws = np.where(left, w * (1.0 - asym), w * (1.0 + asym))
    u = (x - c) / ws
    u2 = u * u
    lor = 1.0 / (1.0 + 4.0 * u2)
    gau = np.exp(-4.0 * LN2 * u2)
    shape = eta * lor + (1.0 - eta) * gau
    dshape_du = -8.0 * u * (eta * lor * lor + (1.0 - eta) * LN2 * gau)
    du_dc = -1.0 / ws
    du_dw = -u / w
    du_da = np.where(left, u / (1.0 - asym), -u / (1.0 + asym))
    return shape, dshape_du, du_dc, du_dw, du_da, lor - gau


class _Fit:
    """Resultado do ajuste de um grupo de picos sobrepostos."""

    def __init__(self, params, cov, chi2_data, chi2_total, n, ok):
        self.params = params
        self.cov = cov
        self.chi2_data = chi2_data
        self.chi2_total = chi2_total
        self.n = n
        self.ok = ok

    @property
    def n_comp(self):
        return (len(self.params) - 4) // 3

    @property
    def dof(self):
        return max(1, self.n - len(self.params))

    @property
    def chi2_red(self):
        return self.chi2_data / self.dof

    def comps(self):
        return self.params[4:].reshape(-1, 3)

    def errors(self):
        if self.cov is None:
            return np.full(len(self.params), np.nan)
        return np.sqrt(np.clip(np.diag(self.cov), 0.0, None))

    def area_and_error(self, j):
        eta = self.params[2]
        c, h, w = self.comps()[j]
        k = area_factor(eta)
        area = h * w * k
        if self.cov is None:
            return area, np.nan
        grad = np.zeros(len(self.params))
        base = 4 + 3 * j
        grad[base + 1] = w * k
        grad[base + 2] = h * k
        grad[2] = h * w * (LORENTZ_AREA - GAUSS_AREA)
        var = float(grad @ self.cov @ grad)
        return area, math.sqrt(var) if var > 0 else np.nan

    def significance(self, j):
        area, err = self.area_and_error(j)
        if not np.isfinite(err) or err <= 0:
            return float("inf") if area > 0 else 0.0
        return area / err


class _GroupFitter:
    def __init__(self, x, y, sigma, bg, step, settings, lam1, lam2, width_trend=None):
        self.x, self.y, self.sigma, self.bg = x, y, sigma, bg
        self.step = step
        self.settings = settings
        self.xm = 0.5 * (x[0] + x[-1])
        self.half_width = max(0.5 * (x[-1] - x[0]), step)
        self.slope_scale = max(self.half_width, 1.0)  # inclinação do fundo limitada por grau
        self.use_ka2 = bool(settings.ka2 and lam1 and lam2)
        self.lam1, self.lam2 = lam1, lam2
        self.ratio = settings.ka2_ratio
        self.width_trend = width_trend if settings.width_prior else None
        self.tau = max(0.05, float(settings.width_tolerance))
        excess = y - bg
        self.amp_scale = max(float(np.max(np.abs(excess))), float(np.median(sigma)) * 3.0, 1e-12)
        self._targets = None
        self._cache_key = None
        self._cache = None

    # --- geometria do Kα2 ---------------------------------------------------
    def ka2_center(self, c):
        return same_d_two_theta(c, self.lam1, self.lam2)

    def _ka2_slope(self, c):
        k = self.lam2 / self.lam1
        th = math.radians(c / 2.0)
        s = k * math.sin(th)
        if s >= 1.0:
            return 0.0
        return k * math.cos(th) / math.sqrt(1.0 - s * s)

    # --- modelo -----------------------------------------------------------
    def _evaluate(self, p, x=None, want_jac=False, profiles_only=False):
        own = x is None
        x = self.x if own else x
        a0, a1, eta, asym = p[:4]
        if profiles_only:
            out = np.zeros(len(x))
        else:
            bg = self.bg if own else np.interp(x, self.x, self.bg)
            out = bg + a0 + a1 * (x - self.xm)
        J = None
        if want_jac:
            J = np.zeros((len(x), len(p)))
            J[:, 0] = 1.0
            J[:, 1] = x - self.xm
        for j, (c, h, w) in enumerate(p[4:].reshape(-1, 3)):
            base = 4 + 3 * j
            shape, ds, duc, duw, dua, lmg = _pv_terms(x, c, w, eta, asym)
            out = out + h * shape
            if want_jac:
                J[:, base] += h * ds * duc
                J[:, base + 1] += shape
                J[:, base + 2] += h * ds * duw
                J[:, 2] += h * lmg
                J[:, 3] += h * ds * dua
            if self.use_ka2:
                c2 = self.ka2_center(c)
                if np.isfinite(c2):
                    r = self.ratio
                    s2, ds2, duc2, duw2, dua2, lmg2 = _pv_terms(x, c2, w, eta, asym)
                    out = out + r * h * s2
                    if want_jac:
                        J[:, base] += r * h * ds2 * duc2 * self._ka2_slope(c)
                        J[:, base + 1] += r * s2
                        J[:, base + 2] += r * h * ds2 * duw2
                        J[:, 2] += r * h * lmg2
                        J[:, 3] += r * h * ds2 * dua2
        return out, J

    def model(self, p, x=None):
        return self._evaluate(p, x)[0]

    def profiles(self, p, x):
        """Só os perfis dos picos (sem fundo nem correção linear) em x."""
        return self._evaluate(p, x, profiles_only=True)[0]

    def _compute(self, p):
        key = p.tobytes()
        if key != self._cache_key:
            model, J = self._evaluate(p, want_jac=True)
            res = (self.y - model) / self.sigma
            jac = -J / self.sigma[:, None]
            if self._targets is not None:
                w = p[4:].reshape(-1, 3)[:, 2]
                prior = (np.log(w) - np.log(self._targets)) / self.tau
                pj = np.zeros((len(w), len(p)))
                pj[np.arange(len(w)), 4 + 3 * np.arange(len(w)) + 2] = 1.0 / (self.tau * w)
                res = np.concatenate([res, prior])
                jac = np.vstack([jac, pj])
            self._cache_key, self._cache = key, (res, jac)
        return self._cache

    def bounds_for(self, comps_init, targets):
        s = self.settings
        a0_lim = 0.1 * self.amp_scale + 3.0 * float(np.median(self.sigma))
        lo = [-a0_lim, -a0_lim / self.slope_scale, 0.0, -0.45]
        hi = [a0_lim, a0_lim / self.slope_scale, 1.0, 0.45]
        max_fwhm = s.effective_max_fwhm()
        for j, (c0, h0, w0) in enumerate(comps_init):
            ref = targets[j] if targets is not None else w0
            dc = max(0.6 * max(w0, ref), 2.0 * self.step)
            if targets is not None:
                w_lo = max(s.min_fwhm, self.step, 0.4 * ref)
                w_hi = min(max_fwhm, 2.5 * ref)
            else:
                w_lo = max(s.min_fwhm, self.step, 0.3 * w0)
                w_hi = min(max_fwhm, max(3.0 * w0, 1.5 * w_lo))
            if w_hi <= w_lo:
                w_hi = w_lo * 1.5
            lo += [c0 - dc, 0.0, w_lo]
            hi += [c0 + dc, max(5.0 * h0, 2.0 * self.amp_scale), w_hi]
        return np.array(lo), np.array(hi)

    def fit(self, comps_init, start=None):
        """Ajusta o grupo. comps_init: lista de (centro, altura, fwhm) iniciais."""
        if not comps_init:
            return None
        targets = None
        if self.width_trend is not None:
            targets = np.array([self.width_trend(c0) for c0, _, _ in comps_init])
        lo, hi = self.bounds_for(comps_init, targets)
        if start is None:
            p0 = [0.0, 0.0, 0.5, 0.0]
            for j, (c0, h0, w0) in enumerate(comps_init):
                p0 += [c0, h0, targets[j] if targets is not None else w0]
            p0 = np.array(p0, dtype=float)
        else:
            p0 = np.array(start, dtype=float)
        p0 = np.clip(p0, lo + 1e-9 * (hi - lo), hi - 1e-9 * (hi - lo))
        self._targets = targets
        self._cache_key = None
        try:
            res = least_squares(lambda q: self._compute(q)[0], p0, jac=lambda q: self._compute(q)[1],
                                bounds=(lo, hi), method="trf", x_scale="jac", max_nfev=40 * len(p0))
        except Exception as exc:  # noqa: BLE001 - ajuste numérico pode falhar de várias formas
            logger.debug(f"Ajuste falhou: {exc}")
            return None
        n = len(self.y)
        chi2_data = float(np.sum(res.fun[:n] ** 2))
        chi2_total = float(np.sum(res.fun ** 2))
        dof = max(1, n - len(res.x))
        cov = None
        try:
            jac = res.jac[:n]
            cov = np.linalg.pinv(jac.T @ jac) * max(1.0, chi2_data / dof)
        except Exception:  # noqa: BLE001
            cov = None
        return _Fit(res.x, cov, chi2_data, chi2_total, n, res.success)

    def residual_candidate(self, fit, threshold):
        """Ombro escondido: o maior calombo significativo do resíduo, se houver."""
        model = self.model(fit.params)
        resid = (self.y - model) / self.sigma / math.sqrt(max(1.0, fit.chi2_red))
        comps = fit.comps()
        w_med = float(np.median(comps[:, 2]))
        best = None
        for factor in (0.6, 1.0, 1.5):
            s = max(0.7, factor * w_med / FWHM_PER_SCALE / self.step)
            r = -(s * s) * ndimage.gaussian_laplace(resid, s, mode="reflect")
            kernel, _ = _log_kernel(s)
            z = r / math.sqrt(float(np.sum(kernel * kernel)))
            margin = min(len(z) // 4, int(2 * s))
            core = z[margin:len(z) - margin] if margin > 0 else z
            if core.size >= 20:
                z = z / max(1.0, _robust_scale(core))
            if margin > 0:
                z[:margin] = -np.inf
                z[-margin:] = -np.inf
            i = int(np.argmax(z))
            if np.isfinite(z[i]) and (best is None or z[i] > best[0]):
                best = (float(z[i]), i, factor * w_med)
        if best is None or best[0] < threshold:
            return None
        z, i, w_new = best
        c_new = float(self.x[i])
        for c, h, w in comps:
            if abs(c_new - c) < 0.35 * w:
                return None
            if self.use_ka2:
                c2 = self.ka2_center(c)
                if np.isfinite(c2) and abs(c_new - c2) < 0.35 * w:
                    return None
        if self.width_trend is not None:
            w_new = self.width_trend(c_new)
        h_new = max(float(self.y[i] - model[i]), float(self.sigma[i]))
        w_new = float(np.clip(w_new, max(self.settings.min_fwhm, self.step),
                              self.settings.effective_max_fwhm()))
        return (c_new, h_new, w_new)


def _delta_bic(old, new):
    """Variação do BIC normalizada pela qualidade do ajuste anterior (robusta a σ mal estimado)."""
    scale = max(1.0, old.chi2_red)
    return (new.chi2_total - old.chi2_total) / scale + (len(new.params) - len(old.params)) * math.log(old.n)


def _try_split(fitter, fit, fit_threshold):
    """Tenta dividir o componente mais suspeito (largo ou assimétrico) em dois.

    Aceita só se o BIC cair bem, se os dois componentes forem significativos,
    separados por pelo menos ~metade da largura e com alturas comparáveis
    (o menor com pelo menos 12% do maior). Isso evita "ombros" criados apenas
    pela diferença entre o perfil real e a pseudo-Voigt.
    """
    comps = fit.comps()
    asym = abs(fit.params[3])
    suspects = []
    for j, (c, h, w) in enumerate(comps):
        if fit.significance(j) < 2.0 * fit_threshold:
            continue  # componente fraco: não há informação para dividir
        if fitter.width_trend is not None:
            ratio = w / fitter.width_trend(c)
        else:
            others = np.delete(comps[:, 2], j)
            ratio = 2.0 if len(others) == 0 else w / float(np.median(others))
        if ratio > 1.4 or asym > 0.2:
            suspects.append((ratio, j))
    for _, j in sorted(suspects, reverse=True)[:2]:  # no máximo 2 tentativas por grupo
        c, h, w = comps[j]
        d = 0.3 * w
        keep = [tuple(cc) for i, cc in enumerate(comps) if i != j]
        new = [(c - d, 0.6 * h, 0.7 * w), (c + d, 0.6 * h, 0.7 * w)]
        start = np.concatenate([fit.params[:4], np.concatenate(keep + new)])
        start[3] = 0.0
        trial = fitter.fit(keep + new, start=start)
        if trial is None or _delta_bic(fit, trial) > -10.0:
            continue
        a, b = trial.n_comp - 2, trial.n_comp - 1
        ca, ha, wa = trial.comps()[a]
        cb, hb, wb = trial.comps()[b]
        if min(trial.significance(a), trial.significance(b)) < fit_threshold:
            continue
        if abs(cb - ca) < 0.45 * min(wa, wb) or min(ha, hb) < 0.12 * max(ha, hb):
            continue
        return trial
    return None


def _pedestal(fit, significant):
    """Índice de um componente "pedestal": bem mais largo que os vizinhos e quase
    concêntrico com um pico estreito (modo cristalino). None se não houver."""
    comps = fit.comps()
    if len(comps) < 2:
        return None
    for j in np.argsort(-comps[:, 2]):
        others = [k for k in range(len(comps)) if k != j and significant[k]]
        if not others:
            continue
        cj, hj, wj = comps[j]
        if wj <= 2.2 * float(np.median(comps[others, 2])):
            continue
        if any(abs(cj - comps[k, 0]) < 0.6 * wj and comps[k, 2] < 0.5 * wj for k in others):
            return int(j)
    return None


def _fit_group(fitter, comps_init, threshold, fit_threshold, max_extra, allow_split=True, cancel=None):
    fit = fitter.fit(comps_init)
    if fit is None:
        return None
    for _ in range(max_extra):
        if cancel and cancel():
            raise SearchCancelled()
        cand = fitter.residual_candidate(fit, threshold)
        if cand is None:
            break
        start = np.concatenate([fit.params, cand])
        trial = fitter.fit([tuple(c) for c in fit.comps()] + [cand], start=start)
        if trial is None or _delta_bic(fit, trial) > -10.0:
            break
        if trial.significance(trial.n_comp - 1) < fit_threshold:
            break
        fit = trial
    if allow_split:
        for _ in range(2):
            if cancel and cancel():
                raise SearchCancelled()
            split = _try_split(fitter, fit, fit_threshold)
            if split is None:
                break
            fit = split
    broad_ok = fitter.settings.broad_mode
    max_w = fitter.settings.effective_max_fwhm()
    while fit is not None and fit.n_comp > 0:
        sig = np.array([fit.significance(j) for j in range(fit.n_comp)])
        at_limit = np.nonzero(fit.comps()[:, 2] >= 0.98 * max_w)[0] if not broad_ok else []
        pedestal = None if broad_ok else _pedestal(fit, sig >= fit_threshold)
        if len(at_limit):
            worst = int(at_limit[0])  # largura no teto: feição de fundo, não pico
        elif pedestal is not None:
            worst = pedestal  # componente largo sob um pico estreito: artefato do ajuste
        else:
            worst = int(np.argmin(sig))
            if sig[worst] >= fit_threshold:
                break
        keep = [tuple(c) for j, c in enumerate(fit.comps()) if j != worst]
        if not keep:
            return None
        start = np.concatenate([fit.params[:4], np.concatenate(keep)])
        fit = fitter.fit(keep, start=start)
    return fit


# =============================================================================
# Busca completa
# =============================================================================

def _candidate_groups(cands, use_ka2, lam1, lam2, max_size=20):
    if not cands:
        return []
    spans = []
    for c in cands:
        lo = c["center"] - 2.5 * c["fwhm"]
        hi = c["center"] + 2.5 * c["fwhm"]
        if use_ka2:
            c2 = same_d_two_theta(c["center"], lam1, lam2)
            if np.isfinite(c2):
                hi = max(hi, c2 + 2.5 * c["fwhm"])
        spans.append((lo, hi))
    order = np.argsort([s[0] for s in spans])
    groups, current, current_hi = [], [], -np.inf
    for idx in order:
        lo, hi = spans[idx]
        if current and lo > current_hi:
            groups.append(current)
            current, current_hi = [], -np.inf
        current.append(int(idx))
        current_hi = max(current_hi, hi)
    if current:
        groups.append(current)

    out = []
    for g in groups:  # grupos grandes demais são divididos nas maiores folgas
        g = sorted(g, key=lambda i: cands[i]["center"])
        stack = [g]
        while stack:
            part = stack.pop()
            if len(part) <= max_size:
                out.append(part)
                continue
            gaps = [(cands[part[j + 1]]["center"] - cands[part[j]]["center"])
                    / (cands[part[j + 1]]["fwhm"] + cands[part[j]]["fwhm"]) for j in range(len(part) - 1)]
            cut = int(np.argmax(gaps)) + 1
            stack.extend([part[:cut], part[cut:]])
    return out


def _drop_ka2_satellites(cands, lam1, lam2, ratio, step):
    """Remove candidatos que são o Kα2 resolvido de um pico mais forte."""
    keep = sorted(cands, key=lambda c: -c["height"])
    removed = set()
    for a, parent in enumerate(keep):
        if a in removed:
            continue
        c2 = same_d_two_theta(parent["center"], lam1, lam2)
        if not np.isfinite(c2):
            continue
        tol = max(0.35 * parent["fwhm"], 2.0 * step)
        for b, child in enumerate(keep):
            if b == a or b in removed:
                continue
            if (abs(child["center"] - c2) <= tol
                    and 0.2 * ratio * parent["height"] <= child["height"] <= 1.6 * ratio * parent["height"]):
                removed.add(b)
    return [c for j, c in enumerate(keep) if j not in removed]


def _flag_kbeta(peaks, lam1, lam_kb, step):
    by_height = sorted(peaks, key=lambda p: -p.height)
    for strong in by_height:
        pos = same_d_two_theta(strong.two_theta, lam1, lam_kb)
        if not np.isfinite(pos):
            continue
        tol = max(0.5 * strong.fwhm, 2.0 * step)
        for weak in peaks:
            if weak is strong or weak.kind != "peak":
                continue
            if abs(weak.two_theta - pos) <= tol and weak.height <= 0.35 * strong.height:
                if "kbeta" not in weak.flags:
                    weak.flags.append("kbeta")


def _peak_from_fit(fit, j, fitter, x, background, settings, use_ka2, origin="auto"):
    errs = fit.errors()
    a0, a1, eta, asym = fit.params[:4]
    c, h, w = fit.comps()[j]
    area, area_err = fit.area_and_error(j)
    base = 4 + 3 * j
    return Peak(
        two_theta=float(c), height=float(h), fwhm=float(w), eta=float(eta), asymmetry=float(asym),
        area=float(area), background=float(np.interp(c, x, background) + a0 + a1 * (c - fitter.xm)),
        two_theta_err=float(errs[base]), height_err=float(errs[base + 1]), fwhm_err=float(errs[base + 2]),
        area_err=float(area_err), significance=float(fit.significance(j)),
        kind="halo" if w >= settings.halo_min_fwhm else "peak", origin=origin, ka2=use_ka2,
    )


def search_peaks(two_theta, intensity, settings=None, wavelength=None, wavelength_ka2=None,
                 wavelength_kb=None, progress=None, cancel=None):
    """Busca picos (e halos) num difratograma.

    Args:
        two_theta, intensity: dados medidos (qualquer ordem; passo pode ser irregular).
        settings: PeakSearchSettings (padrão se None).
        wavelength: Kα1 (ou λ único) em Å. Necessário para o Kα2 e o Kβ.
        wavelength_ka2: Kα2 em Å; sem ele o dubleto não é modelado.
        wavelength_kb: Kβ1 em Å, só para marcar possíveis picos de Kβ.
        progress: função opcional progress(fração, mensagem).
        cancel: função opcional que devolve True para interromper (SearchCancelled).

    Returns:
        PeakSearchResult
    """
    t_start = time.perf_counter()
    s = settings or PeakSearchSettings()
    info = {"warnings": []}

    def report(frac, msg):
        if progress:
            progress(frac, msg)
        if cancel and cancel():
            raise SearchCancelled()

    x, y_raw, step, resampled = prepare_data(two_theta, intensity)
    n = len(x)
    if n < 20 or step <= 0 or np.ptp(y_raw) <= 0:
        info["warnings"].append("dados insuficientes ou constantes")
        empty = np.zeros(n)
        return PeakSearchResult([], x, y_raw, empty, empty, empty, None, info)
    info.update(step=step, resampled=resampled, n_points=n)

    report(0.05, "ruído")
    sigma, poisson = estimate_noise(y_raw)
    y = y_raw
    spikes = 0
    if s.remove_spikes:
        y, spikes = remove_spikes(y_raw, sigma)
        if spikes:
            sigma, poisson = estimate_noise(y, counts=None if poisson else False)
    info.update(spikes_removed=spikes, poisson_noise=poisson, noise_median=float(np.median(sigma)))

    use_ka2 = bool(s.ka2 and wavelength and wavelength_ka2)
    max_fwhm = s.effective_max_fwhm()
    min_fwhm = max(s.min_fwhm, 0.5 * step)

    # --- detecção -----------------------------------------------------------
    report(0.12, "detecção multiescala")
    scales = _scales(step, n, min_fwhm, 1.5 * max_fwhm)  # até 1,5x: pico no limite não é rejeitado
    R, Zraw = scale_space(y, sigma, scales)
    calib = calibrate(Zraw, scales, cap=1.5 if poisson else None)
    raw_cands = ridge_candidates(R, Zraw / calib[:, None], scales, s.sensitivity, s.min_ridge_scales)
    if raw_cands:  # 2ª calibração: ruído medido só longe dos picos achados
        calib = calibrate(Zraw, scales, exclude=[(c["i"], scales[c["k"]]) for c in raw_cands], fallback=calib)
        raw_cands = ridge_candidates(R, Zraw / calib[:, None], scales, s.sensitivity, s.min_ridge_scales)
    info["noise_calibration"] = [round(float(c), 3) for c in calib]
    info["n_ridges"] = len(raw_cands)

    def sigma_factor(widths):
        """Correção de σ para o ruído na escala típica destes picos (nunca menor que 1)."""
        s_pts = float(np.median(widths)) / FWHM_PER_SCALE / step
        k = int(np.argmin(np.abs(scales - s_pts)))
        return max(1.0, float(calib[k]))

    cands = []
    for c in raw_cands:
        sc = float(scales[c["k"]])
        lo = max(0, c["i"] - int(math.ceil(sc)))
        hi = min(n, c["i"] + int(math.ceil(sc)) + 1)
        seg = y[lo:hi]
        smooth = ndimage.gaussian_filter1d(seg, max(0.5, sc / 2.0)) if len(seg) > 3 else seg
        j = lo + int(np.argmax(smooth)) if len(smooth) else c["i"]
        center = float(x[j])
        if 0 < j < n - 1:
            ym, y0, yp = y[j - 1], y[j], y[j + 1]
            den = ym - 2.0 * y0 + yp
            if den < 0:
                center += float(np.clip(0.5 * (ym - yp) / den, -0.5, 0.5)) * step
        fwhm = float(np.clip(FWHM_PER_SCALE * sc * step, min_fwhm, max_fwhm))
        cands.append({"center": center, "fwhm": fwhm, "z": c["z"], "r": c["r"], "i": j})

    cands.sort(key=lambda c: -c["z"])  # duplicatas da mesma crista partida: fica a mais forte
    unique = []
    for c in cands:
        if all(abs(c["center"] - u["center"]) > 0.35 * max(c["fwhm"], u["fwhm"]) for u in unique):
            unique.append(c)
    cands = unique

    # --- fundo --------------------------------------------------------------
    report(0.30, "fundo")
    strong = sorted(cands, key=lambda c: -c["z"])[:15]
    typical = float(np.median([c["fwhm"] for c in strong])) if strong else 4.0 * step
    if s.background_window > 0:
        half_deg = s.background_window
    elif s.broad_mode:
        widest = max((c["fwhm"] for c in cands), default=max_fwhm)
        half_deg = float(np.clip(2.0 * widest, 8.0, 30.0))
    else:
        half_deg = float(np.clip(3.0 * typical, 0.6, 4.0))
    half_deg = min(half_deg, 0.45 * (x[-1] - x[0]))
    peak_mask = np.zeros(n, dtype=bool)
    for c in cands:
        peak_mask |= np.abs(x - c["center"]) < 2.5 * c["fwhm"]
        if use_ka2:
            c2 = same_d_two_theta(c["center"], wavelength, wavelength_ka2)
            if np.isfinite(c2):
                peak_mask |= np.abs(x - c2) < 2.5 * c["fwhm"]
    smooth_pts = max(1.0, 0.5 * typical / FWHM_PER_SCALE / step)
    background = estimate_background(y, half_deg / step, smooth_pts, peak_mask)
    info["background_half_window_deg"] = half_deg

    for c in cands:
        c["height"] = max(float(y[c["i"]] - background[c["i"]]), c["r"] / LOG_PEAK_RESPONSE * 0.25,
                          float(sigma[c["i"]]))
    if use_ka2:
        cands = _drop_ka2_satellites(cands, wavelength, wavelength_ka2, s.ka2_ratio, step)
    info["n_candidates"] = len(cands)

    peaks = []
    fit_threshold = max(2.0, 0.6 * s.sensitivity)
    lam1 = wavelength if use_ka2 else None
    lam2 = wavelength_ka2 if use_ka2 else None

    # --- halos (modo largo): ajustados primeiro, com os picos finos mascarados -----
    halo_cands = [c for c in cands if c["fwhm"] >= s.halo_min_fwhm] if s.broad_mode else []
    if halo_cands and s.fit_profiles:
        report(0.35, "halos")
        narrow = [c for c in cands if c["fwhm"] < s.halo_min_fwhm]
        mask = np.ones(n, dtype=bool)
        for c in narrow:
            mask &= np.abs(x - c["center"]) > 2.0 * c["fwhm"]
            if use_ka2:
                c2 = same_d_two_theta(c["center"], wavelength, wavelength_ka2)
                if np.isfinite(c2):
                    mask &= np.abs(x - c2) > 2.0 * c["fwhm"]
        if mask.sum() >= 20:
            halo_sigma = sigma[mask] * sigma_factor([c["fwhm"] for c in halo_cands])
            no_prior = PeakSearchSettings.from_dict({**s.to_dict(), "width_prior": False})
            halo_fitter = _GroupFitter(x[mask], y[mask], halo_sigma, background[mask], step, no_prior, None, None)
            halo_fit = _fit_group(halo_fitter, [(c["center"], c["height"], c["fwhm"]) for c in halo_cands],
                                  s.sensitivity, fit_threshold, 1, allow_split=False, cancel=cancel)
            if halo_fit is not None:
                for j in range(halo_fit.n_comp):
                    p = _peak_from_fit(halo_fit, j, halo_fitter, x, background, s, False)
                    peaks.append(p)
                background = halo_fitter.model(halo_fit.params, x=x)
        cands = [c for c in cands if c["fwhm"] < s.halo_min_fwhm]

    model = background.copy()
    trend = None
    if s.fit_profiles and cands:
        groups = _candidate_groups(cands, use_ka2, wavelength, wavelength_ka2)
        info["n_groups"] = len(groups)

        def make_fitter(members, width_trend):
            w_max = max(m["fwhm"] for m in members)
            lo_x = min(m["center"] for m in members) - 3.5 * w_max
            hi_x = max(m["center"] for m in members) + 3.5 * w_max
            if use_ka2:
                c2 = same_d_two_theta(max(m["center"] for m in members), wavelength, wavelength_ka2)
                if np.isfinite(c2):
                    hi_x = max(hi_x, c2 + 3.5 * w_max)
            if lo_x < x[0]:  # janela cortada pela borda: desloca para dentro dos dados
                hi_x = min(x[-1], hi_x + (x[0] - lo_x))
            if hi_x > x[-1]:
                lo_x = max(x[0], lo_x - (hi_x - x[-1]))
            sel = (x >= lo_x) & (x <= hi_x)
            if sel.sum() < 8:
                return None, sel
            g_sigma = sigma[sel] * sigma_factor([m["fwhm"] for m in members])
            xs = x[sel]
            own = {id(m) for m in members}
            for other in cands:  # picos de grupos vizinhos na janela: peso zero (não são "redescobertos")
                if id(other) in own:
                    continue
                positions = [other["center"]]
                if use_ka2:
                    c2 = same_d_two_theta(other["center"], wavelength, wavelength_ka2)
                    if np.isfinite(c2):
                        positions.append(c2)
                for pos in positions:
                    if lo_x - 2.5 * other["fwhm"] <= pos <= hi_x + 2.5 * other["fwhm"]:
                        g_sigma[np.abs(xs - pos) < 2.5 * other["fwhm"]] *= 1e3
            return _GroupFitter(xs, y[sel], g_sigma, background[sel], step, s, lam1, lam2, width_trend), sel

        # 1ª passada: ajustes rápidos para aprender a tendência da largura
        if s.width_prior:
            points = []
            for gi, g in enumerate(groups):
                report(0.38 + 0.2 * gi / max(1, len(groups)), "largura dos picos")
                members = [cands[i] for i in g]
                fitter, _ = make_fitter(members, None)
                if fitter is None:
                    continue
                fit = _fit_group(fitter, [(m["center"], m["height"], m["fwhm"]) for m in members],
                                 s.sensitivity, fit_threshold, 0, allow_split=False, cancel=cancel)
                if fit is not None and fit.n_comp == 1:
                    c, h, w = fit.comps()[0]
                    points.append((float(c), float(w), float(fit.significance(0))))
            trend = fit_width_trend(points, x[0], x[-1], min_fwhm, max_fwhm)
            if trend is not None:
                info["width_trend"] = trend.to_dict()
                info["width_trend_points"] = len(points)

        # 2ª passada: ajuste completo com seleção de modelo
        for gi, g in enumerate(groups):
            report(0.6 + 0.38 * gi / max(1, len(groups)), "ajuste de perfis")
            members = [cands[i] for i in g]
            fitter, sel = make_fitter(members, trend)
            if fitter is None:
                continue
            fit = _fit_group(fitter, [(m["center"], m["height"], m["fwhm"]) for m in members],
                             s.sensitivity, fit_threshold, s.max_extra_components, cancel=cancel)
            if fit is None:
                continue
            for j in range(fit.n_comp):
                c = fit.comps()[j][0]
                if x[0] <= c <= x[-1]:
                    peaks.append(_peak_from_fit(fit, j, fitter, x, background, s, use_ka2))
            model += fitter.profiles(fit.params, x)
    else:
        for c in cands:
            peaks.append(Peak(two_theta=c["center"], height=c["height"], fwhm=c["fwhm"],
                              background=float(np.interp(c["center"], x, background)),
                              significance=c["z"],
                              kind="halo" if c["fwhm"] >= s.halo_min_fwhm else "peak",
                              origin="auto", ka2=use_ka2))

    peaks.sort(key=lambda p: p.two_theta)
    if s.flag_kbeta and wavelength and wavelength_kb:
        _flag_kbeta(peaks, wavelength, wavelength_kb, step)

    halo_area = sum(p.area for p in peaks if p.kind == "halo")
    crystal_area = sum(p.area for p in peaks if p.kind == "peak")
    crystallinity = None
    if halo_area > 0 and (halo_area + crystal_area) > 0:
        crystallinity = crystal_area / (halo_area + crystal_area)

    info["elapsed_s"] = time.perf_counter() - t_start
    info["settings"] = s.to_dict()
    report(1.0, "concluído")
    return PeakSearchResult(peaks, x, y, background, model, sigma, crystallinity, info)


def fit_peak_at(two_theta, intensity, x_click, settings=None, wavelength=None, wavelength_ka2=None,
                existing=None, background=None, fwhm_guess=None):
    """Ajusta um único pico perto de x_click (adição manual pelo usuário).

    A largura inicial vem da tendência dos picos existentes (ou da mediana).
    Picos já existentes que tocam a janela entram como contribuição fixa. Se o
    ajuste falhar, devolve um pico no máximo local com a largura estimada.

    Returns:
        Peak com origin="manual".
    """
    s = settings or PeakSearchSettings()
    x, y, step, _ = prepare_data(two_theta, intensity)
    if len(x) < 8:
        raise ValueError("dados insuficientes")
    sigma, _ = estimate_noise(y)
    existing = list(existing or [])
    if fwhm_guess is None:
        trend = fit_width_trend([(p.two_theta, p.fwhm, p.significance) for p in existing if p.kind == "peak"],
                                x[0], x[-1], max(s.min_fwhm, step), s.effective_max_fwhm())
        if trend is not None:
            fwhm_guess = trend(x_click)
        else:
            widths = [p.fwhm for p in existing if p.kind == "peak"]
            fwhm_guess = float(np.median(widths)) if widths else 0.15
    w0 = float(np.clip(fwhm_guess, max(s.min_fwhm, step), s.effective_max_fwhm()))
    if background is None or len(background) != len(x):
        half = float(np.clip(3.0 * w0, 0.6, 4.0)) if not s.broad_mode else float(np.clip(2.0 * w0, 8.0, 30.0))
        background = estimate_background(y, min(half, 0.45 * (x[-1] - x[0])) / step,
                                         max(1.0, 0.5 * w0 / FWHM_PER_SCALE / step))
    use_ka2 = bool(s.ka2 and wavelength and wavelength_ka2)

    near = np.abs(x - x_click) <= max(1.5 * w0, 2 * step)
    if not near.any():
        raise ValueError("clique fora dos dados")
    excess = ndimage.gaussian_filter1d(y - background, max(0.5, w0 / FWHM_PER_SCALE / step / 2.0))
    idx = np.nonzero(near)[0]
    j = int(idx[np.argmax(excess[idx])])
    c0 = float(x[j])
    h0 = max(float(excess[j]), float(sigma[j]))

    sel = np.abs(x - c0) <= 4.0 * w0
    if use_ka2:
        c2 = same_d_two_theta(c0, wavelength, wavelength_ka2)
        if np.isfinite(c2):
            sel |= (x >= c0) & (x <= c2 + 4.0 * w0)
    xs = x[sel]
    fixed = np.zeros(len(xs))
    for p in existing:
        if abs(p.two_theta - c0) > 4.0 * w0 + 4.0 * p.fwhm:
            continue
        fixed += p.height * pv_shape(xs, p.two_theta, p.fwhm, p.eta, p.asymmetry)
        if p.ka2 and wavelength and wavelength_ka2:
            pc2 = same_d_two_theta(p.two_theta, wavelength, wavelength_ka2)
            if np.isfinite(pc2):
                fixed += s.ka2_ratio * p.height * pv_shape(xs, pc2, p.fwhm, p.eta, p.asymmetry)

    fallback = Peak(two_theta=c0, height=h0, fwhm=w0, background=float(background[j]),
                    origin="manual", ka2=use_ka2)
    if len(xs) < 8:
        return fallback
    no_prior = PeakSearchSettings.from_dict({**s.to_dict(), "width_prior": False})
    fitter = _GroupFitter(xs, y[sel], sigma[sel], background[sel] + fixed, step, no_prior,
                          wavelength if use_ka2 else None, wavelength_ka2 if use_ka2 else None)
    fit = fitter.fit([(c0, h0, w0)])
    if fit is None or fit.n_comp == 0:
        return fallback
    c, h, w = fit.comps()[0]
    if h <= 0 or not np.isfinite(c):
        return fallback
    return _peak_from_fit(fit, 0, fitter, x, background, s, use_ka2, origin="manual")
