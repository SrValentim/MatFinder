# -*- coding: utf-8 -*-
"""Linhas de emissão característica dos tubos de raios X (Kα1 e Kβ1).

Usado pela aba de simulação do PhaseDRX: o usuário escolhe quais linhas do tubo
entram no padrão calculado (Kα, Kβ ou as duas). O padrão de cada linha é somado
com o peso relativo da linha sobre intensidades ABSOLUTAS (sem normalizar cada
padrão), para que a razão entre os picos de Kα e de Kβ seja física. Quem chama
normaliza o padrão final.
"""

import numpy as np

# Comprimentos de onda em Å.
# - Kα1 ("ka"): os mesmos valores do seletor "Fonte de Radiação Padrão" do PhaseDRX.
# - Kα2 ("ka2") e Kβ1 ("kb"): os valores da tabela WAVELENGTHS do pymatgen.
ANODE_LINES = {
    "Cu": {"ka": 1.54056, "ka2": 1.54439, "kb": 1.39222},
    "Co": {"ka": 1.78897, "ka2": 1.79285, "kb": 1.63079},
    "Fe": {"ka": 1.93604, "ka2": 1.93998, "kb": 1.75661},
    "Mo": {"ka": 0.70930, "ka2": 0.71359, "kb": 0.63229},
}

# Intensidade de Kα2 relativa a Kα1 (razão padrão usada em XRD de laboratório).
KA2_TO_KA1_RATIO = 0.5

# Intensidade de Kβ1 relativa a Kα1, aproximada, para tubo SEM filtro de Kβ e
# sem monocromador. Vem da razão Kβ/Kα total da emissão (~0,14 para Fe, Co e Cu;
# ~0,19 para Mo) multiplicada por ~1,5, porque o Kα1 responde por ~2/3 do Kα.
# Com filtro de Ni (tubo de Cu) a razão real cai para ~1% ou menos.
KB_TO_KA1_RATIO = {"Cu": 0.20, "Co": 0.20, "Fe": 0.20, "Mo": 0.29}


def radiation_lines(anode=None, use_ka=True, use_kb=False, custom_wavelength=None):
    """Lista de (comprimento de onda em Å, peso relativo) das linhas a simular.

    Args:
        anode: "Cu", "Co", "Fe" ou "Mo".
        use_ka: inclui a linha Kα1 (peso 1).
        use_kb: inclui a linha Kβ1 (peso KB_TO_KA1_RATIO do ânodo).
        custom_wavelength: comprimento de onda livre (ex.: síncrotron). Quando
            informado, simula só esse valor e as opções Kα/Kβ não se aplicam.

    Raises:
        ValueError: nenhuma linha escolhida, ânodo desconhecido ou comprimento
            de onda personalizado inválido.
    """
    if custom_wavelength is not None:
        wavelength = float(custom_wavelength)
        if not np.isfinite(wavelength) or wavelength <= 0:
            raise ValueError(f"Comprimento de onda inválido: {custom_wavelength!r}")
        return [(wavelength, 1.0)]

    if anode not in ANODE_LINES:
        raise ValueError(f"Ânodo desconhecido: {anode!r}")
    if not (use_ka or use_kb):
        raise ValueError("Selecione pelo menos uma linha de emissão (Kα ou Kβ).")

    lines = []
    if use_ka:
        lines.append((ANODE_LINES[anode]["ka"], 1.0))
    if use_kb:
        lines.append((ANODE_LINES[anode]["kb"], KB_TO_KA1_RATIO[anode]))
    return lines


def same_d_two_theta(two_theta, wavelength_from, wavelength_to):
    """2θ (graus) da mesma distância interplanar d medida com outro comprimento de onda.

    Usado para prever onde cai o Kα2 (ou o Kβ) de um pico de Kα1. Devolve NaN
    quando a reflexão não existe no outro comprimento de onda (sen θ > 1).
    """
    theta = np.radians(np.asarray(two_theta, dtype=float) / 2.0)
    ratio = np.sin(theta) * (float(wavelength_to) / float(wavelength_from))
    with np.errstate(invalid="ignore"):
        out = 2.0 * np.degrees(np.arcsin(np.where(np.abs(ratio) <= 1.0, ratio, np.nan)))
    return float(out) if np.ndim(out) == 0 else out


def combined_sticks(structure, lines, max_2theta):
    """Picos de difração (2θ, intensidade) somando todas as linhas de emissão.

    Cada linha é calculada com o XRDCalculator do pymatgen em escala absoluta
    (scaled=False) e multiplicada pelo seu peso. Com uma única linha, o
    resultado é o padrão do pymatgen a menos de um fator de escala global.

    Args:
        structure: pymatgen Structure.
        lines: lista de (comprimento de onda em Å, peso), ex.: radiation_lines().
        max_2theta: limite superior de 2θ em graus.

    Returns:
        (two_theta, intensity): arrays numpy ordenados por 2θ.
    """
    from pymatgen.analysis.diffraction.xrd import XRDCalculator

    if not lines:
        raise ValueError("Nenhuma linha de emissão para simular.")

    all_x, all_y = [], []
    for wavelength, weight in lines:
        pattern = XRDCalculator(wavelength=wavelength).get_pattern(
            structure, scaled=False, two_theta_range=(0, max_2theta))
        all_x.append(np.asarray(pattern.x, dtype=float))
        all_y.append(np.asarray(pattern.y, dtype=float) * float(weight))

    two_theta = np.concatenate(all_x)
    intensity = np.concatenate(all_y)
    order = np.argsort(two_theta, kind="stable")
    return two_theta[order], intensity[order]
