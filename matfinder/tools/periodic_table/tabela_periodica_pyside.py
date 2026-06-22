import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QDialog, QGridLayout, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QFrame, QWidget,
    QSizePolicy, QDialogButtonBox, QTextEdit
)
from PySide6.QtGui import QColor, QPalette, QFont, QIcon, QCursor
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from matfinder.core.translator import ptr

# Importar sistema de tradução
try:
    from matfinder.core.translator import tr, get_current_language
except ImportError:
    def tr(key, **kwargs): return key
    def get_current_language(): return ptr("pt_BR")

# Função para obter nome traduzido do elemento
def get_element_name(symbol):
    """Obtém o nome do elemento traduzido para o idioma atual."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        elements_file = os.path.join(base_dir, 'assets', 'translations', 'elements.json')

        if os.path.exists(elements_file):
            with open(elements_file, 'r', encoding='utf-8') as f:
                elements_data = json.load(f)

            lang = get_current_language()
            el_info = elements_data.get('elements', {}).get(symbol, {})

            if lang == 'en_US':
                return el_info.get('name_en', el_info.get('name', symbol))
            elif lang == 'de_DE':
                return el_info.get('name_de', el_info.get('name', symbol))
            else:
                return el_info.get('name', symbol)
    except Exception:
        pass
    return symbol

# Dados dos elementos e cores (mantidos da sua versão Tkinter para consistência)
ELEMENTOS = [
    {"simbolo": "H", "nome": "Hidrogênio", "numero": 1, "massa": 1.008, "grupo": 1, "periodo": 1,
     "categoria": "diatomic nonmetal"},
    {"simbolo": "He", "nome": "Hélio", "numero": 2, "massa": 4.0026, "grupo": 18, "periodo": 1,
     "categoria": "noble gas"},
    {"simbolo": "Li", "nome": "Lítio", "numero": 3, "massa": 6.94, "grupo": 1, "periodo": 2,
     "categoria": "alkali metal"},
    {"simbolo": "Be", "nome": "Berílio", "numero": 4, "massa": 9.0122, "grupo": 2, "periodo": 2,
     "categoria": "alkaline earth metal"},
    {"simbolo": "B", "nome": "Boro", "numero": 5, "massa": 10.81, "grupo": 13, "periodo": 2, "categoria": "metalloid"},
    {"simbolo": "C", "nome": "Carbono", "numero": 6, "massa": 12.011, "grupo": 14, "periodo": 2,
     "categoria": "polyatomic nonmetal"},
    {"simbolo": "N", "nome": "Nitrogênio", "numero": 7, "massa": 14.007, "grupo": 15, "periodo": 2,
     "categoria": "diatomic nonmetal"},
    {"simbolo": "O", "nome": "Oxigênio", "numero": 8, "massa": 15.999, "grupo": 16, "periodo": 2,
     "categoria": "diatomic nonmetal"},
    {"simbolo": "F", "nome": "Flúor", "numero": 9, "massa": 18.998, "grupo": 17, "periodo": 2, "categoria": "halogen"},
    {"simbolo": "Ne", "nome": "Neônio", "numero": 10, "massa": 20.180, "grupo": 18, "periodo": 2,
     "categoria": "noble gas"},
    {"simbolo": "Na", "nome": "Sódio", "numero": 11, "massa": 22.990, "grupo": 1, "periodo": 3,
     "categoria": "alkali metal"},
    {"simbolo": "Mg", "nome": "Magnésio", "numero": 12, "massa": 24.305, "grupo": 2, "periodo": 3,
     "categoria": "alkaline earth metal"},
    {"simbolo": "Al", "nome": "Alumínio", "numero": 13, "massa": 26.982, "grupo": 13, "periodo": 3,
     "categoria": "post-transition metal"},
    {"simbolo": "Si", "nome": "Silício", "numero": 14, "massa": 28.085, "grupo": 14, "periodo": 3,
     "categoria": "metalloid"},
    {"simbolo": "P", "nome": "Fósforo", "numero": 15, "massa": 30.974, "grupo": 15, "periodo": 3,
     "categoria": "polyatomic nonmetal"},
    {"simbolo": "S", "nome": "Enxofre", "numero": 16, "massa": 32.06, "grupo": 16, "periodo": 3,
     "categoria": "polyatomic nonmetal"},
    {"simbolo": "Cl", "nome": "Cloro", "numero": 17, "massa": 35.45, "grupo": 17, "periodo": 3, "categoria": "halogen"},
    {"simbolo": "Ar", "nome": "Argônio", "numero": 18, "massa": 39.948, "grupo": 18, "periodo": 3,
     "categoria": "noble gas"},
    {"simbolo": "K", "nome": "Potássio", "numero": 19, "massa": 39.098, "grupo": 1, "periodo": 4,
     "categoria": "alkali metal"},
    {"simbolo": "Ca", "nome": "Cálcio", "numero": 20, "massa": 40.078, "grupo": 2, "periodo": 4,
     "categoria": "alkaline earth metal"},
    {"simbolo": "Sc", "nome": "Escândio", "numero": 21, "massa": 44.956, "grupo": 3, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Ti", "nome": "Titânio", "numero": 22, "massa": 47.867, "grupo": 4, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "V", "nome": "Vanádio", "numero": 23, "massa": 50.942, "grupo": 5, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Cr", "nome": "Cromo", "numero": 24, "massa": 51.996, "grupo": 6, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Mn", "nome": "Manganês", "numero": 25, "massa": 54.938, "grupo": 7, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Fe", "nome": "Ferro", "numero": 26, "massa": 55.845, "grupo": 8, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Co", "nome": "Cobalto", "numero": 27, "massa": 58.933, "grupo": 9, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Ni", "nome": "Níquel", "numero": 28, "massa": 58.693, "grupo": 10, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Cu", "nome": "Cobre", "numero": 29, "massa": 63.546, "grupo": 11, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Zn", "nome": "Zinco", "numero": 30, "massa": 65.38, "grupo": 12, "periodo": 4,
     "categoria": "transition metal"},
    {"simbolo": "Ga", "nome": "Gálio", "numero": 31, "massa": 69.723, "grupo": 13, "periodo": 4,
     "categoria": "post-transition metal"},
    {"simbolo": "Ge", "nome": "Germânio", "numero": 32, "massa": 72.63, "grupo": 14, "periodo": 4,
     "categoria": "metalloid"},
    {"simbolo": "As", "nome": "Arsênio", "numero": 33, "massa": 74.922, "grupo": 15, "periodo": 4,
     "categoria": "metalloid"},
    {"simbolo": "Se", "nome": "Selênio", "numero": 34, "massa": 78.971, "grupo": 16, "periodo": 4,
     "categoria": "polyatomic nonmetal"},
    {"simbolo": "Br", "nome": "Bromo", "numero": 35, "massa": 79.904, "grupo": 17, "periodo": 4,
     "categoria": "halogen"},
    {"simbolo": "Kr", "nome": "Criptônio", "numero": 36, "massa": 83.798, "grupo": 18, "periodo": 4,
     "categoria": "noble gas"},
    {"simbolo": "Rb", "nome": "Rubídio", "numero": 37, "massa": 85.468, "grupo": 1, "periodo": 5,
     "categoria": "alkali metal"},
    {"simbolo": "Sr", "nome": "Estrôncio", "numero": 38, "massa": 87.62, "grupo": 2, "periodo": 5,
     "categoria": "alkaline earth metal"},
    {"simbolo": "Y", "nome": "Ítrio", "numero": 39, "massa": 88.906, "grupo": 3, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Zr", "nome": "Zircônio", "numero": 40, "massa": 91.224, "grupo": 4, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Nb", "nome": "Nióbio", "numero": 41, "massa": 92.906, "grupo": 5, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Mo", "nome": "Molibdênio", "numero": 42, "massa": 95.95, "grupo": 6, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Tc", "nome": "Tecnécio", "numero": 43, "massa": 98, "grupo": 7, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Ru", "nome": "Rutênio", "numero": 44, "massa": 101.07, "grupo": 8, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Rh", "nome": "Ródio", "numero": 45, "massa": 102.91, "grupo": 9, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Pd", "nome": "Paládio", "numero": 46, "massa": 106.42, "grupo": 10, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Ag", "nome": "Prata", "numero": 47, "massa": 107.87, "grupo": 11, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "Cd", "nome": "Cádmio", "numero": 48, "massa": 112.41, "grupo": 12, "periodo": 5,
     "categoria": "transition metal"},
    {"simbolo": "In", "nome": "Índio", "numero": 49, "massa": 114.82, "grupo": 13, "periodo": 5,
     "categoria": "post-transition metal"},
    {"simbolo": "Sn", "nome": "Estanho", "numero": 50, "massa": 118.71, "grupo": 14, "periodo": 5,
     "categoria": "post-transition metal"},
    {"simbolo": "Sb", "nome": "Antimônio", "numero": 51, "massa": 121.76, "grupo": 15, "periodo": 5,
     "categoria": "metalloid"},
    {"simbolo": "Te", "nome": "Telúrio", "numero": 52, "massa": 127.60, "grupo": 16, "periodo": 5,
     "categoria": "metalloid"},
    {"simbolo": "I", "nome": "Iodo", "numero": 53, "massa": 126.90, "grupo": 17, "periodo": 5, "categoria": "halogen"},
    {"simbolo": "Xe", "nome": "Xenônio", "numero": 54, "massa": 131.29, "grupo": 18, "periodo": 5,
     "categoria": "noble gas"},
    {"simbolo": "Cs", "nome": "Césio", "numero": 55, "massa": 132.91, "grupo": 1, "periodo": 6,
     "categoria": "alkali metal"},
    {"simbolo": "Ba", "nome": "Bário", "numero": 56, "massa": 137.33, "grupo": 2, "periodo": 6,
     "categoria": "alkaline earth metal"},
    {"simbolo": "La", "nome": "Lantânio", "numero": 57, "massa": 138.91, "grupo": 3, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Ce", "nome": "Cério", "numero": 58, "massa": 140.12, "grupo": 4, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Pr", "nome": "Praseodímio", "numero": 59, "massa": 140.91, "grupo": 5, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Nd", "nome": "Neodímio", "numero": 60, "massa": 144.24, "grupo": 6, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Pm", "nome": "Promécio", "numero": 61, "massa": 145, "grupo": 7, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Sm", "nome": "Samário", "numero": 62, "massa": 150.36, "grupo": 8, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Eu", "nome": "Európio", "numero": 63, "massa": 151.96, "grupo": 9, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Gd", "nome": "Gadolínio", "numero": 64, "massa": 157.25, "grupo": 10, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Tb", "nome": "Térbio", "numero": 65, "massa": 158.93, "grupo": 11, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Dy", "nome": "Disprósio", "numero": 66, "massa": 162.50, "grupo": 12, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Ho", "nome": "Hólmio", "numero": 67, "massa": 164.93, "grupo": 13, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Er", "nome": "Érbio", "numero": 68, "massa": 167.26, "grupo": 14, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Tm", "nome": "Túlio", "numero": 69, "massa": 168.93, "grupo": 15, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Yb", "nome": "Itérbio", "numero": 70, "massa": 173.05, "grupo": 16, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Lu", "nome": "Lutécio", "numero": 71, "massa": 174.97, "grupo": 17, "periodo": 8,
     "categoria": "lanthanide"},
    {"simbolo": "Hf", "nome": "Háfnio", "numero": 72, "massa": 178.49, "grupo": 4, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "Ta", "nome": "Tântalo", "numero": 73, "massa": 180.95, "grupo": 5, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "W", "nome": "Tungstênio", "numero": 74, "massa": 183.84, "grupo": 6, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "Re", "nome": "Rênio", "numero": 75, "massa": 186.21, "grupo": 7, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "Os", "nome": "Ósmio", "numero": 76, "massa": 190.23, "grupo": 8, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "Ir", "nome": "Irídio", "numero": 77, "massa": 192.22, "grupo": 9, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "Pt", "nome": "Platina", "numero": 78, "massa": 195.08, "grupo": 10, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "Au", "nome": "Ouro", "numero": 79, "massa": 196.97, "grupo": 11, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "Hg", "nome": "Mercúrio", "numero": 80, "massa": 200.59, "grupo": 12, "periodo": 6,
     "categoria": "transition metal"},
    {"simbolo": "Tl", "nome": "Tálio", "numero": 81, "massa": 204.38, "grupo": 13, "periodo": 6,
     "categoria": "post-transition metal"},
    {"simbolo": "Pb", "nome": "Chumbo", "numero": 82, "massa": 207.2, "grupo": 14, "periodo": 6,
     "categoria": "post-transition metal"},
    {"simbolo": "Bi", "nome": "Bismuto", "numero": 83, "massa": 208.98, "grupo": 15, "periodo": 6,
     "categoria": "post-transition metal"},
    {"simbolo": "Po", "nome": "Polônio", "numero": 84, "massa": 209, "grupo": 16, "periodo": 6,
     "categoria": "metalloid"},
    {"simbolo": "At", "nome": "Astato", "numero": 85, "massa": 210, "grupo": 17, "periodo": 6, "categoria": "halogen"},
    {"simbolo": "Rn", "nome": "Radônio", "numero": 86, "massa": 222, "grupo": 18, "periodo": 6,
     "categoria": "noble gas"},
    {"simbolo": "Fr", "nome": "Frâncio", "numero": 87, "massa": 223, "grupo": 1, "periodo": 7,
     "categoria": "alkali metal"},
    {"simbolo": "Ra", "nome": "Rádio", "numero": 88, "massa": 226, "grupo": 2, "periodo": 7,
     "categoria": "alkaline earth metal"},
    {"simbolo": "Ac", "nome": "Actínio", "numero": 89, "massa": 227, "grupo": 3, "periodo": 9, "categoria": "actinide"},
    {"simbolo": "Th", "nome": "Tório", "numero": 90, "massa": 232.04, "grupo": 4, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Pa", "nome": "Protactínio", "numero": 91, "massa": 231.04, "grupo": 5, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "U", "nome": "Urânio", "numero": 92, "massa": 238.03, "grupo": 6, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Np", "nome": "Neptúnio", "numero": 93, "massa": 237, "grupo": 7, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Pu", "nome": "Plutônio", "numero": 94, "massa": 244, "grupo": 8, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Am", "nome": "Amerício", "numero": 95, "massa": 243, "grupo": 9, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Cm", "nome": "Cúrio", "numero": 96, "massa": 247, "grupo": 10, "periodo": 9, "categoria": "actinide"},
    {"simbolo": "Bk", "nome": "Berquélio", "numero": 97, "massa": 247, "grupo": 11, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Cf", "nome": "Califórnio", "numero": 98, "massa": 251, "grupo": 12, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Es", "nome": "Einstênio", "numero": 99, "massa": 252, "grupo": 13, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Fm", "nome": "Férmio", "numero": 100, "massa": 257, "grupo": 14, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Md", "nome": "Mendelévio", "numero": 101, "massa": 258, "grupo": 15, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "No", "nome": "Nobélio", "numero": 102, "massa": 259, "grupo": 16, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Lr", "nome": "Laurêncio", "numero": 103, "massa": 262, "grupo": 17, "periodo": 9,
     "categoria": "actinide"},
    {"simbolo": "Rf", "nome": "Rutherfórdio", "numero": 104, "massa": 267, "grupo": 4, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Db", "nome": "Dúbnio", "numero": 105, "massa": 270, "grupo": 5, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Sg", "nome": "Seabórgio", "numero": 106, "massa": 271, "grupo": 6, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Bh", "nome": "Bóhrio", "numero": 107, "massa": 270, "grupo": 7, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Hs", "nome": "Hássio", "numero": 108, "massa": 277, "grupo": 8, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Mt", "nome": "Meitnério", "numero": 109, "massa": 278, "grupo": 9, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Ds", "nome": "Darmstádio", "numero": 110, "massa": 281, "grupo": 10, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Rg", "nome": "Roentgênio", "numero": 111, "massa": 282, "grupo": 11, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Cn", "nome": "Copernício", "numero": 112, "massa": 285, "grupo": 12, "periodo": 7,
     "categoria": "transition metal"},
    {"simbolo": "Nh", "nome": "Nihônio", "numero": 113, "massa": 286, "grupo": 13, "periodo": 7,
     "categoria": "post-transition metal"},
    {"simbolo": "Fl", "nome": "Fleróvio", "numero": 114, "massa": 289, "grupo": 14, "periodo": 7,
     "categoria": "post-transition metal"},
    {"simbolo": "Mc", "nome": "Moscóvio", "numero": 115, "massa": 290, "grupo": 15, "periodo": 7,
     "categoria": "post-transition metal"},
    {"simbolo": "Lv", "nome": "Livermório", "numero": 116, "massa": 293, "grupo": 16, "periodo": 7,
     "categoria": "post-transition metal"},
    {"simbolo": "Ts", "nome": "Tenessino", "numero": 117, "massa": 294, "grupo": 17, "periodo": 7,
     "categoria": "halogen"},
    {"simbolo": "Og", "nome": "Oganessônio", "numero": 118, "massa": 294, "grupo": 18, "periodo": 7,
     "categoria": "noble gas"}
]

CATEGORY_COLORS = {
    "diatomic nonmetal": "#A0FFA0",
    "polyatomic nonmetal": "#A0FFA0",
    "alkali metal": "#FFB366",
    "alkaline earth metal": "#FFFF66",
    "metalloid": "#CC99FF",
    "halogen": "#66FFFF",
    "noble gas": "#FF99CC",
    "transition metal": "#66B3FF",
    "post-transition metal": "#CCCCCC",
    "lanthanide": "#99FF99",
    "actinide": "#FF9999",
    "unknown": "#E0E0E0",
}

# Função para traduzir categoria
def get_category_translation(category_key):
    """Traduz a categoria para o idioma atual."""
    key = category_key.replace(" ", "_").replace("-", "_")
    translated = tr(f'periodic_table.categories.{key}')
    if translated.startswith('periodic_table.categories.'):
        # Fallback para o português original
        return CATEGORY_TRANSLATIONS_PT_DEFAULT.get(category_key, category_key.replace("-", " ").title())
    return translated

# Traduções padrão para fallback
CATEGORY_TRANSLATIONS_PT_DEFAULT = {
    "diatomic nonmetal": "Não Metal Diatômico",
    "polyatomic nonmetal": "Não Metal Poliatômico",
    "alkali metal": "Metal Alcalino",
    "alkaline earth metal": "Metal Alcalino-Terroso",
    "metalloid": "Metaloide",
    "halogen": "Halogênio",
    "noble gas": "Gás Nobre",
    "transition metal": "Metal de Transição",
    "post-transition metal": "Metal Pós-Transição",
    "lanthanide": "Lantanídeo",
    "actinide": "Actinídeo",
    "unknown": "Desconhecido",
}

# Alias para compatibilidade
CATEGORY_TRANSLATIONS_PT = CATEGORY_TRANSLATIONS_PT_DEFAULT

DEFAULT_BUTTON_COLOR = "#D9D9D9"
SELECTED_BORDER_COLOR = "#FFD700"
SCINTILLATION_LIGHT_FACTOR = 1.15
SCINTILLATION_DARK_FACTOR = 0.85


class TabelaPeriodicaDialog(QDialog):
    element_toggled_signal = Signal(str, bool)
    selection_confirmed_signal = Signal(list)
    selection_cleared_signal = Signal()

    def __init__(self, parent=None, initial_selected_elements=None):
        super().__init__(parent)
        self.setWindowTitle(tr('periodic_table.title'))
        self.setFixedSize(880, 660)

        self.selected_elements = set(initial_selected_elements) if initial_selected_elements else set()
        self.element_buttons = {}
        self.original_button_stylesheets = {}
        self.scintillation_timers = {}
        self.scintillation_state_is_light = {}

        self._init_ui()
        self._update_selected_elements_display()
        self._apply_initial_selection_styles()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        selected_area_group = QFrame()
        selected_area_group.setFrameShape(QFrame.Shape.StyledPanel)
        selected_layout = QVBoxLayout(selected_area_group)
        selected_layout.addWidget(QLabel(tr('periodic_table.selected_label')))
        self.selected_elements_text_edit = QTextEdit()
        self.selected_elements_text_edit.setReadOnly(True)
        self.selected_elements_text_edit.setFixedHeight(60)
        selected_layout.addWidget(self.selected_elements_text_edit)
        main_layout.addWidget(selected_area_group)

        table_container_widget = QWidget()
        table_container_layout = QHBoxLayout(table_container_widget)
        table_container_layout.setContentsMargins(0, 0, 0, 0)

        self.table_widget = QWidget()
        self.grid_layout = QGridLayout(self.table_widget)
        self.grid_layout.setSpacing(2)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self._populate_table()

        table_container_layout.addStretch(1)
        table_container_layout.addWidget(self.table_widget)
        table_container_layout.addStretch(1)

        main_layout.addWidget(table_container_widget)

        legend_group = QFrame()
        legend_group.setFrameShape(QFrame.Shape.StyledPanel)
        legend_layout_wrapper = QVBoxLayout(legend_group)
        legend_layout_wrapper.addWidget(QLabel(tr('periodic_table.legend')))

        legend_grid_layout = QGridLayout()
        num_legend_cols = 3
        current_col = 0
        current_row = 0

        legend_order = [
            "alkali metal", "alkaline earth metal", "transition metal",
            "post-transition metal", "metalloid", "lanthanide",
            "actinide", "halogen", "noble gas",
            "diatomic nonmetal", "polyatomic nonmetal"
        ]

        for category_key in legend_order:
            color_hex = CATEGORY_COLORS.get(category_key)
            translated_name = get_category_translation(category_key)
            if not color_hex or category_key == "unknown":
                continue

            color_label = QLabel()
            color_label.setFixedSize(15, 15)
            color_label.setStyleSheet(f"background-color: {color_hex}; border: 1px solid black;")

            name_label = QLabel(translated_name)
            name_label.setWordWrap(True)

            legend_grid_layout.addWidget(color_label, current_row, current_col * 2,
                                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            legend_grid_layout.addWidget(name_label, current_row, current_col * 2 + 1,
                                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            current_col += 1
            if current_col >= num_legend_cols:
                current_col = 0
                current_row += 1

        legend_layout_wrapper.addLayout(legend_grid_layout)
        main_layout.addWidget(legend_group)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | \
                                           QDialogButtonBox.StandardButton.Cancel | \
                                           QDialogButtonBox.StandardButton.Reset)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(tr('periodic_table.confirm'))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(tr('dialogs.confirm.cancel'))
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).setText(tr('periodic_table.clear'))

        self.button_box.accepted.connect(self.confirm_selection)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.clear_all_selections)

        main_layout.addWidget(self.button_box)

    def _populate_table(self):
        button_size = QSize(40, 40)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)

        lanthanide_row = 7
        actinide_row = 8

        period_map = {
            1: 0, 2: 1, 3: 2, 4: 3, 5: 4,
            6: 5,
            7: 6,
            8: lanthanide_row,
            9: actinide_row
        }

        for el_data in ELEMENTOS:
            simbolo = el_data["simbolo"]
            grid_row = period_map.get(el_data["periodo"], el_data["periodo"] - 1)
            grupo = el_data["grupo"]
            categoria = el_data.get("categoria", "unknown")
            cor_hex = CATEGORY_COLORS.get(categoria, DEFAULT_BUTTON_COLOR)

            btn = QPushButton(simbolo)
            btn.setFixedSize(button_size)
            btn.setFont(font)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setAutoDefault(False)  # Impede que o botão seja acionado por Enter por padrão
            btn.setDefault(False)  # Garante que não é o botão padrão do diálogo

            # Nome traduzido do elemento
            nome_traduzido = get_element_name(simbolo)
            categoria_traduzida = tr(f'periodic_table.categories.{categoria.replace(" ", "_").replace("-", "_")}')

            tooltip_text = (
                ptr("<b>{} ({})</b><br>{}: {}<br>{}: {:.4f}<br>{}: {}").format(nome_traduzido, simbolo, tr('periodic_table.atomic_number'), el_data['numero'], tr('periodic_table.atomic_mass'), el_data['massa'], tr('periodic_table.category'), categoria_traduzida)
            )
            btn.setToolTip(tooltip_text)

            style = f"QPushButton {{ background-color: {cor_hex}; border: 1px solid #555555; border-radius: 3px; color: black; }}" \
                    f"QPushButton:hover {{ background-color: {self._vary_color_intensity(cor_hex, 1.1)}; }}"
            btn.setStyleSheet(style)
            self.original_button_stylesheets[simbolo] = style

            btn.clicked.connect(lambda checked=False, s=simbolo: self._toggle_element_selection(s))
            self.element_buttons[simbolo] = btn

            grid_col = grupo - 1
            if el_data["categoria"] == "lanthanide":
                grid_col = (el_data["numero"] - 57) + 2
            elif el_data["categoria"] == "actinide":
                grid_col = (el_data["numero"] - 89) + 2

            self.grid_layout.addWidget(btn, grid_row, grid_col)

        if any(el["categoria"] == "lanthanide" for el in ELEMENTOS):
            lan_label = QLabel(f" {tr('periodic_table.groups.lanthanides')} →")
            lan_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.grid_layout.addWidget(lan_label, lanthanide_row, 0, 1, 2)

        if any(el["categoria"] == "actinide" for el in ELEMENTOS):
            act_label = QLabel(f" {tr('periodic_table.groups.actinides')} →")
            act_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.grid_layout.addWidget(act_label, actinide_row, 0, 1, 2)

        for c in range(self.grid_layout.columnCount()):
            self.grid_layout.setColumnStretch(c, 0)
        for r in range(self.grid_layout.rowCount()):
            self.grid_layout.setRowStretch(r, 0)

        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)
        self.grid_layout.setColumnStretch(self.grid_layout.columnCount(), 1)

    def _apply_initial_selection_styles(self):
        for simbolo in self.selected_elements:
            if simbolo in self.element_buttons:
                self._apply_selection_style(simbolo, True)

    def _toggle_element_selection(self, simbolo):
        is_selected_now = False
        if simbolo in self.selected_elements:
            self.selected_elements.remove(simbolo)
            self._apply_selection_style(simbolo, False)
        else:
            self.selected_elements.add(simbolo)
            is_selected_now = True
            self._apply_selection_style(simbolo, True)

        self._update_selected_elements_display()
        self.element_toggled_signal.emit(simbolo, is_selected_now)

    def _apply_selection_style(self, simbolo, select):
        button = self.element_buttons.get(simbolo)
        if not button:
            return

        original_style = self.original_button_stylesheets.get(simbolo, "")

        if select:
            bg_color_original = DEFAULT_BUTTON_COLOR
            if "background-color:" in original_style:
                parts = original_style.split("background-color:")
                if len(parts) > 1:
                    color_part = parts[1].split(";")[0].strip()
                    bg_color_original = color_part

            selected_style_base = original_style.replace("border: 1px solid #555555;",
                                                         f"border: 2px solid {SELECTED_BORDER_COLOR};")
            button.setStyleSheet(selected_style_base)

            self._start_scintillation(simbolo, bg_color_original, selected_style_base)
        else:
            self._stop_scintillation(simbolo)
            button.setStyleSheet(original_style)

    def _start_scintillation(self, simbolo, base_bg_color_hex, selected_style_base):
        if simbolo in self.scintillation_timers:
            self.scintillation_timers[simbolo].stop()
            self.scintillation_timers[simbolo].deleteLater()

        self.scintillation_state_is_light[simbolo] = False

        timer = QTimer(self)
        timer.setInterval(350)

        def on_timeout():
            button = self.element_buttons.get(simbolo)
            if not button or simbolo not in self.selected_elements:
                self._stop_scintillation(simbolo)
                return

            current_state_light = self.scintillation_state_is_light.get(simbolo, False)

            if current_state_light:
                new_bg_style = f"background-color: {base_bg_color_hex};"
            else:
                light_color_hex = self._vary_color_intensity(base_bg_color_hex, SCINTILLATION_LIGHT_FACTOR)
                new_bg_style = f"background-color: {light_color_hex};"

            base_no_bg = selected_style_base
            if "background-color:" in base_no_bg:
                start_idx = base_no_bg.find("background-color:")
                end_idx = base_no_bg.find(";", start_idx)
                if end_idx != -1:
                    base_no_bg = base_no_bg[:start_idx] + base_no_bg[end_idx + 1:]
                else:
                    base_no_bg = base_no_bg[:start_idx]

            base_no_bg = base_no_bg.replace("QPushButton {", "").replace("}", "").strip()
            final_style = f"QPushButton {{ {base_no_bg} {new_bg_style} }}"

            button.setStyleSheet(final_style)
            self.scintillation_state_is_light[simbolo] = not current_state_light

        timer.timeout.connect(on_timeout)
        self.scintillation_timers[simbolo] = timer
        timer.start()
        on_timeout()

    def _stop_scintillation(self, simbolo):
        if simbolo in self.scintillation_timers:
            self.scintillation_timers[simbolo].stop()
            self.scintillation_timers[simbolo].deleteLater()
            if simbolo in self.scintillation_timers:
                del self.scintillation_timers[simbolo]
        if simbolo in self.scintillation_state_is_light:
            del self.scintillation_state_is_light[simbolo]

    def _vary_color_intensity(self, hex_color, factor):
        if not hex_color.startswith("#"): return hex_color
        qcolor = QColor(hex_color)
        if not qcolor.isValid(): return hex_color

        h, s, l, a = qcolor.getHslF()
        l = max(0.0, min(1.0, l * factor))

        varied_qcolor = QColor.fromHslF(h, s, l, a)
        return varied_qcolor.name()

    def _update_selected_elements_display(self):
        if not self.selected_elements:
            self.selected_elements_text_edit.setText(tr('periodic_table.no_selection'))
        else:
            sorted_symbols = sorted(
                list(self.selected_elements),
                key=lambda s: next((el['numero'] for el in ELEMENTOS if el['simbolo'] == s), 0)
            )

            display_lines = []
            for symbol in sorted_symbols:
                el_data = next((el for el in ELEMENTOS if el['simbolo'] == symbol), None)
                if el_data:
                    categoria_traduzida = get_category_translation(el_data.get('categoria', 'unknown'))
                    nome_traduzido = get_element_name(symbol)
                    line = (f"{el_data['simbolo']} ({nome_traduzido}) - "
                            f"{tr('periodic_table.atomic_number_short')}: {el_data['numero']}, "
                            f"{tr('periodic_table.category_short')}: {categoria_traduzida}")
                    display_lines.append(line)

            self.selected_elements_text_edit.setText("\n".join(display_lines))

    def confirm_selection(self):
        sorted_elements = sorted(
            list(self.selected_elements),
            key=lambda s: next((el['numero'] for el in ELEMENTOS if el['simbolo'] == s), 0)
        )
        self.selection_confirmed_signal.emit(sorted_elements)
        self.accept()

    def clear_all_selections(self):
        for simbolo in list(self.selected_elements):
            self._toggle_element_selection(simbolo)

        self.selected_elements.clear()
        self._update_selected_elements_display()
        self.selection_cleared_signal.emit()

    def keyPressEvent(self, event):
        """Captura eventos de teclado - Delete limpa todos os elementos selecionados."""
        if event.key() == Qt.Key.Key_Delete:
            self.clear_all_selections()
            event.accept()
        else:
            super().keyPressEvent(event)

    def reject(self):
        for simbolo in list(self.scintillation_timers.keys()):
            self._stop_scintillation(simbolo)
        super().reject()

    def closeEvent(self, event):
        for simbolo in list(self.scintillation_timers.keys()):
            self._stop_scintillation(simbolo)
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    initial_selection = {"Fe", "O"}
    dialog = TabelaPeriodicaDialog(initial_selected_elements=initial_selection)


    def handle_element_toggled(simbolo, is_selected):
        print(f"Elemento Trocado: {simbolo}, Selecionado: {is_selected}")


    def handle_selection_confirmed(selected_list):
        print(f"Seleção Confirmada: {selected_list}")


    def handle_selection_cleared():
        print("Seleção Limpa")


    dialog.element_toggled_signal.connect(handle_element_toggled)
    dialog.selection_confirmed_signal.connect(handle_selection_confirmed)
    dialog.selection_cleared_signal.connect(handle_selection_cleared)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Diálogo aceito.")
    else:
        print("Diálogo cancelado/fechado.")

    sys.exit(app.exec())
