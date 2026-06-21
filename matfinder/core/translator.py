# translator.py
# Sistema de internacionalização (i18n) para MatFinder
# Suporta: Português (pt_BR), Inglês (en_US), Alemão (de_DE)

import json
import logging
import os
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal

# Idiomas suportados
SUPPORTED_LANGUAGES = {
    'pt_BR': 'Português (Brasil)',
    'en_US': 'English (US)',
    'de_DE': 'Deutsch'
}

DEFAULT_LANGUAGE = 'en_US'


class Translator(QObject):
    """
    Classe singleton para gerenciamento de traduções.
    Emite sinal quando o idioma é alterado para atualizar a UI.
    """

    language_changed = Signal(str)  # Emite o código do novo idioma

    _instance: Optional['Translator'] = None
    _translations: Dict[str, Dict[str, str]] = {}
    _current_language: str = DEFAULT_LANGUAGE
    _translations_dir: str = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._translations = {}
        self._current_language = DEFAULT_LANGUAGE

        # Diretório de traduções
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._translations_dir = os.path.join(base_dir, 'assets', 'translations')

        # Criar diretório se não existir
        os.makedirs(self._translations_dir, exist_ok=True)

        # Carregar idioma salvo nas configurações
        self._load_saved_language()

        # Carregar traduções do idioma atual
        self._load_translations(self._current_language)

    def _load_saved_language(self):
        """Carrega o idioma salvo em settings.json no diretório de dados GRAVÁVEL
        (cwd, definido no boot do app). 1ª execução (sem settings) usa o padrão
        (DEFAULT_LANGUAGE = inglês). Não lê mais o config/language.json embarcado."""
        try:
            settings_file = os.path.join(os.getcwd(), 'settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                saved_lang = config.get('language', DEFAULT_LANGUAGE)
                if saved_lang in SUPPORTED_LANGUAGES:
                    self._current_language = saved_lang
                    logging.info(f"Idioma carregado: {saved_lang}")
        except Exception as e:
            logging.warning(f"Erro ao carregar idioma salvo: {e}")

    def _save_language(self, language: str):
        """Salva o idioma em settings.json no diretório de dados GRAVÁVEL (cwd).
        (Antes gravava na pasta do app -> falhava quando instalado em Program Files.)"""
        try:
            settings_file = os.path.join(os.getcwd(), 'settings.json')
            settings = {}
            if os.path.exists(settings_file):
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                except Exception:
                    settings = {}

            settings['language'] = language

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            logging.info(f"Idioma salvo em settings.json: {language}")
        except Exception as e:
            logging.error(f"Erro ao salvar idioma: {e}")

    def _load_translations(self, language: str):
        """Carrega as traduções de um idioma específico."""
        translation_file = os.path.join(self._translations_dir, f'{language}.json')

        try:
            if os.path.exists(translation_file):
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self._translations[language] = json.load(f)
                logging.info(f"Traduções carregadas para: {language}")
            else:
                logging.warning(f"Arquivo de tradução não encontrado: {translation_file}")
                self._translations[language] = {}
        except Exception as e:
            logging.error(f"Erro ao carregar traduções para {language}: {e}")
            self._translations[language] = {}

    def set_language(self, language: str) -> bool:
        """
        Define o idioma atual da aplicação.

        Args:
            language: Código do idioma (ex: 'pt_BR', 'en_US', 'de_DE')

        Returns:
            True se o idioma foi alterado com sucesso
        """
        if language not in SUPPORTED_LANGUAGES:
            logging.error(f"Idioma não suportado: {language}")
            return False

        if language == self._current_language:
            return True

        # Carregar traduções se ainda não carregadas
        if language not in self._translations:
            self._load_translations(language)

        self._current_language = language
        self._save_language(language)

        # Emitir sinal para atualizar a UI
        self.language_changed.emit(language)
        logging.info(f"Idioma alterado para: {language}")

        return True

    def get_current_language(self) -> str:
        """Retorna o código do idioma atual."""
        return self._current_language

    def get_language_name(self, language: str = None) -> str:
        """Retorna o nome legível do idioma."""
        lang = language or self._current_language
        return SUPPORTED_LANGUAGES.get(lang, lang)

    def tr(self, key: str, **kwargs) -> str:
        """
        Traduz uma chave para o idioma atual.

        Args:
            key: Chave de tradução (ex: 'menu.file', 'dialog.save.title')
            **kwargs: Variáveis para substituição na string (ex: {name}, {count})

        Returns:
            String traduzida ou a chave original se não encontrada
        """
        translations = self._translations.get(self._current_language, {})

        # Buscar tradução usando notação de ponto (ex: 'menu.file.open')
        result = self._get_nested_value(translations, key)

        if result is None:
            # Fallback para português se não encontrar
            if self._current_language != DEFAULT_LANGUAGE:
                if DEFAULT_LANGUAGE not in self._translations:
                    self._load_translations(DEFAULT_LANGUAGE)
                result = self._get_nested_value(
                    self._translations.get(DEFAULT_LANGUAGE, {}), key
                )

            if result is None:
                # Retornar a chave se não houver tradução
                logging.debug(f"Tradução não encontrada: {key}")
                return key

        # Substituir variáveis
        if kwargs:
            try:
                result = result.format(**kwargs)
            except KeyError as e:
                logging.warning(f"Variável não encontrada na tradução '{key}': {e}")

        return result

    def _get_nested_value(self, data: dict, key: str) -> Optional[str]:
        """Obtém valor aninhado usando notação de ponto."""
        keys = key.split('.')
        value = data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value if isinstance(value, str) else None

    def get_available_languages(self) -> Dict[str, str]:
        """Retorna dicionário com idiomas disponíveis."""
        return SUPPORTED_LANGUAGES.copy()


# Instância global do tradutor
_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """Obtém a instância global do tradutor."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def tr(key: str, **kwargs) -> str:
    """
    Função de conveniência para tradução.

    Uso:
        from matfinder.core.translator import tr

        label = tr('menu.file.open')
        message = tr('dialog.save.confirm', filename='teste.txt')
    """
    return get_translator().tr(key, **kwargs)


def set_language(language: str) -> bool:
    """Função de conveniência para definir idioma."""
    return get_translator().set_language(language)


def get_current_language() -> str:
    """Função de conveniência para obter idioma atual."""
    return get_translator().get_current_language()
