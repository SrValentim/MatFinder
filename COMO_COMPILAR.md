# Como compilar o MatFinder (Windows)

Você vai gerar `dist\MatFinder\MatFinder.exe` — versão **otimizada (~426 MB)**, que
abre sem erro de "módulo faltando".

## Pré-requisito (uma vez só)

- **Python 3.11 (64-bit).** Baixe aqui: <https://www.python.org/downloads/release/python-3119/>
  Na instalação, **marque "Add python.exe to PATH"**.
  > Use 3.11 mesmo — as dependências estão fixadas para essa versão.

## Jeito fácil — 1 clique

1. No GitHub, clique em **Code ▸ Download ZIP** e **extraia** o conteúdo.
2. Abra a pasta extraída e dê **duplo clique em `COMPILAR.bat`**.
3. Espere. Na **primeira vez** ele cria o ambiente e instala tudo (~10 min, precisa
   de internet); nas próximas, só compila (~5 min).
4. Pronto: o app está em **`dist\MatFinder\MatFinder.exe`**.

## Jeito manual (terminal)

Abra o **Prompt de Comando (CMD)** dentro da pasta extraída e rode:

```bat
py -3.11 -m venv .venv-build
.venv-build\Scripts\python -m pip install -r build_tools\requirements-build.lock.txt
.venv-build\Scripts\python build_tools\build_clean.py
```

## Se aparecer "ModuleNotFoundError" (não deve, mas...)

Não fique tentando às cegas. O auto-teste lista **tudo** que falta de uma vez:

```bat
set QT_QPA_PLATFORM=offscreen
dist\MatFinder\MatFinder.exe --selftest
type selftest_report.txt
```

Para cada módulo da lista, adicione `collect_all('pacote')` em
`build_tools\MatFinder.spec` e recompile. (Detalhes em `docs\compilation\GUIA_COMPILACAO.md`.)

## Observações honestas

- Requer **Python 3.11 / Windows 64-bit** (os pacotes do lock são `cp311` / `win_amd64`).
- O `.exe` **não** é byte-a-byte idêntico entre máquinas (o PyInstaller embute
  timestamps/caminhos — isso vale para qualquer projeto). O resultado é
  **funcionalmente o mesmo**: ~426 MB, abre, e `--selftest` = 0 módulos faltando.
- `requirements-build.lock.txt` = ambiente exato (use este). `requirements-build.txt`
  = versão legível/mínima.
