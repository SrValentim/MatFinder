# build_optimized.py
"""
Script de compilação otimizado para MatFinder
Autor: Raynner Valentim - UFAM
Versão: 3.23.0

Este script automatiza o processo de compilação do MatFinder usando PyInstaller
com configurações otimizadas para reduzir o tamanho final.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configurações
APP_NAME = "MatFinder"
APP_VERSION = "3.23.0"
SPEC_FILE = "MatFinder.spec"

# Cores para output no terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprime cabeçalho formatado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_step(step_num, text):
    """Imprime passo da compilação"""
    print(f"{Colors.OKCYAN}[PASSO {step_num}]{Colors.ENDC} {text}")

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    """Imprime aviso"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    """Imprime erro"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def clean_build_dirs():
    """Limpa diretórios de build anteriores"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Removendo {dir_name}/...")
            shutil.rmtree(dir_name)
            print_success(f"Diretório {dir_name}/ removido")

    # Limpar arquivos .pyc e __pycache__
    print("Limpando arquivos temporários Python...")
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
    print_success("Arquivos temporários removidos")

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    print("Verificando dependências...")

    # Mapeamento correto de nomes de pacotes para módulos
    required_packages = {
        'PyInstaller': 'PyInstaller',
        'PySide6': 'PySide6',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy',
        'scipy': 'scipy',
        'pymatgen': 'pymatgen',
        'mp-api': 'mp_api',
    }

    missing = []
    for package_name, module_name in required_packages.items():
        try:
            __import__(module_name)
            print_success(f"{package_name} instalado")
        except ImportError:
            missing.append(package_name)
            print_error(f"{package_name} NÃO encontrado")

    if missing:
        print_error(f"\nFaltam pacotes: {', '.join(missing)}")
        print("Instale com: pip install " + ' '.join(missing))
        return False

    return True

def get_folder_size(folder_path):
    """Calcula o tamanho de uma pasta em MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)  # Converter para MB

def run_pyinstaller():
    """Executa o PyInstaller com o arquivo spec"""
    print(f"Compilando {APP_NAME} v{APP_VERSION}...")
    print("Isso pode levar alguns minutos...\n")

    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        SPEC_FILE
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_success("Compilação concluída com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print_error("Erro durante a compilação!")
        print(e.stderr)
        return False

def analyze_build():
    """Analisa o resultado da compilação"""
    dist_path = Path('dist') / APP_NAME

    if not dist_path.exists():
        print_error("Diretório dist/ não encontrado!")
        return

    print("\n" + "="*60)
    print("ANÁLISE DO BUILD")
    print("="*60)

    # Tamanho total
    total_size = get_folder_size(dist_path)
    print(f"Tamanho total: {total_size:.2f} MB")

    # Arquivo executável
    exe_path = dist_path / f"{APP_NAME}.exe"
    if exe_path.exists():
        exe_size = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"Executável: {exe_size:.2f} MB")

    # Contar arquivos
    file_count = sum([len(files) for _, _, files in os.walk(dist_path)])
    print(f"Número de arquivos: {file_count}")

    # Maiores arquivos
    print("\nMaiores arquivos (Top 10):")
    files_with_size = []
    for dirpath, dirnames, filenames in os.walk(dist_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath) / (1024 * 1024)
                rel_path = os.path.relpath(filepath, dist_path)
                files_with_size.append((rel_path, size))

    files_with_size.sort(key=lambda x: x[1], reverse=True)
    for i, (file, size) in enumerate(files_with_size[:10], 1):
        print(f"  {i}. {file}: {size:.2f} MB")

def main():
    """Função principal"""
    print_header(f"COMPILAÇÃO OTIMIZADA - {APP_NAME} v{APP_VERSION}")

    # Passo 1: Verificar dependências
    print_step(1, "Verificando dependências")
    if not check_dependencies():
        sys.exit(1)

    # Passo 2: Limpar builds anteriores
    print_step(2, "Limpando builds anteriores")
    clean_build_dirs()

    # Passo 3: Compilar com PyInstaller
    print_step(3, "Compilando com PyInstaller")
    if not run_pyinstaller():
        sys.exit(1)

    # Passo 4: Analisar resultado
    print_step(4, "Analisando resultado")
    analyze_build()

    # Conclusão
    print_header("COMPILAÇÃO FINALIZADA COM SUCESSO!")
    print(f"\n{Colors.OKGREEN}O executável está em: dist/{APP_NAME}/{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Para criar o instalador MSI, execute: python scripts/build_msi.py{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\nCompilação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nErro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

