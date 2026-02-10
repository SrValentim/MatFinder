# Guia de Instalação e Execução do DEBUSSY v2.2 no Windows

## 📋 Sobre o DEBUSSY

O DEBUSSY (DEBye USer SYstem) é um software avançado para análise de estruturas cristalinas usando o método de análise de Função de Distribuição de Pares (PDF - Pair Distribution Function). É uma ferramenta complementar ao MatFinder para análises cristalográficas mais aprofundadas.

---

## 🖥️ Requisitos do Sistema

### Requisitos Mínimos
- **Sistema Operacional**: Windows 7/8/10/11 (64-bit recomendado)
- **RAM**: 2GB mínimo (4GB recomendado)
- **Espaço em Disco**: 200MB
- **Processador**: Dual-core 2.0 GHz ou superior

### Software Necessário
- Windows com suporte a aplicações de linha de comando
- Descompactador de arquivos (WinRAR, 7-Zip, ou similar)
- Editor de texto (Notepad++, Sublime Text, ou similar - opcional mas recomendado)

---

## 📥 Passo 1: Baixar o DEBUSSY

### Opção A: Via GitHub CLI (Recomendado)

1. **Instalar GitHub CLI** (se ainda não tiver):
   - Baixe de: https://cli.github.com/
   - Execute o instalador e siga as instruções na tela

2. **Abrir o Prompt de Comando**:
   - Pressione `Win + R`
   - Digite `cmd` e pressione Enter

3. **Navegar até a pasta desejada**:
   ```cmd
   cd C:\Users\SeuUsuario\Documents
   ```

4. **Clonar o repositório**:
   ```cmd
   gh repo clone DeByeUSerSYstem/DEBUSSY_v2.2-WINDOWS
   ```

### Opção B: Download Manual

1. **Acessar o repositório**:
   - Abra seu navegador e acesse: https://github.com/DeByeUSerSYstem/DEBUSSY_v2.2-WINDOWS

2. **Baixar o código**:
   - Clique no botão verde "Code"
   - Selecione "Download ZIP"
   - Salve o arquivo em uma pasta de fácil acesso (ex: `C:\DEBUSSY`)

3. **Extrair os arquivos**:
   - Clique com o botão direito no arquivo ZIP baixado
   - Selecione "Extrair tudo..." ou "Extract Here"
   - Aguarde a conclusão da extração

---

## 📂 Passo 2: Organizar os Arquivos

1. **Localizar a pasta extraída**:
   - A pasta deve se chamar `DEBUSSY_v2.2-WINDOWS` ou similar
   - Recomenda-se movê-la para uma localização simples, como:
     - `C:\DEBUSSY`
     - `C:\Programas\DEBUSSY`

2. **Verificar o conteúdo**:
   - Navegue até a pasta
   - Você deve ver arquivos executáveis (`.exe`), bibliotecas (`.dll`), e possivelmente uma pasta `examples` ou `docs`

---

## 🚀 Passo 3: Executar o DEBUSSY

### Primeira Execução

1. **Abrir a pasta do DEBUSSY**:
   - Navegue até `C:\DEBUSSY` (ou onde você extraiu)

2. **Localizar o executável principal**:
   - Procure por arquivos como:
     - `DEBUSSY.exe`
     - `debussy.exe`
     - `run_debussy.bat`
     - `start.exe`

3. **Executar o programa**:
   - Dê um duplo-clique no arquivo executável
   - **Se aparecer um aviso de segurança do Windows**:
     - Clique em "Mais informações"
     - Clique em "Executar assim mesmo"
     - (Isso é comum para software não assinado digitalmente)

### Execução via Linha de Comando (Método Alternativo)

1. **Abrir o Prompt de Comando como Administrador**:
   - Pressione `Win + X`
   - Selecione "Prompt de Comando (Admin)" ou "Windows PowerShell (Admin)"

2. **Navegar até a pasta do DEBUSSY**:
   ```cmd
   cd C:\DEBUSSY
   ```

3. **Executar o programa**:
   ```cmd
   DEBUSSY.exe
   ```
   ou
   ```cmd
   .\DEBUSSY.exe
   ```

---

## ⚙️ Passo 4: Configuração Inicial

### Configurar Variáveis de Ambiente (Opcional)

Para facilitar o acesso ao DEBUSSY de qualquer lugar:

1. **Abrir Configurações do Sistema**:
   - Pressione `Win + Pause/Break` ou
   - Clique com botão direito em "Este Computador" → "Propriedades"

2. **Acessar Variáveis de Ambiente**:
   - Clique em "Configurações avançadas do sistema"
   - Clique em "Variáveis de Ambiente"

3. **Adicionar ao PATH**:
   - Em "Variáveis do sistema", encontre e selecione "Path"
   - Clique em "Editar"
   - Clique em "Novo"
   - Adicione o caminho completo: `C:\DEBUSSY`
   - Clique em "OK" em todas as janelas

4. **Testar**:
   - Abra um novo Prompt de Comando
   - Digite `DEBUSSY` e pressione Enter
   - O programa deve iniciar de qualquer pasta

### Criar Atalho na Área de Trabalho

1. **Localizar o executável**:
   - Navegue até `C:\DEBUSSY`
   - Encontre `DEBUSSY.exe`

2. **Criar atalho**:
   - Clique com botão direito no executável
   - Selecione "Enviar para" → "Área de trabalho (criar atalho)"

3. **Personalizar o atalho** (opcional):
   - Clique com botão direito no atalho
   - Selecione "Propriedades"
   - Você pode alterar o ícone, nome, e pasta de inicialização

---

## 📚 Passo 5: Usar o DEBUSSY

### Arquivos de Entrada

O DEBUSSY geralmente trabalha com:
- **Arquivos CIF** (Crystallographic Information File)
- **Dados de difração** (formatos .dat, .xy, .txt)
- **Arquivos de configuração** (específicos do DEBUSSY)

### Fluxo de Trabalho Básico

1. **Preparar seus dados**:
   - Tenha seus arquivos CIF ou dados de difração prontos
   - Organize-os em uma pasta de fácil acesso

2. **Carregar dados no DEBUSSY**:
   - Use a interface do programa (se houver GUI)
   - Ou siga instruções de linha de comando conforme a documentação

3. **Configurar análise**:
   - Defina parâmetros conforme necessário
   - Consulte a documentação oficial do DEBUSSY

4. **Executar análise**:
   - Inicie o processamento
   - Aguarde os resultados

5. **Visualizar resultados**:
   - Examine os arquivos de saída
   - Use ferramentas de visualização complementares se necessário

---

## 🔧 Solução de Problemas

### O programa não abre

**Problema**: Duplo-clique no executável não faz nada
- **Solução 1**: Tente executar como Administrador (clique direito → "Executar como administrador")
- **Solução 2**: Verifique se todos os arquivos foram extraídos corretamente
- **Solução 3**: Verifique se há arquivos DLL faltando na pasta

### Erro de DLL faltando

**Problema**: Mensagem de erro sobre DLL não encontrada
- **Solução 1**: Instale o Microsoft Visual C++ Redistributable:
  - Baixe de: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist
  - Instale ambas as versões x86 e x64
- **Solução 2**: Verifique se todas as DLLs estão na pasta do DEBUSSY

### Antivírus bloqueia o programa

**Problema**: O antivírus detecta o DEBUSSY como ameaça
- **Solução**: Adicione uma exceção no seu antivírus:
  1. Abra as configurações do antivírus
  2. Procure por "Exceções" ou "Lista de permissões"
  3. Adicione a pasta `C:\DEBUSSY` completa

### Comando não reconhecido

**Problema**: Ao tentar executar via CMD, aparece "não reconhecido como comando"
- **Solução**: 
  - Certifique-se de estar na pasta correta: `cd C:\DEBUSSY`
  - Use `.\DEBUSSY.exe` em vez de apenas `DEBUSSY.exe`

---

## 🔗 Integração com MatFinder

O DEBUSSY pode ser usado em conjunto com o MatFinder para análises mais completas:

1. **Use o MatFinder** para:
   - Buscar estruturas cristalinas
   - Baixar arquivos CIF
   - Simular padrões de difração iniciais

2. **Use o DEBUSSY** para:
   - Análises avançadas de PDF
   - Refinamento de estruturas
   - Modelagem de desordem local

### Fluxo de Trabalho Integrado

```
MatFinder → Buscar material → Baixar CIF → DEBUSSY → Análise PDF
    ↑                                                      ↓
    └──────────────── Refinar estrutura ←─────────────────┘
```

---

## 📖 Recursos Adicionais

### Documentação

- **Repositório GitHub**: https://github.com/DeByeUSerSYstem/DEBUSSY_v2.2-WINDOWS
- **Issues/Problemas**: Abra um issue no GitHub se encontrar problemas
- **MatFinder**: Para análises complementares, use o MatFinder

### Suporte

- **GitHub Issues**: Reporte problemas no repositório do DEBUSSY
- **Comunidade MatFinder**: Para questões de integração

### Tutoriais Recomendados

1. Comece com os exemplos incluídos na pasta `examples` (se disponível)
2. Leia a documentação oficial do DEBUSSY (arquivo README ou docs)
3. Pratique com estruturas simples antes de análises complexas

---

## ✅ Checklist de Instalação

- [ ] Windows 7 ou superior instalado
- [ ] Espaço em disco suficiente (200MB+)
- [ ] DEBUSSY baixado do GitHub
- [ ] Arquivos extraídos para uma pasta permanente
- [ ] Executável principal localizado
- [ ] Programa executado com sucesso pela primeira vez
- [ ] Atalho criado (opcional)
- [ ] Variáveis de ambiente configuradas (opcional)
- [ ] Dependências instaladas (Visual C++ Redistributable se necessário)
- [ ] Arquivos de exemplo testados (se disponível)

---

## 💡 Dicas Importantes

1. **Mantenha a pasta organizada**: Não mova arquivos individuais, mantenha toda a estrutura intacta
2. **Faça backup**: Antes de atualizações, faça backup de suas configurações
3. **Use caminhos simples**: Evite espaços e caracteres especiais nos caminhos (use `C:\DEBUSSY` em vez de `C:\Meus Programas\DEBUSSY 2.2`)
4. **Consulte a documentação**: Sempre consulte o README do projeto para instruções específicas
5. **Atualize regularmente**: Verifique o GitHub para novas versões e correções

---

## 📝 Notas Finais

Este guia fornece um passo a passo geral para executar o DEBUSSY no Windows. Devido à natureza específica do software, alguns detalhes podem variar dependendo da versão exata do programa. Sempre consulte a documentação oficial incluída no repositório para instruções mais específicas.

Para dúvidas ou problemas específicos:
1. Consulte o repositório GitHub do DEBUSSY
2. Verifique a seção de Issues para problemas similares
3. Abra um novo issue com detalhes do seu problema

---

**Desenvolvido para a comunidade MatFinder**  
*Para análises cristalográficas de excelência*

---

<div align="center">
  <sub>Guia criado em: Fevereiro de 2026</sub>
</div>
