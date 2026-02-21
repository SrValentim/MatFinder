"""
test_bonds_visual.py
Teste visual rápido para verificar se as ligações estão sendo renderizadas
"""

import numpy as np
from pathlib import Path
import sys

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymatgen.core import Structure

def analyze_all_cifs():
    """Analisa todos os CIFs na pasta temp_cifs."""

    cif_dir = project_root / "temp_cifs"

    if not cif_dir.exists():
        print("❌ Pasta temp_cifs não encontrada")
        return

    cif_files = list(cif_dir.glob("*.cif"))

    if not cif_files:
        print("❌ Nenhum arquivo CIF encontrado")
        return

    print("=" * 80)
    print("ANÁLISE DE LIGAÇÕES EM ARQUIVOS CIF")
    print("=" * 80)

    for cif_path in cif_files:
        print(f"\n📁 {cif_path.name}")
        print("-" * 80)

        try:
            structure = Structure.from_file(str(cif_path))
            formula = structure.composition.reduced_formula
            n_atoms = len(structure)

            print(f"   Fórmula: {formula}")
            print(f"   Átomos: {n_atoms}")

            # Testar diferentes distâncias máximas
            for max_dist in [3.0, 3.5, 4.0, 4.5]:
                distance_matrix = structure.distance_matrix
                bonds = 0

                for i in range(n_atoms):
                    for j in range(i + 1, n_atoms):
                        if distance_matrix[i][j] <= max_dist:
                            bonds += 1

                print(f"   Ligações (≤ {max_dist} Å): {bonds}")

            # Mostrar elementos presentes
            elements = set([site.specie.symbol for site in structure])
            print(f"   Elementos: {', '.join(sorted(elements))}")

            # Mostrar distâncias mínimas entre cada par de elementos
            print(f"\n   Distâncias mínimas entre elementos:")
            distance_matrix = structure.distance_matrix

            element_pairs = {}
            for i in range(n_atoms):
                for j in range(i + 1, n_atoms):
                    elem1 = structure[i].specie.symbol
                    elem2 = structure[j].specie.symbol
                    pair = tuple(sorted([elem1, elem2]))
                    dist = distance_matrix[i][j]

                    if pair not in element_pairs or dist < element_pairs[pair]:
                        element_pairs[pair] = dist

            for pair, dist in sorted(element_pairs.items()):
                print(f"      {pair[0]}-{pair[1]}: {dist:.4f} Å")

        except Exception as e:
            print(f"   ❌ Erro: {e}")

    print("\n" + "=" * 80)
    print("RECOMENDAÇÕES:")
    print("=" * 80)
    print("• Para ver ligações, use max_bond_length baseado nas distâncias mínimas")
    print("• Estruturas com átomos muito distantes podem não ter ligações visíveis")
    print("• Aumentar max_bond_length mostra mais ligações")

if __name__ == "__main__":
    analyze_all_cifs()

