# i18n.py
# Módulo de internacionalização (i18n) para suporte a múltiplos idiomas
#
# CAMINHO: matfinder/core/i18n.py
#

# Dicionários de tradução para cada idioma
TRANSLATIONS = {
    "pt": {
        # Menu principal
        "menu_file": "&Arquivo",
        "menu_history": "Histórico de &Busca",
        "menu_history_tip": "Visualizar e gerenciar o histórico de buscas",
        "menu_exit": "&Sair",
        "menu_exit_tip": "Sair da aplicação",
        
        "menu_config": "&Configuração",
        "menu_api_key": "Chave API &Materials Project...",
        "menu_api_key_tip": "Configurar a chave da API para o Materials Project",
        "menu_proxy": "Configurar &Proxy...",
        "menu_proxy_tip": "Configurar servidor proxy para conexões de rede",
        "menu_language": "&Idioma",
        "menu_language_tip": "Selecionar idioma da interface",
        
        "menu_tools": "F&erramentas",
        "menu_about": "S&obre",
        
        # Submenu de idioma
        "language_portuguese": "Português",
        "language_english": "English",
        "language_german": "Deutsch",
        
        # Diálogo de reinicialização
        "restart_title": "Reiniciar Aplicação",
        "restart_message": "O idioma foi alterado para {}.\n\nÉ necessário reiniciar a aplicação para aplicar as mudanças.\n\nDeseja reiniciar agora?",
        "restart_info_title": "Idioma Alterado",
        "restart_info_message": "O idioma foi alterado para {}.\n\nPor favor, reinicie a aplicação para aplicar as mudanças.",
    },
    "en": {
        # Main menu
        "menu_file": "&File",
        "menu_history": "Search &History",
        "menu_history_tip": "View and manage search history",
        "menu_exit": "&Exit",
        "menu_exit_tip": "Exit the application",
        
        "menu_config": "&Settings",
        "menu_api_key": "&Materials Project API Key...",
        "menu_api_key_tip": "Configure the Materials Project API key",
        "menu_proxy": "Configure &Proxy...",
        "menu_proxy_tip": "Configure proxy server for network connections",
        "menu_language": "&Language",
        "menu_language_tip": "Select interface language",
        
        "menu_tools": "&Tools",
        "menu_about": "&About",
        
        # Language submenu
        "language_portuguese": "Português",
        "language_english": "English",
        "language_german": "Deutsch",
        
        # Restart dialog
        "restart_title": "Restart Application",
        "restart_message": "The language has been changed to {}.\n\nA restart is required to apply the changes.\n\nWould you like to restart now?",
        "restart_info_title": "Language Changed",
        "restart_info_message": "The language has been changed to {}.\n\nPlease restart the application to apply the changes.",
    },
    "de": {
        # Hauptmenü
        "menu_file": "&Datei",
        "menu_history": "Such&verlauf",
        "menu_history_tip": "Suchverlauf anzeigen und verwalten",
        "menu_exit": "&Beenden",
        "menu_exit_tip": "Anwendung beenden",
        
        "menu_config": "&Einstellungen",
        "menu_api_key": "&Materials Project API-Schlüssel...",
        "menu_api_key_tip": "Materials Project API-Schlüssel konfigurieren",
        "menu_proxy": "&Proxy konfigurieren...",
        "menu_proxy_tip": "Proxy-Server für Netzwerkverbindungen konfigurieren",
        "menu_language": "&Sprache",
        "menu_language_tip": "Schnittstellensprache auswählen",
        
        "menu_tools": "&Werkzeuge",
        "menu_about": "&Über",
        
        # Sprachuntermenü
        "language_portuguese": "Português",
        "language_english": "English",
        "language_german": "Deutsch",
        
        # Neustart-Dialog
        "restart_title": "Anwendung neu starten",
        "restart_message": "Die Sprache wurde auf {} geändert.\n\nEin Neustart ist erforderlich, um die Änderungen anzuwenden.\n\nMöchten Sie jetzt neu starten?",
        "restart_info_title": "Sprache geändert",
        "restart_info_message": "Die Sprache wurde auf {} geändert.\n\nBitte starten Sie die Anwendung neu, um die Änderungen anzuwenden.",
    }
}

# Idioma atual (será definido na inicialização da aplicação)
_current_language = "pt"


def set_language(language_code):
    """Define o idioma atual da aplicação"""
    global _current_language
    if language_code in TRANSLATIONS:
        _current_language = language_code
    else:
        _current_language = "pt"


def get_language():
    """Retorna o código do idioma atual"""
    return _current_language


def tr(key):
    """
    Traduz uma chave para o idioma atual.
    Se a tradução não existir, retorna a chave em português.
    """
    translations = TRANSLATIONS.get(_current_language, TRANSLATIONS["pt"])
    return translations.get(key, TRANSLATIONS["pt"].get(key, key))


def get_language_name(language_code):
    """Retorna o nome do idioma no próprio idioma"""
    names = {
        "pt": "Português",
        "en": "English", 
        "de": "Deutsch"
    }
    return names.get(language_code, "Português")
