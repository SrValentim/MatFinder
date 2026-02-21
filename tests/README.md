# Testes do MatFinder

Esta pasta contém scripts de teste para diferentes funcionalidades do MatFinder.

## Estrutura dos Testes

### Testes do Visualizador 3D
- **test_structure_viewer_accuracy.py** - Validação de precisão do visualizador 3D
- **test_bonds_quick.py** - Teste rápido do algoritmo de ligações químicas
- **test_bonds_visual.py** - Teste visual das ligações químicas

### Testes de Funcionalidades do PhaseDRX
- **test_logo_resize.py** - Teste do redimensionamento automático da logo
- **test_reflection_dialog.py** - Teste do diálogo de reflexões cristalográficas
- **test_reflection_full.py** - Teste completo do sistema de reflexões

## Como Executar os Testes

### Testes do Visualizador 3D
```bash
# Teste de precisão do visualizador 3D
python tests/test_structure_viewer_accuracy.py

# Teste rápido de ligações
python tests/test_bonds_quick.py

# Teste visual de ligações
python tests/test_bonds_visual.py
```

### Testes do PhaseDRX
```bash
# Teste da logo
python tests/test_logo_resize.py

# Teste do diálogo de reflexões
python tests/test_reflection_dialog.py

# Teste completo de reflexões
python tests/test_reflection_full.py
```

## Requisitos

Todos os testes requerem as dependências principais do MatFinder instaladas:
- PySide6
- pymatgen
- matplotlib
- numpy
- scipy

Para instalar todas as dependências:
```bash
pip install -r requirements.txt
```

## Notas

- Os testes do visualizador 3D requerem `pymatgen` e `pyqtgraph`
- Os testes de reflexões requerem arquivos CIF válidos
- Alguns testes podem abrir janelas gráficas (feche-as para continuar)

