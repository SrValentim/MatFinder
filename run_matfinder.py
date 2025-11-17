# run_matfinder.py
# Este é o novo script de inicialização para o MatFinder.
# Execute este arquivo para iniciar a aplicação.

import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, QSize

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


def main():
    """
    Função principal que inicializa a aplicação, mostra a splash screen
    e depois carrega a janela principal.
    """
    app = QApplication(sys.argv)

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
    main()