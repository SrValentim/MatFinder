# MatFinder

<div align="center">
  <img src="../matfinder/assets/logos/splash.png" alt="MatFinder Logo" width="200"/>
  
  **Busca e Análise de Materiais Cristalinos**
  
  [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20778195.svg)](https://doi.org/10.5281/zenodo.20778195)
  [![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](../LICENSE)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
  [![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#obter-o-matfinder)
  
  🌐 [English](../README.md) · **Português** · [Deutsch](README.de.md)

  <br/><br/>

  <a href="https://github.com/SrValentim/MatFinder/releases/latest">
    <img src="https://img.shields.io/badge/DOWNLOAD-Windows_64--bit-2ea44f?style=for-the-badge&logo=windows&logoColor=white" alt="Baixar MatFinder para Windows"/>
  </a>

  <br/>
  <sub>Instalador para Windows ou <code>.zip</code> portátil · sem necessidade de Python</sub>

  <br/><br/>

  ###  [Visão geral](README.pt-BR.md) ·  [Capturas de tela](SCREENSHOTS.md)
</div>

---

##  Sobre

O MatFinder é uma aplicação desktop completa para buscar, visualizar e analisar estruturas de materiais cristalinos. Desenvolvido na Universidade Federal do Amazonas (UFAM), Brasil, integra múltiplos bancos de dados cristalográficos e ferramentas de análise de difração de raios X.

###  Destaque: identificação automática de fases (search-match)

O PhaseDRX identifica as fases cristalinas de um difratograma com um fluxo de search-match
como o dos programas comerciais de DRX, mas **gratuito e só com bases de dados abertas**:

- **Busca robusta de picos**: detecção multiescala, ajuste do dubleto Kα2, marcação de Kβ e
  um modo para padrões largos ou amorfos. A lista de picos pode ser editada sem mexer nos dados.
- **Candidatos de bases abertas**: o [Crystallography Open Database (COD)](https://www.crystallography.net/)
  e o [Materials Project](https://next-gen.materialsproject.org/) (chave de API gratuita), com
  filtro de elementos na tabela periódica. Nenhuma base paga ou licença é necessária.
- **Pontuação de 0 a 100** que pesa posições dos picos, reflexões fortes esperadas e
  intensidades, com entradas duplicadas agrupadas e as reflexões sobrepostas ao seu difratograma.
- **Aceitar e reavaliar**: as fases aceitas são ajustadas juntas, os outros candidatos são
  pontuados de novo contra a intensidade que ainda não foi explicada, e os picos sem fase ficam marcados.
- **Frações em massa semiquantitativas** (RIR) e um clique para enviar as fases aceitas à
  simulação como combinação multifásica.

Passo a passo (em inglês): [guia de identificação de fases](https://srvalentim.github.io/MatFinder/guide/search-match/).

###  Suporte multilíngue

O MatFinder está disponível em:
- 🇧🇷 **Português** (padrão)
- 🇺🇸 **Inglês**
- 🇩🇪 **Alemão** (Deutsch)


### Principais recursos

- **Busca integrada**: Materials Project, COD (Crystallography Open Database), OQMD, ROD (Raman Open Database)
- **Análise de DRX**: simulação e comparação de padrões de difração
- **Identificação de fases (search-match)**: identificação automática das fases de um padrão
  de DRX, com candidatos do COD e do Materials Project
- **Ferramentas de análise**:
  - Editor de arquivos CIF
  - Calculadora estequiométrica
  - Tabela periódica interativa
  - Remoção de background (SNIP, polinomial)
  - Normalização de dados (múltiplos métodos)
- **Visualização**: gráficos interativos com personalização
- **Gerenciamento**: sistema de favoritos e histórico de buscas

---

##  Obter o MatFinder

###  Opção 1 — Baixar o aplicativo pronto para uso (recomendado)

1. Abra **[Releases ▸ latest](https://github.com/SrValentim/MatFinder/releases/latest)**.
2. Baixe o **instalador** (`MatFinder-…-Setup.exe`) ou o **`.zip`** portátil
   (`MatFinder-…-win64.zip`).
3. Execute o instalador **ou** extraia o zip e rode **`MatFinder/MatFinder.exe`**
   (e `PhaseDRX.exe` para a suíte de DRX). Sem Python, sem configuração.

> Funciona no **Windows 10/11 (64 bits)**. 4 GB de RAM no mínimo (8 GB recomendado).

###  Opção 2 — Executar a partir do código-fonte (Windows, Linux ou macOS)

```bash
git clone https://github.com/SrValentim/MatFinder.git
cd MatFinder

# Windows
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r build_tools\requirements-build.lock.txt
.venv\Scripts\python run_matfinder.py

# Linux / macOS
python3.11 -m venv .venv
.venv/bin/python -m pip install -r build_tools/requirements-build.lock.txt
.venv/bin/python run_matfinder.py
```

> Requer **Python 3.11 (64 bits)**. O arquivo travado `build_tools/requirements-build.lock.txt`
> é o conjunto reprodutível de dependências. A execução a partir do código-fonte
> funciona nas três plataformas; o `.exe`/instalador pré-compilados são apenas para Windows.

###  Opção 3 — Compilar seu próprio `.exe` otimizado

1. Dê duplo-clique em **`build_tools/INSTALAR_REQUISITOS.bat`** — instala Python 3.11 + dependências (uma vez).
2. Dê duplo-clique em **`build_tools/COMPILAR.bat`** — gera `dist/MatFinder/` com `MatFinder.exe`
   e `PhaseDRX.exe` (~450 MB, `_internal` compartilhado).

Guia completo: **[`COMO_COMPILAR.md`](compilation/COMO_COMPILAR.md)** · [`GUIA_COMPILACAO.md`](compilation/GUIA_COMPILACAO.md)

---

## Documentação

- **Guia do usuário (site)**: <https://srvalentim.github.io/MatFinder/> — fonte em [`website/`](../website/)
- **Capturas de tela**: [`docs/SCREENSHOTS.md`](SCREENSHOTS.md)
- **Guias de compilação**: [`docs/compilation/`](compilation/)
- **Notas técnicas e relatórios de validação**: [`docs/dev/`](dev/)
- **Exemplos** (CIFs de exemplo + dados reais de DRX): [`examples/`](../examples/)
- **Licença GPL v3**: [`LICENSE`](../LICENSE)

---

##  Desenvolvimento

### Estrutura do projeto

```
MatFinder/
├── matfinder/                       # Código-fonte
│   ├── core/                        # Módulos centrais (APIs das bases, tradução, favoritos, histórico)
│   ├── data/                        # Tratamento de dados (editor/leitor de CIF, API do COD)
│   ├── tools/                       # Ferramentas: calculadora, tabela periódica, suíte de DRX (PhaseDRX)
│   └── assets/                      # Ícones, logos e traduções
├── tests/                           # Testes automatizados (pytest) + o requirements.txt deles
├── examples/                        # CIFs de exemplo e dados reais de DRX (usados também nos testes)
├── docs/                            # Documentação
│   ├── README.pt-BR.md              # Este README em português
│   ├── README.de.md                 # Este README em alemão
│   ├── SCREENSHOTS.md               # Tour visual (imagens em screenshots/)
│   ├── compilation/                 # Guias de compilação
│   └── dev/                         # Notas técnicas e relatórios de validação
├── website/                         # Site de documentação (MkDocs -> GitHub Pages)
├── build_tools/                     # Ferramentas de build, instalador e release
│   ├── INSTALAR_REQUISITOS.bat      # 1 clique: instala Python 3.11 + dependências
│   ├── COMPILAR.bat                 # 1 clique: compila o .exe
│   ├── build_clean.py               # Pipeline de build: mapeia imports + compila + selftest
│   ├── gen_hiddenimports.py         # Mapeia o fecho real de imports do app
│   ├── MatFinder.spec               # Configuração do PyInstaller (collect_all + filtro de DLLs Qt)
│   ├── MatFinder.iss                # Instalador do Windows (Inno Setup)
│   ├── release.py                   # Release local em um comando
│   ├── version_manager.py           # Sincroniza o número da versão em todos os arquivos
│   ├── requirements-build.lock.txt  # Dependências exatas e reprodutíveis (Python 3.11)
│   └── requirements-build.txt       # Dependências legíveis/mínimas
├── .github/                         # CI, templates de issue, guia de contribuição e código de conduta
├── run_matfinder.py                 # Ponto de entrada: MatFinder (suporta --selftest)
├── run_phasedrx.py                  # Ponto de entrada: PhaseDRX (suíte de DRX autônoma)
├── CHANGELOG.md                     # Histórico de versões
├── CITATION.cff                     # Metadados de citação (Zenodo)
├── LICENSE                          # Licença GPL v3
├── pytest.ini                       # Configuração dos testes
└── VERSION                          # Número da versão atual
```

### Compilação

Build otimizado (~450 MB, dois executáveis compartilhando `_internal`, sem o loop de
"módulo faltante"). Configuração única com `INSTALAR_REQUISITOS.bat` e, em seguida,
`COMPILAR.bat` para compilar (os dois ficam em `build_tools/`):

```bat
build_tools\INSTALAR_REQUISITOS.bat   :: 1x: Python 3.11 + dependências (a partir do lock)
build_tools\COMPILAR.bat              :: build -> dist\MatFinder\MatFinder.exe
build_tools\COMPILAR.bat --clean      :: rebuild limpo (limpa o cache)
```

- Autoverificação após o build (lista de uma vez qualquer módulo faltante): `MatFinder.exe --selftest`
- **Testes:** `python -m pip install -r tests/requirements.txt` e depois `python -m pytest`
  (veja [`tests/README.md`](../tests/README.md)).
- **CI:** enviar uma tag `vX.Y.Z` dispara `.github/workflows/build-release.yml`,
  que compila no **Windows, Linux e macOS** e publica um Release com o instalador
  do Windows + `.zip`, um `.tar.gz` para Linux e um `.zip` para macOS.

Para detalhes, veja **[`COMO_COMPILAR.md`](compilation/COMO_COMPILAR.md)** e
[`GUIA_COMPILACAO.md`](compilation/GUIA_COMPILACAO.md).

### Tecnologias utilizadas

| Componente | Tecnologia |
|-----------|------------|
| **Interface** | PySide6 (Qt for Python) |
| **Gráficos** | Matplotlib |
| **Computação científica** | NumPy, SciPy, Pandas |
| **Cristalografia** | Pymatgen |
| **APIs** | mp-api (Materials Project), OQMD, COD (Crystallography Open Database) e ROD (Raman Open Database) |
| **Compilação** | PyInstaller |

---

##  Contribuindo

Contribuições são bem-vindas — relatos de bugs, ideias de recursos, documentação,
traduções e código. Por favor leia **[`CONTRIBUTING.md`](../.github/CONTRIBUTING.md)**
(configuração de dev, diretrizes de código e tradução, processo de PR) e nosso
**[`CODE_OF_CONDUCT.md`](../.github/CODE_OF_CONDUCT.md)**.

Versão rápida:

1. Faça um fork do repositório
2. Crie um branch para sua funcionalidade (`git checkout -b feature/AmazingFeature`)
3. Faça commit das suas mudanças (`git commit -m 'feat: add some AmazingFeature'`)
4. Envie para o branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

##  Como citar

Se você usar o MatFinder em sua pesquisa, por favor cite-o (arquivado no **Zenodo**):

> Valentim, R. (2026). *MatFinder - X-ray diffraction analysis tools* (3.25.0). Zenodo. https://doi.org/10.5281/zenodo.20820779

**DOI:** [10.5281/zenodo.20820779](https://doi.org/10.5281/zenodo.20820779) (versão 3.25.0) · [10.5281/zenodo.20778195](https://doi.org/10.5281/zenodo.20778195) (todas as versões, sempre a mais recente)

<details>
<summary>BibTeX</summary>

```bibtex
@software{valentim_matfinder_2026,
  author    = {Valentim, Raynner},
  title     = {{MatFinder - X-ray diffraction analysis tools}},
  year      = {2026},
  publisher = {Zenodo},
  version   = {3.25.0},
  doi       = {10.5281/zenodo.20820779},
  url       = {https://doi.org/10.5281/zenodo.20820779}
}
```
</details>

> 💡 O GitHub também gera um botão **"Cite this repository"** (na barra lateral da página do repo) a partir do [`CITATION.cff`](../CITATION.cff).

---

##  Licença

Este projeto está licenciado sob a **GNU General Public License v3.0** — veja o arquivo [`LICENSE`](../LICENSE) para detalhes.

### Resumo da licença

- ✅ Modificação permitida
- ✅ Distribuição permitida
- ✅ Uso privado permitido
- ⚠️ As alterações devem ser documentadas
- ⚠️ O código-fonte deve ser disponibilizado
- ⚠️ A mesma licença deve ser usada em trabalhos derivados

---

##  Autor

**Raynner Valentim**
- 🎓 Universidade Federal do Amazonas (UFAM) | Departamento de Física | Física de Materiais
- 📧 E-mail: [Raynnervalentim@hotmail.com](mailto:Raynnervalentim@hotmail.com)
- 🐙 GitHub: [@SrValentim](https://github.com/SrValentim)

---

## Agradecimentos

- **Materials Project** — banco de dados de materiais
- **Crystallography Open Database (COD)** — estruturas cristalinas
- **Open Quantum Materials Database (OQMD)**
- **Raman Open Database (ROD)**
- **Pymatgen** — framework de análise de materiais
- **Comunidade Python** — ferramentas e bibliotecas de código aberto

---

##  Status do projeto

🟢 **Ativo** — em desenvolvimento e manutenção.

**Versão atual:** 3.28.0 — veja o [`CHANGELOG.md`](../CHANGELOG.md) para o histórico completo.

Destaques recentes:
- Identificação automática de fases (search-match) com as bases abertas COD e Materials Project
- Tradução completa da interface (português, inglês, alemão)
- PhaseDRX como aplicativo autônomo (`PhaseDRX.exe`) com exportação de CIF entre aplicativos
- Recuperação de artigos de acesso aberto por DOI (OpenAlex/Unpaywall)
- Executa a partir do código-fonte no Windows, Linux e macOS

---

## Reportar problemas

Encontrou um bug? Tem uma sugestão? Abra uma [issue](https://github.com/SrValentim/MatFinder/issues)
(há templates disponíveis) — veja [`CONTRIBUTING.md`](../.github/CONTRIBUTING.md) para o que incluir.

---

<div align="center">
  <sub>Excellence is a habit</sub>
</div>
