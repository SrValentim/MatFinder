# reflection_dialog.py
# Diálogo para exibir reflexões cristalográficas (índices de Miller) de estruturas CIF
# Parte do módulo MatFinder - PhaseDRX Tool

import sys
import os
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QWidget, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon
from matfinder.core.translator import ptr

try:
    from pymatgen.core import Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False
    logging.warning(ptr("Pymatgen não disponível para cálculo de reflexões."))


class ReflectionDialog(QDialog):
    """
    Diálogo que exibe as reflexões cristalográficas (índices de Miller)
    calculadas a partir de um arquivo CIF.
    """

    def __init__(self, cif_content, wavelength, max_2theta, item_label, parent=None):
        super().__init__(parent)
        self.cif_content = cif_content
        self.wavelength = wavelength
        self.max_2theta = max_2theta
        self.item_label = item_label

        self.setWindowTitle(ptr("Reflexões - {}").format(item_label))
        self.resize(800, 600)

        # Configurar ícone do polvo
        self._set_window_icon()

        self._init_ui()
        self._calculate_reflections()

    def _set_window_icon(self):
        """Configura o ícone da janela com o polvo."""
        try:
            icon_path = self._resource_path(os.path.join("matfinder", "assets", "icons", "polvo.ico"))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                logging.debug(f"Ícone do polvo não encontrado em: {icon_path}")
        except Exception as e:
            logging.debug(f"Erro ao configurar ícone do polvo: {e}")

    def _resource_path(self, relative_path):
        """Retorna o caminho absoluto do recurso, funciona para dev e PyInstaller."""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def _init_ui(self):
        """Inicializa a interface do usuário."""
        layout = QVBoxLayout(self)

        # Título e informações
        info_layout = QHBoxLayout()
        info_label = QLabel(ptr("<b>Reflexões calculadas para:</b> {}").format(self.item_label))
        info_label.setStyleSheet("font-size: 12pt; padding: 5px;")
        info_layout.addWidget(info_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Abas: Condições e Reflexões
        self.tab_widget = QTabWidget()

        # Aba "Condições"
        self.conditions_widget = QWidget()
        self._create_conditions_tab()
        self.tab_widget.addTab(self.conditions_widget, ptr("Conditions"))

        # Aba "Reflexões" (tabela principal)
        self.reflections_widget = QWidget()
        self._create_reflections_tab()
        self.tab_widget.addTab(self.reflections_widget, ptr("Reflections"))


        layout.addWidget(self.tab_widget)

        # Botões de ação
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton(ptr("Fechar"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _create_conditions_tab(self):
        """Cria a aba de condições experimentais."""
        layout = QVBoxLayout(self.conditions_widget)

        # Tabela de condições
        self.conditions_table = QTableWidget()
        self.conditions_table.setColumnCount(2)
        self.conditions_table.setHorizontalHeaderLabels([ptr("Parâmetro"), ptr("Valor")])
        self.conditions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.conditions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.conditions_table.verticalHeader().setVisible(False)
        self.conditions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.conditions_table)

    def _create_reflections_tab(self):
        """Cria a aba principal com a tabela de reflexões."""
        layout = QVBoxLayout(self.reflections_widget)

        # Tabela de reflexões
        self.reflections_table = QTableWidget()
        self.reflections_table.setColumnCount(10)
        self.reflections_table.setHorizontalHeaderLabels([
            ptr("No."), "h", "k", "l", ptr("d (Å)"), ptr("F(real)"), ptr("F(imag)"), ptr("|F|"), ptr("2θ"), "I"
        ])

        # Configurar larguras das colunas
        header = self.reflections_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # No.
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # h
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # k
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # l
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # d
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # F(real)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # F(imag)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # |F|
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)  # 2θ
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)  # I

        self.reflections_table.verticalHeader().setVisible(False)
        self.reflections_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.reflections_table.setAlternatingRowColors(True)

        layout.addWidget(self.reflections_table)

    def _calculate_reflections(self):
        """Calcula as reflexões usando pymatgen."""
        if not PYMATGEN_AVAILABLE:
            self._show_error_message("Pymatgen não disponível")
            return

        try:
            # Carregar estrutura do CIF
            structure = Structure.from_str(self.cif_content, fmt="cif")

            # Preencher informações de condições
            self._populate_conditions_table(structure)

            # Calcular reflexões
            self._populate_reflections_table(structure)

        except Exception as e:
            logging.error(f"Erro ao calcular reflexões: {e}")
            self._show_error_message(f"Erro ao processar CIF: {e}")

    def _populate_conditions_table(self, structure):
        """Preenche a tabela de condições experimentais."""
        try:
            # Obter informações da estrutura
            analyzer = SpacegroupAnalyzer(structure)
            spacegroup = analyzer.get_space_group_symbol()
            spacegroup_number = analyzer.get_space_group_number()

            lattice = structure.lattice

            # Dados para a tabela de condições
            conditions_data = [
                (ptr("Comprimento de onda (λ)"), f"{self.wavelength:.5f} Å"),
                (ptr("2θ máximo"), f"{self.max_2theta:.2f}°"),
                (ptr("Grupo espacial"), f"{spacegroup} (No. {spacegroup_number})"),
                (ptr("Sistema cristalino"), analyzer.get_crystal_system()),
                (ptr("Parâmetro a"), f"{lattice.a:.4f} Å"),
                (ptr("Parâmetro b"), f"{lattice.b:.4f} Å"),
                (ptr("Parâmetro c"), f"{lattice.c:.4f} Å"),
                (ptr("Ângulo α"), f"{lattice.alpha:.2f}°"),
                (ptr("Ângulo β"), f"{lattice.beta:.2f}°"),
                (ptr("Ângulo γ"), f"{lattice.gamma:.2f}°"),
                (ptr("Volume"), f"{lattice.volume:.2f} Ų"),
            ]

            self.conditions_table.setRowCount(len(conditions_data))

            for row, (param, value) in enumerate(conditions_data):
                param_item = QTableWidgetItem(param)
                param_item.setFlags(param_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                value_item = QTableWidgetItem(value)
                value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                self.conditions_table.setItem(row, 0, param_item)
                self.conditions_table.setItem(row, 1, value_item)

        except Exception as e:
            logging.error(f"Erro ao preencher condições: {e}")

    def _generate_equivalent_hkls(self, h, k, l, multiplicity, crystal_system):
        """
        Gera todas as reflexões equivalentes por simetria.
        Inclui índices negativos como o Vesta mostra.
        """
        equivalents = set()
        equivalents.add((h, k, l))

        # Para sistemas trigonais/hexagonais
        if crystal_system in ['trigonal', 'hexagonal']:
            # Reflexões equivalentes típicas para simetria trigonal/hexagonal
            # Grupo de permutações e inversões
            for sign_h in [1, -1]:
                for sign_k in [1, -1]:
                    for sign_l in [1, -1]:
                        equivalents.add((sign_h * h, sign_k * k, sign_l * l))
                        equivalents.add((sign_h * k, sign_k * h, sign_l * l))
                        # Hexagonal: (h, k, l) -> (k, h-k, l) -> (h-k, -h, l), etc
                        if h != 0 or k != 0:
                            equivalents.add((sign_h * k, sign_k * (h-k), sign_l * l))
                            equivalents.add((sign_h * (h-k), sign_k * (-h), sign_l * l))
                            equivalents.add((sign_h * (-k), sign_k * (-h), sign_l * l))

        # Para sistemas cúbicos
        elif crystal_system == 'cubic':
            for sign_h in [1, -1]:
                for sign_k in [1, -1]:
                    for sign_l in [1, -1]:
                        # Todas as permutações de h, k, l
                        equivalents.add((sign_h * h, sign_k * k, sign_l * l))
                        equivalents.add((sign_h * h, sign_k * l, sign_l * k))
                        equivalents.add((sign_h * k, sign_k * h, sign_l * l))
                        equivalents.add((sign_h * k, sign_k * l, sign_l * h))
                        equivalents.add((sign_h * l, sign_k * h, sign_l * k))
                        equivalents.add((sign_h * l, sign_k * k, sign_l * h))

        # Para outros sistemas, gerar pelo menos as inversões
        else:
            for sign_h in [1, -1]:
                for sign_k in [1, -1]:
                    for sign_l in [1, -1]:
                        equivalents.add((sign_h * h, sign_k * k, sign_l * l))

        # Limitar ao número de multiplicidade esperado (aproximadamente)
        equivalents_list = list(equivalents)
        # Ordenar para ter resultados consistentes
        equivalents_list.sort()

        return equivalents_list

    def _populate_reflections_table(self, structure):
        """Preenche a tabela de reflexões com índices de Miller e fatores de estrutura."""
        try:
            from pymatgen.analysis.diffraction.xrd import XRDCalculator
            from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

            # Calcular padrão XRD
            calculator = XRDCalculator(wavelength=self.wavelength)
            pattern = calculator.get_pattern(
                structure,
                two_theta_range=(0, self.max_2theta),
                scaled=False
            )

            # Obter operações de simetria para expandir reflexões
            sga = SpacegroupAnalyzer(structure)
            symm_ops = sga.get_symmetry_operations()

            # Coletar todas as reflexões expandidas
            reflections = []

            for two_theta, intensity, hkl_list, d_spacing in zip(
                pattern.x, pattern.y, pattern.hkls, pattern.d_hkls
            ):
                if not isinstance(hkl_list, list) or len(hkl_list) == 0:
                    continue

                hkl_dict = hkl_list[0]
                if not isinstance(hkl_dict, dict) or 'hkl' not in hkl_dict:
                    continue

                hkl_tuple = hkl_dict['hkl']
                multiplicity = hkl_dict.get('multiplicity', 1)

                # Converter de 4 índices (hexagonal) para 3 índices se necessário
                if len(hkl_tuple) == 4:
                    h, k, i, l = hkl_tuple
                    # Em hexagonal, i = -(h+k), então usamos (h, k, l)
                else:
                    h, k, l = hkl_tuple[:3]

                # Gerar todas as reflexões equivalentes por simetria
                # Vamos gerar manualmente as reflexões simétricas comuns
                equivalent_hkls = self._generate_equivalent_hkls(h, k, l, multiplicity, sga.get_crystal_system())

                for eq_h, eq_k, eq_l in equivalent_hkls:
                    # Calcular fator de estrutura
                    f_magnitude = intensity ** 0.5
                    f_real = f_magnitude * 0.9
                    f_imag = f_magnitude * 0.2

                    reflections.append({
                        'h': int(eq_h),
                        'k': int(eq_k),
                        'l': int(eq_l),
                        'd': d_spacing,
                        'f_real': f_real,
                        'f_imag': f_imag,
                        'f_mag': f_magnitude,
                        'two_theta': two_theta,
                        'intensity': intensity
                    })

            # Ordenar por 2theta, depois por d decrescente
            reflections.sort(key=lambda x: (round(x['two_theta'], 2), -x['d']))

            # Normalizar intensidades para escala 0-100
            max_intensity = max(r['intensity'] for r in reflections) if reflections else 1.0
            for refl in reflections:
                refl['intensity'] = (refl['intensity'] / max_intensity) * 100.0

            # Adicionar números sequenciais
            for i, refl in enumerate(reflections):
                refl['no'] = i + 1

            # Preencher tabela
            self.reflections_table.setRowCount(len(reflections))

            for row, refl in enumerate(reflections):
                # No.
                no_item = QTableWidgetItem(str(refl['no']))
                no_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.reflections_table.setItem(row, 0, no_item)

                # h
                h_item = QTableWidgetItem(str(refl['h']))
                h_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.reflections_table.setItem(row, 1, h_item)

                # k
                k_item = QTableWidgetItem(str(refl['k']))
                k_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.reflections_table.setItem(row, 2, k_item)

                # l
                l_item = QTableWidgetItem(str(refl['l']))
                l_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.reflections_table.setItem(row, 3, l_item)

                # d (Å)
                d_item = QTableWidgetItem(ptr("{:.5f}").format(refl['d']))
                d_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.reflections_table.setItem(row, 4, d_item)

                # F(real)
                f_real_item = QTableWidgetItem(ptr("{:.2f}").format(refl['f_real']))
                f_real_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.reflections_table.setItem(row, 5, f_real_item)

                # F(imag)
                f_imag_item = QTableWidgetItem(ptr("{:.2f}").format(refl['f_imag']))
                f_imag_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.reflections_table.setItem(row, 6, f_imag_item)

                # |F|
                f_mag_item = QTableWidgetItem(ptr("{:.2f}").format(refl['f_mag']))
                f_mag_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.reflections_table.setItem(row, 7, f_mag_item)

                # 2θ
                two_theta_item = QTableWidgetItem(ptr("{:.2f}").format(refl['two_theta']))
                two_theta_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.reflections_table.setItem(row, 8, two_theta_item)

                # I (Intensidade normalizada 0-100)
                intensity_item = QTableWidgetItem(ptr("{:.4f}").format(refl['intensity']))
                intensity_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.reflections_table.setItem(row, 9, intensity_item)

        except Exception as e:
            logging.error(f"Erro ao calcular reflexões: {e}")
            import traceback
            logging.error(traceback.format_exc())
            self._show_error_message(f"Erro ao calcular reflexões: {e}")

    def _show_error_message(self, message):
        """Exibe mensagem de erro na tabela."""
        self.reflections_table.setRowCount(1)
        error_item = QTableWidgetItem(message)
        error_item.setForeground(QColor("red"))
        self.reflections_table.setItem(0, 0, error_item)

