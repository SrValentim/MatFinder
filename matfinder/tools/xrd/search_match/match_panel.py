# -*- coding: utf-8 -*-
"""Aba "Identificação" do PhaseDRX: candidatos do COD e do Materials Project com score.

Usa a lista de picos da aba Picos (mesmo difratograma). O filtro de elementos e
as opções ficam salvos no item, em ``item["analysis"]["search_match"]``; os
candidatos ficam só na sessão (as estruturas baixadas ficam no cache local).
"""

import csv
import logging
import math

import numpy as np
from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QProgressBar, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from scipy import ndimage

from matfinder.core.translator import ptr
from .candidate_search import CandidateSearchSettings, find_candidates
from .candidates import ElementFilter, SearchCancelled, find_mp_api_key
from .element_dialog import ElementFilterDialog, describe_filter
from .scoring import ScoreSettings

logger = logging.getLogger(__name__)

STAGES = {
    "consultando o COD": "Consultando o COD",
    "consultando o Materials Project": "Consultando o Materials Project",
    "baixando estruturas": "Baixando estruturas",
    "simulando e pontuando": "Simulando e pontuando",
    "concluído": "Concluído",
}
COLORS = {"matched": "#1f77b4", "missing": "#d62728", "weak": "#9e9e9e"}


class _NumericItem(QTableWidgetItem):
    """Célula que ordena pelo valor numérico (não pelo texto)."""

    def __init__(self, text, value):
        super().__init__(text)
        self._value = value

    def __lt__(self, other):  # noqa: D105
        if isinstance(other, _NumericItem):
            return self._value < other._value
        return super().__lt__(other)


class _CandidateWorker(QThread):
    progressed = Signal(float, str)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, kwargs, parent=None):
        super().__init__(parent)
        self.kwargs = kwargs
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            result = find_candidates(progress=lambda f, s: self.progressed.emit(f, s),
                                     cancel=lambda: self._cancel, **self.kwargs)
            self.succeeded.emit(result)
        except SearchCancelled:
            self.failed.emit("")
        except ValueError as exc:
            self.failed.emit(ptr(str(exc)))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Falha na busca de candidatos")
            self.failed.emit(str(exc))


def _pct_spin(value, maximum, suffix=" %", decimals=1):
    box = QDoubleSpinBox()
    box.setRange(0.0, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(0.1)
    box.setValue(value)
    box.setSuffix(suffix)
    return box


class MatchPanel(QWidget):
    COLUMNS = ("Score", "Fórmula", "Grupo espacial", "Fonte", "ID", "Linhas", "Posições", "Intensid.",
               "Explicado (%)", "Zero (°)", "Rede", "Notas")

    def __init__(self, host, peaks_panel, parent=None):
        super().__init__(parent)
        self.host = host
        self.peaks_panel = peaks_panel
        self.element_filter = ElementFilter()
        self.result = None
        self.result_item_id = None
        self.selected_key = None
        self._worker = None
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------ interface
    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.item_label = QLabel()
        form.addRow(ptr("Difratograma:"), self.item_label)
        peaks_row = QHBoxLayout()
        self.peaks_label = QLabel()
        self.go_peaks_button = QPushButton(ptr("Ir para a aba Picos"))
        peaks_row.addWidget(self.peaks_label, 1)
        peaks_row.addWidget(self.go_peaks_button)
        form.addRow(ptr("Picos:"), peaks_row)
        elements_row = QHBoxLayout()
        self.filter_label = QLabel()
        self.filter_label.setWordWrap(True)
        self.elements_button = QPushButton(ptr("Escolher elementos..."))
        elements_row.addWidget(self.filter_label, 1)
        elements_row.addWidget(self.elements_button)
        form.addRow(ptr("Elementos:"), elements_row)
        sources_row = QHBoxLayout()
        self.cod_check = QCheckBox("COD")
        self.cod_check.setChecked(True)
        self.mp_check = QCheckBox("Materials Project")
        self.mp_exp_check = QCheckBox(ptr("só experimentais"))
        self.mp_exp_check.setChecked(True)
        self.mp_exp_check.setToolTip(ptr("Só estruturas do Materials Project ligadas a uma entrada experimental (ICSD)."))
        sources_row.addWidget(self.cod_check)
        sources_row.addWidget(self.mp_check)
        sources_row.addWidget(self.mp_exp_check)
        sources_row.addStretch()
        form.addRow(ptr("Fontes:"), sources_row)
        layout.addLayout(form)

        self.advanced_box = QGroupBox(ptr("Avançado"))
        self.advanced_box.setCheckable(True)
        self.advanced_box.setChecked(False)
        self.advanced_widget = QWidget()
        advanced = QFormLayout(self.advanced_widget)
        QVBoxLayout(self.advanced_box).addWidget(self.advanced_widget)
        self.advanced_widget.setVisible(False)
        self.advanced_box.toggled.connect(self.advanced_widget.setVisible)
        defaults = ScoreSettings()
        self.shift_spin = _pct_spin(defaults.shift_range, 1.0, " °", 2)
        self.shift_spin.setSingleStep(0.01)
        self.lattice_spin = _pct_spin(100 * defaults.lattice_tol_exp, 5.0)
        self.dft_spin = _pct_spin(100 * (defaults.dft_max_scale - 1.0), 10.0)
        self.ehull_spin = _pct_spin(0.2, 2.0, " eV/át.", 2)
        self.ehull_spin.setSingleStep(0.05)
        self.max_spin = QSpinBox()
        self.max_spin.setRange(10, 2000)
        self.max_spin.setValue(300)
        self.group_check = QCheckBox(ptr("Agrupar entradas da mesma fase"))
        self.group_check.setChecked(True)
        self.weight_spins = {}
        for key, value in (("w_positions", defaults.w_positions), ("w_reference", defaults.w_reference),
                           ("w_observed", defaults.w_observed), ("w_intensity", defaults.w_intensity)):
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 1.0)
            spin.setSingleStep(0.05)
            spin.setValue(value)
            self.weight_spins[key] = spin
        advanced.addRow(ptr("Deslocamento de zero (±):"), self.shift_spin)
        advanced.addRow(ptr("Variação de rede, experimentais (±):"), self.lattice_spin)
        advanced.addRow(ptr("Expansão de rede aceita no MP (DFT):"), self.dft_spin)
        advanced.addRow(ptr("Estabilidade máxima no MP:"), self.ehull_spin)
        advanced.addRow(ptr("Máximo de candidatos:"), self.max_spin)
        advanced.addRow(self.group_check)
        for key, label in (("w_positions", "Peso das posições:"), ("w_reference", "Peso das reflexões fortes:"),
                           ("w_observed", "Peso dos picos explicados:"), ("w_intensity", "Peso das intensidades:")):
            advanced.addRow(ptr(label), self.weight_spins[key])
        layout.addWidget(self.advanced_box)

        search_row = QHBoxLayout()
        self.search_button = QPushButton(ptr("Buscar candidatos"))
        self.cancel_button = QPushButton(ptr("Cancelar"))
        self.cancel_button.setVisible(False)
        search_row.addWidget(self.search_button, 1)
        search_row.addWidget(self.cancel_button)
        layout.addLayout(search_row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([ptr(c) for c in self.COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(58)  # cabeçalho + seta de ordenação
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        self.errors_label = QLabel()
        self.errors_label.setWordWrap(True)
        self.errors_label.setStyleSheet("color: #d08000;")
        self.errors_label.setVisible(False)
        layout.addWidget(self.errors_label)

        actions = QHBoxLayout()
        self.add_button = QPushButton(ptr("Adicionar à lista do PhaseDRX"))
        self.add_button.setToolTip(ptr("Carrega o CIF do candidato na aba de simulação."))
        self.open_button = QPushButton(ptr("Abrir na fonte"))
        self.export_button = QPushButton(ptr("Exportar CSV..."))
        actions.addWidget(self.add_button)
        actions.addWidget(self.open_button)
        actions.addStretch()
        actions.addWidget(self.export_button)
        layout.addLayout(actions)

        self.go_peaks_button.clicked.connect(self._go_to_peaks)
        self.elements_button.clicked.connect(self.choose_elements)
        self.search_button.clicked.connect(self.start_search)
        self.cancel_button.clicked.connect(self.cancel_search)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.add_button.clicked.connect(self.add_selected_to_list)
        self.open_button.clicked.connect(self.open_selected_source)
        self.export_button.clicked.connect(self.export_csv)
        self.mp_check.toggled.connect(lambda on: self.mp_exp_check.setEnabled(on))

    # ------------------------------------------------------------------ estado
    def current_item(self):
        return self.peaks_panel.current_item() if self.peaks_panel is not None else None

    def refresh(self):
        """Atualiza difratograma, picos, filtro salvo e disponibilidade das fontes."""
        item = self.current_item()
        peak_list = self.peaks_panel.peak_list_of(item) if item is not None else None
        self.item_label.setText(item.get("label", "?") if item else ptr("nenhum (carregue dados na aba Dados Experimentais)"))
        if peak_list is None:
            self.peaks_label.setText(ptr("nenhuma busca de picos neste difratograma"))
        else:
            n_peaks, n_halos = peak_list.counts()
            self.peaks_label.setText(ptr("{} picos").format(n_peaks))
        saved = ((item or {}).get("analysis") or {}).get("search_match") or {}
        if saved.get("filter") and item is not None and item.get("id") != getattr(self, "_filter_item_id", None):
            self.element_filter = ElementFilter.from_dict(saved["filter"])
        self._filter_item_id = item.get("id") if item else None
        self.filter_label.setText(describe_filter(self.element_filter))
        key = find_mp_api_key()
        self.mp_check.setEnabled(key is not None)
        if key is None:
            self.mp_check.setChecked(False)
            self.mp_check.setToolTip(ptr("Configure a chave da API do Materials Project no MatFinder."))
        else:
            self.mp_check.setToolTip(ptr("Chave da API do Materials Project encontrada."))
            if not getattr(self, "_mp_initialized", False):
                self.mp_check.setChecked(True)
        self._mp_initialized = True
        if self.result is not None and (item is None or item.get("id") != self.result_item_id):
            self.result = None
            self.selected_key = None
            self._fill_table()
        self._update_buttons()

    def settings_from_ui(self):
        score = ScoreSettings(
            shift_range=self.shift_spin.value(), lattice_tol_exp=self.lattice_spin.value() / 100.0,
            dft_max_scale=1.0 + self.dft_spin.value() / 100.0,
            **{k: spin.value() for k, spin in self.weight_spins.items()},
        )
        return CandidateSearchSettings(
            use_cod=self.cod_check.isChecked(), use_mp=self.mp_check.isChecked() and self.mp_check.isEnabled(),
            mp_only_experimental=self.mp_exp_check.isChecked(), mp_max_e_above_hull=self.ehull_spin.value(),
            max_candidates=self.max_spin.value(), group_duplicates=self.group_check.isChecked(), score=score,
        )

    def selected_candidate(self):
        if self.result is None or self.selected_key is None:
            return None
        return next((c for c in self.result.candidates if c.key == self.selected_key), None)

    def _update_buttons(self):
        has = self.selected_candidate() is not None
        self.add_button.setEnabled(has)
        self.open_button.setEnabled(has)
        self.export_button.setEnabled(self.result is not None and bool(self.result.candidates))

    # ------------------------------------------------------------------ ações
    def _go_to_peaks(self):
        tabs = getattr(self.host, "tab_widget", None)
        if tabs is not None:
            tabs.setCurrentWidget(self.peaks_panel)

    def choose_elements(self):
        dialog = ElementFilterDialog(self, self.element_filter)
        if dialog.exec():
            self.element_filter = dialog.element_filter()
            self.filter_label.setText(describe_filter(self.element_filter))
            self._save_options()

    def _save_options(self):
        item = self.current_item()
        if item is None:
            return
        item.setdefault("analysis", {})
        item["analysis"]["search_match"] = {"filter": self.element_filter.to_dict(),
                                            "settings": self.settings_from_ui().to_dict()}
        self.host.set_dirty()

    def start_search(self):
        if self._worker is not None:
            return
        item = self.current_item()
        peak_list = self.peaks_panel.peak_list_of(item) if item is not None else None
        if item is None or item.get("data") is None:
            QMessageBox.information(self, ptr("Identificação"), ptr("Carregue um difratograma experimental e escolha-o na aba Picos."))
            return
        if peak_list is None or peak_list.counts()[0] < 2:
            QMessageBox.information(self, ptr("Identificação"), ptr("Busque os picos na aba Picos antes de buscar candidatos."))
            return
        problem = self.element_filter.validate()
        if problem:
            QMessageBox.information(self, ptr("Identificação"), ptr(problem))
            return
        settings = self.settings_from_ui()
        if not (settings.use_cod or settings.use_mp):
            QMessageBox.information(self, ptr("Identificação"), ptr("Escolha pelo menos uma fonte."))
            return
        info = self.host.radiation_info()
        x = np.asarray(item["data"][0], dtype=float)
        self._save_options()
        kwargs = dict(peaks=list(peak_list), element_filter=self.element_filter, wavelength=info["ka1"],
                      two_theta_range=(float(np.min(x)), float(np.max(x))), settings=settings,
                      noise=peak_list.noise_level)
        self._search_item_id = item["id"]
        self._worker = _CandidateWorker(kwargs, self)
        self._worker.progressed.connect(self._on_progress)
        self._worker.succeeded.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._on_finished)
        self._set_busy(True)
        self._worker.start()

    def cancel_search(self):
        if self._worker is not None:
            self._worker.cancel()

    def shutdown(self):
        if self._worker is not None:
            self._worker.cancel()
            self._worker.wait(10000)

    def _set_busy(self, busy):
        self.search_button.setEnabled(not busy)
        self.elements_button.setEnabled(not busy)
        self.cancel_button.setVisible(busy)
        self.progress.setVisible(busy)
        self.progress.setValue(0)

    def _on_progress(self, fraction, stage):
        self.progress.setValue(int(round(100 * fraction)))
        self.progress.setFormat(ptr(STAGES.get(stage, stage)) + " — %p%")

    def _on_finished(self):
        self._worker = None
        self._set_busy(False)

    def _on_failed(self, message):
        if message:
            QMessageBox.warning(self, ptr("Identificação"), ptr("A busca de candidatos falhou:\n{}").format(message))

    def _on_done(self, result):
        self.result = result
        self.result_item_id = self._search_item_id
        self.selected_key = result.candidates[0].key if result.candidates else None
        self._fill_table()
        self.host._redraw_all_plots()

    def add_selected_to_list(self):
        cand = self.selected_candidate()
        if cand is None or not cand.cif:
            return
        self.host.load_cif_from_data(cand.cif, cand.file_name())

    def open_selected_source(self):
        cand = self.selected_candidate()
        if cand is not None:
            QDesktopServices.openUrl(QUrl(cand.url))

    def export_csv(self):
        if self.result is None or not self.result.candidates:
            return
        path, _ = QFileDialog.getSaveFileName(self, ptr("Exportar candidatos"), "candidatos.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["score", "formula", "spacegroup", "source", "id", "lines_found", "lines_expected",
                                 "positions", "reference", "observed", "intensity", "zero_shift_deg",
                                 "lattice_scale", "group_size", "url"])
                for c in self.result.candidates:
                    m = c.match
                    writer.writerow([f"{c.score:.2f}", c.formula, c.spacegroup, c.source, c.source_id, m.lines_found,
                                     m.lines_expected] + [f"{c.subscores[k]:.4f}" for k in
                                                          ("positions", "reference", "observed", "intensity")]
                                    + [f"{m.shift:.3f}", f"{m.lattice_scale:.4f}", 1 + len(c.group_members), c.url])
        except OSError as exc:
            QMessageBox.critical(self, ptr("Exportar candidatos"), ptr("Não foi possível salvar:\n{}").format(exc))

    # ------------------------------------------------------------------ tabela
    def _on_selection(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            cell = self.table.item(rows[0].row(), 0)
            self.selected_key = cell.data(Qt.ItemDataRole.UserRole) if cell is not None else None
        self._update_buttons()
        self.host._redraw_all_plots()

    def _fill_table(self):
        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        candidates = self.result.candidates if self.result is not None else []
        self.table.setRowCount(len(candidates))
        select_row = None
        for r, c in enumerate(candidates):
            m = c.match
            notes = []
            if c.mineral:
                notes.append(c.mineral)
            if c.source == "MP" and c.e_above_hull is not None:
                notes.append(f"E_hull {c.e_above_hull:.3f} eV")
            if c.group_members:
                notes.append(ptr("+{} entradas iguais").format(len(c.group_members)))
            cells = [
                _NumericItem(f"{c.score:.1f}", c.score),
                QTableWidgetItem(c.formula),
                QTableWidgetItem(c.spacegroup),
                QTableWidgetItem(c.source),
                QTableWidgetItem(c.source_id),
                _NumericItem(f"{m.lines_found}/{m.lines_expected}", m.lines_found / max(1, m.lines_expected)),
                _NumericItem(f"{c.subscores['positions']:.2f}", c.subscores["positions"]),
                _NumericItem(f"{c.subscores['intensity']:.2f}", c.subscores["intensity"]),
                _NumericItem(f"{100 * c.subscores['observed']:.0f}", c.subscores["observed"]),
                _NumericItem(f"{m.shift:+.2f}", m.shift),
                _NumericItem(f"{m.lattice_scale:.4f}", m.lattice_scale),
                QTableWidgetItem(" · ".join(notes)),
            ]
            cells[0].setData(Qt.ItemDataRole.UserRole, c.key)
            cells[-1].setToolTip(cells[-1].text())
            if c.group_members:
                cells[0].setToolTip(ptr("Entradas iguais: {}").format(", ".join(c.group_members)))
            for col, cell in enumerate(cells):
                self.table.setItem(r, col, cell)
            if c.key == self.selected_key:
                select_row = r
        self.table.blockSignals(False)
        self.table.setSortingEnabled(True)
        if select_row is not None:
            self.table.selectRow(select_row)
        self._update_summary()
        self._update_buttons()

    def _update_summary(self):
        if self.result is None:
            self.summary_label.setText(ptr("Nenhuma busca de candidatos neste difratograma."))
            self.errors_label.setVisible(False)
            return
        info = self.result.info
        by_source = info.get("by_source", {})
        text = ptr("{} candidatos (COD {}, MP {}) em {} fases").format(
            info.get("n_scored", 0), by_source.get("COD", 0), by_source.get("MP", 0), info.get("n_groups", 0))
        if self.result.candidates:
            best = self.result.candidates[0]
            text += " · " + ptr("melhor: {} ({:.0f})").format(best.label, best.score)
        if info.get("truncated"):
            text += " · " + ptr("lista limitada aos candidatos mais prováveis")
        self.summary_label.setText(text)
        errors = [f"{src}: {ptr(msg)}" for src, msg in self.result.errors.items()]
        self.errors_label.setText(ptr("Avisos das fontes:") + " " + " | ".join(errors) if errors else "")
        self.errors_label.setVisible(bool(errors))


def _baseline(panel, item, x, y):
    """Linha de base sob as reflexões: fundo da busca de picos ou envoltória inferior suavizada."""
    result = panel.peaks_panel.overlay_result(item) if panel.peaks_panel is not None else None
    if result is not None:
        return result.two_theta, result.background
    order = np.argsort(x)
    xs, ys = x[order], y[order]
    step = float(np.median(np.diff(xs))) if len(xs) > 1 else 0.02
    size = max(3, int(round(1.0 / max(step, 1e-6))))
    low = ndimage.minimum_filter1d(ys, size=size, mode="nearest")
    return xs, ndimage.uniform_filter1d(low, size=size, mode="nearest")


def draw_candidate_overlay(ax, item, offset, panel=None):
    """Reflexões do candidato selecionado sobre o difratograma (prévia)."""
    if panel is None or panel.result is None or item.get("id") != panel.result_item_id:
        return
    cand = panel.selected_candidate()
    if cand is None or cand.match is None or item.get("data") is None:
        return
    m = cand.match
    x, y = (np.asarray(v, dtype=float) for v in item["data"])
    bx, by = _baseline(panel, item, x, y)
    matched = {r for r, _, _ in m.pairs}
    groups = {"matched": ([], [], []), "missing": ([], [], []), "weak": ([], [], [])}
    for j, (tt, inten) in enumerate(zip(m.ref_two_theta, m.ref_intensity)):
        base = float(np.interp(tt, bx, by)) + offset
        top = base + m.scale_factor * inten
        if j in matched:
            key = "matched"
        elif m.expected[j]:
            key = "missing"
        else:
            key = "weak"
        groups[key][0].append(tt)
        groups[key][1].append(base)
        groups[key][2].append(top)
    styles = {"matched": dict(lw=1.6, ls="-"), "missing": dict(lw=1.2, ls="--"), "weak": dict(lw=0.8, ls=":")}
    for key, (xs_, ymin, ymax) in groups.items():
        if xs_:
            ax.vlines(xs_, ymin, ymax, colors=COLORS[key], label="_candidate_" + key, zorder=4, **styles[key])
    ax.text(0.01, 0.98, f"{cand.label} · score {cand.score:.0f}", transform=ax.transAxes, ha="left", va="top",
            fontsize=8, color=COLORS["matched"], bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7))
