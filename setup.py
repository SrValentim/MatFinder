import sys
import os
import pymatgen  # <<< ADICIONADO para encontrar o caminho do pacote
from cx_Freeze import setup, Executable

# --- CONFIGURAÇÃO ---
APP_NAME = "MatFinder"
# --- ALTERAÇÃO DE REATORAÇÃO 1: Script Principal ---
# Agora aponta para o novo ponto de entrada na raiz
MAIN_SCRIPT = "run_matfinder.py"
APP_VERSION = "3.23.0"
# --- ALTERAÇÃO DE REATORAÇÃO 2: Caminho do Ícone ---
# Aponta para a nova pasta 'matfinder/assets/icons/'
ICON_FILE = os.path.join("matfinder", "assets", "icons", "polvo.ico")

# --- Dependências ---
# --- ALTERAÇÃO DE REATORAÇÃO 3: Adicionar Pacote 'matfinder' ---
# Adicionamos "matfinder" para que o cx_Freeze inclua todo o seu código-fonte
packages_to_include = ["matfinder", "PySide6", "requests", "pymatgen", "numpy", "scipy", "bs4", "pkg_resources"]

# <<< INÍCIO DA CORREÇÃO >>>
# Encontra o caminho completo para a pasta do pacote pymatgen
pymatgen_path = os.path.dirname(pymatgen.__file__)
# <<< FIM DA CORREÇÃO >>>

# --- Arquivos de Dados ---
# Lista de tuplas (arquivo_ou_pasta_origem, pasta_destino_na_build)
# --- ALTERAÇÃO DE REATORAÇÃO 4: Caminhos dos Assets ---
files_to_include = [
    # (Origem, Destino na build)
    (os.path.join("matfinder", "assets", "logos"), os.path.join("matfinder", "assets", "logos")),
    ("docs", "docs"),  # (A pasta 'doc' foi renomeada para 'docs')
    # <<< ADICIONADO: Copia a pasta inteira da pymatgen para a pasta 'lib' da build
    # Isso garante que todos os arquivos de dados (.yml, .json, etc.) sejam incluídos.
    (pymatgen_path, "lib/pymatgen"),
]

# Adiciona o arquivo de configuração e histórico apenas se eles existirem
config_path = os.path.join("matfinder", "assets", "config", "config.txt")
if os.path.exists(config_path):
    files_to_include.append((config_path, config_path))

# --- ALTERAÇÃO DE REATORAÇÃO 5: Remover Ficheiros de Utilizador ---
# Removemos a inclusão de 'historico_buscas.json'
# Ficheiros de dados do utilizador não devem ser incluídos no instalador.


# --- Opções da Build ---
build_exe_options = {
    "packages": packages_to_include,
    "include_files": files_to_include,
    "excludes": ["tkinter", "unittest"],  # Exclui o tkinter e unittest
    # Adicionado para evitar alguns avisos comuns, mas inofensivos
    "zip_include_packages": ["*"],
    "zip_exclude_packages": [],
}

# --- Configuração do Executável ---
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executable = Executable(
    script=MAIN_SCRIPT,
    base=base,
    target_name=f"{APP_NAME}.exe",
    icon=ICON_FILE
)

# --- Chamada Principal do Setup ---
setup(
    name=APP_NAME,
    version=APP_VERSION,
    description="MatFinder - Ferramenta de Consulta de Materiais",
    options={"build_exe": build_exe_options},
    executables=[executable]
)