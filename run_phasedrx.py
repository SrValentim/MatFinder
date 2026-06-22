# run_phasedrx.py
# Ponto de entrada do "PhaseDRX Suite" — abre o PhaseDRX como aplicativo separado
# (mesmo fluxo da ferramenta dentro do MatFinder: diálogo Novo/Abrir projeto).

import sys
import os
import logging
import tempfile
from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap, QColor, QIcon
from PySide6.QtCore import Qt, QSize, QLockFile


# --- Diretório de dados GRAVÁVEL (igual ao MatFinder) ------------------------
def _ensure_writable_data_dir():
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        _probe = os.path.join(app_dir, ".write_test")
        with open(_probe, "w", encoding="utf-8") as _f:
            _f.write("ok")
        os.remove(_probe)
        return app_dir
    except Exception:
        base = (os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
                or tempfile.gettempdir())
        data_dir = os.path.join(base, "MatFinder")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir


os.chdir(_ensure_writable_data_dir())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("phasedrx.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def resource_path(relative_path):
    """Caminho absoluto do recurso (compatível com PyInstaller)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)

    # Ícone do app = PhaseDRX
    icon_png = resource_path(os.path.join("matfinder", "assets", "logos", "PhaseDRX.png"))
    if os.path.exists(icon_png):
        app.setWindowIcon(QIcon(icon_png))

    # Instância única (lock próprio, separado do MatFinder)
    lock_file = QLockFile(os.path.join(tempfile.gettempdir(), "phasedrx_suite.lock"))
    if not lock_file.tryLock(100):
        QMessageBox.warning(
            None, "PhaseDRX Suite",
            "O PhaseDRX Suite já está em execução.\nUtilize a janela já aberta.")
        return

    # Splash (mesmo padrão do MatFinder, com a logo do PhaseDRX)
    splash = None
    try:
        if os.path.exists(icon_png):
            pixmap = QPixmap(icon_png)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(QSize(420, 300), Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
                splash.show()
                splash.showMessage("Iniciando PhaseDRX Suite...",
                                   Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                                   QColor("white"))
                app.processEvents()
    except Exception as e:
        logging.error(f"Falha ao criar splash do PhaseDRX: {e}")

    # Abre o fluxo do PhaseDRX (diálogo Novo/Abrir projeto -> ferramenta).
    # A splash é fechada DENTRO de open_phasedrx, no instante em que o diálogo
    # de projeto aparece (não fica sobreposta a ele).
    from matfinder.phasedrx_launcher import open_phasedrx
    tool = open_phasedrx(parent=None, splash=splash)

    if tool is None:
        # Usuário cancelou o diálogo de projeto -> encerra o app
        if splash:
            splash.close()
        logging.info("PhaseDRX Suite: usuário cancelou o diálogo de projeto.")
        return

    tool.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
