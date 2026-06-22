#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
release.py - Release LOCAL do MatFinder, de um comando só.

Enquanto o GitHub Actions estiver bloqueado (problema de billing da conta), este
script faz TUDO que o workflow faria, localmente e na ordem certa:

    bump de versao  ->  build (2 exes)  ->  instalador (.exe)  ->  zip portatil
    ->  commit + tag  ->  push  ->  Release no GitHub (zip + instalador)

Assim que o Actions voltar, o mesmo resultado sai automatico ao dar push da tag;
este script continua util como fallback offline e para iterar rapido.

USO (rodar com o python do .venv-build):
    .venv-build\\Scripts\\python build_tools\\release.py --bump patch
    .venv-build\\Scripts\\python build_tools\\release.py --version 3.25.0
    ... --no-publish   # faz build+instalador+zip mas NAO commita/taggeia/sobe (ensaio)
    ... --no-build     # reusa o dist/ atual (pula a compilacao)

Requisitos: Inno Setup instalado; git autenticado (GCM, conta SrValentim).
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import version_manager as vm  # noqa: E402

REPO = "SrValentim/MatFinder"
API = f"https://api.github.com/repos/{REPO}"
UPLOADS = f"https://uploads.github.com/repos/{REPO}"


def step(msg):
    print(f"\n{'=' * 64}\n  {msg}\n{'=' * 64}")


def run(cmd):
    print(">", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"[X] Falhou (exit {r.returncode}): {' '.join(cmd)}")


def git_out(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def get_token():
    p = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    sys.exit("[X] Token do GitHub nao encontrado (git credential / GCM).")


def find_iscc():
    for p in (r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
              r"C:\Program Files\Inno Setup 6\ISCC.exe"):
        if os.path.exists(p):
            return p
    sys.exit("[X] Inno Setup (ISCC.exe) nao encontrado. Instale o Inno Setup 6.")


def api(method, url, token, payload=None, raw=None, content_type=None):
    headers = {"Authorization": f"token {token}", "User-Agent": "MatFinder-release",
               "Accept": "application/vnd.github+json"}
    data = raw
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        if method == "GET" and e.code == 404:
            return None
        sys.exit(f"[X] API {method} {url} -> {e.code}: {e.read().decode(errors='replace')[:300]}")


def main():
    ap = argparse.ArgumentParser(description="Release local do MatFinder")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--bump", choices=["major", "minor", "patch"])
    g.add_argument("--version", metavar="X.Y.Z")
    ap.add_argument("--no-build", action="store_true", help="reusa dist/ atual")
    ap.add_argument("--no-publish", action="store_true", help="nao commita/taggeia/sobe")
    args = ap.parse_args()

    py = sys.executable
    cur = vm.read_version()
    new = vm.bump_version(cur, args.bump) if args.bump else args.version
    major, minor, patch = vm.parse_version(new)
    new = f"{major}.{minor}.{patch}"
    tag = f"v{new}"
    zip_name = f"MatFinder-{new}-win64.zip"
    setup_name = f"MatFinder-{new}-Setup.exe"
    installer_dir = os.path.join(ROOT, "dist", "installer")
    zip_path = os.path.join(installer_dir, zip_name)
    setup_path = os.path.join(installer_dir, setup_name)

    step(f"Release MatFinder {cur} -> {new}  (tag {tag})")
    if git_out("tag", "-l", tag):
        sys.exit(f"[X] A tag {tag} ja existe. Tags publicadas sao imutaveis - "
                 f"escolha uma versao nova.")

    step("1/6  Sincronizando versao em todos os arquivos")
    vm.update_all(new)

    if not args.no_build:
        step("2/6  Compilando (build + selftest)")
        run([py, os.path.join("build_tools", "build_clean.py")])
    else:
        step("2/6  Build pulado (--no-build)")

    step("3/6  Gerando instalador (.exe)")
    run([find_iscc(), os.path.join("build_tools", "MatFinder.iss")])
    if not os.path.exists(setup_path):
        sys.exit(f"[X] Instalador nao encontrado: {setup_path}")

    step("4/6  Empacotando .zip portatil")
    import shutil
    if os.path.exists(zip_path):
        os.remove(zip_path)
    base = os.path.join(installer_dir, f"MatFinder-{new}-win64")
    shutil.make_archive(base, "zip", os.path.join(ROOT, "dist"), "MatFinder")
    print(f"  {zip_path}  ({os.path.getsize(zip_path) / 1e6:.1f} MB)")

    if args.no_publish:
        step("OK (ensaio) - build/instalador/zip prontos; nada foi enviado (--no-publish)")
        print(f"  {setup_path}\n  {zip_path}")
        return

    step("5/6  Commit + tag + push")
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"chore: release {tag}"])
    run(["git", "tag", tag])
    branch = git_out("rev-parse", "--abbrev-ref", "HEAD") or "main"
    run(["git", "push", "origin", branch])
    run(["git", "push", "origin", tag])

    step("6/6  Publicando Release no GitHub")
    token = get_token()
    notes = (f"MatFinder {new} (Windows x64).\\n\\n"
             f"- **{setup_name}** - instalador (recomendado).\\n"
             f"- **{zip_name}** - portatil (extrair e rodar MatFinder.exe ou PhaseDRX.exe).\\n\\n"
             f"Mudancas: ver CHANGELOG.md.")
    rel = api("POST", f"{API}/releases", token,
              payload={"tag_name": tag, "name": f"MatFinder {tag}", "body": notes})
    rel_id = rel["id"]
    for path, name, ctype in ((setup_path, setup_name, "application/octet-stream"),
                              (zip_path, zip_name, "application/zip")):
        with open(path, "rb") as f:
            raw = f.read()
        print(f"  subindo {name} ({len(raw) / 1e6:.1f} MB)...")
        a = api("POST", f"{UPLOADS}/releases/{rel_id}/assets?name={name}", token,
                raw=raw, content_type=ctype)
        print(f"    OK state={a.get('state')}")

    step(f"PRONTO - Release {tag} publicado com instalador + zip")
    print(f"  https://github.com/{REPO}/releases/tag/{tag}")


if __name__ == "__main__":
    main()
