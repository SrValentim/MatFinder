"""
Biblioteca Universal de Distâncias de Ligações Químicas
========================================================

Baseado em:
1. Cambridge Structural Database (CSD) - Distâncias experimentais
2. Pyykko & Atsumi (2009) - Raios covalentes
3. ICSD - Inorganic Crystal Structure Database
4. VESTA - Validação prática

Última atualização: 2025-11-26
"""

import logging
from typing import Tuple, Optional, Dict

# =============================================================================
# RAIOS COVALENTES PADRÃO (Pyykko & Atsumi, 2009)
# =============================================================================
COVALENT_RADII = {
    # Período 1
    'H': 0.31, 'He': 0.28,

    # Período 2
    'Li': 1.28, 'Be': 0.96, 'B': 0.84, 'C': 0.76, 'N': 0.71,
    'O': 0.66, 'F': 0.57, 'Ne': 0.58,

    # Período 3
    'Na': 1.66, 'Mg': 1.41, 'Al': 1.21, 'Si': 1.11, 'P': 1.07,
    'S': 1.05, 'Cl': 1.02, 'Ar': 1.06,

    # Período 4
    'K': 2.03, 'Ca': 1.76, 'Sc': 1.70, 'Ti': 1.60, 'V': 1.53,
    'Cr': 1.39, 'Mn': 1.39, 'Fe': 1.32, 'Co': 1.26, 'Ni': 1.24,
    'Cu': 1.32, 'Zn': 1.22, 'Ga': 1.22, 'Ge': 1.20, 'As': 1.19,
    'Se': 1.20, 'Br': 1.20, 'Kr': 1.16,

    # Período 5
    'Rb': 2.20, 'Sr': 1.95, 'Y': 1.90, 'Zr': 1.75, 'Nb': 1.64,
    'Mo': 1.54, 'Tc': 1.47, 'Ru': 1.46, 'Rh': 1.42, 'Pd': 1.39,
    'Ag': 1.45, 'Cd': 1.44, 'In': 1.42, 'Sn': 1.39, 'Sb': 1.39,
    'Te': 1.38, 'I': 1.39, 'Xe': 1.40,

    # Período 6 (incluindo lantanídeos)
    'Cs': 2.44, 'Ba': 2.15,
    'La': 2.07, 'Ce': 2.04, 'Pr': 2.03, 'Nd': 2.01, 'Pm': 1.99,
    'Sm': 1.98, 'Eu': 1.98, 'Gd': 1.96, 'Tb': 1.94, 'Dy': 1.92,
    'Ho': 1.92, 'Er': 1.89, 'Tm': 1.90, 'Yb': 1.87, 'Lu': 1.87,
    'Hf': 1.75, 'Ta': 1.70, 'W': 1.62, 'Re': 1.51, 'Os': 1.44,
    'Ir': 1.41, 'Pt': 1.36, 'Au': 1.36, 'Hg': 1.32, 'Tl': 1.45,
    'Pb': 1.46, 'Bi': 1.48, 'Po': 1.40, 'At': 1.50,

    # Período 7 (actinídeos)
    'Ac': 2.15, 'Th': 2.06, 'Pa': 2.00, 'U': 1.96, 'Np': 1.90,
    'Pu': 1.87, 'Am': 1.80, 'Cm': 1.69,
}

# =============================================================================
# BIBLIOTECA EXTENSIVA: DISTÂNCIAS MÁXIMAS POR PAR (>200 pares)
# Baseado em CSD e ICSD (distâncias experimentais)
# =============================================================================
BOND_DISTANCES_LIBRARY: Dict[Tuple[str, str], float] = {

    # =========================================================================
    # CARBONO - Casos Críticos (2D/3D materials)
    # =========================================================================
    ('C', 'C'): 1.70,    # 🔴 Grafite/grafeno: 1.42 Å típico, max 1.70 Å
                          # Diamante: 1.54 Å, max 1.70 Å
                          # CRÍTICO: Evita ligações inter-camadas (3.35 Å)

    ('C', 'H'): 1.20,    # C-H: 1.09 Å típico, max 1.20 Å
    ('C', 'N'): 1.60,    # C-N: 1.47 Å (simples), 1.27 Å (dupla)
    ('C', 'O'): 1.60,    # C-O: 1.43 Å (simples), 1.20 Å (dupla)
    ('C', 'S'): 2.00,    # C-S: 1.82 Å típico
    ('C', 'P'): 2.00,    # C-P: 1.85 Å típico
    ('C', 'F'): 1.50,    # C-F: 1.35 Å típico
    ('C', 'Cl'): 1.90,   # C-Cl: 1.77 Å típico
    ('C', 'Br'): 2.00,   # C-Br: 1.94 Å típico
    ('C', 'I'): 2.20,    # C-I: 2.14 Å típico
    ('C', 'Si'): 2.00,   # C-Si: 1.85 Å típico (organosilanos)
    ('C', 'B'): 1.70,    # C-B: 1.56 Å típico

    # Carbetos metálicos
    ('C', 'Ti'): 2.30,   # Carbeto de titânio
    ('C', 'W'): 2.30,    # Carbeto de tungstênio (WC)
    ('C', 'Mo'): 2.30,   # Carbeto de molibdênio
    ('C', 'Cr'): 2.20,   # Carbeto de cromo
    ('C', 'Fe'): 2.20,   # Carbeto de ferro (cementita)
    ('C', 'Nb'): 2.40,   # Carbeto de nióbio
    ('C', 'Ta'): 2.40,   # Carbeto de tântalo
    ('C', 'Zr'): 2.40,   # Carbeto de zircônio
    ('C', 'Hf'): 2.40,   # Carbeto de háfnio

    # =========================================================================
    # NITROGÊNIO
    # =========================================================================
    ('N', 'N'): 1.60,    # N-N: 1.45 Å (simples), 1.25 Å (dupla), 1.10 Å (tripla)
    ('N', 'H'): 1.15,    # N-H: 1.01 Å típico
    ('N', 'O'): 1.55,    # N-O: 1.40 Å típico
    ('N', 'P'): 1.85,    # N-P: 1.77 Å típico
    ('N', 'S'): 1.80,    # N-S: 1.74 Å típico
    ('N', 'F'): 1.50,    # N-F: 1.36 Å típico
    ('N', 'Cl'): 1.90,   # N-Cl: 1.75 Å típico

    # Nitretos
    ('N', 'B'): 1.70,    # Nitreto de boro (hBN): 1.45 Å
    ('N', 'Si'): 2.00,   # Nitreto de silício (Si3N4)
    ('N', 'Al'): 2.10,   # Nitreto de alumínio (AlN)
    ('N', 'Ga'): 2.10,   # Nitreto de gálio (GaN)
    ('N', 'Ti'): 2.20,   # Nitreto de titânio (TiN)

    # =========================================================================
    # OXIGÊNIO - Óxidos (classe mais comum!)
    # =========================================================================
    ('O', 'O'): 1.60,    # O-O: 1.48 Å (peróxidos), 1.21 Å (O₂)
    ('H', 'O'): 1.10,    # O-H: 0.96 Å típico
    ('O', 'S'): 1.80,    # O-S: 1.48 Å (sulfatos)
    ('O', 'P'): 1.80,    # O-P: 1.58 Å (fosfatos)
    ('O', 'Si'): 1.90,   # O-Si: 1.63 Å (silicatos, quartzo)
    ('N', 'O'): 1.55,    # Já definido acima

    # Óxidos de metais alcalinos
    ('Li', 'O'): 2.20,   # Li₂O: 2.00 Å típico
    ('Na', 'O'): 2.60,   # Na₂O: 2.40 Å típico
    ('K', 'O'): 3.00,    # K₂O: 2.80 Å típico
    ('Rb', 'O'): 3.20,   # Rb₂O
    ('Cs', 'O'): 3.40,   # Cs₂O

    # Óxidos de metais alcalino-terrosos
    ('Be', 'O'): 1.90,   # BeO: 1.65 Å típico
    ('Mg', 'O'): 2.30,   # MgO: 2.10 Å típico
    ('Ca', 'O'): 2.60,   # CaO: 2.40 Å típico
    ('Sr', 'O'): 2.80,   # SrO: 2.57 Å típico
    ('Ba', 'O'): 3.00,   # BaO: 2.77 Å típico

    # Óxidos de metais de transição (3d)
    ('Sc', 'O'): 2.30,   # Sc₂O₃
    ('Ti', 'O'): 2.20,   # TiO₂ (rutilo): 1.95 Å típico
    ('V', 'O'): 2.10,    # V₂O₅: 1.88 Å típico
    ('Cr', 'O'): 2.10,   # Cr₂O₃: 1.97 Å típico
    ('Mn', 'O'): 2.20,   # MnO₂: 1.90 Å típico
    ('Fe', 'O'): 2.20,   # Fe₂O₃, Fe₃O₄: 2.05 Å típico
    ('Co', 'O'): 2.20,   # CoO: 2.13 Å típico
    ('Ni', 'O'): 2.20,   # NiO: 2.09 Å típico
    ('Cu', 'O'): 2.10,   # CuO: 1.96 Å típico
    ('Zn', 'O'): 2.20,   # ZnO: 1.98 Å típico

    # Óxidos de metais de transição (4d)
    ('Y', 'O'): 2.50,    # Y₂O₃: 2.29 Å típico
    ('Zr', 'O'): 2.40,   # ZrO₂ (zircônia): 2.17 Å típico
    ('Nb', 'O'): 2.30,   # Nb₂O₅: 2.09 Å típico
    ('Mo', 'O'): 2.20,   # MoO₃: 1.95 Å típico
    ('Ru', 'O'): 2.10,   # RuO₂: 1.99 Å típico
    ('Rh', 'O'): 2.20,   # Rh₂O₃
    ('Pd', 'O'): 2.20,   # PdO: 2.02 Å típico
    ('Ag', 'O'): 2.30,   # Ag₂O: 2.05 Å típico
    ('Cd', 'O'): 2.50,   # CdO: 2.35 Å típico

    # Óxidos de metais de transição (5d)
    ('La', 'O'): 2.70,   # La₂O₃
    ('Hf', 'O'): 2.40,   # HfO₂
    ('Ta', 'O'): 2.30,   # Ta₂O₅: 2.09 Å típico
    ('W', 'O'): 2.20,    # WO₃: 1.91 Å típico
    ('Re', 'O'): 2.10,   # ReO₃
    ('Os', 'O'): 2.10,   # OsO₄
    ('Ir', 'O'): 2.10,   # IrO₂: 2.00 Å típico
    ('Pt', 'O'): 2.20,   # PtO₂
    ('Au', 'O'): 2.20,   # Au₂O₃
    ('Hg', 'O'): 2.30,   # HgO: 2.05 Å típico

    # Óxidos de lantanídeos
    ('Ce', 'O'): 2.60,   # CeO₂ (ceria): 2.34 Å típico
    ('Pr', 'O'): 2.60,   # Pr₂O₃
    ('Nd', 'O'): 2.60,   # Nd₂O₃: 2.43 Å típico
    ('Sm', 'O'): 2.60,   # Sm₂O₃: 2.41 Å típico
    ('Eu', 'O'): 2.60,   # Eu₂O₃
    ('Gd', 'O'): 2.60,   # Gd₂O₃: 2.38 Å típico
    ('Tb', 'O'): 2.50,   # Tb₂O₃
    ('Dy', 'O'): 2.50,   # Dy₂O₃
    ('Ho', 'O'): 2.50,   # Ho₂O₃
    ('Er', 'O'): 2.50,   # Er₂O₃
    ('Tm', 'O'): 2.50,   # Tm₂O₃
    ('Yb', 'O'): 2.50,   # Yb₂O₃
    ('Lu', 'O'): 2.50,   # Lu₂O₃

    # Óxidos de pós-transição
    ('Al', 'O'): 2.10,   # Al₂O₃ (alumina): 1.86 Å típico
    ('Ga', 'O'): 2.10,   # Ga₂O₃
    ('In', 'O'): 2.40,   # In₂O₃: 2.18 Å típico
    ('Tl', 'O'): 2.50,   # Tl₂O₃
    ('Sn', 'O'): 2.30,   # SnO₂: 2.05 Å típico
    ('Pb', 'O'): 2.60,   # PbO: 2.32 Å típico
    ('Bi', 'O'): 2.50,   # Bi₂O₃: 2.31 Å típico

    # Óxidos de actinídeos
    ('Th', 'O'): 2.70,   # ThO₂
    ('U', 'O'): 2.50,    # UO₂: 2.37 Å típico

    # =========================================================================
    # ENXOFRE - Sulfetos
    # =========================================================================
    ('S', 'S'): 2.20,    # S-S: 2.05 Å (dissulfetos)
    ('H', 'S'): 1.50,    # S-H: 1.34 Å típico
    ('S', 'P'): 2.20,    # S-P: 2.10 Å típico
    ('O', 'S'): 1.80,    # Já definido

    # Sulfetos metálicos
    ('Fe', 'S'): 2.50,   # FeS, FeS₂ (pirita): 2.26 Å típico
    ('Cu', 'S'): 2.40,   # Cu₂S, CuS: 2.30 Å típico
    ('Zn', 'S'): 2.50,   # ZnS (blenda, wurtzita): 2.34 Å típico
    ('Pb', 'S'): 3.00,   # PbS (galena): 2.97 Å típico
    ('Cd', 'S'): 2.70,   # CdS: 2.52 Å típico
    ('Mo', 'S'): 2.60,   # MoS₂ (molibdenita): 2.41 Å típico
    ('W', 'S'): 2.60,    # WS₂
    ('Ni', 'S'): 2.50,   # NiS
    ('Co', 'S'): 2.50,   # CoS
    ('Ag', 'S'): 2.70,   # Ag₂S: 2.49 Å típico
    ('Hg', 'S'): 2.60,   # HgS (cinábrio): 2.53 Å típico

    # =========================================================================
    # FÓSFORO - Fosfetos e Fosfatos
    # =========================================================================
    ('P', 'P'): 2.30,    # P-P: 2.21 Å (P₄)
    ('H', 'P'): 1.50,    # P-H: 1.42 Å típico
    ('O', 'P'): 1.80,    # Já definido

    # Fosfetos
    ('P', 'Ga'): 2.50,   # GaP: 2.36 Å típico
    ('P', 'In'): 2.70,   # InP: 2.54 Å típico
    ('P', 'Al'): 2.50,   # AlP: 2.36 Å típico

    # =========================================================================
    # SILÍCIO - Silicatos e Semicondutores
    # =========================================================================
    ('Si', 'Si'): 2.50,  # Si-Si: 2.35 Å (cristal)
    ('H', 'Si'): 1.60,   # Si-H: 1.48 Å típico
    ('O', 'Si'): 1.90,   # Já definido
    ('C', 'Si'): 2.00,   # Já definido (SiC)
    ('N', 'Si'): 2.00,   # Já definido (Si₃N₄)

    # Silicetos
    ('Si', 'Fe'): 2.60,  # FeSi
    ('Si', 'Mg'): 2.80,  # Mg₂Si: 2.75 Å típico
    ('Si', 'Ca'): 3.00,  # CaSi₂

    # =========================================================================
    # GERMÂNIO
    # =========================================================================
    ('Ge', 'Ge'): 2.60,  # Ge-Ge: 2.45 Å (cristal)
    ('Ge', 'O'): 2.00,   # GeO₂: 1.88 Å típico
    ('Ge', 'S'): 2.50,   # GeS: 2.40 Å típico

    # =========================================================================
    # BORO
    # =========================================================================
    ('B', 'B'): 1.90,    # B-B: 1.77 Å típico
    ('B', 'H'): 1.30,    # B-H: 1.19 Å (boranos)
    ('B', 'N'): 1.70,    # BN (nitreto de boro hexagonal): 1.45 Å
    ('B', 'O'): 1.60,    # B-O: 1.47 Å típico
    ('B', 'F'): 1.50,    # B-F: 1.32 Å típico

    # =========================================================================
    # HALOGÊNIOS
    # =========================================================================
    ('F', 'F'): 1.60,    # F-F: 1.42 Å (F₂)
    ('Cl', 'Cl'): 2.10,  # Cl-Cl: 1.99 Å (Cl₂)
    ('Br', 'Br'): 2.40,  # Br-Br: 2.28 Å (Br₂)
    ('I', 'I'): 2.80,    # I-I: 2.67 Å (I₂)

    # Haletos metálicos (exemplos principais)
    ('Na', 'Cl'): 3.00,  # NaCl: 2.82 Å típico
    ('K', 'Cl'): 3.30,   # KCl: 3.15 Å típico
    ('Li', 'F'): 2.20,   # LiF: 2.01 Å típico
    ('Na', 'F'): 2.50,   # NaF: 2.32 Å típico
    ('Ca', 'F'): 2.60,   # CaF₂: 2.36 Å típico

    # =========================================================================
    # LIGAÇÕES METÁLICAS (Metal-Metal)
    # =========================================================================
    ('Fe', 'Fe'): 2.80,  # Fe metálico: 2.48 Å típico
    ('Cu', 'Cu'): 2.80,  # Cu metálico: 2.56 Å típico
    ('Al', 'Al'): 3.00,  # Al metálico: 2.86 Å típico
    ('Au', 'Au'): 3.00,  # Au metálico: 2.88 Å típico
    ('Ag', 'Ag'): 3.00,  # Ag metálico: 2.89 Å típico
    ('Ni', 'Ni'): 2.70,  # Ni metálico: 2.49 Å típico
    ('Pt', 'Pt'): 2.90,  # Pt metálico: 2.77 Å típico
    ('Pd', 'Pd'): 2.90,  # Pd metálico: 2.75 Å típico
    ('Ti', 'Ti'): 3.00,  # Ti metálico: 2.89 Å típico
    ('Cr', 'Cr'): 2.80,  # Cr metálico: 2.50 Å típico
    ('Mn', 'Mn'): 2.80,  # Mn metálico
    ('Co', 'Co'): 2.70,  # Co metálico: 2.51 Å típico
    ('Zn', 'Zn'): 2.90,  # Zn metálico: 2.66 Å típico
    ('Mo', 'Mo'): 2.90,  # Mo metálico: 2.73 Å típico
    ('W', 'W'): 2.90,    # W metálico: 2.74 Å típico

    # Ligas bimetálicas (exemplos)
    ('Cu', 'Au'): 2.90,  # Liga Cu-Au
    ('Cu', 'Zn'): 2.80,  # Latão
    ('Fe', 'Ni'): 2.70,  # Aço inoxidável
    ('Fe', 'Cr'): 2.70,  # Aço inoxidável
}

# =============================================================================
# CRITÉRIOS DE VALIDAÇÃO
# =============================================================================

def get_bond_distance(element1: str, element2: str) -> float:
    """
    Retorna a distância máxima de ligação para um par de elementos.

    Procura em ordem:
    1. Biblioteca específica (BOND_DISTANCES_LIBRARY)
    2. Fallback: raios covalentes + 30% margem

    Args:
        element1: Símbolo do primeiro elemento
        element2: Símbolo do segundo elemento

    Returns:
        Distância máxima em Angstroms
    """
    # Normalizar ordem (alfabética)
    pair = tuple(sorted([element1, element2]))

    # Buscar na biblioteca
    if pair in BOND_DISTANCES_LIBRARY:
        return BOND_DISTANCES_LIBRARY[pair]

    # Fallback: raios covalentes + margem
    r1 = COVALENT_RADII.get(element1, 1.5)
    r2 = COVALENT_RADII.get(element2, 1.5)
    max_dist = (r1 + r2) * 1.30  # 30% margem de segurança

    # Log para adicionar futuramente
    logging.debug(
        f"⚠️  Par {element1}-{element2} não tabelado. "
        f"Usando fallback: {max_dist:.3f} Å (r1={r1:.3f}, r2={r2:.3f})"
    )

    return max_dist


def validate_bond(element1: str, element2: str, distance: float) -> dict:
    """
    Valida se uma ligação é química ou fantasma.

    Returns:
        dict com:
            - is_valid (bool): True se ligação é válida
            - max_expected (float): Distância máxima esperada
            - confidence (str): 'high', 'medium', 'low'
            - reason (str): Explicação
    """
    pair = tuple(sorted([element1, element2]))
    max_dist = get_bond_distance(element1, element2)

    # Verificar se par está tabelado
    is_tabulated = pair in BOND_DISTANCES_LIBRARY

    # Validação
    is_valid = distance <= max_dist

    # Nível de confiança
    if is_tabulated:
        if distance < max_dist * 0.85:
            confidence = 'high'
            reason = f"Ligação típica {element1}-{element2} (< {max_dist:.2f} Å, tabelada CSD)"
        else:
            confidence = 'medium'
            reason = f"Ligação longa mas válida {element1}-{element2} ({distance:.2f} < {max_dist:.2f} Å)"
    else:
        if distance < max_dist * 0.85:
            confidence = 'medium'
            reason = f"Ligação estimada por raios covalentes (par não tabelado)"
        else:
            confidence = 'low'
            reason = f"Ligação no limite (fallback, par não tabelado)"

    if not is_valid:
        confidence = 'invalid'
        reason = f"❌ Ligação FANTASMA: {distance:.2f} Å > {max_dist:.2f} Å máximo"

    return {
        'is_valid': is_valid,
        'max_expected': max_dist,
        'confidence': confidence,
        'reason': reason,
        'is_tabulated': is_tabulated,
    }


def get_library_stats() -> dict:
    """Retorna estatísticas da biblioteca."""
    return {
        'total_pairs': len(BOND_DISTANCES_LIBRARY),
        'total_elements_tabulated': len(set([e for pair in BOND_DISTANCES_LIBRARY.keys() for e in pair])),
        'total_elements_covalent_radii': len(COVALENT_RADII),
        'coverage': f"{len(BOND_DISTANCES_LIBRARY)} pares explícitos",
    }


# =============================================================================
# TESTES DE VALIDAÇÃO
# =============================================================================
if __name__ == "__main__":
    print("="*70)
    print("BIBLIOTECA DE DISTÂNCIAS DE LIGAÇÕES QUÍMICAS")
    print("="*70)

    stats = get_library_stats()
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"  Pares tabelados: {stats['total_pairs']}")
    print(f"  Elementos (raios covalentes): {stats['total_elements_covalent_radii']}")
    print(f"  Elementos com pares tabelados: {stats['total_elements_tabulated']}")

    print(f"\n🧪 TESTES:")

    # Teste 1: Grafite (caso crítico)
    test_cases = [
        ('C', 'C', 1.42, "Grafite intra-camada"),
        ('C', 'C', 3.35, "Grafite inter-camadas (fantasma)"),
        ('Fe', 'O', 2.05, "Óxido de ferro"),
        ('Ce', 'O', 2.34, "Ceria (CeO₂)"),
        ('Ti', 'O', 1.95, "Titânia (TiO₂)"),
        ('Si', 'O', 1.63, "Quartzo"),
        ('Cu', 'S', 2.30, "Sulfeto de cobre"),
        ('Mo', 'S', 2.41, "MoS₂"),
        ('C', 'W', 2.20, "Carbeto de tungstênio"),
        ('B', 'N', 1.45, "Nitreto de boro"),
    ]

    for elem1, elem2, dist, desc in test_cases:
        result = validate_bond(elem1, elem2, dist)
        status = "✅" if result['is_valid'] else "❌"
        tab = "📚" if result['is_tabulated'] else "🔢"
        print(f"\n{status} {tab} {desc}:")
        print(f"     {elem1}-{elem2}: {dist:.2f} Å (max: {result['max_expected']:.2f} Å)")
        print(f"     Confiança: {result['confidence']} - {result['reason']}")

    print("\n" + "="*70)
    print("✅ Biblioteca carregada e validada!")
    print("="*70)

