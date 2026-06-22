# auto_fit.py
# Modulo de Auto-Ajuste de parametros de rede por minimizacao de posicoes de pico
# v2 - Com reflexoes reais via XRDCalculator
#
# Fundamento cientifico:
# A posicao 2theta de cada reflexao (hkl) depende dos parametros de rede
# (a, b, c, alpha, beta, gamma) e do comprimento de onda lambda:
#   Lei de Bragg:  n*lambda = 2d*sin(theta)
#
# MELHORIA v2: Usa o pymatgen XRDCalculator para obter apenas reflexoes REAIS
# (com fator de estrutura nao-nulo e considerando extincoes sistematicas).
#
# Referencias:
#   - Young, R.A. (1993). The Rietveld Method. Oxford University Press.
#   - Le Bail, A. et al. (1988). Mat. Res. Bull. 23, 447-452.
#   - International Tables for Crystallography, Vol. A (2016). Wiley.
#
# Parte do projeto MatFinder - Copyright (C) 2025 Raynner Valentim (UFAM)

import logging
import math
import numpy as np
from scipy.optimize import minimize
from scipy.signal import find_peaks
from matfinder.core.translator import ptr

logger = logging.getLogger(__name__)


# ============================================================================
# EQUACOES DE ESPACAMENTO INTERPLANAR d(hkl)
# ============================================================================

def d_spacing_cubic(h, k, l, a):
    denom = (h**2 + k**2 + l**2) / a**2
    if denom <= 0:
        return float('inf')
    return 1.0 / math.sqrt(denom)


def d_spacing_tetragonal(h, k, l, a, c):
    denom = (h**2 + k**2) / a**2 + l**2 / c**2
    if denom <= 0:
        return float('inf')
    return 1.0 / math.sqrt(denom)


def d_spacing_orthorhombic(h, k, l, a, b, c):
    denom = h**2 / a**2 + k**2 / b**2 + l**2 / c**2
    if denom <= 0:
        return float('inf')
    return 1.0 / math.sqrt(denom)


def d_spacing_hexagonal(h, k, l, a, c):
    denom = 4.0 * (h**2 + h*k + k**2) / (3.0 * a**2) + l**2 / c**2
    if denom <= 0:
        return float('inf')
    return 1.0 / math.sqrt(denom)


def d_spacing_rhombohedral(h, k, l, a, alpha_rad):
    cos_a = math.cos(alpha_rad)
    sin_a = math.sin(alpha_rad)
    num = (h**2 + k**2 + l**2) * sin_a**2 + 2*(h*k + k*l + h*l) * (cos_a**2 - cos_a)
    den = a**2 * (1.0 - 3.0*cos_a**2 + 2.0*cos_a**3)
    if den <= 0 or num <= 0:
        return float('inf')
    return 1.0 / math.sqrt(num / den)


def d_spacing_monoclinic(h, k, l, a, b, c, beta_rad):
    sin_b = math.sin(beta_rad)
    cos_b = math.cos(beta_rad)
    denom = (1.0 / sin_b**2) * (
        h**2 / a**2 +
        k**2 * sin_b**2 / b**2 +
        l**2 / c**2 -
        2.0 * h * l * cos_b / (a * c)
    )
    if denom <= 0:
        return float('inf')
    return 1.0 / math.sqrt(denom)


def d_spacing_triclinic(h, k, l, a, b, c, alpha_rad, beta_rad, gamma_rad):
    cos_a = math.cos(alpha_rad)
    cos_b = math.cos(beta_rad)
    cos_g = math.cos(gamma_rad)
    sin_a = math.sin(alpha_rad)
    sin_b = math.sin(beta_rad)
    sin_g = math.sin(gamma_rad)
    V_sq = a**2 * b**2 * c**2 * (
        1.0 - cos_a**2 - cos_b**2 - cos_g**2 + 2.0*cos_a*cos_b*cos_g
    )
    if V_sq <= 0:
        return float('inf')
    s11 = b**2 * c**2 * sin_a**2
    s22 = a**2 * c**2 * sin_b**2
    s33 = a**2 * b**2 * sin_g**2
    s12 = a * b * c**2 * (cos_a * cos_b - cos_g)
    s23 = a**2 * b * c * (cos_b * cos_g - cos_a)
    s13 = a * b**2 * c * (cos_g * cos_a - cos_b)
    inv_d_sq = (
        s11 * h**2 + s22 * k**2 + s33 * l**2 +
        2.0 * s12 * h * k + 2.0 * s23 * k * l + 2.0 * s13 * h * l
    ) / V_sq
    if inv_d_sq <= 0:
        return float('inf')
    return 1.0 / math.sqrt(inv_d_sq)


def calc_d_spacing(h, k, l, crystal_system, a, b, c, alpha, beta, gamma):
    """Calcula d-spacing para qualquer sistema cristalino."""
    alpha_rad = math.radians(alpha)
    beta_rad = math.radians(beta)
    gamma_rad = math.radians(gamma)
    if crystal_system == 'cubic':
        return d_spacing_cubic(h, k, l, a)
    elif crystal_system == 'tetragonal':
        return d_spacing_tetragonal(h, k, l, a, c)
    elif crystal_system == 'orthorhombic':
        return d_spacing_orthorhombic(h, k, l, a, b, c)
    elif crystal_system == 'hexagonal':
        return d_spacing_hexagonal(h, k, l, a, c)
    elif crystal_system in ('trigonal', 'rhombohedral'):
        if abs(a - c) < 0.01 and abs(alpha - 90.0) > 0.1:
            return d_spacing_rhombohedral(h, k, l, a, alpha_rad)
        else:
            return d_spacing_hexagonal(h, k, l, a, c)
    elif crystal_system == 'monoclinic':
        return d_spacing_monoclinic(h, k, l, a, b, c, beta_rad)
    else:
        return d_spacing_triclinic(h, k, l, a, b, c, alpha_rad, beta_rad, gamma_rad)


def two_theta_from_d(d, wavelength):
    """Calcula 2theta a partir do espacamento d e comprimento de onda."""
    if d <= 0 or d == float('inf'):
        return None
    sin_theta = wavelength / (2.0 * d)
    if abs(sin_theta) > 1.0:
        return None
    return 2.0 * math.degrees(math.asin(sin_theta))


# ============================================================================
# OBTENCAO DE REFLEXOES REAIS VIA PYMATGEN (CHAVE DA MELHORIA v2)
# ============================================================================

def get_real_reflections_from_structure(cif_handler, wavelength, max_2theta=100.0,
                                        min_intensity_pct=0.5):
    """
    Obtem reflexoes REAIS a partir da estrutura usando pymatgen XRDCalculator.
    Usa o fator de estrutura e aplica extincoes sistematicas do grupo espacial.
    """
    try:
        from pymatgen.analysis.diffraction.xrd import XRDCalculator

        structure = cif_handler.get_structure()
        if structure is None:
            return []

        if abs(wavelength - 1.5406) < 0.01:
            radiation = "CuKa"
        elif abs(wavelength - 0.7107) < 0.01:
            radiation = "MoKa"
        elif abs(wavelength - 1.7902) < 0.01:
            radiation = "CoKa"
        else:
            radiation = "CuKa"

        calculator = XRDCalculator(wavelength=radiation)
        pattern = calculator.get_pattern(structure, two_theta_range=(0, max_2theta))

        reflections = []
        max_int = max(pattern.y) if len(pattern.y) > 0 else 100.0

        for i in range(len(pattern.x)):
            tt = float(pattern.x[i])
            intensity = float(pattern.y[i])
            rel_intensity = (intensity / max_int) * 100.0

            if rel_intensity < min_intensity_pct:
                continue

            hkl = None
            if hasattr(pattern, 'hkls') and i < len(pattern.hkls):
                hkl_info = pattern.hkls[i]
                if hkl_info:
                    first_hkl = list(hkl_info[0].keys())[0] if hkl_info else None
                    if first_hkl is not None:
                        hkl = tuple(int(x) for x in first_hkl)

            d_val = 0.0
            if tt > 0:
                d_val = float(wavelength / (2.0 * math.sin(math.radians(tt / 2.0))))

            reflections.append({
                'two_theta': tt,
                'intensity': rel_intensity,
                'hkl': hkl,
                'd_spacing': d_val
            })

        reflections.sort(key=lambda r: r['two_theta'])
        logger.info(f"Obtidas {len(reflections)} reflexoes reais via XRDCalculator")
        return reflections

    except Exception as e:
        logger.warning(f"Falha ao obter reflexoes via XRDCalculator: {e}")
        return []


# ============================================================================
# GERACAO DE REFLEXOES (hkl) - FALLBACK GEOMETRICO
# ============================================================================

def generate_hkl_list(crystal_system, max_index=10):
    """Gera lista de reflexoes (hkl) unicas (FALLBACK sem extincoes)."""
    hkl_set = set()
    for h in range(-max_index, max_index + 1):
        for k in range(-max_index, max_index + 1):
            for l_val in range(-max_index, max_index + 1):
                if h == 0 and k == 0 and l_val == 0:
                    continue
                hkl = _canonical_hkl(h, k, l_val)
                hkl_set.add(hkl)
    return sorted(hkl_set)


def _canonical_hkl(h, k, l):
    for idx in [h, k, l]:
        if idx != 0:
            if idx < 0:
                return (-h, -k, -l)
            else:
                return (h, k, l)
    return (h, k, l)


def get_theoretical_peaks(crystal_system, a, b, c, alpha, beta, gamma,
                          wavelength, max_2theta=100.0, max_index=8):
    """Calcula posicoes 2theta teoricas (FALLBACK geometrico)."""
    hkl_list = generate_hkl_list(crystal_system, max_index)
    peaks = []
    seen_2theta = set()
    for h, k, l in hkl_list:
        d = calc_d_spacing(h, k, l, crystal_system, a, b, c, alpha, beta, gamma)
        tt = two_theta_from_d(d, wavelength)
        if tt is not None and 0 < tt <= max_2theta:
            tt_rounded = round(tt, 3)
            if tt_rounded not in seen_2theta:
                seen_2theta.add(tt_rounded)
                peaks.append((tt, (h, k, l)))
    peaks.sort(key=lambda x: x[0])
    return peaks


# ============================================================================
# DETECCAO DE PICOS NO EXPERIMENTAL
# ============================================================================

def detect_experimental_peaks(two_theta, intensities, prominence_factor=0.05,
                              min_distance_deg=0.3, min_intensity_pct=2.0):
    """Detecta picos no difratograma experimental usando scipy.signal.find_peaks."""
    if len(two_theta) < 10 or len(intensities) < 10:
        return []
    step = abs(two_theta[1] - two_theta[0]) if len(two_theta) > 1 else 0.02
    min_distance_pts = max(1, int(min_distance_deg / step))
    max_intensity = np.max(intensities)
    min_prominence = max_intensity * prominence_factor
    min_height = max_intensity * (min_intensity_pct / 100.0)
    peak_indices, _ = find_peaks(
        intensities, distance=min_distance_pts,
        prominence=min_prominence, height=min_height
    )
    peaks = []
    for idx in peak_indices:
        peaks.append({
            'two_theta': float(two_theta[idx]),
            'intensity': float(intensities[idx]),
            'index': int(idx)
        })
    peaks.sort(key=lambda p: p['intensity'], reverse=True)
    logger.info(f"Detectados {len(peaks)} picos no experimental")
    return peaks


# ============================================================================
# CORRESPONDENCIA BIDIRECIONAL DE PICOS (MELHORIA v2)
# ============================================================================

def _match_peaks_greedy(obs_2theta, calc_reflections, max_delta=2.0):
    """Correspondencia greedy 1:1 entre picos observados e calculados."""
    if not calc_reflections or len(obs_2theta) == 0:
        return []
    calc_2theta = np.array([r['two_theta'] for r in calc_reflections])
    used_calc = set()
    matches = []
    for obs_idx in range(len(obs_2theta)):
        obs_tt = float(obs_2theta[obs_idx])
        best_calc_idx = -1
        best_delta = float('inf')
        for calc_idx in range(len(calc_2theta)):
            if calc_idx in used_calc:
                continue
            delta = abs(obs_tt - calc_2theta[calc_idx])
            if delta < best_delta and delta < max_delta:
                best_delta = delta
                best_calc_idx = calc_idx
        if best_calc_idx >= 0:
            used_calc.add(best_calc_idx)
            matches.append((obs_idx, best_calc_idx, best_delta))
        else:
            matches.append((obs_idx, -1, float('inf')))
    return matches


# ============================================================================
# FUNCAO CUSTO (MELHORADA v2)
# ============================================================================

def _cost_function(params, crystal_system, ref_hkl_list, obs_peaks_2theta,
                   obs_peaks_weights, wavelength, original_params):
    """Funcao custo: usa apenas reflexoes reais."""
    a, b, c, alpha, beta, gamma = _expand_params(params, crystal_system, original_params)
    calc_positions = []
    for hkl in ref_hkl_list:
        h, k, l = hkl
        d = calc_d_spacing(h, k, l, crystal_system, a, b, c, alpha, beta, gamma)
        tt = two_theta_from_d(d, wavelength)
        if tt is not None:
            calc_positions.append(tt)
        else:
            calc_positions.append(999.0)
    if not calc_positions:
        return 1e10
    calc_2theta = np.array(calc_positions)
    total_cost = 0.0
    for i in range(len(obs_peaks_2theta)):
        obs_tt = float(obs_peaks_2theta[i])
        distances = np.abs(calc_2theta - obs_tt)
        min_dist = float(np.min(distances))
        if min_dist > 1.0:
            cost_i = float(obs_peaks_weights[i]) * (1.0 + (min_dist - 1.0) * 0.5)
        else:
            cost_i = float(obs_peaks_weights[i]) * min_dist ** 2
        total_cost += cost_i
    return total_cost


def _expand_params(free_params, crystal_system, original_params):
    """Expande parametros livres para (a, b, c, alpha, beta, gamma)."""
    a0, b0, c0, alpha0, beta0, gamma0 = original_params
    if crystal_system == 'cubic':
        a = free_params[0]
        return a, a, a, 90.0, 90.0, 90.0
    elif crystal_system == 'tetragonal':
        a, c = free_params[0], free_params[1]
        return a, a, c, 90.0, 90.0, 90.0
    elif crystal_system == 'orthorhombic':
        a, b, c = free_params[0], free_params[1], free_params[2]
        return a, b, c, 90.0, 90.0, 90.0
    elif crystal_system == 'hexagonal':
        a, c = free_params[0], free_params[1]
        return a, a, c, 90.0, 90.0, 120.0
    elif crystal_system in ('trigonal', 'rhombohedral'):
        is_rhombohedral = (abs(a0 - c0) < 0.01 and abs(alpha0 - 90.0) > 0.1)
        if is_rhombohedral:
            a, alpha = free_params[0], free_params[1]
            return a, a, a, alpha, alpha, alpha
        else:
            a, c = free_params[0], free_params[1]
            return a, a, c, 90.0, 90.0, 120.0
    elif crystal_system == 'monoclinic':
        a, b, c, beta = free_params[0], free_params[1], free_params[2], free_params[3]
        return a, b, c, 90.0, beta, 90.0
    else:
        return tuple(free_params[:6])


def _extract_free_params(crystal_system, a, b, c, alpha, beta, gamma):
    """Extrai parametros livres de acordo com o sistema cristalino."""
    if crystal_system == 'cubic':
        return [a]
    elif crystal_system == 'tetragonal':
        return [a, c]
    elif crystal_system == 'orthorhombic':
        return [a, b, c]
    elif crystal_system == 'hexagonal':
        return [a, c]
    elif crystal_system in ('trigonal', 'rhombohedral'):
        is_rhombohedral = (abs(a - c) < 0.01 and abs(alpha - 90.0) > 0.1)
        if is_rhombohedral:
            return [a, alpha]
        else:
            return [a, c]
    elif crystal_system == 'monoclinic':
        return [a, b, c, beta]
    else:
        return [a, b, c, alpha, beta, gamma]


def _get_param_bounds(free_params, crystal_system, max_variation_pct=5.0):
    """Calcula limites (bounds) para cada parametro livre."""
    bounds = []
    frac = max_variation_pct / 100.0
    for i, val in enumerate(free_params):
        is_angle = False
        if crystal_system == 'monoclinic' and i == 3:
            is_angle = True
        elif crystal_system == 'triclinic' and i >= 3:
            is_angle = True
        elif crystal_system in ('trigonal', 'rhombohedral') and i == 1:
            is_angle = True
        if is_angle:
            low = max(val * (1 - frac), 60.0)
            high = min(val * (1 + frac), 150.0)
        else:
            low = max(val * (1 - frac), 0.1)
            high = val * (1 + frac)
        bounds.append((low, high))
    return bounds


def _get_param_names(crystal_system, a, b, c, alpha, beta, gamma):
    """Retorna nomes dos parametros livres."""
    if crystal_system == 'cubic':
        return ['a']
    elif crystal_system == 'tetragonal':
        return ['a', 'c']
    elif crystal_system == 'orthorhombic':
        return ['a', 'b', 'c']
    elif crystal_system == 'hexagonal':
        return ['a', 'c']
    elif crystal_system in ('trigonal', 'rhombohedral'):
        is_rhombohedral = (abs(a - c) < 0.01 and abs(alpha - 90.0) > 0.1)
        if is_rhombohedral:
            return ['a', 'alpha']
        else:
            return ['a', 'c']
    elif crystal_system == 'monoclinic':
        return ['a', 'b', 'c', 'beta']
    else:
        return ['a', 'b', 'c', 'alpha', 'beta', 'gamma']


# ============================================================================
# FUNCAO PRINCIPAL DE AUTO-AJUSTE (v2 - COM REFLEXOES REAIS)
# ============================================================================

def auto_fit_lattice(crystal_system, a, b, c, alpha, beta, gamma,
                     wavelength, obs_peaks, max_variation_pct=5.0,
                     max_2theta=100.0, cif_handler=None):
    """
    Ajusta automaticamente os parametros de rede para minimizar a diferenca
    entre posicoes de pico observadas e calculadas.

    MELHORIA v2: Se cif_handler e fornecido, usa reflexoes reais (com fator
    de estrutura) do XRDCalculator. Senao, usa metodo geometrico como fallback.
    """
    if not obs_peaks:
        return {'success': False, 'message': 'Nenhum pico observado fornecido.'}

    logger.info(f"Iniciando auto-ajuste v2: {crystal_system}, "
                f"a={a:.4f}, b={b:.4f}, c={c:.4f}, "
                f"wavelength={wavelength:.5f} A, {len(obs_peaks)} picos")

    obs_2theta = np.array([p['two_theta'] for p in obs_peaks])
    obs_intensity = np.array([p['intensity'] for p in obs_peaks])

    max_int = float(np.max(obs_intensity)) if float(np.max(obs_intensity)) > 0 else 1.0
    weights = np.sqrt(obs_intensity / max_int)
    weights = weights / float(np.sum(weights)) * len(weights)

    original_params = (a, b, c, alpha, beta, gamma)

    # --- OBTER REFLEXOES DE REFERENCIA ---
    real_reflections = []
    if cif_handler is not None:
        real_reflections = get_real_reflections_from_structure(
            cif_handler, wavelength, max_2theta=max_2theta, min_intensity_pct=0.5
        )

    if real_reflections:
        ref_hkl_list = [r['hkl'] for r in real_reflections if r['hkl'] is not None]
        logger.info(f"Usando {len(ref_hkl_list)} reflexoes reais do XRDCalculator")
    else:
        logger.info("Usando metodo geometrico (fallback)")
        theoretical = get_theoretical_peaks(
            crystal_system, a, b, c, alpha, beta, gamma,
            wavelength, max_2theta=max_2theta, max_index=8
        )
        ref_hkl_list = [hkl for _, hkl in theoretical]

    if not ref_hkl_list:
        return {'success': False, 'message': 'Nenhuma reflexao de referencia disponivel.'}

    free_params = _extract_free_params(crystal_system, a, b, c, alpha, beta, gamma)
    param_names = _get_param_names(crystal_system, a, b, c, alpha, beta, gamma)

    cost_before = _cost_function(
        free_params, crystal_system, ref_hkl_list, obs_2theta,
        weights, wavelength, original_params
    )

    bounds = _get_param_bounds(free_params, crystal_system, max_variation_pct)

    logger.info(f"Parametros livres: {dict(zip(param_names, free_params))}")
    logger.info(f"Custo inicial: {cost_before:.6f}")

    # --- OTIMIZACAO ---
    result = minimize(
        _cost_function,
        x0=free_params,
        args=(crystal_system, ref_hkl_list, obs_2theta, weights, wavelength, original_params),
        method='L-BFGS-B',
        bounds=bounds,
        options={'maxiter': 2000, 'ftol': 1e-14, 'gtol': 1e-10}
    )

    opt_params = result.x
    a_opt, b_opt, c_opt, alpha_opt, beta_opt, gamma_opt = _expand_params(
        opt_params, crystal_system, original_params
    )
    cost_after = float(result.fun)

    from pymatgen.core import Lattice
    vol_before = Lattice.from_parameters(a, b, c, alpha, beta, gamma).volume
    vol_after = Lattice.from_parameters(a_opt, b_opt, c_opt, alpha_opt, beta_opt, gamma_opt).volume

    # --- CORRESPONDENCIA FINAL com greedy matching ---
    calc_after = []
    for hkl in ref_hkl_list:
        h, k, l = hkl
        d = calc_d_spacing(h, k, l, crystal_system,
                           a_opt, b_opt, c_opt, alpha_opt, beta_opt, gamma_opt)
        tt = two_theta_from_d(d, wavelength)
        if tt is not None:
            calc_after.append({'two_theta': tt, 'hkl': hkl})

    matches = _match_peaks_greedy(obs_2theta, calc_after, max_delta=1.0)

    residuals = []
    n_matched = 0
    for obs_idx, calc_idx, delta in matches:
        matched_hkl = calc_after[calc_idx]['hkl'] if calc_idx >= 0 else None
        calc_tt = calc_after[calc_idx]['two_theta'] if calc_idx >= 0 else None
        if delta < 0.5:
            n_matched += 1
        residuals.append({
            'obs_2theta': float(obs_2theta[obs_idx]),
            'calc_2theta': float(calc_tt) if calc_tt is not None else None,
            'delta_2theta': float(delta) if delta != float('inf') else 999.0,
            'hkl': matched_hkl,
            'weight': float(weights[obs_idx]),
            'intensity': float(obs_intensity[obs_idx])
        })

    # Variacoes %
    param_changes = {}
    before_vals = {'a': a, 'b': b, 'c': c, 'alpha': alpha, 'beta': beta, 'gamma': gamma}
    after_vals = {'a': a_opt, 'b': b_opt, 'c': c_opt,
                  'alpha': alpha_opt, 'beta': beta_opt, 'gamma': gamma_opt}
    for key in before_vals:
        if before_vals[key] != 0:
            change_pct = ((after_vals[key] - before_vals[key]) / before_vals[key]) * 100.0
        else:
            change_pct = 0.0
        param_changes[key] = change_pct
    param_changes['volume'] = ((vol_after - vol_before) / vol_before) * 100.0 if vol_before > 0 else 0.0

    improvement = ((cost_before - cost_after) / cost_before * 100.0) if cost_before > 0 else 0.0
    msg = (ptr("Ajuste concluido: {}/{} picos correspondidos. Erro reduzido em {:.1f}%.").format(n_matched, len(obs_peaks), improvement))

    logger.info(f"Auto-ajuste v2 concluido: {msg}")
    logger.info(f"  Antes:  a={a:.5f}, b={b:.5f}, c={c:.5f}, V={vol_before:.3f}")
    logger.info(f"  Depois: a={a_opt:.5f}, b={b_opt:.5f}, c={c_opt:.5f}, V={vol_after:.3f}")

    return {
        'success': result.success or cost_after < cost_before,
        'params_before': {
            'a': a, 'b': b, 'c': c,
            'alpha': alpha, 'beta': beta, 'gamma': gamma,
            'volume': vol_before
        },
        'params_after': {
            'a': a_opt, 'b': b_opt, 'c': c_opt,
            'alpha': alpha_opt, 'beta': beta_opt, 'gamma': gamma_opt,
            'volume': vol_after
        },
        'param_changes': param_changes,
        'cost_before': float(cost_before),
        'cost_after': float(cost_after),
        'n_peaks_matched': n_matched,
        'n_peaks_total': len(obs_peaks),
        'residuals': residuals,
        'message': msg,
        'optimizer_message': result.message if hasattr(result, 'message') else '',
        'real_reflections': real_reflections
    }
