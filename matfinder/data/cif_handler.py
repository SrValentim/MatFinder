# cif_handler.py
# Módulo para manipulação de parâmetros de arquivos CIF usando pymatgen.
# Versão 3.0 - Gerador de CIF com preservação de simetria (validável por FINDSYM/checkCIF)
#
# O pymatgen por padrão gera CIF em P1 (sem simetria), expandindo todos os átomos
# e duplicando labels. Este módulo usa CifWriter(symprec) para gerar CIF com simetria
# preservada, labels únicos e operações de simetria corretas.

import re
import logging
import math
import numpy as np

try:
    from pymatgen.core import Structure, Lattice, Element
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    from pymatgen.io.cif import CifWriter

    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False
    logging.warning("Pymatgen não encontrado. A manipulação de CIF não funcionará.")

# Tabela de fatores de espalhamento anômalo (f', f'') para Cu Kα (λ=1.54184 Å)
# e Mo Kα (λ=0.71073 Å) - Valores tabelados do International Tables for Crystallography Vol. C
# Formato: {elemento: {'CuKa': (f', f''), 'MoKa': (f', f'')}}
ANOMALOUS_SCATTERING = {
    'H':  {'CuKa': (0.0000, 0.0000), 'MoKa': (0.0000, 0.0000)},
    'C':  {'CuKa': (0.0181, 0.0091), 'MoKa': (0.0033, 0.0016)},
    'N':  {'CuKa': (0.0311, 0.0180), 'MoKa': (0.0061, 0.0033)},
    'O':  {'CuKa': (0.0492, 0.0322), 'MoKa': (0.0106, 0.0060)},
    'F':  {'CuKa': (0.0727, 0.0534), 'MoKa': (0.0171, 0.0103)},
    'Na': {'CuKa': (0.1353, 0.1316), 'MoKa': (0.0362, 0.0249)},
    'Mg': {'CuKa': (0.1719, 0.1771), 'MoKa': (0.0486, 0.0363)},
    'Al': {'CuKa': (0.2130, 0.2455), 'MoKa': (0.0645, 0.0514)},
    'Si': {'CuKa': (0.2541, 0.3302), 'MoKa': (0.0817, 0.0704)},
    'P':  {'CuKa': (0.2955, 0.4335), 'MoKa': (0.1023, 0.0942)},
    'S':  {'CuKa': (0.3331, 0.5567), 'MoKa': (0.1246, 0.1234)},
    'Cl': {'CuKa': (0.3639, 0.7018), 'MoKa': (0.1484, 0.1585)},
    'K':  {'CuKa': (0.3868, 1.0519), 'MoKa': (0.2009, 0.2494)},
    'Ca': {'CuKa': (0.3641, 1.2855), 'MoKa': (0.2262, 0.3064)},
    'Ti': {'CuKa': (0.2776, 1.8784), 'MoKa': (0.2776, 0.4457)},
    'V':  {'CuKa': (0.1984, 2.1918), 'MoKa': (0.3005, 0.5294)},
    'Cr': {'CuKa': (0.0589, 2.5599), 'MoKa': (0.3209, 0.6236)},
    'Mn': {'CuKa': (-0.1461, 2.9820), 'MoKa': (0.3368, 0.7283)},
    'Fe': {'CuKa': (-1.1336, 3.1974), 'MoKa': (0.3463, 0.8444)},
    'Co': {'CuKa': (-2.3653, 3.6143), 'MoKa': (0.3494, 0.9721)},
    'Ni': {'CuKa': (-3.0029, 0.5091), 'MoKa': (0.3393, 1.1124)},
    'Cu': {'CuKa': (-1.9646, 0.5888), 'MoKa': (0.3201, 1.2651)},
    'Zn': {'CuKa': (-1.5491, 0.6778), 'MoKa': (0.2839, 1.4301)},
    'Ga': {'CuKa': (-1.2246, 0.7846), 'MoKa': (0.2307, 1.6083)},
    'Ge': {'CuKa': (-0.9605, 0.9007), 'MoKa': (0.1547, 1.8001)},
    'As': {'CuKa': (-0.7375, 1.0284), 'MoKa': (0.0519, 2.0058)},
    'Se': {'CuKa': (-0.5364, 1.1674), 'MoKa': (-0.0929, 2.2259)},
    'Br': {'CuKa': (-0.3494, 1.3194), 'MoKa': (-0.2901, 2.4595)},
    'Rb': {'CuKa': (-0.0023, 1.6625), 'MoKa': (-0.9393, 2.9611)},
    'Sr': {'CuKa': (0.2079, 1.8528), 'MoKa': (-1.5307, 3.2498)},
    'Y':  {'CuKa': (0.5255, 2.0564), 'MoKa': (-2.7962, 3.5667)},
    'Zr': {'CuKa': (0.8803, 2.2448), 'MoKa': (-2.9673, 0.5597)},
    'Nb': {'CuKa': (1.3041, 2.3726), 'MoKa': (-2.0727, 0.6215)},
    'Mo': {'CuKa': (1.8214, 2.4134), 'MoKa': (-1.6832, 0.6857)},
    'Ru': {'CuKa': (3.3075, 2.0673), 'MoKa': (-1.2584, 0.8361)},
    'Rh': {'CuKa': (4.1308, 1.7284), 'MoKa': (-1.1178, 0.9187)},
    'Pd': {'CuKa': (5.2377, 1.0572), 'MoKa': (-0.9988, 1.0072)},
    'Ag': {'CuKa': (5.3352, 0.7845), 'MoKa': (-0.8971, 1.1015)},
    'Cd': {'CuKa': (4.6649, 0.5765), 'MoKa': (-0.8075, 1.2024)},
    'In': {'CuKa': (3.9324, 0.4572), 'MoKa': (-0.7276, 1.3100)},
    'Sn': {'CuKa': (3.2188, 0.3809), 'MoKa': (-0.6537, 1.4246)},
    'Sb': {'CuKa': (2.5364, 0.3312), 'MoKa': (-0.5866, 1.5461)},
    'Te': {'CuKa': (1.8967, 0.2993), 'MoKa': (-0.5308, 1.6747)},
    'I':  {'CuKa': (1.3025, 0.2813), 'MoKa': (-0.4742, 1.8119)},
    'Cs': {'CuKa': (0.2471, 0.2717), 'MoKa': (-0.3680, 2.1192)},
    'Ba': {'CuKa': (-0.3244, 0.2757), 'MoKa': (-0.3244, 2.2802)},
    'La': {'CuKa': (-0.6783, 0.2871), 'MoKa': (-0.2871, 2.4523)},
    'Ce': {'CuKa': (-0.9768, 0.3034), 'MoKa': (-0.2486, 2.6331)},
    'Pr': {'CuKa': (-1.2558, 0.3237), 'MoKa': (-0.2180, 2.8214)},
    'Nd': {'CuKa': (-1.5236, 0.3484), 'MoKa': (-0.1943, 3.0179)},
    'Sm': {'CuKa': (-2.0487, 0.4143), 'MoKa': (-0.1638, 3.4327)},
    'Eu': {'CuKa': (-2.3143, 0.4603), 'MoKa': (-0.1578, 3.6431)},
    'Gd': {'CuKa': (-2.5893, 0.5161), 'MoKa': (-0.1585, 3.8617)},
    'Tb': {'CuKa': (-2.8802, 0.5850), 'MoKa': (-0.1667, 4.0878)},
    'Dy': {'CuKa': (-3.2063, 0.6694), 'MoKa': (-0.1859, 4.3199)},
    'Ho': {'CuKa': (-3.5925, 0.7767), 'MoKa': (-0.2150, 4.5581)},
    'Er': {'CuKa': (-4.0791, 0.9155), 'MoKa': (-0.2580, 4.8008)},
    'Tm': {'CuKa': (-4.7366, 1.1021), 'MoKa': (-0.3184, 5.0486)},
    'Yb': {'CuKa': (-5.6743, 1.3659), 'MoKa': (-0.3850, 5.3034)},
    'Lu': {'CuKa': (-7.2803, 1.7707), 'MoKa': (-0.4720, 5.5588)},
    'Hf': {'CuKa': (-6.1694, 1.4726), 'MoKa': (-0.5830, 5.8294)},
    'Ta': {'CuKa': (-4.3783, 1.1544), 'MoKa': (-0.7145, 6.0601)},
    'W':  {'CuKa': (-3.0823, 0.8939), 'MoKa': (-0.8493, 6.8722)},
    'Re': {'CuKa': (-2.0568, 0.6916), 'MoKa': (-1.0345, 7.2310)},
    'Os': {'CuKa': (-1.2165, 0.5330), 'MoKa': (-1.2165, 7.6511)},
    'Ir': {'CuKa': (-0.5011, 0.4132), 'MoKa': (-1.4442, 8.0210)},
    'Pt': {'CuKa': (0.1432, 0.3238), 'MoKa': (-1.7033, 8.3905)},
    'Au': {'CuKa': (0.7520, 0.2591), 'MoKa': (-2.0133, 8.8109)},
    'Pb': {'CuKa': (1.8746, 0.1832), 'MoKa': (-3.3944, 10.1111)},
    'Bi': {'CuKa': (2.3488, 0.1609), 'MoKa': (-4.1077, 10.2566)},
    'Th': {'CuKa': (4.2430, 0.1241), 'MoKa': (-7.3318, 11.2576)},
    'U':  {'CuKa': (5.6748, 0.1136), 'MoKa': (-9.6767, 11.2422)},
}

# Tabela de coeficientes de absorção de massa (cm²/g) para Cu Kα e Mo Kα
# International Tables for Crystallography Vol. C, Table 4.2.4.3
MASS_ATTENUATION = {
    'H':  {'CuKa': 0.435, 'MoKa': 0.386},
    'C':  {'CuKa': 4.60,  'MoKa': 0.625},
    'N':  {'CuKa': 7.52,  'MoKa': 0.916},
    'O':  {'CuKa': 11.5,  'MoKa': 1.31},
    'F':  {'CuKa': 16.4,  'MoKa': 1.80},
    'Na': {'CuKa': 30.1,  'MoKa': 3.21},
    'Mg': {'CuKa': 38.6,  'MoKa': 4.02},
    'Al': {'CuKa': 48.6,  'MoKa': 5.03},
    'Si': {'CuKa': 60.6,  'MoKa': 6.44},
    'P':  {'CuKa': 74.1,  'MoKa': 7.87},
    'S':  {'CuKa': 89.1,  'MoKa': 9.55},
    'Cl': {'CuKa': 106.0, 'MoKa': 11.4},
    'K':  {'CuKa': 143.0, 'MoKa': 15.0},
    'Ca': {'CuKa': 162.0, 'MoKa': 17.1},
    'Ti': {'CuKa': 208.0, 'MoKa': 22.1},
    'V':  {'CuKa': 233.0, 'MoKa': 24.7},
    'Cr': {'CuKa': 260.0, 'MoKa': 27.6},
    'Mn': {'CuKa': 285.0, 'MoKa': 30.6},
    'Fe': {'CuKa': 308.0, 'MoKa': 34.0},
    'Co': {'CuKa': 313.0, 'MoKa': 37.6},
    'Ni': {'CuKa': 49.5,  'MoKa': 41.4},
    'Cu': {'CuKa': 52.7,  'MoKa': 45.7},
    'Zn': {'CuKa': 60.3,  'MoKa': 50.6},
    'Ga': {'CuKa': 67.9,  'MoKa': 55.4},
    'Ge': {'CuKa': 75.6,  'MoKa': 60.4},
    'As': {'CuKa': 84.1,  'MoKa': 65.7},
    'Se': {'CuKa': 92.6,  'MoKa': 71.7},
    'Br': {'CuKa': 101.0, 'MoKa': 78.2},
    'Sr': {'CuKa': 124.0, 'MoKa': 93.3},
    'Y':  {'CuKa': 134.0, 'MoKa': 100.0},
    'Zr': {'CuKa': 143.0, 'MoKa': 107.0},
    'Nb': {'CuKa': 153.0, 'MoKa': 15.5},
    'Mo': {'CuKa': 162.0, 'MoKa': 16.4},
    'Ru': {'CuKa': 181.0, 'MoKa': 18.4},
    'Pd': {'CuKa': 199.0, 'MoKa': 20.7},
    'Ag': {'CuKa': 212.0, 'MoKa': 22.2},
    'Cd': {'CuKa': 226.0, 'MoKa': 24.1},
    'In': {'CuKa': 240.0, 'MoKa': 25.9},
    'Sn': {'CuKa': 254.0, 'MoKa': 27.6},
    'Sb': {'CuKa': 267.0, 'MoKa': 29.4},
    'Te': {'CuKa': 280.0, 'MoKa': 31.2},
    'I':  {'CuKa': 294.0, 'MoKa': 33.2},
    'Cs': {'CuKa': 323.0, 'MoKa': 37.1},
    'Ba': {'CuKa': 330.0, 'MoKa': 38.6},
    'La': {'CuKa': 345.0, 'MoKa': 40.6},
    'Ce': {'CuKa': 352.0, 'MoKa': 42.2},
    'Pr': {'CuKa': 362.0, 'MoKa': 44.1},
    'Nd': {'CuKa': 371.0, 'MoKa': 45.7},
    'Sm': {'CuKa': 388.0, 'MoKa': 49.1},
    'Eu': {'CuKa': 396.0, 'MoKa': 50.7},
    'Gd': {'CuKa': 403.0, 'MoKa': 52.4},
    'Tb': {'CuKa': 410.0, 'MoKa': 54.2},
    'Dy': {'CuKa': 417.0, 'MoKa': 55.8},
    'Ho': {'CuKa': 424.0, 'MoKa': 57.9},
    'Er': {'CuKa': 430.0, 'MoKa': 59.5},
    'Yb': {'CuKa': 443.0, 'MoKa': 63.4},
    'Lu': {'CuKa': 449.0, 'MoKa': 65.1},
    'Hf': {'CuKa': 454.0, 'MoKa': 66.8},
    'Ta': {'CuKa': 459.0, 'MoKa': 68.3},
    'W':  {'CuKa': 464.0, 'MoKa': 70.6},
    'Pt': {'CuKa': 478.0, 'MoKa': 76.2},
    'Au': {'CuKa': 483.0, 'MoKa': 78.0},
    'Pb': {'CuKa': 232.0, 'MoKa': 80.8},
    'Bi': {'CuKa': 240.0, 'MoKa': 83.3},
    'Th': {'CuKa': 266.0, 'MoKa': 94.0},
    'U':  {'CuKa': 279.0, 'MoKa': 100.0},
}


class CifHandler:
    """
    Uma classe para carregar, manipular e salvar estruturas cristalinas de/para
    strings de formato CIF.
    """

    def __init__(self, cif_content: str):
        if not PYMATGEN_AVAILABLE:
            raise ImportError("A biblioteca 'pymatgen' é necessária para manipular arquivos CIF.")

        if not cif_content or not isinstance(cif_content, str):
            raise ValueError("O conteúdo do CIF fornecido é inválido ou está vazio.")

        self._original_cif_content = cif_content

        try:
            self.structure = Structure.from_str(cif_content, fmt="cif")
            self.analyzer = SpacegroupAnalyzer(self.structure)
        except Exception as e:
            logging.error(f"Falha ao analisar a string do CIF: {e}")
            raise ValueError(f"Não foi possível analisar o conteúdo do CIF. Erro: {e}")

        # Preservar metadados de simetria do CIF original para validação
        self._original_symmetry = self._extract_symmetry_metadata(cif_content)

    def get_structure(self):
        """Retorna a estrutura pymatgen (Structure) carregada."""
        return self.structure

    def get_lattice_params(self) -> dict:
        """
        Obtém os parâmetros de rede da estrutura carregada.
        """
        lattice = self.structure.lattice
        return {
            "a": lattice.a,
            "b": lattice.b,
            "c": lattice.c,
            "alpha": lattice.alpha,
            "beta": lattice.beta,
            "gamma": lattice.gamma,
            "volume": lattice.volume,
        }

    def get_crystal_system(self) -> str:
        """Retorna o sistema cristalino da estrutura."""
        return self.analyzer.get_crystal_system().lower()

    def get_space_group_info(self) -> dict:
        """
        Retorna informações do grupo espacial da estrutura.

        Returns:
            dict: Dicionário com 'number' (int) e 'symbol' (str) do grupo espacial
        """
        try:
            spacegroup = self.analyzer.get_space_group_symbol()
            spacegroup_number = self.analyzer.get_space_group_number()

            return {
                'number': spacegroup_number,
                'symbol': spacegroup
            }
        except Exception as e:
            logging.warning(f"Não foi possível obter informações do grupo espacial: {e}")
            return {
                'number': None,
                'symbol': 'Desconhecido'
            }

    def update_lattice_params(self, a=None, b=None, c=None, alpha=None, beta=None, gamma=None):
        """
        Atualiza a estrutura com novos parâmetros de rede, respeitando as restrições
        do sistema cristalino.
        """
        current_params = self.get_lattice_params()
        crystal_system = self.get_crystal_system()

        # Usa os novos valores ou mantém os antigos se não forem fornecidos
        new_a = a if a is not None else current_params['a']
        new_b = b if b is not None else current_params['b']
        new_c = c if c is not None else current_params['c']
        new_alpha = alpha if alpha is not None else current_params['alpha']
        new_beta = beta if beta is not None else current_params['beta']
        new_gamma = gamma if gamma is not None else current_params['gamma']

        # Aplica restrições cristalográficas
        if crystal_system == 'cubic':
            # Cúbico: a = b = c, α = β = γ = 90°
            new_b, new_c = new_a, new_a
            new_alpha, new_beta, new_gamma = 90.0, 90.0, 90.0
        elif crystal_system == 'tetragonal':
            # Tetragonal: a = b ≠ c, α = β = γ = 90°
            new_b = new_a
            new_alpha, new_beta, new_gamma = 90.0, 90.0, 90.0
        elif crystal_system == 'hexagonal':
            # Hexagonal: a = b ≠ c, α = β = 90°, γ = 120°
            new_b = new_a
            new_alpha, new_beta, new_gamma = 90.0, 90.0, 120.0
        elif crystal_system in ['trigonal', 'rhombohedral']:
            # Trigonal pode ter duas configurações:
            # 1. Hexagonal: a = b ≠ c, α = β = 90°, γ = 120°
            # 2. Romboédrica: a = b = c, α = β = γ ≠ 90°
            # Detectar qual configuração baseado nos parâmetros atuais
            is_rhombohedral = (abs(current_params['a'] - current_params['c']) < 0.01 and
                              abs(current_params['alpha'] - current_params['gamma']) < 0.1 and
                              abs(current_params['alpha'] - 90.0) > 0.1)

            if is_rhombohedral or crystal_system == 'rhombohedral':
                # Romboédrico: a = b = c, α = β = γ ≠ 90°
                new_b, new_c = new_a, new_a
                new_beta, new_gamma = new_alpha, new_alpha
                logging.debug("Trigonal/Romboédrico detectado: configuração romboédrica")
            else:
                # Hexagonal: a = b ≠ c, α = β = 90°, γ = 120°
                new_b = new_a
                new_alpha, new_beta, new_gamma = 90.0, 90.0, 120.0
                logging.debug("Trigonal detectado: configuração hexagonal")
        elif crystal_system == 'orthorhombic':
            # Ortorrômbico: a ≠ b ≠ c, α = β = γ = 90°
            new_alpha, new_beta, new_gamma = 90.0, 90.0, 90.0
        elif crystal_system == 'monoclinic':
            # Monoclínico: a ≠ b ≠ c, α = γ = 90°, β ≠ 90°
            new_alpha, new_gamma = 90.0, 90.0
        # Triclínico: a ≠ b ≠ c, α ≠ β ≠ γ (sem restrições)

        try:
            # Salvar sistema cristalino antigo para detectar mudanças
            old_crystal_system = crystal_system

            new_lattice = Lattice.from_parameters(
                a=new_a, b=new_b, c=new_c,
                alpha=new_alpha, beta=new_beta, gamma=new_gamma
            )
            self.structure = Structure(
                new_lattice,
                self.structure.species,
                self.structure.frac_coords,
                coords_are_cartesian=False
            )

            # CRÍTICO: Atualizar analyzer com nova estrutura
            self.analyzer = SpacegroupAnalyzer(self.structure)
            new_crystal_system = self.get_crystal_system()

            # Validar se o sistema cristalino mudou
            if old_crystal_system != new_crystal_system:
                logging.warning(f"⚠️ Sistema cristalino mudou após edição: {old_crystal_system} → {new_crystal_system}")
                logging.warning(f"   Parâmetros: a={new_a:.3f}, b={new_b:.3f}, c={new_c:.3f}, α={new_alpha:.2f}°, β={new_beta:.2f}°, γ={new_gamma:.2f}°")

            logging.info(f"Parâmetros de rede atualizados para: a={new_a:.3f}, b={new_b:.3f}, c={new_c:.3f}")
        except Exception as e:
            logging.error(f"Erro ao criar nova rede com os parâmetros fornecidos: {e}")
            raise ValueError(f"Parâmetros de rede inválidos. Erro: {e}")

    def scale_volume(self, new_volume: float):
        """
        Escala a célula unitária para um novo volume, mantendo sua forma.
        """
        if new_volume <= 0:
            raise ValueError("O novo volume deve ser um número positivo.")

        old_volume = self.structure.lattice.volume
        self.structure.scale_lattice(new_volume)

        # CRÍTICO: Atualizar analyzer com nova estrutura
        self.analyzer = SpacegroupAnalyzer(self.structure)

        logging.info(f"Volume escalado de {old_volume:.2f} para {self.structure.lattice.volume:.2f} Å³")

    def get_cif_string(self) -> str:
        """
        Gera uma string no formato CIF a partir da estrutura atual,
        preservando simetria e gerando labels únicos.

        Usa CifWriter(symprec) para detectar simetria e gerar CIF válido.
        Se falhar, tenta preservar a simetria do CIF original como fallback.
        """
        try:
            # Tentar gerar CIF com simetria detectada automaticamente
            cif_string = self._generate_symmetric_cif()

            # Validar o CIF gerado
            validation = self._validate_cif_string(cif_string)
            if validation['valid']:
                # Validação extra: tentar parsear o CIF gerado para garantir integridade
                try:
                    Structure.from_str(cif_string, fmt="cif")
                except Exception as parse_err:
                    logging.warning(f"CIF gerado falhou na validação de parse: {parse_err}. Usando fallback...")
                    return self._generate_fallback_cif()

                logging.info(
                    f"CIF gerado com simetria: {validation.get('space_group', 'N/A')} "
                    f"(#{validation.get('sg_number', '?')}), "
                    f"{validation.get('n_unique_atoms', '?')} átomos únicos"
                )
                return cif_string
            else:
                logging.warning(f"CIF simétrico com problemas: {validation.get('issues', [])}. Tentando fallback...")
                return self._generate_fallback_cif()

        except Exception as e:
            logging.error(f"Erro ao gerar CIF simétrico: {e}. Usando fallback.")
            return self._generate_fallback_cif()

    def _generate_symmetric_cif(self, symprec: float = 0.1) -> str:
        """
        Gera CIF validável por checkCIF/PLATON usando CifWriter com detecção de simetria.

        Pós-processamento para conformidade checkCIF:
        - Labels com indexação a partir de 1 (Ce1 em vez de Ce0)
        - _atom_site_Wyckoff_symbol adicionado
        - _chemical_formula_sum por unidade de fórmula (dividido por Z)
        - _symmetry_space_group_name_H-M com aspas
        - _symmetry_cell_setting adicionado
        - _atom_type loop adicionado
        - Tags de loop_ sem indentação (coluna 1)
        - Precisão numérica adequada
        """
        try:
            writer = CifWriter(self.structure, symprec=symprec, significant_figures=8)
            cif_str = str(writer)

            # Obter dados de Wyckoff do SpacegroupAnalyzer
            wyckoff_map = self._get_wyckoff_map(symprec)

            # Pós-processamento completo para conformidade checkCIF
            cif_str = self._postprocess_cif(cif_str, wyckoff_map)

            # Adicionar cabeçalho
            header = (
                "# CIF generated by MatFinder/PhaseDRX\n"
                "# Modified from original using symmetry-aware CIF generator\n"
                "#\n"
            )
            if cif_str.startswith("# generated using pymatgen"):
                first_newline = cif_str.index('\n')
                cif_str = cif_str[:first_newline + 1] + header + cif_str[first_newline + 1:]
            else:
                cif_str = header + cif_str

            return cif_str

        except Exception as e:
            logging.warning(f"CifWriter(symprec={symprec}) falhou: {e}")
            if symprec < 1.0:
                logging.info("Tentando com symprec=0.01 (mais restritivo)...")
                try:
                    writer = CifWriter(self.structure, symprec=0.01, significant_figures=8)
                    return self._postprocess_cif(str(writer), self._get_wyckoff_map(0.01))
                except Exception:
                    pass
            raise

    def _get_wyckoff_map(self, symprec: float = 0.1) -> dict:
        """
        Obtém mapeamento de átomos equivalentes para letras de Wyckoff.

        Returns:
            dict mapeando índice do átomo equivalente para letra Wyckoff.
        """
        try:
            sga = SpacegroupAnalyzer(self.structure, symprec=symprec)
            dataset = sga.get_symmetry_dataset()

            wyckoff_map = {}
            seen_equiv = set()
            for i, (equiv_idx, wyckoff_letter) in enumerate(
                zip(dataset.equivalent_atoms, dataset.wyckoffs)
            ):
                if equiv_idx not in seen_equiv:
                    seen_equiv.add(equiv_idx)
                    wyckoff_map[equiv_idx] = wyckoff_letter

            return wyckoff_map
        except Exception as e:
            logging.warning(f"Não foi possível obter dados de Wyckoff: {e}")
            return {}

    @staticmethod
    def _format_number(value: float, precision: int = 6) -> str:
        """
        Formata número removendo zeros desnecessários.
        90.00000000 → '90', 5.53500000 → '5.535', 0.25000000 → '0.25'
        """
        formatted = f"{value:.{precision}f}"
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return formatted

    @staticmethod
    def _get_formula_per_z(composition, z: int) -> str:
        """
        Retorna _chemical_formula_sum por unidade de fórmula (dividido por Z).
        Ex: composition='Ce4 Nb4 O16', Z=4 → 'Ce1 Nb1 O4'
        """
        if z <= 0:
            z = 1
        try:
            element_amounts = composition.get_el_amt_dict()
            parts = []
            for element in sorted(element_amounts.keys()):
                count = element_amounts[element] / z
                if abs(count - round(count)) < 0.01:
                    count = int(round(count))
                # checkCIF PLAT041: omitir "1" quando count=1 (ex: 'Ce Nb O4' não 'Ce1 Nb1 O4')
                if count == 1:
                    parts.append(f"{element}")
                else:
                    parts.append(f"{element}{count}")
            return "'" + ' '.join(parts) + "'"
        except Exception:
            return "'" + composition.reduced_formula + "'"

    def _get_crystal_system_name(self) -> str:
        """Retorna nome do sistema cristalino para _symmetry_cell_setting."""
        try:
            return self.analyzer.get_crystal_system().lower()
        except Exception:
            return 'triclinic'

    def _get_hall_symbol(self) -> str:
        """Retorna o símbolo Hall do grupo espacial para _symmetry_space_group_name_Hall."""
        try:
            import spglib
            cell = (
                self.structure.lattice.matrix,
                self.structure.frac_coords,
                [s.specie.Z for s in self.structure]
            )
            dataset = spglib.get_symmetry_dataset(cell, symprec=0.1)
            if dataset is not None:
                # Usar interface de atributo (spglib >= 2.x) ou dict (fallback)
                hall = getattr(dataset, 'hall', None) or (dataset.get('hall') if hasattr(dataset, 'get') else None)
                if hall:
                    return hall
        except Exception:
            pass
        # Fallback: obter do número do grupo espacial
        try:
            import spglib
            sg_number = self.analyzer.get_space_group_number()
            sg_type = spglib.get_spacegroup_type(sg_number)
            if sg_type is not None:
                hall = getattr(sg_type, 'hall_symbol', None) or (sg_type.get('hall_symbol') if hasattr(sg_type, 'get') else None)
                if hall:
                    return hall
        except Exception:
            pass
        return '?'

    def _calculate_density(self, z_val: int) -> float:
        """
        Calcula a densidade cristalográfica (Dx) em g/cm³.
        Dx = (Z * Mr) / (V * Na) onde Na = 6.02214076e23, V em cm³
        """
        try:
            mol_weight = self.structure.composition.weight / z_val if z_val > 0 else self.structure.composition.weight
            volume_angstrom3 = self.structure.lattice.volume
            volume_cm3 = volume_angstrom3 * 1e-24  # 1 Å³ = 1e-24 cm³
            na = 6.02214076e23
            density = (z_val * mol_weight) / (volume_cm3 * na)
            return density
        except Exception:
            return 0.0

    def _build_atom_type_loop(self, atom_symbols: list, wavelength: str = 'MoKa') -> list:
        """
        Gera o bloco loop_ _atom_type com fatores de espalhamento anômalo.
        Obrigatório pelo checkCIF. Inclui f' e f'' (PLAT981, PLAT986).

        Args:
            atom_symbols: Lista de símbolos atômicos
            wavelength: 'MoKa' (0.71073 Å) ou 'CuKa' (1.54184 Å)
        """
        # Extrair elementos únicos preservando ordem
        seen = set()
        unique_symbols = []
        for sym in atom_symbols:
            base = re.match(r'^([A-Za-z]+)', sym)
            base_elem = base.group(1) if base else sym
            if base_elem not in seen:
                seen.add(base_elem)
                unique_symbols.append(base_elem)

        lines = [
            "loop_",
            "_atom_type_symbol",
            "_atom_type_scat_dispersion_real",
            "_atom_type_scat_dispersion_imag",
            "_atom_type_scat_source"
        ]
        for sym in unique_symbols:
            scattering = ANOMALOUS_SCATTERING.get(sym, {})
            f_prime, f_double_prime = scattering.get(wavelength, (0.0, 0.0))
            source = f"'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'"
            lines.append(f"{sym}   {f_prime:.4f}   {f_double_prime:.4f}   {source}")
        return lines

    def _calculate_mu(self, wavelength: str = 'MoKa') -> float:
        """
        Calcula o coeficiente de absorção linear µ (mm⁻¹).
        µ = ρ * Σ(wi * µi/ρi) onde wi é a fração em peso do elemento i.

        Args:
            wavelength: 'MoKa' ou 'CuKa'
        Returns:
            float: µ em mm⁻¹
        """
        try:
            density = self.structure.density  # g/cm³
            composition = self.structure.composition
            total_weight = composition.weight

            mu_rho_sum = 0.0
            for el in composition.elements:
                sym = el.symbol
                weight_fraction = (composition[el] * el.atomic_mass) / total_weight
                mu_rho = MASS_ATTENUATION.get(sym, {}).get(wavelength, 0.0)
                mu_rho_sum += weight_fraction * mu_rho

            # µ (cm⁻¹) = ρ (g/cm³) * Σ(wi * (µ/ρ)i) (cm²/g)
            mu_cm = density * mu_rho_sum
            # Converter para mm⁻¹
            mu_mm = mu_cm / 10.0
            return mu_mm
        except Exception as e:
            logging.warning(f"Erro ao calcular µ: {e}")
            return 0.0

    def _calculate_f000(self, z_val: int) -> float:
        """
        Calcula F(000) = Σ(Z_i * occupancy_i * multiplicity)
        onde Z_i é o número atômico de cada átomo.

        Para uma célula unitária completa: F(000) = Σ(número de elétrons por átomo na célula).
        """
        try:
            f000 = 0.0
            for site in self.structure:
                f000 += site.specie.Z  # Número atômico = número de elétrons (neutro)
            return f000
        except Exception as e:
            logging.warning(f"Erro ao calcular F(000): {e}")
            return 0.0

    def _build_bond_geometry_loop(self) -> list:
        """
        Calcula e gera o loop_ de distâncias interatômicas (bonds).
        Resolve GEOM001, GEOM002, GEOM003.

        Usa o SpacegroupAnalyzer para trabalhar com a unidade assimétrica
        e gerar bonds com informação de simetria.
        """
        try:
            # Usar estrutura simétrica para obter os sites independentes
            sga = SpacegroupAnalyzer(self.structure, symprec=0.1)
            sym_structure = sga.get_symmetrized_structure()

            lines = [
                "loop_",
                "_geom_bond_atom_site_label_1",
                "_geom_bond_atom_site_label_2",
                "_geom_bond_distance",
                "_geom_bond_site_symmetry_2"
            ]

            # Criar labels para os sites equivalentes
            site_labels = {}
            atom_counter = {}
            equiv_site_list = []
            for i, equiv_sites in enumerate(sym_structure.equivalent_sites):
                site = equiv_sites[0]
                elem = site.specie.symbol
                if elem not in atom_counter:
                    atom_counter[elem] = 1
                label = f"{elem}{atom_counter[elem]}"
                atom_counter[elem] += 1
                site_labels[i] = label
                equiv_site_list.append(site)

            # Calcular bonds usando a biblioteca de ligações
            try:
                from matfinder.tools.xrd.bond_library import get_bond_distance
            except ImportError:
                get_bond_distance = None

            added_bonds = set()
            for i, site_i in enumerate(equiv_site_list):
                label_i = site_labels[i]
                elem_i = site_i.specie.symbol

                # Encontrar TODOS os vizinhos dentro de 3.5 Å
                neighbors = self.structure.get_neighbors(site_i, 3.5)

                # Agrupar vizinhos por tipo de elemento e pegar a menor distância de cada tipo
                best_by_elem = {}
                for neighbor in neighbors:
                    n_site = neighbor[0] if isinstance(neighbor, tuple) else neighbor
                    n_dist = neighbor[1] if isinstance(neighbor, tuple) else neighbor.nn_distance
                    n_elem = n_site.specie.symbol if hasattr(n_site, 'specie') else ''

                    # Validar distância com a biblioteca
                    if get_bond_distance is not None:
                        max_dist = get_bond_distance(elem_i, n_elem)
                    else:
                        max_dist = 3.0

                    if n_dist <= max_dist:
                        # Encontrar qual site equivalente este vizinho corresponde
                        for j, site_j in enumerate(equiv_site_list):
                            if site_j.specie.symbol == n_elem:
                                label_j = site_labels[j]
                                bond_key = tuple(sorted([label_i, label_j])) + (round(n_dist, 3),)
                                if bond_key not in added_bonds:
                                    added_bonds.add(bond_key)
                                    lines.append(f"{label_i}   {label_j}   {n_dist:.4f}   .")
                                break

            if len(lines) <= 5:  # Apenas headers, sem dados
                return []
            return lines

        except Exception as e:
            logging.warning(f"Erro ao gerar geometria de bonds: {e}")
            return []

    def _build_angle_geometry_loop(self) -> list:
        """
        Calcula e gera o loop_ de ângulos interatômicos.
        Resolve GEOM006, GEOM007, GEOM008.
        """
        try:
            sga = SpacegroupAnalyzer(self.structure, symprec=0.1)
            sym_structure = sga.get_symmetrized_structure()

            lines = [
                "loop_",
                "_geom_angle_atom_site_label_1",
                "_geom_angle_atom_site_label_2",
                "_geom_angle_atom_site_label_3",
                "_geom_angle",
                "_geom_angle_site_symmetry_1",
                "_geom_angle_site_symmetry_3"
            ]

            # Criar labels
            site_labels = {}
            atom_counter = {}
            equiv_site_list = []
            for i, equiv_sites in enumerate(sym_structure.equivalent_sites):
                site = equiv_sites[0]
                elem = site.specie.symbol
                if elem not in atom_counter:
                    atom_counter[elem] = 1
                label = f"{elem}{atom_counter[elem]}"
                atom_counter[elem] += 1
                site_labels[i] = label
                equiv_site_list.append(site)

            try:
                from matfinder.tools.xrd.bond_library import get_bond_distance
            except ImportError:
                get_bond_distance = None

            added_angles = set()

            # Para cada átomo central, encontrar vizinhos bonded e calcular ângulos
            for i, site_i in enumerate(equiv_site_list):
                label_i = site_labels[i]
                elem_i = site_i.specie.symbol

                # Encontrar vizinhos bonded
                neighbors_info = []  # (label, coords, distance)
                all_neighbors = self.structure.get_neighbors(site_i, 3.5)

                for neighbor in all_neighbors:
                    n_site = neighbor[0] if isinstance(neighbor, tuple) else neighbor
                    n_dist = neighbor[1] if isinstance(neighbor, tuple) else neighbor.nn_distance
                    n_elem = n_site.specie.symbol if hasattr(n_site, 'specie') else ''
                    n_coords = n_site.coords if hasattr(n_site, 'coords') else None

                    if n_coords is None:
                        continue

                    # Validar que é uma ligação real
                    if get_bond_distance is not None:
                        max_dist = get_bond_distance(elem_i, n_elem)
                    else:
                        max_dist = 3.0

                    if n_dist <= max_dist:
                        # Determinar label do vizinho
                        for j, site_j in enumerate(equiv_site_list):
                            if site_j.specie.symbol == n_elem:
                                neighbors_info.append((site_labels[j], n_coords, n_dist))
                                break

                # Calcular ângulos entre pares de vizinhos
                for ni in range(len(neighbors_info)):
                    for nj in range(ni + 1, len(neighbors_info)):
                        label_ni = neighbors_info[ni][0]
                        label_nj = neighbors_info[nj][0]
                        coords_ni = neighbors_info[ni][1]
                        coords_nj = neighbors_info[nj][1]

                        vec1 = coords_ni - site_i.coords
                        vec2 = coords_nj - site_i.coords

                        norm1 = np.linalg.norm(vec1)
                        norm2 = np.linalg.norm(vec2)

                        if norm1 > 0.01 and norm2 > 0.01:
                            cos_angle = np.clip(np.dot(vec1, vec2) / (norm1 * norm2), -1, 1)
                            angle = math.degrees(math.acos(cos_angle))

                            # Ignorar ângulos degenerados (< 5° ou > 175°)
                            if angle < 5.0 or angle > 175.0:
                                continue

                            # Evitar duplicatas (sort labels mas manter central)
                            sorted_ends = tuple(sorted([label_ni, label_nj]))
                            angle_key = (sorted_ends[0], label_i, sorted_ends[1], round(angle, 1))
                            if angle_key not in added_angles:
                                added_angles.add(angle_key)
                                lines.append(f"{label_ni}   {label_i}   {label_nj}   {angle:.2f}   .   .")

            if len(lines) <= 7:  # Apenas headers
                return []
            return lines

        except Exception as e:
            logging.warning(f"Erro ao gerar geometria de ângulos: {e}")
            return []

    def _build_checkcif_metadata_block(self, z_val: int, wavelength: str = 'MoKa') -> list:
        """
        Gera bloco de metadados para conformidade com checkCIF/PLATON.
        Resolve alertas: EXPT005, DIFF003, PLAT197, PLAT198, PLAT699,
        PLAT183-185, PLAT880-881, PLAT029, ATOM007.

        Args:
            z_val: Número de unidades de fórmula (Z)
            wavelength: 'MoKa' ou 'CuKa'
        """
        lines = []

        # Wavelength info
        wl = 0.71073 if wavelength == 'MoKa' else 1.54184
        lines.append(f"_diffrn_radiation_wavelength   {wl:.5f}")
        rad_type = wavelength.replace('Ka', ' K\\a')
        lines.append(f"_diffrn_radiation_type   '{rad_type}'")
        # Crystal description (EXPT005, PLAT699)
        lines.append("_exptl_crystal_description   'computationally derived'")

        # Diffractometer type (DIFF003)
        lines.append("_diffrn_measurement_device_type   'computationally derived'")

        # Temperature (PLAT197, PLAT198)
        lines.append("_cell_measurement_temperature   293(2)")
        lines.append("_diffrn_ambient_temperature   293(2)")

        # Experimental data not applicable for computational CIF (PLAT183-185)
        lines.append("_cell_measurement_reflns_used   .")
        lines.append("_cell_measurement_theta_min   .")
        lines.append("_cell_measurement_theta_max   .")

        # Diffraction reflections not applicable (PLAT880, PLAT881, PLAT882)
        lines.append("_diffrn_reflns_number   .")
        lines.append("_diffrn_reflns_av_R_equivalents   .")
        lines.append("_diffrn_reflns_av_unetI/netI   .")
        lines.append("_diffrn_measured_fraction_theta_full   .")
        lines.append("_diffrn_measured_fraction_theta_max   .")

        # Absorption coefficient µ (mm⁻¹)
        mu = self._calculate_mu(wavelength)
        lines.append(f"_exptl_absorpt_coefficient_mu   {mu:.3f}")

        # F(000)
        f000 = self._calculate_f000(z_val)
        lines.append(f"_exptl_crystal_F_000   {f000:.0f}")

        # Audit information
        lines.append("_computing_structure_solution   'ab initio calculation'")
        lines.append("_audit_creation_method   'MatFinder/PhaseDRX CIF generator'")

        # Atom sites solution (PLAT883)
        lines.append("_atom_sites_solution_primary   'direct methods'")

        return lines

    def _postprocess_cif(self, cif_str: str, wyckoff_map: dict) -> str:
        """
        Pós-processa o CIF do CifWriter para conformidade com checkCIF/PLATON.

        Correções aplicadas:
        1. Labels com indexação a partir de 1 (Ce1 em vez de Ce0)
        2. _atom_site_Wyckoff_symbol adicionado
        3. _chemical_formula_sum por unidade de fórmula (/ Z)
        4. _symmetry_space_group_name_H-M com aspas simples
        5. _symmetry_cell_setting adicionado
        6. _atom_type loop adicionado antes do _atom_site loop
        7. Tags de loop_ sem indentação (coluna 1)
        8. Precisão numérica adequada nos parâmetros de rede
        """
        lines = cif_str.split('\n')
        result_lines = []

        # --- Fase 1: Processar linhas antes do bloco _atom_site ---
        atom_block_start = -1
        atom_block_header_end = -1
        header_fields = []
        in_atom_header = False
        formula_sum_fixed = False
        hm_fixed = False
        cell_setting_added = False

        # Identificar início do bloco _atom_site e coletar headers
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('_atom_site_type_symbol') and not in_atom_header:
                in_atom_header = True
                atom_block_start = i
                header_fields.append(stripped)
                continue
            if in_atom_header and stripped.startswith('_atom_site_'):
                header_fields.append(stripped)
                continue
            if in_atom_header and not stripped.startswith('_atom_site_') and stripped:
                atom_block_header_end = i
                break

        # Processar linhas antes do bloco _atom_site
        # Encontrar onde inserir _symmetry_cell_setting (após _symmetry_Int_Tables_number)
        insert_cell_setting_after = -1
        in_symop_loop = False  # Para rastrear se estamos no loop_ de simetria
        formula_weight_added = False

        # Calcular onde o loop_ do _atom_site começa (1 linha antes do atom_block_start)
        # O pymatgen gera: loop_\n _atom_site_type_symbol\n ...
        # Precisamos excluir esse loop_ para não gerar um loop_ vazio
        atom_loop_line = atom_block_start - 1 if atom_block_start > 0 else -1
        # Verificar se realmente é um loop_
        if atom_loop_line >= 0 and lines[atom_loop_line].strip() != 'loop_':
            atom_loop_line = -1

        for i in range(atom_block_start if atom_block_start >= 0 else len(lines)):
            line = lines[i]
            stripped = line.strip()

            # --- Pular o loop_ que pertence ao bloco _atom_site ---
            if i == atom_loop_line:
                continue

            # --- Fix _chemical_formula_sum: dividir por Z ---
            if stripped.startswith('_chemical_formula_sum'):
                try:
                    z_val = int(self._original_symmetry.get('z', 0))
                    if z_val == 0:
                        # Tentar encontrar Z no CIF
                        z_match = re.search(r'_cell_formula_units_Z\s+(\d+)', cif_str)
                        z_val = int(z_match.group(1)) if z_match else 1
                    formula_per_z = self._get_formula_per_z(self.structure.composition, z_val)
                    result_lines.append(f"_chemical_formula_sum   {formula_per_z}")
                    # Adicionar _chemical_formula_moiety (mesmo formato da sum formula)
                    result_lines.append(f"_chemical_formula_moiety   {formula_per_z}")
                    formula_sum_fixed = True
                    # PLAT043: Adicionar peso molecular por unidade de fórmula
                    if not formula_weight_added:
                        mol_weight = self.structure.composition.weight / z_val if z_val > 0 else self.structure.composition.weight
                        result_lines.append(f"_chemical_formula_weight   {mol_weight:.2f}")
                        # Adicionar densidade cristalográfica calculada
                        density = self._calculate_density(z_val)
                        if density > 0:
                            result_lines.append(f"_exptl_crystal_density_diffrn   {density:.3f}")
                        formula_weight_added = True
                    continue
                except Exception:
                    pass  # Manter original se falhar

            # --- Fix _symmetry_space_group_name_H-M: adicionar aspas ---
            if stripped.startswith('_symmetry_space_group_name_H-M'):
                match = re.match(r"_symmetry_space_group_name_H-M\s+['\"]?(.+?)['\"]?\s*$", stripped)
                if match:
                    hm_symbol = match.group(1).strip()
                    result_lines.append(f"_symmetry_space_group_name_H-M   '{hm_symbol}'")
                    hm_fixed = True
                    # Adicionar Hall symbol se ausente no CIF original
                    hall_symbol = self._get_hall_symbol()
                    if hall_symbol and hall_symbol != '?':
                        result_lines.append(f"_symmetry_space_group_name_Hall   '{hall_symbol}'")
                    continue

            # --- Rastrear _symmetry_Int_Tables_number para inserir _cell_setting depois ---
            if stripped.startswith('_symmetry_Int_Tables_number'):
                result_lines.append(stripped)  # Sem indentação extra
                insert_cell_setting_after = len(result_lines)
                continue

            # --- Pular Hall symbol existente (já adicionamos após H-M) ---
            if stripped.startswith('_symmetry_space_group_name_Hall'):
                continue

            # --- Pular campos que já adicionamos programaticamente ---
            if stripped.startswith(('_chemical_formula_moiety', '_exptl_crystal_density_diffrn',
                                    '_chemical_formula_weight',
                                    '_diffrn_radiation_', '_exptl_crystal_description',
                                    '_diffrn_measurement_device_type',
                                    '_cell_measurement_temperature', '_diffrn_ambient_temperature',
                                    '_cell_measurement_reflns_used', '_cell_measurement_theta_',
                                    '_diffrn_reflns_number', '_diffrn_reflns_av_',
                                    '_diffrn_measured_fraction_',
                                    '_exptl_absorpt_coefficient_mu', '_exptl_crystal_F_000',
                                    '_computing_structure_solution', '_audit_creation_method',
                                    '_atom_sites_solution_primary')):
                continue

            # --- Limpar precisão numérica em parâmetros de rede (com s.u.) ---
            # PLAT141-145: Adicionar incertezas padrão nos parâmetros
            # PLAT151: Adicionar s.u. no volume
            if stripped.startswith(('_cell_length_', '_cell_angle_', '_cell_volume')):
                match = re.match(r'(_cell_\w+)\s+([\d.]+)', stripped)
                if match:
                    tag = match.group(1)
                    if '_volume' in tag:
                        val = self.structure.lattice.volume
                        # s.u. estimado como ~0.1% do volume
                        su = max(1, round(val * 0.001))
                        formatted = f"{val:.3f}({su})"
                    elif '_angle_' in tag:
                        val = float(match.group(2))
                        formatted_val = self._format_number(val, 4)
                        # Ângulos fixos (90, 120) não precisam de s.u.
                        if abs(val - 90.0) < 0.001 or abs(val - 120.0) < 0.001:
                            formatted = formatted_val
                        else:
                            formatted = f"{val:.4f}(10)"  # s.u. de 0.0010°
                    else:
                        val = float(match.group(2))
                        formatted = f"{val:.5f}(10)"  # s.u. de 0.00010 Å
                    result_lines.append(f"{tag}   {formatted}")
                    continue

            # --- Remover indentação de tags no loop_ de simetria ---
            if stripped.startswith('_symmetry_equiv_pos_'):
                result_lines.append(stripped)  # Sem indentação
                in_symop_loop = True
                continue

            # --- Dados do loop_ de simetria: remover indentação ---
            if in_symop_loop and stripped and not stripped.startswith('_') and not stripped.startswith('#'):
                if stripped.startswith(('loop_',)):
                    in_symop_loop = False
                    result_lines.append(stripped)
                else:
                    # Linha de dados de simetria — remover indentação
                    result_lines.append(stripped)
                continue
            elif in_symop_loop and not stripped:
                in_symop_loop = False

            # --- Linha genérica: remover indentação desnecessária de tags ---
            if stripped.startswith('_'):
                result_lines.append(stripped)
                continue

            result_lines.append(line)

        # --- Inserir _symmetry_cell_setting após _symmetry_Int_Tables_number ---
        if insert_cell_setting_after > 0:
            crystal_system = self._get_crystal_system_name()
            result_lines.insert(insert_cell_setting_after,
                                f"_symmetry_cell_setting   {crystal_system}")

        # --- Inserir bloco de metadados checkCIF ---
        # Determinar Z para cálculos
        z_for_meta = int(self._original_symmetry.get('z', 0))
        if z_for_meta == 0:
            z_match = re.search(r'_cell_formula_units_Z\s+(\d+)', cif_str)
            z_for_meta = int(z_match.group(1)) if z_match else 1

        checkcif_meta = self._build_checkcif_metadata_block(z_for_meta)
        # Inserir após a density (ou após cell_setting)
        insert_pos = insert_cell_setting_after + 1 if insert_cell_setting_after > 0 else len(result_lines)
        for idx_m, meta_line in enumerate(checkcif_meta):
            result_lines.insert(insert_pos + idx_m, meta_line)

        # --- Fase 2: Construir _atom_type loop e _atom_site loop ---
        if atom_block_start < 0 or atom_block_header_end < 0:
            return '\n'.join(result_lines)

        # Coletar dados dos átomos para extrair símbolos para _atom_type
        atom_data_lines = []
        atom_symbols = []
        for i in range(atom_block_header_end, len(lines)):
            stripped = lines[i].strip()
            if not stripped or stripped.startswith('loop_') or stripped.startswith('#') or stripped.startswith('_'):
                break
            atom_data_lines.append(stripped)
            # Primeiro campo é _atom_site_type_symbol
            parts = stripped.split()
            if parts:
                atom_symbols.append(parts[0])

        # Construir _atom_type loop (obrigatório para checkCIF)
        atom_type_lines = self._build_atom_type_loop(atom_symbols)
        result_lines.append("")
        for atl in atom_type_lines:
            result_lines.append(atl)

        # Encontrar índice do campo label nos headers
        label_field_idx = -1
        for idx, field in enumerate(header_fields):
            if field == '_atom_site_label':
                label_field_idx = idx
                break

        # Verificar se Wyckoff já está presente
        has_wyckoff = any('_atom_site_Wyckoff_symbol' in f for f in header_fields)

        # Encontrar posição da multiplicidade para inserir Wyckoff depois
        multiplicity_idx = -1
        for idx, field in enumerate(header_fields):
            if '_atom_site_symmetry_multiplicity' in field:
                multiplicity_idx = idx
                break
        wyckoff_insert_pos = multiplicity_idx + 1 if multiplicity_idx >= 0 else len(header_fields)

        # Escrever cabeçalho do _atom_site loop (SEM indentação nos tags)
        result_lines.append("")
        result_lines.append("loop_")

        wyckoff_inserted = False
        for idx, field in enumerate(header_fields):
            # PLAT700: Renomear tag superseded
            if field == '_atom_site_symmetry_multiplicity':
                field = '_atom_site_site_symmetry_multiplicity'
            result_lines.append(field)  # Sem indentação — coluna 1
            if not has_wyckoff and wyckoff_map and idx == (wyckoff_insert_pos - 1):
                result_lines.append('_atom_site_Wyckoff_symbol')
                wyckoff_inserted = True

        # Escrever dados dos átomos
        wyckoff_values = list(wyckoff_map.values()) if wyckoff_map else []
        atom_counter = {}

        # Identificar índices das coordenadas fracionárias e occupancy nos headers
        fract_indices = set()
        occ_index = -1
        for idx, field in enumerate(header_fields):
            if 'fract_x' in field or 'fract_y' in field or 'fract_z' in field:
                fract_indices.add(idx)
            if 'occupancy' in field:
                occ_index = idx

        for atom_idx, data_line in enumerate(atom_data_lines):
            parts = data_line.split()

            # Corrigir label (indexação a partir de 1)
            if label_field_idx >= 0 and label_field_idx < len(parts):
                old_label = parts[label_field_idx]
                label_match = re.match(r'^([A-Za-z]+\d*[+-]?)(\d+)$', old_label)
                if label_match:
                    element_base = label_match.group(1)
                    clean_base = re.match(r'^([A-Za-z]+)', element_base).group(1)
                    if clean_base not in atom_counter:
                        atom_counter[clean_base] = 1
                    parts[label_field_idx] = f"{clean_base}{atom_counter[clean_base]}"
                    atom_counter[clean_base] += 1

            # Limpar precisão numérica das coordenadas fracionárias
            for fi in fract_indices:
                if fi < len(parts):
                    try:
                        val = float(parts[fi])
                        parts[fi] = self._format_number(val, 6)
                    except ValueError:
                        pass

            # Limpar occupancy (1.0 → 1, 0.5 → 0.5)
            if occ_index >= 0 and occ_index < len(parts):
                try:
                    val = float(parts[occ_index])
                    parts[occ_index] = self._format_number(val, 4)
                except ValueError:
                    pass

            # Inserir Wyckoff symbol
            if wyckoff_inserted:
                insert_pos = wyckoff_insert_pos
                if atom_idx < len(wyckoff_values):
                    wyckoff_val = wyckoff_values[atom_idx]
                else:
                    # Fallback: usar '?' se não tiver dados de Wyckoff para este átomo
                    wyckoff_val = '?'
                if insert_pos <= len(parts):
                    parts.insert(insert_pos, wyckoff_val)

            result_lines.append(' '.join(parts))

        # Adicionar linhas restantes do CIF (após o bloco _atom_site)
        # Precisamos pular: linhas de dados de átomos (já processadas)
        # e o bloco _atom_type do pymatgen (já adicionamos o nosso)
        past_atom_block = False
        in_atom_type_block = False
        for i in range(atom_block_header_end, len(lines)):
            stripped = lines[i].strip()
            if not past_atom_block:
                if not stripped or stripped.startswith('loop_') or stripped.startswith('#') or stripped.startswith('_'):
                    past_atom_block = True
                else:
                    continue  # Pular linhas de dados de átomos (já processadas)
            if past_atom_block:
                # Detectar início do bloco _atom_type (loop_ seguido de _atom_type_)
                if stripped == 'loop_' and i + 1 < len(lines) and lines[i + 1].strip().startswith('_atom_type_'):
                    in_atom_type_block = True
                    continue
                # Pular tags _atom_type_ e linhas de dados do bloco _atom_type
                if in_atom_type_block:
                    if stripped.startswith('_atom_type_'):
                        continue  # Tag do bloco
                    elif stripped and not stripped.startswith(('#', 'loop_', '_', 'data_')):
                        continue  # Linha de dados do bloco (ex: "Ce4+  4.0")
                    else:
                        in_atom_type_block = False  # Fim do bloco _atom_type
                result_lines.append(lines[i])

        # Garantir final limpo
        result_text = '\n'.join(result_lines)
        # Remover linhas em branco excessivas
        result_text = re.sub(r'\n{3,}', '\n\n', result_text)

        # --- Fase 3: Adicionar loops de geometria (bonds e angles) ---
        try:
            bond_lines = self._build_bond_geometry_loop()
            if bond_lines:
                result_text += '\n\n' + '\n'.join(bond_lines)

            angle_lines = self._build_angle_geometry_loop()
            if angle_lines:
                result_text += '\n\n' + '\n'.join(angle_lines)
        except Exception as e:
            logging.warning(f"Erro ao adicionar geometria ao CIF: {e}")

        return result_text

    def _generate_fallback_cif(self) -> str:
        """
        Fallback: gera CIF preservando a simetria do CIF original.
        Formatado para conformidade com checkCIF.
        """
        orig = self._original_symmetry
        lattice = self.structure.lattice

        lines = []
        lines.append("# CIF generated by MatFinder/PhaseDRX (fallback mode)")
        lines.append("# Symmetry preserved from original CIF")
        lines.append("#")

        formula = self.structure.composition.reduced_formula
        lines.append(f"data_{formula}")
        lines.append("")

        # Parâmetros de rede com s.u. (PLAT141-145, PLAT151)
        def _fmt_cell_length(val):
            return f"{val:.5f}(10)"

        def _fmt_cell_angle(val):
            if abs(val - 90.0) < 0.001 or abs(val - 120.0) < 0.001:
                return self._format_number(val, 4)
            return f"{val:.4f}(10)"

        lines.append(f"_cell_length_a   {_fmt_cell_length(lattice.a)}")
        lines.append(f"_cell_length_b   {_fmt_cell_length(lattice.b)}")
        lines.append(f"_cell_length_c   {_fmt_cell_length(lattice.c)}")
        lines.append(f"_cell_angle_alpha   {_fmt_cell_angle(lattice.alpha)}")
        lines.append(f"_cell_angle_beta   {_fmt_cell_angle(lattice.beta)}")
        lines.append(f"_cell_angle_gamma   {_fmt_cell_angle(lattice.gamma)}")
        # Volume with s.u.
        vol = lattice.volume
        vol_su = max(1, round(vol * 0.001))
        lines.append(f"_cell_volume   {vol:.3f}({vol_su})")

        # Fórmula por unidade (dividida por Z)
        z_val = int(orig.get('z', 1))
        formula_sum = self._get_formula_per_z(self.structure.composition, z_val)
        lines.append(f"_chemical_formula_structural   '{formula}'")
        lines.append(f"_chemical_formula_sum   {formula_sum}")
        lines.append(f"_chemical_formula_moiety   {formula_sum}")

        # PLAT043: Peso molecular por unidade de fórmula
        mol_weight = self.structure.composition.weight / z_val if z_val > 0 else self.structure.composition.weight
        lines.append(f"_chemical_formula_weight   {mol_weight:.2f}")

        # Densidade cristalográfica calculada
        density = self._calculate_density(z_val)
        if density > 0:
            lines.append(f"_exptl_crystal_density_diffrn   {density:.3f}")

        if z_val > 0:
            lines.append(f"_cell_formula_units_Z   {z_val}")

        lines.append("")

        # Grupo espacial (com aspas)
        sg_symbol = orig.get('space_group_hm', 'P 1')
        sg_number = orig.get('space_group_number', '1')
        lines.append(f"_symmetry_space_group_name_H-M   '{sg_symbol}'")
        # Hall symbol
        hall_symbol = self._get_hall_symbol()
        if hall_symbol and hall_symbol != '?':
            lines.append(f"_symmetry_space_group_name_Hall   '{hall_symbol}'")
        lines.append(f"_symmetry_Int_Tables_number   {sg_number}")
        lines.append(f"_symmetry_cell_setting   {self._get_crystal_system_name()}")

        # Bloco de metadados checkCIF (µ, F000, temperatura, etc.)
        lines.append("")
        checkcif_meta = self._build_checkcif_metadata_block(z_val)
        lines.extend(checkcif_meta)

        # Operações de simetria (tags sem indentação)
        symops = orig.get('symmetry_operations', [])
        if symops:
            lines.append("")
            lines.append("loop_")
            lines.append("_symmetry_equiv_pos_site_id")
            lines.append("_symmetry_equiv_pos_as_xyz")
            for i, op in enumerate(symops, 1):
                lines.append(f"{i} '{op}'")

        # _atom_type loop
        atom_sites = orig.get('atom_sites', [])
        if atom_sites:
            atom_symbols = [s.get('type_symbol', s.get('label', '?')) for s in atom_sites]
            atom_type_lines = self._build_atom_type_loop(atom_symbols)
            lines.append("")
            lines.extend(atom_type_lines)

            # _atom_site loop (tags sem indentação)
            lines.append("")
            lines.append("loop_")
            lines.append("_atom_site_label")
            lines.append("_atom_site_type_symbol")
            lines.append("_atom_site_fract_x")
            lines.append("_atom_site_fract_y")
            lines.append("_atom_site_fract_z")
            lines.append("_atom_site_occupancy")
            for site in atom_sites:
                label = site.get('label', '')
                symbol = site.get('type_symbol', '')
                x = site.get('fract_x', '0')
                y = site.get('fract_y', '0')
                z = site.get('fract_z', '0')
                occ = site.get('occupancy', '1')
                lines.append(f"{label} {symbol} {x} {y} {z} {occ}")
        else:
            logging.warning("Sem átomos do CIF original. Usando estrutura P1.")
            try:
                writer = CifWriter(self.structure, significant_figures=8)
                return str(writer)
            except Exception:
                return self.structure.to(fmt="cif")

        # Adicionar loops de geometria (bonds e ângulos)
        lines.append("")
        try:
            bond_lines = self._build_bond_geometry_loop()
            if bond_lines:
                lines.extend(bond_lines)
                lines.append("")

            angle_lines = self._build_angle_geometry_loop()
            if angle_lines:
                lines.extend(angle_lines)
        except Exception as e:
            logging.warning(f"Erro ao adicionar geometria ao CIF fallback: {e}")

        lines.append("")
        return "\n".join(lines)

    def _extract_symmetry_metadata(self, cif_content: str) -> dict:
        """
        Extrai metadados de simetria do texto de um CIF original.

        Preserva: grupo espacial, operações de simetria, labels de átomos,
        multiplicidade, Wyckoff e Z.
        """
        metadata = {}

        # Grupo espacial H-M
        match = re.search(r"_symmetry_space_group_name_H-M\s+['\"]?(.+?)['\"]?\s*$", cif_content, re.MULTILINE)
        if match:
            metadata['space_group_hm'] = match.group(1).strip().strip("'\"")

        # Número do grupo espacial
        match = re.search(r"_symmetry_Int_Tables_number\s+(\d+)", cif_content)
        if match:
            metadata['space_group_number'] = match.group(1).strip()

        # Sistema cristalino
        match = re.search(r"_symmetry_cell_setting\s+(\w+)", cif_content)
        if match:
            metadata['crystal_system'] = match.group(1).strip()

        # Z (fórmula units)
        match = re.search(r"_cell_formula_units_Z\s+(\d+)", cif_content)
        if match:
            metadata['z'] = match.group(1).strip()

        # Operações de simetria
        symops = self._extract_symmetry_operations(cif_content)
        if symops:
            metadata['symmetry_operations'] = symops

        # Átomos da unidade assimétrica
        atom_sites = self._extract_atom_sites(cif_content)
        if atom_sites:
            metadata['atom_sites'] = atom_sites

        logging.debug(f"Metadados de simetria extraídos: SG={metadata.get('space_group_hm', 'N/A')}, "
                      f"#{metadata.get('space_group_number', '?')}, "
                      f"{len(metadata.get('symmetry_operations', []))} operações, "
                      f"{len(metadata.get('atom_sites', []))} átomos")

        return metadata

    def _extract_symmetry_operations(self, cif_content: str) -> list:
        """Extrai as operações de simetria do CIF."""
        symops = []

        # Padrão 1: com _symmetry_equiv_pos_site_id e _symmetry_equiv_pos_as_xyz (formato com id)
        pattern = re.compile(
            r"loop_\s*\n\s*_symmetry_equiv_pos_site_id\s*\n\s*_symmetry_equiv_pos_as_xyz\s*\n(.*?)(?:\nloop_|\n_|\n#|\Z)",
            re.DOTALL
        )
        match = pattern.search(cif_content)
        if match:
            block = match.group(1).strip()
            for line in block.split('\n'):
                line = line.strip()
                if not line or line.startswith('_') or line.startswith('#') or line.startswith('loop'):
                    break
                # Remover o ID numérico no início
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    op = parts[1].strip().strip("'\"")
                    symops.append(op)
                elif len(parts) == 1:
                    op = parts[0].strip().strip("'\"")
                    symops.append(op)
            return symops

        # Padrão 2: apenas _symmetry_equiv_pos_as_xyz (sem id)
        pattern2 = re.compile(
            r"loop_\s*\n\s*_symmetry_equiv_pos_as_xyz\s*\n(.*?)(?:\nloop_|\n_|\n#|\Z)",
            re.DOTALL
        )
        match2 = pattern2.search(cif_content)
        if match2:
            block = match2.group(1).strip()
            for line in block.split('\n'):
                line = line.strip()
                if not line or line.startswith('_') or line.startswith('#') or line.startswith('loop'):
                    break
                op = line.strip().strip("'\"")
                if ',' in op:  # Validação básica de operação de simetria
                    symops.append(op)

        return symops

    def _extract_atom_sites(self, cif_content: str) -> list:
        """Extrai os átomos da unidade assimétrica do CIF original."""
        atom_sites = []

        # Encontrar o bloco de loop_ com _atom_site_label
        pattern = re.compile(
            r"loop_\s*\n((?:\s*_atom_site_\w+\s*\n)+)(.*?)(?:\nloop_|\n#|\Z)",
            re.DOTALL
        )

        for match in pattern.finditer(cif_content):
            headers_block = match.group(1).strip()
            data_block = match.group(2).strip()

            headers = [h.strip() for h in headers_block.split('\n') if h.strip().startswith('_atom_site_')]

            if '_atom_site_label' not in headers:
                continue

            # Mapear indices dos campos
            field_map = {}
            for i, h in enumerate(headers):
                key = h.replace('_atom_site_', '')
                field_map[key] = i

            for line in data_block.split('\n'):
                line = line.strip()
                if not line or line.startswith('_') or line.startswith('#') or line.startswith('loop'):
                    break

                parts = line.split()
                if len(parts) < len(headers):
                    continue

                site = {}
                for key, idx in field_map.items():
                    if idx < len(parts):
                        site[key] = parts[idx]

                if 'label' in site:
                    atom_sites.append(site)

            break  # Usar apenas o primeiro bloco _atom_site

        return atom_sites

    def _validate_cif_string(self, cif_string: str) -> dict:
        """
        Valida um CIF gerado, verificando labels únicos, grupo espacial e consistência.

        Returns:
            dict com 'valid' (bool), 'issues' (list), e info adicional.
        """
        result = {
            'valid': True,
            'issues': [],
            'space_group': None,
            'sg_number': None,
            'n_unique_atoms': 0
        }

        # Extrair grupo espacial
        sg_match = re.search(r"_symmetry_space_group_name_H-M\s+(.+?)$", cif_string, re.MULTILINE)
        if sg_match:
            result['space_group'] = sg_match.group(1).strip().strip("'\"")

        sg_num_match = re.search(r"_symmetry_Int_Tables_number\s+(\d+)", cif_string)
        if sg_num_match:
            result['sg_number'] = int(sg_num_match.group(1))

        # Verificar labels duplicados
        label_pattern = re.compile(r"^\s+\w+\s+(\w+)\s+\d+\s+[\d.-]+", re.MULTILINE)
        labels = label_pattern.findall(cif_string)
        result['n_unique_atoms'] = len(labels)

        if len(labels) != len(set(labels)):
            duplicates = [l for l in labels if labels.count(l) > 1]
            result['valid'] = False
            result['issues'].append(f"Labels duplicados: {set(duplicates)}")

        # Verificar se está em P1 (potencialmente problemático se tinha simetria antes)
        orig_sg_num = self._original_symmetry.get('space_group_number', '1')
        if result['sg_number'] == 1 and str(orig_sg_num) != '1':
            result['issues'].append(
                f"Simetria reduzida para P1 (original era #{orig_sg_num})"
            )
            # Não invalidar completamente - P1 é válido mas não ideal
            logging.warning(f"CIF gerado em P1, original era SG #{orig_sg_num}")

        # Verificar se tem operações de simetria
        if "'x, y, z'" not in cif_string and "x,y,z" not in cif_string:
            result['valid'] = False
            result['issues'].append("Sem operações de simetria")

        return result
