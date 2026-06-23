#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste do diálogo de reflexões
"""

import sys
from PySide6.QtWidgets import QApplication
from matfinder.tools.xrd.reflection_dialog import ReflectionDialog

def test_reflection_dialog():
    """Testa o diálogo de reflexões com um arquivo CIF."""

    # Ler arquivo CIF de teste
    cif_path = r"temp_cifs\MP_mp-568619_SiC.cif"
    with open(cif_path, 'r') as f:
        cif_content = f.read()

    # Parâmetros
    wavelength = 1.54056  # Cu Kα
    max_2theta = 100.0
    item_label = "SiC (MP_mp-568619)"

    # Criar aplicação Qt
    app = QApplication(sys.argv)

    # Criar e exibir diálogo
    dialog = ReflectionDialog(
        cif_content=cif_content,
        wavelength=wavelength,
        max_2theta=max_2theta,
        item_label=item_label
    )

    dialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    test_reflection_dialog()

