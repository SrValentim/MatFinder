# cif_editor_dialog.py
# Versão 6.0 - Adicionados parâmetros de simulação de pico ao editor multifásico
#
# CAMINHO REFATORADO: matfinder/data/cif_editor_dialog.py
#

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QDialogButtonBox, QLabel, QWidget,
    QMessageBox, QGroupBox, QComboBox, QDoubleSpinBox, QHBoxLayout,
    QPushButton, QListWidget, QAbstractItemView, QListWidgetItem,
    QFormLayout
)
from PySide6.QtCore import Qt, Signal

# --- ALTERAÇÃO DE REATORAÇÃO: Importação Relativa ---
# Como 'cif_handler.py' está na mesma pasta 'data/',
# usamos um '.' para importá-lo.
from .cif_handler import CifHandler, PYMATGEN_AVAILABLE
# --- FIM DA ALTERAÇÃO ---


class CustomDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox customizado com passo diferente para roda do mouse."""

    def __init__(self, parent=None, wheel_step=None):
        super().__init__(parent)
        self._wheel_step = wheel_step  # Passo customizado para roda do mouse

    def wheelEvent(self, event):
        """Override do evento da roda do mouse para usar passo customizado."""
        if self._wheel_step is not None:
            # Obter direção da roda
            delta = event.angleDelta().y()
            if delta > 0:  # Roda para cima
                self.setValue(self.value() + self._wheel_step)
            elif delta < 0:  # Roda para baixo
                self.setValue(self.value() - self._wheel_step)
            event.accept()
        else:
            # Usar comportamento padrão se wheel_step não foi definido
            super().wheelEvent(event)


class CifEditorDialog(QDialog):
    """
    Diálogo para editar os parâmetros de rede e simulação de um arquivo CIF.
    """
    simulationParametersModified = Signal(str, dict)
    structureModified = Signal(str)  # Emitido quando a estrutura CIF muda (conteúdo CIF atualizado)

    def __init__(self, cif_content: str, initial_pattern: tuple, simulation_params: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Parâmetros Cristalográficos")
        self.setMinimumWidth(550)

        self.original_cif_content = cif_content
        self.initial_pattern_peaks = initial_pattern[0] if initial_pattern else []
        self.simulation_params = simulation_params if simulation_params else {}
        self.cif_handler = None
        self._block_signals = False
        self.selected_ranges = []

        self._init_ui()
        self._setup_connections()

        try:
            if not PYMATGEN_AVAILABLE:
                raise ImportError("A biblioteca 'pymatgen' não foi encontrada.")
            self.cif_handler = CifHandler(cif_content)
            self._populate_fields_from_handler()
            self._apply_crystal_system_constraints()
            self._populate_peak_list()
            self._populate_simulation_fields()
        except (ImportError, ValueError) as e:
            QMessageBox.critical(self, "Erro ao Carregar CIF", f"Não foi possível processar o arquivo CIF:\n{e}")
            self.main_widget.setEnabled(False)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)

        params_group = QGroupBox("Parâmetros da Célula Unitária")
        params_grid = QGridLayout(params_group)

        self.a_spin = self._create_spinbox(step=0.01, wheel_step=0.05)
        self.b_spin = self._create_spinbox(step=0.01, wheel_step=0.05)
        self.c_spin = self._create_spinbox(step=0.01, wheel_step=0.05)
        self.alpha_spin = self._create_spinbox(0, 180, step=0.01, wheel_step=0.05)
        self.beta_spin = self._create_spinbox(0, 180, step=0.01, wheel_step=0.05)
        self.gamma_spin = self._create_spinbox(0, 180, step=0.01, wheel_step=0.05)
        self.volume_spin = self._create_spinbox(decimals=4, step=1.0, wheel_step=0.2)

        params_grid.addWidget(QLabel("a (Å)"), 0, 0);
        params_grid.addWidget(self.a_spin, 0, 1)
        params_grid.addWidget(QLabel("b (Å)"), 0, 2);
        params_grid.addWidget(self.b_spin, 0, 3)
        params_grid.addWidget(QLabel("c (Å)"), 0, 4);
        params_grid.addWidget(self.c_spin, 0, 5)
        params_grid.addWidget(QLabel("α (°)"), 1, 0);
        params_grid.addWidget(self.alpha_spin, 1, 1)
        params_grid.addWidget(QLabel("β (°)"), 1, 2);
        params_grid.addWidget(self.beta_spin, 1, 3)
        params_grid.addWidget(QLabel("γ (°)"), 1, 4);
        params_grid.addWidget(self.gamma_spin, 1, 5)
        params_grid.addWidget(QLabel("Volume (Å³)"), 2, 0);
        params_grid.addWidget(self.volume_spin, 2, 1, 1, 5)
        main_layout.addWidget(params_group)

        sim_group = QGroupBox("Parâmetros de Simulação de Pico")
        sim_layout = QVBoxLayout(sim_group)

        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Função de Perfil:"))
        self.convolution_combo = QComboBox()
        self.convolution_combo.addItems(["Pseudo-Voigt", "Gaussiana", "Lorentziana"])
        profile_layout.addWidget(self.convolution_combo)
        profile_layout.addWidget(QLabel("FWHM (°):"))
        self.fwhm_spin = self._create_spinbox(min_val=0.001, max_val=5.0, decimals=3, step=0.01)
        profile_layout.addWidget(self.fwhm_spin)
        sim_layout.addLayout(profile_layout)

        apply_mode_layout = QHBoxLayout()
        apply_mode_layout.addWidget(QLabel("Aplicar em:"))
        self.apply_mode_combo = QComboBox()
        self.apply_mode_combo.addItems(["Padrão Inteiro", "Ranges Selecionados"])
        apply_mode_layout.addWidget(self.apply_mode_combo)
        self.apply_button = QPushButton("Aplicar Função")
        apply_mode_layout.addWidget(self.apply_button)
        sim_layout.addLayout(apply_mode_layout)

        self.range_widget = QWidget()
        range_layout = QHBoxLayout(self.range_widget)

        peak_list_group = QGroupBox("Picos Detectados (2θ)")
        peak_list_layout = QVBoxLayout(peak_list_group)
        self.peak_list_widget = QListWidget()
        self.peak_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        peak_list_layout.addWidget(self.peak_list_widget)
        range_layout.addWidget(peak_list_group)

        range_buttons_layout = QVBoxLayout()
        self.add_range_button = QPushButton("Adicionar\nRange →")
        self.remove_range_button = QPushButton("← Remover\nRange")
        range_buttons_layout.addWidget(self.add_range_button)
        range_buttons_layout.addWidget(self.remove_range_button)
        range_buttons_layout.addStretch()
        range_layout.addLayout(range_buttons_layout)

        selected_ranges_group = QGroupBox("Ranges para Convolução")
        selected_ranges_layout = QVBoxLayout(selected_ranges_group)
        self.selected_ranges_list = QListWidget()
        selected_ranges_layout.addWidget(self.selected_ranges_list)
        range_layout.addWidget(selected_ranges_group)

        sim_layout.addWidget(self.range_widget)
        main_layout.addWidget(sim_group)

        layout.addWidget(self.main_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.range_widget.setVisible(False)

    def _create_spinbox(self, min_val=0.0001, max_val=1000.0, decimals=4, step=0.01, wheel_step=None):
        spinbox = CustomDoubleSpinBox(wheel_step=wheel_step)
        spinbox.setRange(min_val, max_val)
        spinbox.setDecimals(decimals)
        spinbox.setSingleStep(step)
        spinbox.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        spinbox.setKeyboardTracking(False)
        return spinbox

    def _setup_connections(self):
        self.a_spin.valueChanged.connect(lambda: self._update_from_lattice_params('a'))
        self.b_spin.valueChanged.connect(lambda: self._update_from_lattice_params('b'))
        self.c_spin.valueChanged.connect(lambda: self._update_from_lattice_params('c'))
        self.alpha_spin.valueChanged.connect(self._update_from_lattice_params)
        self.beta_spin.valueChanged.connect(self._update_from_lattice_params)
        self.gamma_spin.valueChanged.connect(self._update_from_lattice_params)
        self.volume_spin.valueChanged.connect(self._update_from_volume)

        self.apply_mode_combo.currentIndexChanged.connect(self._toggle_range_selection_ui)
        self.add_range_button.clicked.connect(self._add_range)
        self.remove_range_button.clicked.connect(self._remove_range)
        self.apply_button.clicked.connect(self._apply_simulation_params)

    def _populate_fields_from_handler(self):
        if not self.cif_handler: return
        self._block_signals = True
        try:
            params = self.cif_handler.get_lattice_params()
            self.a_spin.setValue(params['a'])
            self.b_spin.setValue(params['b'])
            self.c_spin.setValue(params['c'])
            self.alpha_spin.setValue(params['alpha'])
            self.beta_spin.setValue(params['beta'])
            self.gamma_spin.setValue(params['gamma'])
            self.volume_spin.setValue(params['volume'])
        finally:
            self._block_signals = False

    def _populate_simulation_fields(self):
        self._block_signals = True
        try:
            fwhm = self.simulation_params.get('fwhm', 0.120)
            self.fwhm_spin.setValue(fwhm)

            profile = self.simulation_params.get('profile', 'pseudo-voigt').capitalize()
            if profile == "Pseudo-voigt": profile = "Pseudo-Voigt"
            self.convolution_combo.setCurrentText(profile)

            apply_mode = self.simulation_params.get('apply_mode', 'Padrão Inteiro')
            self.apply_mode_combo.setCurrentText(apply_mode)
            self._toggle_range_selection_ui(self.apply_mode_combo.currentIndex())

            self.selected_ranges = self.simulation_params.get('ranges', [])
            self.selected_ranges_list.clear()
            for r_min, r_max in self.selected_ranges:
                self.selected_ranges_list.addItem(f"Range: {r_min:.2f}° - {r_max:.2f}°")

        finally:
            self._block_signals = False

    def _apply_crystal_system_constraints(self):
        if not self.cif_handler: return

        system = self.cif_handler.get_crystal_system()

        # Obter informações do grupo espacial
        sg_info = self.cif_handler.get_space_group_info()
        sg_number = sg_info.get('number')
        sg_symbol = sg_info.get('symbol', '')

        # Criar título com número do grupo espacial
        if sg_number:
            title = f"Editor - Sistema {system.capitalize()} - {sg_symbol} ({sg_number})"
        else:
            title = f"Editor - Sistema {system.capitalize()}"

        self.setWindowTitle(title)

        # Habilita todos por padrão
        for spinbox in [self.a_spin, self.b_spin, self.c_spin, self.alpha_spin, self.beta_spin, self.gamma_spin]:
            spinbox.setEnabled(True)

        # Aplica restrições específicas por sistema
        if system == 'cubic':
            # Cúbico: a = b = c, α = β = γ = 90° (apenas 'a' editável)
            self.b_spin.setEnabled(False)
            self.c_spin.setEnabled(False)
            self.alpha_spin.setEnabled(False)
            self.beta_spin.setEnabled(False)
            self.gamma_spin.setEnabled(False)
        elif system == 'tetragonal':
            # Tetragonal: a = b ≠ c, α = β = γ = 90° (apenas 'a' e 'c' editáveis)
            self.b_spin.setEnabled(False)
            self.alpha_spin.setEnabled(False)
            self.beta_spin.setEnabled(False)
            self.gamma_spin.setEnabled(False)
        elif system == 'hexagonal':
            # Hexagonal: a = b ≠ c, α = β = 90°, γ = 120° (apenas 'a' e 'c' editáveis)
            self.b_spin.setEnabled(False)
            self.alpha_spin.setEnabled(False)
            self.beta_spin.setEnabled(False)
            self.gamma_spin.setEnabled(False)
        elif system in ['trigonal', 'rhombohedral']:
            # Trigonal pode ter duas configurações:
            # 1. Hexagonal: a = b ≠ c, α = β = 90°, γ = 120° → editar a, c
            # 2. Romboédrica: a = b = c, α = β = γ ≠ 90° → editar a, α
            # Detectar qual configuração pelos parâmetros
            params = self.cif_handler.get_lattice_params()
            is_rhombohedral = (abs(params['a'] - params['c']) < 0.01 and
                              abs(params['alpha'] - params['gamma']) < 0.1 and
                              abs(params['alpha'] - 90.0) > 0.1)

            if is_rhombohedral or system == 'rhombohedral':
                # Romboédrico: a = b = c, α = β = γ ≠ 90° (apenas 'a' e 'alpha' editáveis)
                if sg_number:
                    self.setWindowTitle(f"Editor - Sistema Trigonal (Romboédrico) - {sg_symbol} ({sg_number})")
                else:
                    self.setWindowTitle(f"Editor - Sistema Trigonal (Romboédrico)")
                self.b_spin.setEnabled(False)
                self.c_spin.setEnabled(False)
                self.beta_spin.setEnabled(False)
                self.gamma_spin.setEnabled(False)
            else:
                # Hexagonal: a = b ≠ c, α = β = 90°, γ = 120° (apenas 'a' e 'c' editáveis)
                if sg_number:
                    self.setWindowTitle(f"Editor - Sistema Trigonal (Hexagonal) - {sg_symbol} ({sg_number})")
                else:
                    self.setWindowTitle(f"Editor - Sistema Trigonal (Hexagonal)")
                self.b_spin.setEnabled(False)
                self.alpha_spin.setEnabled(False)
                self.beta_spin.setEnabled(False)
                self.gamma_spin.setEnabled(False)
        elif system == 'orthorhombic':
            # Ortorrômbico: a ≠ b ≠ c, α = β = γ = 90° (apenas a, b, c editáveis)
            self.alpha_spin.setEnabled(False)
            self.beta_spin.setEnabled(False)
            self.gamma_spin.setEnabled(False)
        elif system == 'monoclinic':
            # Monoclínico: a ≠ b ≠ c, α = γ = 90°, β ≠ 90° (apenas 'beta' editável nos ângulos)
            self.alpha_spin.setEnabled(False)
            self.gamma_spin.setEnabled(False)
        elif system == 'triclinic':
            # Triclínico: a ≠ b ≠ c, α ≠ β ≠ γ (todos editáveis)
            pass  # Todos já estão habilitados

    def _update_from_lattice_params(self, changed_param=None):
        if self._block_signals or not self.cif_handler: return
        try:
            system = self.cif_handler.get_crystal_system()

            # Sincroniza parâmetros dependentes
            if system == 'cubic':
                # a = b = c
                val = self.a_spin.value()
                self.b_spin.setValue(val)
                self.c_spin.setValue(val)
            elif system in ['tetragonal', 'hexagonal']:
                # a = b
                if changed_param == 'a':
                    self.b_spin.setValue(self.a_spin.value())
                elif changed_param == 'b':
                    self.a_spin.setValue(self.b_spin.value())
            elif system in ['trigonal', 'rhombohedral']:
                # Detectar configuração (hexagonal vs romboédrica)
                params = self.cif_handler.get_lattice_params()
                is_rhombohedral = (abs(params['a'] - params['c']) < 0.01 and
                                  abs(params['alpha'] - params['gamma']) < 0.1 and
                                  abs(params['alpha'] - 90.0) > 0.1)

                if is_rhombohedral or system == 'rhombohedral':
                    # Romboédrico: a = b = c e α = β = γ
                    if changed_param == 'a':
                        self.b_spin.setValue(self.a_spin.value())
                        self.c_spin.setValue(self.a_spin.value())
                    elif changed_param in ['b', 'c']:
                        val = self.b_spin.value() if changed_param == 'b' else self.c_spin.value()
                        self.a_spin.setValue(val)
                        self.b_spin.setValue(val)
                        self.c_spin.setValue(val)

                    if changed_param == 'alpha':
                        self.beta_spin.setValue(self.alpha_spin.value())
                        self.gamma_spin.setValue(self.alpha_spin.value())
                    elif changed_param in ['beta', 'gamma']:
                        val = self.beta_spin.value() if changed_param == 'beta' else self.gamma_spin.value()
                        self.alpha_spin.setValue(val)
                        self.beta_spin.setValue(val)
                        self.gamma_spin.setValue(val)
                else:
                    # Hexagonal: a = b (γ = 120° é fixo)
                    if changed_param == 'a':
                        self.b_spin.setValue(self.a_spin.value())
                    elif changed_param == 'b':
                        self.a_spin.setValue(self.b_spin.value())

            self.cif_handler.update_lattice_params(
                a=self.a_spin.value(), b=self.b_spin.value(), c=self.c_spin.value(),
                alpha=self.alpha_spin.value(), beta=self.beta_spin.value(), gamma=self.gamma_spin.value()
            )
            self._send_update(lattice_changed=True)
        except (ValueError, TypeError) as e:
            QMessageBox.warning(self, "Valor Inválido", f"Erro ao atualizar: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Atualização", f"Não foi possível atualizar a estrutura:\n{e}")

    def _update_from_volume(self):
        if self._block_signals or not self.cif_handler: return
        try:
            self.cif_handler.scale_volume(self.volume_spin.value())
            self._send_update(lattice_changed=True)
        except (ValueError, TypeError) as e:
            QMessageBox.warning(self, "Valor Inválido", f"Erro ao escalar volume: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Atualização", f"Não foi possível escalar o volume:\n{e}")

    def _toggle_range_selection_ui(self, index):
        self.range_widget.setVisible(index == 1)

    def _populate_peak_list(self):
        self.peak_list_widget.clear()
        for peak_2theta in self.initial_pattern_peaks:
            self.peak_list_widget.addItem(f"{peak_2theta:.4f}")

    def _add_range(self):
        selected_items = self.peak_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Nenhuma Seleção", "Selecione um ou mais picos para criar um range.")
            return

        selected_peaks = sorted([float(item.text()) for item in selected_items])
        if not selected_peaks: return

        range_min = selected_peaks[0] - 0.1
        range_max = selected_peaks[-1] + 0.1

        new_range = (range_min, range_max)
        self.selected_ranges.append(new_range)
        self.selected_ranges_list.addItem(f"Range: {range_min:.2f}° - {range_max:.2f}°")

    def _remove_range(self):
        selected_items = self.selected_ranges_list.selectedItems()
        if not selected_items: return

        for item in selected_items:
            row = self.selected_ranges_list.row(item)
            self.selected_ranges_list.takeItem(row)
            if 0 <= row < len(self.selected_ranges):
                del self.selected_ranges[row]

    def _apply_simulation_params(self):
        self._send_update(lattice_changed=False)

    def _send_update(self, lattice_changed=False):
        if lattice_changed:
            self._populate_fields_from_handler()

        new_cif_content = self.cif_handler.get_cif_string()

        sim_params = {
            "profile": self.convolution_combo.currentText().lower().replace("-", ""),
            "fwhm": self.fwhm_spin.value(),
            "apply_mode": self.apply_mode_combo.currentText(),
            "ranges": self.selected_ranges if self.apply_mode_combo.currentText() == "Ranges Selecionados" else []
        }

        self.simulationParametersModified.emit(new_cif_content, sim_params)
        logging.info("Sinal simulationParametersModified emitido.")

        # Emitir sinal para atualizar visualizador 3D
        if lattice_changed:
            self.structureModified.emit(new_cif_content)
            logging.debug("Sinal structureModified emitido para atualizar visualizador 3D.")


class MultiphaseEditorDialog(QDialog):
    """
    Diálogo para editar os parâmetros de uma combinação multifásica.
    """
    parametersChanged = Signal(str, list, dict)

    def __init__(self, multiphase_item: dict, component_info: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Combinação Multifásica")
        self.setMinimumWidth(450)

        self.item_id = multiphase_item.get("id")
        self.component_info = component_info
        self.simulation_params = multiphase_item.get("simulation_params", {})
        self.spinboxes = []
        self._block_signals = False

        self._init_ui()
        self._setup_connections()
        self._populate_simulation_fields()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Grupo de Proporções de Fase ---
        proportions_group = QGroupBox(f"Proporções de Fase")
        form_layout = QFormLayout(proportions_group)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        for comp in self.component_info:
            label = QLabel(comp.get("label"))
            spinbox = QDoubleSpinBox()
            spinbox.setRange(0.0, 1.0)
            spinbox.setDecimals(3)
            spinbox.setSingleStep(0.01)
            spinbox.setValue(comp.get("weight", 0.0))
            form_layout.addRow(label, spinbox)
            self.spinboxes.append(spinbox)
        main_layout.addWidget(proportions_group)

        self.total_label = QLabel("Total: 100.0%")
        self.total_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.total_label, 0, Qt.AlignmentFlag.AlignRight)

        # --- Grupo de Simulação de Pico ---
        sim_group = QGroupBox("Parâmetros de Simulação de Pico (para a combinação)")
        sim_layout = QVBoxLayout(sim_group)
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Função de Perfil:"))
        self.convolution_combo = QComboBox()
        self.convolution_combo.addItems(["Pseudo-Voigt", "Gaussiana", "Lorentziana"])
        profile_layout.addWidget(self.convolution_combo)
        profile_layout.addWidget(QLabel("FWHM (°):"))
        self.fwhm_spin = QDoubleSpinBox()
        self.fwhm_spin.setRange(0.001, 5.0)
        self.fwhm_spin.setDecimals(3)
        self.fwhm_spin.setSingleStep(0.01)
        sim_layout.addLayout(profile_layout)
        profile_layout.addWidget(self.fwhm_spin)
        main_layout.addWidget(sim_group)

        # --- Botões ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._update_total_label()

    def _setup_connections(self):
        for spinbox in self.spinboxes:
            spinbox.valueChanged.connect(self._update_weights)

    def _populate_simulation_fields(self):
        self._block_signals = True
        fwhm = self.simulation_params.get('fwhm', 0.120)
        self.fwhm_spin.setValue(fwhm)
        profile = self.simulation_params.get('profile', 'pseudo-voigt').capitalize()
        if profile == "Pseudo-voigt": profile = "Pseudo-Voigt"
        self.convolution_combo.setCurrentText(profile)
        self._block_signals = False

    def _update_weights(self, changed_value):
        if self._block_signals:
            return
        self._block_signals = True
        total = sum(s.value() for s in self.spinboxes)
        if total > 1.0:
            sender_spinbox = self.sender()
            others_total = total - changed_value
            if others_total > 0:
                scale_factor = (1.0 - changed_value) / others_total
                for s in self.spinboxes:
                    if s is not sender_spinbox:
                        s.setValue(s.value() * scale_factor)
        final_total = sum(s.value() for s in self.spinboxes)
        if abs(final_total - 1.0) > 1e-4 and final_total > 0:
            for s in self.spinboxes:
                s.setValue(s.value() / final_total)
        self._block_signals = False
        self._update_total_label()

    def _update_total_label(self):
        total = sum(s.value() for s in self.spinboxes)
        self.total_label.setText(f"Total: {total * 100:.1f}%")
        if abs(total - 1.0) > 0.01:
            self.total_label.setStyleSheet("font-weight: bold; color: red;")
        else:
            self.total_label.setStyleSheet("font-weight: bold; color: green;")

    def get_parameters(self):
        weights = [s.value() for s in self.spinboxes]
        total = sum(weights)
        if total > 0:
            normalized_weights = [w / total for w in weights]
        else:
            normalized_weights = weights

        sim_params = {
            "profile": self.convolution_combo.currentText().lower().replace("-", ""),
            "fwhm": self.fwhm_spin.value()
        }
        return normalized_weights, sim_params

    def accept(self):
        weights, sim_params = self.get_parameters()
        if abs(sum(weights) - 1.0) > 0.01:
            QMessageBox.warning(self, "Soma Inválida", "A soma das proporções deve ser 100%. Por favor, ajuste os valores.")
            return
        self.parametersChanged.emit(self.item_id, weights, sim_params)
        super().accept()