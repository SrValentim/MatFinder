# -*- coding: utf-8 -*-
"""Aba "Identificação" do PhaseDRX: candidatos do COD e do Materials Project com score.

Usa a lista de picos da aba Picos (mesmo difratograma). O ciclo é o do HighScore:
aceitar um candidato ajusta juntas as escalas das fases aceitas, e os outros
candidatos são pontuados de novo contra a intensidade que sobrou nos picos.

Ficam salvos no item, em ``item["analysis"]["search_match"]``: o filtro de
elementos, as opções e as fases aceitas (com o CIF, para reabrir o projeto sem
rede). Os candidatos ficam só na sessão; as estruturas baixadas ficam no cache.
"""

import csv
import hashlib
import logging
import uuid

import numpy as np
from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QMessageBox, QProgressBar, QPushButton, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)
from scipy import ndimage

from matfinder.core.translator import ptr
from .candidate_search import CandidateSearchSettings, find_candidates
from .candidates import ElementFilter, SearchCancelled, find_mp_api_key, group_duplicates
from .element_dialog import ElementFilterDialog, describe_filter
from .phase_analysis import AcceptedPhase, analyze, next_color, peak_list_is_poor, rescore
from .quantify import build_profile_context, rir_of, semi_quant
from .scoring import ObservedPeaks, ScoreSettings, reference_pattern, score_candidate

logger = logging.getLogger(__name__)

STAGES = {
    "preparando o perfil": "Preparando o perfil",
    "consultando o COD": "Consultando o COD",
    "consultando o Materials Project": "Consultando o Materials Project",
    "baixando estruturas": "Baixando estruturas",
    "simulando e pontuando": "Simulando e pontuando",
    "concluído": "Concluído",
}
COLORS = {"matched": "#1f77b4", "missing": "#d62728", "weak": "#9e9e9e"}
UNEXPLAINED_COLOR = "#d62728"
SCORE_MODE_LABELS = (("auto", "Automático"), ("peaks", "Picos"), ("profile", "Perfil"), ("both", "Picos e perfil"))
USED_MODE_NAMES = {"peaks": "picos", "profile": "perfil", "both": "picos e perfil"}


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

    def __init__(self, kwargs, profile_args=None, parent=None):
        super().__init__(parent)
        self.kwargs = kwargs
        self.profile_args = profile_args
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            kwargs = dict(self.kwargs)
            ctx = kwargs.get("profile_ctx")
            if self.profile_args is not None:
                self.progressed.emit(0.0, "preparando o perfil")
                try:
                    ctx = build_profile_context(**self.profile_args)
                except Exception as exc:  # noqa: BLE001 - sem perfil, a busca segue só com os picos
                    logger.warning(f"Score de perfil indisponível: {exc}")
                kwargs["profile_ctx"] = ctx
            result = find_candidates(progress=lambda f, s: self.progressed.emit(f, s),
                                     cancel=lambda: self._cancel, **kwargs)
            self.succeeded.emit((result, ctx))
        except SearchCancelled:
            self.failed.emit("")
        except ValueError as exc:
            self.failed.emit(ptr(str(exc)))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Falha na busca de candidatos")
            self.failed.emit(str(exc))


class _QuantifyWorker(QThread):
    """RIR das fases aceitas, calculado da estrutura (o pymatgen pode levar alguns segundos)."""

    done = Signal(object)

    def __init__(self, jobs, wavelength, two_theta_range, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.wavelength = wavelength
        self.two_theta_range = two_theta_range

    def run(self):
        out = {}
        for key, cif in self.jobs:
            try:
                out[key] = rir_of(cif, self.wavelength, self.two_theta_range)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"RIR não calculado para {key}: {exc}")
                out[key] = None
        self.done.emit(out)


def _pct_spin(value, maximum, suffix=" %", decimals=1):
    box = QDoubleSpinBox()
    box.setRange(0.0, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(0.1)
    box.setValue(value)
    box.setSuffix(suffix)
    return box


def intensity_weights(phases):
    """Pesos da combinação multifásica do PhaseDRX a partir das escalas ajustadas.

    A combinação normaliza cada fase pela própria linha mais forte (100); a escala
    da identificação é relativa à linha mais forte dentro da faixa medida.
    """
    if not phases:
        return []
    raw = []
    for phase in phases:
        fraction = (phase.rir or {}).get("inrange_fraction") or 1.0
        raw.append(max(float(phase.scale), 0.0) / max(float(fraction), 1e-6))
    total = sum(raw)
    if total <= 0:
        return [round(1.0 / len(phases), 4)] * len(phases)
    return [round(r / total, 4) for r in raw]


class MatchPanel(QWidget):
    COLUMNS = ("Score", "Fórmula", "Grupo espacial", "Fonte", "ID", "Linhas", "Posições", "Intensid.",
               "Explicado (%)", "Perfil (%)", "Zero (°)", "Rede", "Notas")
    COLUMN_TIPS = {
        "Linhas": "Reflexões fortes encontradas / esperadas acima do limite de detecção.",
        "Explicado (%)": "Parte da intensidade dos picos explicada pelo candidato. Com fases aceitas, parte do que sobrou.",
        "Perfil (%)": "Parte do difratograma sem fundo explicada pelo padrão simulado do candidato (score de perfil).",
        "Zero (°)": "Deslocamento de zero que alinha a referência aos picos.",
        "Rede": "Fator de escala da rede aplicado à referência (1 = sem mudança).",
    }
    PHASE_COLUMNS = ("", "Fase", "Score", "Massa (%)", "Escala", "Picos")
    PHASE_TIPS = {
        "Score": "Score do candidato quando foi aceito.",
        "Massa (%)": "Fração em massa semiquantitativa pelo método RIR (I/Ic calculado da estrutura). "
                     "É uma estimativa: textura, microabsorção e fase amorfa não entram.",
        "Escala": "Altura observada por unidade de intensidade da referência (ajuste conjunto das fases aceitas).",
        "Picos": "Picos em que esta fase é a maior contribuição.",
    }

    def __init__(self, host, peaks_panel, parent=None):
        super().__init__(parent)
        self.host = host
        self.peaks_panel = peaks_panel
        self.element_filter = ElementFilter()
        self.score_mode = "auto"
        self.result = None
        self.result_item_id = None
        self.selected_key = None
        self.accepted = []
        self.accepted_item_id = None
        self.state = None
        self.observed = None
        self._signature = None
        self._wavelength_used = None
        self._restored_signature = None
        self._pool = []
        self._result_wavelength = None
        self._profile_cache = (None, None)
        self._options_item_id = None
        self._mp_initialized = False
        self._worker = None
        self._quant_worker = None
        self._quant_pending = False
        self._quant_signature = None
        self._quant_tried = set()
        self._summary_note = ""
        self._phase_note = ""
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
        mode_row = QHBoxLayout()
        self.mode_combo = QComboBox()
        for value, label in SCORE_MODE_LABELS:
            self.mode_combo.addItem(ptr(label), value)
        self.mode_combo.setToolTip(ptr(
            "Automático: só os picos quando a lista de picos é boa; picos e perfil inteiro quando há poucos "
            "picos ou picos largos (dados ruidosos, nanocristalinos).\n"
            "Perfil: ajusta o padrão simulado de cada candidato ao difratograma sem fundo."))
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        form.addRow(ptr("Pontuação:"), mode_row)
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
        for col, name in enumerate(self.COLUMNS):
            if name in self.COLUMN_TIPS:
                self.table.horizontalHeaderItem(col).setToolTip(ptr(self.COLUMN_TIPS[name]))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(58)  # cabeçalho + seta de ordenação
        self.table.setSortingEnabled(True)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.errors_label = QLabel()
        self.errors_label.setWordWrap(True)
        self.errors_label.setStyleSheet("color: #d08000;")
        self.errors_label.setVisible(False)

        actions = QHBoxLayout()
        self.accept_button = QPushButton(ptr("Aceitar fase"))
        self.accept_button.setStyleSheet("font-weight: bold;")
        self.accept_button.setToolTip(ptr(
            "Aceita o candidato selecionado. As escalas das fases aceitas são ajustadas juntas e os outros "
            "candidatos são pontuados de novo contra os picos que sobraram."))
        self.add_button = QPushButton(ptr("Adicionar à lista do PhaseDRX"))
        self.add_button.setToolTip(ptr("Carrega o CIF do candidato na aba de simulação."))
        self.open_button = QPushButton(ptr("Abrir na fonte"))
        self.export_button = QPushButton(ptr("Exportar CSV..."))
        actions.addWidget(self.accept_button)
        actions.addWidget(self.add_button)
        actions.addWidget(self.open_button)
        actions.addStretch()
        actions.addWidget(self.export_button)

        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(self.table, 1)
        top_layout.addWidget(self.summary_label)
        top_layout.addWidget(self.errors_label)
        top_layout.addLayout(actions)

        self.phases_box = QGroupBox(ptr("Fases aceitas"))
        phases_layout = QVBoxLayout(self.phases_box)
        self.phase_table = QTableWidget(0, len(self.PHASE_COLUMNS))
        self.phase_table.setHorizontalHeaderLabels([ptr(c) if c else "" for c in self.PHASE_COLUMNS])
        for col, name in enumerate(self.PHASE_COLUMNS):
            if name in self.PHASE_TIPS:
                self.phase_table.horizontalHeaderItem(col).setToolTip(ptr(self.PHASE_TIPS[name]))
        self.phase_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.phase_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.phase_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.phase_table.verticalHeader().setVisible(False)
        header = self.phase_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        self.phase_label = QLabel()
        self.phase_label.setWordWrap(True)
        phase_actions = QHBoxLayout()
        self.remove_phase_button = QPushButton(ptr("Remover fase"))
        self.remove_phase_button.setToolTip(ptr("Remove as fases selecionadas (tecla Delete) e pontua os candidatos de novo."))
        self.send_button = QPushButton(ptr("Enviar fases aceitas para a lista"))
        self.send_button.setToolTip(ptr(
            "Carrega os CIFs das fases aceitas na aba de simulação e cria uma combinação com as proporções ajustadas."))
        phase_actions.addWidget(self.remove_phase_button)
        phase_actions.addStretch()
        phase_actions.addWidget(self.send_button)
        phases_layout.addWidget(self.phase_table, 1)
        phases_layout.addWidget(self.phase_label)
        phases_layout.addLayout(phase_actions)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(top)
        self.splitter.addWidget(self.phases_box)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter, 1)

        self.go_peaks_button.clicked.connect(self._go_to_peaks)
        self.elements_button.clicked.connect(self.choose_elements)
        self.search_button.clicked.connect(self.start_search)
        self.cancel_button.clicked.connect(self.cancel_search)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.accept_button.clicked.connect(self.accept_selected)
        self.add_button.clicked.connect(self.add_selected_to_list)
        self.open_button.clicked.connect(self.open_selected_source)
        self.export_button.clicked.connect(self.export_csv)
        self.phase_table.itemSelectionChanged.connect(self._update_buttons)
        self.remove_phase_button.clicked.connect(self.remove_selected_phases)
        self.send_button.clicked.connect(self.send_accepted_to_list)
        self.mp_check.toggled.connect(lambda on: self.mp_exp_check.setEnabled(on))
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.phase_table)
        delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete_shortcut.activated.connect(self.remove_selected_phases)
        self._update_summary()
        self._update_phase_status()

    # ------------------------------------------------------------------ estado
    def current_item(self):
        return self.peaks_panel.current_item() if self.peaks_panel is not None else None

    @staticmethod
    def _saved(item):
        return (((item or {}).get("analysis") or {}).get("search_match")) or {}

    @staticmethod
    def _saved_dict(item):
        analysis = item.get("analysis")
        if not isinstance(analysis, dict):
            analysis = item["analysis"] = {}
        saved = analysis.get("search_match")
        if not isinstance(saved, dict):
            saved = analysis["search_match"] = {}
        return saved

    def _wavelength(self):
        try:
            return self.host.radiation_info().get("ka1")
        except (AttributeError, ValueError, KeyError):
            return None

    def refresh(self):
        """Atualiza difratograma, picos, opções salvas, fases aceitas e scores (se algo mudou)."""
        item = self.current_item()
        peak_list = self.peaks_panel.peak_list_of(item) if item is not None else None
        self.item_label.setText(item.get("label", "?") if item else ptr("nenhum (carregue dados na aba Dados Experimentais)"))
        if peak_list is None:
            self.peaks_label.setText(ptr("nenhuma busca de picos neste difratograma"))
        else:
            n_peaks, _n_halos = peak_list.counts()
            self.peaks_label.setText(ptr("{} picos").format(n_peaks))
        item_id = item.get("id") if item else None
        if item_id != self._options_item_id:
            saved = self._saved(item)
            if saved.get("filter"):
                self.element_filter = ElementFilter.from_dict(saved["filter"])
            if saved.get("score_mode"):
                self._set_mode(saved["score_mode"])
            self._options_item_id = item_id
        self.filter_label.setText(describe_filter(self.element_filter))
        key = find_mp_api_key()
        self.mp_check.setEnabled(key is not None)
        if key is None:
            self.mp_check.setChecked(False)
            self.mp_check.setToolTip(ptr("Configure a chave da API do Materials Project no MatFinder."))
        else:
            self.mp_check.setToolTip(ptr("Chave da API do Materials Project encontrada."))
            if not self._mp_initialized:
                self.mp_check.setChecked(True)
        self._mp_initialized = True
        changed = False
        if self.result is not None and item_id != self.result_item_id:
            self._clear_result()
            changed = True
        changed |= self._sync_accepted(item)
        changed |= self._ensure_state(item, peak_list)
        if changed:
            self._fill_table()
            self._fill_phases()
        self._update_buttons()

    def _set_mode(self, mode):
        index = self.mode_combo.findData(mode)
        if index < 0:
            return
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(index)
        self.mode_combo.blockSignals(False)
        self.score_mode = mode

    def _clear_result(self, note=""):
        self.result = None
        self.result_item_id = None
        self._pool = []
        self._result_wavelength = None
        self.selected_key = None
        self._summary_note = note

    def _sync_accepted(self, item):
        """As fases aceitas acompanham o item: troca de difratograma, desfazer/refazer, projeto aberto."""
        item_id = item.get("id") if item else None
        saved = self._saved(item)
        data = saved.get("accepted") or []
        keys = [f"{d.get('source')}:{d.get('source_id')}" for d in data]
        if item_id == self.accepted_item_id and keys == [p.candidate.key for p in self.accepted]:
            return False
        phases = []
        for entry in data:
            try:
                phase = AcceptedPhase.from_dict(entry)
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning(f"Fase aceita inválida no projeto: {exc}")
                continue
            if phase.candidate.cif:
                phases.append(phase)
        self.accepted = phases
        self.accepted_item_id = item_id
        self._restored_signature = saved.get("signature")
        self._signature = None
        self._quant_tried.clear()
        return True

    def _peaks_signature(self, peak_list, wavelength):
        parts = [f"{wavelength:.6f}", f"{peak_list.noise_level or 0.0:.6g}", str(peak_list.data_signature)]
        parts += [f"{p.two_theta:.5f}/{p.height:.6g}/{p.fwhm:.5f}/{p.kind}/{','.join(sorted(p.flags))}"
                  for p in peak_list]
        return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _observed(item, peak_list):
        x = np.asarray(item["data"][0], dtype=float)
        return ObservedPeaks.from_peaks(list(peak_list), (float(np.min(x)), float(np.max(x))), peak_list.noise_level)

    def _needs_profile(self, obs):
        mode = self.score_mode
        return mode in ("profile", "both") or (mode == "auto" and peak_list_is_poor(obs))

    def _profile_args(self, item, peak_list):
        info = self.host.radiation_info()
        settings = peak_list.settings or {}
        result = self.peaks_panel.overlay_result(item)
        return dict(two_theta=np.asarray(item["data"][0], dtype=float),
                    intensity=np.asarray(item["data"][1], dtype=float), peaks=list(peak_list),
                    wavelength=info.get("ka1"), wavelength_ka2=info.get("ka2") if settings.get("ka2", True) else None,
                    ka2_ratio=float(settings.get("ka2_ratio", 0.5)),
                    background=result.background if result is not None else None,
                    noise=result.noise if result is not None else None)

    def _profile_context(self, item, peak_list, signature):
        key = (item.get("id"), signature)
        if self._profile_cache[0] == key:
            return self._profile_cache[1]
        try:
            ctx = build_profile_context(**self._profile_args(item, peak_list))
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Score de perfil indisponível: {exc}")
            ctx = None
        self._profile_cache = (key, ctx)
        return ctx

    def _ensure_state(self, item, peak_list=None, force=False):
        """Recalcula escalas, resíduo e scores se os picos, a radiação ou as fases mudaram.

        Returns:
            True se algo foi recalculado (as tabelas precisam ser refeitas).
        """
        if item is not None and peak_list is None:
            peak_list = self.peaks_panel.peak_list_of(item)
        wavelength = self._wavelength() if item is not None else None
        if item is None or item.get("data") is None or peak_list is None or not wavelength:
            had = self.state is not None
            self.state = self.observed = self._signature = None
            return had
        signature = self._peaks_signature(peak_list, wavelength)
        if signature == self._signature and not force:
            return False
        if self.result is not None and self._result_wavelength and abs(self._result_wavelength - wavelength) > 1e-6:
            self._clear_result(ptr("A radiação mudou: busque os candidatos de novo."))
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._recompute(item, peak_list, wavelength, signature)
        finally:
            QApplication.restoreOverrideCursor()
        return True

    def _recompute(self, item, peak_list, wavelength, signature):
        obs = self._observed(item, peak_list)
        settings = self.settings_from_ui().score
        peaks_changed = signature != self._signature
        new_wavelength = self._wavelength_used is None or abs(self._wavelength_used - wavelength) > 1e-6
        keep_derived = self._restored_signature == signature  # restauradas do projeto com os mesmos picos
        ctx = self._profile_context(item, peak_list, signature) if self._needs_profile(obs) else None
        for phase in self.accepted:
            cand = phase.candidate
            try:
                if cand.reference is None or new_wavelength:
                    cand.reference = reference_pattern(cand.cif, wavelength, (obs.lo, obs.hi), settings.min_ref_intensity)
                if cand.match is None or peaks_changed or new_wavelength:
                    center = cand.match.shift if cand.match is not None else phase.shift_hint
                    cand.match = score_candidate(cand.reference, obs, settings, cand.source, shift_center=center)
            except Exception as exc:  # noqa: BLE001 - CIF problemático: a fase fica sem contribuição
                logger.warning(f"Fase aceita sem padrão de referência ({cand.label}): {exc}")
                cand.match = None
            if new_wavelength and not keep_derived:
                phase.rir = None  # o RIR depende do comprimento de onda
        state = analyze(obs, self.accepted, ctx)
        self.state, self.observed = state, obs
        self._signature, self._wavelength_used = signature, wavelength
        self._restored_signature = None
        self._update_fractions()
        if self.result is not None and self.result_item_id == item.get("id"):
            self._rescore(obs, state, ctx, settings)
        self._start_quantify()

    def _rescore(self, obs, state, ctx, settings):
        ranked, used = rescore(self._pool, obs, self.accepted, settings, state=state, profile_ctx=ctx,
                               mode=self.score_mode)
        self.result.all_candidates = ranked
        self.result.candidates = group_duplicates(ranked) if self.group_check.isChecked() else list(ranked)
        self.result.info.update(score_mode=used, n_scored=len(ranked), n_groups=len(self.result.candidates),
                                by_source={src: sum(1 for c in ranked if c.source == src) for src in ("COD", "MP")})
        if self.selected_key not in {c.key for c in self.result.candidates}:
            self.selected_key = self.result.candidates[0].key if self.result.candidates else None

    def _update_fractions(self):
        pending = any(p.rir is None and (p.candidate.key, self._signature) not in self._quant_tried
                      for p in self.accepted)
        if pending:
            for phase in self.accepted:
                phase.weight_fraction = None
            return
        fractions = semi_quant([p.scale for p in self.accepted], [p.rir for p in self.accepted])
        for phase, fraction in zip(self.accepted, fractions):
            phase.weight_fraction = fraction

    def _store_accepted(self, item):
        saved = self._saved_dict(item)
        saved["accepted"] = [p.to_dict() for p in self.accepted]
        saved["signature"] = self._signature
        self.host.set_dirty()

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

    def _selected_phase_keys(self):
        keys = set()
        for index in self.phase_table.selectionModel().selectedRows():
            cell = self.phase_table.item(index.row(), 0)
            if cell is not None:
                keys.add(cell.data(Qt.ItemDataRole.UserRole))
        return keys

    def _update_buttons(self):
        busy = self._worker is not None
        has = self.selected_candidate() is not None
        self.accept_button.setEnabled(has and not busy)
        self.add_button.setEnabled(has)
        self.open_button.setEnabled(has)
        self.export_button.setEnabled(self.result is not None and bool(self.result.candidates))
        self.remove_phase_button.setEnabled(bool(self._selected_phase_keys()) and not busy)
        self.send_button.setEnabled(bool(self.accepted) and not busy)

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
        saved = self._saved_dict(item)
        saved["filter"] = self.element_filter.to_dict()
        saved["settings"] = self.settings_from_ui().to_dict()
        saved["score_mode"] = self.score_mode
        self.host.set_dirty()

    def _on_mode_changed(self, *_args):
        self.score_mode = self.mode_combo.currentData() or "auto"
        self._save_options()
        item = self.current_item()
        if item is not None and (self.result is not None or self.accepted):
            self._ensure_state(item, force=True)
            self._fill_table()
            self._fill_phases()
            self.host._redraw_all_plots()

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
        wavelength = self._wavelength()
        if not wavelength:
            QMessageBox.information(self, ptr("Identificação"), ptr("Comprimento de onda inválido."))
            return
        self._save_options()
        self._ensure_state(item, peak_list)  # fases aceitas casadas com os picos atuais
        x = np.asarray(item["data"][0], dtype=float)
        kwargs = dict(peaks=list(peak_list), element_filter=self.element_filter, wavelength=wavelength,
                      two_theta_range=(float(np.min(x)), float(np.max(x))), settings=settings,
                      noise=peak_list.noise_level, accepted=list(self.accepted), score_mode=self.score_mode)
        profile_args = None
        if self.observed is not None and self._needs_profile(self.observed):
            if self._profile_cache[0] == (item["id"], self._signature) and self._profile_cache[1] is not None:
                kwargs["profile_ctx"] = self._profile_cache[1]
            else:
                profile_args = self._profile_args(item, peak_list)
        self._search_item_id = item["id"]
        self._search_wavelength = wavelength
        self._search_signature = self._signature
        self._worker = _CandidateWorker(kwargs, profile_args, self)
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
        if self._quant_worker is not None:
            self._quant_worker.wait(30000)

    def _set_busy(self, busy):
        self.search_button.setEnabled(not busy)
        self.elements_button.setEnabled(not busy)
        self.mode_combo.setEnabled(not busy)
        self.cancel_button.setVisible(busy)
        self.progress.setVisible(busy)
        self.progress.setValue(0)
        self._update_buttons()

    def _on_progress(self, fraction, stage):
        self.progress.setValue(int(round(100 * fraction)))
        self.progress.setFormat(ptr(STAGES.get(stage, stage)) + " — %p%")

    def _on_finished(self):
        self._worker = None
        self._set_busy(False)

    def _on_failed(self, message):
        if message:
            QMessageBox.warning(self, ptr("Identificação"), ptr("A busca de candidatos falhou:\n{}").format(message))

    def _on_done(self, payload):
        result, ctx = payload
        self.result = result
        self.result_item_id = self._search_item_id
        self._result_wavelength = self._search_wavelength
        self._pool = list(result.pool or result.all_candidates)
        self._summary_note = ""
        if ctx is not None:
            self._profile_cache = ((self._search_item_id, self._search_signature), ctx)
        self.selected_key = result.candidates[0].key if result.candidates else None
        item = self.current_item()
        if item is not None and item.get("id") == self.result_item_id and self._signature != self._search_signature:
            self._ensure_state(item, force=True)  # os picos mudaram durante a busca: pontua de novo
        self._fill_table()
        self._fill_phases()
        self.host._redraw_all_plots()

    def accept_selected(self):
        """Aceita o candidato selecionado e pontua os outros contra o que sobrou."""
        item = self.current_item()
        cand = self.selected_candidate()
        if item is None or cand is None or cand.match is None or self._worker is not None:
            return
        if any(p.candidate.key == cand.key for p in self.accepted):
            return
        self.host._add_state_to_history()
        self.accepted.append(AcceptedPhase(cand, next_color(self.accepted)))
        self.accepted_item_id = item.get("id")
        self.selected_key = None
        self._phase_note = ""
        self._apply_change(item)

    def remove_selected_phases(self):
        item = self.current_item()
        keys = self._selected_phase_keys()
        if item is None or not keys or self._worker is not None:
            return
        self.host._add_state_to_history()
        pool_keys = {c.key for c in self._pool}
        for phase in self.accepted:
            cand = phase.candidate
            if cand.key in keys and self.result is not None and cand.key not in pool_keys and cand.reference is not None:
                self._pool.append(cand)  # volta para a lista de candidatos
        self.accepted = [p for p in self.accepted if p.candidate.key not in keys]
        self.selected_key = None  # a classificação muda: seleciona o melhor candidato de novo
        self._phase_note = ""
        self._apply_change(item)

    def _apply_change(self, item):
        self._ensure_state(item, force=True)
        self._store_accepted(item)
        self._fill_table()
        self._fill_phases()
        self._update_buttons()
        self.host._redraw_all_plots()

    def send_accepted_to_list(self):
        """CIFs das fases aceitas na lista do PhaseDRX e uma combinação com as proporções ajustadas."""
        if not self.accepted or self._worker is not None:
            return
        host = self.host
        host._add_state_to_history()
        sent = []
        for phase in self.accepted:
            cand = phase.candidate
            name = cand.file_name()
            existing = next((p for p in host.plot_items if p.get("label") == name), None)
            if existing is None:
                existing = host.load_cif_from_data(cand.cif, name, record_history=False)
            if existing is not None and existing.get("type") == "cif":
                sent.append((phase, existing))
        combo = None
        if len(sent) >= 2:
            ids = [it["id"] for _, it in sent]
            weights = intensity_weights([p for p, _ in sent])
            combo = next((p for p in host.plot_items
                          if p.get("type") == "multiphase" and p.get("component_ids") == ids), None)
            if combo is None:
                fwhm = float(np.median(self.observed.fwhm)) if self.observed is not None and len(self.observed) else 0.12
                combo = {
                    "id": str(uuid.uuid4()), "type": "multiphase",
                    "label": ptr("Comb: {}").format(" + ".join(p.candidate.formula for p, _ in sent)),
                    "data": None, "visible": True, "color": host._get_next_color(), "style": "--", "linewidth": 2.0,
                    "component_ids": ids, "component_weights": weights,
                    "simulation_params": {"profile": "pseudo-voigt", "fwhm": round(float(np.clip(fwhm, 0.01, 2.0)), 3)},
                }
                host.plot_items.append(combo)
            else:
                combo["component_weights"] = weights
            host._recalculate_multiphase_item(combo)
        host._repopulate_all_lists()
        host._redraw_all_plots()
        host.set_dirty()
        if combo is not None:
            self._phase_note = ptr("Fases enviadas para a lista, com a combinação {}.").format(combo["label"])
        elif sent:
            self._phase_note = ptr("Fase enviada para a lista.")
        else:
            self._phase_note = ptr("Nenhuma fase foi enviada.")
        self._update_phase_status()

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
                                 "positions", "reference", "observed", "intensity", "profile_explained",
                                 "zero_shift_deg", "lattice_scale", "group_size", "url"])
                for c in self.result.candidates:
                    m = c.match
                    profile = f"{c.profile_explained:.4f}" if c.profile_explained is not None else ""
                    writer.writerow([f"{c.score:.2f}", c.formula, c.spacegroup, c.source, c.source_id, m.lines_found,
                                     m.lines_expected] + [f"{c.subscores[k]:.4f}" for k in
                                                          ("positions", "reference", "observed", "intensity")]
                                    + [profile, f"{m.shift:.3f}", f"{m.lattice_scale:.4f}", 1 + len(c.group_members),
                                       c.url])
        except OSError as exc:
            QMessageBox.critical(self, ptr("Exportar candidatos"), ptr("Não foi possível salvar:\n{}").format(exc))

    # ------------------------------------------------------------------ quantificação (em segundo plano)
    def _start_quantify(self):
        if self.observed is None or not self.accepted:
            return
        if self._quant_worker is not None:
            self._quant_pending = True
            return
        jobs = [(p.candidate.key, p.candidate.cif) for p in self.accepted
                if p.rir is None and p.candidate.cif and (p.candidate.key, self._signature) not in self._quant_tried]
        if not jobs:
            return
        self._quant_signature = self._signature
        worker = _QuantifyWorker(jobs, self._wavelength_used, (self.observed.lo, self.observed.hi), self)
        worker.done.connect(self._on_quantified)
        worker.finished.connect(self._on_quantify_finished)
        self._quant_worker = worker
        worker.start()
        self._update_phase_status()

    def _on_quantified(self, results):
        if self._quant_signature != self._signature:
            return  # picos ou radiação mudaram durante o cálculo: será refeito
        for phase in self.accepted:
            if phase.candidate.key not in results:
                continue
            self._quant_tried.add((phase.candidate.key, self._signature))
            if phase.rir is None:
                phase.rir = results[phase.candidate.key]
        self._update_fractions()
        item = self.current_item()
        if item is not None and item.get("id") == self.accepted_item_id:
            self._store_accepted(item)
        self.host._redraw_all_plots()

    def _on_quantify_finished(self):
        self._quant_worker = None
        if self._quant_pending or self._quant_signature != self._signature:
            self._quant_pending = False
            self._start_quantify()
        self._fill_phases()

    # ------------------------------------------------------------------ tabelas
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
            profile = c.profile_explained
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
                _NumericItem(f"{100 * profile:.0f}" if profile is not None else "—",
                             profile if profile is not None else -1.0),
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
            self.summary_label.setText(self._summary_note or ptr("Nenhuma busca de candidatos neste difratograma."))
            self.errors_label.setVisible(False)
            return
        info = self.result.info
        by_source = info.get("by_source", {})
        text = ptr("{} candidatos (COD {}, MP {}) em {} fases").format(
            info.get("n_scored", 0), by_source.get("COD", 0), by_source.get("MP", 0), info.get("n_groups", 0))
        if self.result.candidates:
            best = self.result.candidates[0]
            text += " · " + ptr("melhor: {} ({:.0f})").format(best.label, best.score)
        used = info.get("score_mode")
        if used in USED_MODE_NAMES:
            text += " · " + ptr("pontuação: {}").format(ptr(USED_MODE_NAMES[used]))
        if self.accepted:
            text += " · " + ptr("pontuados contra os picos que sobraram")
        if info.get("truncated"):
            text += " · " + ptr("lista limitada aos candidatos mais prováveis")
        self.summary_label.setText(text)
        errors = [f"{src}: {ptr(msg)}" for src, msg in self.result.errors.items()]
        self.errors_label.setText(ptr("Avisos das fontes:") + " " + " | ".join(errors) if errors else "")
        self.errors_label.setVisible(bool(errors))

    def _fill_phases(self):
        table = self.phase_table
        selected = self._selected_phase_keys()
        quantifying = self._quant_worker is not None
        table.blockSignals(True)
        table.clearSelection()
        table.setRowCount(len(self.accepted))
        for r, phase in enumerate(self.accepted):
            cand = phase.candidate
            waiting = quantifying and (cand.key, self._signature) not in self._quant_tried
            swatch = QTableWidgetItem("")
            swatch.setBackground(QColor(phase.color))
            swatch.setData(Qt.ItemDataRole.UserRole, cand.key)
            name = QTableWidgetItem(cand.label)
            name.setToolTip(cand.url)
            if cand.match is None:
                name.setForeground(QColor(UNEXPLAINED_COLOR))
                name.setToolTip(ptr("Não foi possível simular esta fase."))
            if phase.weight_fraction is not None:
                mass = QTableWidgetItem(f"{100 * phase.weight_fraction:.1f}")
            else:
                mass = QTableWidgetItem("…" if waiting else "—")
            if phase.rir:
                mass.setToolTip(ptr("RIR (I/Ic) calculado da estrutura: {}").format(f"{phase.rir['rir']:.2f}"))
            cells = (swatch, name, QTableWidgetItem(f"{cand.score:.1f}"), mass, QTableWidgetItem(f"{phase.scale:.4g}"),
                     QTableWidgetItem(str(phase.peaks_explained)))
            for col, cell in enumerate(cells):
                if col in (2, 3, 4, 5):
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r, col, cell)
        table.blockSignals(False)
        for r, phase in enumerate(self.accepted):
            if phase.candidate.key in selected:
                table.selectRow(r)
                break
        self._update_phase_status()
        self._update_buttons()

    def _update_phase_status(self):
        if not self.accepted:
            text = ptr("Nenhuma fase aceita. Selecione um candidato e clique em Aceitar fase.")
        else:
            parts = []
            state = self.state
            if state is not None:
                parts.append(ptr("As fases aceitas explicam {}% da intensidade dos picos").format(
                    f"{100 * state.explained_fraction:.0f}"))
                parts.append(ptr("picos sem fase: {}").format(int(np.sum(state.unexplained))))
                if state.global_shift is not None:
                    parts.append(ptr("zero global {}°").format(f"{state.global_shift:+.3f}"))
                if state.profile_explained is not None:
                    parts.append(ptr("perfil explicado: {}%").format(f"{100 * state.profile_explained:.0f}"))
            if self._quant_worker is not None:
                parts.append(ptr("calculando o RIR..."))
            text = " · ".join(parts)
        if self._phase_note:
            text += "\n" + self._phase_note
        self.phase_label.setText(text)


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


def _draw_peak_assignment(ax, offset, panel, x, y):
    """Picos coloridos pela fase que mais os explica; picos sem fase ganham um anel vermelho."""
    state, obs = panel.state, panel.observed
    if state is None or obs is None or not len(obs) or len(state.dominant) != len(obs):
        return
    order = np.argsort(x)
    xs, ys = x[order], y[order]
    lift = 0.03 * (float(np.ptp(ys)) or 1.0)          # mesma posição dos marcadores da aba Picos
    marks = np.interp(obs.two_theta, xs, ys) + offset + lift
    for a, phase in enumerate(panel.accepted):
        sel = state.dominant == a
        if sel.any():
            ax.plot(obs.two_theta[sel], marks[sel], linestyle="none", marker="v", ms=6, color=phase.color,
                    mec="white", mew=0.5, label="_peak_phase", zorder=5.5)
    loose = state.unexplained
    if loose.any():
        ax.plot(obs.two_theta[loose], marks[loose], linestyle="none", marker="o", ms=11, mfc="none",
                mec=UNEXPLAINED_COLOR, mew=1.3, label="_peak_unexplained", zorder=5.6)


def draw_candidate_overlay(ax, item, offset, panel=None):
    """Fases aceitas (cada uma na sua cor) e prévia do candidato selecionado sobre o difratograma."""
    if panel is None or item.get("data") is None:
        return
    has_accepted = bool(panel.accepted) and item.get("id") == panel.accepted_item_id
    cand = panel.selected_candidate() if panel.result is not None and item.get("id") == panel.result_item_id else None
    if cand is not None and cand.match is None:
        cand = None
    if not has_accepted and cand is None:
        return
    x, y = (np.asarray(v, dtype=float) for v in item["data"])
    bx, by = _baseline(panel, item, x, y)
    legend = []
    if has_accepted:
        for phase in panel.accepted:
            m = phase.candidate.match
            if m is None or not len(m.ref_two_theta) or phase.scale <= 0:
                continue
            base = np.interp(m.ref_two_theta, bx, by) + offset
            ax.vlines(m.ref_two_theta, base, base + phase.scale * m.ref_intensity, colors=phase.color, lw=1.4,
                      alpha=0.9, label="_accepted_phase", zorder=3.5)
            mass = f" · {100 * phase.weight_fraction:.0f}%" if phase.weight_fraction is not None else ""
            legend.append((f"{phase.candidate.formula} {phase.candidate.spacegroup}".strip() + mass, phase.color))
        _draw_peak_assignment(ax, offset, panel, x, y)
    if cand is not None:
        m = cand.match
        matched = {r for r, _, _ in m.pairs}
        groups = {"matched": ([], [], []), "missing": ([], [], []), "weak": ([], [], [])}
        for j, (tt, inten) in enumerate(zip(m.ref_two_theta, m.ref_intensity)):
            base = float(np.interp(tt, bx, by)) + offset
            if j in matched:
                key = "matched"
            elif m.expected[j]:
                key = "missing"
            else:
                key = "weak"
            groups[key][0].append(tt)
            groups[key][1].append(base)
            groups[key][2].append(base + m.scale_factor * inten)
        styles = {"matched": dict(lw=1.6, ls="-"), "missing": dict(lw=1.2, ls="--"), "weak": dict(lw=0.8, ls=":")}
        for key, (xs_, ymin, ymax) in groups.items():
            if xs_:
                ax.vlines(xs_, ymin, ymax, colors=COLORS[key], label="_candidate_" + key, zorder=4, **styles[key])
        legend.append((f"{cand.label} · score {cand.score:.0f}", COLORS["matched"]))
    for k, (text, color) in enumerate(legend):
        ax.annotate(text, xy=(0.01, 0.98), xycoords="axes fraction", xytext=(0, -13 * k), textcoords="offset points",
                    ha="left", va="top", fontsize=8, color=color, annotation_clip=False,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7))
