# cif_handler.py
# Módulo para manipulação de parâmetros de arquivos CIF usando pymatgen.
# Versão 2.0 - Adicionada lógica de restrições cristalográficas.
# (Este arquivo não precisa de alterações para a nova funcionalidade)

import numpy as np
import logging

try:
    from pymatgen.core import Structure, Lattice
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False
    logging.warning("Pymatgen não encontrado. A manipulação de CIF não funcionará.")


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

        try:
            self.structure = Structure.from_str(cif_content, fmt="cif")
            self.analyzer = SpacegroupAnalyzer(self.structure)
        except Exception as e:
            logging.error(f"Falha ao analisar a string do CIF: {e}")
            raise ValueError(f"Não foi possível analisar o conteúdo do CIF. Erro: {e}")

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
            # Trigonal/Romboédrico: a = b = c, α = β = γ ≠ 90°
            new_b, new_c = new_a, new_a
            new_beta, new_gamma = new_alpha, new_alpha
        elif crystal_system == 'orthorhombic':
            # Ortorrômbico: a ≠ b ≠ c, α = β = γ = 90°
            new_alpha, new_beta, new_gamma = 90.0, 90.0, 90.0
        elif crystal_system == 'monoclinic':
            # Monoclínico: a ≠ b ≠ c, α = γ = 90°, β ≠ 90°
            new_alpha, new_gamma = 90.0, 90.0
        # Triclínico: a ≠ b ≠ c, α ≠ β ≠ γ (sem restrições)

        try:
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
        self.structure.scale_lattice(new_volume)
        logging.info(f"Volume escalado para {self.structure.lattice.volume:.2f}")

    def get_cif_string(self) -> str:
        """
        Gera uma string no formato CIF a partir da estrutura atual.
        """
        try:
            return self.structure.to(fmt="cif")
        except Exception as e:
            logging.error(f"Não foi possível converter a estrutura para o formato CIF: {e}")
            return f"# ERRO: Não foi possível gerar o CIF. {e}"
