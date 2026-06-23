# Changelog

Todas as mudanças relevantes do MatFinder são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e versionamento [Semantic Versioning](https://semver.org/lang/pt-BR/) (MAJOR.MINOR.PATCH):
- **MAJOR** — mudanças incompatíveis / reformulação grande.
- **MINOR** — novos recursos compatíveis.
- **PATCH** — correções de bugs compatíveis.

## Fluxo de release (mantenedores)

1. `python version_manager.py --bump patch|minor|major` (sincroniza VERSION, `__init__.py`,
   traduções, `setup.py`, `MatFinder.iss`, `CITATION.cff` e a versão no README).
2. Mover as entradas de **[Não publicado]** para a nova versão abaixo.
3. `git commit -am "chore: release vX.Y.Z"` e `git tag vX.Y.Z`.
4. Enviar a tag; o CI compila os pacotes e publica o Release.
   (`build_tools/release.py` faz o fluxo completo localmente em um comando.)

> Tags publicadas são imutáveis — nunca mover/reescrever uma tag já lançada.

---

## [Não publicado]

### Added
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1) e templates de
  issue (bug/feature).
- Pasta **`examples/`** com dados de exemplo (CIFs + série temporal de DRX SmFeO₃) e um
  tutorial (`examples/README.md`) do fluxo completo. Substitui a antiga "Galeria de CIF".
- **Suíte de testes automatizados (pytest)** em `tests/` cobrindo a lógica central
  (normalização, background, matemática de DRX, calculadora, DOI, traduções, dados de
  exemplo) + workflow de CI (`tests.yml`) e `requirements-dev.txt`.

### Changed
- **Cross-platform:** roda de fonte em Windows, Linux e macOS. O diretório de dados
  do usuário passa a ser escolhido por plataforma (LOCALAPPDATA / ~/Library/Application
  Support / XDG). README "Run from source" com comandos para os 3 SOs.

### Removed
- Dependência **`cloudscraper`** (ficou morta após a remoção do Sci-Hub): retirada do
  código, do `MatFinder.spec` e dos `requirements-build`.

### Infra
- CI (`build-release.yml`) virou **matriz de 3 SOs**: na tag, gera instalador+zip
  (Windows), `.tar.gz` (Linux) e `.zip` (macOS) e publica todos no Release.
- `build_clean.py` ciente do SO (nome do binário sem `.exe` em Linux/macOS).

---

## [3.24.1] - 2026-06-22

### Changed
- **Download de artigo por DOI** agora usa apenas fontes legais de **acesso aberto**
  (OpenAlex + Unpaywall) no lugar do Sci-Hub. O botão "Buscar e Salvar PDF" continua,
  mas busca a versão de acesso aberto do artigo.

### Removed
- Antigo downloader de artigos via **Sci-Hub** (substituído pelo acesso aberto) e todo
  o código de scraping associado.

### Added
- `CHANGELOG.md`.
- `build_tools/release.py` — release local de um comando (bump → build → instalador →
  zip → commit/tag/push → Release no GitHub).

### Infra
- `version_manager.py` agora sincroniza também `build_tools/MatFinder.iss` e
  `CITATION.cff`, normaliza a versão para `X.Y.Z` completo e força saída UTF-8.
- GitHub Actions (`build-release.yml`) passa a gerar **também o instalador** (`.exe` via
  Inno Setup) e publicar `.zip` + instalador no Release.
- Versão consistente em `X.Y.Z` em todos os arquivos.

---

## [3.24.0] - 2026-06-21

Primeira versão estável da linha 3.24.

### Added
- Tradução completa (PT/EN/DE) de **toda** a interface (~660 textos): diálogos,
  cabeçalhos de tabela, eixos do gráfico, mensagens de erro/conexão, leitores de
  arquivo, descrições de método, calculadora e diálogo Sobre.
- **PhaseDRX como aplicativo separado** (`PhaseDRX.exe`) na mesma pasta do MatFinder,
  com ícone e splash próprios, rodando junto com o MatFinder.
- **"Exportar para PhaseDRX" entre processos** via bridge IPC (QLocalServer): abrir o
  PhaseDRX sozinho e o MatFinder depois, e enviar o CIF sem baixar/recarregar.

### Changed
- "Exportar para PhaseDRX" usa **sempre o CIF simetrizado**.

### Fixed
- Erro `[WinError 5] Acesso negado` ao exportar/usar CIF: `temp_cifs`, favoritos e
  histórico de busca passam a gravar no diretório de dados **gravável** (antes tentavam
  gravar em `C:\Program Files\MatFinder`, somente-leitura).
- Splash do PhaseDRX Suite não fica mais sobreposta ao diálogo de projeto.
- Comboboxes traduzidos lidos por valor (perfil de pico, modo, estilo de linha, paleta,
  direção de ticks, fonte de radiação) deixam de quebrar a lógica em EN/DE.

---

## [2.0.0]

Versão anterior (linha 2.x).
