# ui_dialogs.py
# Este arquivo contém as classes de diálogo da aplicação.
# Versão com a nova AdvancedAnalysisDialog
#
# CAMINHO REFATORADO: matfinder/ui_dialogs.py
#

import logging
import os
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QCheckBox, QLineEdit,
    QDialogButtonBox, QLabel, QPushButton, QScrollArea, QWidget,
    QHBoxLayout, QTextEdit, QMessageBox, QGroupBox, QFileDialog,
    QComboBox, QStackedWidget, QSlider, QSpinBox
)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Qt, QStandardPaths, Signal, Slot
from matplotlib.backend_bases import MouseEvent

# --- Integração com Matplotlib para Gráficos ---
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- ALTERAÇÃO DE REATORAÇÃO: Importações de Módulos Locais ---
# Os caminhos foram atualizados para refletir a nova estrutura de pacotes
try:
    # Importa da nova localização da ferramenta Tabela Periódica
    from matfinder.tools.periodic_table.tabela_periodica_pyside import (
        ELEMENTOS as TABELA_PERIODICA_ELEMENTOS,
        TabelaPeriodicaDialog
    )
    # Importa da nova localização da ferramenta XRD
    # (background_correction_tools não foi fornecido, mas presumimos que esteja junto com xrd_math_tools)
    from matfinder.tools.xrd import xrd_math_tools

    # (Este import assume que background_correction_tools.py está em matfinder/tools/xrd/)
    # from matfinder.tools.xrd import background_correction_tools

    # --- Solução Provisória (se 'background_correction_tools' não existir como módulo) ---
    # Vamos assumir que as funções estão em 'xrd_math_tools' por enquanto,
    # já que não tenho o ficheiro 'background_correction_tools.py'.
    # Se ele existir, a linha acima (comentada) é a correta.
    # Esta é uma ADAPTAÇÃO:
    if hasattr(xrd_math_tools, 'calculate_background'):
        class background_correction_tools:
            calculate_background = xrd_math_tools.calculate_sonneveld_visser_background  # Exemplo
            # Ou qualquer que seja a função real:
            # calculate_background = xrd_math_tools.calculate_background
    else:
        # Fallback se a função não estiver em nenhum dos dois
        class background_correction_tools:
            @staticmethod
            def calculate_background(*args, **kwargs):
                logging.error("background_correction_tools.calculate_background não encontrado!")
                return None
    # --- Fim da Solução Provisória ---

except ImportError as e:
    logging.warning(
        f"AVISO: Um módulo local não foi encontrado em ui_dialogs.py: {e}. Algumas funcionalidades podem não funcionar.")
    TABELA_PERIODICA_ELEMENTOS = []


    class TabelaPeriodicaDialog:
        pass


    class background_correction_tools:
        @staticmethod
        def calculate_background(*args, **kwargs): return None


    class xrd_math_tools:
        pass
# --- FIM DA ALTERAÇÃO ---


MASSAS_ATOMICAS = {el["simbolo"]: el["massa"] for el in TABELA_PERIODICA_ELEMENTOS}


class ProxyConfigDialog(QDialog):
    # ... (O conteúdo desta classe permanece o mesmo)
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Proxy")
        self.setMinimumWidth(400)
        self.settings = current_settings.copy()
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.enable_proxy_checkbox = QCheckBox("Habilitar Proxy")
        self.enable_proxy_checkbox.setChecked(self.settings.get("enabled", False))
        form_layout.addRow(self.enable_proxy_checkbox)
        self.http_proxy_edit = QLineEdit(self.settings.get("http", ""))
        self.http_proxy_edit.setPlaceholderText(
            "ex: http://utilizador:senha@host:porta"
        )
        form_layout.addRow("Proxy HTTP:", self.http_proxy_edit)
        self.https_proxy_edit = QLineEdit(self.settings.get("https", ""))
        self.https_proxy_edit.setPlaceholderText(
            "ex: https://utilizador:senha@host:porta"
        )
        form_layout.addRow("Proxy HTTPS:", self.https_proxy_edit)
        info_label = QLabel(
            "Nota: As configurações são para a sessão atual.\n"
            "O proxy SOCKS não está implementado nesta versão."
        )
        info_label.setWordWrap(True)
        form_layout.addRow(info_label)
        layout.addLayout(form_layout)
        button_box = QDialogButtonBox()
        button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.enable_proxy_checkbox.stateChanged.connect(self._toggle_fields_enabled)
        self._toggle_fields_enabled()

    def _toggle_fields_enabled(self):
        enabled = self.enable_proxy_checkbox.isChecked()
        self.http_proxy_edit.setEnabled(enabled)
        self.https_proxy_edit.setEnabled(enabled)

    def get_settings(self):
        self.settings["enabled"] = self.enable_proxy_checkbox.isChecked()
        self.settings["http"] = self.http_proxy_edit.text().strip()
        self.settings["https"] = self.https_proxy_edit.text().strip()
        return self.settings


class CalculadoraProporcaoMassaDialog(QDialog):
    # ... (O conteúdo desta classe permanece o mesmo,
    # pois TabelaPeriodicaDialog já foi importada corretamente no topo)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proporção de Massa")
        self.setFixedWidth(320)
        self.setMinimumHeight(380)

        self.selected_elements_symbols = []
        self.proporcao_entries = {}

        self._init_ui()
        self._setup_connections()
        self._update_proporcao_fields()
        logging.info("Calculadora de Proporção de Massa inicializada.")

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(10)

        self.select_elements_button = QPushButton("1. Selecionar Elementos")
        outer_layout.addWidget(self.select_elements_button)

        self.selected_elements_label = QLabel("Elementos Selecionados: Nenhum")
        self.selected_elements_label.setWordWrap(True)
        self.selected_elements_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selected_elements_label.setStyleSheet(
            "padding: 5px; border: 1px solid #c5c5c5; "
            "background-color: #f0f0f0; border-radius: 3px;"
        )
        outer_layout.addWidget(self.selected_elements_label)

        proporcoes_group_label = QLabel("2. Proporções Atômicas:")
        outer_layout.addWidget(proporcoes_group_label)

        self.proporcoes_outer_scroll_area = QScrollArea()
        self.proporcoes_outer_scroll_area.setWidgetResizable(True)
        self.proporcoes_outer_scroll_area.setMinimumHeight(80)
        self.proporcoes_outer_scroll_area.setMaximumHeight(150)
        self.proporcoes_outer_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.proporcoes_outer_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.proporcoes_outer_scroll_area.setStyleSheet(
            "QScrollArea { border: 1px solid #c5c5c5; border-radius: 3px; }"
        )

        self.proporcoes_widget_container = QWidget()
        self.proporcoes_form_layout = QFormLayout(self.proporcoes_widget_container)
        self.proporcoes_form_layout.setContentsMargins(8, 8, 8, 8)
        self.proporcoes_form_layout.setSpacing(6)
        self.proporcoes_form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        self.proporcoes_outer_scroll_area.setWidget(self.proporcoes_widget_container)
        outer_layout.addWidget(self.proporcoes_outer_scroll_area)

        massa_total_layout = QHBoxLayout()
        massa_total_label = QLabel("3. Massa Total da Amostra (g):")
        massa_total_layout.addWidget(massa_total_label)
        self.massa_total_entry = QLineEdit()
        self.massa_total_entry.setValidator(QDoubleValidator(0.0001, 1000000.0, 4))
        self.massa_total_entry.setPlaceholderText("Ex: 10.0")
        massa_total_layout.addWidget(self.massa_total_entry)
        outer_layout.addLayout(massa_total_layout)

        action_buttons_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Calcular")
        action_buttons_layout.addWidget(self.calculate_button)
        self.clear_button = QPushButton("Limpar")
        action_buttons_layout.addWidget(self.clear_button)
        action_buttons_layout.addStretch()
        outer_layout.addLayout(action_buttons_layout)

        results_label = QLabel("4. Resultados (Massas Individuais):")
        outer_layout.addWidget(results_label)
        self.results_text_edit = QTextEdit()
        self.results_text_edit.setReadOnly(True)
        self.results_text_edit.setPlaceholderText(
            "As massas calculadas aparecerão aqui..."
        )
        self.results_text_edit.setFixedHeight(100)
        outer_layout.addWidget(self.results_text_edit)

        outer_layout.addStretch(1)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        outer_layout.addWidget(self.button_box)
        self.adjustSize()

    def _setup_connections(self):
        self.select_elements_button.clicked.connect(self._open_periodic_table)
        self.calculate_button.clicked.connect(self._calculate_mass_proportions)
        self.clear_button.clicked.connect(self._clear_all_fields)
        self.button_box.rejected.connect(self.reject)

    def _open_periodic_table(self):
        if not TABELA_PERIODICA_ELEMENTOS:
            QMessageBox.critical(
                self,
                "Erro de Dados",
                "Os dados dos elementos para a Tabela Periódica não foram carregados.\n"
                "A seleção de elementos não pode prosseguir.",
            )
            logging.error(
                "Dados da Tabela Periódica não carregados ao tentar abrir na Calculadora de Proporção."
            )
            return

        dialog_tabela = TabelaPeriodicaDialog(
            parent=self,
            initial_selected_elements=set(self.selected_elements_symbols),
        )
        temp_selected_elements = []

        def on_confirm(selected_list):
            nonlocal temp_selected_elements
            temp_selected_elements = selected_list

        dialog_tabela.selection_confirmed_signal.connect(on_confirm)

        if dialog_tabela.exec() == QDialog.DialogCode.Accepted:
            self._handle_elements_selected(temp_selected_elements)
        else:
            logging.info("Seleção de elementos cancelada na Calculadora de Proporção.")

    def _handle_elements_selected(self, selected_symbols_list: list):
        self.selected_elements_symbols = selected_symbols_list
        if not self.selected_elements_symbols:
            self.selected_elements_label.setText("Elementos Selecionados: Nenhum")
        else:
            sorted_symbols = sorted(
                self.selected_elements_symbols,
                key=lambda s: next(
                    (
                        el["numero"]
                        for el in TABELA_PERIODICA_ELEMENTOS
                        if el["simbolo"] == s
                    ),
                    float("inf"),
                ),
            )
            self.selected_elements_symbols = sorted_symbols
            self.selected_elements_label.setText(
                f"Elementos Selecionados: {', '.join(self.selected_elements_symbols)}"
            )
            logging.info(
                "Elementos selecionados na Calculadora de Proporção: "
                f"{self.selected_elements_symbols}"
            )
        self._update_proporcao_fields()
        self.results_text_edit.clear()
        self.adjustSize()

    def _update_proporcao_fields(self):
        while self.proporcoes_form_layout.count() > 0:
            self.proporcoes_form_layout.removeRow(0)
        self.proporcao_entries.clear()

        if not self.selected_elements_symbols:
            placeholder_label = QLabel(
                "Nenhum elemento selecionado.\nClique em 'Selecionar Elementos...'"
            )
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_label.setStyleSheet(
                "font-style: italic; color: gray; padding: 10px;"
            )
            self.proporcoes_form_layout.addRow(placeholder_label)
        else:
            for simbolo in self.selected_elements_symbols:
                massa_atomica = MASSAS_ATOMICAS.get(simbolo, 0.0)
                label_text = f"{simbolo} (MM: {massa_atomica:.3f}):"
                entry = QLineEdit()
                entry.setValidator(QDoubleValidator(0.0001, 1000.0, 4))
                entry.setPlaceholderText("Proporção (ex: 1)")
                self.proporcoes_form_layout.addRow(label_text, entry)
                self.proporcao_entries[simbolo] = entry
        self.proporcoes_widget_container.adjustSize()
        self.adjustSize()

    def _calculate_mass_proportions(self):
        logging.info("Iniciando cálculo de proporção de massa.")
        if not self.selected_elements_symbols:
            QMessageBox.warning(
                self, "Seleção Incompleta", "Por favor, selecione os elementos primeiro."
            )
            logging.warning(
                "Tentativa de cálculo de proporção de massa sem elementos selecionados."
            )
            return

        proporcoes_input = {}
        try:
            if not self.proporcao_entries and self.selected_elements_symbols:
                QMessageBox.warning(
                    self,
                    "Erro Interno",
                    "Campos de proporção não foram criados. "
                    "Tente selecionar os elementos novamente.",
                )
                logging.error(
                    "Campos de proporção não encontrados na Calculadora de Proporção."
                )
                return
            for simbolo in self.selected_elements_symbols:
                entry = self.proporcao_entries.get(simbolo)
                if not entry:
                    QMessageBox.critical(
                        self,
                        "Erro Interno",
                        f"Campo de proporção para {simbolo} não encontrado.",
                    )
                    logging.error(
                        f"Campo de proporção para {simbolo} não encontrado internamente."
                    )
                    return
                valor_str = entry.text().strip()
                if not valor_str:
                    QMessageBox.warning(
                        self,
                        "Entrada Inválida",
                        f"Por favor, insira a proporção para {simbolo}.",
                    )
                    return
                proporcao_val = float(valor_str.replace(",", "."))
                if proporcao_val <= 0:
                    QMessageBox.warning(
                        self,
                        "Valor Inválido",
                        f"A proporção para {simbolo} deve ser positiva.",
                    )
                    return
                proporcoes_input[simbolo] = proporcao_val
        except ValueError:
            QMessageBox.critical(
                self,
                "Erro de Entrada",
                "Valor numérico inválido para uma das proporções.",
            )
            logging.warning(
                "Erro de valor (ValueError) ao ler proporções na Calculadora de Proporção."
            )
            return
        except Exception as e:
            QMessageBox.critical(
                self, "Erro Inesperado", f"Erro ao processar proporções: {e}"
            )
            logging.exception(
                "Erro inesperado ao processar proporções na Calculadora de Proporção."
            )
            return

        if len(proporcoes_input) != len(self.selected_elements_symbols):
            QMessageBox.warning(
                self,
                "Entrada Incompleta",
                "Por favor, preencha todas as proporções para os elementos selecionados.",
            )
            return

        massa_total_str = self.massa_total_entry.text().strip()
        if not massa_total_str:
            QMessageBox.warning(
                self, "Entrada Inválida", "Por favor, insira a massa total da amostra."
            )
            return
        try:
            massa_total_amostra = float(massa_total_str.replace(",", "."))
            if massa_total_amostra <= 0:
                QMessageBox.warning(
                    self,
                    "Valor Inválido",
                    "A massa total da amostra deve ser positiva.",
                )
                return
        except ValueError:
            QMessageBox.critical(
                self, "Erro de Entrada", "Valor numérico inválido para a massa total."
            )
            logging.warning(
                "Valor numérico inválido (ValueError) para massa total na Calculadora de Proporção."
            )
            return

        massa_molar_composto_total = 0
        massas_atomicas_selecionadas = {}
        for simbolo in self.selected_elements_symbols:
            if simbolo not in MASSAS_ATOMICAS:
                QMessageBox.critical(
                    self,
                    "Erro de Dados",
                    f"Massa atômica para o elemento '{simbolo}' não encontrada.",
                )
                logging.error(
                    f"Massa atômica para {simbolo} não encontrada no dicionário global MASSAS_ATOMICAS."
                )
                return
            massas_atomicas_selecionadas[simbolo] = MASSAS_ATOMICAS[simbolo]
            massa_molar_composto_total += (
                    proporcoes_input[simbolo] * massas_atomicas_selecionadas[simbolo]
            )

        if massa_molar_composto_total == 0:
            QMessageBox.critical(
                self,
                "Erro de Cálculo",
                "Massa molar total do composto calculada como zero. "
                "Verifique as proporções e massas atômicas.",
            )
            logging.error(
                "Massa molar total do composto calculada como zero na Calculadora de Proporção, "
                "evitando divisão por zero."
            )
            return

        resultados_finais = []
        for simbolo in self.selected_elements_symbols:
            proporcao = proporcoes_input[simbolo]
            massa_atomica_el = massas_atomicas_selecionadas[simbolo]
            fracao_massica_elemento = (
                                              proporcao * massa_atomica_el
                                      ) / massa_molar_composto_total
            massa_do_elemento_na_amostra = (
                    fracao_massica_elemento * massa_total_amostra
            )
            resultados_finais.append(
                f"{simbolo}: {massa_do_elemento_na_amostra:.4f} g"
            )
        self.results_text_edit.setText("Resultados:\n" + "\n".join(resultados_finais))
        logging.info(
            f"Cálculo de proporção de massa concluído. Resultados: {resultados_finais}"
        )

    def _clear_all_fields(self):
        self.selected_elements_symbols = []
        self.selected_elements_label.setText("Elementos Selecionados: Nenhum")
        self._update_proporcao_fields()
        self.massa_total_entry.clear()
        self.results_text_edit.clear()
        self.adjustSize()
        logging.info("Campos da Calculadora de Proporção de Massa limpos.")


class BackgroundCorrectionDialog(QDialog):
    """
    Dialog profissional para remoção de background em dados XRD.
    Implementa os 3 melhores métodos: SNIP (recomendado), arPLS e Polynomial.
    """
    correction_applied = Signal(np.ndarray)

    def __init__(self, x_data, y_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Remoção de Background - PhaseDRX")
        self.setMinimumSize(1000, 700)

        # Import do módulo de background
        try:
            import sys
            import os
            # Tentar import relativo primeiro
            try:
                from matfinder.tools.xrd import background_removal
                self.bg_module = background_removal
            except:
                # Tentar import absoluto
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from tools.xrd import background_removal
                self.bg_module = background_removal
        except Exception as e:
            logging.error(f"Erro ao importar background_removal: {e}")
            QMessageBox.critical(self, "Erro",
                               f"Não foi possível carregar o módulo de remoção de background:\n{e}")
            self.bg_module = None

        self.x_data = np.array(x_data)
        self.y_data = np.array(y_data)
        self.current_background = np.zeros_like(self.y_data)
        self.manual_points_x = []  # Para métodos manuais

        self._init_ui()
        self._setup_connections()
        self._update_plot()

    def _init_ui(self):
        """Inicializa a interface do usuário."""
        main_layout = QVBoxLayout(self)

        # Gráfico
        self.plot_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        self.axes = self.plot_canvas.figure.add_subplot(111)
        main_layout.addWidget(self.plot_canvas)

        # Controles
        controls_group = QGroupBox("Configurações de Remoção de Background")
        controls_layout = QVBoxLayout(controls_group)

        # Seleção de método
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("<b>Método:</b>"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "SNIP (Automático)",
            "arPLS (Automático)",
            "Polynomial (Manual)"
        ])
        method_layout.addWidget(self.method_combo)
        method_layout.addStretch()
        controls_layout.addLayout(method_layout)

        # Stack de parâmetros para cada método
        self.params_stack = QStackedWidget()

        # === MÉTODO 1: SNIP ===
        snip_widget = QWidget()
        snip_layout = QFormLayout(snip_widget)

        self.snip_iterations_slider = QSlider(Qt.Orientation.Horizontal)
        self.snip_iterations_slider.setRange(10, 100)
        self.snip_iterations_slider.setValue(40)
        self.snip_iterations_spin = QSpinBox()
        self.snip_iterations_spin.setRange(10, 100)
        self.snip_iterations_spin.setValue(40)
        snip_iter_widget = self._create_slider_spinbox(self.snip_iterations_slider, self.snip_iterations_spin)
        snip_layout.addRow("Iterações:", snip_iter_widget)
        snip_layout.addRow(QLabel("<i>Mais iterações = background mais baixo (20-60 típico)</i>"))

        self.snip_smooth_check = QCheckBox("Aplicar suavização (recomendado para dados ruidosos)")
        snip_layout.addRow(self.snip_smooth_check)

        self.params_stack.addWidget(snip_widget)

        # === MÉTODO 2: arPLS ===
        arpls_widget = QWidget()
        arpls_layout = QFormLayout(arpls_widget)

        self.arpls_lam_slider = QSlider(Qt.Orientation.Horizontal)
        self.arpls_lam_slider.setRange(30, 90)  # 10^3 a 10^9
        self.arpls_lam_slider.setValue(60)  # 10^6
        self.arpls_lam_label = QLabel()
        arpls_lam_widget = self._create_slider_label(self.arpls_lam_slider, self.arpls_lam_label,
                                                     lambda v: f"10^{v/10:.1f} = {10**(v/10):.1e}")
        arpls_layout.addRow("Suavidade (λ):", arpls_lam_widget)
        arpls_layout.addRow(QLabel("<i>Valores maiores = background mais suave</i>"))

        self.params_stack.addWidget(arpls_widget)

        # === MÉTODO 3: Polynomial ===
        poly_widget = QWidget()
        poly_layout = QVBoxLayout(poly_widget)

        poly_degree_layout = QFormLayout()
        self.poly_degree_spin = QSpinBox()
        self.poly_degree_spin.setRange(2, 6)
        self.poly_degree_spin.setValue(3)
        poly_degree_layout.addRow("Grau do Polinômio:", self.poly_degree_spin)
        poly_layout.addLayout(poly_degree_layout)

        poly_instructions = QLabel(
            "<b>Como usar:</b><br>"
            "1. Clique no gráfico em <b>regiões de background</b> (sem picos)<br>"
            "2. Continue clicando para adicionar mais pontos<br>"
            "3. Mínimo de pontos necessários = Grau + 1<br>"
            "4. Clique em 'Limpar Pontos' para recomeçar"
        )
        poly_instructions.setWordWrap(True)
        poly_layout.addWidget(poly_instructions)

        poly_buttons_layout = QHBoxLayout()
        self.poly_clear_button = QPushButton("Limpar Pontos")
        self.poly_points_label = QLabel("Pontos selecionados: 0")
        poly_buttons_layout.addWidget(self.poly_clear_button)
        poly_buttons_layout.addWidget(self.poly_points_label)
        poly_buttons_layout.addStretch()
        poly_layout.addLayout(poly_buttons_layout)

        self.params_stack.addWidget(poly_widget)

        controls_layout.addWidget(self.params_stack)

        # Opções de visualização
        viz_group = QGroupBox("Visualização")
        viz_layout = QVBoxLayout(viz_group)

        self.show_result_check = QCheckBox("Mostrar resultado da subtração (verde)")
        self.show_result_check.setChecked(True)
        viz_layout.addWidget(self.show_result_check)

        self.show_background_check = QCheckBox("Mostrar background estimado (vermelho)")
        self.show_background_check.setChecked(True)
        viz_layout.addWidget(self.show_background_check)

        controls_layout.addWidget(viz_group)
        main_layout.addWidget(controls_group)

        # Botões
        self.button_box = QDialogButtonBox()
        self.button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).setText("Aplicar")
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("OK")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        main_layout.addWidget(self.button_box)

    def _create_slider_spinbox(self, slider, spinbox):
        """Cria widget com slider e spinbox sincronizados."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(slider)
        layout.addWidget(spinbox)

        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)

        return widget

    def _create_slider_label(self, slider, label, format_func):
        """Cria widget com slider e label."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(slider)
        layout.addWidget(label)

        def update_label(val):
            label.setText(format_func(val))

        slider.valueChanged.connect(update_label)
        update_label(slider.value())

        return widget

    def _setup_connections(self):
        """Configura conexões de sinais."""
        self.method_combo.currentIndexChanged.connect(self.params_stack.setCurrentIndex)
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)

        # SNIP
        self.snip_iterations_slider.valueChanged.connect(self._update_plot)
        self.snip_smooth_check.stateChanged.connect(self._update_plot)

        # arPLS
        self.arpls_lam_slider.valueChanged.connect(self._update_plot)

        # Polynomial
        self.poly_degree_spin.valueChanged.connect(self._update_plot)
        self.poly_clear_button.clicked.connect(self._clear_manual_points)

        # Visualização
        self.show_result_check.stateChanged.connect(self._update_plot)
        self.show_background_check.stateChanged.connect(self._update_plot)

        # Botões
        self.button_box.clicked.connect(self._handle_button_click)

        # Clique no gráfico (para modo manual)
        self.plot_canvas.mpl_connect('button_press_event', self._on_canvas_click)

    def _on_method_changed(self):
        """Chamado quando o método é alterado."""
        method_idx = self.method_combo.currentIndex()

        if method_idx == 2:  # Polynomial (manual)
            self.manual_points_x = []
            self.poly_points_label.setText("Pontos selecionados: 0")

        self._update_plot()

    def _on_canvas_click(self, event: MouseEvent):
        """Manipula cliques no gráfico (para seleção de pontos manuais)."""
        if self.method_combo.currentIndex() != 2:  # Só para Polynomial
            return

        if event.inaxes != self.axes:
            return

        if event.button == 1:  # Clique esquerdo
            x_clicked = event.xdata
            self.manual_points_x.append(x_clicked)
            self.poly_points_label.setText(f"Pontos selecionados: {len(self.manual_points_x)}")
            self._update_plot()

    def _clear_manual_points(self):
        """Limpa pontos manuais selecionados."""
        self.manual_points_x = []
        self.poly_points_label.setText("Pontos selecionados: 0")
        self._update_plot()

    @Slot()
    def _update_plot(self):
        """Atualiza o gráfico com o background calculado."""
        if self.bg_module is None:
            self.axes.clear()
            self.axes.text(0.5, 0.5, "Módulo de background não carregado",
                          ha='center', va='center', transform=self.axes.transAxes, color='red')
            self.plot_canvas.draw()
            return

        method_idx = self.method_combo.currentIndex()

        # Calcular background baseado no método
        try:
            if method_idx == 0:  # SNIP
                iterations = self.snip_iterations_spin.value()
                smooth = self.snip_smooth_check.isChecked()
                self.current_background = self.bg_module.calculate_background(
                    self.x_data, self.y_data, 'snip',
                    {'iterations': iterations, 'smooth': smooth}
                )

            elif method_idx == 1:  # arPLS
                lam_value = 10 ** (self.arpls_lam_slider.value() / 10.0)
                self.current_background = self.bg_module.calculate_background(
                    self.x_data, self.y_data, 'arpls',
                    {'lam': lam_value}
                )

            elif method_idx == 2:  # Polynomial
                degree = self.poly_degree_spin.value()
                if len(self.manual_points_x) < degree + 1:
                    self.current_background = np.zeros_like(self.y_data)
                else:
                    self.current_background = self.bg_module.calculate_background(
                        self.x_data, self.y_data, 'polynomial',
                        {'points_x': self.manual_points_x, 'degree': degree}
                    )

        except Exception as e:
            logging.error(f"Erro ao calcular background: {e}")
            self.current_background = np.zeros_like(self.y_data)

        # Plotar
        self.axes.clear()

        # Dados originais
        self.axes.plot(self.x_data, self.y_data, label="Dados Originais",
                      color='#1f77b4', alpha=0.7, linewidth=1.5)

        # Background
        if self.show_background_check.isChecked():
            self.axes.plot(self.x_data, self.current_background,
                          label="Background Estimado",
                          color='#d62728', linestyle='--', linewidth=2)

        # Resultado corrigido
        if self.show_result_check.isChecked() and np.any(self.current_background > 0):
            corrected = self.y_data - self.current_background
            self.axes.plot(self.x_data, corrected,
                          label="Dados Corrigidos",
                          color='#2ca02c', linewidth=1.5, alpha=0.8)

        # Pontos manuais (se modo polynomial)
        if method_idx == 2 and len(self.manual_points_x) > 0:
            for px in self.manual_points_x:
                idx = np.argmin(np.abs(self.x_data - px))
                py = self.y_data[idx]
                self.axes.plot(px, py, 'ro', markersize=8,
                              markeredgecolor='darkred', markeredgewidth=1.5)

        self.axes.set_xlabel("2θ (Graus)", fontsize=11, fontweight='bold')
        self.axes.set_ylabel("Intensidade (Unid. arb.)", fontsize=11, fontweight='bold')
        self.axes.legend(loc='best', framealpha=0.9)
        self.axes.grid(True, linestyle=':', alpha=0.4)
        self.plot_canvas.figure.tight_layout()
        self.plot_canvas.draw()

    def _apply_correction(self):
        """Emite sinal com dados corrigidos."""
        if np.any(self.current_background > 0):
            corrected_y = self.y_data - self.current_background
            corrected_y = np.maximum(corrected_y, 0)  # Sem valores negativos
            self.correction_applied.emit(corrected_y)
            logging.info("Background removido e dados corrigidos aplicados")
        else:
            QMessageBox.warning(self, "Aviso",
                              "Nenhum background foi calculado ainda.")

    @Slot()
    def _handle_button_click(self, button):
        """Manipula cliques nos botões."""
        role = self.button_box.buttonRole(button)

        if role == QDialogButtonBox.ButtonRole.AcceptRole:  # OK
            self._apply_correction()
            self.accept()
        elif role == QDialogButtonBox.ButtonRole.ApplyRole:  # Apply
            self._apply_correction()
        elif role == QDialogButtonBox.ButtonRole.RejectRole:  # Cancel
            self.reject()


class PhaseDRXProjectDialog(QDialog):
    # ... (O conteúdo desta classe permanece o mesmo)
    ANONYMOUS_SESSION = 0
    NEW_PROJECT = 1
    OPEN_PROJECT = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bem-vindo ao PhaseDRX")
        self.setMinimumWidth(450)
        self.choice = self.ANONYMOUS_SESSION
        self.project_name = ""
        self.project_base_path = ""
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        new_project_group = QGroupBox("Novo Projeto")
        new_project_layout = QFormLayout(new_project_group)
        new_project_layout.setSpacing(10)
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("Ex: Analise_Amostra_X")
        new_project_layout.addRow("Nome do Projeto:", self.project_name_edit)
        path_layout = QHBoxLayout()
        self.project_path_edit = QLineEdit()
        self.project_path_edit.setReadOnly(True)
        default_docs_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        self.project_path_edit.setText(default_docs_path)
        browse_button = QPushButton("Procurar...")
        browse_button.clicked.connect(self._browse_project_path)
        path_layout.addWidget(self.project_path_edit)
        path_layout.addWidget(browse_button)
        new_project_layout.addRow("Salvar em:", path_layout)
        create_button = QPushButton("Criar Novo Projeto")
        create_button.setStyleSheet("font-weight: bold; padding: 5px;")
        create_button.clicked.connect(self._on_create_clicked)
        new_project_layout.addRow(create_button)
        main_layout.addWidget(new_project_group)
        other_options_layout = QHBoxLayout()
        open_button = QPushButton("Abrir Projeto Existente...")
        open_button.clicked.connect(self._on_open_clicked)
        anonymous_button = QPushButton("Continuar em Sessão Anônima")
        anonymous_button.clicked.connect(self._on_anonymous_clicked)
        other_options_layout.addWidget(open_button)
        other_options_layout.addWidget(anonymous_button)
        main_layout.addLayout(other_options_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box, 0, Qt.AlignmentFlag.AlignRight)

    def _browse_project_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Pasta Base para o Projeto",
                                                     self.project_path_edit.text())
        if directory:
            self.project_path_edit.setText(directory)

    def _on_create_clicked(self):
        name = self.project_name_edit.text().strip()
        path = self.project_path_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Nome Inválido", "Por favor, insira um nome para o projeto.")
            return
        invalid_chars = r'[\\/:"*?<>|]'
        if any(c in invalid_chars for c in name):
            QMessageBox.warning(self, "Nome Inválido",
                                "O nome do projeto não pode conter os seguintes caracteres:\n"
                                f'\\ / : * ? " < > |')
            return
        if not path or not os.path.isdir(path):
            QMessageBox.warning(self, "Caminho Inválido",
                                "Por favor, selecione uma pasta válida para salvar o projeto.")
            return
        self.choice = self.NEW_PROJECT
        self.project_name = name
        self.project_base_path = path
        self.accept()

    def _on_open_clicked(self):
        self.choice = self.OPEN_PROJECT
        self.accept()

    def _on_anonymous_clicked(self):
        self.choice = self.ANONYMOUS_SESSION
        self.accept()


class GplLicenseDialog(QDialog):
    def __init__(self, license_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Licença - GNU GPL v3")
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setMinimumSize(700, 500)
        self.setMaximumSize(900, 650)
        layout = QVBoxLayout(self)

        self.text_browser = QTextEdit()
        self.text_browser.setReadOnly(True)
        self.text_browser.setAcceptRichText(True)
        self.set_license_text(license_text)
        self.text_browser.setStyleSheet(
            "QTextEdit { font-family: 'Segoe UI'; font-size: 11pt; }"
        )
        layout.addWidget(self.text_browser, 1)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def set_license_text(self, license_text: str):
        safe_text = (
            license_text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        html = (
            "<pre style='text-align: justify; white-space: pre-wrap; font-family: \"Segoe UI\";'>"
            f"{safe_text}"
            "</pre>"
        )
        self.text_browser.setHtml(html)
