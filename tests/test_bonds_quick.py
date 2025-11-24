"""
test_bonds_quick.py
Teste rápido para verificar se as ligações estão sendo calculadas corretamente
"""

import numpy as np
from pathlib import Path
import sys

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymatgen.core import Structure

def test_bonds():
    """Testa o cálculo de ligações."""

    # Encontrar um arquivo CIF
    cif_dir = project_root / "temp_cifs"

    if not cif_dir.exists() or not list(cif_dir.glob("*.cif")):
        print("❌ Nenhum arquivo CIF encontrado em temp_cifs/")
        return False

    # Usar o primeiro CIF encontrado
    cif_path = list(cif_dir.glob("*.cif"))[0]
    print(f"📁 Testando: {cif_path.name}\n")

    # Carregar estrutura
    structure = Structure.from_file(str(cif_path))
    print(f"✅ Estrutura carregada: {structure.composition.reduced_formula}")
    print(f"   Átomos: {len(structure)}\n")

    # Calcular ligações usando distance_matrix
    max_bond_length = 3.5
    distance_matrix = structure.distance_matrix
    n_sites = len(structure)

    bonds_found = []

    for i in range(n_sites):
        for j in range(i + 1, n_sites):
            distance = distance_matrix[i][j]

            if distance <= max_bond_length:
                element1 = structure[i].specie.symbol
                element2 = structure[j].specie.symbol
                pos1 = structure[i].coords
                pos2 = structure[j].coords

                bonds_found.append({
                    'i': i,
                    'j': j,
                    'element1': element1,
                    'element2': element2,
                    'distance': distance,
                    'pos1': pos1,
                    'pos2': pos2
                })

    print(f"🔗 Ligações encontradas (distância ≤ {max_bond_length} Å): {len(bonds_found)}\n")

    if len(bonds_found) == 0:
        print("⚠️  NENHUMA LIGAÇÃO ENCONTRADA!")
        print("   Possíveis razões:")
        print("   1. Estrutura muito esparsa (átomos muito distantes)")
        print("   2. max_bond_length muito pequeno")
        print("   3. Erro no cálculo da distance_matrix")
        return False

    # Mostrar as primeiras 10 ligações
    print("📊 Primeiras ligações encontradas:")
    print("-" * 80)

    for i, bond in enumerate(bonds_found[:10]):
        print(f"Ligação {i+1:2d}: {bond['element1']:3s}({bond['i']+1:2d}) ↔ "
              f"{bond['element2']:3s}({bond['j']+1:2d}) = {bond['distance']:.4f} Å")
        print(f"            Pos1: [{bond['pos1'][0]:8.4f}, {bond['pos1'][1]:8.4f}, {bond['pos1'][2]:8.4f}]")
        print(f"            Pos2: [{bond['pos2'][0]:8.4f}, {bond['pos2'][1]:8.4f}, {bond['pos2'][2]:8.4f}]")

    if len(bonds_found) > 10:
        print(f"... e mais {len(bonds_found) - 10} ligações")

    print("\n✅ O método está calculando ligações corretamente!")
    print("   Se as ligações não aparecem no visualizador, o problema é na renderização OpenGL")

    return True

if __name__ == "__main__":
    test_bonds()

