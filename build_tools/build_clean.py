#!/usr/bin/env python
"""
build_clean.py - Pipeline de compilação OTIMIZADA do MatFinder.

Faz tudo de uma vez:
  1) limpa build/ e dist/
  2) compila com build_tools/MatFinder.spec
  3) roda o SMOKE TEST headless (MatFinder.exe --selftest) -> pega módulo
     faltante em ~10s, sem precisar abrir a GUI e clicar por 15 min
  4) imprime o tamanho final e os 15 maiores arquivos

COMO RODAR (sempre com o python do VENV LIMPO):
    .venv-build\\Scripts\\python build_tools\\build_clean.py

Por que o venv limpo importa: o PyInstaller empacota o que está IMPORTÁVEL no
ambiente. Rodando do venv gigante do PyCharm, ele arrasta jupyter/jax/opencv/etc.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC = os.path.join(HERE, "MatFinder.spec")
DIST_APP = os.path.join(ROOT, "dist", "MatFinder")
EXE = os.path.join(DIST_APP, "MatFinder.exe")


def sh(title, cmd, **kw):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    print(">", " ".join(cmd))
    return subprocess.run(cmd, **kw)


def folder_size_mb(path):
    total = 0
    for dp, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(dp, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)


def biggest_files(path, n=15):
    items = []
    for dp, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(dp, f)
            if os.path.exists(fp):
                items.append((os.path.relpath(fp, path), os.path.getsize(fp) / (1024 * 1024)))
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:n]


def main():
    print(f"Python do build : {sys.executable}")
    print(f"Raiz do projeto : {ROOT}")
    if "venv-build" not in sys.executable and "--allow-any-venv" not in sys.argv:
        print("\n[!] ATENÇÃO: você NÃO está usando o .venv-build dedicado.")
        print("    Rode:  .venv-build\\Scripts\\python build_tools\\build_clean.py")
        print("    (ou passe --allow-any-venv se souber o que está fazendo)")
        return 2

    full = ("--clean" in sys.argv) or ("--full" in sys.argv)
    gen_file = os.path.join(HERE, "hiddenimports_generated.txt")

    # 0) Fecho real de imports (hiddenimports_generated.txt). Só (re)gera se faltar
    #    ou se pedirem --regen/--full. Pular isto economiza ~1 min em builds repetidos.
    gen = os.path.join(HERE, "gen_hiddenimports.py")
    if (not os.path.exists(gen_file)) or ("--regen" in sys.argv) or full:
        r = sh("PASSO 1/3  -  Mapeando imports reais (gen_hiddenimports.py)",
               [sys.executable, gen], cwd=ROOT)
        if r.returncode != 0:
            print("\n[!] AVISO: gen_hiddenimports.py falhou; seguindo com o que houver.")
    else:
        print("\nPASSO 1/3  -  Mapa de imports reutilizado (use --regen para refazer).")

    # 1) PyInstaller. Por padrão NÃO usa --clean (reusa o cache em build/ -> bem
    #    mais rápido). Use 'build_clean.py --clean' para um rebuild do zero.
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", SPEC]
    if full:
        cmd.insert(3, "--clean")
    r = sh("PASSO 2/3  -  Compilando com PyInstaller" + ("  [--clean]" if full else "  [cache]"),
           cmd, cwd=ROOT)
    if r.returncode != 0:
        print("\n[X] Falha na compilação do PyInstaller.")
        return r.returncode

    if not os.path.exists(EXE):
        print(f"\n[X] Executável não encontrado em {EXE}")
        return 1

    # 2) Smoke test headless do .exe congelado
    report = os.path.join(ROOT, "selftest_report.txt")
    if os.path.exists(report):
        os.remove(report)
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", MATFINDER_SELFTEST_REPORT=report)
    r = sh("PASSO 3/3  -  Smoke test (MatFinder.exe --selftest)",
           [EXE, "--selftest"], cwd=ROOT, env=env, timeout=180)

    print("\n----- relatório do selftest -----")
    if os.path.exists(report):
        with open(report, encoding="utf-8") as fh:
            print(fh.read())
    else:
        print("(sem relatório; exe windowed pode não ter escrito - confira o exit code)")

    # 3) Tamanho
    size = folder_size_mb(DIST_APP)
    print(f"\n{'=' * 70}\nTAMANHO FINAL: {size:.1f} MB  ({DIST_APP})\n{'=' * 70}")
    print("Maiores arquivos:")
    for name, mb in biggest_files(DIST_APP):
        print(f"  {mb:8.1f} MB  {name}")

    if r.returncode == 0:
        print("\n[OK] BUILD + SELFTEST PASSARAM. App pronto em dist/MatFinder/")
        return 0
    print(f"\n[X] SELFTEST FALHOU (exit {r.returncode}). Veja os módulos acima e ajuste o spec.")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
