# calculadora_esteq_pyside.py
#
# CAMINHO REFATORADO: matfinder/tools/calculator/calculadora_esteq_pyside.py
#

import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit,
    QGroupBox, QScrollArea, QWidget, QSizePolicy, QDialogButtonBox,
    QMessageBox
)
from PySide6.QtGui import QFont, QColor, QGuiApplication
from PySide6.QtCore import Qt, Signal

# --- ALTERAÇÃO DE REATORAÇÃO: Importação Relativa ---
# Como 'quimica_calc.py' está na mesma pasta 'calculator/',
# usamos um '.' para importá-lo.
try:
    from .quimica_calc import (
        parse_equation_string,
        balance_chemical_equation,
        format_balanced_equation,
        calcular_massa_molar,
        massa_para_moles,
        identificar_reagente_limitante,
        calcular_rendimento_teorico,
        moles_para_massa,
        calcular_percentagem_rendimento,
        CHEMPY_AVAILABLE
    )
except ImportError:
# --- FIM DA ALTERAÇÃO ---
    # Isso só deve acontecer se o arquivo quimica_calc.py estiver faltando.
    # Em uma aplicação real, seria melhor empacotar ou garantir a presença do arquivo.
    def _placeholder_critical_error(*args, **kwargs):
        print(f"ERRO CRÍTICO: Função de 'quimica_calc.py' não encontrada: {args}, {kwargs}")
        app = QApplication.instance()
        if app:  # Só mostra QMessageBox se a aplicação QApplication já existe
            QMessageBox.critical(None, "Erro de Importação Crítico",
                                 "O arquivo essencial 'quimica_calc.py' não foi encontrado.\n"
                                 "A calculadora não pode funcionar. Verifique a instalação.")
        # Para o caso de teste __main__ sem app ainda, apenas imprimir.
        # Em uma aplicação real, talvez queira sair ou impedir a instanciação da classe.
        return None


    parse_equation_string = _placeholder_critical_error
    balance_chemical_equation = lambda x, y: (None, None)  # Precisa retornar tupla para desempacotar
    format_balanced_equation = lambda w, x, y, z: "Erro: quimica_calc.py não carregado."
    calcular_massa_molar = _placeholder_critical_error
    massa_para_moles = _placeholder_critical_error
    identificar_reagente_limitante = _placeholder_critical_error
    calcular_rendimento_teorico = _placeholder_critical_error
    moles_para_massa = _placeholder_critical_error
    calcular_percentagem_rendimento = _placeholder_critical_error
    CHEMPY_AVAILABLE = False


class CalculadoraEstequiometricaDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calculadora Estequiométrica e de Soluções")

        self.setFixedWidth(620)
        self.setMinimumHeight(620)
        self.setMaximumHeight(620)
        self.resize(620, 780)

        # Variáveis de estado
        self.parsed_reactants_formulas = []
        self.parsed_products_formulas = []
        self.balanced_reac_coeffs = {}
        self.balanced_prod_coeffs = {}
        self.reactant_widgets = {}
        self.reagente_limitante_formula = None
        self.reagente_limitante_moles = None
        self.rt_moles_calculado = None

        self._init_ui()
        self._update_sections_state()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content_widget = QWidget()
        sections_layout = QVBoxLayout(scroll_content_widget)
        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)

        # --- 1. Seção da Equação Química ---
        self.eq_group = QGroupBox("1. Equação Química")
        self.eq_group.setCheckable(True)
        self.eq_group.setChecked(True)
        eq_layout_outer = QVBoxLayout(self.eq_group)

        self.eq_content_widget = QWidget()
        eq_layout_inner = QVBoxLayout(self.eq_content_widget)

        eq_layout_inner.addWidget(QLabel("Insira a equação (ex: CH4 + O2 -> CO2 + H2O):"))
        self.equation_entry = QLineEdit()
        self.equation_entry.setPlaceholderText("H2 + O2 -> H2O")
        self.equation_entry.returnPressed.connect(self.balancear_equacao)
        eq_layout_inner.addWidget(self.equation_entry)

        eq_buttons_layout = QHBoxLayout()
        self.balance_button = QPushButton("Balancear Equação")
        self.balance_button.clicked.connect(self.balancear_equacao)
        eq_buttons_layout.addWidget(self.balance_button)

        self.reset_button = QPushButton("Resetar Tudo")
        self.reset_button.clicked.connect(self.resetar_calculadora)
        eq_buttons_layout.addWidget(self.reset_button)

        info_button = QPushButton("!")
        info_button.setFixedSize(30, 30)
        info_button.setToolTip("Informações sobre o formato da equação")
        info_button.clicked.connect(self.mostrar_info_formatacao_equacao)
        eq_buttons_layout.addWidget(info_button)
        eq_buttons_layout.addStretch()
        eq_layout_inner.addLayout(eq_buttons_layout)

        self.balanced_equation_label = QLabel("Equação balanceada aparecerá aqui.")
        self.balanced_equation_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.balanced_equation_label.setWordWrap(True)
        eq_layout_inner.addWidget(self.balanced_equation_label)

        eq_layout_outer.addWidget(self.eq_content_widget)
        self.eq_group.toggled.connect(self.eq_content_widget.setVisible)
        sections_layout.addWidget(self.eq_group)

        # --- 2. Seção de Quantidades Iniciais dos Reagentes ---
        self.quant_group = QGroupBox("2. Quantidades Iniciais dos Reagentes")
        self.quant_group.setCheckable(True)
        self.quant_group.setChecked(False)
        quant_layout_outer = QVBoxLayout(self.quant_group)

        self.quant_content_widget = QWidget()
        quant_layout_inner = QVBoxLayout(self.quant_content_widget)

        self.quant_placeholder_label = QLabel("Balanceie uma equação para inserir as quantidades.")
        quant_layout_inner.addWidget(self.quant_placeholder_label)

        self.quant_reagents_container_widget = QWidget()
        self.quant_reagents_layout = QVBoxLayout(self.quant_reagents_container_widget)
        quant_layout_inner.addWidget(self.quant_reagents_container_widget)

        self.limitante_button = QPushButton("Identificar Reagente Limitante")
        self.limitante_button.clicked.connect(self.identificar_reagente_limitante_action)
        quant_layout_inner.addWidget(self.limitante_button, alignment=Qt.AlignmentFlag.AlignLeft)

        quant_layout_outer.addWidget(self.quant_content_widget)
        self.quant_group.toggled.connect(self.quant_content_widget.setVisible)
        sections_layout.addWidget(self.quant_group)

        # --- 3. Seção de Cálculo de Rendimento ---
        self.rend_group = QGroupBox("3. Cálculo de Rendimento")
        self.rend_group.setCheckable(True)
        self.rend_group.setChecked(False)
        rend_layout_outer = QVBoxLayout(self.rend_group)

        self.rend_main_content_widget = QWidget()
        rend_layout_inner = QVBoxLayout(self.rend_main_content_widget)

        self.rend_placeholder_label = QLabel("Defina as quantidades e identifique o reagente limitante.")
        rend_layout_inner.addWidget(self.rend_placeholder_label)

        self.rend_actual_content_widget = QWidget()
        rend_content_layout = QGridLayout(self.rend_actual_content_widget)

        rend_content_layout.addWidget(QLabel("Produto para Rendimento Teórico:"), 0, 0)
        self.produto_rt_combo = QComboBox()
        rend_content_layout.addWidget(self.produto_rt_combo, 0, 1)

        self.calc_rt_button = QPushButton("Calcular Rendimento Teórico")
        self.calc_rt_button.clicked.connect(self.calcular_rendimento_teorico_action)
        rend_content_layout.addWidget(self.calc_rt_button, 0, 2)

        rend_content_layout.addWidget(QLabel("Rendimento Real Obtido:"), 1, 0)
        self.rend_real_entry = QLineEdit()
        self.rend_real_entry.setPlaceholderText("ex: 10.5")
        rend_real_unit_layout = QHBoxLayout()
        rend_real_unit_layout.addWidget(self.rend_real_entry)
        self.rend_real_unit_combo = QComboBox()
        self.rend_real_unit_combo.addItems(["g", "mol"])
        rend_real_unit_layout.addWidget(self.rend_real_unit_combo)
        rend_content_layout.addLayout(rend_real_unit_layout, 1, 1)

        self.calc_perc_rend_button = QPushButton("Calcular % Rendimento")
        self.calc_perc_rend_button.clicked.connect(self.calcular_percentagem_rendimento_action)
        rend_content_layout.addWidget(self.calc_perc_rend_button, 1, 2)

        self.rend_actual_content_widget.setVisible(False)
        rend_layout_inner.addWidget(self.rend_actual_content_widget)

        rend_layout_outer.addWidget(self.rend_main_content_widget)
        self.rend_group.toggled.connect(self.rend_main_content_widget.setVisible)
        sections_layout.addWidget(self.rend_group)

        # --- 4. Seção de Cálculo de Molaridade ---
        self.molaridade_group = QGroupBox("4. Cálculo de Molaridade de Solução")
        self.molaridade_group.setCheckable(True)
        self.molaridade_group.setChecked(True)
        molaridade_layout_outer = QVBoxLayout(self.molaridade_group)

        self.molaridade_content_widget = QWidget()
        molaridade_layout_inner = QGridLayout(self.molaridade_content_widget)

        molaridade_layout_inner.addWidget(QLabel("Fórmula do Soluto:"), 0, 0)
        self.molaridade_formula_entry = QLineEdit()
        self.molaridade_formula_entry.setPlaceholderText("ex: NaCl")
        molaridade_layout_inner.addWidget(self.molaridade_formula_entry, 0, 1)

        molaridade_layout_inner.addWidget(QLabel("Massa Molar do Soluto (g/mol):"), 1, 0)
        self.molaridade_mm_entry = QLineEdit()
        self.molaridade_mm_entry.setPlaceholderText("ex: 58.44 (para NaCl)")
        molaridade_layout_inner.addWidget(self.molaridade_mm_entry, 1, 1)
        self.molaridade_formula_entry.editingFinished.connect(self.preencher_massa_molar_soluto)

        molaridade_layout_inner.addWidget(QLabel("Massa do Soluto (g):"), 2, 0)
        self.molaridade_massa_soluto_entry = QLineEdit()
        self.molaridade_massa_soluto_entry.setPlaceholderText("ex: 5.844")
        molaridade_layout_inner.addWidget(self.molaridade_massa_soluto_entry, 2, 1)

        molaridade_layout_inner.addWidget(QLabel("Volume da Solução:"), 3, 0)
        self.molaridade_volume_solucao_entry = QLineEdit()
        self.molaridade_volume_solucao_entry.setPlaceholderText("ex: 0.5 ou 500")
        self.molaridade_volume_unit_combo = QComboBox()
        self.molaridade_volume_unit_combo.addItems(["L", "mL"])
        molaridade_volume_layout = QHBoxLayout()
        molaridade_volume_layout.addWidget(self.molaridade_volume_solucao_entry)
        molaridade_volume_layout.addWidget(self.molaridade_volume_unit_combo)
        molaridade_layout_inner.addLayout(molaridade_volume_layout, 3, 1)

        self.molaridade_calc_button = QPushButton("Calcular Molaridade")
        self.molaridade_calc_button.clicked.connect(self.calcular_molaridade_action)
        molaridade_layout_inner.addWidget(self.molaridade_calc_button, 4, 0, 1, 2)

        self.molaridade_reset_button = QPushButton("Resetar Molaridade")
        self.molaridade_reset_button.clicked.connect(self.resetar_campos_molaridade)
        molaridade_layout_inner.addWidget(self.molaridade_reset_button, 4, 2)

        self.molaridade_resultado_label = QLabel("Molaridade (M): N/A")
        self.molaridade_resultado_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        molaridade_layout_inner.addWidget(self.molaridade_resultado_label, 5, 0, 1, 3)

        molaridade_layout_outer.addWidget(self.molaridade_content_widget)
        self.molaridade_group.toggled.connect(self.molaridade_content_widget.setVisible)
        sections_layout.addWidget(self.molaridade_group)

        # --- 5. Seção de Resultados Detalhados (Estequiometria) ---
        res_group = QGroupBox("5. Resultados Detalhados (Estequiometria)")
        res_layout = QVBoxLayout()
        self.results_text_edit = QTextEdit()
        self.results_text_edit.setReadOnly(True)
        self.results_text_edit.setFont(QFont("Courier New", 9))
        self.results_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.results_text_edit.setFixedHeight(150)
        res_layout.addWidget(self.results_text_edit)
        res_group.setLayout(res_layout)
        sections_layout.addWidget(res_group)

        sections_layout.addStretch(0)  # Não adicionar stretch aqui para o QScrollArea funcionar melhor

        # --- Botões de Ação Inferiores ---
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()

        self.copy_results_button = QPushButton("Copiar Resultados")  # <--- ALTERADO
        self.copy_results_button.setToolTip(
            "Copiar o conteúdo da caixa de resultados para a área de transferência.")  # <--- ALTERADO
        self.copy_results_button.setEnabled(False)
        self.copy_results_button.clicked.connect(self.copiar_resultados_clipboard)  # <--- ALTERADO
        action_buttons_layout.addWidget(self.copy_results_button)  # <--- ALTERADO

        self.dialog_button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.dialog_button_box.rejected.connect(self.reject)
        main_layout.addLayout(action_buttons_layout)

    def _update_sections_state(self, equation_balanced=False, limitante_identificado=False, rt_calculado=False):
        """Atualiza a visibilidade e o estado habilitado das seções e seus conteúdos."""
        # Habilita/desabilita o grupo inteiro (afeta o checkbox e o título)
        # mas não controla a visibilidade do conteúdo aqui, isso é feito pelo .toggled.connect
        self.quant_group.setEnabled(equation_balanced)
        self.rend_group.setEnabled(limitante_identificado)

        # Controla a visibilidade do placeholder vs. campos reais DENTRO do content_widget
        if equation_balanced:
            self.quant_placeholder_label.hide()
            self.quant_reagents_container_widget.show()
            self.limitante_button.setEnabled(bool(self.parsed_reactants_formulas))
        else:
            self.quant_placeholder_label.show()
            self.quant_reagents_container_widget.hide()
            self.limitante_button.setEnabled(False)

        if limitante_identificado:
            self.rend_placeholder_label.hide()
            self.rend_actual_content_widget.show()
            self.produto_rt_combo.setEnabled(True)
            self.calc_rt_button.setEnabled(True)
            self.rend_real_entry.setEnabled(rt_calculado)
            self.rend_real_unit_combo.setEnabled(rt_calculado)
            self.calc_perc_rend_button.setEnabled(rt_calculado)
        else:
            self.rend_placeholder_label.show()
            self.rend_actual_content_widget.hide()
            self.produto_rt_combo.setEnabled(False)
            self.calc_rt_button.setEnabled(False)
            self.rend_real_entry.setEnabled(False)
            self.rend_real_unit_combo.setEnabled(False)
            self.calc_perc_rend_button.setEnabled(False)

        # Habilita o botão de copiar se houver texto nos resultados
        self.copy_results_button.setEnabled(bool(self.results_text_edit.toPlainText().strip()))

    def mostrar_info_formatacao_equacao(self):
        info_text = (
            "Formato da Equação:\n"
            "- Use símbolos válidos (ex: H, O, Fe, CH4).\n"
            "- Índices após o elemento (ex: H2O, O2).\n"
            "- Separe reagentes de produtos com '->', '=' ou '=>'.\n"
            "- Separe espécies com '+'.\n"
            "- Não insira coeficientes para balanceamento.\n"
            "- Parênteses são suportados (ex: Ca(OH)2)."
        )
        QMessageBox.information(self, "Formato da Equação", info_text)

    def balancear_equacao(self):
        # Resetar estados relevantes antes de um novo balanceamento
        self.results_text_edit.clear()
        self.parsed_reactants_formulas = []
        self.parsed_products_formulas = []
        self.balanced_reac_coeffs = {}
        self.balanced_prod_coeffs = {}
        self.reagente_limitante_formula = None
        self.reagente_limitante_moles = None
        self.rt_moles_calculado = None
        self._clear_reagent_fields()
        self.produto_rt_combo.clear()
        self.rend_real_entry.clear()  # Limpa rendimento real também
        self.rend_group.setChecked(False)  # Recolhe seção de rendimento
        self.quant_group.setChecked(False)  # Recolhe seção de quantidades

        equation_str = self.equation_entry.text().strip()
        if not equation_str:
            self.balanced_equation_label.setText("<font color='red'>Por favor, insira uma equação.</font>")
            self._update_sections_state()
            return

        if not CHEMPY_AVAILABLE:
            self.balanced_equation_label.setText(
                "<font color='red'>Balanceamento indisponível (Chempy não instalado).</font>")
            # QMessageBox.warning(self, "Chempy Ausente", ...) # Já é mostrado no __main__
            self._update_sections_state()
            return

        parsed_data = parse_equation_string(equation_str)
        if not parsed_data or not parsed_data[0] or not parsed_data[1]:
            self.balanced_equation_label.setText("<font color='red'>Erro ao ler a equação. Verifique o formato.</font>")
            self._update_sections_state()
            return

        self.parsed_reactants_formulas, self.parsed_products_formulas = parsed_data

        try:
            reac_set = {str(f) for f in self.parsed_reactants_formulas}
            prod_set = {str(f) for f in self.parsed_products_formulas}
            coeffs = balance_chemical_equation(reac_set, prod_set)
        except Exception as e:
            self.balanced_equation_label.setText(f"<font color='red'>Erro no balanceamento: {e}</font>")
            self._update_sections_state()
            return

        if coeffs and coeffs[0] and coeffs[1]:
            self.balanced_reac_coeffs, self.balanced_prod_coeffs = coeffs
            formatted_eq = format_balanced_equation(
                self.parsed_reactants_formulas,
                self.parsed_products_formulas,
                self.balanced_reac_coeffs,
                self.balanced_prod_coeffs
            )
            self.balanced_equation_label.setText(f"<b>{formatted_eq}</b>")
            self.log_resultado(f"Equação Balanceada: {formatted_eq}")
            self._create_reagent_fields()
            self._populate_product_combo()
            self._update_sections_state(equation_balanced=True)
            self.quant_group.setChecked(True)
            self.rend_group.setChecked(False)  # Garante que rendimento comece recolhido
            self.molaridade_group.setChecked(False)  # Recolhe molaridade também
        else:
            self.balanced_equation_label.setText(
                "<font color='red'>Não foi possível balancear. Verifique as fórmulas.</font>")
            self._update_sections_state()

    def _clear_reagent_fields(self):
        """Limpa os campos de entrada de reagentes dinamicamente criados."""
        while self.quant_reagents_layout.count():
            item = self.quant_reagents_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                inner_layout = item.layout()
                while inner_layout.count():
                    inner_item = inner_layout.takeAt(0)
                    if inner_item.widget():
                        inner_item.widget().deleteLater()
        self.reactant_widgets = {}

    def _create_reagent_fields(self):
        """Cria campos de entrada para cada reagente na equação balanceada."""
        self._clear_reagent_fields()

        if not self.parsed_reactants_formulas:
            no_reagents_label = QLabel("Nenhum reagente explícito na equação para inserir quantidades.")
            self.quant_reagents_layout.addWidget(no_reagents_label)
            return

        for formula in self.parsed_reactants_formulas:
            h_layout = QHBoxLayout()
            label = QLabel(f"{formula}:")
            label.setFixedWidth(100)
            entry = QLineEdit()
            entry.setPlaceholderText("Quantidade")
            unit_combo = QComboBox()
            unit_combo.addItems(["g", "mol"])

            h_layout.addWidget(label)
            h_layout.addWidget(entry)
            h_layout.addWidget(unit_combo)
            self.quant_reagents_layout.addLayout(h_layout)

            self.reactant_widgets[formula] = {"entry": entry, "unit_combo": unit_combo}

    def _populate_product_combo(self):
        """Preenche o ComboBox de produtos para cálculo de rendimento."""
        self.produto_rt_combo.clear()
        if self.parsed_products_formulas:
            self.produto_rt_combo.addItems(self.parsed_products_formulas)

    def identificar_reagente_limitante_action(self):
        if not self.balanced_reac_coeffs:
            QMessageBox.warning(self, "Atenção", "Balanceie a equação primeiro.")
            return

        quantidades_moles_reagentes = {}
        pode_calcular = True
        self.reagente_limitante_formula = None  # Reseta antes de tentar calcular
        self.reagente_limitante_moles = None

        for formula, widgets in self.reactant_widgets.items():
            try:
                valor_str = widgets["entry"].text().strip()
                if not valor_str:
                    QMessageBox.warning(self, "Entrada Inválida", f"Por favor, insira uma quantidade para {formula}.")
                    pode_calcular = False
                    break
                valor = float(valor_str)
                if valor < 0:
                    QMessageBox.warning(self, "Valor Inválido", f"A quantidade de {formula} não pode ser negativa.")
                    pode_calcular = False
                    break

                unidade = widgets["unit_combo"].currentText()

                if unidade == "g":
                    massa_molar_reagente = calcular_massa_molar(formula)
                    if massa_molar_reagente is None or massa_molar_reagente <= 0:
                        self.log_resultado(f"ERRO: Massa molar inválida ou não calculada para {formula}.")
                        QMessageBox.critical(self, "Erro de Cálculo",
                                             f"Não foi possível calcular a massa molar para {formula}.")
                        pode_calcular = False
                        break
                    moles = massa_para_moles(valor, massa_molar_reagente)
                    if moles is None:
                        self.log_resultado(f"ERRO: Falha ao converter massa para moles para {formula}.")
                        QMessageBox.critical(self, "Erro de Cálculo",
                                             f"Não foi possível converter a massa de {formula} para moles.")
                        pode_calcular = False
                        break
                    quantidades_moles_reagentes[formula] = moles
                else:
                    quantidades_moles_reagentes[formula] = valor
            except ValueError:
                QMessageBox.warning(self, "Erro de Entrada", f"Valor numérico inválido inserido para {formula}.")
                pode_calcular = False
                break
            except Exception as e:
                QMessageBox.critical(self, "Erro Inesperado", f"Ocorreu um erro ao processar {formula}: {e}")
                pode_calcular = False
                break

        if not pode_calcular:
            self._update_sections_state(equation_balanced=True, limitante_identificado=False)
            return

        if not self.reactant_widgets or not quantidades_moles_reagentes:  # Verifica se há reagentes ou se as quantidades foram preenchidas
            QMessageBox.warning(self, "Sem Dados",
                                "Nenhuma quantidade de reagente válida foi inserida ou não há reagentes.")
            self._update_sections_state(equation_balanced=True, limitante_identificado=False)
            return

        self.reagente_limitante_formula = identificar_reagente_limitante(
            quantidades_moles_reagentes,
            self.balanced_reac_coeffs
        )

        if self.reagente_limitante_formula:
            self.reagente_limitante_moles = quantidades_moles_reagentes[self.reagente_limitante_formula]
            self.log_resultado(
                f"Reagente Limitante: {self.reagente_limitante_formula} ({self.reagente_limitante_moles:.4f} mol)")
            self._update_sections_state(equation_balanced=True, limitante_identificado=True)
            self.rend_group.setChecked(True)
        else:
            self.log_resultado("Não foi possível determinar o reagente limitante com os dados fornecidos.")
            self.reagente_limitante_moles = None
            self._update_sections_state(equation_balanced=True, limitante_identificado=False)

    def calcular_rendimento_teorico_action(self):
        if not self.reagente_limitante_formula or self.reagente_limitante_moles is None:
            QMessageBox.warning(self, "Atenção", "Identifique o reagente limitante primeiro.")
            return

        produto_selecionado = self.produto_rt_combo.currentText()
        if not produto_selecionado:
            QMessageBox.warning(self, "Seleção Necessária",
                                "Por favor, selecione um produto para calcular o rendimento.")
            return

        self.rt_moles_calculado = None  # Reseta antes de calcular

        rt_moles = calcular_rendimento_teorico(
            formula_produto_desejado=produto_selecionado,
            reagente_limitante_formula=self.reagente_limitante_formula,
            quantidade_reagente_limitante_moles=self.reagente_limitante_moles,
            equacao_balanceada=(self.balanced_reac_coeffs, self.balanced_prod_coeffs)
        )

        if rt_moles is not None:
            self.rt_moles_calculado = rt_moles

            massa_molar_produto = calcular_massa_molar(produto_selecionado)
            rt_gramas_str = "N/A"
            mm_produto_str = "N/A"
            if massa_molar_produto is not None and massa_molar_produto > 0:
                mm_produto_str = f"{massa_molar_produto:.4f} g/mol"
                rt_gramas = moles_para_massa(rt_moles, massa_molar_produto)
                if rt_gramas is not None:
                    rt_gramas_str = f"{rt_gramas:.4f} g"
            else:
                self.log_resultado(
                    f"AVISO: Não foi possível calcular a massa molar para o produto {produto_selecionado}.")

            self.log_resultado(f"\nRendimento Teórico para {produto_selecionado}:")
            self.log_resultado(f"  - Em moles: {rt_moles:.4f} mol")
            self.log_resultado(f"  - Em gramas: {rt_gramas_str} (MM: {mm_produto_str})")
            self._update_sections_state(equation_balanced=True, limitante_identificado=True, rt_calculado=True)
        else:
            self.log_resultado(f"\nNão foi possível calcular o rendimento teórico para {produto_selecionado}.")
            self._update_sections_state(equation_balanced=True, limitante_identificado=True, rt_calculado=False)

    def calcular_percentagem_rendimento_action(self):
        if self.rt_moles_calculado is None:
            QMessageBox.warning(self, "Atenção", "Calcule o Rendimento Teórico primeiro.")
            return

        rend_real_str = self.rend_real_entry.text().strip()
        if not rend_real_str:
            QMessageBox.warning(self, "Entrada Inválida", "Por favor, insira o Rendimento Real Obtido.")
            return

        try:
            rend_real_valor = float(rend_real_str)
            if rend_real_valor < 0:
                QMessageBox.warning(self, "Valor Inválido", "O Rendimento Real não pode ser negativo.")
                return
        except ValueError:
            QMessageBox.warning(self, "Erro de Entrada", "Valor numérico inválido para Rendimento Real.")
            return

        rend_real_unidade = self.rend_real_unit_combo.currentText()
        rend_real_moles = 0
        produto_selecionado_para_mm = self.produto_rt_combo.currentText()  # Produto para o qual RT foi calculado

        if not produto_selecionado_para_mm:
            QMessageBox.critical(self, "Erro Interno", "Produto não definido para cálculo de % de rendimento (MM).")
            return

        if rend_real_unidade == "g":
            massa_molar_produto = calcular_massa_molar(produto_selecionado_para_mm)
            if massa_molar_produto is None or massa_molar_produto <= 0:
                self.log_resultado(
                    f"ERRO: Falha ao obter MM para {produto_selecionado_para_mm} para converter rendimento real.")
                QMessageBox.critical(self, "Erro de Cálculo",
                                     f"Não foi possível obter massa molar para {produto_selecionado_para_mm} para converter rendimento real.")
                return

            moles_convertidos = massa_para_moles(rend_real_valor, massa_molar_produto)
            if moles_convertidos is None:
                self.log_resultado(
                    f"ERRO: Falha ao converter massa de {produto_selecionado_para_mm} (rend. real) para moles.")
                QMessageBox.critical(self, "Erro de Conversão",
                                     f"Não foi possível converter a massa de {produto_selecionado_para_mm} (rendimento real) para moles.")
                return
            rend_real_moles = moles_convertidos
        else:
            rend_real_moles = rend_real_valor

        # Chama a função do backend
        # Certifique-se que quimica_calc.calcular_percentagem_rendimento está correta
        percent_rend = calcular_percentagem_rendimento(rend_real_moles, self.rt_moles_calculado)

        if percent_rend is not None:
            self.log_resultado(
                f"\nPercentagem de Rendimento para {self.produto_rt_combo.currentText()}: {percent_rend:.2f}%")
            self.log_resultado(
                f"  (Rendimento Real: {rend_real_moles:.4f} mol / Rendimento Teórico: {self.rt_moles_calculado:.4f} mol)")
        else:
            self.log_resultado(
                f"\nNão foi possível calcular a percentagem de rendimento para {self.produto_rt_combo.currentText()}. Verifique os valores (RT pode ser zero).")
        # Mantém o estado, pois o cálculo foi tentado/realizado
        self._update_sections_state(equation_balanced=True, limitante_identificado=True, rt_calculado=True)

    def preencher_massa_molar_soluto(self):
        """Chamado quando a edição no campo da fórmula do soluto termina."""
        formula_soluto = self.molaridade_formula_entry.text().strip()
        if formula_soluto:
            mm = calcular_massa_molar(formula_soluto)
            if mm is not None and mm > 0:
                self.molaridade_mm_entry.setText(f"{mm:.4f}")
            else:
                self.molaridade_mm_entry.clear()
                # Opcional: notificar o usuário se o cálculo da MM falhar silenciosamente
                # self.log_resultado(f"AVISO: Não foi possível calcular MM para soluto '{formula_soluto}'.")
        else:
            self.molaridade_mm_entry.clear()

    def calcular_molaridade_action(self):
        try:
            massa_soluto_str = self.molaridade_massa_soluto_entry.text().strip()
            mm_soluto_str = self.molaridade_mm_entry.text().strip()
            volume_solucao_str = self.molaridade_volume_solucao_entry.text().strip()
            formula_soluto_str = self.molaridade_formula_entry.text().strip()  # Pega a fórmula para log

            if not all([massa_soluto_str, mm_soluto_str, volume_solucao_str]):
                QMessageBox.warning(self, "Campos Vazios", "Preencha todos os campos para calcular a molaridade.")
                return

            massa_soluto = float(massa_soluto_str)
            mm_soluto = float(mm_soluto_str)
            volume_solucao = float(volume_solucao_str)
            unidade_volume = self.molaridade_volume_unit_combo.currentText()

            if mm_soluto <= 0:
                QMessageBox.warning(self, "Valor Inválido", "A massa molar do soluto deve ser positiva.")
                return
            if massa_soluto < 0:
                QMessageBox.warning(self, "Valor Inválido", "A massa do soluto não pode ser negativa.")
                return
            if volume_solucao <= 0:
                QMessageBox.warning(self, "Valor Inválido", "O volume da solução deve ser positivo.")
                return

            if unidade_volume == "mL":
                volume_solucao_L = volume_solucao / 1000.0
            else:
                volume_solucao_L = volume_solucao

            if volume_solucao_L == 0:
                QMessageBox.warning(self, "Volume Zero",
                                    "O volume da solução não pode ser zero após conversão para litros.")
                return

            moles_soluto = massa_soluto / mm_soluto
            molaridade = moles_soluto / volume_solucao_L

            self.molaridade_resultado_label.setText(f"Molaridade (M): {molaridade:.4f} mol/L")
            self.log_resultado(f"\n--- Cálculo de Molaridade ---")
            if formula_soluto_str:
                self.log_resultado(f"  Soluto: {formula_soluto_str}")
            self.log_resultado(f"  Massa Molar: {mm_soluto:.4f} g/mol")
            self.log_resultado(f"  Massa do Soluto: {massa_soluto:.4f} g ({moles_soluto:.4f} mol)")
            self.log_resultado(f"  Volume da Solução: {volume_solucao} {unidade_volume} ({volume_solucao_L:.4f} L)")
            self.log_resultado(f"  Molaridade Calculada: {molaridade:.4f} M")
            self.log_resultado(f"----------------------------")


        except ValueError:
            QMessageBox.warning(self, "Erro de Entrada", "Verifique se todos os valores numéricos são válidos.")
            self.molaridade_resultado_label.setText("Molaridade (M): Erro")
        except Exception as e:
            QMessageBox.critical(self, "Erro Inesperado", f"Ocorreu um erro no cálculo da molaridade: {e}")
            self.molaridade_resultado_label.setText("Molaridade (M): Erro")

    def resetar_campos_molaridade(self):
        self.molaridade_formula_entry.clear()
        self.molaridade_mm_entry.clear()
        self.molaridade_massa_soluto_entry.clear()
        self.molaridade_volume_solucao_entry.clear()
        self.molaridade_volume_unit_combo.setCurrentIndex(0)
        self.molaridade_resultado_label.setText("Molaridade (M): N/A")
        # self.log_resultado("\nCampos de molaridade resetados.") # Log opcional ao resetar apenas esta seção

    def copiar_resultados_clipboard(self):  # <--- NOVO MÉTODO
        texto_resultados = self.results_text_edit.toPlainText()
        if texto_resultados.strip():
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(texto_resultados)
            self.log_resultado("\n[Resultados copiados para a área de transferência]")
            QMessageBox.information(self, "Copiado",
                                    "Os resultados detalhados foram copiados para a área de transferência.")
        else:
            QMessageBox.information(self, "Nada para Copiar", "A caixa de resultados está vazia.")

    def exportar_resultados(self):  # Mantido, mas o botão agora é de copiar
        QMessageBox.information(self, "TODO",
                                "Funcionalidade de exportar para Excel a ser implementada. Use o botão 'Copiar Resultados'.")

    def resetar_calculadora(self):
        self.equation_entry.clear()
        self.balanced_equation_label.setText("Equação balanceada aparecerá aqui.")

        self.parsed_reactants_formulas = []
        self.parsed_products_formulas = []
        self.balanced_reac_coeffs = {}
        self.balanced_prod_coeffs = {}
        self.reagente_limitante_formula = None
        self.reagente_limitante_moles = None
        self.rt_moles_calculado = None

        self._clear_reagent_fields()
        self.produto_rt_combo.clear()
        self.rend_real_entry.clear()

        # Recolher seções ao resetar tudo, exceto a primeira e a de molaridade
        self.eq_group.setChecked(True)
        self.quant_group.setChecked(False)
        self.rend_group.setChecked(False)
        self.molaridade_group.setChecked(True)

        self._update_sections_state()  # Reseta o estado dos botões e placeholders
        self.resetar_campos_molaridade()
        self.results_text_edit.clear()  # Limpa resultados por último
        self.log_resultado("Calculadora resetada.")

    def log_resultado(self, mensagem):
        self.results_text_edit.append(mensagem)
        self.copy_results_button.setEnabled(bool(self.results_text_edit.toPlainText().strip()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if not CHEMPY_AVAILABLE:  # Verifica e informa se Chempy não estiver disponível
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Componente Ausente")
        msg_box.setText("A biblioteca 'chempy' não foi encontrada.")
        msg_box.setInformativeText(
            "O balanceamento de equações químicas não funcionará.\n"
            "Para instalar, execute no seu terminal: pip install chempy sympy"
        )
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    dialog = CalculadoraEstequiometricaDialog()
    dialog.show()
    sys.exit(app.exec())