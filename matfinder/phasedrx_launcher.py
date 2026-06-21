"""Fluxo de abertura do PhaseDRX (diálogo Novo/Abrir + criação de projeto).

Reaproveitado por:
  - MatFinder (menu Ferramentas > PhaseDRX)  -> app_main.open_phasedrx_tool
  - PhaseDRX Suite (executável standalone)    -> run_phasedrx.py

Mantém UM único lugar com a lógica de projeto, evitando duplicação.
"""

import json
import logging
import os

from PySide6.QtWidgets import QMessageBox, QFileDialog

from matfinder.core.translator import tr


def open_phasedrx(parent=None):
    """Mostra o diálogo de projeto e retorna uma instância de PhaseDRXTool pronta
    para .show(), ou None se o usuário cancelar."""
    from matfinder.tools.xrd.xrd import PhaseDRXTool
    from matfinder.ui_dialogs import PhaseDRXProjectDialog

    dialog = PhaseDRXProjectDialog(parent)
    if not dialog.exec():
        return None

    choice = dialog.choice
    project_path_to_open = None

    if choice == dialog.NEW_PROJECT:
        project_name = dialog.project_name
        base_path = dialog.project_base_path
        project_dir = os.path.join(base_path, project_name)
        cif_dir = os.path.join(project_dir, "Cif")
        dados_dir = os.path.join(project_dir, "Dados")
        project_file = os.path.join(project_dir, f"{project_name}.mfpx")

        if os.path.exists(project_dir):
            reply = QMessageBox.question(
                parent, tr('project.folder_exists_title'),
                tr('project.folder_exists_msg', folder=project_dir),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.No:
                return None
            if not os.path.exists(project_file):
                QMessageBox.warning(parent, tr('project.file_not_found_title'),
                                    tr('project.file_not_found_msg', file=project_file))
                return None
            project_path_to_open = project_file
        else:
            try:
                os.makedirs(cif_dir)
                os.makedirs(dados_dir)
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                project_path_to_open = project_file
                logging.info(f"Nova estrutura de projeto criada em: {project_dir}")
            except OSError as e:
                QMessageBox.critical(parent, tr('project.create_error_title'),
                                     tr('project.create_error_msg', error=str(e)))
                return None

    elif choice == dialog.OPEN_PROJECT:
        path, _ = QFileDialog.getOpenFileName(
            parent, "Abrir Projeto PhaseDRX", "",
            "Projetos MatFinder (*.mfpx);;Todos os Arquivos (*)")
        if not path:
            return None
        project_path_to_open = path

    elif choice == dialog.ANONYMOUS_SESSION:
        project_path_to_open = None

    tool = PhaseDRXTool(parent=None, project_path=project_path_to_open)
    logging.info(f"PhaseDRX aberto. Projeto: {project_path_to_open or 'Sessão Anônima'}")
    return tool
