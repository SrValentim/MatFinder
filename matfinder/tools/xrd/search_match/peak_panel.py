# -*- coding: utf-8 -*-
"""Painel "Picos" do PhaseDRX: busca robusta, edição manual e tabela de picos.

O painel conversa com a janela do PhaseDRX (host) por poucos pontos:

- ``host.plot_items`` e ``host._find_plot_item_by_id(id)``: itens e dados;
- ``host.radiation_info()``: comprimentos de onda da fonte (aba de simulação);
- ``host._add_state_to_history()``, ``host._redraw_all_plots()``, ``host.set_dirty()``;
- ``host.plot_canvas``: cursor do modo de edição.

A lista de picos de cada difratograma fica em ``item["analysis"]["peak_list"]``
(dicionário JSON). Assim ela entra no projeto salvo e no desfazer/refazer.
"""

import logging
import math

import numpy as np
from PySide6.QtCore import QPoint, Qt, QThread, Signal
from PySide6.QtGui import QColor, QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QMessageBox, QProgressBar, QPushButton, QSlider,
    QTableWidget, QTableWidgetItem, QToolTip, QVBoxLayout, QWidget,
)

from matfinder.core.translator import ptr
from .peak_list import PeakList, data_signature
from .peak_search import PRESETS, PeakSearchSettings, SearchCancelled, fit_peak_at, search_peaks

logger = logging.getLogger(__name__)

COLORS = {"auto": "#d62728", "manual": "#1f77b4", "halo": "#9467bd", "kbeta": "#ff7f0e"}
STAGES = {  # etapas internas da busca -> texto da barra de progresso
    "ruído": "Estimando o ruído",
    "detecção multiescala": "Detectando picos",
    "fundo": "Estimando o fundo",
    "halos": "Ajustando halos",
    "largura dos picos": "Aprendendo a largura dos picos",
    "ajuste de perfis": "Ajustando perfis",
    "concluído": "Concluído",
}


def _fmt(value, digits):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return ""
    return f"{value:.{digits}f}"


class _SearchWorker(QThread):
    """Roda a busca fora da interface, com progresso e cancelamento."""

    progressed = Signal(float, str)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, x, y, settings, lam1, lam2, lamb, parent=None):
        super().__init__(parent)
        self.x, self.y = x, y
        self.settings = settings
        self.lam1, self.lam2, self.lamb = lam1, lam2, lamb
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            result = search_peaks(self.x, self.y, settings=self.settings, wavelength=self.lam1,
                                  wavelength_ka2=self.lam2, wavelength_kb=self.lamb,
                                  progress=lambda f, m: self.progressed.emit(f, m),
                                  cancel=lambda: self._cancel)
            self.succeeded.emit(result)
        except SearchCancelled:
            self.failed.emit("")
        except Exception as exc:  # noqa: BLE001 - qualquer falha vira mensagem ao usuário
            logger.exception("Falha na busca de picos")
            self.failed.emit(str(exc))


def _spin(minimum, maximum, value, decimals, suffix=" °"):
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(10 ** -decimals if decimals < 3 else 0.005)
    box.setValue(value)
    box.setSuffix(suffix)
    return box


class PeakSearchPanel(QWidget):
    """Aba "Picos": busca, edição (adicionar/apagar) e tabela dos picos de um difratograma."""

    COLUMNS = ("2θ (°)", "± 2θ", "d (Å)", "I rel. (%)", "Altura", "Área", "FWHM (°)", "Signif.",
               "Tipo", "Origem", "Obs.")

    def __init__(self, host, parent=None):
        super().__init__(parent)
        self.host = host
        self.edit_mode = None        # None | "add" | "remove"
        self.selected_ids = set()
        self._results = {}           # id do item -> PeakSearchResult (só nesta sessão)
        self._worker = None
        self._search_item_id = None
        self._build_ui()
        self._apply_preset()
        self.refresh_items()
        self.update_radiation()

    # ------------------------------------------------------------------ interface
    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.item_combo = QComboBox()
        form.addRow(ptr("Difratograma:"), self.item_combo)
        self.radiation_label = QLabel()
        self.radiation_label.setToolTip(ptr("A radiação é escolhida na aba de simulação."))
        form.addRow(ptr("Radiação:"), self.radiation_label)
        self.preset_combo = QComboBox()
        self.preset_combo.addItem(ptr("Padrão"), "standard")
        self.preset_combo.addItem(ptr("Dados ruidosos"), "noisy")
        self.preset_combo.addItem(ptr("Picos largos / amorfo"), "broad")
        self.preset_combo.setToolTip(ptr("Ajusta os parâmetros da busca ao tipo de difratograma."))
        form.addRow(ptr("Tipo de dado:"), self.preset_combo)
        sensitivity_row = QHBoxLayout()
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(20, 100)
        self.sensitivity_slider.setPageStep(5)
        self.sensitivity_slider.setToolTip(ptr("Limiar de detecção em desvios-padrão do ruído. Menor = encontra picos mais fracos."))
        self.sensitivity_label = QLabel()
        self.sensitivity_label.setMinimumWidth(48)
        sensitivity_row.addWidget(self.sensitivity_slider, 1)
        sensitivity_row.addWidget(self.sensitivity_label)
        form.addRow(ptr("Limiar:"), sensitivity_row)
        self.ka2_check = QCheckBox(ptr("Dados com Kα2 (dubleto ajustado junto)"))
        self.ka2_check.setChecked(True)
        self.ka2_check.setToolTip(ptr("Ajusta Kα1 e Kα2 juntos e lista só o Kα1. Desmarque para dados com monocromador de Kα1."))
        form.addRow("", self.ka2_check)
        layout.addLayout(form)

        self.advanced_box = QGroupBox(ptr("Avançado"))
        self.advanced_box.setCheckable(True)
        self.advanced_box.setChecked(False)
        self.advanced_widget = QWidget()
        advanced = QFormLayout(self.advanced_widget)
        QVBoxLayout(self.advanced_box).addWidget(self.advanced_widget)
        self.advanced_widget.setVisible(False)
        self.advanced_box.toggled.connect(self.advanced_widget.setVisible)
        self.min_fwhm_spin = _spin(0.005, 1.0, 0.02, 3)
        self.max_fwhm_spin = _spin(0.1, 20.0, 2.0, 2)
        self.bg_window_spin = _spin(0.0, 40.0, 0.0, 1)
        self.bg_window_spin.setSpecialValueText(ptr("automática"))
        self.halo_spin = _spin(0.5, 20.0, 2.0, 1)
        self.spikes_check = QCheckBox(ptr("Remover spikes de um ponto"))
        self.kbeta_check = QCheckBox(ptr("Marcar possíveis picos de Kβ"))
        self.width_check = QCheckBox(ptr("Larguras seguem uma tendência suave com 2θ"))
        advanced.addRow(ptr("FWHM mínima:"), self.min_fwhm_spin)
        advanced.addRow(ptr("FWHM máxima:"), self.max_fwhm_spin)
        advanced.addRow(ptr("Janela do fundo:"), self.bg_window_spin)
        advanced.addRow(ptr("Halo a partir de:"), self.halo_spin)
        advanced.addRow(self.spikes_check)
        advanced.addRow(self.kbeta_check)
        advanced.addRow(self.width_check)
        layout.addWidget(self.advanced_box)

        search_row = QHBoxLayout()
        self.search_button = QPushButton(ptr("Buscar picos"))
        self.search_button.setDefault(True)
        self.cancel_button = QPushButton(ptr("Cancelar"))
        self.cancel_button.setVisible(False)
        self.clear_button = QPushButton(ptr("Limpar picos"))
        search_row.addWidget(self.search_button, 1)
        search_row.addWidget(self.cancel_button)
        search_row.addWidget(self.clear_button)
        layout.addLayout(search_row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        edit_row = QHBoxLayout()
        self.add_button = QPushButton(ptr("Adicionar pico"))
        self.add_button.setCheckable(True)
        self.add_button.setToolTip(ptr("Clique no gráfico onde está o pico. Esc encerra."))
        self.remove_button = QPushButton(ptr("Apagar pico"))
        self.remove_button.setCheckable(True)
        self.remove_button.setToolTip(ptr("Clique perto do marcador. Apaga só o pico, nunca os dados. Esc encerra."))
        self.show_fit_check = QCheckBox(ptr("Mostrar ajuste e fundo"))
        edit_row.addWidget(self.add_button)
        edit_row.addWidget(self.remove_button)
        edit_row.addStretch()
        edit_row.addWidget(self.show_fit_check)
        layout.addLayout(edit_row)

        self.stale_label = QLabel(ptr("Os dados mudaram depois da busca. Busque de novo para atualizar alturas e áreas."))
        self.stale_label.setWordWrap(True)
        self.stale_label.setStyleSheet("color: #d08000;")
        self.stale_label.setVisible(False)
        layout.addWidget(self.stale_label)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([ptr(c) for c in self.COLUMNS])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        bottom = QHBoxLayout()
        self.delete_selected_button = QPushButton(ptr("Apagar selecionados"))
        self.restore_button = QPushButton(ptr("Restaurar apagados"))
        self.restore_button.setToolTip(ptr("Libera os picos apagados e busca de novo."))
        self.export_button = QPushButton(ptr("Exportar CSV..."))
        bottom.addWidget(self.delete_selected_button)
        bottom.addWidget(self.restore_button)
        bottom.addStretch()
        bottom.addWidget(self.export_button)
        layout.addLayout(bottom)

        self.item_combo.currentIndexChanged.connect(self._on_item_changed)
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        self.sensitivity_slider.valueChanged.connect(self._update_sensitivity_label)
        self.search_button.clicked.connect(self.start_search)
        self.cancel_button.clicked.connect(self.cancel_search)
        self.clear_button.clicked.connect(self.clear_peaks)
        self.add_button.toggled.connect(lambda on: self._set_edit_mode("add", on))
        self.remove_button.toggled.connect(lambda on: self._set_edit_mode("remove", on))
        self.show_fit_check.toggled.connect(lambda _on: self.host._redraw_all_plots())
        self.table.itemSelectionChanged.connect(self._on_table_selection)
        self.delete_selected_button.clicked.connect(self.delete_selected)
        self.restore_button.clicked.connect(self.restore_deleted)
        self.export_button.clicked.connect(self.export_csv)
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.table)
        delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete_shortcut.activated.connect(self.delete_selected)
        escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self.host)
        escape_shortcut.activated.connect(self.exit_edit_mode)

    # ------------------------------------------------------------------ itens e radiação
    def current_item_id(self):
        return self.item_combo.currentData()

    def current_item(self):
        item_id = self.current_item_id()
        return self.host._find_plot_item_by_id(item_id) if item_id else None

    def refresh_items(self):
        """Repopula a lista de difratogramas (chamado quando a lista do PhaseDRX muda)."""
        previous = self.current_item_id()
        items = [p for p in getattr(self.host, "plot_items", []) if p.get("type") == "experimental"]
        self.item_combo.blockSignals(True)
        self.item_combo.clear()
        for item in items:
            self.item_combo.addItem(item.get("label", "?"), item.get("id"))
        index = self.item_combo.findData(previous) if previous else -1
        if index < 0 and items:
            selected = self._selected_experimental_id()
            index = self.item_combo.findData(selected) if selected else 0
        self.item_combo.setCurrentIndex(max(index, 0) if items else -1)
        self.item_combo.blockSignals(False)
        self._on_item_changed()

    def _selected_experimental_id(self):
        widget = getattr(self.host, "exp_list_widget", None)
        if widget is None or not widget.selectedItems():
            return None
        return widget.selectedItems()[0].data(Qt.ItemDataRole.UserRole)

    def update_radiation(self):
        info = self._radiation()
        if info["ka1"] is None:
            text = ptr("comprimento de onda inválido")
        elif info["anode"] is None:
            text = ptr("λ = {} Å (personalizado)").format(f"{info['ka1']:.5f}")
        else:
            text = ptr("{} Kα1 = {} Å").format(info["anode"], f"{info['ka1']:.5f}")
        self.radiation_label.setText(text)
        self.ka2_check.setEnabled(info["ka2"] is not None)

    def _radiation(self):
        getter = getattr(self.host, "radiation_info", None)
        if getter is None:
            return {"anode": None, "ka1": None, "ka2": None, "kb": None}
        return getter()

    # ------------------------------------------------------------------ parâmetros
    def _apply_preset(self, *_args):
        preset = PRESETS.get(self.preset_combo.currentData() or "standard", PeakSearchSettings())
        self.sensitivity_slider.setValue(int(round(preset.sensitivity * 10)))
        self.min_fwhm_spin.setValue(preset.min_fwhm)
        self.max_fwhm_spin.setValue(preset.broad_max_fwhm if preset.broad_mode else preset.max_fwhm)
        self.bg_window_spin.setValue(preset.background_window)
        self.halo_spin.setValue(preset.halo_min_fwhm)
        self.spikes_check.setChecked(preset.remove_spikes)
        self.kbeta_check.setChecked(preset.flag_kbeta)
        self.width_check.setChecked(preset.width_prior)
        self._update_sensitivity_label()

    def _update_sensitivity_label(self, *_args):
        self.sensitivity_label.setText(f"{self.sensitivity_slider.value() / 10:.1f} σ")

    def settings_from_ui(self):
        preset = PRESETS.get(self.preset_combo.currentData() or "standard", PeakSearchSettings())
        data = preset.to_dict()
        data.update(
            sensitivity=self.sensitivity_slider.value() / 10.0,
            min_fwhm=self.min_fwhm_spin.value(),
            background_window=self.bg_window_spin.value(),
            halo_min_fwhm=self.halo_spin.value(),
            remove_spikes=self.spikes_check.isChecked(),
            flag_kbeta=self.kbeta_check.isChecked(),
            width_prior=self.width_check.isChecked(),
            ka2=self.ka2_check.isChecked() and self.ka2_check.isEnabled(),
        )
        if preset.broad_mode:
            data["broad_max_fwhm"] = self.max_fwhm_spin.value()
        else:
            data["max_fwhm"] = self.max_fwhm_spin.value()
        return PeakSearchSettings.from_dict(data)

    # ------------------------------------------------------------------ lista de picos do item
    @staticmethod
    def peak_list_of(item):
        data = (item or {}).get("analysis", {}).get("peak_list") if item else None
        return PeakList.from_dict(data) if data else None

    @staticmethod
    def _store(item, peak_list):
        item.setdefault("analysis", {})
        item["analysis"]["peak_list"] = peak_list.to_dict() if peak_list is not None else None

    def _commit(self, item, peak_list):
        """Grava a lista no item (o histórico já foi registrado) e atualiza a tela."""
        self._store(item, peak_list)
        self.refresh_table()
        self.host._redraw_all_plots()
        self.host.set_dirty()

    # ------------------------------------------------------------------ busca
    def start_search(self):
        item = self.current_item()
        if item is None or item.get("data") is None:
            QMessageBox.information(self, ptr("Busca de picos"),
                                    ptr("Carregue um difratograma experimental e escolha-o na lista."))
            return
        if self._worker is not None:
            return
        info = self._radiation()
        settings = self.settings_from_ui()
        x, y = (np.asarray(v, dtype=float).copy() for v in item["data"])
        self._search_item_id = item["id"]
        self._worker = _SearchWorker(x, y, settings, info["ka1"], info["ka2"] if settings.ka2 else None,
                                     info["kb"], self)
        self._worker.progressed.connect(self._on_progress)
        self._worker.succeeded.connect(self._on_search_done)
        self._worker.failed.connect(self._on_search_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._set_busy(True)
        self._worker.start()

    def cancel_search(self):
        if self._worker is not None:
            self._worker.cancel()

    def shutdown(self):
        """Interrompe uma busca em andamento (fechamento da janela)."""
        if self._worker is not None:
            self._worker.cancel()
            self._worker.wait(5000)

    def _set_busy(self, busy):
        self.search_button.setEnabled(not busy)
        self.clear_button.setEnabled(not busy)
        self.item_combo.setEnabled(not busy)
        self.cancel_button.setVisible(busy)
        self.progress.setVisible(busy)
        self.progress.setValue(0)

    def _on_progress(self, fraction, stage):
        self.progress.setValue(int(round(100 * fraction)))
        self.progress.setFormat(ptr(STAGES.get(stage, stage)) + " — %p%")

    def _on_worker_finished(self):
        self._worker = None
        self._set_busy(False)

    def _on_search_done(self, result):
        item = self.host._find_plot_item_by_id(self._search_item_id)
        if item is None or item.get("data") is None:
            return
        info = self._radiation()
        self.host._add_state_to_history()
        peak_list = self.peak_list_of(item) or PeakList()
        peak_list.replace_auto(result.peaks)
        peak_list.wavelength = info["ka1"]
        peak_list.settings = result.info.get("settings", {})
        peak_list.data_signature = data_signature(*item["data"])
        peak_list.noise_level = result.info.get("noise_median")
        peak_list.crystallinity = result.crystallinity
        self._results[item["id"]] = result
        self.selected_ids.clear()
        if self.current_item_id() != item["id"]:
            index = self.item_combo.findData(item["id"])
            if index >= 0:
                self.item_combo.setCurrentIndex(index)
        self._commit(item, peak_list)

    def _on_search_failed(self, message):
        if message:
            QMessageBox.critical(self, ptr("Busca de picos"), ptr("A busca falhou:\n{}").format(message))

    def clear_peaks(self):
        item = self.current_item()
        if item is None or self.peak_list_of(item) is None:
            return
        self.host._add_state_to_history()
        self._results.pop(item["id"], None)
        self.selected_ids.clear()
        self._commit(item, None)

    def restore_deleted(self):
        item = self.current_item()
        peak_list = self.peak_list_of(item)
        if peak_list is None or not peak_list.suppressed:
            return
        self.host._add_state_to_history()
        peak_list.restore_suppressed()
        self._store(item, peak_list)
        self.start_search()

    # ------------------------------------------------------------------ edição pelo gráfico
    def _set_edit_mode(self, mode, on):
        other = self.remove_button if mode == "add" else self.add_button
        if on:
            other.blockSignals(True)
            other.setChecked(False)
            other.blockSignals(False)
            self.edit_mode = mode
        elif self.edit_mode == mode:
            self.edit_mode = None
        canvas = getattr(self.host, "plot_canvas", None)
        if canvas is not None:
            shape = Qt.CursorShape.CrossCursor if self.edit_mode else Qt.CursorShape.ArrowCursor
            canvas.setCursor(QCursor(shape))

    def exit_edit_mode(self):
        for button in (self.add_button, self.remove_button):
            if button.isChecked():
                button.setChecked(False)

    def handle_plot_click(self, x_click):
        """Clique no gráfico durante a edição. Devolve True se o clique foi usado."""
        if not self.edit_mode or x_click is None:
            return False
        item = self.current_item()
        if item is None or item.get("data") is None:
            self._tip(ptr("Escolha um difratograma na aba Picos."))
            return True
        if self.edit_mode == "add":
            self._add_peak_at(item, float(x_click))
        else:
            self._remove_peak_near(item, float(x_click))
        return True

    def _add_peak_at(self, item, x_click):
        x, y = (np.asarray(v, dtype=float) for v in item["data"])
        info = self._radiation()
        settings = self.settings_from_ui()
        peak_list = self.peak_list_of(item) or PeakList(wavelength=info["ka1"])
        result = self._results.get(item["id"])
        background = None
        if result is not None and peak_list.data_signature == data_signature(x, y):
            background = result.background
        try:
            peak = fit_peak_at(x, y, x_click, settings=settings, wavelength=info["ka1"],
                               wavelength_ka2=info["ka2"] if settings.ka2 else None,
                               existing=list(peak_list), background=background)
        except ValueError:
            self._tip(ptr("Clique dentro da faixa de dados."))
            return
        self.host._add_state_to_history()
        peak_list.add(peak)
        if peak_list.wavelength is None:
            peak_list.wavelength = info["ka1"]
        if peak_list.data_signature is None:
            peak_list.data_signature = data_signature(x, y)
        self.selected_ids = {peak.id}
        self._commit(item, peak_list)

    def _remove_peak_near(self, item, x_click):
        peak_list = self.peak_list_of(item)
        if peak_list is None or not len(peak_list):
            self._tip(ptr("Este difratograma ainda não tem picos."))
            return
        nearest = peak_list.nearest(x_click)
        span = np.ptp(self.host.plot_canvas.axes.get_xlim()) if hasattr(self.host, "plot_canvas") else 10.0
        if abs(nearest.two_theta - x_click) > max(0.75 * nearest.fwhm, 0.01 * span):
            self._tip(ptr("Nenhum pico perto do clique."))
            return
        self.host._add_state_to_history()
        peak_list.remove([nearest.id])
        self.selected_ids.discard(nearest.id)
        self._commit(item, peak_list)

    def delete_selected(self):
        item = self.current_item()
        peak_list = self.peak_list_of(item)
        ids = self._table_selected_ids()
        if peak_list is None or not ids:
            return
        self.host._add_state_to_history()
        peak_list.remove(ids)
        self.selected_ids.clear()
        self._commit(item, peak_list)

    def export_csv(self):
        item = self.current_item()
        peak_list = self.peak_list_of(item)
        if peak_list is None or not len(peak_list):
            QMessageBox.information(self, ptr("Exportar picos"), ptr("Não há picos para exportar."))
            return
        default = f"{item.get('label', 'picos')}_picos.csv"
        path, _ = QFileDialog.getSaveFileName(self, ptr("Exportar picos"), default, "CSV (*.csv)")
        if not path:
            return
        try:
            peak_list.write_csv(path)
        except OSError as exc:
            QMessageBox.critical(self, ptr("Exportar picos"), ptr("Não foi possível salvar:\n{}").format(exc))

    def _tip(self, text):
        QToolTip.showText(QCursor.pos() + QPoint(12, 12), text, self)

    # ------------------------------------------------------------------ tabela
    def _on_item_changed(self, *_args):
        self.selected_ids.clear()
        self.refresh_table()
        if hasattr(self.host, "_redraw_all_plots") and getattr(self.host, "plot_canvas", None) is not None:
            self.host._redraw_all_plots()

    def _table_selected_ids(self):
        ids = []
        for index in self.table.selectionModel().selectedRows():
            cell = self.table.item(index.row(), 0)
            if cell is not None:
                ids.append(cell.data(Qt.ItemDataRole.UserRole))
        return ids

    def _on_table_selection(self):
        self.selected_ids = set(self._table_selected_ids())
        self.host._redraw_all_plots()

    def refresh_table(self):
        item = self.current_item()
        peak_list = self.peak_list_of(item)
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        if peak_list is not None:
            rows = peak_list.rows()
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                flags = ptr("possível Kβ") if "kbeta" in row["flags"].split(",") else ""
                values = [
                    _fmt(row["two_theta"], 4), _fmt(row["two_theta_err"], 4), _fmt(row["d"], 4),
                    _fmt(row["rel_intensity"], 1), _fmt(row["height"], 1), _fmt(row["area"], 1),
                    _fmt(row["fwhm"], 3), _fmt(row["significance"], 1),
                    ptr("halo") if row["kind"] == "halo" else ptr("pico"),
                    ptr("manual") if row["origin"] == "manual" else ptr("auto"), flags,
                ]
                for c, value in enumerate(values):
                    cell = QTableWidgetItem(value)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                                          if c < 8 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    if c == 0:
                        cell.setData(Qt.ItemDataRole.UserRole, row["id"])
                    if row["kind"] == "halo":
                        cell.setForeground(QColor(COLORS["halo"]))
                    elif row["origin"] == "manual":
                        cell.setForeground(QColor(COLORS["manual"]))
                    self.table.setItem(r, c, cell)
                    if row["id"] in self.selected_ids:
                        cell.setSelected(True)
        self.table.blockSignals(False)
        self._update_summary(item, peak_list)

    def _update_summary(self, item, peak_list):
        stale = False
        if peak_list is not None and item is not None and item.get("data") is not None:
            stale = bool(peak_list.data_signature) and peak_list.data_signature != data_signature(*item["data"])
        self.stale_label.setVisible(stale)
        n_suppressed = len(peak_list.suppressed) if peak_list is not None else 0
        self.restore_button.setEnabled(n_suppressed > 0)
        self.restore_button.setText(ptr("Restaurar apagados") + (f" ({n_suppressed})" if n_suppressed else ""))
        has_peaks = peak_list is not None and len(peak_list) > 0
        for button in (self.delete_selected_button, self.export_button):
            button.setEnabled(has_peaks)
        if peak_list is None:
            self.summary_label.setText(ptr("Nenhuma busca feita neste difratograma."))
            return
        peaks, halos = peak_list.counts()
        parts = [ptr("{} picos").format(peaks)]
        if halos:
            parts.append(ptr("{} halo(s)").format(halos))
        if peak_list.crystallinity is not None:
            parts.append(ptr("cristalinidade {}%").format(f"{100 * peak_list.crystallinity:.0f}"))
        if peak_list.noise_level:
            parts.append(ptr("ruído ≈ {}").format(f"{peak_list.noise_level:.3g}"))
        self.summary_label.setText(" · ".join(parts))

    # ------------------------------------------------------------------ desenho no gráfico
    def overlay_result(self, item):
        """Resultado da última busca deste item, se os dados não mudaram desde então."""
        result = self._results.get(item.get("id"))
        peak_list = self.peak_list_of(item)
        if result is None or peak_list is None or item.get("data") is None:
            return None
        if peak_list.data_signature != data_signature(*item["data"]):
            return None
        return result


def draw_peak_overlays(ax, item, offset, panel=None):
    """Marcadores dos picos de um item experimental (e, se pedido, ajuste e fundo)."""
    peak_list = PeakSearchPanel.peak_list_of(item)
    if peak_list is None or item.get("data") is None:
        return
    x, y = (np.asarray(v, dtype=float) for v in item["data"])
    if len(x) < 2:
        return
    order = np.argsort(x)
    xs, ys = x[order], y[order]
    lift = 0.03 * (float(np.ptp(ys)) or 1.0)
    is_current = panel is not None and panel.current_item_id() == item.get("id")
    selected = panel.selected_ids if is_current else set()

    if is_current and panel.show_fit_check.isChecked():
        result = panel.overlay_result(item)
        if result is not None:
            ax.plot(result.two_theta, result.model + offset, "--", color=COLORS["auto"], lw=0.8,
                    alpha=0.85, label="_peak_fit", zorder=4)
            ax.plot(result.two_theta, result.background + offset, ":", color="#2ca02c", lw=0.9,
                    label="_peak_background", zorder=4)

    styles = {}
    for p in peak_list:
        if p.kind == "halo":
            key = ("D", COLORS["halo"])
        elif p.origin == "manual":
            key = ("v", COLORS["manual"])
        elif "kbeta" in p.flags:
            key = ("v", COLORS["kbeta"])
        else:
            key = ("v", COLORS["auto"])
        y_mark = float(np.interp(p.two_theta, xs, ys)) + offset + lift
        styles.setdefault(key, ([], []))
        styles[key][0].append(p.two_theta)
        styles[key][1].append(y_mark)
        if p.id in selected:
            ax.axvline(p.two_theta, color="0.3", lw=0.8, ls="--", alpha=0.6, label="_peak_selected_line", zorder=3)
            ax.plot([p.two_theta], [y_mark], marker="o", ms=12, mfc="none", mec="black", mew=1.4,
                    linestyle="none", label="_peak_selected", zorder=6)
    for (marker, color), (px, py) in styles.items():
        ax.plot(px, py, linestyle="none", marker=marker, ms=6, color=color, mec="white", mew=0.5,
                label="_peaks", zorder=5)
