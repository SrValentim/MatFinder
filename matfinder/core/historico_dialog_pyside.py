# historico_dialog_pyside.py
#
# CAMINHO REFATORADO: matfinder/core/historico_dialog_pyside.py
#

import sys
import json
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QAbstractItemView,
    QMessageBox, QDialogButtonBox, QLabel, QAbstractButton
)
from PySide6.QtCore import Qt, Signal, QSize, Slot
from PySide6.QtGui import QIcon, QColor, QPixmap, QPainter

# Constantes para o arquivo de histórico
HISTORICO_FILE = "historico_buscas.json"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

# Ícones de estrela (Unicode)
FAVORITE_ICON_FILLED_STR = "★"
FAVORITE_ICON_EMPTY_STR = "☆"


class HistoricoDialog(QDialog):
    refazer_busca_signal = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico de Busca de Materiais")
        self.setMinimumSize(750, 500)
        self.historico_data = []

        self._init_ui()
        self.carregar_historico()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        # --- ALTERAÇÃO: Colunas ajustadas ---
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(
            ["★", "Termos da Busca", "Base de Dados", "Data da Consulta"]
        )
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_widget.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table_widget.verticalHeader().setVisible(False)

        self.table_widget.cellClicked.connect(self.on_cell_clicked)
        self.table_widget.itemDoubleClicked.connect(self.refazer_busca_selecionada_action)

        main_layout.addWidget(self.table_widget)

        buttons_layout = QHBoxLayout()

        self.refazer_busca_button = QPushButton("Refazer Busca")
        self.refazer_busca_button.setToolTip("Refaz a busca para o item selecionado.")
        self.refazer_busca_button.clicked.connect(self.refazer_busca_selecionada_action)
        buttons_layout.addWidget(self.refazer_busca_button)

        self.apagar_selecionado_button = QPushButton("Apagar Selecionado(s)")
        self.apagar_selecionado_button.setToolTip("Apaga os itens selecionados do histórico.")
        self.apagar_selecionado_button.clicked.connect(self.apagar_selecionados_action)
        buttons_layout.addWidget(self.apagar_selecionado_button)

        buttons_layout.addStretch()

        self.apagar_historico_button = QPushButton("Apagar Todo o Histórico")
        self.apagar_historico_button.setStyleSheet("color: red; font-weight: bold;")
        self.apagar_historico_button.setToolTip("Apaga permanentemente todo o histórico de busca.")
        self.apagar_historico_button.clicked.connect(self.apagar_todo_historico_action)
        buttons_layout.addWidget(self.apagar_historico_button)

        main_layout.addLayout(buttons_layout)

        self.dialog_button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.dialog_button_box.button(QDialogButtonBox.StandardButton.Close).setText("Fechar")
        self.dialog_button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.dialog_button_box)

    def resource_path(self, relative_path):
        """ 
        Obtém o caminho absoluto para o recurso.
        Modificado para apontar para a pasta raiz do projeto,
        não para a pasta 'core'.
        """
        try:
            # Se estiver compilado (PyInstaller), _MEIPASS é a pasta de extração
            base_path = sys._MEIPASS
        except AttributeError:
            # --- ALTERAÇÃO DE REATORAÇÃO: Lógica de Caminho ---
            # Em vez de os.path.abspath(os.path.dirname(__file__)), 
            # subimos dois níveis para chegar à raiz (MatFinder/).
            # __file__ -> matfinder/core/historico_dialog_pyside.py
            # .. -> matfinder/
            # .. -> MatFinder/ (raiz)
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            # --- FIM DA ALTERAÇÃO ---

        return os.path.join(base_path, relative_path)

    def carregar_historico(self):
        filepath = self.resource_path(HISTORICO_FILE)
        try:
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.historico_data = json.load(f)
                    if not isinstance(self.historico_data, list):
                        self.historico_data = []
            else:
                self.historico_data = []
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar histórico '{filepath}': {e}")
            self.historico_data = []

        self.ordenar_e_popular_tabela()

    def salvar_historico(self):
        filepath = self.resource_path(HISTORICO_FILE)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.historico_data, f, indent=4, ensure_ascii=False)
            print(f"Histórico salvo em: {filepath}")
        except IOError as e:
            print(f"Erro ao salvar histórico: {e}")
            QMessageBox.warning(self, "Erro ao Salvar", f"Não foi possível salvar o histórico: {e}")

    def ordenar_e_popular_tabela(self):
        try:
            self.historico_data.sort(key=lambda x: (
                not x.get("favorito", False),
                datetime.strptime(x.get("data_consulta", "1900-01-01T00:00:00.000000"), DATETIME_FORMAT)
            ), reverse=True)
        except ValueError as e:
            print(f"Erro ao ordenar histórico devido a formato de data inválido: {e}")
            self.historico_data.sort(key=lambda x: not x.get("favorito", False), reverse=True)

        self.table_widget.setRowCount(0)
        self.table_widget.setSortingEnabled(False)

        for i, entrada in enumerate(self.historico_data):
            self.table_widget.insertRow(i)

            fav_icon_str = FAVORITE_ICON_FILLED_STR if entrada.get("favorito") else FAVORITE_ICON_EMPTY_STR
            fav_item = QTableWidgetItem(fav_icon_str)
            fav_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if entrada.get("favorito"):
                fav_item.setForeground(QColor("orange"))
            self.table_widget.setItem(i, 0, fav_item)

            # --- ALTERAÇÃO: Usa o campo 'nome_display' que agora contém os termos da busca ---
            self.table_widget.setItem(i, 1, QTableWidgetItem(str(entrada.get("nome_display", "N/A"))))
            self.table_widget.setItem(i, 2, QTableWidgetItem(str(entrada.get("base_dados", "N/A"))))

            data_str_display = entrada.get("data_consulta", "N/A")
            try:
                data_obj = datetime.strptime(data_str_display, DATETIME_FORMAT)
                data_str_display = data_obj.strftime("%d/%m/%Y %H:%M:%S")
            except ValueError:
                pass
            self.table_widget.setItem(i, 3, QTableWidgetItem(data_str_display))

            for col in range(self.table_widget.columnCount()):
                if self.table_widget.item(i, col):
                    self.table_widget.item(i, col).setData(Qt.ItemDataRole.UserRole, i)

        self.table_widget.setSortingEnabled(True)

    @Slot(int, int)
    def on_cell_clicked(self, row, column):
        if column == 0:
            if 0 <= row < len(self.historico_data):
                entrada_selecionada = self.historico_data[row]
                entrada_selecionada["favorito"] = not entrada_selecionada.get("favorito", False)
                self.salvar_historico()
                self.ordenar_e_popular_tabela()

    @Slot()
    def refazer_busca_selecionada_action(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Nenhuma Seleção",
                                    "Por favor, selecione uma busca no histórico para refazer.")
            return

        selected_row = selected_items[0].row()

        if 0 <= selected_row < len(self.historico_data):
            entrada = self.historico_data[selected_row]
            termos = entrada.get("termos_busca")
            base = entrada.get("base_dados")
            if termos and base:
                self.refazer_busca_signal.emit(termos, base)
                self.accept()
            else:
                QMessageBox.warning(self, "Dados Incompletos",
                                    "A entrada do histórico selecionada não possui informações suficientes para refazer a busca.")

    @Slot()
    def apagar_selecionados_action(self):
        selected_rows = sorted(list(set(index.row() for index in self.table_widget.selectedIndexes())), reverse=True)
        if not selected_rows:
            QMessageBox.information(self, "Nenhuma Seleção", "Por favor, selecione itens do histórico para apagar.")
            return

        reply = QMessageBox.question(self, "Confirmar Exclusão",
                                     f"Tem certeza que deseja apagar os {len(selected_rows)} item(ns) selecionado(s) do histórico?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            indices_para_remover_da_lista_ordenada = selected_rows

            for row_index in indices_para_remover_da_lista_ordenada:
                if 0 <= row_index < len(self.historico_data):
                    del self.historico_data[row_index]

            self.salvar_historico()
            self.ordenar_e_popular_tabela()

    @Slot()
    def apagar_todo_historico_action(self):
        reply = QMessageBox.question(self, "Confirmar Exclusão Total",
                                     "Tem certeza que deseja apagar TODO o histórico de busca?\nEsta ação não pode ser desfeita.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.historico_data = []
            self.salvar_historico()
            self.ordenar_e_popular_tabela()
            QMessageBox.information(self, "Histórico Apagado", "Todo o histórico de busca foi apagado.")

    def showEvent(self, event):
        self.carregar_historico()
        super().showEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = HistoricoDialog()
    dialog.show()
    sys.exit(app.exec())