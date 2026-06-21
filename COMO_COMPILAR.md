# Como compilar o MatFinder (Windows)

Você vai gerar `dist\MatFinder\MatFinder.exe` — versão **otimizada (~426 MB)** que
abre sem erro de "módulo faltando". São **2 passos**:

## Passo 1 — Instalar requisitos (só na 1ª vez)

Dê **duplo clique em `INSTALAR_REQUISITOS.bat`**.

Ele instala o **Python 3.11** (via `winget`, se você ainda não tiver) e todas as
dependências de build. Leva ~10 min e precisa de internet.

> Se o `winget` não existir no seu Windows, o script mostra o link para instalar
> o Python 3.11 manualmente (<https://www.python.org/downloads/release/python-3119/>,
> marque **"Add python.exe to PATH"**) e é só rodar o `INSTALAR_REQUISITOS.bat` de novo.

## Passo 2 — Compilar (sempre que quiser)

Dê **duplo clique em `COMPILAR.bat`**. Pronto: `dist\MatFinder\MatFinder.exe`.

- A **1ª compilação** é mais demorada; as seguintes são **bem mais rápidas**
  (reusa cache automaticamente).
- Se algo ficar estranho, force um rebuild limpo: no terminal, `COMPILAR.bat --clean`.
- O `COMPILAR.bat` **não instala nada** — se faltar Python 3.11 ou as dependências,
  ele dá um erro pedindo para rodar o `INSTALAR_REQUISITOS.bat`.

## Pelo terminal (alternativa ao duplo clique)

```bat
:: 1x:
py -3.11 -m venv .venv-build
.venv-build\Scripts\python -m pip install -r build_tools\requirements-build.lock.txt
:: compilar:
.venv-build\Scripts\python build_tools\build_clean.py
```

## Se aparecer "ModuleNotFoundError" (não deve, mas...)

Não fique tentando às cegas — o auto-teste lista **tudo** que falta de uma vez:

```bat
set QT_QPA_PLATFORM=offscreen
dist\MatFinder\MatFinder.exe --selftest
type selftest_report.txt
```

Para cada módulo da lista, adicione `collect_all('pacote')` em
`build_tools\MatFinder.spec`. (Detalhes em `docs\compilation\GUIA_COMPILACAO.md`.)

## Observações honestas

- Requer **Python 3.11 / Windows 64-bit** (os pacotes do lock são `cp311` / `win_amd64`).
- O `.exe` **não** é byte-a-byte idêntico entre máquinas (o PyInstaller embute
  timestamps/caminhos — vale para qualquer projeto). O resultado é
  **funcionalmente o mesmo**: ~426 MB, abre, e `--selftest` = 0 módulos faltando.
- `requirements-build.lock.txt` = ambiente exato (usado pelos `.bat`).
  `requirements-build.txt` = versão legível/mínima.
