"""
MatFinder - Ferramenta de busca de materiais cristalográficos
Copyright (C) 2025 Raynner Valentim (UFAM)

Sistema centralizado de versionamento
"""

# Versão do programa - ALTERE APENAS AQUI
__version__ = "3.24"
__version_info__ = (3, 24, 0)  # (major, minor, patch)

# Informações do programa
__author__ = "Raynner Valentim"
__email__ = "Raynnervalentim@hotmail.com"
__institution__ = "Universidade Federal do Amazonas - UFAM"

def get_version():
    """Retorna a versão formatada."""
    return __version__

def get_full_title():
    """Retorna o título completo com versão."""
    return f"MatFinder Ver. {__version__}"
