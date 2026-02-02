# settings_manager.py
# Módulo para gerir as configurações da aplicação (idioma, etc.)
#
# CAMINHO: matfinder/core/settings_manager.py
#

import json
import os
import sys
import logging

SETTINGS_FILE = "settings.json"


class SettingsManager:
    """Gerencia as configurações da aplicação em settings.json"""
    
    def __init__(self):
        self.settings_file_path = self._resource_path(SETTINGS_FILE)
        self.settings = self.load_settings()
    
    def _resource_path(self, relative_path):
        """
        Obtém o caminho absoluto para o recurso.
        """
        try:
            # Se estiver compilado (PyInstaller), _MEIPASS é a pasta de extração
            base_path = sys._MEIPASS
        except AttributeError:
            # Em desenvolvimento, usa a raiz do projeto
            # __file__ -> matfinder/core/settings_manager.py
            # .. -> matfinder/
            # .. -> MatFinder/ (raiz)
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        
        return os.path.join(base_path, relative_path)
    
    def load_settings(self):
        """
        Carrega as configurações do arquivo JSON.
        Retorna um dicionário com configurações padrão se o arquivo não existir.
        """
        default_settings = {
            "language": "pt",  # Idioma padrão: Português
        }
        
        try:
            if os.path.exists(self.settings_file_path):
                with open(self.settings_file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Garante que todas as chaves padrão existam
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    logging.info(f"Configurações carregadas de {self.settings_file_path}")
                    return settings
            else:
                logging.info(f"Arquivo de configurações não encontrado. Usando configurações padrão.")
                return default_settings
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON de {self.settings_file_path}: {e}")
            return default_settings
        except Exception as e:
            logging.error(f"Erro ao carregar configurações: {e}")
            return default_settings
    
    def save_settings(self):
        """
        Salva as configurações atuais no arquivo JSON.
        """
        try:
            with open(self.settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logging.info(f"Configurações salvas em {self.settings_file_path}")
            return True
        except IOError as e:
            logging.error(f"Erro de E/S ao salvar configurações: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def get_language(self):
        """Retorna o idioma atual"""
        return self.settings.get("language", "pt")
    
    def set_language(self, language_code):
        """
        Define o idioma.
        language_code: 'pt', 'en', ou 'de'
        """
        if language_code in ["pt", "en", "de"]:
            self.settings["language"] = language_code
            return self.save_settings()
        else:
            logging.warning(f"Código de idioma inválido: {language_code}")
            return False


# Instância global do gerenciador de configurações
settings_manager = SettingsManager()
