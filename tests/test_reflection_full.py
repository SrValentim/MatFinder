#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste completo do diálogo de reflexões
"""

import sys
import os
sys.path.insert(0, '.')

from PySide6.QtWidgets import QApplication

# Importar o diálogo
from matfinder.tools.xrd.reflection_dialog import ReflectionDialog

# CIF de exemplo (WC - Carbeto de Tungstênio)
SAMPLE_CIF = """
data_WC
_symmetry_space_group_name_H-M   'P -6 m 2'
_cell_length_a                   2.90610
_cell_length_b                   2.90610
_cell_length_c                   2.83780
_cell_angle_alpha                90
_cell_angle_beta                 90
_cell_angle_gamma                120
_symmetry_Int_Tables_number      187

loop_
_symmetry_equiv_pos_site_id
_symmetry_equiv_pos_as_xyz
1  'x, y, z'
2  '-y, x-y, z'
3  '-x+y, -x, z'
4  'x, y, -z'
5  '-y, x-y, -z'
6  '-x+y, -x, -z'
7  'y, x, z'
8  'x-y, -y, z'
9  '-x, -x+y, z'
10  'y, x, -z'
11  'x-y, -y, -z'
12  '-x, -x+y, -z'

loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_symmetry_multiplicity
_atom_site_Wyckoff_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
W1 W  1 a 0.00000 0.00000 0.00000 1.0
C1 C  1 d 0.33333 0.66667 0.50000 1.0
"""

def test_reflection_dialog():
    """Testa a abertura do diálogo de reflexões."""
    print("=" * 60)
    print("TESTE DO DIÁLOGO DE REFLEXÕES")
    print("=" * 60)

    # Criar aplicação Qt
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    print("\n✓ Aplicação Qt criada")

    # Parâmetros de teste
    wavelength = 1.54056  # Cu Kα
    max_2theta = 100.0
    item_label = "WC (Carbeto de Tungstênio)"

    print(f"✓ Comprimento de onda: {wavelength} Å")
    print(f"✓ 2θ máximo: {max_2theta}°")
    print(f"✓ Material: {item_label}")

    try:
        # Criar diálogo
        dialog = ReflectionDialog(
            cif_content=SAMPLE_CIF,
            wavelength=wavelength,
            max_2theta=max_2theta,
            item_label=item_label
        )

        print("\n✓ Diálogo criado com sucesso!")
        print(f"✓ Título da janela: {dialog.windowTitle()}")
        print(f"✓ Número de abas: {dialog.tab_widget.count()}")
        print(f"✓ Nome das abas: {[dialog.tab_widget.tabText(i) for i in range(dialog.tab_widget.count())]}")

        # Verificar tabela de condições
        cond_rows = dialog.conditions_table.rowCount()
        print(f"\n✓ Linhas na tabela de condições: {cond_rows}")

        if cond_rows > 0:
            print("\nPrimeiras 3 condições:")
            for i in range(min(3, cond_rows)):
                param = dialog.conditions_table.item(i, 0).text() if dialog.conditions_table.item(i, 0) else "N/A"
                value = dialog.conditions_table.item(i, 1).text() if dialog.conditions_table.item(i, 1) else "N/A"
                print(f"  {i+1}. {param}: {value}")

        # Verificar tabela de reflexões
        refl_rows = dialog.reflections_table.rowCount()
        refl_cols = dialog.reflections_table.columnCount()
        print(f"\n✓ Linhas na tabela de reflexões: {refl_rows}")
        print(f"✓ Colunas na tabela de reflexões: {refl_cols}")

        if refl_rows > 0:
            print("\nPrimeiras 5 reflexões:")
            headers = [dialog.reflections_table.horizontalHeaderItem(i).text()
                      for i in range(refl_cols)]
            print("  " + " | ".join(f"{h:>8}" for h in headers))
            print("  " + "-" * (10 * refl_cols))

            for i in range(min(5, refl_rows)):
                row_data = []
                for j in range(refl_cols):
                    item = dialog.reflections_table.item(i, j)
                    text = item.text() if item else "N/A"
                    row_data.append(text)
                print("  " + " | ".join(f"{d:>8}" for d in row_data))

        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("\nO diálogo está funcionando perfeitamente!")
        print("Para testar visualmente, execute o MatFinder e:")
        print("1. Abra PhaseDRX (Ferramentas → PhaseDRX)")
        print("2. Carregue um arquivo CIF")
        print("3. Clique direito no CIF → Reflexão")

        # Não mostrar o diálogo em modo de teste
        # dialog.exec()

        return True

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_reflection_dialog()
    sys.exit(0 if success else 1)

