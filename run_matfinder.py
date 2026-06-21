# run_matfinder.py
# Este é o novo script de inicialização para o MatFinder.
# Execute este arquivo para iniciar a aplicação.

import sys
import os
import logging
import tempfile
from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, QSize, QLockFile

# --- Configuração básica do Logging ---
# (Mantido como está. O ficheiro 'matfinder.log' será criado
# na pasta raiz onde este script é executado, o que está correto.)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("matfinder.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso, útil para PyInstaller. """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def _selftest():
    """Auto-teste do build congelado (headless) — valida que NENHUM módulo ficou de fora.

    Importa todas as libs de terceiros que o app usa (inclusive as de import
    dinâmico/lazy, que o PyInstaller costuma perder) e todos os submódulos do
    pacote 'matfinder'. Reporta cada módulo ausente e sai 1 se faltar algo, 0 se OK.

    Uso:  MatFinder.exe --selftest
    Isso troca o ciclo "compila 15min -> abre -> crasha por módulo faltando" por
    uma verificação de ~10s que lista de uma vez tudo que falta.
    """
    import importlib
    import pkgutil

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    missing = []
    ok = 0

    # 1) Libs de terceiros realmente usadas pelo MatFinder (incl. submódulos lazy).
    third_party = [
        "PySide6.QtWidgets", "PySide6.QtGui", "PySide6.QtCore",
        "PySide6.QtOpenGLWidgets", "PySide6.QtPrintSupport", "PySide6.QtNetwork",
        "numpy", "scipy", "scipy.signal", "scipy.optimize", "scipy.interpolate",
        "scipy.ndimage", "scipy.special", "scipy.sparse",
        "matplotlib", "matplotlib.pyplot", "matplotlib.backends.backend_qtagg",
        "pyqtgraph", "pyqtgraph.opengl", "OpenGL.GL",
        "pymatgen.core", "pymatgen.core.structure", "pymatgen.io.cif",
        "pymatgen.symmetry.analyzer", "pymatgen.analysis.diffraction.xrd",
        "mp_api.client", "emmet.core", "monty.json", "monty.serialization",
        "spglib", "pydantic", "pydantic_core",
        "PIL.Image", "openpyxl", "bs4", "chempy", "cloudscraper", "requests",
        "pywt", "pandas",
    ]
    for name in third_party:
        try:
            importlib.import_module(name)
            ok += 1
        except ModuleNotFoundError as e:
            missing.append(f"{name}  (falta: {e.name})")
        except Exception as e:  # DLL ausente, etc. — também é problema de build
            missing.append(f"{name}  ({type(e).__name__}: {e})")

    # 2) Todos os submódulos do pacote 'matfinder'.
    try:
        import matfinder
        for info in pkgutil.walk_packages(matfinder.__path__, prefix="matfinder."):
            try:
                importlib.import_module(info.name)
                ok += 1
            except ModuleNotFoundError as e:
                missing.append(f"{info.name}  (falta: {e.name})")
            except Exception as e:
                msg = str(e)
                # Só nos importam falhas por módulo ausente; ignora erros de runtime/UI.
                if "No module named" in msg:
                    missing.append(f"{info.name}  ({msg})")
    except Exception as e:
        missing.append(f"matfinder (pacote raiz)  ({type(e).__name__}: {e})")

    # O .exe final é windowed (sem stdout); por isso gravamos um relatório em
    # arquivo. O exit code (0/1) é a fonte da verdade pro smoke test.
    lines = [f"[SELFTEST] modulos importados com sucesso: {ok}"]
    if missing:
        lines.append(f"[SELFTEST] FALHAS ({len(missing)}):")
        lines += ["   - " + m for m in missing]
        lines.append("[SELFTEST] RESULTADO: FALHOU")
    else:
        lines.append("[SELFTEST] RESULTADO: OK - nenhum modulo ausente")
    report = "\n".join(lines)
    print(report)
    try:
        report_path = os.environ.get("MATFINDER_SELFTEST_REPORT",
                                     os.path.join(os.getcwd(), "selftest_report.txt"))
        with open(report_path, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
    except Exception:
        pass
    return 1 if missing else 0


def main():
    """
    Função principal que inicializa a aplicação, mostra a splash screen
    e depois carrega a janela principal.
    """
    app = QApplication(sys.argv)

    # --- Verificação de Instância Única ---
    # Cria um arquivo de lock para garantir que apenas uma instância seja executada
    lock_file_path = os.path.join(tempfile.gettempdir(), "matfinder.lock")
    lock_file = QLockFile(lock_file_path)

    # Tenta obter o lock
    if not lock_file.tryLock(100):
        # Se não conseguir o lock, significa que já existe uma instância em execução
        QMessageBox.warning(
            None,
            "MatFinder já está em execução",
            "Uma instância do MatFinder já está em execução.\n"
            "Por favor, utilize a janela já aberta ou feche-a antes de abrir uma nova.",
            QMessageBox.StandardButton.Ok
        )
        logging.warning("Tentativa de abrir uma segunda instância bloqueada.")
        return

    logging.info(f"Lock file criado em: {lock_file_path}")

    # --- Etapa 1: Mostrar a Splash Screen Imediatamente ---
    splash = None
    try:
        # --- ALTERAÇÃO DE REATORAÇÃO 1: Caminho do Asset ---
        # O caminho agora aponta para dentro da nova estrutura de pastas
        # matfinder/assets/logos/
        splash_img_path = resource_path(os.path.join("matfinder", "assets", "logos", "splash.png"))

        if os.path.exists(splash_img_path):
            pixmap = QPixmap(splash_img_path)
            if not pixmap.isNull():
                # --- EDITE AS DIMENSÕES DA LOGO AQUI ---
                # Altere os valores (largura, altura) para ajustar o tamanho da splash screen.
                pixmap = pixmap.scaled(QSize(500, 300), Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)

                splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
                splash.show()
                splash.showMessage(
                    "Inicializando MatFinder...",
                    Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                    QColor("white")
                )
                # Processa os eventos da aplicação para garantir que a splash screen seja desenhada
                app.processEvents()
            else:
                logging.warning(f"Pixmap da splash screen em '{splash_img_path}' é inválido.")
        else:
            logging.warning(f"Imagem da splash screen não encontrada em: {splash_img_path}")
    except Exception as e:
        logging.error(f"Falha ao criar a splash screen: {e}")

    # --- Etapa 2: Importar e Carregar a Aplicação Principal (a parte demorada) ---
    if splash:
        splash.showMessage(
            "Carregando...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            QColor("white")
        )
        app.processEvents()

    # --- ALTERAÇÃO DE REATORAÇÃO 2: Importação Principal ---
    # A importação pesada só acontece AQUI.
    # Importamos a app principal (antiga OQMD_pyside.py)
    # do seu novo local (matfinder/app_main.py).
    from matfinder.app_main import MaterialsApp

    main_window = MaterialsApp()
    main_window.show()

    # --- Etapa 3: Fechar a Splash Screen ---
    if splash:
        splash.finish(main_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    main()