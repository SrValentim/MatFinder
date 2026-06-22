# -*- coding: utf-8 -*-
"""
log_viewer_dialog.py - Visualizador de Log do MatFinder
Versão: 3.24.0
Autor: Raynner Valentim - UFAM

Diálogo para visualização, exportação e gerenciamento de logs do sistema.
"""

import os
import sys
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QComboBox, QFileDialog, QMessageBox, QGroupBox,
    QCheckBox, QSpinBox, QApplication, QSplitter, QWidget
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QTextCursor, QColor, QIcon, QTextCharFormat
from matfinder.core.translator import ptr

# Importar sistema de tradução
try:
    from matfinder.core.translator import tr
except ImportError:
    def tr(key, **kwargs):
        return kwargs.get('default', key)


class LogViewerDialog(QDialog):
    """Diálogo para visualização de logs do MatFinder."""

    def __init__(self, parent=None, log_file_path=None):
        super().__init__(parent)
        self.log_file_path = log_file_path or self._get_default_log_path()
        self.auto_scroll = True
        self.auto_refresh = False
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_log)
        self.last_position = 0

        self._setup_ui()
        self._load_log()

        # Configurar ícone
        self._setup_icon()

    def _setup_icon(self):
        """Configura o ícone da janela."""
        try:
            icon_path = self._resource_path(os.path.join('matfinder', 'assets', 'icons', 'polvo.ico'))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

    def _resource_path(self, relative_path):
        """Obtém caminho absoluto para recursos."""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(base_path, relative_path)

    def _get_default_log_path(self):
        """Retorna o caminho padrão do arquivo de log."""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(base_path, "matfinder.log")

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        self.setWindowTitle(tr('log_viewer.title', default='Log do Sistema - MatFinder'))
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # === CABEÇALHO ===
        header_layout = QHBoxLayout()

        title_label = QLabel(tr('log_viewer.header', default='Visualizador de Log'))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Informações do arquivo
        self.file_info_label = QLabel()
        self.file_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        header_layout.addWidget(self.file_info_label)

        main_layout.addLayout(header_layout)

        # === CONTROLES ===
        controls_group = QGroupBox(tr('log_viewer.controls', default='Controles'))
        controls_layout = QHBoxLayout(controls_group)

        # Filtro de nível
        controls_layout.addWidget(QLabel(tr('log_viewer.filter_level', default='Filtrar por nível:')))
        self.level_filter = QComboBox()
        self.level_filter.addItems([ptr('Todos'), ptr('DEBUG'), ptr('INFO'), ptr('WARNING'), ptr('ERROR'), ptr('CRITICAL')])
        self.level_filter.currentTextChanged.connect(self._apply_filter)
        self.level_filter.setMinimumWidth(100)
        controls_layout.addWidget(self.level_filter)

        controls_layout.addSpacing(20)

        # Auto-scroll
        self.auto_scroll_check = QCheckBox(tr('log_viewer.auto_scroll', default='Auto-scroll'))
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.stateChanged.connect(self._toggle_auto_scroll)
        controls_layout.addWidget(self.auto_scroll_check)

        # Auto-refresh
        self.auto_refresh_check = QCheckBox(tr('log_viewer.auto_refresh', default='Atualização automática'))
        self.auto_refresh_check.setChecked(False)
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_check)

        # Intervalo de atualização
        controls_layout.addWidget(QLabel(tr('log_viewer.refresh_interval', default='Intervalo (s):')))
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(1, 60)
        self.refresh_interval.setValue(5)
        self.refresh_interval.setMaximumWidth(60)
        controls_layout.addWidget(self.refresh_interval)

        controls_layout.addStretch()

        # Botão atualizar
        self.refresh_btn = QPushButton(tr('log_viewer.refresh', default='Atualizar'))
        self.refresh_btn.clicked.connect(self._load_log)
        controls_layout.addWidget(self.refresh_btn)

        main_layout.addWidget(controls_group)

        # === ÁREA DE LOG ===
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        main_layout.addWidget(self.log_text, 1)

        # === ESTATÍSTICAS ===
        stats_layout = QHBoxLayout()

        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #7f8c8d;")
        stats_layout.addWidget(self.stats_label)

        stats_layout.addStretch()

        # Contadores de níveis
        self.error_count_label = QLabel()
        self.error_count_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        stats_layout.addWidget(self.error_count_label)

        self.warning_count_label = QLabel()
        self.warning_count_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        stats_layout.addWidget(self.warning_count_label)

        self.info_count_label = QLabel()
        self.info_count_label.setStyleSheet("color: #3498db; font-weight: bold;")
        stats_layout.addWidget(self.info_count_label)

        main_layout.addLayout(stats_layout)

        # === BOTÕES DE AÇÃO ===
        buttons_layout = QHBoxLayout()

        # Limpar log
        self.clear_btn = QPushButton(tr('log_viewer.clear', default='Limpar Log'))
        self.clear_btn.setStyleSheet("color: #e74c3c;")
        self.clear_btn.clicked.connect(self._clear_log)
        buttons_layout.addWidget(self.clear_btn)

        buttons_layout.addStretch()

        # Exportar
        export_label = QLabel(tr('log_viewer.export_to', default='Exportar para:'))
        buttons_layout.addWidget(export_label)

        self.export_format = QComboBox()
        self.export_format.addItems([ptr('TXT'), ptr('LOG'), ptr('HTML'), ptr('PDF'), ptr('CSV')])
        self.export_format.setMinimumWidth(80)
        buttons_layout.addWidget(self.export_format)

        self.export_btn = QPushButton(tr('log_viewer.export', default='Exportar'))
        self.export_btn.clicked.connect(self._export_log)
        buttons_layout.addWidget(self.export_btn)

        buttons_layout.addSpacing(20)

        # Fechar
        self.close_btn = QPushButton(tr('dialogs.confirm.close', default='Fechar'))
        self.close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_btn)

        main_layout.addLayout(buttons_layout)

    def _load_log(self):
        """Carrega o conteúdo do arquivo de log."""
        try:
            if not os.path.exists(self.log_file_path):
                self.log_text.setPlainText(tr('log_viewer.no_log_file',
                    default=f"Arquivo de log não encontrado:\n{self.log_file_path}"))
                self._update_stats([])
                return

            with open(self.log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            lines = content.split('\n')
            self._display_log(lines)
            self._update_file_info()

            if self.auto_scroll:
                self.log_text.moveCursor(QTextCursor.MoveOperation.End)

        except Exception as e:
            self.log_text.setPlainText(f"Erro ao carregar log: {str(e)}")
            logging.error(f"Erro ao carregar log: {e}")

    def _display_log(self, lines):
        """Exibe as linhas de log com formatação de cores."""
        self.log_text.clear()

        current_filter = self.level_filter.currentText()

        # Contadores
        counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}

        cursor = self.log_text.textCursor()

        for line in lines:
            if not line.strip():
                continue

            # Detectar nível do log
            level = self._detect_level(line)
            if level:
                counts[level] = counts.get(level, 0) + 1

            # Aplicar filtro
            if current_filter != 'Todos' and level != current_filter:
                continue

            # Definir cor baseada no nível
            format = QTextCharFormat()
            if 'ERROR' in line or 'CRITICAL' in line:
                format.setForeground(QColor("#e74c3c"))  # Vermelho
            elif 'WARNING' in line:
                format.setForeground(QColor("#f39c12"))  # Laranja
            elif 'INFO' in line:
                format.setForeground(QColor("#3498db"))  # Azul
            elif 'DEBUG' in line:
                format.setForeground(QColor("#95a5a6"))  # Cinza
            else:
                format.setForeground(QColor("#d4d4d4"))  # Branco

            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(line + '\n', format)

        self._update_stats(counts)

    def _detect_level(self, line):
        """Detecta o nível de log de uma linha."""
        levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
        for level in levels:
            if f' - {level} - ' in line or f'[{level}]' in line:
                return level
        return None

    def _update_stats(self, counts):
        """Atualiza as estatísticas de log."""
        if isinstance(counts, dict):
            total = sum(counts.values())
            self.stats_label.setText(ptr("Total: {} entradas").format(total))
            self.error_count_label.setText(ptr("Erros: {}").format(counts.get('ERROR', 0) + counts.get('CRITICAL', 0)))
            self.warning_count_label.setText(ptr("Avisos: {}").format(counts.get('WARNING', 0)))
            self.info_count_label.setText(ptr("Info: {}").format(counts.get('INFO', 0)))
        else:
            self.stats_label.setText(ptr("Total: 0 entradas"))
            self.error_count_label.setText(ptr("Erros: 0"))
            self.warning_count_label.setText(ptr("Avisos: 0"))
            self.info_count_label.setText(ptr("Info: 0"))

    def _update_file_info(self):
        """Atualiza informações do arquivo."""
        try:
            if os.path.exists(self.log_file_path):
                size = os.path.getsize(self.log_file_path)
                mtime = datetime.fromtimestamp(os.path.getmtime(self.log_file_path))

                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"

                self.file_info_label.setText(
                    ptr("Arquivo: {} | Tamanho: {} | Modificado: {}").format(os.path.basename(self.log_file_path), size_str, mtime.strftime('%d/%m/%Y %H:%M:%S'))
                )
        except Exception:
            self.file_info_label.setText("")

    def _apply_filter(self):
        """Aplica o filtro de nível."""
        self._load_log()

    def _toggle_auto_scroll(self, state):
        """Ativa/desativa auto-scroll."""
        self.auto_scroll = state == Qt.CheckState.Checked.value

    def _toggle_auto_refresh(self, state):
        """Ativa/desativa atualização automática."""
        self.auto_refresh = state == Qt.CheckState.Checked.value
        if self.auto_refresh:
            interval = self.refresh_interval.value() * 1000
            self.refresh_timer.start(interval)
        else:
            self.refresh_timer.stop()

    def _refresh_log(self):
        """Atualiza o log (chamado pelo timer)."""
        self._load_log()

    def _clear_log(self):
        """Limpa o arquivo de log."""
        reply = QMessageBox.question(
            self,
            tr('log_viewer.clear_confirm_title', default='Confirmar Limpeza'),
            tr('log_viewer.clear_confirm_msg', default='Tem certeza que deseja limpar todo o log?\nEsta ação não pode ser desfeita.'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.log_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Log limpo em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

                logging.info("Log limpo pelo usuário")
                self._load_log()

                QMessageBox.information(
                    self,
                    tr('log_viewer.clear_success_title', default='Log Limpo'),
                    tr('log_viewer.clear_success_msg', default='O arquivo de log foi limpo com sucesso.')
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    tr('log_viewer.clear_error_title', default='Erro'),
                    ptr("Erro ao limpar log: {}").format(str(e))
                )

    def _export_log(self):
        """Exporta o log para o formato selecionado."""
        format_selected = self.export_format.currentText()

        # Definir extensão e filtro
        extensions = {
            'TXT': ('txt', 'Arquivo de Texto (*.txt)'),
            'LOG': ('log', 'Arquivo de Log (*.log)'),
            'HTML': ('html', 'Arquivo HTML (*.html)'),
            'PDF': ('pdf', 'Arquivo PDF (*.pdf)'),
            'CSV': ('csv', 'Arquivo CSV (*.csv)')
        }

        ext, filter_str = extensions.get(format_selected, ('txt', 'Arquivo de Texto (*.txt)'))

        # Diálogo de salvamento
        default_name = f"matfinder_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr('log_viewer.export_dialog_title', default='Exportar Log'),
            default_name,
            filter_str
        )

        if not file_path:
            return

        try:
            content = self.log_text.toPlainText()

            if format_selected == 'HTML':
                self._export_html(file_path, content)
            elif format_selected == 'PDF':
                self._export_pdf(file_path, content)
            elif format_selected == 'CSV':
                self._export_csv(file_path, content)
            else:
                # TXT ou LOG - exportação simples
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            QMessageBox.information(
                self,
                tr('log_viewer.export_success_title', default='Exportação Concluída'),
                tr('log_viewer.export_success_msg', default=f'Log exportado com sucesso para:\n{file_path}')
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                tr('log_viewer.export_error_title', default='Erro na Exportação'),
                ptr("Erro ao exportar log: {}").format(str(e))
            )

    def _export_html(self, file_path, content):
        """Exporta log em formato HTML."""
        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MatFinder - Log do Sistema</title>
    <style>
        body {{
            font-family: 'Consolas', 'Courier New', monospace;
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            line-height: 1.4;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 5px 0 0 0; opacity: 0.8; }}
        .log-container {{
            background-color: #252526;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
        }}
        .log-line {{ margin: 2px 0; white-space: pre-wrap; }}
        .level-error {{ color: #e74c3c; }}
        .level-warning {{ color: #f39c12; }}
        .level-info {{ color: #3498db; }}
        .level-debug {{ color: #95a5a6; }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MatFinder - Log do Sistema</h1>
        <p>Universidade Federal do Amazonas - UFAM</p>
        <p>Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>
    <div class="log-container">
"""
        # Processar linhas
        for line in content.split('\n'):
            if not line.strip():
                continue

            css_class = 'log-line'
            if 'ERROR' in line or 'CRITICAL' in line:
                css_class += ' level-error'
            elif 'WARNING' in line:
                css_class += ' level-warning'
            elif 'INFO' in line:
                css_class += ' level-info'
            elif 'DEBUG' in line:
                css_class += ' level-debug'

            # Escapar caracteres HTML
            line_escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_content += f'        <div class="{css_class}">{line_escaped}</div>\n'

        html_content += """    </div>
    <div class="footer">
        <p>MatFinder - Software de Análise de Materiais Cristalinos</p>
        <p>Desenvolvido por Raynner Valentim - UFAM</p>
    </div>
</body>
</html>"""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _export_pdf(self, file_path, content):
        """Exporta log em formato PDF."""
        try:
            from PySide6.QtGui import QFont, QTextDocument
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtCore import QMarginsF

            # Criar documento HTML para PDF
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Consolas, monospace; font-size: 9pt; }}
                    .header {{ 
                        text-align: center; 
                        border-bottom: 2px solid #2c3e50; 
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }}
                    .header h1 {{ color: #2c3e50; margin: 0; }}
                    .header p {{ color: #7f8c8d; margin: 5px 0; }}
                    .log {{ white-space: pre-wrap; font-size: 8pt; }}
                    .error {{ color: #e74c3c; }}
                    .warning {{ color: #f39c12; }}
                    .info {{ color: #3498db; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>MatFinder - Log do Sistema</h1>
                    <p>Universidade Federal do Amazonas - UFAM</p>
                    <p>Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                <div class="log">
            """

            for line in content.split('\n'):
                if not line.strip():
                    continue

                css_class = ''
                if 'ERROR' in line or 'CRITICAL' in line:
                    css_class = 'error'
                elif 'WARNING' in line:
                    css_class = 'warning'
                elif 'INFO' in line:
                    css_class = 'info'

                line_escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if css_class:
                    html_content += f'<span class="{css_class}">{line_escaped}</span><br/>'
                else:
                    html_content += f'{line_escaped}<br/>'

            html_content += """
                </div>
            </body>
            </html>
            """

            # Criar printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageMargins(QMarginsF(15, 15, 15, 15))

            # Criar documento e imprimir
            doc = QTextDocument()
            doc.setHtml(html_content)
            doc.print_(printer)

        except Exception as e:
            # Fallback: salvar como texto se PDF falhar
            logging.warning(f"Falha ao criar PDF, salvando como texto: {e}")
            with open(file_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write(f"MatFinder - Log do Sistema\n")
                f.write(f"Universidade Federal do Amazonas - UFAM\n")
                f.write(f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(content)
            raise Exception(ptr("PDF não disponível. Salvo como TXT: {}").format(e))

    def _export_csv(self, file_path, content):
        """Exporta log em formato CSV."""
        import csv

        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Data/Hora', 'Nível', 'Módulo', 'Mensagem'])

            for line in content.split('\n'):
                if not line.strip():
                    continue

                # Tentar parsear linha de log padrão
                # Formato: 2024-01-01 12:00:00,000 - INFO - [module:123] - Mensagem
                try:
                    parts = line.split(' - ', 3)
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        level = parts[1]
                        module = parts[2]
                        message = parts[3]
                    else:
                        timestamp = ''
                        level = ''
                        module = ''
                        message = line

                    writer.writerow([timestamp, level, module, message])
                except Exception:
                    writer.writerow(['', '', '', line])


# Teste standalone
if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = LogViewerDialog()
    dialog.show()
    sys.exit(app.exec())
