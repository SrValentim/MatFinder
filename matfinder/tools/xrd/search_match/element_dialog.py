# -*- coding: utf-8 -*-
"""Tabela periódica com três estados por elemento, para o filtro do search-match.

Cada clique avança o estado: nenhum -> obrigatório -> possível -> proibido -> nenhum.
O botão direito volta o elemento para "nenhum". Reaproveita os dados e as cores
da tabela periódica do MatFinder.
"""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from matfinder.core.translator import ptr
from matfinder.tools.periodic_table.tabela_periodica_pyside import (
    CATEGORY_COLORS, DEFAULT_BUTTON_COLOR, ELEMENTOS, get_element_name,
)
from .candidates import ElementFilter

CYCLE = ("neutral", "required", "possible", "forbidden")
STATE_COLORS = {"required": "#2e7d32", "possible": "#1565c0", "forbidden": "#b71c1c"}
STATE_LABELS = {"required": "Obrigatório", "possible": "Possível", "forbidden": "Proibido"}


class _ElementButton(QPushButton):
    right_clicked = Signal()

    def mousePressEvent(self, event):  # noqa: N802 - nome da API do Qt
        if event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
            return
        super().mousePressEvent(event)


class ElementFilterDialog(QDialog):
    """Escolha de elementos obrigatórios, possíveis e proibidos."""

    def __init__(self, parent=None, element_filter=None):
        super().__init__(parent)
        self.setWindowTitle(ptr("Elementos da amostra"))
        flt = element_filter or ElementFilter()
        self.states = {el: "neutral" for el in (e["simbolo"] for e in ELEMENTOS)}
        for el in flt.required:
            self.states[el] = "required"
        for el in flt.possible:
            self.states[el] = "possible"
        for el in flt.forbidden:
            self.states[el] = "forbidden"
        self.buttons = {}
        self._build(flt.allow_others)
        self._update_summary()

    def _build(self, allow_others):
        layout = QVBoxLayout(self)
        legend = QHBoxLayout()
        for state in ("required", "possible", "forbidden"):
            chip = QLabel(ptr(STATE_LABELS[state]))
            chip.setStyleSheet(f"background-color: {STATE_COLORS[state]}; color: white; padding: 3px 8px; border-radius: 3px;")
            legend.addWidget(chip)
        legend.addStretch()
        layout.addLayout(legend)
        help_label = QLabel(ptr("Clique para alternar: obrigatório, possível, proibido, nenhum. O botão direito limpa o elemento."))
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(2)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        rows = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8}
        for data in ELEMENTOS:
            symbol = data["simbolo"]
            button = _ElementButton(symbol)
            button.setFixedSize(QSize(34, 34))
            button.setFont(font)
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            button.setAutoDefault(False)
            button.setToolTip(f"{get_element_name(symbol)} ({symbol})")
            button.clicked.connect(lambda _checked=False, s=symbol: self._cycle(s))
            button.right_clicked.connect(lambda s=symbol: self._set(s, "neutral"))
            column = data["grupo"] - 1
            if data["categoria"] == "lanthanide":
                column = data["numero"] - 57 + 2
            elif data["categoria"] == "actinide":
                column = data["numero"] - 89 + 2
            grid.addWidget(button, rows.get(data["periodo"], data["periodo"] - 1) + (1 if data["periodo"] >= 8 else 0), column)
            self.buttons[symbol] = button
            self._paint(symbol)
        grid.setRowMinimumHeight(7, 8)  # espaço antes dos lantanídeos e actinídeos
        layout.addWidget(grid_widget)

        self.allow_check = QCheckBox(ptr("Permitir outros elementos além dos marcados (sistema aberto)"))
        self.allow_check.setChecked(bool(allow_others))
        self.allow_check.setToolTip(ptr("Desmarcado: o candidato só pode conter elementos obrigatórios ou possíveis."))
        self.allow_check.toggled.connect(self._update_summary)
        layout.addWidget(self.allow_check)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                                   | QDialogButtonBox.StandardButton.Reset)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Reset).setText(ptr("Limpar"))
        buttons.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.clear)
        layout.addWidget(buttons)

    def _paint(self, symbol):
        state = self.states[symbol]
        if state == "neutral":
            category = next((e["categoria"] for e in ELEMENTOS if e["simbolo"] == symbol), "")
            color, text = CATEGORY_COLORS.get(category, DEFAULT_BUTTON_COLOR), "black"
            border = "1px solid #555555"
        else:
            color, text, border = STATE_COLORS[state], "white", "2px solid #111111"
        decoration = "line-through" if state == "forbidden" else "none"
        self.buttons[symbol].setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: {text}; border: {border}; border-radius: 3px;"
            f" text-decoration: {decoration}; }}")

    def _cycle(self, symbol):
        current = CYCLE.index(self.states[symbol])
        self._set(symbol, CYCLE[(current + 1) % len(CYCLE)])

    def _set(self, symbol, state):
        self.states[symbol] = state
        self._paint(symbol)
        self._update_summary()

    def clear(self):
        for symbol in self.states:
            if self.states[symbol] != "neutral":
                self.states[symbol] = "neutral"
                self._paint(symbol)
        self._update_summary()

    def element_filter(self):
        pick = lambda state: [s for s, st in self.states.items() if st == state]  # noqa: E731
        return ElementFilter(required=pick("required"), possible=pick("possible"), forbidden=pick("forbidden"),
                             allow_others=self.allow_check.isChecked())

    def _update_summary(self, *_args):
        flt = self.element_filter()
        self.summary_label.setText(describe_filter(flt))
        problem = flt.validate()
        ok = self.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok) if self.findChild(QDialogButtonBox) else None
        if ok is not None:
            ok.setEnabled(problem is None)
            ok.setToolTip(ptr(problem) if problem else "")


def describe_filter(flt):
    """Resumo legível de um filtro de elementos."""
    dash = "—"
    parts = [
        ptr("Obrigatórios: {}").format(", ".join(flt.required) or dash),
        ptr("Possíveis: {}").format(", ".join(flt.possible) or dash),
        ptr("Proibidos: {}").format(", ".join(flt.forbidden) or dash),
    ]
    if flt.allow_others:
        parts.append(ptr("outros elementos permitidos"))
    return " · ".join(parts)
