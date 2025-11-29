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
        Gera uma string no formato CIF a partir da estrutura atual.
        """
        try:
            return self.structure.to(fmt="cif")
        except Exception as e:
            logging.error(f"Não foi possível converter a estrutura para o formato CIF: {e}")
            return f"# ERRO: Não foi possível gerar o CIF. {e}"
