# favorites_manager.py
# Módulo para gerir a persistência de compostos favoritos.
#
# CAMINHO REFATORADO: matfinder/core/favorites_manager.py
#

import json
import os
import sys
import logging

FAVORITES_FILE = "favorites.json"


class FavoritesManager:
    def __init__(self):
        self.favorites_file_path = self._resource_path(FAVORITES_FILE)
        self.favorited_ids = self.load_favorites()

    def _resource_path(self, relative_path):
        """
        Obtém o caminho absoluto para o recurso.
        Modificado para apontar para a pasta raiz do projeto,
        não para a pasta 'core'.
        """
        try:
            # Se estiver compilado (PyInstaller), _MEIPASS é a pasta de extração
            base_path = sys._MEIPASS
        except AttributeError:
            # --- ALTERAÇÃO DE REATORAÇÃO: Lógica de Caminho ---
            # Em vez de os.path.abspath("."), subimos dois níveis
            # de __file__ (que está em matfinder/core/) para
            # chegar à raiz (MatFinder/).
            # __file__ -> matfinder/core/favorites_manager.py
            # .. -> matfinder/
            # .. -> MatFinder/ (raiz)
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            # --- FIM DA ALTERAÇÃO ---

        return os.path.join(base_path, relative_path)

    def load_favorites(self):
        """
        Carrega o conjunto de IDs de compostos favoritos do ficheiro JSON.
        Retorna um conjunto vazio se o ficheiro não existir ou estiver corrompido.
        """
        try:
            if os.path.exists(self.favorites_file_path):
                with open(self.favorites_file_path, 'r', encoding='utf-8') as f:
                    # Carrega a lista e converte-a para um conjunto para buscas rápidas
                    return set(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Erro ao carregar favoritos de '{self.favorites_file_path}': {e}")
        return set()

    def save_favorites(self):
        """Salva o conjunto atual de IDs favoritos no ficheiro JSON."""
        try:
            with open(self.favorites_file_path, 'w', encoding='utf-8') as f:
                # Converte o conjunto para uma lista para ser serializável em JSON
                json.dump(list(self.favorited_ids), f, indent=4)
        except IOError as e:
            logging.error(f"Erro ao salvar favoritos em '{self.favorites_file_path}': {e}")

    def is_favorite(self, compound_id: str) -> bool:
        """Verifica se um ID de composto está na lista de favoritos."""
        return compound_id in self.favorited_ids

    def add_favorite(self, compound_id: str):
        """Adiciona um ID de composto aos favoritos e salva."""
        if compound_id not in self.favorited_ids:
            self.favorited_ids.add(compound_id)
            self.save_favorites()
            logging.info(f"Composto '{compound_id}' adicionado aos favoritos.")

    def remove_favorite(self, compound_id: str):
        """Remove um ID de composto dos favoritos e salva."""
        if compound_id in self.favorited_ids:
            self.favorited_ids.remove(compound_id)
            self.save_favorites()
            logging.info(f"Composto '{compound_id}' removido dos favoritos.")


# Cria uma instância única (singleton) para ser usada em toda a aplicação
favorites_manager = FavoritesManager()