# Changelog

Todas as mudanças relevantes do MatFinder são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e versionamento [Semantic Versioning](https://semver.org/lang/pt-BR/) (MAJOR.MINOR.PATCH):
- **MAJOR** — mudanças incompatíveis / reformulação grande.
- **MINOR** — novos recursos compatíveis.
- **PATCH** — correções de bugs compatíveis.

## Fluxo de release (mantenedores)

1. `python build_tools/version_manager.py --bump patch|minor|major` (sincroniza VERSION,
   `__init__.py`, traduções, `MatFinder.iss`, `CITATION.cff` e a versão nos READMEs).
2. Mover as entradas de **[Não publicado]** para a nova versão abaixo.
3. `git commit -am "chore: release vX.Y.Z"` e `git tag vX.Y.Z`.
4. Enviar a tag; o CI compila os pacotes e publica o Release.
   (`build_tools/release.py` faz o fluxo completo localmente em um comando.)

> Tags publicadas são imutáveis — nunca mover/reescrever uma tag já lançada.

---

## [Não publicado]

### Added
- Ciclo de identificação no estilo do HighScore (PhaseDRX, search-match fase 3): **Aceitar fase**
  leva o candidato para a tabela de fases aceitas. As escalas das fases aceitas são ajustadas
  juntas às alturas dos picos e os outros candidatos são pontuados de novo contra a intensidade
  que sobrou, com o zero fixado pelas fases aceitas. A tabela mostra escala, picos atribuídos e
  fração em massa semiquantitativa (RIR calculado da estrutura); o resumo mostra quanto da
  intensidade está explicado, os picos sem fase e o zero global. No gráfico, as reflexões das
  fases aceitas aparecem na cor de cada fase, cada pico ganha a cor da fase que mais o explica e
  os picos sem fase ficam com um anel vermelho. Para dados ruins (poucos picos ou picos largos),
  um score de perfil inteiro ajusta o padrão simulado ao difratograma sem fundo; o modo
  **Automático** liga esse score quando a lista de picos é pobre. **Enviar fases aceitas para a
  lista** carrega os CIFs e cria uma combinação com as proporções ajustadas. As fases aceitas
  ficam salvas no projeto (com o CIF), entram no desfazer/refazer e são recalculadas quando a
  lista de picos ou a radiação muda.
- Identificação de fases (PhaseDRX, search-match fase 2): nova aba **Identificação**.
  Os elementos obrigatórios, possíveis e proibidos são escolhidos numa tabela periódica de
  três estados (sistema fechado ou aberto) e os candidatos vêm do COD e do Materials
  Project. Cada candidato é simulado e pontuado de 0 a 100 contra a lista de picos:
  posições, reflexões fortes achadas (só as esperadas acima do ruído), picos explicados e
  intensidades, com zero e escala da rede alinhados (faixa maior para as estruturas de DFT
  do MP). Entradas da mesma fase são agrupadas; a tabela é ordenável, mostra a prévia das
  reflexões sobre o difratograma, abre a entrada na fonte e envia o CIF para a lista do
  PhaseDRX. Consultas, CIFs e padrões simulados ficam em cache local; o COD é consultado por
  sistema químico (respostas menores, sem cortes), com novas tentativas e HTTP quando o HTTPS falha.
- Busca de picos (PhaseDRX, search-match fase 1): nova aba **Picos** com um detector
  refeito do zero. Detecção multiescala (segunda derivada suavizada em várias larguras)
  com ruído calibrado longe dos picos, fundo SNIP robusto a ruído e a bordas, e ajuste
  por pseudo-Voigt assimétrica com dubleto Kα2, tendência de largura (Caglioti) e
  seleção de modelo para ombros. Mostra 2θ com incerteza, d, intensidade relativa,
  altura, área, FWHM e significância; marca possíveis picos de Kβ; no modo "Picos
  largos / amorfo" separa halos amorfos e estima a cristalinidade. A busca roda em
  segundo plano, com progresso e cancelamento.
- Edição da lista de picos (PhaseDRX): adicionar pico com um clique (ajuste local),
  apagar pico pelo gráfico ou pela tabela (só o pico, nunca os dados), picos apagados
  continuam apagados numa nova busca até serem restaurados, exportação em CSV. A lista
  fica salva no projeto e entra no desfazer/refazer.
- Simulação (PhaseDRX): opções **Kα** e **Kβ** na aba de simulação para escolher as
  linhas de emissão do tubo que entram no padrão calculado. Pelo menos uma fica sempre
  marcada. O Kβ1 entra com a razão de intensidade aproximada de um tubo sem filtro, e as
  opções ficam desativadas com comprimento de onda personalizado. Com só o Kα marcado, o
  resultado é idêntico ao de antes.
- Visualizador 3D (PhaseDRX): exibição completa da célula unitária. Átomos em faces,
  arestas e vértices são replicados em todas as imagens de borda dentro de [0, N] e a
  vizinhança ligada imediatamente fora da célula é incluída para fechar anéis e poliedros
  (convenção adotada por VESTA e Mercury). As posições atômicas não são alteradas.
- Visualizador 3D (PhaseDRX): shader GLSL para átomos e ligações — iluminação headlight
  com termo especular e atenuação por profundidade (mistura para o branco conforme a
  distância à câmera). Executa na GPU; retorna ao shader embutido em falha de compilação.
- Visualizador 3D (PhaseDRX): ligações em duas cores (metade da cor de cada átomo, com
  transição no ponto médio), em um único mesh por ligação.
- Visualizador 3D (PhaseDRX): botões de orientação da câmera ao longo dos eixos
  cristalográficos a, b e c, e botão de vista isométrica.

### Changed
- Organização do repositório: a raiz ficou só com o essencial. Os READMEs em português e
  alemão, a página de capturas de tela e o `COMO_COMPILAR.md` foram para `docs/`;
  `CONTRIBUTING.md` e `CODE_OF_CONDUCT.md` para `.github/`; `COMPILAR.bat`,
  `INSTALAR_REQUISITOS.bat` e `version_manager.py` para `build_tools/`. A licença passou a
  ser `LICENSE` na raiz e as dependências de teste ficam em `tests/requirements.txt`. O
  relatório do selftest do build agora é gravado em `build/selftest_report.txt`.
- `version_manager.py` também atualiza a versão nos READMEs em português e alemão.

### Removed
- Arquivos obsoletos: `setup.py` (cx_Freeze), a pasta `scripts/` (hooks antigos do
  PyInstaller, build MSI e um `.iss` antigo), `build_tools/COMPILE.bat`,
  `build_tools/build_optimized.py`, o `requirements.txt` da raiz (freeze do ambiente
  inteiro, sem uso), a cópia duplicada da licença, os scripts de `tests/manual/`, assets
  sem uso (`cod_logo.png`, a cópia de `polvo.ico` em `logos/`, `language.json`) e dois
  documentos vazios.

### Fixed
- PhaseDRX: o Desfazer recuava duas ações por clique (e o Refazer devolvia só uma);
  agora cada clique desfaz ou refaz exatamente uma ação.
- Visualizador 3D (PhaseDRX): arestas da célula unitária passam a usar
  glOptions='opaque' (antes 'additive', sem teste de profundidade), corrigindo linhas
  desenhadas por cima de ligações e átomos.
- *Sobre ▸ Licença* rodando pelo código-fonte: o texto da licença não era encontrado
  (o app procurava `LICENSE_FULL.txt` na raiz, mas o arquivo ficava em `licenses/`).

---

## [3.26.0] - 2026-07-11

### Added
- **Medição de distância interatômica no visualizador 3D (PhaseDRX)**, recurso baseado
  em VESTA, Mercury e outros programas de visualização cristalográfica: o duplo-clique em
  dois átomos traça uma linha pontilhada e mostra a distância em Å no meio dela; o rótulo
  acompanha a estrutura ao girar/dar zoom, e o botão direito limpa as medições.

### Changed
- Abas do PhaseDRX com nomes mais curtos: **Difração** (antes "Difratograma (2D)") e
  **Estrutura** (antes "Estrutura Cristalina (3D)"), com traduções em inglês e alemão.

### Fixed
- Visualizador 3D agora carrega **estruturas desordenadas** (ocupação parcial, comuns em
  CIFs do COD): passa a usar a espécie de maior ocupação em vez de falhar em `site.specie`.
- Projeção 3D do picking compatível com diferentes versões do pyqtgraph.

---

## [3.25.0] - 2026-06-23

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
