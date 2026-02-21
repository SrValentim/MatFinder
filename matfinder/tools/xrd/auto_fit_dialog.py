# auto_fit_dialog.py
# Diálogo de Auto-Ajuste de parâmetros de rede
#
# Interface para o módulo auto_fit.py que permite ao usuário:
# 1. Selecionar um experimental de referência
# 2. Visualizar picos detectados e adicionar/remover manualmente
# 3. Ajustar sensibilidade da detecção
# 4. Executar o ajuste e avaliar resultados (antes/depois)
# 5. Aceitar ou rejeitar o ajuste
#
# Parte do projeto MatFinder - Copyright (C) 2025 Raynner Valentim (UFAM)

import logging
import numpy as np

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QSlider, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QAbstractItemView, QSplitter, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .auto_fit import (
    auto_fit_lattice, detect_experimental_peaks,
    get_real_reflections_from_structure,
    calc_d_spacing, two_theta_from_d
)

logger = logging.getLogger(__name__)


class AutoFitDialog(QDialog):
    """
    Diálogo de auto-ajuste de parâmetros de rede.

    Fluxo:
    1. Mostra o difratograma com picos detectados automaticamente
    2. Usuário ajusta detecção ou adiciona/remove picos manualmente
    3. Clica "Ajustar" → algoritmo roda
    4. Mostra resultado com comparação antes/depois
    5. Aceita ou rejeita
    """
    parametersAccepted = Signal(dict)  # Emite os novos parâmetros quando aceito

    def __init__(self, cif_handler, experimental_data, wavelength=1.5406,
                 max_2theta=100.0, parent=None):
        """
        Args:
            cif_handler: Instância de CifHandler com o CIF carregado
            experimental_data: Tupla (two_theta_array, intensity_array)
            wavelength: Comprimento de onda em Angstroms
            max_2theta: 2θ máximo
            parent: Widget pai
        """
        super().__init__(parent)
        self.setWindowTitle("Auto-Ajuste de Parametros de Rede")
        self.setMinimumSize(950, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)

        self.cif_handler = cif_handler
        self.exp_2theta = experimental_data[0]
        self.exp_intensity = experimental_data[1]
        self.wavelength = wavelength
        self.max_2theta = max_2theta

        # Estado
        self.detected_peaks = []
        self.fit_result = None
        self._adding_peak_mode = False

        # Reflexões reais do XRDCalculator (calculadas uma vez)
        self._real_reflections = []
        self._load_real_reflections()

        self._init_ui()
        self._detect_peaks()
        self._update_plot()

    def _load_real_reflections(self):
        """Carrega reflexões reais do CIF usando XRDCalculator."""
        try:
            self._real_reflections = get_real_reflections_from_structure(
                self.cif_handler, self.wavelength,
                max_2theta=self.max_2theta, min_intensity_pct=0.5
            )
            logger.info(f"AutoFit: {len(self._real_reflections)} reflexoes reais carregadas")
        except Exception as e:
            logger.warning(f"AutoFit: Falha ao carregar reflexoes reais: {e}")
            self._real_reflections = []

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Splitter principal ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === PAINEL ESQUERDO: Gráfico ===
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(5, 5, 5, 5)

        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.figure.set_facecolor('white')
        self.figure.subplots_adjust(left=0.08, right=0.97, top=0.95, bottom=0.12)
        plot_layout.addWidget(self.canvas)

        # Conectar clique no gráfico para adicionar pico
        self.canvas.mpl_connect('button_press_event', self._on_plot_click)

        splitter.addWidget(plot_widget)

        # === PAINEL DIREITO: Controles ===
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        # --- Detecção ---
        detect_group = QGroupBox("Detecao de Picos")
        detect_layout = QVBoxLayout(detect_group)

        # Sensibilidade
        sens_layout = QHBoxLayout()
        sens_layout.addWidget(QLabel("Sensibilidade:"))
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 20)
        self.sensitivity_slider.setValue(5)
        self.sensitivity_slider.setToolTip(
            "Baixo = menos picos (apenas os maiores)\nAlto = mais picos (inclui menores)")
        sens_layout.addWidget(self.sensitivity_slider)
        self.sensitivity_label = QLabel("5")
        self.sensitivity_label.setMinimumWidth(25)
        sens_layout.addWidget(self.sensitivity_label)
        detect_layout.addLayout(sens_layout)

        # Distância mínima entre picos
        dist_layout = QHBoxLayout()
        dist_layout.addWidget(QLabel("Dist. min (°):"))
        self.min_dist_spin = QDoubleSpinBox()
        self.min_dist_spin.setRange(0.05, 5.0)
        self.min_dist_spin.setValue(0.3)
        self.min_dist_spin.setDecimals(2)
        self.min_dist_spin.setSingleStep(0.05)
        dist_layout.addWidget(self.min_dist_spin)
        detect_layout.addLayout(dist_layout)

        # Botões de detecção
        detect_btn_layout = QHBoxLayout()
        self.redetect_btn = QPushButton("Detectar")
        self.redetect_btn.clicked.connect(self._detect_peaks)
        detect_btn_layout.addWidget(self.redetect_btn)

        self.add_peak_btn = QPushButton("Adicionar")
        self.add_peak_btn.setCheckable(True)
        self.add_peak_btn.setToolTip("Clique no grafico para adicionar um pico manualmente")
        self.add_peak_btn.toggled.connect(self._toggle_add_peak_mode)
        detect_btn_layout.addWidget(self.add_peak_btn)

        self.remove_peak_btn = QPushButton("Remover")
        self.remove_peak_btn.setToolTip("Remove os picos selecionados da tabela")
        self.remove_peak_btn.clicked.connect(self._remove_selected_peaks)
        detect_btn_layout.addWidget(self.remove_peak_btn)
        detect_layout.addLayout(detect_btn_layout)

        self.peaks_count_label = QLabel("0 picos detectados")
        self.peaks_count_label.setStyleSheet("color: gray; font-style: italic;")
        detect_layout.addWidget(self.peaks_count_label)

        controls_layout.addWidget(detect_group)

        # --- Tabela de Picos ---
        peaks_group = QGroupBox("Picos Selecionados")
        peaks_layout = QVBoxLayout(peaks_group)
        self.peaks_table = QTableWidget()
        self.peaks_table.setColumnCount(3)
        self.peaks_table.setHorizontalHeaderLabels(["2θ (°)", "Intensidade", ""])
        self.peaks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.peaks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.peaks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.peaks_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.peaks_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.peaks_table.setMaximumHeight(200)
        peaks_layout.addWidget(self.peaks_table)
        controls_layout.addWidget(peaks_group)

        # --- Configuração do Ajuste ---
        fit_group = QGroupBox("Ajuste")
        fit_layout = QVBoxLayout(fit_group)

        var_layout = QHBoxLayout()
        var_layout.addWidget(QLabel("Variacao max (%):"))
        self.max_var_spin = QDoubleSpinBox()
        self.max_var_spin.setRange(0.5, 20.0)
        self.max_var_spin.setValue(5.0)
        self.max_var_spin.setDecimals(1)
        self.max_var_spin.setSingleStep(0.5)
        self.max_var_spin.setToolTip(
            "Variacao maxima permitida para cada parametro de rede.\n"
            "Valores menores = ajuste mais conservador.\n"
            "Recomendado: 3-5% para ajuste fino.")
        var_layout.addWidget(self.max_var_spin)
        fit_layout.addLayout(var_layout)

        self.fit_btn = QPushButton("Ajustar")
        self.fit_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #45a049; }")
        self.fit_btn.clicked.connect(self._run_fit)
        fit_layout.addWidget(self.fit_btn)

        controls_layout.addWidget(fit_group)

        # --- Resultados ---
        result_group = QGroupBox("Resultado")
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["Param", "Antes", "Depois", "Var (%)"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.setMaximumHeight(200)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        result_layout.addWidget(self.result_table)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("padding: 4px;")
        result_layout.addWidget(self.result_label)

        controls_layout.addWidget(result_group)

        controls_layout.addStretch()

        # --- Botões finais ---
        btn_layout = QHBoxLayout()
        self.accept_btn = QPushButton("Aceitar")
        self.accept_btn.setEnabled(False)
        self.accept_btn.clicked.connect(self._accept_result)
        btn_layout.addWidget(self.accept_btn)

        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        controls_layout.addLayout(btn_layout)

        controls_widget.setMaximumWidth(360)
        splitter.addWidget(controls_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Conectar slider
        self.sensitivity_slider.valueChanged.connect(self._on_sensitivity_changed)

    def _on_sensitivity_changed(self, value):
        self.sensitivity_label.setText(str(value))

    def _detect_peaks(self):
        """Detecta picos no experimental com os parâmetros atuais."""
        sensitivity = self.sensitivity_slider.value()

        # Mapear sensibilidade (1-20) para prominence_factor (0.20 - 0.01)
        prominence = 0.20 - (sensitivity - 1) * (0.19 / 19.0)
        min_dist = self.min_dist_spin.value()

        self.detected_peaks = detect_experimental_peaks(
            self.exp_2theta, self.exp_intensity,
            prominence_factor=prominence,
            min_distance_deg=min_dist,
            min_intensity_pct=1.0
        )

        self._update_peaks_table()
        self._update_plot()

    def _update_peaks_table(self):
        """Atualiza a tabela de picos."""
        self.peaks_table.setRowCount(len(self.detected_peaks))

        for i, peak in enumerate(self.detected_peaks):
            tt_item = QTableWidgetItem(f"{peak['two_theta']:.4f}")
            tt_item.setFlags(tt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.peaks_table.setItem(i, 0, tt_item)

            int_item = QTableWidgetItem(f"{peak['intensity']:.1f}")
            int_item.setFlags(int_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.peaks_table.setItem(i, 1, int_item)

            # Coluna de status (vazia por agora, preenchida após ajuste)
            status_item = QTableWidgetItem("")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.peaks_table.setItem(i, 2, status_item)

        self.peaks_count_label.setText(f"{len(self.detected_peaks)} picos detectados")

    def _toggle_add_peak_mode(self, checked):
        """Alterna modo de adição manual de pico."""
        self._adding_peak_mode = checked
        if checked:
            self.add_peak_btn.setStyleSheet(
                "QPushButton { background-color: #ff9800; color: white; font-weight: bold; }")
            self.canvas.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.add_peak_btn.setStyleSheet("")
            self.canvas.setCursor(Qt.CursorShape.ArrowCursor)

    def _on_plot_click(self, event):
        """Callback para clique no gráfico — adiciona pico manualmente."""
        if not self._adding_peak_mode:
            return
        if event.inaxes != self.ax:
            return
        if event.button != 1:  # Apenas botão esquerdo
            return

        click_2theta = event.xdata

        # Encontrar o ponto mais próximo no experimental
        idx = np.argmin(np.abs(self.exp_2theta - click_2theta))
        actual_2theta = float(self.exp_2theta[idx])
        actual_intensity = float(self.exp_intensity[idx])

        # Verificar se já existe um pico próximo
        for peak in self.detected_peaks:
            if abs(peak['two_theta'] - actual_2theta) < 0.1:
                return  # Pico já existe

        # Adicionar pico
        self.detected_peaks.append({
            'two_theta': actual_2theta,
            'intensity': actual_intensity,
            'index': int(idx)
        })

        # Reordenar por intensidade
        self.detected_peaks.sort(key=lambda p: p['intensity'], reverse=True)

        self._update_peaks_table()
        self._update_plot()

        # Desativar modo de adição após clique
        self.add_peak_btn.setChecked(False)

    def _remove_selected_peaks(self):
        """Remove picos selecionados na tabela."""
        selected_rows = set()
        for item in self.peaks_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            return

        # Remover de trás para frente
        for row in sorted(selected_rows, reverse=True):
            if 0 <= row < len(self.detected_peaks):
                del self.detected_peaks[row]

        self._update_peaks_table()
        self._update_plot()

    def _update_plot(self):
        """Atualiza o gráfico com experimental + picos + reflexões reais."""
        self.ax.clear()

        # Normalizar intensidade experimental para visualização
        y_max = float(np.max(self.exp_intensity)) if len(self.exp_intensity) > 0 else 1.0

        # Plotar experimental
        self.ax.plot(self.exp_2theta, self.exp_intensity, 'b-', linewidth=0.8,
                     alpha=0.7, label='Experimental')

        # Plotar picos detectados
        if self.detected_peaks:
            peak_x = [p['two_theta'] for p in self.detected_peaks]
            peak_y = [p['intensity'] for p in self.detected_peaks]
            self.ax.plot(peak_x, peak_y, 'rv', markersize=8, label='Picos selecionados')

        # Plotar reflexões REAIS do CIF (barras proporcionais à intensidade)
        if self._real_reflections:
            max_ref_int = max(r['intensity'] for r in self._real_reflections)
            if max_ref_int > 0:
                for ref in self._real_reflections:
                    bar_height = (ref['intensity'] / max_ref_int) * y_max * 0.3
                    self.ax.plot([ref['two_theta'], ref['two_theta']], [0, bar_height],
                                color='green', alpha=0.6, linewidth=1.0)
                self.ax.plot([], [], 'g-', alpha=0.6, linewidth=1.0, label='Reflexoes CIF')

        # Plotar resultado se disponível (reflexões ajustadas)
        if self.fit_result and self.fit_result.get('success'):
            p = self.fit_result['params_after']
            cs = self.cif_handler.get_crystal_system()
            max_ref_int = max(r['intensity'] for r in self._real_reflections) if self._real_reflections else 100.0

            for ref in self._real_reflections:
                if ref.get('hkl') is None:
                    continue
                h, k, l = ref['hkl']
                d = calc_d_spacing(h, k, l, cs, p['a'], p['b'], p['c'],
                                   p['alpha'], p['beta'], p['gamma'])
                tt = two_theta_from_d(d, self.wavelength)
                if tt is not None and 0 < tt <= self.max_2theta:
                    bar_height = (ref['intensity'] / max_ref_int) * y_max * 0.3
                    self.ax.plot([tt, tt], [0, bar_height],
                                color='red', alpha=0.6, linewidth=1.2)

            self.ax.plot([], [], 'r-', alpha=0.6, linewidth=1.2, label='Reflexoes ajustadas')

        self.ax.set_xlabel('2\u03b8 (\u00b0)', fontsize=12)
        self.ax.set_ylabel('Intensidade', fontsize=12)
        self.ax.legend(fontsize=8, loc='upper right')

        x_min = int(np.min(self.exp_2theta)) if len(self.exp_2theta) > 0 else 0
        x_max = int(np.max(self.exp_2theta)) + 1 if len(self.exp_2theta) > 0 else 100
        self.ax.set_xlim(x_min, x_max)

        self.canvas.draw_idle()

    def _run_fit(self):
        """Executa o auto-ajuste."""
        if not self.detected_peaks:
            QMessageBox.warning(self, "Sem Picos",
                                "Detecte ou adicione pelo menos 3 picos para o ajuste.")
            return

        if len(self.detected_peaks) < 3:
            QMessageBox.warning(self, "Poucos Picos",
                                "Recomenda-se pelo menos 3 picos para um ajuste confiavel.\n"
                                "Adicione mais picos ou aumente a sensibilidade.")
            return

        params = self.cif_handler.get_lattice_params()
        cs = self.cif_handler.get_crystal_system()

        try:
            self.fit_result = auto_fit_lattice(
                crystal_system=cs,
                a=params['a'], b=params['b'], c=params['c'],
                alpha=params['alpha'], beta=params['beta'], gamma=params['gamma'],
                wavelength=self.wavelength,
                obs_peaks=self.detected_peaks,
                max_variation_pct=self.max_var_spin.value(),
                max_2theta=self.max_2theta,
                cif_handler=self.cif_handler
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro no Ajuste",
                                 f"Ocorreu um erro durante o ajuste:\n{e}")
            logger.error(f"Erro no auto-ajuste: {e}", exc_info=True)
            return

        self._show_result()
        self._update_residuals_in_table()
        self._update_plot()

    def _show_result(self):
        """Mostra os resultados do ajuste na tabela e label."""
        if not self.fit_result:
            return

        r = self.fit_result
        before = r['params_before']
        after = r['params_after']
        changes = r['param_changes']

        # Preencher tabela de resultados
        params_to_show = ['a', 'b', 'c', 'alpha', 'beta', 'gamma', 'volume']
        param_labels = {
            'a': 'a (A)', 'b': 'b (A)', 'c': 'c (A)',
            'alpha': 'α (°)', 'beta': 'β (°)', 'gamma': 'γ (°)',
            'volume': 'V (A³)'
        }
        units_fmt = {
            'a': '.5f', 'b': '.5f', 'c': '.5f',
            'alpha': '.3f', 'beta': '.3f', 'gamma': '.3f',
            'volume': '.3f'
        }

        self.result_table.setRowCount(len(params_to_show))

        for i, key in enumerate(params_to_show):
            # Nome
            name_item = QTableWidgetItem(param_labels.get(key, key))
            self.result_table.setItem(i, 0, name_item)

            # Antes
            fmt = units_fmt.get(key, '.4f')
            before_item = QTableWidgetItem(f"{before[key]:{fmt}}")
            self.result_table.setItem(i, 1, before_item)

            # Depois
            after_item = QTableWidgetItem(f"{after[key]:{fmt}}")
            self.result_table.setItem(i, 2, after_item)

            # Variação %
            change_val = changes.get(key, 0.0)
            change_item = QTableWidgetItem(f"{change_val:+.3f}%")

            # Colorir baseado na magnitude da mudança
            if abs(change_val) < 0.1:
                change_item.setForeground(QBrush(QColor('#4CAF50')))  # Verde
            elif abs(change_val) < 1.0:
                change_item.setForeground(QBrush(QColor('#FF9800')))  # Laranja
            else:
                change_item.setForeground(QBrush(QColor('#F44336')))  # Vermelho

            self.result_table.setItem(i, 3, change_item)

        # Mensagem de resultado
        if r['success']:
            color = '#4CAF50'
            self.accept_btn.setEnabled(True)
        else:
            color = '#F44336'
            self.accept_btn.setEnabled(False)

        msg = (f"{r['n_peaks_matched']}/{r['n_peaks_total']} picos correspondidos\n"
               f"Erro: {r['cost_before']:.4f} → {r['cost_after']:.4f}")
        self.result_label.setText(msg)
        self.result_label.setStyleSheet(f"color: {color}; padding: 4px; font-weight: bold;")

    def _update_residuals_in_table(self):
        """Atualiza a tabela de picos com informações de resíduos."""
        if not self.fit_result or not self.fit_result.get('residuals'):
            return

        residuals = self.fit_result['residuals']

        for i, res in enumerate(residuals):
            if i >= self.peaks_table.rowCount():
                break

            delta = res.get('delta_2theta', float('inf'))
            hkl = res.get('hkl')

            if hkl:
                hkl_str = f"({hkl[0]}{hkl[1]}{hkl[2]})"
            else:
                hkl_str = ""

            status_text = f"Δ={delta:.3f}° {hkl_str}"
            status_item = QTableWidgetItem(status_text)

            if delta < 0.1:
                status_item.setForeground(QBrush(QColor('#4CAF50')))
            elif delta < 0.3:
                status_item.setForeground(QBrush(QColor('#FF9800')))
            else:
                status_item.setForeground(QBrush(QColor('#F44336')))

            self.peaks_table.setItem(i, 2, status_item)

    def _accept_result(self):
        """Aceita o resultado do ajuste e emite os novos parâmetros."""
        if not self.fit_result or not self.fit_result.get('success'):
            return

        self.parametersAccepted.emit(self.fit_result['params_after'])
        self.accept()

    def get_result(self):
        """Retorna o resultado do ajuste."""
        return self.fit_result
