#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
version_manager.py
Gerenciador de versões do MatFinder

Uso:
    python version_manager.py --show          # Mostra versão atual
    python version_manager.py --set 4.5.0     # Define nova versão
    python version_manager.py --bump patch    # Incrementa patch (4.4.0 -> 4.4.1)
    python version_manager.py --bump minor    # Incrementa minor (4.4.0 -> 4.5.0)
    python version_manager.py --bump major    # Incrementa major (4.4.0 -> 5.0.0)

Copyright (C) 2025 Raynner Valentim (UFAM)
"""

import argparse
import json
import os
import re
import sys


def get_root_dir():
    """Retorna o diretório raiz do projeto."""
    return os.path.dirname(os.path.abspath(__file__))


def read_version():
    """Lê a versão atual do arquivo VERSION."""
    version_file = os.path.join(get_root_dir(), 'VERSION')
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"


def write_version(version):
    """Escreve a versão no arquivo VERSION."""
    version_file = os.path.join(get_root_dir(), 'VERSION')
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version + '\n')


def parse_version(version_str):
    """Converte string de versão em tupla (major, minor, patch)."""
    match = re.match(r'^(\d+)\.(\d+)(?:\.(\d+))?$', version_str)
    if not match:
        raise ValueError(f"Formato de versão inválido: {version_str}")
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3)) if match.group(3) else 0
    return major, minor, patch


def bump_version(current_version, bump_type):
    """Incrementa a versão baseado no tipo de bump."""
    major, minor, patch = parse_version(current_version)

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Tipo de bump inválido: {bump_type}")

    return f"{major}.{minor}.{patch}"


def update_init_file(version):
    """Atualiza o arquivo __init__.py com a nova versão."""
    init_file = os.path.join(get_root_dir(), 'matfinder', '__init__.py')
    major, minor, patch = parse_version(version)

    # Versão simplificada (sem patch se for 0)
    simple_version = f"{major}.{minor}" if patch == 0 else f"{major}.{minor}.{patch}"

    content = f'''"""
MatFinder - Ferramenta de busca de materiais cristalográficos
Copyright (C) 2025 Raynner Valentim (UFAM)

Sistema centralizado de versionamento
"""

# Versão do programa - ALTERE APENAS AQUI OU USE version_manager.py
__version__ = "{simple_version}"
__version_info__ = ({major}, {minor}, {patch})  # (major, minor, patch)

# Informações do programa
__author__ = "Raynner Valentim"
__email__ = "Raynnervalentim@hotmail.com"
__institution__ = "Universidade Federal do Amazonas - UFAM"

def get_version():
    """Retorna a versão formatada."""
    return __version__

def get_full_title():
    """Retorna o título completo com versão."""
    return f"MatFinder Ver. {{__version__}}"
'''

    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Atualizado: {init_file}")


def update_translation_files(version):
    """Atualiza os arquivos de tradução com a nova versão."""
    translations_dir = os.path.join(get_root_dir(), 'matfinder', 'assets', 'translations')

    major, minor, patch = parse_version(version)
    simple_version = f"{major}.{minor}" if patch == 0 else f"{major}.{minor}.{patch}"
    title = f"MatFinder Ver. {simple_version}"

    for filename in ['pt_BR.json', 'en_US.json', 'de_DE.json']:
        filepath = os.path.join(translations_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'app' in data and 'title' in data['app']:
                    data['app']['title'] = title

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"✓ Atualizado: {filepath}")
            except Exception as e:
                print(f"✗ Erro ao atualizar {filepath}: {e}")


def update_setup_file(version):
    """Atualiza o arquivo setup.py com a nova versão."""
    setup_file = os.path.join(get_root_dir(), 'setup.py')
    if not os.path.exists(setup_file):
        return

    try:
        with open(setup_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Atualiza version="X.X.X"
        content = re.sub(
            r'version\s*=\s*["\'][\d.]+["\']',
            f'version="{version}"',
            content
        )

        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ Atualizado: {setup_file}")
    except Exception as e:
        print(f"✗ Erro ao atualizar {setup_file}: {e}")


def update_all(version):
    """Atualiza todos os arquivos com a nova versão."""
    print(f"\n📦 Atualizando versão para: {version}\n")

    write_version(version)
    print(f"✓ Atualizado: VERSION")

    update_init_file(version)
    update_translation_files(version)
    update_setup_file(version)

    print(f"\n✅ Versão atualizada com sucesso para {version}!")
    print("\nPróximos passos sugeridos:")
    print("  1. Testar o programa")
    print("  2. Commitar alterações: git commit -am 'Bump version to {}'".format(version))
    print("  3. Criar tag: git tag v{}".format(version))


def main():
    parser = argparse.ArgumentParser(
        description='Gerenciador de versões do MatFinder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python version_manager.py --show
  python version_manager.py --set 4.5.0
  python version_manager.py --bump patch
  python version_manager.py --bump minor
  python version_manager.py --bump major
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--show', action='store_true', help='Mostra a versão atual')
    group.add_argument('--set', metavar='VERSION', help='Define uma nova versão (ex: 4.5.0)')
    group.add_argument('--bump', choices=['major', 'minor', 'patch'], help='Incrementa a versão')

    args = parser.parse_args()

    current_version = read_version()

    if args.show:
        print(f"\n📦 MatFinder")
        print(f"   Versão atual: {current_version}")
        major, minor, patch = parse_version(current_version)
        print(f"   Versão info: ({major}, {minor}, {patch})")
        print()
        return

    if args.set:
        try:
            parse_version(args.set)  # Valida o formato
            update_all(args.set)
        except ValueError as e:
            print(f"❌ Erro: {e}")
            sys.exit(1)
        return

    if args.bump:
        try:
            new_version = bump_version(current_version, args.bump)
            print(f"📈 Bump {args.bump}: {current_version} → {new_version}")
            update_all(new_version)
        except ValueError as e:
            print(f"❌ Erro: {e}")
            sys.exit(1)
        return


if __name__ == '__main__':
    main()
