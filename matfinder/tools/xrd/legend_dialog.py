# legend_dialog.py
# Dialog para personalização da legenda do gráfico
# Permite configurar fonte, tamanho, borda, ordem dos itens, posição e mais

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QSpinBox, QCheckBox, QComboBox, QDialogButtonBox,
    QLabel, QDoubleSpinBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import logging
import sys
import os
from matfinder.core.translator import ptr


class LegendDialog(QDialog):
    """Dialog para personalizar a aparência e comportamento da legenda."""

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)

        self.current_settings = current_settings or self._get_default_settings()

        self.setWindowTitle(ptr("Personalizar Legenda"))
        self.setMinimumWidth(500)
        self.setModal(True)

        # Configurar ícone do polvo
        self._set_polvo_icon()

        self._init_ui()
        self._load_current_settings()

    def _set_polvo_icon(self):
        """Configura o ícone do polvo no dialog."""
        try:
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.abspath(".")

            icon_path = os.path.join(base_path, "matfinder", "assets", "icons", "polvo.ico")

            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logging.debug(f"Erro ao configurar ícone do polvo: {e}")

    def _get_default_settings(self):
        """Retorna configurações padrão da legenda."""
        return {
            "visible": True,
            "fontsize": 10,
            "fontweight": "normal",  # 'normal' ou 'bold'
            "fontstyle": "normal",   # 'normal' ou 'italic'
            "frameon": True,         # Borda ao redor da legenda
            "reverse": False,        # Inverter ordem dos itens
            "loc": "best",           # Localização ('best', 'upper right', etc.)
            "draggable": True,       # Permitir arrastar a legenda
            "fancybox": True,        # Cantos arredondados
            "shadow": False,         # Sombra
            "framealpha": 0.9,       # Transparência da borda (0-1)
            "ncol": 1,               # Número de colunas
        }

    def _init_ui(self):
        """Inicializa a interface do usuário."""
        main_layout = QVBoxLayout(self)

        # Grupo: Aparência da Fonte
        font_group = self._create_font_group()
        main_layout.addWidget(font_group)

        # Grupo: Borda e Estilo
        frame_group = self._create_frame_group()
        main_layout.addWidget(frame_group)

        # Grupo: Posição e Comportamento
        position_group = self._create_position_group()
        main_layout.addWidget(position_group)

        # Grupo: Layout
        layout_group = self._create_layout_group()
        main_layout.addWidget(layout_group)

        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Apply).setText(ptr("Aplicar"))
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText(ptr("Aceitar"))
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(ptr("Cancelar"))

        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)

    def _create_font_group(self):
        """Cria grupo de configurações de fonte."""
        group = QGroupBox(ptr("Aparência da Fonte"))
        layout = QFormLayout(group)

        # Tamanho da fonte
        self.fontsize_spin = QSpinBox()
        self.fontsize_spin.setRange(6, 72)
        self.fontsize_spin.setValue(10)
        self.fontsize_spin.setSuffix(ptr(" pt"))
        layout.addRow("Tamanho da Fonte:", self.fontsize_spin)

        # Negrito e Itálico
        style_layout = QHBoxLayout()
        self.bold_check = QCheckBox(ptr("Negrito"))
        self.italic_check = QCheckBox(ptr("Itálico"))
        style_layout.addWidget(self.bold_check)
        style_layout.addWidget(self.italic_check)
        style_layout.addStretch()
        layout.addRow("Estilo:", style_layout)

        return group

    def _create_frame_group(self):
        """Cria grupo de configurações de borda."""
        group = QGroupBox(ptr("Borda e Estilo"))
        layout = QFormLayout(group)

        # Mostrar borda
        self.frameon_check = QCheckBox(ptr("Mostrar borda ao redor da legenda"))
        self.frameon_check.setChecked(True)
        layout.addRow(self.frameon_check)

        # Transparência da borda
        self.framealpha_spin = QDoubleSpinBox()
        self.framealpha_spin.setRange(0.0, 1.0)
        self.framealpha_spin.setSingleStep(0.1)
        self.framealpha_spin.setValue(0.9)
        self.framealpha_spin.setDecimals(2)
        layout.addRow("Opacidade da Borda:", self.framealpha_spin)

        # Cantos arredondados
        self.fancybox_check = QCheckBox(ptr("Cantos arredondados"))
        self.fancybox_check.setChecked(True)
        layout.addRow(self.fancybox_check)

        # Sombra
        self.shadow_check = QCheckBox(ptr("Adicionar sombra"))
        self.shadow_check.setChecked(False)
        layout.addRow(self.shadow_check)

        return group

    def _create_position_group(self):
        """Cria grupo de configurações de posição."""
        group = QGroupBox(ptr("Posição e Comportamento"))
        layout = QFormLayout(group)

        # Localização
        self.location_combo = QComboBox()
        locations = [
            ("Melhor Posição (Automático)", "best"),
            ("Superior Direita", "upper right"),
            ("Superior Esquerda", "upper left"),
            ("Inferior Direita", "lower right"),
            ("Inferior Esquerda", "lower left"),
            ("Centro Direita", "center right"),
            ("Centro Esquerda", "center left"),
            ("Superior Centro", "upper center"),
            ("Inferior Centro", "lower center"),
            ("Centro", "center"),
        ]
        for label, value in locations:
            self.location_combo.addItem(label, value)
        layout.addRow("Localização Inicial:", self.location_combo)

        # Travar posição
        self.draggable_check = QCheckBox(ptr("Permitir mover legenda com o mouse"))
        self.draggable_check.setChecked(True)
        self.draggable_check.setToolTip(
            "Se ativado, você pode clicar e arrastar a legenda para qualquer posição no gráfico.\n"
            "Se desativado, a legenda fica fixa na posição selecionada acima."
        )
        layout.addRow(self.draggable_check)

        # Info sobre arrastar
        info_label = QLabel(
            ptr("<i>Dica: Com a opção acima ativada, clique e arraste a legenda no gráfico para reposicioná-la.</i>")
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addRow(info_label)

        # Botão para resetar posição customizada
        self.reset_position_btn = QPushButton(ptr("Resetar Posição Customizada"))
        self.reset_position_btn.setToolTip(
            "Clique para remover qualquer posição customizada (arrastada) "
            "e usar a localização selecionada acima."
        )
        self.reset_position_btn.clicked.connect(self._reset_custom_position)
        layout.addRow(self.reset_position_btn)

        return group

    def _reset_custom_position(self):
        """Remove a posição customizada (bbox_to_anchor) das configurações."""
        if "bbox_to_anchor" in self.current_settings:
            self.current_settings.pop("bbox_to_anchor")
            QMessageBox.information(
                self,
                ptr("Posição Resetada"),
                "A posição customizada foi removida.\n"
                "A legenda agora usará a localização selecionada acima.\n\n"
                "Clique em 'Aplicar' ou 'Aceitar' para ver o resultado."
            )
            logging.debug("Posição customizada da legenda removida")

    def _create_layout_group(self):
        """Cria grupo de configurações de layout."""
        group = QGroupBox(ptr("Layout da Legenda"))
        layout = QFormLayout(group)

        # Número de colunas
        self.ncol_spin = QSpinBox()
        self.ncol_spin.setRange(1, 10)
        self.ncol_spin.setValue(1)
        self.ncol_spin.setToolTip(
            "Número de colunas para organizar os itens da legenda.\n"
            "1 coluna = vertical (padrão)\n"
            "2+ colunas = itens organizados horizontalmente"
        )
        layout.addRow("Número de Colunas:", self.ncol_spin)

        # Inverter ordem
        self.reverse_check = QCheckBox(ptr("Inverter ordem dos itens"))
        self.reverse_check.setChecked(False)
        self.reverse_check.setToolTip(
            "Inverte a ordem em que os itens aparecem na legenda.\n"
            "Útil para ajustar a ordem de visualização."
        )
        layout.addRow(self.reverse_check)

        return group

    def _load_current_settings(self):
        """Carrega as configurações atuais nos widgets."""
        settings = self.current_settings

        # Fonte
        self.fontsize_spin.setValue(settings.get("fontsize", 10))
        self.bold_check.setChecked(settings.get("fontweight", "normal") == "bold")
        self.italic_check.setChecked(settings.get("fontstyle", "normal") == "italic")

        # Borda
        self.frameon_check.setChecked(settings.get("frameon", True))
        self.framealpha_spin.setValue(settings.get("framealpha", 0.9))
        self.fancybox_check.setChecked(settings.get("fancybox", True))
        self.shadow_check.setChecked(settings.get("shadow", False))

        # Posição
        loc = settings.get("loc", "best")
        index = self.location_combo.findData(loc)
        if index >= 0:
            self.location_combo.setCurrentIndex(index)
        self.draggable_check.setChecked(settings.get("draggable", True))

        # Layout
        self.ncol_spin.setValue(settings.get("ncol", 1))
        self.reverse_check.setChecked(settings.get("reverse", False))

    def get_settings(self):
        """Retorna as configurações atuais do dialog."""
        settings = {
            "visible": True,
            "fontsize": self.fontsize_spin.value(),
            "fontweight": "bold" if self.bold_check.isChecked() else "normal",
            "fontstyle": "italic" if self.italic_check.isChecked() else "normal",
            "frameon": self.frameon_check.isChecked(),
            "framealpha": self.framealpha_spin.value(),
            "fancybox": self.fancybox_check.isChecked(),
            "shadow": self.shadow_check.isChecked(),
            "loc": self.location_combo.currentData(),
            "draggable": self.draggable_check.isChecked(),
            "ncol": self.ncol_spin.value(),
            "reverse": self.reverse_check.isChecked(),
        }

        # Preservar bbox_to_anchor se existir (posição customizada)
        if "bbox_to_anchor" in self.current_settings:
            settings["bbox_to_anchor"] = self.current_settings["bbox_to_anchor"]

        return settings

    def apply_settings(self):
        """Aplica as configurações sem fechar o dialog."""
        settings = self.get_settings()
        logging.debug(f"Aplicando configurações da legenda: {settings}")

        # Emitir sinal para aplicar (será implementado no parent)
        if hasattr(self.parent(), 'apply_legend_settings'):
            self.parent().apply_legend_settings(settings)

