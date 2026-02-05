# MatFinder v3.24.0

<div align="center">
  <img src="matfinder/assets/logos/splash.png" alt="MatFinder Logo" width="200"/>
  
  **Busca e Análise de Materiais Cristalinos**
  
  [![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](licenses/LICENSE)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
  [![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
  
  🌐 **Disponível em:** Português | English | Deutsch
</div>

---

## 📋 Sobre

MatFinder é uma aplicação desktop completa para pesquisa, visualização e análise de estruturas cristalinas de materiais. Desenvolvido na Universidade Federal do Amazonas (UFAM), integra múltiplas bases de dados cristalográficas e ferramentas de análise de difração de raios-X.

### 🌍 Suporte Multilíngue

O MatFinder está disponível em **três idiomas**:
- 🇧🇷 **Português** (padrão)
- 🇺🇸 **Inglês** (English)
- 🇩🇪 **Alemão** (Deutsch)

O idioma pode ser alterado em **Configurações → Idioma**. A mudança requer reinicialização do programa.

### Funcionalidades Principais

- **Busca Integrada**: Materials Project, COD (Crystallography Open Database), OQMD, ROD (Raman Open Database)
- **Análise XRD**: Simulação e comparação de padrões de difração
- **Ferramentas de Análise**:
  - Editor de arquivos CIF
  - Calculadora estequiométrica
  - Tabela periódica interativa
  - Remoção de background (SNIP, Rolling Ball, Polynomial)
  - Normalização de dados (múltiplos métodos)
- **Visualização**: Gráficos interativos com customização
- **Gerenciamento**: Sistema de favoritos e histórico de buscas

---

## Instalação

### Requisitos

- **Sistema Operacional**: Windows 10/11 (64-bit)
- **Python**: 3.11 ou superior
- **Memória RAM**: 4GB mínimo (8GB recomendado)
- **Espaço em Disco**: 500MB

### Instalação via Python

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/SrValentim/MatFinder.git
   cd MatFinder
   ```

2. **Crie um ambiente virtual**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute o programa**:
   ```bash
   python run_matfinder.py
   ```

### Executável Pré-compilado

Baixe a versão mais recente em [Releases](https://github.com/SrValentim/MatFinder/releases) e execute `MatFinder.exe`.

---

## 📖 Documentação

- **Manual do Usuário**: [`docs/Manual do Usuário.pdf`](docs/Manual%20do%20Usuário.pdf)
- **Guia de Compilação**: [`docs/compilation/`](docs/compilation/)
- **Licença GPL v3**: [`licenses/LICENSE_FULL.txt`](licenses/LICENSE_FULL.txt)

---

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
MatFinder/
├── matfinder/              # Código-fonte principal
│   ├── core/              # Módulos principais
│   ├── data/              # Manipulação de dados (CIF, APIs)
│   ├── tools/             # Ferramentas (calculadora, XRD, etc.)
│   └── assets/            # Recursos (ícones, logos, configs)
├── build_tools/           # Scripts de compilação
│   ├── MatFinder.spec     # Configuração PyInstaller
│   ├── build_optimized.py # Script de build otimizado
│   └── COMPILE.bat        # Compilação automatizada
├── scripts/               # Scripts auxiliares
│   ├── hooks/            # Hooks personalizados PyInstaller
│   └── build_msi.py      # Gerador de instalador MSI
├── docs/                  # Documentação
├── licenses/              # Arquivos de licença
├── tests/                 # Testes
├── run_matfinder.py       # Ponto de entrada da aplicação
├── setup.py               # Configuração de instalação
└── requirements.txt       # Dependências Python
```

### Compilação

Para compilar o MatFinder em um executável:

1. **Navegue para a pasta de ferramentas de build**:
   ```bash
   cd build_tools
   ```

2. **Execute o script de compilação**:
   ```bash
   COMPILE.bat
   ```

3. **O executável será gerado em**: `dist/MatFinder/MatFinder.exe`

Para mais detalhes, consulte [`docs/compilation/BUILD_GUIDE.md`](docs/compilation/).

### Tecnologias Utilizadas

| Componente | Tecnologia |
|------------|------------|
| **Interface** | PySide6 (Qt for Python) |
| **Gráficos** | Matplotlib |
| **Computação Científica** | NumPy, SciPy, Pandas |
| **Cristalografia** | Pymatgen |
| **APIs** | mp-api (Materials Project), OQMD, COD (Crystallography Open Database) e ROD (Raman Open Database) |
| **Compilação** | PyInstaller |

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📜 Licença

Este projeto está licenciado sob a **GNU General Public License v3.0** - veja o arquivo [`licenses/LICENSE`](licenses/LICENSE) para detalhes.

### Resumo da Licença

-  Modificação permitida
-  Distribuição permitida
-  Uso privado permitido
-  Mudanças devem ser documentadas
-  Código-fonte deve ser disponibilizado
-  Mesma licença deve ser usada em trabalhos derivados

---

## 👨‍💻 Autor

**Raynner Valentim**
- 🎓 Universidade Federal do Amazonas (UFAM) | Departamento de Física | Departamento de Física de Materiais
- 📧 Email: [Raynnervalentim@hotmail.com](mailto:Raynnervalentim@hotmail.com)
- 🐙 GitHub: [@SrValentim](https://github.com/SrValentim)

---

##  Agradecimentos

- **Materials Project** - Base de dados de materiais
- **Crystallography Open Database (COD)** - Estruturas cristalinas
- **Open Quantum Materials Database (OQMD)**
- **Raman Open Database (ROD)**
- **Pymatgen** - Framework de análise de materiais
- **Comunidade Python** - Ferramentas e bibliotecas de código aberto

---

## 📊 Status do Projeto

🟢 **Ativo** - Em desenvolvimento e manutenção

### Versão Atual: 3.24.0

**Últimas Atualizações**:
- 🌍 Suporte multilíngue completo (Português, Inglês, Alemão)
- Normalização por pico específico
- Diálogo de legenda interativa
- Remoção de background (SNIP, Rolling Ball, Polynomial)
- Correção de bugs no editor de CIF
- Melhorias de performance na plotagem
- Integração da licença GPL v3

---

## 🐛 Reportar Problemas

Encontrou um bug? Tem uma sugestão? Abra uma [issue](https://github.com/SrValentim/MatFinder/issues).

---

<div align="center">
  <sub>A excelência é um hábito</sub>
</div>

