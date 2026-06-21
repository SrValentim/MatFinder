# Guia de Compilação do MatFinder (otimizado)

> Objetivo: build **pequeno (~426 MB, era ~1,5 GB)** e **sem o ciclo "compila →
> abre → falta módulo → compila..."**. A chave é (1) um venv de build LIMPO e
> (2) um **smoke test headless** que lista todos os módulos faltantes de uma vez.

## TL;DR — como compilar

```bat
REM 1x: criar o venv de build (fora da pasta do repo), Python 3.11
py -3.11 -m venv ..\.venv-build
REM use o LOCK para reproduzir EXATAMENTE o ambiente (recomendado):
..\.venv-build\Scripts\python -m pip install -r build_tools\requirements-build.lock.txt

REM sempre que for compilar:
build_tools\COMPILE.bat
REM (ou:  ..\.venv-build\Scripts\python build_tools\build_clean.py)
```

### Reprodutibilidade ("dá o mesmo resultado em outra máquina?")

- **`requirements-build.lock.txt`** = lock COMPLETO (184 pacotes fixados). Use
  ESTE para reproduzir o ambiente exato. Requer **Python 3.11** (os wheels são cp311).
- **`requirements-build.txt`** = versão legível/mínima (30 pins + comentários).
  Mostra o que importa, mas deixa transitivas livres → pode driftar com o tempo.
- O `.exe` em si **não** é byte-idêntico entre builds (o PyInstaller embute
  timestamps/paths). Com o lock + Python 3.11, o resultado é **funcionalmente o
  mesmo**: ~426 MB, abre, e `--selftest` = 0 módulos faltando.
- O venv inclui jupyter/boto3/etc. de propósito (são deps transitivas de
  chempy→pyodesys e maggma). Eles ficam no `excludes` do spec e **não** entram no
  `.exe`. Para atualizar o lock após mudar deps: `pip freeze > build_tools\requirements-build.lock.txt`.

O `build_clean.py` faz tudo: compila → roda `MatFinder.exe --selftest` (headless)
→ imprime tamanho final. Se faltar módulo, o selftest lista **todos** de uma vez.

## Por que o build inchava e dava "módulo faltando" (causas-raiz)

1. **Venv poluído.** O `requirements.txt` da raiz é um `pip freeze` do ambiente
   inteiro do PyCharm (jupyter, jax, opencv, PyQt5, boto3, tensorflow...). O
   PyInstaller seguia esses imports e empacotava tudo → 1,5 GB. **Solução:** o
   `.venv-build` tem só o que o app usa (`requirements-build.txt`).

2. **Imports dinâmicos/lazy** (pymatgen, mp_api, emmet, monty, chempy, plotly):
   a análise estática do PyInstaller não os enxerga. **Solução:** `collect_all()`
   no spec + `gen_hiddenimports.py` (mede o fecho real de imports rodando o app).

3. **Cadeia frágil pymatgen ↔ emmet-core ↔ mp-api.** pymatgen 2025.x quebra com
   `No module named 'pymatgen.core.graphs'`. **Solução:** versões fixadas e
   casadas em `requirements-build.txt` (pymatgen 2024.10.29 + emmet-core 0.84.7rc1).

4. **setuptools 81+ removeu `pkg_resources`** (que o pybtex usa) e o
   `backports`/`jaraco` vendorizados não eram empacotados → crash no boot
   (`No module named 'backports'`). **Solução:** `setuptools<81` +
   `backports.tarfile` real + `collect_submodules('setuptools._vendor')`.

5. **`cipher=block_cipher`** no spec antigo: removido no PyInstaller 6 (podia
   quebrar o spec). O novo spec não usa.

## Arquivos do build

| Arquivo | Papel |
|---|---|
| `build_tools/requirements-build.txt` | deps mínimas, versões casadas |
| `build_tools/MatFinder.spec` | spec novo (collect_all + filtro DLL Qt + lê o gerado) |
| `build_tools/gen_hiddenimports.py` | mede o fecho real de imports → `hiddenimports_generated.txt` |
| `build_tools/build_clean.py` | pipeline: compila + smoke test + tamanho |
| `build_tools/COMPILE.bat` | atalho que chama o venv limpo + build_clean.py |
| `run_matfinder.py --selftest` | importa tudo headless; sai 0/1; grava `selftest_report.txt` |
| `MatFinder.spec.legacy.bak` | spec antigo (referência) |

## Diagnóstico (quebrar o ciclo, não tentativa-e-erro)

- **Build OK mas .exe não abre?** Rode `MatFinder.exe --selftest` (defina
  `QT_QPA_PLATFORM=offscreen`). Ele lista **todos** os módulos faltantes de uma
  vez no `selftest_report.txt`. Para cada um, prefira `collect_all('<pkg>')` no
  spec a adicioná-lo solto.
- **Mudou dependência?** Rode `gen_hiddenimports.py` de novo antes de compilar.
- **Faltou DLL?** Veja se não foi removida pelo filtro `excluded_binaries` no spec.

## Tamanho

- **Atual: ~426 MB.** Maiores pesos: OpenBLAS (numpy+scipy ~73 MB), PySide6/Qt,
  `opengl32sw.dll` (~20 MB), cryptography `_rust.pyd`, plotly (~10 MB).
- WebEngine/Quick/Multimedia/3D/Charts do PySide6_Addons são removidos pelo
  filtro de DLL (`excluded_binaries`).
