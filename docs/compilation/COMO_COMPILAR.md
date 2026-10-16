# Como compilar o MatFinder (Windows)

> **Só quer usar o programa?** Não precisa compilar nada: baixe o `.zip` pronto na
> aba **[Releases](https://github.com/SrValentim/MatFinder/releases/latest)** do GitHub, extraia e rode `MatFinder/MatFinder.exe`.
> O guia abaixo é para quem quer **compilar** a partir do código.

Você vai gerar `dist\MatFinder\MatFinder.exe` — versão **otimizada (~402 MB)** que
abre sem erro de "módulo faltando". São **2 passos**:

## Passo 1 — Instalar requisitos (só na 1ª vez)

Dê **duplo clique em `build_tools\INSTALAR_REQUISITOS.bat`**.

Ele instala o **Python 3.11** (via `winget`, se você ainda não tiver) e todas as
dependências de build. Leva ~10 min e precisa de internet.

> Se o `winget` não existir no seu Windows, o script mostra o link para instalar
> o Python 3.11 manualmente (<https://www.python.org/downloads/release/python-3119/>,
> marque **"Add python.exe to PATH"**) e é só rodar o `INSTALAR_REQUISITOS.bat` de novo.

## Passo 2 — Compilar (sempre que quiser)

Dê **duplo clique em `build_tools\COMPILAR.bat`**. Pronto: `dist\MatFinder\MatFinder.exe`.

- A **1ª compilação** é mais demorada; as seguintes são **bem mais rápidas**
  (reusa cache automaticamente).
- Se algo ficar estranho, force um rebuild limpo: no terminal, na raiz do projeto,
  `build_tools\COMPILAR.bat --clean`.
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

Não fique tentando às cegas — o auto-teste lista **tudo** que falta de uma vez.
O `COMPILAR.bat` já roda esse teste no fim e mostra o relatório (salvo em
`build\selftest_report.txt`). Para rodar de novo à mão, na raiz do projeto:

```bat
set QT_QPA_PLATFORM=offscreen
set MATFINDER_SELFTEST_REPORT=%CD%\build\selftest_report.txt
dist\MatFinder\MatFinder.exe --selftest
type build\selftest_report.txt
```

Para cada módulo da lista, adicione `collect_all('pacote')` em
`build_tools\MatFinder.spec`. (Detalhes em [`GUIA_COMPILACAO.md`](GUIA_COMPILACAO.md).)

## Publicar uma versão (mantenedor)

O GitHub Actions compila na nuvem e publica sozinho. Para lançar:

```bat
:: sincroniza a versao em todos os arquivos (VERSION, __init__.py, .iss, CITATION.cff, READMEs)
python build_tools\version_manager.py --bump minor
:: mova as notas de [Nao publicado] do CHANGELOG.md para a nova versao, depois:
git commit -am "chore: release vX.Y.Z"
git tag vX.Y.Z
git push origin main vX.Y.Z
```

Isso dispara `.github/workflows/build-release.yml`, que compila no Windows, Linux e
macOS e cria um **Release** com o instalador e os pacotes. Para só testar sem lançar:
aba **Actions ▸ Build & Release ▸ Run workflow** (sobe os pacotes como *artifacts*,
sem criar release).

## Observações honestas

- Requer **Python 3.11 / Windows 64-bit** (os pacotes do lock são `cp311` / `win_amd64`).
- O `.exe` **não** é byte-a-byte idêntico entre máquinas (o PyInstaller embute
  timestamps/caminhos — vale para qualquer projeto). O resultado é
  **funcionalmente o mesmo**: ~426 MB, abre, e `--selftest` = 0 módulos faltando.
- `requirements-build.lock.txt` = ambiente exato (usado pelos `.bat`).
  `requirements-build.txt` = versão legível/mínima.
