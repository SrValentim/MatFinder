# MÓDULO PRINCIPAL DA APLICAÇÃO MATFINDER
# Versão 3.24

# --- MÓDulos PADRÃO (leves e rápidos para importar) ---
import sys
import os
import subprocess
import threading
import io
from urllib.parse import quote, urljoin
import json
from datetime import datetime
import logging
import re

# --- ALTERAÇÃO DE REATORAÇÃO ---
# O bloco logging.basicConfig() foi MOVIDO daqui para o 'run_matfinder.py'
# para garantir que os logs sejam capturados desde o início.
# --- FIM DA ALTERAÇÃO ---

# --- IMPORTAÇÕES PESADAS (LAZY LOADING - carregadas sob demanda) ---
# Essas importações são carregadas apenas quando necessárias para acelerar inicialização
requests = None  # Carregado sob demanda
BeautifulSoup = None  # Carregado sob demanda
MPRester = None  # Carregado sob demanda
Composition = None  # Carregado sob demanda
Structure = None  # Carregado sob demanda


def _ensure_requests():
    """Carrega módulo requests sob demanda."""
    global requests
    if requests is None:
        import requests as _requests
        requests = _requests
    return requests


def _ensure_beautifulsoup():
    """Carrega BeautifulSoup sob demanda."""
    global BeautifulSoup
    if BeautifulSoup is None:
        from bs4 import BeautifulSoup as _BeautifulSoup
        BeautifulSoup = _BeautifulSoup
    return BeautifulSoup


def _ensure_mp_api():
    """Carrega módulos do Materials Project sob demanda."""
    global MPRester
    if MPRester is None:
        from mp_api.client import MPRester as _MPRester
        MPRester = _MPRester
        # Aceitar IDs alfanuméricos novos do MP (ex.: 'mp-aaadipjz') com o
        # emmet-core fixado. Sem isto, a consulta quebra com "Invalid MPID Format".
        try:
            from matfinder import _mp_compat
            _mp_compat.apply()
        except Exception:
            pass
    return MPRester


def _ensure_pymatgen():
    """Carrega módulos pymatgen sob demanda."""
    global Composition, Structure
    if Composition is None:
        from pymatgen.core.composition import Composition as _Composition
        from pymatgen.core.structure import Structure as _Structure
        Composition = _Composition
        Structure = _Structure
    return Composition, Structure

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem, QFileDialog,
    QMessageBox, QDialog, QFormLayout, QGroupBox, QSizePolicy,
    QHeaderView, QMenu, QInputDialog, QApplication,
    QStatusBar, QTableWidget,
    QTableWidgetItem, QAbstractItemView
)
from PySide6.QtGui import (
    QAction, QIcon, QPixmap, QDesktopServices, QColor, QBrush,
    QCursor, QPainter, QGuiApplication, QStandardItemModel,
    QStandardItem
)
from PySide6.QtCore import (
    Qt, QUrl, QTimer, QSize, QPoint, Signal, Slot, QObject, QStandardPaths
)
from PySide6.QtSvg import QSvgRenderer
from matfinder.core.translator import ptr

# --- ALTERAÇÃO DE REATORAÇÃO: Importações de Módulos Locais ---
# Os caminhos de importação foram atualizados para refletir a nova estrutura de pacotes
# NOTA: TABELA_PERIODICA_ELEMENTOS agora é carregada sob demanda para acelerar inicialização
TABELA_PERIODICA_ELEMENTOS = None  # Carregado sob demanda

def _ensure_tabela_periodica_elementos():
    """Carrega dados da tabela periódica sob demanda."""
    global TABELA_PERIODICA_ELEMENTOS
    if TABELA_PERIODICA_ELEMENTOS is None:
        from matfinder.tools.periodic_table.tabela_periodica_pyside import ELEMENTOS
        TABELA_PERIODICA_ELEMENTOS = ELEMENTOS
    return TABELA_PERIODICA_ELEMENTOS

try:
    from matfinder import __version__, get_full_title
    from matfinder.core.grupo_espacial import obter_info_grupo_espacial
    from matfinder.core.historico_dialog_pyside import HISTORICO_FILE, DATETIME_FORMAT
    from matfinder.data import COD_api_logic
    from matfinder.core.favorites_manager import favorites_manager
    from matfinder.core.translator import tr, get_translator, set_language, get_current_language, SUPPORTED_LANGUAGES
except ImportError as e:
    # Log crítico se os módulos centrais falharem
    logging.critical(f"Falha ao importar módulos locais essenciais: {e}", exc_info=True)
    # Em um app real, poderíamos mostrar um QMessageBox crítico e sair.
    # Por enquanto, definimos valores padrão para evitar que o resto do ficheiro falhe ao carregar.
    def _ensure_tabela_periodica_elementos(): return []
    def obter_info_grupo_espacial(arg): return None
    HISTORICO_FILE = "historico_buscas.json"
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
    class MockFavoritesManager:
        def is_favorite(self, *args): return False
        def add_favorite(self, *args): pass
        def remove_favorite(self, *args): pass
    favorites_manager = MockFavoritesManager()
    class MockCodApiLogic:
        def search_cod_by_elements(self, *args, **kwargs): return []
        def get_cod_cif_data(self, *args, **kwargs): return None
    COD_api_logic = MockCodApiLogic()
    # Fallback para tradução
    def tr(key, **kwargs): return key
    def get_translator(): return None
    def set_language(lang): return False
    def get_current_language(): return 'pt_BR'
    SUPPORTED_LANGUAGES = {'pt_BR': 'Português (Brasil)', 'en_US': 'English (US)', 'de_DE': 'Deutsch'}
# --- FIM DA ALTERAÇÃO ---


# --- Constantes Globais ---
SISTEMAS_CRISTALINOS_PT = {
    "triclinic": "Triclínico", "monoclinic": "Monoclínico",
    "orthorhombic": "Ortorrômbico", "tetragonal": "Tetragonal",
    "trigonal": "Trigonal", "rhombohedral": "Romboédrico",
    "hexagonal": "Hexagonal", "cubic": "Cúbico", "unknown": "Desconhecido",
}
ROD_SEARCH_BASE_URL = "https://solsa.crystallography.net/rod/result"
ROD_ENTRY_BASE_URL = "https://solsa.crystallography.net/rod/"


# --- Função para traduzir sistemas cristalinos ---
def get_crystal_system_translated(system_key: str) -> str:
    """Retorna o nome do sistema cristalino traduzido."""
    return tr(f'crystal_systems.{system_key.lower()}')


class Worker(QObject):
    # (O conteúdo da classe Worker permanece o mesmo)
    material_search_results_ready = Signal(list, str)
    oa_pdf_downloaded = Signal(bytes, str)
    task_error = Signal(str, str)
    cif_data_ready = Signal(str, str)
    cod_cif_data_ready = Signal(str, str, str)
    rod_file_data_ready = Signal(str, str, str)
    doi_from_ccdc_ready = Signal(str)

    def __init__(self, task_callable, task_type: str, *args):
        super().__init__()
        self.task_callable = task_callable
        self.task_type = task_type
        self.args = args

    @Slot()
    def run(self):
        # Carregar requests para tratamento de exceções de rede
        import requests as _requests

        context_for_error = ptr("Tarefa Desconhecida")
        try:
            if self.task_type == "material_search":
                context_for_error = (
                    self.args[1] if len(self.args) > 1 else "API Materiais"
                )
                results_raw, db_choice_from_func = self.task_callable(*self.args)
                self.material_search_results_ready.emit(
                    results_raw, db_choice_from_func
                )
            elif self.task_type == "oa_pdf":
                context_for_error = ptr("Open-Access PDF")
                pdf_content, suggested_filename = self.task_callable(*self.args)
                self.oa_pdf_downloaded.emit(pdf_content, suggested_filename)
            elif self.task_type == "fetch_doi_from_ccdc":
                context_for_error = ptr("Busca de DOI (CCDC)")
                doi = self.task_callable(*self.args)
                self.doi_from_ccdc_ready.emit(doi)
            elif self.task_type == "fetch_cif_mp":
                context_for_error = ptr("Busca CIF (MP)")
                cif_string, suggested_filename = self.task_callable(*self.args)
                self.cif_data_ready.emit(cif_string, suggested_filename)
            elif self.task_type == "fetch_cif_cod":
                cod_id = self.args[0]
                formula_for_filename = (
                    self.args[1] if len(self.args) > 1 else cod_id
                )
                context_for_error = ptr("Busca CIF (COD - {})").format(cod_id)
                cif_string = self.task_callable(cod_id)
                if cif_string:
                    safe_formula = "".join(
                        c if c.isalnum() else "_" for c in formula_for_filename
                    )
                    suggested_filename = f"COD_{cod_id}_{safe_formula}.cif"
                    self.cod_cif_data_ready.emit(
                        cif_string, suggested_filename, cod_id
                    )
                else:
                    self.task_error.emit(
                        context_for_error,
                        f"Não foi possível obter o arquivo CIF para COD ID: {cod_id}",
                    )
            elif self.task_type == "fetch_rod_file":
                rod_id = self.args[0]
                formula_for_filename = self.args[1] if len(self.args) > 1 else rod_id
                context_for_error = ptr("Busca Arquivo .rod (ROD - {})").format(rod_id)
                rod_file_content = self.task_callable(rod_id)
                if rod_file_content:
                    self.rod_file_data_ready.emit(rod_file_content, rod_id, formula_for_filename)
                else:
                    self.task_error.emit(
                        context_for_error,
                        f"Não foi possível obter o arquivo .rod para ROD ID: {rod_id}",
                    )
            else:
                logging.error(
                    f"Tipo de tarefa desconhecido no Worker: {self.task_type}"
                )
                self.task_error.emit(
                    "Erro de Worker", f"Tipo de tarefa desconhecido: {self.task_type}"
                )
                return
        except _requests.exceptions.Timeout as timeout_err:
            error_title = ptr("Timeout de Conexão ({})").format(context_for_error)
            user_message = (
                ptr("A conexão demorou muito para responder.\n\nDetalhes: {}\n\nVerifique sua conexão ou tente novamente mais tarde.").format(timeout_err)
            )
            logging.error(f"{error_title}: {timeout_err}")
            self.task_error.emit(error_title, user_message)
        except _requests.exceptions.ConnectionError as conn_err:
            error_title = ptr("Erro de Conexão ({})").format(context_for_error)
            user_message = (
                ptr("Falha ao estabelecer conexão.\n\nDetalhes: {}\n\nVerifique sua conexão com a internet e as configurações de proxy.").format(conn_err)
            )
            logging.error(f"{error_title}: {conn_err}")
            self.task_error.emit(error_title, user_message)
        except _requests.exceptions.ProxyError as proxy_err:
            error_title = ptr("Erro de Proxy ({})").format(context_for_error)
            user_message = (
                ptr("Falha ao conectar através do proxy.\n\nDetalhes: {}\n\nVerifique as configurações do proxy e a sua conexão.").format(proxy_err)
            )
            logging.error(f"{error_title}: {proxy_err}")
            self.task_error.emit(error_title, user_message)
        except _requests.exceptions.HTTPError as http_err:
            error_title = ptr("Erro HTTP ({})").format(context_for_error)
            user_message = (
                ptr("O servidor retornou um erro.\n\nStatus: {}\nDetalhes: {}\n\nVerifique os parâmetros da busca ou tente mais tarde.").format(http_err.response.status_code, http_err)
            )
            logging.error(
                f"{error_title} - Status {http_err.response.status_code}: {http_err}"
            )
            self.task_error.emit(error_title, user_message)
        except _requests.exceptions.RequestException as req_err:
            error_title = ptr("Erro de Requisição ({})").format(context_for_error)
            user_message = (
                ptr("Ocorreu um problema com a requisição de rede.\n\nDetalhes: {}\n\nTente novamente ou verifique sua conexão.").format(req_err)
            )
            logging.error(f"{error_title}: {req_err}")
            self.task_error.emit(error_title, user_message)
        except json.JSONDecodeError as json_err:
            error_title = ptr("Erro ao Processar Dados ({})").format(context_for_error)
            user_message = (
                ptr("Falha ao ler os dados recebidos do servidor (formato JSON inválido).\n\nDetalhes: {}").format(json_err)
            )
            logging.error(f"{error_title}: {json_err}")
            self.task_error.emit(error_title, user_message)
        except Exception as e_thread:
            if "API_KEY_MISSING_MP_THREAD" in str(e_thread):
                error_title = ptr("Chave API Materials Project Necessária")
                user_message = (
                    ptr("A chave da API do Materials Project não foi configurada ou é inválida.\nPor favor, configure-a em 'Configuração > Chave Materials Project...'.")
                )
                logging.error(f"{error_title} (detectado na thread): {e_thread}")
                self.task_error.emit(error_title, user_message)
            else:
                error_context_final = context_for_error
                logging.exception(
                    f"Erro inesperado durante {error_context_final} na thread Worker:"
                )
                self.task_error.emit(
                    f"Erro em {error_context_final}",
                    f"Falha inesperada na thread:\n{type(e_thread).__name__}: {str(e_thread)}",
                )


class MaterialsApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(get_full_title())
        self.setMinimumSize(790, 520)

        self.search_cache = {}
        self.is_searching = False
        self.current_worker = None

        self.calculadora_esteq_window_ref = None
        self.tabela_periodica_window_ref = None
        self.historico_dialog_ref = None
        self.calc_prop_massa_dialog_ref = None
        self.phasedrx_window_ref = None

        self.logo_original_pixmap = None
        self.logo_fading_pixmaps = []
        self.current_logo_blink_index = 0
        self.is_blinking = False
        self.logo_blink_timer = QTimer(self)
        self.logo_blink_timer.timeout.connect(self._update_logo_blink_qt)

        self.pt_selected_elements = set()

        self.api_key_mp = None

        self._current_selected_database = "OQMD"
        self.current_search_terms = ""
        self.cif_export_target = None

        self.search_thread = None
        self.oa_pdf_thread = None
        self.cif_fetch_thread = None
        self.cod_cif_fetch_thread = None
        self.rod_file_fetch_thread = None
        self.doi_fetch_thread = None

        self.btn_consultar_ref = None
        self.btn_oa_pdf_ref = None
        self.doi_entry_ref = None

        self.proxy_settings = {"enabled": False, "http": "", "https": ""}

        self._prepare_logo_animation_pixmaps()
        self.setup_ui()
        self.setStatusBar(QStatusBar(self))
        logging.info("Aplicação MatFinder inicializada.")

    def get_api_key_on_demand(self):
        if self.api_key_mp is None:
            self.api_key_mp = self.read_api_key_from_config()
        return self.api_key_mp

    def _prepare_logo_animation_pixmaps(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Caminho do Asset ---
        logo_path = self.resource_path(os.path.join("matfinder", "assets", "logos", "logo-polvo-verde.png"))
        if os.path.exists(logo_path):
            self.logo_original_pixmap = QPixmap(logo_path)
            if not self.logo_original_pixmap.isNull():
                base_size = QSize(50, 50)
                scaled_original = self.logo_original_pixmap.scaled(
                    base_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.logo_original_pixmap = scaled_original
                num_steps = 10
                self.logo_fading_pixmaps.clear()
                for i in range(num_steps):
                    opacity = (i + 1) / float(num_steps)
                    fading_pixmap = QPixmap(scaled_original.size())
                    fading_pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(fading_pixmap)
                    painter.setOpacity(opacity)
                    painter.drawPixmap(0, 0, scaled_original)
                    painter.end()
                    self.logo_fading_pixmaps.append(fading_pixmap)
            else:
                self.logo_original_pixmap = None
                logging.warning(f"Falha ao carregar pixmap do logo '{logo_path}'.")
        else:
            self.logo_original_pixmap = None
            logging.warning(
                f"Arquivo de logo '{logo_path}' não encontrado para animação."
            )

    def toggle_logo_blink_qt(self, start_blinking: bool):
        # (O conteúdo desta função permanece o mesmo)
        self.is_blinking = start_blinking
        if hasattr(self, "logo_label") and self.logo_label:
            if start_blinking:
                if not self.logo_fading_pixmaps:
                    if self.logo_original_pixmap:
                        self.logo_label.setPixmap(self.logo_original_pixmap)
                    return
                self.current_logo_blink_index = 0
                self.logo_blink_timer.start(100)
            else:
                self.logo_blink_timer.stop()
                if self.logo_original_pixmap:
                    self.logo_label.setPixmap(self.logo_original_pixmap)
        elif not start_blinking:
            self.logo_blink_timer.stop()

    def _update_logo_blink_qt(self):
        # (O conteúdo desta função permanece o mesmo)
        if (
                not self.is_blinking
                or not self.logo_fading_pixmaps
                or not hasattr(self, "logo_label")
                or not self.logo_label.isVisible()
        ):
            self.logo_blink_timer.stop()
            return
        try:
            pixmap_to_show = self.logo_fading_pixmaps[self.current_logo_blink_index]
            self.logo_label.setPixmap(pixmap_to_show)
            self.current_logo_blink_index = (
                                                    self.current_logo_blink_index + 1
                                            ) % len(self.logo_fading_pixmaps)
        except IndexError:
            logging.error("Erro de índice na animação do logo.")
            self.toggle_logo_blink_qt(False)
        except Exception as e:
            logging.exception("Erro em _update_logo_blink_qt:")
            self.toggle_logo_blink_qt(False)

    def resource_path(self, relative_path):
        # (O conteúdo desta função permanece o mesmo)
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        return os.path.join(base_path, relative_path)

    def _api_key_path(self):
        """Caminho GRAVÁVEL da chave (cwd = pasta de dados definida no boot).
        A chave NÃO é mais empacotada no .exe (era um vazamento de segurança)."""
        return os.path.join(os.getcwd(), "config.txt")

    def read_api_key_from_config(self):
        # Lê de um local gravável (cwd). Fallback: config.txt da fonte (modo dev).
        candidates = [
            self._api_key_path(),
            self.resource_path(os.path.join("matfinder", "assets", "config", "config.txt")),
        ]
        for config_path in candidates:
            try:
                with open(config_path, "r") as f:
                    key = f.readline().strip()
                if (
                        key
                        and key != "COLOQUE_A_SUA_CHAVE_DA_API_DO_MATERIALS_PROJECT_AQUI"
                ):
                    logging.info(f"Chave API MP carregada de '{config_path}'.")
                    return key
            except FileNotFoundError:
                continue
            except Exception as e:
                logging.error(f"Erro ao ler chave de API de '{config_path}': {e}")

        logging.warning(ptr("Chave API MP não encontrada ou inválida."))
        return None

    def save_api_key_to_config(self, api_key):
        config_path = self._api_key_path()
        try:
            with open(config_path, "w") as f:
                f.write(api_key)
            logging.info(f"Chave da API salva em {config_path}")
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar a chave da API em '{config_path}': {e}")
            QMessageBox.critical(
                self,
                ptr("Erro ao Salvar Chave"),
                ptr("Não foi possível salvar a chave da API em '{}':\n{}").format(config_path, e),
            )
        return False

    def open_api_key_dialog(self):
        # Diálogo com campo da chave + ajuda "Como conseguir" (passos + link).
        # Sem restrição de tamanho: as chaves do MP variam (não são sempre 32).
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox

        current_key = self.get_api_key_on_demand() or ""
        dlg = QDialog(self)
        dlg.setWindowTitle(tr('dialogs.api_key.title'))
        dlg.setMinimumWidth(480)
        lay = QVBoxLayout(dlg)

        lay.addWidget(QLabel(tr('dialogs.api_key.prompt')))
        edit = QLineEdit(current_key)
        edit.setEchoMode(QLineEdit.EchoMode.Normal)
        lay.addWidget(edit)

        help_lbl = QLabel(tr('dialogs.api_key.how_to'))
        help_lbl.setWordWrap(True)
        help_lbl.setStyleSheet(
            "color:#444; background:#f4f4f4; padding:8px; border-radius:4px;"
        )
        lay.addWidget(help_lbl)

        link = QLabel(
            ptr("<a href=\"https://legacy.materialsproject.org/dashboard\">{}</a>").format(tr('dialogs.api_key.open_dashboard'))
        )
        link.setOpenExternalLinks(True)
        link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        lay.addWidget(link)

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_key = edit.text().strip()
            if new_key:
                if self.save_api_key_to_config(new_key):
                    self.api_key_mp = new_key
                    QMessageBox.information(
                        self,
                        tr('dialogs.api_key.saved'),
                        tr('dialogs.api_key.saved_msg'),
                    )
                    logging.info("Nova chave API do Materials Project salva.")
            else:
                QMessageBox.warning(
                    self, tr('dialogs.api_key.invalid'), tr('dialogs.api_key.invalid_msg')
                )

    def open_proxy_config_dialog(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Importação Local ---
        from matfinder.ui_dialogs import ProxyConfigDialog
        dialog = ProxyConfigDialog(self.proxy_settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.proxy_settings = dialog.get_settings()
            logging.info(
                f"Configurações de Proxy (sessão atual): {self.proxy_settings}"
            )
            if self.proxy_settings["enabled"]:
                QMessageBox.information(
                    self,
                    tr('dialogs.proxy.configured'),
                    tr('dialogs.proxy.configured_msg',
                       http=self.proxy_settings['http'],
                       https=self.proxy_settings['https']),
                )
            else:
                QMessageBox.information(
                    self,
                    tr('dialogs.proxy.disabled'),
                    tr('dialogs.proxy.disabled_msg'),
                )

    def _get_proxies_dict(self):
        # (O conteúdo desta função permanece o mesmo)
        if self.proxy_settings.get("enabled"):
            proxies = {}
            http_proxy = self.proxy_settings.get("http", "").strip()
            https_proxy = self.proxy_settings.get("https", "").strip()
            if http_proxy:
                proxies["http"] = http_proxy
            if https_proxy:
                proxies["https"] = https_proxy
            return proxies if proxies else None
        return None

    def setup_ui(self):
        # (O conteúdo desta função permanece o mesmo)
        self.set_icon()
        self.create_menu()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self.create_database_selection_frame(main_layout)
        self.create_main_search_frame(main_layout)

        self.results_display_widget_container = QWidget()
        self.results_display_layout = QVBoxLayout(
            self.results_display_widget_container
        )
        self.results_display_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.results_display_widget_container, 1)

        self.create_results_treeview_oqmd_mp()
        self.create_results_tableview_cod_rod()

        self.results_display_layout.addWidget(self.tree_oqmd_mp)
        self.results_display_layout.addWidget(self.table_cod_rod)
        self.table_cod_rod.setVisible(False)

        self.create_bottom_frame(main_layout)

    def set_icon(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Caminho do Asset ---
        icon_path_str = self.resource_path(os.path.join("matfinder", "assets", "icons", "polvo.ico"))
        if os.path.exists(icon_path_str):
            self.setWindowIcon(QIcon(icon_path_str))
        else:
            logging.warning(f"Ícone da aplicação não encontrado em: {icon_path_str}")

    def create_menu(self):
        """Cria o menu principal com suporte a tradução."""
        menubar = self.menuBar()

        # Menu Arquivo
        menu_arquivo = menubar.addMenu(tr('menu.file.title'))
        historico_action = QAction(
            QIcon.fromTheme("document-open-recent"), tr('menu.file.history'), self
        )
        historico_action.setStatusTip(tr('menu.file.history_tip'))
        historico_action.triggered.connect(self.open_search_history_dialog)
        menu_arquivo.addAction(historico_action)

        # Opção de Log
        log_action = QAction(tr('menu.file.log', default='Log do Sistema'), self)
        log_action.setStatusTip(tr('menu.file.log_tip', default='Visualizar logs do sistema'))
        log_action.triggered.connect(self.open_log_viewer)
        menu_arquivo.addAction(log_action)

        menu_arquivo.addSeparator()

        sair_action = QAction(QIcon.fromTheme("application-exit"), tr('menu.file.exit'), self)
        sair_action.setShortcut("Alt+F4")
        sair_action.setStatusTip(tr('menu.file.exit_tip'))
        sair_action.triggered.connect(self.close)
        menu_arquivo.addAction(sair_action)

        # Menu Configuração
        menu_config = menubar.addMenu(tr('menu.config.title'))
        config_api_action = QAction(tr('menu.config.api_key'), self)
        config_api_action.setStatusTip(tr('menu.config.api_key_tip'))
        config_api_action.triggered.connect(self.open_api_key_dialog)
        menu_config.addAction(config_api_action)

        config_proxy_action = QAction(tr('menu.config.proxy'), self)
        config_proxy_action.setStatusTip(tr('menu.config.proxy_tip'))
        config_proxy_action.triggered.connect(self.open_proxy_config_dialog)
        menu_config.addAction(config_proxy_action)

        menu_config.addSeparator()

        # Submenu de Idioma
        language_menu = menu_config.addMenu(tr('menu.config.language'))
        language_menu.setStatusTip(tr('menu.config.language_tip'))

        # Adicionar opções de idioma
        current_lang = get_current_language()
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            lang_action = QAction(lang_name, self)
            lang_action.setCheckable(True)
            lang_action.setChecked(lang_code == current_lang)
            lang_action.setData(lang_code)
            lang_action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            language_menu.addAction(lang_action)

        # Menu Ferramentas
        menu_ferramentas = menubar.addMenu(tr('menu.tools.title'))

        phasedrx_action = QAction(tr('menu.tools.phasedrx'), self)
        phasedrx_action.setStatusTip(tr('menu.tools.phasedrx_tip'))
        phasedrx_action.triggered.connect(self.open_phasedrx_tool)
        menu_ferramentas.addAction(phasedrx_action)
        menu_ferramentas.addSeparator()

        calc_esteq_action = QAction(tr('menu.tools.stoich_calc'), self)
        calc_esteq_action.setStatusTip(tr('menu.tools.stoich_calc_tip'))
        calc_esteq_action.triggered.connect(self.open_calculadora_estequiometrica)
        menu_ferramentas.addAction(calc_esteq_action)

        calc_prop_massa_action = QAction(tr('menu.tools.mass_calc'), self)
        calc_prop_massa_action.setStatusTip(tr('menu.tools.mass_calc_tip'))
        calc_prop_massa_action.triggered.connect(
            self.open_calculadora_proporcao_massa
        )
        menu_ferramentas.addAction(calc_prop_massa_action)

        # Menu Sobre
        menu_sobre = menubar.addMenu(tr('menu.about.title'))

        # "Instrução de uso" ocultada por enquanto (manual desatualizado).
        # Reativar quando o novo manual estiver pronto:
        # instrucoes_action = QAction(tr('menu.about.instructions'), self)
        # instrucoes_action.setStatusTip(tr('menu.about.instructions_tip'))
        # instrucoes_action.triggered.connect(self.open_readme)
        # menu_sobre.addAction(instrucoes_action)

        cite_action = QAction(tr('menu.about.cite'), self)
        cite_action.setStatusTip(tr('menu.about.cite_tip'))
        cite_action.triggered.connect(self.show_citation)
        menu_sobre.addAction(cite_action)

        licenca_action = QAction(tr('menu.about.license'), self)
        licenca_action.setStatusTip(tr('menu.about.license_tip'))
        licenca_action.triggered.connect(self.open_license)
        menu_sobre.addAction(licenca_action)

    def change_language(self, lang_code: str):
        """Altera o idioma da interface - requer reinício para aplicar completamente."""
        current_lang = get_current_language()
        if lang_code == current_lang:
            return

        if set_language(lang_code):
            lang_name = SUPPORTED_LANGUAGES.get(lang_code, lang_code)
            # Mostrar mensagem pedindo para reiniciar
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle(tr('dialogs.language.restart_required'))
            msg.setText(tr('dialogs.language.restart_msg'))
            msg.setInformativeText(tr('dialogs.language.selected', language=lang_name))

            restart_btn = msg.addButton(tr('dialogs.language.restart_button'), QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg.addButton(tr('dialogs.confirm.cancel'), QMessageBox.ButtonRole.RejectRole)

            msg.exec()

            if msg.clickedButton() == restart_btn:
                # Reiniciar o programa
                self._restart_application()
            else:
                # Reverter para o idioma anterior
                set_language(current_lang)

    def _restart_application(self):
        """Reinicia a aplicação para aplicar mudanças de idioma."""
        import subprocess
        import sys

        # Fechar a aplicação atual
        self.close()

        # Reiniciar o programa
        python = sys.executable
        script = sys.argv[0]
        subprocess.Popen([python, script])

        # Sair do processo atual
        QApplication.quit()

    def update_ui_translations(self):
        """Atualiza todos os textos da interface após mudança de idioma."""
        # Atualizar título da janela
        self.setWindowTitle(tr('app.title'))

        # Recriar menu
        self.menuBar().clear()
        self.create_menu()

        # Atualizar labels
        if hasattr(self, 'label_buscar_em') and self.label_buscar_em:
            self.label_buscar_em.setText(tr('search.database_label'))

        if hasattr(self, 'label_elementos_ref') and self.label_elementos_ref:
            self.label_elementos_ref.setText(tr('search.elements_label'))

        if hasattr(self, 'entry_elementos') and self.entry_elementos:
            self.entry_elementos.setPlaceholderText(tr('search.elements_placeholder'))

        if hasattr(self, 'btn_consultar_ref') and self.btn_consultar_ref:
            if self.is_searching:
                self.btn_consultar_ref.setText(tr('search.cancel_button'))
            else:
                self.btn_consultar_ref.setText(tr('search.search_button'))

        # Atualizar cabeçalhos das tabelas
        if hasattr(self, 'tree_oqmd_mp'):
            self.tree_oqmd_mp.setHeaderLabels([
                tr('results.columns.favorite'),
                tr('results.columns.name'),
                tr('results.columns.id'),
                tr('results.columns.spacegroup'),
                tr('results.columns.bandgap'),
                tr('results.columns.formation_energy'),
                tr('results.columns.stability'),
            ])

        if hasattr(self, 'table_cod_rod'):
            columns_cod = [
                tr('results.columns.favorite'),
                tr('results.columns.id'),
                tr('results.columns.file'),
                tr('results.columns.formula'),
                tr('results.columns.system'),
                tr('results.columns.parameters'),
                tr('results.columns.volume'),
                tr('results.columns.reference'),
                tr('results.columns.year'),
            ]
            self.table_cod_rod.setHorizontalHeaderLabels(columns_cod)

        # Atualizar painel inferior
        if hasattr(self, 'db_logos_group') and self.db_logos_group:
            self.db_logos_group.setTitle(tr('bottom_panel.external_databases'))

        if hasattr(self, 'oa_pdf_group') and self.oa_pdf_group:
            self.oa_pdf_group.setTitle(tr('bottom_panel.oa_pdf_downloader'))

        if hasattr(self, 'article_search_group') and self.article_search_group:
            self.article_search_group.setTitle(tr('bottom_panel.article_search'))

        if hasattr(self, 'doi_entry_ref') and self.doi_entry_ref:
            self.doi_entry_ref.setPlaceholderText(tr('bottom_panel.doi_placeholder'))
            self.doi_entry_ref.setToolTip(tr('bottom_panel.doi_tooltip'))

        if hasattr(self, 'btn_oa_pdf_ref') and self.btn_oa_pdf_ref:
            self.btn_oa_pdf_ref.setText(tr('bottom_panel.oa_pdf_button'))
            self.btn_oa_pdf_ref.setToolTip(tr('bottom_panel.oa_pdf_tooltip'))

        # Atualizar botão da tabela periódica
        if hasattr(self, 'btn_tabela_periodica') and self.btn_tabela_periodica:
            self.btn_tabela_periodica.setText(tr('search.periodic_table_button'))

        logging.info(f"Interface atualizada para idioma: {get_current_language()}")

    def create_database_selection_frame(self, parent_layout):
        """Cria o frame de seleção de base de dados."""
        db_frame_widget = QWidget()
        db_layout = QHBoxLayout(db_frame_widget)
        db_layout.setContentsMargins(5, 0, 5, 0)

        self.label_buscar_em = QLabel(tr('search.database_label'))
        db_layout.addWidget(self.label_buscar_em)

        self.db_combobox = QComboBox()

        model = QStandardItemModel(self.db_combobox)

        db_options = [
            ("OQMD", tr('databases.oqmd')),
            ("Materials Project", tr('databases.mp')),
            ("COD", tr('databases.cod')),
            ("ROD", tr('databases.rod'))
        ]

        for text, tooltip in db_options:
            item = QStandardItem(text)
            item.setToolTip(tooltip)
            model.appendRow(item)
            if text == self._current_selected_database:
                self.db_combobox.setCurrentText(text)

        self.db_combobox.setModel(model)
        self.db_combobox.setFixedWidth(180)
        self.db_combobox.currentTextChanged.connect(self.on_database_change)
        db_layout.addWidget(self.db_combobox)

        db_layout.addStretch(1)
        parent_layout.addWidget(db_frame_widget)

    def on_database_change(self, selected_text: str):
        # (O conteúdo desta função permanece o mesmo)
        if self.is_searching:
            self.cancel_search()
            logging.info(f"Busca cancelada devido à mudança de base de dados para {selected_text}")

        self._current_selected_database = selected_text
        logging.info(f"Base de dados alterada para: {self._current_selected_database}")

        cached_results = self.search_cache.get(selected_text)
        if cached_results:
            logging.info(f"Encontrado cache para {selected_text}. Exibindo resultados cacheados.")
            self.populate_results_display(cached_results, selected_text)
        else:
            self.clear_results_display()
            if self._current_selected_database == "COD" or self._current_selected_database == "ROD":
                self.entry_elementos.setPlaceholderText(ptr("Elementos (ex: C, H, O)"))
                self.entry_elementos.setToolTip(
                    ptr("Para {}, insira elementos separados por vírgula.").format(self._current_selected_database)
                )
            else:
                self.entry_elementos.setPlaceholderText(ptr("Elementos (ex: Sm, Fe, O)"))
                self.entry_elementos.setToolTip(
                    ptr("Para OQMD/MP, insira elementos separados por vírgula.")
                )
            if hasattr(self, "entry_elementos") and self.entry_elementos.text().strip():
                logging.info("Refazendo a busca para a nova base de dados selecionada (sem cache).")
                self.start_search()
            else:
                self.statusBar().clearMessage()

    def create_main_search_frame(self, parent_layout):
        """Cria o frame de busca principal."""
        search_frame_widget = QWidget()
        search_layout = QHBoxLayout(search_frame_widget)
        search_layout.setContentsMargins(5, 2, 5, 2)
        search_layout.addStretch(1)

        self.label_elementos_ref = QLabel(tr('search.elements_label'))
        search_layout.addWidget(self.label_elementos_ref)

        self.entry_elementos = QLineEdit()
        self.entry_elementos.setPlaceholderText(tr('search.elements_placeholder'))
        self.entry_elementos.setMinimumWidth(150)
        self.entry_elementos.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        self.entry_elementos.returnPressed.connect(self.toggle_search_cancellation)
        search_layout.addWidget(self.entry_elementos)

        self.btn_consultar_ref = QPushButton(tr('search.search_button'))
        self.btn_consultar_ref.clicked.connect(self.toggle_search_cancellation)
        search_layout.addWidget(self.btn_consultar_ref)

        self.logo_label = QLabel()
        if self.logo_original_pixmap:
            self.logo_label.setPixmap(self.logo_original_pixmap)
        else:
            self.logo_label.setText(ptr("Logo"))
        self.logo_label.setFixedSize(50, 50)
        search_layout.addWidget(self.logo_label)

        self.btn_tabela_periodica = QPushButton(tr('search.periodic_table_button'))
        self.btn_tabela_periodica.clicked.connect(self.open_periodic_table)
        search_layout.addWidget(self.btn_tabela_periodica)

        search_layout.addStretch(1)
        parent_layout.addWidget(search_frame_widget)

    def create_results_treeview_oqmd_mp(self):
        """Cria o TreeView de resultados para OQMD/MP."""
        self.tree_oqmd_mp = QTreeWidget()
        self.initial_columns_oqmd_mp = (
            tr('results.columns.favorite'),
            tr('results.columns.name'),
            tr('results.columns.id'),
            tr('results.columns.spacegroup'),
            tr('results.columns.bandgap'),
            tr('results.columns.formation_energy'),
            tr('results.columns.stability'),
        )
        self.tree_oqmd_mp.setColumnCount(len(self.initial_columns_oqmd_mp))
        self.tree_oqmd_mp.setHeaderLabels(self.initial_columns_oqmd_mp)

        headers = self.tree_oqmd_mp.header()
        headers.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        headers.resizeSection(0, 30)
        headers.resizeSection(1, 120)
        headers.resizeSection(2, 80)
        headers.resizeSection(3, 110)
        headers.resizeSection(4, 120)
        headers.resizeSection(5, 150)
        headers.setStretchLastSection(True)

        headers.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # --- CORREÇÃO: Remove a indentação padrão da árvore ---
        self.tree_oqmd_mp.setIndentation(0)

        self.tree_oqmd_mp.setSortingEnabled(True)
        self.tree_oqmd_mp.setAlternatingRowColors(True)
        self.tree_oqmd_mp.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_oqmd_mp.customContextMenuRequested.connect(
            self.show_results_popup_menu
        )
        self.tree_oqmd_mp.itemDoubleClicked.connect(self.handle_results_double_click)
        self.tree_oqmd_mp.setStyleSheet(
            """
            QTreeView::item:selected { background-color: #e0efff; color: black; }
            QTreeView::item:selected:active { background-color: #cce6ff; }
            QTreeView::item:selected:!active { background-color: #f0f8ff; }
            """
        )
        self.tree_oqmd_mp.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def create_results_tableview_cod_rod(self):
        """Cria tabela de resultados COD/ROD com design moderno e elegante."""
        self.table_cod_rod = QTableWidget()

        # Colunas organizadas e com nomes traduzidos
        self.columns_cod = [
            tr('results.columns.favorite'),
            tr('results.columns.id'),
            tr('results.columns.file'),
            tr('results.columns.formula'),
            tr('results.columns.system'),
            tr('results.columns.parameters'),
            tr('results.columns.volume'),
            tr('results.columns.reference'),
            tr('results.columns.year'),
        ]
        self.columns_rod = [
            tr('results.columns.favorite'),
            tr('results.columns.id'),
            tr('results.columns.file'),
            tr('results.columns.formula'),
            tr('results.columns.system'),
            tr('results.columns.parameters'),
            tr('results.columns.volume'),
            tr('results.columns.reference'),
            tr('results.columns.year'),
        ]

        self.table_cod_rod.setColumnCount(len(self.columns_cod))
        self.table_cod_rod.setHorizontalHeaderLabels(self.columns_cod)

        # Configurações básicas
        self.table_cod_rod.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_cod_rod.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_cod_rod.setAlternatingRowColors(True)
        self.table_cod_rod.setShowGrid(False)  # Remove linhas de grade completamente
        self.table_cod_rod.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_cod_rod.customContextMenuRequested.connect(self.show_results_popup_menu)
        self.table_cod_rod.itemDoubleClicked.connect(self.handle_results_double_click)
        self.table_cod_rod.setWordWrap(False)
        self.table_cod_rod.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.table_cod_rod.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table_cod_rod.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table_cod_rod.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # DESIGN MODERNO E ELEGANTE - CORRIGIDO
        self.table_cod_rod.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                gridline-color: transparent;
                font-size: 10pt;
                selection-background-color: #2196F3;
                selection-color: white;
                show-decoration-selected: 1;
            }
            
            QTableWidget::item {
                padding: 8px 12px;
                border: none;
                border-bottom: 1px solid #F5F5F5;
            }
            
            QTableWidget::item:selected {
                background-color: #2196F3 !important;
                color: white !important;
                font-weight: 500;
                border: none;
            }
            
            QTableWidget::item:selected:!active {
                background-color: #42A5F5 !important;
                color: white !important;
            }
            
            QTableWidget::item:hover:!selected {
                background-color: #E3F2FD;
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #FAFAFA, stop:1 #F0F0F0);
                color: #424242;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid #2196F3;
                border-right: 1px solid #E0E0E0;
                font-weight: bold;
                font-size: 10pt;
                text-align: center;
            }
            
            QHeaderView::section:first {
                border-left: none;
            }
            
            QHeaderView::section:last {
                border-right: none;
            }
            
            QHeaderView::section:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #E3F2FD, stop:1 #BBDEFB);
            }
            
            QTableWidget::item:alternate {
                background-color: #FAFAFA;
            }
            
            QTableWidget::item:alternate:selected {
                background-color: #2196F3 !important;
                color: white !important;
            }
            
            QScrollBar:vertical {
                background-color: #F5F5F5;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #BDBDBD;
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #9E9E9E;
            }
            
            QScrollBar:horizontal {
                background-color: #F5F5F5;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #BDBDBD;
                border-radius: 6px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #9E9E9E;
            }
        """)

        # Configuração inteligente de colunas
        header_cod_rod = self.table_cod_rod.horizontalHeader()
        header_cod_rod.setStretchLastSection(False)

        # Coluna 0: Favorito (★)
        header_cod_rod.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_cod_rod.resizeSection(0, 35)

        # Coluna 1: ID
        header_cod_rod.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_cod_rod.setMinimumSectionSize(70)

        # Coluna 2: Arquivo (Link CIF/ROD)
        header_cod_rod.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header_cod_rod.resizeSection(2, 80)

        # Coluna 3: Fórmula
        header_cod_rod.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header_cod_rod.resizeSection(3, 140)

        # Coluna 4: Sistema (Grupo Espacial)
        header_cod_rod.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header_cod_rod.resizeSection(4, 110)

        # Coluna 5: Parâmetros da Célula
        header_cod_rod.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header_cod_rod.resizeSection(5, 240)

        # Coluna 6: Volume
        header_cod_rod.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header_cod_rod.setMinimumSectionSize(80)

        # Coluna 7: Bibliografia (Stretch - ocupa espaço restante)
        header_cod_rod.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        # Coluna 8: Ano
        header_cod_rod.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        header_cod_rod.resizeSection(8, 60)

        # Altura das linhas mais confortável
        self.table_cod_rod.verticalHeader().setDefaultSectionSize(42)
        self.table_cod_rod.verticalHeader().setVisible(False)

    def create_bottom_frame(self, parent_layout):
        """Cria o painel inferior com links externos e busca."""
        bottom_container_widget = QWidget()
        bottom_container_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        bottom_main_layout = QHBoxLayout(bottom_container_widget)
        bottom_main_layout.setContentsMargins(5, 5, 5, 5)

        # GroupBox de bases de dados externas
        self.db_logos_group = QGroupBox(tr('bottom_panel.external_databases'))
        db_logos_layout = QHBoxLayout(self.db_logos_group)

        # --- ALTERAÇÃO DE REATORAÇÃO: Caminhos dos Assets ---
        # Todos os caminhos de logo são atualizados para 'matfinder/assets/logos/'
        logos_info = {
            "icsd": (
                os.path.join("matfinder", "assets", "logos", "icsd_only_logo.png"),
                "https://icsd.fiz-karlsruhe.de/search/basic.xhtml",
            ),
            "oqmd": (os.path.join("matfinder", "assets", "logos", "new_logo_oqmd.png"), "https://oqmd.org/"),
            "mp": (os.path.join("matfinder", "assets", "logos", "mp_color.png"), "https://legacy.materialsproject.org/"),
            "cod": (os.path.join("matfinder", "assets", "logos", "cod_logo.svg"), "http://www.crystallography.net/cod/"),
            "rod": (os.path.join("matfinder", "assets", "logos", "ROD.jpg"), "https://solsa.crystallography.net/rod/"),
        }
        # O resto da lógica para criar os botões de logo permanece o mesmo
        for name, (path, url) in logos_info.items():
            logo_path_str = self.resource_path(path)
            btn = QPushButton()
            target_logical_icon_size = QSize(60, 30)

            logo_exists = os.path.exists(logo_path_str)
            if not logo_exists:
                logging.warning(f"Arquivo de logo '{logo_path_str}' para {name.upper()} não encontrado. Usando texto.")

            if logo_exists:
                if logo_path_str.lower().endswith(".svg"):
                    renderer = QSvgRenderer(logo_path_str)
                    if renderer.isValid():
                        dpr = (
                            self.devicePixelRatioF()
                            if hasattr(self, "devicePixelRatioF")
                            else 1.0
                        )
                        physical_width = int(target_logical_icon_size.width() * dpr)
                        physical_height = int(target_logical_icon_size.height() * dpr)
                        render_pixmap = QPixmap(physical_width, physical_height)
                        render_pixmap.setDevicePixelRatio(dpr)
                        render_pixmap.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(render_pixmap)
                        renderer.render(painter)
                        painter.end()
                        btn.setIcon(QIcon(render_pixmap))
                        btn.setIconSize(target_logical_icon_size)
                        btn.setFixedSize(
                            target_logical_icon_size.width() + 10,
                            target_logical_icon_size.height() + 10,
                        )
                    else:
                        btn.setText(name.upper())
                else:
                    pixmap = QPixmap(logo_path_str)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            target_logical_icon_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        btn.setIcon(QIcon(scaled_pixmap))
                        btn.setIconSize(scaled_pixmap.size())
                        btn.setFixedSize(
                            scaled_pixmap.size().width() + 10,
                            scaled_pixmap.size().height() + 10,
                        )
                    else:
                        btn.setText(name.upper())
            else:
                btn.setText(name.upper())

            btn.setToolTip(tr('bottom_panel.open_database', name=name.upper(), url=url))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(
                lambda checked=False, u=url: QDesktopServices.openUrl(QUrl(u))
            )
            db_logos_layout.addWidget(btn)
        db_logos_layout.addStretch(1)
        bottom_main_layout.addWidget(self.db_logos_group)

        # GroupBox do PDF de acesso aberto
        self.oa_pdf_group = QGroupBox(tr('bottom_panel.oa_pdf_downloader'))
        oa_pdf_layout = QVBoxLayout(self.oa_pdf_group)
        self.doi_entry_ref = QLineEdit()
        self.doi_entry_ref.setPlaceholderText(tr('bottom_panel.doi_placeholder'))
        self.doi_entry_ref.returnPressed.connect(self.trigger_oa_pdf_download)
        oa_pdf_layout.addWidget(self.doi_entry_ref)
        self.btn_oa_pdf_ref = QPushButton(tr('bottom_panel.oa_pdf_button'))
        self.btn_oa_pdf_ref.clicked.connect(self.trigger_oa_pdf_download)
        oa_pdf_layout.addWidget(self.btn_oa_pdf_ref)
        oa_pdf_layout.addStretch(1)
        bottom_main_layout.addWidget(self.oa_pdf_group)

        # GroupBox de busca de artigos
        self.article_search_group = QGroupBox(tr('bottom_panel.article_search'))
        article_search_layout = QVBoxLayout(self.article_search_group)
        google_scholar_widget = self._create_search_box_widget(
            tr('bottom_panel.google_scholar'), "https://scholar.google.com.br/scholar?q="
        )
        sciencedirect_widget = self._create_search_box_widget(
            tr('bottom_panel.sciencedirect'), "https://www.sciencedirect.com/search?qs="
        )
        article_search_layout.addWidget(google_scholar_widget)
        article_search_layout.addWidget(sciencedirect_widget)
        article_search_layout.addStretch(1)
        bottom_main_layout.addWidget(self.article_search_group)

        parent_layout.addWidget(bottom_container_widget)

    def _create_search_box_widget(
            self, label_text: str, base_url: str
    ) -> QWidget:
        """Cria widget de busca com label e campo de texto."""
        search_box_widget = QWidget()
        layout = QVBoxLayout(search_box_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        label = QLabel(label_text)
        layout.addWidget(label)
        entry = QLineEdit()
        entry.setPlaceholderText(tr('bottom_panel.search_placeholder'))
        entry.returnPressed.connect(
            lambda: self._search_article_site_triggered(base_url, entry)
        )
        layout.addWidget(entry)
        return search_box_widget

    def _search_article_site_triggered(
            self, base_url: str, query_edit_widget: QLineEdit
    ):
        # (O conteúdo desta função permanece o mesmo)
        query = query_edit_widget.text().strip()
        if query:
            QDesktopServices.openUrl(QUrl(f"{base_url}{quote(query)}"))
            logging.info(f"Busca rápida de artigo acionada para: {base_url}{query}")
        else:
            QMessageBox.information(
                self, tr('search.empty_title'), tr('search.empty_message')
            )

    def trigger_oa_pdf_download(self):
        doi = self.doi_entry_ref.text().strip()
        if not doi:
            QMessageBox.warning(self, tr('oa_pdf.doi_missing_title'), tr('oa_pdf.doi_missing_message'))
            return

        if self.oa_pdf_thread and self.oa_pdf_thread.is_alive():
            QMessageBox.information(
                self, tr('oa_pdf.in_progress_title'), tr('oa_pdf.in_progress_message')
            )
            return

        logging.info(f"Buscando PDF de acesso aberto para o DOI: {doi}")
        self.statusBar().showMessage(
            ptr("Buscando PDF de acesso aberto para o DOI: {}...").format(doi), 3000
        )
        self.btn_oa_pdf_ref.setEnabled(False)
        self.doi_entry_ref.setEnabled(False)

        oa_worker = Worker(self._fetch_oa_pdf_logic, "oa_pdf", doi)
        oa_worker.oa_pdf_downloaded.connect(self.handle_oa_pdf_ready)
        oa_worker.task_error.connect(self.handle_oa_pdf_fetch_error)

        self.oa_pdf_thread = threading.Thread(target=oa_worker.run)
        self.oa_pdf_thread.daemon = True
        self.oa_pdf_thread.start()

    def _fetch_oa_pdf_logic(self, doi: str):
        """Procura e baixa a versao de ACESSO ABERTO (legal) do artigo a partir do
        DOI, via OpenAlex e Unpaywall. Retorna (pdf_bytes, filename) ou levanta erro."""
        from matfinder.core import api_logic
        return api_logic.fetch_oa_pdf(doi, proxies=self._get_proxies_dict())

    @Slot(bytes, str)
    def handle_oa_pdf_ready(self, pdf_content_bytes: bytes, suggested_filename: str):
        self.statusBar().clearMessage()
        self.btn_oa_pdf_ref.setEnabled(True)
        self.doi_entry_ref.setEnabled(True)

        downloads_path = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        if not downloads_path:
            downloads_path = os.path.expanduser("~")

        filePath, _ = QFileDialog.getSaveFileName(
            self,
            ptr("Salvar PDF do Artigo"),
            os.path.join(downloads_path, suggested_filename),
            ptr("PDF Files (*.pdf)"),
        )
        if filePath:
            try:
                with open(filePath, "wb") as f:
                    f.write(pdf_content_bytes)
                self.statusBar().showMessage(tr('status.file_saved', path=filePath), 7000)
                QMessageBox.information(
                    self, tr('oa_pdf.download_complete'), tr('oa_pdf.file_saved', path=filePath)
                )
                logging.info(f"Artigo (acesso aberto) salvo em: {filePath}")
                if not QDesktopServices.openUrl(QUrl.fromLocalFile(filePath)):
                    QMessageBox.warning(
                        self,
                        tr('dialogs.error.warning'),
                        tr('oa_pdf.cannot_open_file', path=filePath),
                    )
            except IOError as ioe:
                QMessageBox.critical(
                    self,
                    tr('oa_pdf.save_error'),
                    tr('oa_pdf.save_io_error', error=str(ioe)),
                )
                logging.exception(f"Erro de E/S ao salvar PDF em {filePath}:")
            except Exception as e:
                QMessageBox.critical(
                    self, tr('oa_pdf.save_error'), tr('oa_pdf.save_generic_error', error=str(e))
                )
                logging.exception(f"Erro inesperado ao salvar PDF em {filePath}:")
        else:
            QMessageBox.information(
                self, tr('oa_pdf.download_cancelled_title'), tr('oa_pdf.download_cancelled_msg')
            )
            self.statusBar().showMessage(tr('oa_pdf.download_cancelled_status'), 3000)

    @Slot(str, str)
    def handle_oa_pdf_fetch_error(self, error_title: str, error_message: str):
        self.statusBar().clearMessage()
        self.btn_oa_pdf_ref.setEnabled(True)
        self.doi_entry_ref.setEnabled(True)
        QMessageBox.critical(self, error_title, error_message)

    def toggle_search_cancellation(self):
        # (O conteúdo desta função permanece o mesmo)
        if self.is_searching:
            self.cancel_search()
        else:
            self.start_search()

    def cancel_search(self):
        # (O conteúdo desta função permanece o mesmo)
        if not self.is_searching:
            return

        logging.info("Tentativa de cancelar a busca atual.")

        if self.current_worker:
            try:
                self.current_worker.material_search_results_ready.disconnect(self.handle_results_ready)
                self.current_worker.task_error.disconnect(self.handle_search_error)
            except (RuntimeError, TypeError):
                pass

        self.reset_search_ui_state()
        self.statusBar().showMessage(tr('search.search_cancelled'), 3000)

    def reset_search_ui_state(self):
        # (O conteúdo desta função permanece o mesmo)
        self.is_searching = False
        self.current_worker = None
        self.toggle_logo_blink_qt(False)
        self.btn_consultar_ref.setText(tr('search.search_button'))
        self.entry_elementos.setEnabled(True)
        self.db_combobox.setEnabled(True)

    def start_search(self):
        # (O conteúdo desta função permanece o mesmo)
        elements_input_str = self.entry_elementos.text().strip()
        if not elements_input_str:
            QMessageBox.warning(
                self, tr('search.empty_title'), tr('search.enter_elements')
            )
            return

        if self.current_search_terms != elements_input_str:
            self.search_cache.clear()
            self.current_search_terms = elements_input_str
            logging.info(f"Nova busca iniciada para '{elements_input_str}'. Cache limpo.")

        self.clear_results_display()
        self.set_ui_for_searching(True)

        elements_list = [
            e.strip().capitalize() for e in elements_input_str.split(",") if e.strip()
        ]
        if not all(e.isalpha() and 1 <= len(e) <= 2 for e in elements_list):
            QMessageBox.warning(
                self,
                tr('search.invalid_format_title'),
                tr('search.invalid_format_message'),
            )
            self.set_ui_for_searching(False)
            logging.warning(
                f"Formato de elementos inválido para busca: {elements_input_str}"
            )
            return

        db_choice = self._current_selected_database

        cached_results = self.search_cache.get(db_choice)
        if cached_results:
            logging.info(f"Busca para '{elements_input_str}' em '{db_choice}' encontrada no cache.")
            self.populate_results_display(cached_results, db_choice)
            self.set_ui_for_searching(False)
            return

        worker = Worker(
            self.load_results_from_selected_db,
            "material_search",
            elements_list,
            db_choice,
        )
        worker.material_search_results_ready.connect(self.handle_results_ready)
        worker.task_error.connect(self.handle_search_error)

        self.current_worker = worker

        self.search_thread = threading.Thread(target=worker.run)
        self.search_thread.daemon = True
        self.search_thread.start()

    def set_ui_for_searching(self, searching: bool):
        # (O conteúdo desta função permanece o mesmo)
        self.is_searching = searching
        self.toggle_logo_blink_qt(searching)
        self.entry_elementos.setEnabled(not searching)
        self.db_combobox.setEnabled(not searching)
        if searching:
            self.btn_consultar_ref.setText(tr('search.cancel_button'))
            self.statusBar().showMessage(tr('search.searching', db=self._current_selected_database), 0)
        else:
            self.btn_consultar_ref.setText(tr('search.search_button'))
            if not self.statusBar().currentMessage().startswith(tr('search.search_cancelled')):
                self.statusBar().clearMessage()

    def load_results_from_selected_db(
            self, elements_list: list, db_choice: str
    ):
        # (O conteúdo desta função permanece o mesmo,
        # pois as chamadas 'COD_api_logic.search_cod_by_elements'
        # já estão corretas após a importação no topo do ficheiro ser corrigida)
        results_raw = []
        proxies = self._get_proxies_dict()
        if db_choice == "OQMD":
            results_raw = self._query_oqmd(elements_list, proxies)
        elif db_choice == "Materials Project":
            if self.get_api_key_on_demand() is None:
                raise Exception("API_KEY_MISSING_MP_THREAD")
            results_raw = self._query_mp(elements_list, proxies)
        elif db_choice == "COD":
            results_raw = COD_api_logic.search_cod_by_elements(
                elements_list, result_format="json", strict_elements=True
            )
            if results_raw is None:
                results_raw = []
                logging.warning(
                    ptr("Busca JSON no COD falhou ou retornou None na função principal.")
                )
        elif db_choice == "ROD":
            results_raw = self._query_rod(elements_list, proxies=proxies)
            if results_raw is None:
                results_raw = []
                logging.warning(
                    ptr("Busca JSON na ROD falhou ou retornou None.")
                )
        return results_raw, db_choice

    def _query_oqmd(self, elements_list: list, proxies=None):
        # Carregar requests sob demanda
        import requests as _requests

        url_base = "http://oqmd.org/oqmdapi/formationenergy"
        elements_str_param = ",".join(elements_list)
        # --- ALTERAÇÃO: Adicionada 'icsd_id' aos campos solicitados ---
        url = (
            f"{url_base}?fields=name,entry_id,spacegroup,ntypes,band_gap,delta_e,stability,icsd_id"
            f"&filter=element_set=({elements_str_param}) AND ntypes={len(elements_list)}"
        )
        logging.info(f"Query OQMD: {url}")
        try:
            response = _requests.get(url, timeout=45, proxies=proxies)
            response.raise_for_status()
            return response.json().get("data", [])
        except _requests.exceptions.Timeout as timeout_err:
            logging.error(f"Timeout na query OQMD ({url}): {timeout_err}")
            raise
        except _requests.exceptions.HTTPError as http_err:
            logging.error(
                f"Erro HTTP {http_err.response.status_code} na query OQMD ({url}): {http_err}"
            )
            raise
        except _requests.exceptions.ConnectionError as conn_err:
            logging.error(f"Erro de conexão na query OQMD ({url}): {conn_err}")
            raise
        except _requests.exceptions.RequestException as req_err:
            logging.error(
                f"Erro genérico de requisição na query OQMD ({url}): {req_err}"
            )
            raise
        except json.JSONDecodeError as json_err:
            logging.error(
                f"Erro ao decodificar JSON da resposta OQMD ({url}): {json_err}"
            )
            raise
        except Exception as e:
            logging.exception(f"Erro inesperado na query OQMD ({url}):")
            raise

    def _query_mp(self, elements_list: list, proxies=None):
        # Carregar módulos sob demanda
        _ensure_mp_api()
        _ensure_pymatgen()

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        if getattr(sys, 'frozen', False):
            if sys.stdout is None:
                sys.stdout = io.StringIO()
            if sys.stderr is None:
                sys.stderr = io.StringIO()

        old_proxies_env = {}
        if proxies:
            if "http" in proxies:
                old_proxies_env["HTTP_PROXY"] = os.environ.get("HTTP_PROXY")
                os.environ["HTTP_PROXY"] = proxies["http"]
            if "https" in proxies:
                old_proxies_env["HTTPS_PROXY"] = os.environ.get("HTTPS_PROXY")
                os.environ["HTTPS_PROXY"] = proxies["https"]
        logging.info(
            f"Query Materials Project para elementos: {elements_list} "
            f"com proxies: {proxies if proxies else 'Nenhum'}"
        )
        try:
            with MPRester(api_key=self.api_key_mp) as mpr:
                docs = mpr.materials.summary.search(
                    elements=elements_list,
                    fields=[
                        "formula_pretty", "material_id", "symmetry", "band_gap",
                        "formation_energy_per_atom", "energy_above_hull",
                        "nelements", "database_IDs",
                    ],
                )
                filtered_docs_data = []
                for doc in docs:
                    comp = Composition(doc.formula_pretty)
                    if len(comp.elements) == len(elements_list) and set(
                            e.symbol for e in comp.elements
                    ) == set(elements_list):
                        symmetry_data = doc.symmetry.symbol if doc.symmetry else None
                        crystal_system_value = (
                            doc.symmetry.crystal_system.value
                            if doc.symmetry
                               and hasattr(doc.symmetry, "crystal_system")
                               and doc.symmetry.crystal_system
                            else None
                        )
                        db_ids_processed = {}
                        if doc.database_IDs:
                            if hasattr(doc.database_IDs, 'model_dump'):
                                db_ids_processed = doc.database_IDs.model_dump(exclude_none=True)
                            elif isinstance(doc.database_IDs, dict):
                                db_ids_processed = doc.database_IDs
                            else:
                                try:
                                    db_ids_processed = doc.database_IDs.dict(exclude_none=True)
                                except AttributeError:
                                    logging.warning(f"Não foi possível processar database_IDs para {doc.material_id}")

                        doc_data = {
                            "formula_pretty": doc.formula_pretty,
                            "material_id": str(doc.material_id),
                            "symmetry_symbol": symmetry_data,
                            "crystal_system": crystal_system_value,
                            "band_gap": doc.band_gap,
                            "formation_energy_per_atom": doc.formation_energy_per_atom,
                            "energy_above_hull": doc.energy_above_hull,
                            "database_IDs": db_ids_processed,
                        }
                        filtered_docs_data.append(doc_data)
                return filtered_docs_data
        except Exception as exc:
            logging.error(f"Erro na query Materials Project: {exc}")
            raise
        finally:
            if getattr(sys, 'frozen', False):
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            if "HTTP_PROXY" in old_proxies_env:
                if old_proxies_env["HTTP_PROXY"] is None:
                    os.environ.pop("HTTP_PROXY", None)
                else:
                    os.environ["HTTP_PROXY"] = old_proxies_env["HTTP_PROXY"]
            elif proxies and "http" in proxies:
                os.environ.pop("HTTP_PROXY", None)

            if "HTTPS_PROXY" in old_proxies_env:
                if old_proxies_env["HTTPS_PROXY"] is None:
                    os.environ.pop("HTTPS_PROXY", None)
                else:
                    os.environ["HTTPS_PROXY"] = old_proxies_env["HTTPS_PROXY"]
            elif proxies and "https" in proxies:
                os.environ.pop("HTTPS_PROXY", None)

    def _query_rod(self, elements_list: list, result_format: str = "json", timeout: int = 45, proxies=None):
        # Carregar requests sob demanda
        import requests as _requests

        if not elements_list:
            logging.warning(ptr("ROD API: A lista de elementos não pode ser vazia."))
            return []

        params = {}
        for i, el_symbol in enumerate(elements_list):
            if i < 8:
                params[f"el{i + 1}"] = el_symbol.strip().capitalize()
            else:
                logging.warning(
                    f"ROD API: Máximo de 8 elementos suportados para busca. Ignorando extras: {elements_list[8:]}"
                )
                break
        params["format"] = result_format

        logging.info(
            f"ROD API: Buscando por elementos: {', '.join(elements_list)} no formato: {result_format}"
        )

        try:
            response = _requests.get(ROD_SEARCH_BASE_URL, params=params, timeout=timeout, proxies=proxies)
            response.raise_for_status()

            if result_format == "json":
                try:
                    return response.json()
                except json.JSONDecodeError as json_err:
                    logging.error("ROD API: Erro ao decodificar JSON da resposta.")
                    logging.error(f"  Status Code: {response.status_code}")
                    logging.error(f"  Resposta (primeiros 500 chars): {response.text[:500]}")
                    logging.error(f"  Erro JSON: {json_err}")
                    raise
            else:
                return [response.text]

        except _requests.exceptions.Timeout as timeout_err:
            logging.error(f"ROD API: Timeout na requisição: {timeout_err}")
            raise
        except _requests.exceptions.HTTPError as http_err:
            logging.error(f"ROD API: Erro HTTP {http_err.response.status_code}: {http_err}")
            logging.error(f"  Resposta do servidor (primeiros 500 chars): {http_err.response.text[:500]}")
            raise
        except _requests.exceptions.RequestException as req_err:
            logging.error(f"ROD API: Erro de requisição: {req_err}")
            raise
        except Exception as e:
            logging.exception("ROD API: Erro inesperado na query ROD:")
            raise

    @Slot(list, str)
    def handle_results_ready(
            self, raw_results_or_dict: list | dict, db_choice: str
    ):
        # (O conteúdo desta função permanece o mesmo)
        self.set_ui_for_searching(False)
        raw_len = (
            len(raw_results_or_dict)
            if isinstance(raw_results_or_dict, list)
            else "N/A (dict)"
        )
        logging.info(
            f"Resultados recebidos da busca em {db_choice}. "
            f"Número de itens brutos: {raw_len}"
        )

        standardized_results = self._standardize_results_qt(
            raw_results_or_dict, db_choice
        )

        self.search_cache[db_choice] = standardized_results
        logging.info(f"Resultados para '{db_choice}' salvos no cache.")

        self.populate_results_display(standardized_results, db_choice)

        if standardized_results:
            self._add_search_to_history(self.current_search_terms, db_choice)

    @Slot(str, str)
    def handle_search_error(self, error_title: str, error_message: str):
        # (O conteúdo desta função permanece o mesmo)
        self.set_ui_for_searching(False)
        QMessageBox.critical(self, error_title, error_message)

    def _standardize_results_qt(
            self, raw_data: list | dict, source_db: str
    ) -> list:
        # (O conteúdo desta função permanece o mesmo)
        standardized = []
        entries = []
        if source_db == "COD" or source_db == "ROD":
            if isinstance(raw_data, dict):
                possible_keys = [
                    "entries", "result", "data", "items", "results", "entry",
                ]
                for pk in possible_keys:
                    if pk in raw_data and isinstance(raw_data[pk], list):
                        entries = raw_data[pk]
                        break
                if not entries:
                    for key, value in raw_data.items():
                        if (
                                isinstance(value, list)
                                and value
                                and all(isinstance(item, dict) for item in value)
                        ):
                            entries = value
                            break
            elif isinstance(raw_data, list):
                entries = raw_data

            if not entries and raw_data is not None:
                keys_info = (
                    raw_data.keys()
                    if isinstance(raw_data, dict)
                    else "Não é um dicionário"
                )
                logging.warning(
                    f"AVISO ({source_db}): Estrutura JSON inesperada. Chaves recebidas: {keys_info}"
                )
        elif isinstance(raw_data, list):
            entries = raw_data

        if not entries:
            logging.info(f"Nenhuma entrada para padronizar para {source_db}.")
            return standardized

        for item_data in entries:
            if not isinstance(item_data, dict):
                continue
            res = {"source_db": source_db, "raw_data": item_data}
            if source_db == "OQMD":
                stability_val = item_data.get("stability", float("inf"))
                # --- ALTERAÇÃO: Captura o icsd_id ---
                icsd_id = item_data.get("icsd_id")
                icsd_codes = [str(icsd_id)] if icsd_id else []

                res.update(
                    {
                        "name_display": item_data.get("name", "N/A"),
                        "id_display": str(item_data.get("entry_id", "N/A")),
                        "unique_id": f"oqmd-{item_data.get('entry_id', 'N/A')}",
                        "spacegroup_display": item_data.get("spacegroup", "N/A"),
                        "band_gap_display": (
                            f"{float(item_data.get('band_gap', 0)):.4f}"
                            if item_data.get("band_gap") is not None
                            else "N/A"
                        ),
                        "formation_energy_display": (
                            f"{float(item_data.get('delta_e', 0)):.4f}"
                            if item_data.get("delta_e") is not None
                            else "N/A"
                        ),
                        "stability_metric_value": float(stability_val),
                        "is_stable": float(stability_val) <= 0,
                        "stability_tooltip_text": (
                            f"{tr('results.stability_tooltip.convex_hull_oqmd')}:\n"
                            f"{float(stability_val):.4f} eV/{tr('results.stability_tooltip.atom')}"
                        ),
                        "icsd_codes_list": icsd_codes, # Salva a lista de códigos
                    }
                )
            elif source_db == "Materials Project":
                crystal_system_en = item_data.get("crystal_system", "unknown")
                crystal_system_pt = SISTEMAS_CRISTALINOS_PT.get(
                    crystal_system_en.lower() if crystal_system_en else "unknown",
                    SISTEMAS_CRISTALINOS_PT["unknown"],
                )
                database_ids_dict = item_data.get("database_IDs", {})
                raw_icsd_values = database_ids_dict.get("icsd", [])
                if raw_icsd_values is None: raw_icsd_values = []
                icsd_numeric_str_list = []
                if isinstance(raw_icsd_values, list):
                    for code in raw_icsd_values:
                        if isinstance(code, str):
                            numeric_part = code.lower().replace("icsd-", "")
                            if numeric_part.isdigit():
                                icsd_numeric_str_list.append(numeric_part)
                        elif isinstance(code, int):
                            icsd_numeric_str_list.append(str(code))
                elif isinstance(raw_icsd_values, str):
                    numeric_part = raw_icsd_values.lower().replace("icsd-", "")
                    if numeric_part.isdigit():
                        icsd_numeric_str_list.append(numeric_part)
                e_above_hull = item_data.get("energy_above_hull")
                stability_metric = (
                    float(e_above_hull)
                    if e_above_hull is not None
                    else float("inf")
                )
                res.update(
                    {
                        "name_display": item_data.get("formula_pretty", "N/A"),
                        "id_display": str(item_data.get("material_id", "N/A")),
                        "unique_id": f"mp-{item_data.get('material_id', 'N/A')}",
                        "spacegroup_display": item_data.get(
                            "symmetry_symbol", "N/A"
                        ),
                        "crystal_system_pt": crystal_system_pt,
                        "band_gap_display": (
                            f"{float(item_data.get('band_gap')):.4f}"
                            if item_data.get("band_gap") is not None
                            else "N/A"
                        ),
                        "formation_energy_display": (
                            f"{float(item_data.get('formation_energy_per_atom')):.4f}"
                            if item_data.get("formation_energy_per_atom")
                               is not None
                            else "N/A"
                        ),
                        "stability_metric_value": stability_metric,
                        "is_stable": stability_metric <= 0.025,
                        "stability_tooltip_text": (
                            f"{tr('results.stability_tooltip.energy_above_hull_mp')}:\n"
                            f"{stability_metric:.4f} eV/{tr('results.stability_tooltip.atom')}"
                        ),
                        "icsd_codes_list": icsd_numeric_str_list,
                    }
                )
            elif source_db == "COD" or source_db == "ROD":
                id_from_payload = "N/A"
                if source_db == "ROD":
                    id_from_payload = item_data.get("file", "N/A")
                else:
                    id_from_payload = item_data.get("file", item_data.get("id", "N/A"))

                cleaned_id_str = str(id_from_payload).replace(".cif", "")

                if cleaned_id_str.isdigit() and cleaned_id_str != "N/A":
                    res["id_display"] = cleaned_id_str
                else:
                    res["id_display"] = "N/A"
                    if id_from_payload != "N/A":
                        logging.warning(
                            f"ID inválido ou não numérico para {source_db}: '{id_from_payload}' -> '{cleaned_id_str}'")

                prefix = "rod" if source_db == "ROD" else "cod"
                res["unique_id"] = f"{prefix}-{res['id_display']}"

                raw_formula = item_data.get("formula", "N/A")
                cleaned_formula = raw_formula.strip().replace("- ", "").replace(" -", "") if isinstance(raw_formula,
                                                                                                        str) else "N/A"
                res["name_display"] = cleaned_formula
                res["formula_display"] = cleaned_formula

                res["spacegroup_display"] = item_data.get(
                    "sg", item_data.get("spacegroup", "N/A")
                )
                a = item_data.get("a", "")
                b = item_data.get("b", "")
                c_param = item_data.get("c", "")
                alpha = item_data.get("alpha", "")
                beta = item_data.get("beta", "")
                gamma = item_data.get("gamma", "")
                cell_parts = []
                try:
                    if a: cell_parts.append(f"a={float(a):.3f}")
                    if b: cell_parts.append(f"b={float(b):.3f}")
                    if c_param: cell_parts.append(f"c={float(c_param):.3f}")
                    if alpha: cell_parts.append(f"α={float(alpha):.1f}°")
                    if beta: cell_parts.append(f"β={float(beta):.1f}°")
                    if gamma: cell_parts.append(f"γ={float(gamma):.1f}°")
                except ValueError:
                    cell_parts = [f"a={a}", f"b={b}", f"c={c_param}", f"α={alpha}", f"β={beta}", f"γ={gamma}"]
                res["cell_parameters_display"] = ", ".join(filter(None, cell_parts)) if cell_parts else "N/A"

                volume_val = item_data.get("volume", "")
                try:
                    res["volume_display"] = (f"{float(volume_val):.2f}" if volume_val else "N/A")
                except ValueError:
                    res["volume_display"] = str(volume_val) if volume_val else "N/A"

                authors = item_data.get("authors", item_data.get("author", ""))
                title = item_data.get("title", "")
                journal = item_data.get("journal", "")
                year = str(item_data.get("year", ""))
                pub_vol = item_data.get("volume", "")
                if source_db == "COD":
                    pub_vol = item_data.get("journal_volume", item_data.get("vol", pub_vol))

                pub_issue = item_data.get("journal_issue", item_data.get("issue", ""))
                firstpage = str(item_data.get("firstpage", ""))
                lastpage = str(item_data.get("lastpage", ""))
                if source_db == "COD":
                    pub_pages_cod = item_data.get("journal_pages",
                                                  item_data.get("pagerange", item_data.get("pages", "")))
                    if pub_pages_cod:
                        if not firstpage and not lastpage:
                            if isinstance(pub_pages_cod, str) and '-' in pub_pages_cod:
                                parts = pub_pages_cod.split('-')
                                firstpage = parts[0].strip()
                                lastpage = parts[1].strip() if len(parts) > 1 else ""
                            elif isinstance(pub_pages_cod, str):
                                firstpage = pub_pages_cod.strip()

                doi = item_data.get("doi", "")
                bib_parts = []
                author_str = ""
                if isinstance(authors, list):
                    author_names = [auth.get("name", "") for auth in authors if
                                    isinstance(auth, dict) and auth.get("name")]
                    author_str = ", ".join(filter(None, author_names))
                elif isinstance(authors, str):
                    author_str = authors
                if author_str: bib_parts.append(author_str)

                if title and not journal: bib_parts.append(f'"{title}"')
                if journal: bib_parts.append(f"{journal}")
                if year: bib_parts.append(f"{year}")

                page_info_parts = []
                if pub_vol: page_info_parts.append(str(pub_vol))
                if pub_issue: page_info_parts.append(f"({pub_issue})")

                page_range_str = ""
                if firstpage and lastpage:
                    page_range_str = f"{firstpage}-{lastpage}"
                elif firstpage:
                    page_range_str = firstpage
                if page_range_str: page_info_parts.append(f": {page_range_str}")

                if page_info_parts: bib_parts.append("".join(page_info_parts))

                res["bibliography_display"] = ". ".join(filter(None, bib_parts))
                res["doi_display"] = doi
                res["year_display"] = year if year else "N/A"

            standardized.append(res)
        return standardized

    def populate_results_display(self, standardized_results: list, db_choice: str):
        # (O conteúdo desta função permanece o mesmo)
        self.clear_results_display()

        is_cod_rod = db_choice in ("COD", "ROD")
        self.tree_oqmd_mp.setVisible(not is_cod_rod)
        self.table_cod_rod.setVisible(is_cod_rod)

        if not standardized_results:
            QMessageBox.information(
                self,
                tr('search.no_results_title'),
                tr('search.no_results_msg', db=db_choice),
            )
            self.statusBar().showMessage(
                tr('search.no_results_status', query=self.entry_elementos.text(), db=db_choice),
                5000,
            )
            logging.info(
                f"Nenhum resultado encontrado para '{self.entry_elementos.text()}' em {db_choice}."
            )
            return

        if is_cod_rod:
            current_columns = self.columns_rod if db_choice == "ROD" else self.columns_cod
            self.table_cod_rod.setColumnCount(len(current_columns))
            self.table_cod_rod.setHorizontalHeaderLabels(current_columns)

            self.table_cod_rod.setRowCount(len(standardized_results))
            for row, compound_data in enumerate(standardized_results):
                unique_id = compound_data.get("unique_id", "")
                is_fav = favorites_manager.is_favorite(unique_id)

                fav_item = QTableWidgetItem("★" if is_fav else "")
                fav_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                if is_fav:
                    fav_item.setForeground(QColor("#FFA500"))
                    from PySide6.QtGui import QFont
                    font = QFont()
                    font.setPointSize(12)
                    fav_item.setFont(font)
                self.table_cod_rod.setItem(row, 0, fav_item)

                id_item_text = compound_data.get("id_display", "N/A")
                id_item = QTableWidgetItem(id_item_text)
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_cod_rod.setItem(row, 1, id_item)

                link_button_text = "📄 ROD" if db_choice == "ROD" else "📄 CIF"
                btn_link = QPushButton(link_button_text)
                btn_link.setStyleSheet("""
                    QPushButton {
                        background-color: #E3F2FD;
                        color: #1976D2;
                        border: 1px solid #BBDEFB;
                        border-radius: 4px;
                        padding: 4px 12px;
                        font-weight: 500;
                        font-size: 9pt;
                    }
                    QPushButton:hover {
                        background-color: #BBDEFB;
                        border: 1px solid #90CAF9;
                    }
                    QPushButton:pressed {
                        background-color: #90CAF9;
                    }
                    QPushButton:disabled {
                        background-color: #F5F5F5;
                        color: #BDBDBD;
                        border: 1px solid #E0E0E0;
                    }
                """)
                btn_link.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

                id_val_for_button = id_item_text
                formula_val = compound_data.get("formula_display", id_val_for_button)

                if id_val_for_button and id_val_for_button != "N/A":
                    if db_choice == "ROD":
                        btn_link.clicked.connect(
                            lambda chk=False, r_id=id_val_for_button, f_name=formula_val: self.trigger_baixar_rod_file(
                                r_id, f_name
                            )
                        )
                    else:
                        btn_link.clicked.connect(
                            lambda chk=False, c_id=id_val_for_button, f_name=formula_val: self.trigger_baixar_cif_cod(
                                c_id, f_name
                            )
                        )
                else:
                    btn_link.setEnabled(False)
                    btn_link.setText(ptr("N/D"))
                self.table_cod_rod.setCellWidget(row, 2, btn_link)

                # Coluna 3: Fórmula (centralizada, com fonte destaque)
                formula_item = QTableWidgetItem(compound_data.get("formula_display", "N/A"))
                formula_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                from PySide6.QtGui import QFont
                formula_font = QFont()
                formula_font.setPointSize(10)
                formula_font.setBold(True)
                formula_item.setFont(formula_font)
                formula_item.setForeground(QColor("#1565C0"))
                self.table_cod_rod.setItem(row, 3, formula_item)

                # Coluna 4: Grupo Espacial (centralizado)
                spacegroup_item = QTableWidgetItem(compound_data.get("spacegroup_display", "N/A"))
                spacegroup_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.table_cod_rod.setItem(row, 4, spacegroup_item)

                # Coluna 5: Parâmetros da Célula (monoespaçado para melhor leitura)
                cell_params_item = QTableWidgetItem(compound_data.get("cell_parameters_display", "N/A"))
                cell_params_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                cell_font = QFont("Courier New")
                cell_font.setPointSize(9)
                cell_params_item.setFont(cell_font)
                self.table_cod_rod.setItem(row, 5, cell_params_item)

                # Coluna 6: Volume (direita, numérico)
                volume_item = QTableWidgetItem(compound_data.get("volume_display", "N/A"))
                volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_cod_rod.setItem(row, 6, volume_item)

                # Coluna 7: Bibliografia (com estilo elegante e DOI em azul)
                bib_text = compound_data.get("bibliography_display", "N/A")
                doi_text = compound_data.get("doi_display", "")
                if doi_text:
                    bib_text += f" <span style='color: #1976D2;'>(DOI: <a href='https://doi.org/{doi_text}' style='color: #1976D2; text-decoration: none;'>{doi_text}</a>)</span>"

                bib_label = QLabel(bib_text)
                bib_label.setOpenExternalLinks(True)
                bib_label.setWordWrap(True)
                bib_label.setStyleSheet("""
                    QLabel {
                        padding: 4px 8px;
                        color: #424242;
                        font-size: 9pt;
                        line-height: 1.4;
                        background: transparent;
                    }
                    QLabel a {
                        color: #1976D2;
                        text-decoration: none;
                    }
                    QLabel a:hover {
                        text-decoration: underline;
                    }
                """)
                # Configurar para que o label se adapte à cor de seleção da linha
                bib_label.setAutoFillBackground(False)
                self.table_cod_rod.setCellWidget(row, 7, bib_label)

                # Coluna 8: Ano (centralizado, destaque)
                year_item = QTableWidgetItem(compound_data.get("year_display", "N/A"))
                year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                year_font = QFont()
                year_font.setPointSize(10)
                year_font.setBold(True)
                year_item.setFont(year_font)
                year_item.setForeground(QColor("#558B2F"))
                self.table_cod_rod.setItem(row, 8, year_item)

                self.table_cod_rod.item(row, 0).setData(Qt.ItemDataRole.UserRole, compound_data)

            self.table_cod_rod.resizeRowsToContents()

        else:  # OQMD ou MP
            for compound_data in standardized_results:
                unique_id = compound_data.get("unique_id", "")
                is_fav = favorites_manager.is_favorite(unique_id)

                values = [
                    "★" if is_fav else "",
                    compound_data.get("name_display", "N/A"),
                    compound_data.get("id_display", "N/A"),
                    compound_data.get("spacegroup_display", "N/A"),
                    compound_data.get("band_gap_display", "N/A"),
                    compound_data.get("formation_energy_display", "N/A"),
                    tr('results.stability_values.stable') if compound_data.get("is_stable") else tr('results.stability_values.unstable'),
                ]
                tree_item = QTreeWidgetItem(self.tree_oqmd_mp, values)
                tree_item.setData(0, Qt.ItemDataRole.UserRole, compound_data)

                if is_fav:
                    tree_item.setForeground(0, QColor("orange"))

                if compound_data.get("is_stable") is not None:
                    color = (
                        QColor("lightgreen")
                        if compound_data.get("is_stable")
                        else QColor("#ffcdd2")
                    )
                    tree_item.setBackground(6, QBrush(color))

                tree_item.setToolTip(6, compound_data.get("stability_tooltip_text", ""))
                sg_symbol = compound_data.get("spacegroup_display", "N/A")
                crystal_system_pt_api = compound_data.get("crystal_system_pt", "")
                tooltip_sg_parts = [f"{tr('results.tooltip.symbol')}: {sg_symbol}"]
                info_grupo_custom = obter_info_grupo_espacial(sg_symbol)
                if info_grupo_custom:
                    cs_custom = info_grupo_custom.get("sistema_cristalino")
                    if cs_custom and (not crystal_system_pt_api or crystal_system_pt_api == SISTEMAS_CRISTALINOS_PT.get(
                            "unknown")):
                        crystal_system_pt_api = cs_custom
                    desc_add = info_grupo_custom.get("descricao_adicional")
                    if desc_add:
                        tooltip_sg_parts.append(f"{tr('results.tooltip.detail')}: {desc_add}")
                    elif info_grupo_custom.get("ponto_grupo"):
                        tooltip_sg_parts.append(f"{tr('results.tooltip.point_group')}: {info_grupo_custom['ponto_grupo']}")
                if crystal_system_pt_api and crystal_system_pt_api != SISTEMAS_CRISTALINOS_PT.get("unknown"):
                    tooltip_sg_parts.append(f"{tr('results.tooltip.system')}: {crystal_system_pt_api}")
                tree_item.setToolTip(3, "\n".join(tooltip_sg_parts))

        self.statusBar().showMessage(
            tr('search.results_found', count=len(standardized_results)) + f" {tr('search.in_db', db=db_choice)}", 5000
        )
        logging.info(
            f"{len(standardized_results)} resultados padronizados e exibidos para {db_choice}."
        )

    def clear_results_display(self):
        self.tree_oqmd_mp.clear()
        self.table_cod_rod.setRowCount(0)
        logging.debug("Resultados (Tree e Table) limpos.")

    def show_results_popup_menu(self, position: QPoint):
        active_display_widget = None
        item_or_row_index = None
        is_table = False
        if self.tree_oqmd_mp.isVisible():
            active_display_widget = self.tree_oqmd_mp
            item_or_row_index = active_display_widget.itemAt(position)
        elif self.table_cod_rod.isVisible():
            active_display_widget = self.table_cod_rod
            item_or_row_index = active_display_widget.indexAt(position)
            is_table = True
        if not item_or_row_index:
            return
        if is_table and not item_or_row_index.isValid():
            return

        compound_data = None
        if is_table:
            fav_item_widget = active_display_widget.item(item_or_row_index.row(), 0)
            if fav_item_widget:
                compound_data = fav_item_widget.data(Qt.ItemDataRole.UserRole)
        else:
            active_display_widget.setCurrentItem(item_or_row_index)
            compound_data = item_or_row_index.data(0, Qt.ItemDataRole.UserRole)

        if not compound_data or not isinstance(compound_data, dict):
            logging.warning(
                ptr("Dados não encontrados ou em formato incorreto para o item no menu de contexto.")
            )
            return

        source_db = compound_data.get("source_db")
        id_original = compound_data.get("id_display", "N/A")
        name_display = compound_data.get("name_display", compound_data.get("formula_display", "N/A"))
        unique_id = compound_data.get("unique_id", "")
        menu = QMenu(self)

        if source_db == "ROD" and id_original != "N/A":
            action_abrir_rod_site = menu.addAction(
                tr('context_menu.open_on_site', name=name_display, id=id_original, db="ROD")
            )
            action_abrir_rod_site.triggered.connect(
                lambda checked=False, id_val=id_original: self.open_material_page(id_val, "ROD")
            )
        elif source_db != "ROD" and id_original != "N/A":
            action_text = tr('context_menu.open_on_site', name=name_display, id=id_original, db=source_db)
            action_abrir_db = menu.addAction(action_text)
            action_abrir_db.triggered.connect(
                lambda checked=False, id_val=id_original, src=source_db: self.open_material_page(
                    id_val, src
                )
            )

        can_export_cif = source_db in ["Materials Project", "COD"]
        # PhaseDRX aberto: no mesmo processo (referência direta) OU em processo
        # separado (PhaseDRX.exe), detectado pelo bridge IPC.
        phasedrx_is_open = bool(self.phasedrx_window_ref and self.phasedrx_window_ref.isVisible())
        if not phasedrx_is_open:
            try:
                from matfinder.core.phasedrx_bridge import is_phasedrx_running
                phasedrx_is_open = is_phasedrx_running()
            except Exception:
                pass

        if can_export_cif:
            action_export_phasedrx = menu.addAction(tr('context_menu.export_cif_phasedrx'))
            if not phasedrx_is_open:
                action_export_phasedrx.setEnabled(False)
                action_export_phasedrx.setToolTip(tr('context_menu.open_phasedrx_first'))
            else:
                action_export_phasedrx.triggered.connect(
                    lambda: self.handle_export_cif_to_phasedrx(compound_data)
                )

        if source_db == "Materials Project":
            menu_cif_mp = menu.addMenu(tr('context_menu.download_cif_mp'))
            for _mode, _key in (
                ("symmetrized", 'context_menu.cif_symmetrized'),
                ("conventional", 'context_menu.cif_conventional'),
                ("primitive", 'context_menu.cif_primitive'),
            ):
                _act_cif = menu_cif_mp.addAction(tr(_key))
                _act_cif.triggered.connect(
                    lambda checked=False, name=name_display, id_val=id_original, mode=_mode:
                    self.trigger_baixar_cif_mp(name, id_val, mode)
                )
            icsd_numeric_codes = compound_data.get("icsd_codes_list", [])
            if icsd_numeric_codes:
                menu_icsd_principal = menu.addMenu(tr('context_menu.icsd_via_mp'))
                for code_num_str in icsd_numeric_codes:
                    submenu_code_specific = menu_icsd_principal.addMenu(
                        f"ICSD-{code_num_str}"
                    )
                    action_abrir_ccdc = submenu_code_specific.addAction(tr('context_menu.open_ccdc'))
                    url_ccdc = f"https://www.ccdc.cam.ac.uk/structures/Search?Ccdcid={code_num_str}&DatabaseToSearch=ICSD"
                    action_abrir_ccdc.triggered.connect(
                        lambda checked=False, url=url_ccdc: QDesktopServices.openUrl(QUrl(url))
                    )
                    action_abrir_fiz = submenu_code_specific.addAction(tr('context_menu.open_fiz'))
                    url_fiz = f"https://icsd.fiz-karlsruhe.de/linkicsd.xhtml?coll_code={code_num_str}"
                    action_abrir_fiz.triggered.connect(
                        lambda checked=False, url=url_fiz: QDesktopServices.openUrl(QUrl(url))
                    )
                    action_refs = submenu_code_specific.addAction(tr('context_menu.references'))
                    action_refs.setEnabled(False)
                    action_copiar_codigo = submenu_code_specific.addAction(tr('context_menu.copy_code'))
                    code_to_copy = f"ICSD-{code_num_str}"
                    action_copiar_codigo.triggered.connect(
                        lambda checked=False, code=code_to_copy: self.copy_to_clipboard(code)
                    )
        # --- ALTERAÇÃO: Adiciona o menu ICSD para OQMD ---
        elif source_db == "OQMD":
            icsd_numeric_codes = compound_data.get("icsd_codes_list", [])
            if icsd_numeric_codes:
                menu_icsd_principal = menu.addMenu(tr('context_menu.icsd_via_oqmd'))
                for code_num_str in icsd_numeric_codes:
                    submenu_code_specific = menu_icsd_principal.addMenu(
                        f"ICSD-{code_num_str}"
                    )
                    action_abrir_ccdc = submenu_code_specific.addAction(tr('context_menu.open_ccdc'))
                    url_ccdc = f"https://www.ccdc.cam.ac.uk/structures/Search?Ccdcid={code_num_str}&DatabaseToSearch=ICSD"
                    action_abrir_ccdc.triggered.connect(
                        lambda checked=False, url=url_ccdc: QDesktopServices.openUrl(QUrl(url))
                    )
                    action_abrir_fiz = submenu_code_specific.addAction(tr('context_menu.open_fiz'))
                    url_fiz = f"https://icsd.fiz-karlsruhe.de/linkicsd.xhtml?coll_code={code_num_str}"
                    action_abrir_fiz.triggered.connect(
                        lambda checked=False, url=url_fiz: QDesktopServices.openUrl(QUrl(url))
                    )
                    action_refs = submenu_code_specific.addAction(tr('context_menu.references'))
                    action_refs.setEnabled(False)
                    action_copiar_codigo = submenu_code_specific.addAction(tr('context_menu.copy_code'))
                    code_to_copy = f"ICSD-{code_num_str}"
                    action_copiar_codigo.triggered.connect(
                        lambda checked=False, code=code_to_copy: self.copy_to_clipboard(code)
                    )
        elif source_db == "COD" and id_original != "N/A":
            formula_cod = compound_data.get("formula_display", id_original)
            action_baixar_cif_cod = menu.addAction(
                tr('context_menu.download_cif_cod', id=id_original)
            )
            action_baixar_cif_cod.triggered.connect(
                lambda checked=False, cod_id=id_original, fname=formula_cod: self.trigger_baixar_cif_cod(
                    cod_id, fname
                )
            )
        elif source_db == "ROD" and id_original != "N/A":
            formula_rod = compound_data.get("formula_display", id_original)
            action_baixar_rod_file = menu.addAction(
                tr('context_menu.download_rod', id=id_original)
            )
            action_baixar_rod_file.triggered.connect(
                lambda checked=False, rod_id=id_original, fname=formula_rod: self.trigger_baixar_rod_file(
                    rod_id, fname
                )
            )

        if unique_id:
            menu.addSeparator()
            is_fav = favorites_manager.is_favorite(unique_id)
            fav_text = tr('context_menu.remove_favorite') if is_fav else tr('context_menu.add_favorite')
            action_favoritar = menu.addAction(fav_text)
            action_favoritar.triggered.connect(
                lambda: self.toggle_favorite_status(unique_id)
            )

        menu.exec(active_display_widget.mapToGlobal(position))

    @Slot(str)
    def toggle_favorite_status(self, unique_id: str):
        # (O conteúdo desta função permanece o mesmo)
        if favorites_manager.is_favorite(unique_id):
            favorites_manager.remove_favorite(unique_id)
        else:
            favorites_manager.add_favorite(unique_id)

        db_choice = self._current_selected_database
        if db_choice in self.search_cache:
            self.populate_results_display(self.search_cache[db_choice], db_choice)

    def handle_export_cif_to_phasedrx(self, compound_data: dict):
        # (O conteúdo desta função permanece o mesmo)
        source_db = compound_data.get("source_db")
        id_original = compound_data.get("id_display", "N/A")
        name_display = compound_data.get("name_display", "N/A")

        in_process = bool(self.phasedrx_window_ref and self.phasedrx_window_ref.isVisible())
        bridge_open = False
        if not in_process:
            try:
                from matfinder.core.phasedrx_bridge import is_phasedrx_running
                bridge_open = is_phasedrx_running()
            except Exception:
                bridge_open = False
        if not in_process and not bridge_open:
            QMessageBox.warning(self, tr('cif.phasedrx_closed_title'), tr('cif.phasedrx_closed_msg'))
            return

        logging.info(
            f"Iniciando exportação de CIF para PhaseDRX. Material: {name_display} ({id_original}) de {source_db}")
        self.statusBar().showMessage(tr('cif.exporting', name=name_display), 5000)

        self.cif_export_target = 'phasedrx'
        if source_db == "Materials Project":
            # Exportar para PhaseDRX usa SEMPRE o CIF simetrizado (explícito).
            self.trigger_baixar_cif_mp(name_display, id_original, mode="symmetrized")
        elif source_db == "COD":
            self.trigger_baixar_cif_cod(id_original, name_display)

    def _send_cif_via_bridge(self, cif_string: str, suggested_filename: str) -> bool:
        """Envia o CIF a um PhaseDRX aberto em OUTRO processo (PhaseDRX.exe) via o
        bridge IPC. Retorna True se entregue."""
        try:
            from matfinder.core.phasedrx_bridge import is_phasedrx_running, send_cif_to_phasedrx
            if is_phasedrx_running() and send_cif_to_phasedrx(cif_string, suggested_filename):
                self.statusBar().showMessage(tr('cif.sent_to_phasedrx', filename=suggested_filename), 4000)
                return True
        except Exception:
            logging.exception("Falha ao enviar CIF ao PhaseDRX via bridge.")
        return False

    def trigger_baixar_cif_mp(self, formula_pretty: str, material_id: str, mode: str = "symmetrized"):
        if self.get_api_key_on_demand() is None:
            QMessageBox.warning(
                self,
                tr('dialogs.api_key.required_title'),
                tr('dialogs.api_key.required_cif_msg'),
            )
            self.cif_export_target = None
            return
        if self.cif_fetch_thread and self.cif_fetch_thread.is_alive():
            QMessageBox.information(
                self, tr('status.in_progress'), tr('cif.mp_in_progress')
            )
            return
        logging.info(
            f"Iniciando download de CIF (MP) para {formula_pretty} (ID: {material_id})."
        )
        self.statusBar().showMessage(
            tr('cif.fetching_mp', formula=formula_pretty, id=material_id), 5000
        )
        cif_worker = Worker(
            self._fetch_cif_data_logic_mp,
            "fetch_cif_mp",
            material_id,
            formula_pretty,
            mode,
        )
        cif_worker.cif_data_ready.connect(self.handle_cif_data_ready_mp)
        cif_worker.task_error.connect(self.handle_cif_fetch_error)
        self.cif_fetch_thread = threading.Thread(target=cif_worker.run)
        self.cif_fetch_thread.daemon = True
        self.cif_fetch_thread.start()

    def _fetch_cif_data_logic_mp(self, material_id: str, formula_pretty: str, mode: str = "symmetrized"):
        # mode: "symmetrized" (célula convencional + grupo espacial),
        #       "conventional" (célula convencional em P1) ou "primitive" (célula primitiva).
        # Carregar módulos sob demanda
        _ensure_mp_api()

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        if getattr(sys, 'frozen', False):
            if sys.stdout is None:
                sys.stdout = io.StringIO()
            if sys.stderr is None:
                sys.stderr = io.StringIO()

        proxies = self._get_proxies_dict()
        old_proxies_env = {}
        if proxies:
            if "http" in proxies:
                old_proxies_env["HTTP_PROXY"] = os.environ.get("HTTP_PROXY")
                os.environ["HTTP_PROXY"] = proxies["http"]
            if "https" in proxies:
                old_proxies_env["HTTPS_PROXY"] = os.environ.get("HTTPS_PROXY")
                os.environ["HTTPS_PROXY"] = proxies["https"]
        try:
            use_conventional = (mode != "primitive")
            with MPRester(api_key=self.api_key_mp) as mpr:
                structure = mpr.get_structure_by_material_id(
                    material_id, conventional_unit_cell=use_conventional
                )
                if structure:
                    try:
                        from pymatgen.io.cif import CifWriter
                        if mode == "symmetrized":
                            # Detecta simetria e escreve com grupo espacial.
                            writer = CifWriter(structure, symprec=0.1, significant_figures=8)
                        else:
                            # Convencional ou primitiva, sem reduzir por simetria (P1).
                            writer = CifWriter(structure, significant_figures=8)
                        cif_string = str(writer)
                    except Exception as cif_err:
                        logging.warning(f"CifWriter falhou: {cif_err}. Usando fallback P1.")
                        cif_string = structure.to(fmt="cif")
                    safe_formula = "".join(
                        c if c.isalnum() else "_" for c in formula_pretty
                    )
                    _suffix = {"symmetrized": "sym", "conventional": "conv", "primitive": "prim"}.get(mode, "")
                    suggested_filename = (
                        f"MP_{material_id}_{safe_formula}_{_suffix}.cif" if _suffix
                        else f"MP_{material_id}_{safe_formula}.cif"
                    )
                    return cif_string, suggested_filename
                else:
                    raise Exception(
                        ptr("Estrutura não encontrada para material_id (MP): {}").format(material_id)
                    )
        except Exception as e:
            logging.exception(f"Erro ao buscar CIF do MP para ID {material_id}:")
            raise
        finally:
            if getattr(sys, 'frozen', False):
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            if "HTTP_PROXY" in old_proxies_env:
                if old_proxies_env["HTTP_PROXY"] is None:
                    os.environ.pop("HTTP_PROXY", None)
                else:
                    os.environ["HTTP_PROXY"] = old_proxies_env["HTTP_PROXY"]
            elif proxies and "http" in proxies:
                os.environ.pop("HTTP_PROXY", None)

            if "HTTPS_PROXY" in old_proxies_env:
                if old_proxies_env["HTTPS_PROXY"] is None:
                    os.environ.pop("HTTPS_PROXY", None)
                else:
                    os.environ["HTTPS_PROXY"] = old_proxies_env["HTTPS_PROXY"]
            elif proxies and "https" in proxies:
                os.environ.pop("HTTPS_PROXY", None)

    @Slot(str, str)
    def handle_cif_data_ready_mp(self, cif_string: str, suggested_filename: str):
        # (O conteúdo desta função permanece o mesmo)
        self.statusBar().clearMessage()

        if self.cif_export_target == 'phasedrx':
            if self.phasedrx_window_ref and self.phasedrx_window_ref.isVisible():
                self.phasedrx_window_ref.load_cif_from_data(cif_string, suggested_filename)
                self.statusBar().showMessage(tr('cif.sent_to_phasedrx', filename=suggested_filename), 4000)
            elif self._send_cif_via_bridge(cif_string, suggested_filename):
                pass
            else:
                QMessageBox.warning(self, tr('cif.window_closed_title'), tr('cif.window_closed_saving'))
                self._save_cif_file_dialog(cif_string, suggested_filename, "MP")
            self.cif_export_target = None
        else:
            self._save_cif_file_dialog(cif_string, suggested_filename, "MP")

        logging.info(f"CIF (MP) pronto para salvar: {suggested_filename}")

    def trigger_baixar_cif_cod(self, cod_id: str, formula_for_filename: str):
        # (O conteúdo desta função permanece o mesmo)
        if self.cod_cif_fetch_thread and self.cod_cif_fetch_thread.is_alive():
            QMessageBox.information(
                self, tr('status.in_progress'), tr('cif.cod_in_progress')
            )
            return
        logging.info(f"Iniciando download de CIF (COD) para ID: {cod_id}.")
        self.statusBar().showMessage(tr('cif.fetching_cod', id=cod_id), 5000)
        cod_cif_worker = Worker(
            COD_api_logic.get_cod_cif_data,
            "fetch_cif_cod",
            cod_id,
            formula_for_filename,
        )
        cod_cif_worker.cod_cif_data_ready.connect(
            self.handle_cod_cif_data_ready
        )
        cod_cif_worker.task_error.connect(self.handle_cif_fetch_error)
        self.cod_cif_fetch_thread = threading.Thread(
            target=cod_cif_worker.run
        )
        self.cod_cif_fetch_thread.daemon = True
        self.cod_cif_fetch_thread.start()

    @Slot(str, str, str)
    def handle_cod_cif_data_ready(
            self, cif_string: str, suggested_filename: str, cod_id: str
    ):
        # (O conteúdo desta função permanece o mesmo)
        self.statusBar().clearMessage()

        if self.cif_export_target == 'phasedrx':
            if self.phasedrx_window_ref and self.phasedrx_window_ref.isVisible():
                self.phasedrx_window_ref.load_cif_from_data(cif_string, suggested_filename)
                self.statusBar().showMessage(tr('cif.sent_to_phasedrx', filename=suggested_filename), 4000)
            elif self._send_cif_via_bridge(cif_string, suggested_filename):
                pass
            else:
                QMessageBox.warning(self, tr('cif.window_closed_title'), tr('cif.window_closed_saving'))
                self._save_cif_file_dialog(cif_string, suggested_filename, f"COD ({cod_id})")
            self.cif_export_target = None
        else:
            self._save_cif_file_dialog(cif_string, suggested_filename, f"COD ({cod_id})")

        logging.info(f"CIF (COD {cod_id}) pronto para salvar: {suggested_filename}")

    def trigger_baixar_rod_file(self, rod_id: str, formula_for_filename: str):
        # (O conteúdo desta função permanece o mesmo)
        if self.rod_file_fetch_thread and self.rod_file_fetch_thread.is_alive():
            QMessageBox.information(
                self, tr('status.in_progress'), tr('cif.rod_in_progress')
            )
            return
        logging.info(f"Iniciando download de arquivo .rod (ROD) para ID: {rod_id}.")
        self.statusBar().showMessage(tr('cif.fetching_rod', id=rod_id), 5000)

        rod_file_worker = Worker(
            self._fetch_rod_file_content_logic,
            "fetch_rod_file",
            rod_id,
            formula_for_filename,
        )
        rod_file_worker.rod_file_data_ready.connect(self.handle_rod_file_data_ready)
        rod_file_worker.task_error.connect(self.handle_rod_file_fetch_error)

        self.rod_file_fetch_thread = threading.Thread(target=rod_file_worker.run)
        self.rod_file_fetch_thread.daemon = True
        self.rod_file_fetch_thread.start()

    @Slot(str, str, str)
    def handle_rod_file_data_ready(self, rod_file_content: str, rod_id: str, formula_for_filename: str):
        # (O conteúdo desta função permanece o mesmo)
        self.statusBar().clearMessage()

        safe_formula = "".join(c if c.isalnum() else "_" for c in formula_for_filename)
        suggested_filename = f"ROD_{rod_id}_{safe_formula}.txt"

        downloads_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        if not downloads_path:
            downloads_path = os.path.expanduser("~")

        filePath, _ = QFileDialog.getSaveFileName(
            self,
            f"Salvar Arquivo .rod como .txt (ROD ID: {rod_id})",
            os.path.join(downloads_path, suggested_filename),
            ptr("Text Files (*.txt);;All Files (*)"),
        )

        if filePath:
            try:
                with open(filePath, "w", encoding="utf-8") as f:
                    f.write(rod_file_content)
                self.statusBar().showMessage(ptr("Arquivo .rod (ROD {}) salvo como .txt em: {}").format(rod_id, filePath), 7000)
                QMessageBox.information(
                    self,
                    ptr("Arquivo .rod Salvo como .txt (ROD {})").format(rod_id),
                    ptr("Arquivo .rod salvo com sucesso como .txt em:\n{}").format(filePath),
                )
                logging.info(f"Arquivo .rod (ROD {rod_id}) salvo como .txt em: {filePath}")
            except IOError as ioe:
                QMessageBox.critical(self, ptr("Erro ao Salvar Arquivo"),
                                     ptr("Não foi possível salvar o arquivo (erro de E/S):\n{}").format(ioe))
                logging.exception(f"Erro de E/S ao salvar arquivo .rod (ROD {rod_id}) em {filePath}:")
            except Exception as e:
                QMessageBox.critical(self, ptr("Erro ao Salvar Arquivo"), ptr("Não foi possível salvar o arquivo:\n{}").format(e))
                logging.exception(f"Erro inesperado ao salvar arquivo .rod (ROD {rod_id}) em {filePath}:")
        else:
            QMessageBox.information(self, ptr("Download Cancelado"), ptr("O download do arquivo .rod foi cancelado."))
            logging.info(f"Download do arquivo .rod (ROD {rod_id}) cancelado pelo usuário.")

    @Slot(str, str)
    def handle_rod_file_fetch_error(self, error_title: str, error_message: str):
        # (O conteúdo desta função permanece o mesmo)
        self.statusBar().clearMessage()
        QMessageBox.critical(self, error_title, error_message)

    def _save_cif_file_dialog(
            self, cif_string: str, suggested_filename: str, source_info: str
    ):
        # (O conteúdo desta função permanece o mesmo)
        downloads_path = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        if not downloads_path:
            downloads_path = os.path.expanduser("~")
        filePath, _ = QFileDialog.getSaveFileName(
            self,
            f"Salvar Arquivo CIF ({source_info})",
            os.path.join(downloads_path, suggested_filename),
            ptr("CIF Files (*.cif);;All Files (*)"),
        )
        if filePath:
            try:
                with open(filePath, "w", encoding="utf-8") as f:
                    f.write(cif_string)
                self.statusBar().showMessage(
                    ptr("Arquivo CIF ({}) salvo em: {}").format(source_info, filePath), 7000
                )
                QMessageBox.information(
                    self,
                    ptr("CIF Salvo ({})").format(source_info),
                    ptr("Arquivo CIF salvo com sucesso em:\n{}").format(filePath),
                )
                logging.info(f"Arquivo CIF ({source_info}) salvo em: {filePath}")
                if not QDesktopServices.openUrl(QUrl.fromLocalFile(filePath)):
                    QMessageBox.warning(
                        self,
                        ptr("Abrir Arquivo"),
                        ptr("Não foi possível abrir o arquivo CIF automaticamente.\nO sistema pode não ter um programa associado para arquivos .cif.\nVocê pode encontrá-lo em: {}").format(filePath),
                    )
                    logging.warning(
                        f"Não foi possível abrir automaticamente o arquivo CIF: {filePath}"
                    )
            except IOError as ioe:
                QMessageBox.critical(
                    self,
                    ptr("Erro ao Salvar CIF ({})").format(source_info),
                    ptr("Não foi possível salvar o arquivo CIF (erro de E/S):\n{}").format(ioe),
                )
                logging.exception(
                    f"Erro de E/S ao salvar CIF ({source_info}) em {filePath}:"
                )
                self.statusBar().showMessage(
                    ptr("Erro ao salvar CIF ({}).").format(source_info), 5000
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    ptr("Erro ao Salvar CIF ({})").format(source_info),
                    ptr("Não foi possível salvar o arquivo CIF:\n{}").format(e),
                )
                logging.exception(
                    f"Erro inesperado ao salvar CIF ({source_info}) em {filePath}:"
                )
                self.statusBar().showMessage(
                    ptr("Erro ao salvar CIF ({}).").format(source_info), 5000
                )
        else:
            QMessageBox.information(
                self,
                ptr("Download Cancelado"),
                ptr("O download do arquivo CIF ({}) foi cancelado.").format(source_info),
            )
            self.statusBar().showMessage(
                ptr("Download do CIF ({}) cancelado.").format(source_info), 3000
            )
            logging.info(f"Download do CIF ({source_info}) cancelado pelo usuário.")

    @Slot(str, str)
    def handle_cif_fetch_error(self, error_title: str, error_message: str):
        # (O conteúdo desta função permanece o mesmo)
        self.statusBar().clearMessage()
        if self.cif_export_target:
            self.cif_export_target = None
        QMessageBox.critical(self, error_title, error_message)

    def handle_results_double_click(
            self, item_or_row, column=None
    ):
        # (O conteúdo desta função permanece o mesmo)
        source_db = self._current_selected_database
        id_original = ""
        compound_data = None

        if isinstance(item_or_row, QTableWidgetItem):
            fav_item_widget = self.table_cod_rod.item(item_or_row.row(), 0)
            if fav_item_widget:
                compound_data = fav_item_widget.data(Qt.ItemDataRole.UserRole)
                if compound_data:
                    id_original = compound_data.get("id_display", "")

            if item_or_row.column() == 2 and id_original and id_original != "N/A":
                if source_db == "COD":
                    formula = (compound_data.get("formula_display", id_original) if compound_data else id_original)
                    self.trigger_baixar_cif_cod(id_original, formula)
                    return
                elif source_db == "ROD":
                    formula_rod = (compound_data.get("formula_display", id_original) if compound_data else id_original)
                    self.trigger_baixar_rod_file(id_original, formula_rod)
                    return

        elif isinstance(item_or_row, QTreeWidgetItem):
            compound_data = item_or_row.data(0, Qt.ItemDataRole.UserRole)
            if compound_data:
                id_original = compound_data.get("id_display", "")

        if id_original and id_original != "N/A":
            self.open_material_page(id_original, source_db)
        elif compound_data:
            logging.warning(
                f"Tentando abrir página para {compound_data.get('name_display', 'item desconhecido')} "
                f"de {source_db} sem ID claro para URL."
            )
        else:
            logging.warning(
                ptr("Não foi possível abrir a página para o material (ID não encontrado ou dados insuficientes).")
            )

    def open_material_page(self, material_id: str, source_db: str):
        # (O conteúdo desta função permanece o mesmo)
        url_map = {
            "OQMD": f"https://oqmd.org/materials/entry/{material_id}",
            "Materials Project": f"https://next-gen.materialsproject.org/materials/{material_id}",
            "COD": f"https://www.crystallography.net/cod/{material_id}.html",
            "ROD": f"{ROD_ENTRY_BASE_URL}{material_id}.html",
        }
        url_to_open = url_map.get(source_db)
        if url_to_open:
            logging.info(f"Abrindo página do material: {url_to_open}")
            if not QDesktopServices.openUrl(QUrl(url_to_open)):
                QMessageBox.warning(
                    self,
                    ptr("Erro ao Abrir URL"),
                    ptr("Não foi possível abrir o URL no navegador:\n{}").format(url_to_open),
                )
                logging.error(f"Falha ao abrir URL: {url_to_open}")
        else:
            QMessageBox.critical(
                self,
                ptr("Erro de URL"),
                ptr("Fonte de base de dados '{}' desconhecida ou ID '{}' inválido.").format(source_db, material_id),
            )
            logging.error(
                f"Fonte de DB '{source_db}' ou ID '{material_id}' inválido para URL."
            )

    def _fetch_rod_file_content_logic(self, rod_id: str):
        # Carregar requests sob demanda
        import requests as _requests

        if not rod_id or not rod_id.isdigit():
            logging.error(f"ROD File Fetch: ID da ROD '{rod_id}' inválido.")
            raise ValueError(ptr("ID da ROD '{}' inválido para busca de arquivo.").format(rod_id))

        url = f"{ROD_ENTRY_BASE_URL}{rod_id}.rod"
        logging.info(f"ROD File Fetch: Buscando conteúdo de {url} ...")
        proxies = self._get_proxies_dict()
        try:
            response = _requests.get(url, timeout=30, proxies=proxies)
            response.raise_for_status()
            return response.text
        except _requests.exceptions.RequestException as req_err:
            logging.error(f"ROD File Fetch: Erro ao buscar arquivo .rod para {rod_id}: {req_err}")
            raise
        except Exception as e:
            logging.exception(f"ROD File Fetch: Erro inesperado ao buscar arquivo .rod para {rod_id}:")
            raise

    def trigger_fetch_doi_from_ccdc(self, url: str):
        # (O conteúdo desta função permanece o mesmo)
        if self.doi_fetch_thread and self.doi_fetch_thread.is_alive():
            QMessageBox.information(self, tr('status.in_progress'), tr('search.doi_in_progress'))
            return

        logging.info(f"Iniciando busca de DOI na página do CCDC: {url}")
        self.statusBar().showMessage(tr('search.fetching_doi_ccdc'), 5000)

        doi_worker = Worker(self._fetch_doi_from_ccdc_logic, "fetch_doi_from_ccdc", url)
        doi_worker.doi_from_ccdc_ready.connect(self.handle_doi_from_ccdc_ready)
        doi_worker.task_error.connect(self.handle_search_error)

        self.doi_fetch_thread = threading.Thread(target=doi_worker.run)
        self.doi_fetch_thread.daemon = True
        self.doi_fetch_thread.start()

    def _fetch_doi_from_ccdc_logic(self, url: str) -> str:
        """
        Acessa a URL do CCDC, analisa o HTML e retorna o DOI se encontrado.
        """
        # Carregar módulos sob demanda
        import requests as _requests
        _ensure_beautifulsoup()

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = _requests.get(url, timeout=30, proxies=self._get_proxies_dict(), headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            pub_container = soup.find('div', class_='media-body')
            if pub_container:
                doi_link = pub_container.find('a', href=re.compile(r'doi\.org'))
                if doi_link and doi_link.text:
                    return doi_link.text.strip()

            all_doi_links = soup.find_all('a', href=re.compile(r'doi\.org'))
            for link in all_doi_links:
                if link.text and '10.' in link.text:
                    return link.text.strip()

            return ""
        except Exception as e:
            logging.error(f"Erro ao tentar buscar DOI em {url}: {e}")
            raise

    @Slot(str)
    def handle_doi_from_ccdc_ready(self, doi: str):
        # (O conteúdo desta função permanece o mesmo)
        self.statusBar().clearMessage()
        if doi:
            self.copy_to_clipboard(doi)
            QMessageBox.information(self, tr('search.doi_found_title'),
                                    tr('search.doi_found_msg', doi=doi))
        else:
            QMessageBox.warning(self, tr('search.doi_not_found_title'),
                                tr('search.doi_not_found_msg'))

    def open_cod_material_page(self, cod_id: str):
        # (O conteúdo desta função permanece o mesmo)
        if not cod_id or cod_id == "N/A":
            QMessageBox.warning(
                self, tr('dialogs.error.invalid_id'), tr('results.context_menu.no_cod_id')
            )
            return
        url = f"https://www.crystallography.net/cod/{cod_id}.html"
        logging.info(f"Abrindo página do COD: {url}")
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(
                self,
                tr('dialogs.error.open_url_cod'),
                tr('dialogs.error.open_url_cod_msg', id=cod_id, url=url),
            )
            logging.error(f"Falha ao abrir URL do COD: {url}")

    def open_icsd_entry_page(self, icsd_code_number: str):
        # (O conteúdo desta função permanece o mesmo)
        if not str(icsd_code_number).strip():
            QMessageBox.warning(
                self,
                tr('dialogs.error.invalid_icsd'),
                tr('dialogs.error.invalid_icsd_msg', code=icsd_code_number),
            )
            return
        url = f"https://www.ccdc.cam.ac.uk/structures/Search?Ccdcid={icsd_code_number}&DatabaseToSearch=ICSD"
        logging.info(f"Abrindo página do CCDC para ICSD: {url}")
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(
                self,
                tr('dialogs.error.open_url_icsd'),
                tr('dialogs.error.open_url_icsd_msg', code=icsd_code_number, url=url),
            )
            logging.error(f"Falha ao abrir URL do CCDC/ICSD: {url}")

    def copy_to_clipboard(self, value_to_copy: str):
        # (O conteúdo desta função permanece o mesmo)
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(str(value_to_copy))
        self.statusBar().showMessage(tr('status.copied', value=value_to_copy), 2000)
        logging.info(
            f"Valor '{value_to_copy[:50]}...' copiado para a área de transferência."
        )

    def open_periodic_table(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Importação Local ---
        from matfinder.tools.periodic_table.tabela_periodica_pyside import TabelaPeriodicaDialog
        if (
                self.tabela_periodica_window_ref is None
                or not self.tabela_periodica_window_ref.isVisible()
        ):
            current_elements_str = self.entry_elementos.text().strip()
            initial_selection = {
                el.strip().capitalize()
                for el in current_elements_str.split(",")
                if el.strip().isalpha()
            }
            self.tabela_periodica_window_ref = TabelaPeriodicaDialog(
                parent=self, initial_selected_elements=initial_selection
            )
            self.tabela_periodica_window_ref.element_toggled_signal.connect(
                self.handle_pt_element_toggled
            )
            self.tabela_periodica_window_ref.selection_confirmed_signal.connect(
                self.handle_pt_selection_confirmed
            )
            self.tabela_periodica_window_ref.selection_cleared_signal.connect(
                self.handle_pt_selection_cleared
            )
            logging.info("Abrindo Tabela Periódica.")
            if (
                    self.tabela_periodica_window_ref.exec() == QDialog.DialogCode.Accepted
                    and self.entry_elementos.text().strip()
            ):
                self.start_search()
        else:
            self.tabela_periodica_window_ref.raise_()
            self.tabela_periodica_window_ref.activateWindow()

    @Slot(str, bool)
    def handle_pt_element_toggled(self, symbol: str, is_selected: bool):
        # Garantir que a tabela periódica esteja carregada
        elementos = _ensure_tabela_periodica_elementos()

        if is_selected:
            self.pt_selected_elements.add(symbol)
        elif symbol in self.pt_selected_elements:
            self.pt_selected_elements.remove(symbol)
        sorted_symbols = sorted(
            list(self.pt_selected_elements),
            key=lambda s: next(
                (
                    el["numero"]
                    for el in elementos
                    if el["simbolo"] == s
                ),
                0,
            ),
        )
        self.entry_elementos.setText(", ".join(sorted_symbols))

    @Slot(list)
    def handle_pt_selection_confirmed(self, selected_symbols: list):
        # (O conteúdo desta função permanece o mesmo)
        self.pt_selected_elements = set(selected_symbols)
        self.entry_elementos.setText(", ".join(selected_symbols))
        logging.info(
            f"Seleção da Tabela Periódica confirmada: {selected_symbols}"
        )

    @Slot()
    def handle_pt_selection_cleared(self):
        # (O conteúdo desta função permanece o mesmo)
        self.pt_selected_elements.clear()
        self.entry_elementos.setText("")
        logging.info("Seleção da Tabela Periódica limpa.")

    def open_calculadora_estequiometrica(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Importação Local ---
        from matfinder.tools.calculator.calculadora_esteq_pyside import CalculadoraEstequiometricaDialog
        if (
                self.calculadora_esteq_window_ref is None
                or not self.calculadora_esteq_window_ref.isVisible()
        ):
            try:
                self.calculadora_esteq_window_ref = CalculadoraEstequiometricaDialog(
                    self
                )
                self.calculadora_esteq_window_ref.show()
                logging.info("Calculadora Estequiométrica aberta.")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    ptr("Erro ao Abrir Calculadora"),
                    ptr("Não foi possível abrir a Calculadora Estequiométrica:\n{}\n\nVerifique se os arquivos 'calculadora_esteq_pyside.py' e 'quimica_calc.py' estão corretos.").format(e),
                )
                logging.exception("Erro ao abrir Calculadora Estequiométrica:")
        else:
            self.calculadora_esteq_window_ref.raise_()
            self.calculadora_esteq_window_ref.activateWindow()

    def open_calculadora_proporcao_massa(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Importação Local ---
        from matfinder.ui_dialogs import CalculadoraProporcaoMassaDialog
        if (
                self.calc_prop_massa_dialog_ref is None
                or not self.calc_prop_massa_dialog_ref.isVisible()
        ):
            try:
                self.calc_prop_massa_dialog_ref = CalculadoraProporcaoMassaDialog(
                    self
                )
                self.calc_prop_massa_dialog_ref.show()
                logging.info("Calculadora de Proporção de Massa aberta.")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    ptr("Erro ao Abrir Calculadora"),
                    ptr("Não foi possível abrir a Calculadora de Proporção de Massa:\n{}").format(e),
                )
                logging.exception("Erro ao abrir Calculadora de Proporção de Massa:")
        else:
            self.calc_prop_massa_dialog_ref.raise_()
            self.calc_prop_massa_dialog_ref.activateWindow()

    def open_phasedrx_tool(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Importações Locais ---
        from matfinder.tools.xrd.xrd import PhaseDRXTool
        from matfinder.ui_dialogs import PhaseDRXProjectDialog

        if self.phasedrx_window_ref and self.phasedrx_window_ref.isVisible():
            self.phasedrx_window_ref.raise_()
            self.phasedrx_window_ref.activateWindow()
            return

        dialog = PhaseDRXProjectDialog(self)
        if not dialog.exec():
            return

        choice = dialog.choice
        project_path_to_open = None

        if choice == dialog.NEW_PROJECT:
            project_name = dialog.project_name
            base_path = dialog.project_base_path
            project_dir = os.path.join(base_path, project_name)
            cif_dir = os.path.join(project_dir, "Cif")
            dados_dir = os.path.join(project_dir, "Dados")
            project_file = os.path.join(project_dir, f"{project_name}.mfpx")

            if os.path.exists(project_dir):
                reply = QMessageBox.question(self, tr('project.folder_exists_title'),
                                             tr('project.folder_exists_msg', folder=project_dir),
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.No:
                    return
                if not os.path.exists(project_file):
                     QMessageBox.warning(self, tr('project.file_not_found_title'),
                                         tr('project.file_not_found_msg', file=project_file))
                     return
                project_path_to_open = project_file
            else:
                try:
                    os.makedirs(cif_dir)
                    os.makedirs(dados_dir)
                    with open(project_file, 'w', encoding='utf-8') as f:
                        json.dump({}, f)
                    project_path_to_open = project_file
                    logging.info(f"Nova estrutura de projeto criada em: {project_dir}")
                except OSError as e:
                    QMessageBox.critical(self, tr('project.create_error_title'),
                                         tr('project.create_error_msg', error=str(e)))
                    return

        elif choice == dialog.OPEN_PROJECT:
            path, _ = QFileDialog.getOpenFileName(self, ptr("Abrir Projeto PhaseDRX"), "",
                                                  ptr("Projetos MatFinder (*.mfpx);;Todos os Arquivos (*)"))
            if not path:
                return
            project_path_to_open = path

        elif choice == dialog.ANONYMOUS_SESSION:
            project_path_to_open = None

        try:
            # --- INÍCIO DA CORREÇÃO ---
            # Passamos None como pai para que a janela não seja modal
            self.phasedrx_window_ref = PhaseDRXTool(parent=None, project_path=project_path_to_open)
            # --- FIM DA CORREÇÃO ---
            self.phasedrx_window_ref.show()
            logging.info(f"Ferramenta PhaseDRX aberta. Projeto: {project_path_to_open or 'Sessão Anônima'}")
        except Exception as e:
            QMessageBox.critical(
                self,
                ptr("Erro ao Abrir PhaseDRX"),
                ptr("Não foi possível abrir a ferramenta de análise de DRX:\n{}\n\nVerifique se o arquivo 'xrd.py' e suas dependências (matplotlib, pymatgen) estão corretos.").format(e),
            )
            logging.exception("Erro ao abrir PhaseDRX:")

    def _add_search_to_history(self, termos_busca: str, base_dados: str):
        # --- ALTERAÇÃO DE REATORAÇÃO: Importação Local ---
        # (HISTORICO_FILE já é importado do local correto no topo do ficheiro)
        filepath = os.path.join(os.getcwd(), HISTORICO_FILE)  # dir gravável (não _MEIPASS, read-only)
        historico_existente = []
        try:
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                with open(filepath, "r", encoding="utf-8") as f:
                    historico_existente = json.load(f)
                if not isinstance(historico_existente, list):
                    historico_existente = []
        except (json.JSONDecodeError, IOError) as e:
            logging.error(
                f"Erro ao carregar histórico ('{filepath}') para adicionar nova entrada: {e}"
            )
            historico_existente = []

        termos_str_normalizados = ", ".join(
            sorted(
                list(
                    set(
                        el.strip().capitalize()
                        for el in termos_busca.split(",")
                        if el.strip()
                    )
                )
            )
        )

        nova_entrada = {
            "termos_busca": termos_str_normalizados,
            "nome_display": termos_str_normalizados,
            "base_dados": base_dados,
            "data_consulta": datetime.now().strftime(DATETIME_FORMAT),
            "favorito": False,
        }
        if historico_existente:
            ultima_entrada = historico_existente[-1]
            if (
                    ultima_entrada["termos_busca"] == nova_entrada["termos_busca"]
                    and ultima_entrada["base_dados"] == nova_entrada["base_dados"]
            ):
                logging.info(
                    "Nova busca é idêntica à última entrada do histórico. Não adicionando."
                )
                return
        historico_existente.append(nova_entrada)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(historico_existente, f, indent=4, ensure_ascii=False)
            self.statusBar().showMessage(
                tr('history.added_to_history', query=termos_str_normalizados, db=base_dados),
                3000,
            )
            logging.info(
                f"Busca por '{termos_str_normalizados}' em '{base_dados}' adicionada ao histórico."
            )
        except IOError as e:
            self.statusBar().showMessage(tr('history.save_error', error=str(e)), 5000)
            logging.error(f"Erro de E/S ao salvar histórico: {e}")
        except Exception as e:
            self.statusBar().showMessage(
                tr('history.save_error', error=str(e)), 5000
            )
            logging.error(f"Erro inesperado ao salvar histórico: {e}")

    def open_search_history_dialog(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Importação Local ---
        from matfinder.core.historico_dialog_pyside import HistoricoDialog
        if (
                self.historico_dialog_ref is None
                or not self.historico_dialog_ref.isVisible()
        ):
            try:
                self.historico_dialog_ref = HistoricoDialog(self)
                self.historico_dialog_ref.refazer_busca_signal.connect(
                    self.handle_refazer_busca_do_historico
                )
                self.historico_dialog_ref.show()
                logging.info("Janela de Histórico de Busca aberta.")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    ptr("Erro ao Abrir Histórico"),
                    ptr("Não foi possível abrir a janela de Histórico de Busca:\n{}\n\nVerifique se o arquivo 'historico_dialog_pyside.py' está correto.").format(e),
                )
                logging.exception("Erro ao abrir janela de Histórico de Busca:")
        else:
            self.historico_dialog_ref.carregar_historico()
            self.historico_dialog_ref.raise_()
            self.historico_dialog_ref.activateWindow()

    def open_log_viewer(self):
        """Abre o visualizador de log do sistema."""
        from matfinder.core.log_viewer_dialog import LogViewerDialog
        try:
            log_path = self.resource_path("matfinder.log")
            dialog = LogViewerDialog(self, log_file_path=log_path)
            dialog.exec()
            logging.info("Visualizador de Log aberto.")
        except Exception as e:
            QMessageBox.critical(
                self,
                tr('log_viewer.error_title', default='Erro ao Abrir Log'),
                ptr("Não foi possível abrir o visualizador de log:\n{}").format(e)
            )
            logging.exception("Erro ao abrir visualizador de log:")

    @Slot(str, str)
    def handle_refazer_busca_do_historico(self, termos_busca: str, base_dados: str):
        # (O conteúdo desta função permanece o mesmo)
        self.entry_elementos.setText(termos_busca)
        logging.info(
            f"Refazendo busca do histórico: Termos='{termos_busca}', Base='{base_dados}'"
        )
        if base_dados in [
            self.db_combobox.itemText(i) for i in range(self.db_combobox.count())
        ]:
            if self.db_combobox.currentText() != base_dados:
                self.db_combobox.setCurrentText(base_dados)
            else:
                QTimer.singleShot(0, self.start_search)
        else:
            QMessageBox.warning(
                self,
                ptr("Base de Dados Desconhecida"),
                ptr("A base de dados '{}' do histórico não é mais uma opção válida. Usando a seleção atual.").format(base_dados),
            )
            logging.warning(
                f"Base de dados '{base_dados}' do histórico não é mais uma opção válida."
            )
            QTimer.singleShot(0, self.start_search)

    def open_readme(self):
        # --- ALTERAÇÃO DE REATORAÇÃO: Caminho do Asset ---
        readme_path = os.path.join("docs", "Manual do Usuário.pdf")
        abs_readme_path = os.path.abspath(self.resource_path(readme_path))
        logging.info(f"Tentando abrir arquivo Leiame: {abs_readme_path}")
        if QDesktopServices.openUrl(QUrl.fromLocalFile(abs_readme_path)):
            pass
        else:
            try:
                if sys.platform == "win32":
                    os.startfile(abs_readme_path)
                elif sys.platform == "darwin":
                    subprocess.call(["open", abs_readme_path])
                else:
                    subprocess.call(["xdg-open", abs_readme_path])
            except FileNotFoundError:
                QMessageBox.warning(
                    self,
                    ptr("Erro ao Abrir Instruções"),
                    ptr("Não foi possível encontrar o arquivo de instruções ('{}').").format(abs_readme_path),
                )
                logging.error(
                    f"Arquivo Leiame.txt não encontrado em: {abs_readme_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    ptr("Erro ao Abrir Instruções"),
                    ptr("Não foi possível abrir o arquivo de instruções ('{}').\nPor favor, procure o arquivo 'Leiame.txt' na pasta 'doc' da aplicação.\n\nErro: {}").format(abs_readme_path, e),
                )
                logging.error(f"Erro ao abrir Leiame.txt ({abs_readme_path}): {e}")

    def open_license(self):
        license_path = self.resource_path('LICENSE_FULL.txt')
        if not os.path.exists(license_path):
            QMessageBox.warning(
                self,
                ptr("Arquivo Não Encontrado"),
                ptr("O arquivo de licença não foi encontrado em:\n{}").format(os.path.abspath(license_path))
            )
            return
        try:
            with open(license_path, 'r', encoding='utf-8') as f:
                license_text = f.read()
        except Exception as e:
            QMessageBox.critical(
                self,
                ptr("Erro ao Ler Licença"),
                ptr("Não foi possível ler o arquivo de licença:\n{}").format(e)
            )
            logging.error(f"Erro ao ler LICENSE_FULL.txt: {e}")
            return
        from matfinder.ui_dialogs import GplLicenseDialog
        dialog = GplLicenseDialog(license_text, self)
        dialog.setModal(True)
        dialog.exec()

    def show_citation(self):
        """Diálogo 'Citar este software': propósito, onde foi desenvolvido,
        contato para feedback/colaboração e a citação do Zenodo (com DOI)."""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton
        )
        from PySide6.QtGui import QGuiApplication

        labels = {
            "pt_BR": {
                "title": "Citar este software",
                "purpose": "Aplicativo de desktop para busca, visualização e análise de "
                           "estruturas de materiais cristalinos, integrando bases de dados "
                           "cristalográficas e ferramentas de difração de raios X.",
                "developed": "Desenvolvido na",
                "dev_place": "Universidade Federal do Amazonas (UFAM) — Departamento de "
                             "Física (Física de Materiais), Brasil.",
                "contact": "Autor e contato",
                "welcome": "Feedbacks e colaborações são muito bem-vindos.",
                "howto": "Como citar (Zenodo)",
                "version": "versão 3.24",
                "all_versions": "todas as versões",
                "copy": "Copiar citação", "copied": "Copiado!", "close": "Fechar",
            },
            "en_US": {
                "title": "Cite this software",
                "purpose": "Desktop application for searching, visualizing and analyzing "
                           "crystalline material structures, integrating crystallographic "
                           "databases and X-ray diffraction tools.",
                "developed": "Developed at the",
                "dev_place": "Federal University of Amazonas (UFAM) — Department of Physics "
                             "(Materials Physics), Brazil.",
                "contact": "Author and contact",
                "welcome": "Feedback and collaborations are very welcome.",
                "howto": "How to cite (Zenodo)",
                "version": "version 3.24",
                "all_versions": "all versions",
                "copy": "Copy citation", "copied": "Copied!", "close": "Close",
            },
            "de_DE": {
                "title": "Diese Software zitieren",
                "purpose": "Desktop-Anwendung zum Suchen, Visualisieren und Analysieren "
                           "kristalliner Materialstrukturen; integriert kristallographische "
                           "Datenbanken und Röntgenbeugungs-Werkzeuge.",
                "developed": "Entwickelt an der",
                "dev_place": "Bundesuniversität von Amazonas (UFAM) — Institut für Physik "
                             "(Materialphysik), Brasilien.",
                "contact": "Autor und Kontakt",
                "welcome": "Feedback und Kooperationen sind herzlich willkommen.",
                "howto": "Zitierweise (Zenodo)",
                "version": "Version 3.24",
                "all_versions": "alle Versionen",
                "copy": "Zitat kopieren", "copied": "Kopiert!", "close": "Schließen",
            },
        }
        try:
            lang = get_current_language()
        except Exception:
            lang = "en_US"
        S = labels.get(lang, labels["en_US"])

        apa = ("Valentim, R. (2026). MatFinder - X-ray diffraction analysis tools "
               "(3.24). Zenodo. https://doi.org/10.5281/zenodo.20778196")
        apa_html = (
            "Valentim, R. (2026). <i>MatFinder - X-ray diffraction analysis tools</i> "
            "(3.24). Zenodo. "
            "<a href='https://doi.org/10.5281/zenodo.20778196'>"
            "https://doi.org/10.5281/zenodo.20778196</a>"
        )

        html = f"""
        <div style="font-family:'Segoe UI',sans-serif;">
          <h2 style="margin:0;">MatFinder
            <span style="color:#888;font-size:13px;">v3.24</span></h2>
          <p style="color:#555;margin:2px 0 10px 0;"><b>X-ray diffraction analysis tools</b></p>
          <p>{S['purpose']}</p>
          <p><b>{S['developed']}</b> {S['dev_place']}</p>
          <p><b>{S['contact']}:</b> Raynner Valentim<br>
             &#9993; <a href="mailto:raynnervalentim@hotmail.com">raynnervalentim@hotmail.com</a><br>
             ORCID: <a href="https://orcid.org/0009-0004-3470-6893">0009-0004-3470-6893</a><br>
             GitHub: <a href="https://github.com/SrValentim/MatFinder">github.com/SrValentim/MatFinder</a></p>
          <p style="color:#1a7f37;"><i>{S['welcome']}</i></p>
          <hr>
          <p style="margin-bottom:4px;"><b>{S['howto']}:</b></p>
          <p style="background:#f4f4f4;padding:8px;border-radius:4px;">{apa_html}</p>
          <p style="font-size:12px;color:#555;">DOI:
             <a href="https://doi.org/10.5281/zenodo.20778196">10.5281/zenodo.20778196</a> ({S['version']})
             &middot;
             <a href="https://doi.org/10.5281/zenodo.20778195">10.5281/zenodo.20778195</a> ({S['all_versions']})</p>
        </div>
        """

        dialog = QDialog(self)
        dialog.setWindowTitle(S["title"])
        dialog.resize(600, 540)
        v = QVBoxLayout(dialog)
        browser = QTextBrowser(dialog)
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        v.addWidget(browser)

        btns = QHBoxLayout()
        copy_btn = QPushButton(S["copy"], dialog)

        def _copy():
            QGuiApplication.clipboard().setText(apa)
            copy_btn.setText(S["copied"])

        copy_btn.clicked.connect(_copy)
        close_btn = QPushButton(S["close"], dialog)
        close_btn.clicked.connect(dialog.accept)
        btns.addWidget(copy_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        v.addLayout(btns)
        dialog.exec()

    def closeEvent(self, event):
        # (O conteúdo desta função permanece o mesmo)
        logging.info("Fechando aplicação MatFinder.")
        if self.logo_blink_timer.isActive():
            self.logo_blink_timer.stop()

        if self.tabela_periodica_window_ref and self.tabela_periodica_window_ref.isVisible():
            self.tabela_periodica_window_ref.close()
        if self.calculadora_esteq_window_ref and self.calculadora_esteq_window_ref.isVisible():
            self.calculadora_esteq_window_ref.close()
        if self.historico_dialog_ref and self.historico_dialog_ref.isVisible():
            self.historico_dialog_ref.close()
        if self.calc_prop_massa_dialog_ref and self.calc_prop_massa_dialog_ref.isVisible():
            self.calc_prop_massa_dialog_ref.close()
        if self.phasedrx_window_ref and self.phasedrx_window_ref.isVisible():
            self.phasedrx_window_ref.close()

        super().closeEvent(event)

