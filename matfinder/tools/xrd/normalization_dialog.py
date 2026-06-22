# normalization_dialog.py
# Diálogo e funções para normalização de dados de DRX
# Parte do módulo MatFinder - PhaseDRX Tool

import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QRadioButton, QButtonGroup, QDialogButtonBox, QGroupBox, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from matfinder.core.translator import ptr


class NormalizationDialog(QDialog):
    """
    Diálogo para seleção do método de normalização de dados experimentais de DRX.

    Opções disponíveis:
    - Normalizar [0, 1]: Escala os dados para o intervalo [0, 1]
    - Dividir pelo Máximo: Divide todos os valores pelo valor máximo
    - Dividir pelo Mínimo: Divide todos os valores pelo valor mínimo
    - Dividir pela Mediana: Divide todos os valores pela mediana
    """

    normalization_applied = Signal(str)  # Emite o método selecionado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(ptr("Normalização de Dados"))
        self.setModal(True)
        self.selected_method = None
        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)

        # Descrição
        description = QLabel(
            ptr("Selecione o método de normalização para os dados experimentais selecionados:")
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Grupo de opções de normalização
        options_group = QGroupBox(ptr("Métodos de Normalização"))
        options_layout = QVBoxLayout(options_group)

        # Criar grupo de botões de rádio
        self.button_group = QButtonGroup(self)

        # Opção 1: Normalizar [0, 1]
        self.radio_normalize_01 = QRadioButton(ptr("Normalizar [0, 1]"))
        self.radio_normalize_01.setToolTip(
            ptr("Escala os dados para o intervalo [0, 1].\nFórmula: (y - y_min) / (y_max - y_min)")
        )
        self.radio_normalize_01.setChecked(True)  # Padrão
        self.button_group.addButton(self.radio_normalize_01, 0)
        options_layout.addWidget(self.radio_normalize_01)

        # Opção 2: Dividir pelo Máximo
        self.radio_div_max = QRadioButton(ptr("Dividir pelo Máximo"))
        self.radio_div_max.setToolTip(
            ptr("Divide todos os valores pelo valor máximo.\nFórmula: y / y_max")
        )
        self.button_group.addButton(self.radio_div_max, 1)
        options_layout.addWidget(self.radio_div_max)

        # Opção 3: Dividir pelo Mínimo
        self.radio_div_min = QRadioButton(ptr("Dividir pelo Mínimo"))
        self.radio_div_min.setToolTip(
            ptr("Divide todos os valores pelo valor mínimo.\nFórmula: y / y_min")
        )
        self.button_group.addButton(self.radio_div_min, 2)
        options_layout.addWidget(self.radio_div_min)

        # Opção 4: Dividir pela Mediana
        self.radio_div_median = QRadioButton(ptr("Dividir pela Mediana"))
        self.radio_div_median.setToolTip(
            ptr("Divide todos os valores pela mediana.\nFórmula: y / mediana(y)")
        )
        self.button_group.addButton(self.radio_div_median, 3)
        options_layout.addWidget(self.radio_div_median)

        layout.addWidget(options_group)

        # Botões de ação
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.setMinimumWidth(400)

    def get_selected_method(self):
        """Retorna o método de normalização selecionado."""
        checked_id = self.button_group.checkedId()

        methods = {
            0: "normalize_01",
            1: "divide_by_max",
            2: "divide_by_min",
            3: "divide_by_median"
        }

        return methods.get(checked_id, "normalize_01")


def normalize_data(y_data, method="normalize_01"):
    """
    Normaliza os dados de acordo com o método especificado.

    Args:
        y_data (np.ndarray): Array com os dados de intensidade (eixo Y)
        method (str): Método de normalização
            - "normalize_01": Normaliza para [0, 1]
            - "divide_by_max": Divide pelo máximo
            - "divide_by_min": Divide pelo mínimo
            - "divide_by_median": Divide pela mediana

    Returns:
        np.ndarray: Array com os dados normalizados

    Raises:
        ValueError: Se o método for inválido ou os dados não permitirem a normalização
    """
    y_data = np.array(y_data, dtype=float)

    if method == "normalize_01":
        # Normalizar para [0, 1]
        min_val = y_data.min()
        max_val = y_data.max()
        range_val = max_val - min_val

        # Usar tolerância numérica ao invés de comparação exata
        if range_val < 1e-10:
            raise ValueError(ptr("Os dados não podem ser normalizados [0,1]: máximo igual ao mínimo (dados constantes)."))

        normalized = (y_data - min_val) / range_val
        return normalized

    elif method == "divide_by_max":
        # Dividir pelo máximo
        max_val = y_data.max()

        if abs(max_val) < 1e-10:
            raise ValueError(ptr("Os dados não podem ser normalizados: máximo é essencialmente zero."))

        normalized = y_data / max_val
        return normalized

    elif method == "divide_by_min":
        # Dividir pelo mínimo
        min_val = y_data.min()

        if abs(min_val) < 1e-10:
            raise ValueError(ptr("Os dados não podem ser normalizados: mínimo é essencialmente zero."))

        normalized = y_data / min_val
        return normalized

    elif method == "divide_by_median":
        # Dividir pela mediana
        median_val = np.median(y_data)

        if abs(median_val) < 1e-10:
            raise ValueError(ptr("Os dados não podem ser normalizados: mediana é essencialmente zero."))

        normalized = y_data / median_val
        return normalized

    else:
        raise ValueError(ptr("Método de normalização inválido: {}").format(method))


def get_method_description(method):
    """
    Retorna uma descrição amigável do método de normalização.

    Args:
        method (str): Método de normalização

    Returns:
        str: Descrição do método
    """
    descriptions = {
        "normalize_01": "Normalização [0, 1]",
        "divide_by_max": "Divisão pelo Máximo",
        "divide_by_min": "Divisão pelo Mínimo",
        "divide_by_median": "Divisão pela Mediana"
    }

    from matfinder.core.translator import ptr
    return ptr(descriptions.get(method, "Método Desconhecido"))


def normalize_by_peak(x_data, y_data, peak_x, window_size=0.5):
    """
    Normaliza os dados dividindo pela intensidade de um pico específico.

    Args:
        x_data (np.ndarray): Array com valores de 2θ
        y_data (np.ndarray): Array com intensidades
        peak_x (float): Posição 2θ do pico de interesse
        window_size (float): Janela em graus ao redor do pico para buscar o máximo

    Returns:
        tuple: (y_normalizado, intensidade_do_pico)

    Raises:
        ValueError: Se o pico não for encontrado ou tiver intensidade zero
    """
    x_data = np.array(x_data)
    y_data = np.array(y_data)

    # Encontrar índices na janela ao redor do pico
    mask = (x_data >= peak_x - window_size) & (x_data <= peak_x + window_size)

    if not np.any(mask):
        raise ValueError(ptr("Nenhum dado encontrado na região do pico (2θ = {:.2f}°)").format(peak_x))

    # Encontrar o máximo na janela
    y_in_window = y_data[mask]
    peak_intensity = np.max(y_in_window)

    if peak_intensity <= 0:
        raise ValueError(ptr("Intensidade do pico é zero ou negativa (2θ = {:.2f}°)").format(peak_x))

    # Normalizar dividindo pela intensidade do pico
    y_normalized = y_data / peak_intensity

    return y_normalized, peak_intensity


class NormalizeByPeakConfirmDialog(QDialog):
    """
    Diálogo para confirmar se deve normalizar todos os experimentais pelo pico selecionado.
    """

    def __init__(self, selected_label, peak_position, other_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle(ptr("Normalizar por Pico Específico"))
        self.setModal(True)
        self.normalize_others = False
        self._setup_ui(selected_label, peak_position, other_count)

    def _setup_ui(self, selected_label, peak_position, other_count):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)

        # Título
        title_label = QLabel(ptr("Normalização por Pico Específico"))
        title_font = title_label.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Informações sobre a normalização
        info_text = (
            ptr("<b>Arquivo selecionado:</b> {}<br><b>Posição do pico:</b> 2θ = {:.3f}°<br><br>O arquivo selecionado será normalizado dividindo todas as intensidades pela intensidade deste pico.").format(selected_label, peak_position)
        )
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Separador
        layout.addSpacing(10)

        # Pergunta sobre os outros arquivos
        if other_count > 0:
            question_label = QLabel(
                ptr("<b>Existem {} outro(s) arquivo(s) experimental(is) carregado(s).</b><br>Deseja normalizar todos eles usando o mesmo pico como referência?").format(other_count)
            )
            question_label.setWordWrap(True)
            layout.addWidget(question_label)

            # Grupo de opções
            options_group = QGroupBox(ptr("Opções de Normalização"))
            options_layout = QVBoxLayout(options_group)

            self.button_group = QButtonGroup(self)

            # Opção 1: Normalizar apenas o selecionado
            self.radio_only_selected = QRadioButton(
                ptr("Normalizar apenas '{}' por este pico").format(selected_label)
            )
            self.radio_only_selected.setToolTip(
                ptr("Apenas o arquivo selecionado será normalizado pelo pico.\nOs outros arquivos permanecerão inalterados.")
            )
            self.radio_only_selected.setChecked(True)
            self.button_group.addButton(self.radio_only_selected, 0)
            options_layout.addWidget(self.radio_only_selected)

            # Opção 2: Normalizar todos pelo mesmo pico
            self.radio_normalize_all = QRadioButton(
                ptr("Normalizar TODOS os experimentais pelo pico em 2θ = {:.3f}°").format(peak_position)
            )
            self.radio_normalize_all.setToolTip(
                ptr("Todos os arquivos experimentais serão normalizados usando\na intensidade do pico na mesma posição 2θ de cada arquivo.")
            )
            self.button_group.addButton(self.radio_normalize_all, 1)
            options_layout.addWidget(self.radio_normalize_all)

            layout.addWidget(options_group)
        else:
            # Não há outros arquivos
            note_label = QLabel(
                ptr("<i>Este é o único arquivo experimental carregado.</i>")
            )
            layout.addWidget(note_label)

        # Botões de ação
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.setMinimumWidth(500)

    def should_normalize_others(self):
        """Retorna True se deve normalizar todos os experimentais."""
        if hasattr(self, 'button_group'):
            return self.button_group.checkedId() == 1
        return False
