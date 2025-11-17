# teste.py
# Este script demonstra como obter os dados estruturais de uma entrada específica
# da OQMD API e construir um arquivo CIF formatado usando a biblioteca pymatgen.

import requests
from pymatgen.core import Structure
import sys


def get_cif_from_oqmd(entry_id: int):
    """
    Busca os dados estruturais de um material na OQMD pelo seu ID e retorna
    uma string formatada como um arquivo CIF.

    Args:
        entry_id (int): O ID da entrada do material na base de dados OQMD.

    Returns:
        str: Uma string contendo os dados no formato CIF, ou None se ocorrer um erro.
    """
    print(f"Buscando dados estruturais para o OQMD ID: {entry_id}...")

    # 1. Monta a URL para a API, pedindo apenas os campos que definem a estrutura.
    url = f"http://oqmd.org/oqmdapi/entry/{entry_id}?fields=unit_cell,sites,name"

    try:
        # 2. Faz a requisição à API
        response = requests.get(url, timeout=50)
        response.raise_for_status()  # Lança um erro se a resposta não for bem-sucedida (e.g., erro 404, 500)

        json_data = response.json()

        # 3. Verifica se os dados necessários foram retornados
        if "data" not in json_data or not json_data["data"]:
            print(f"Erro: Nenhum dado encontrado para o ID {entry_id}.")
            return None

        entry_data = json_data["data"]
        formula_name = entry_data.get("name", f"oqmd_{entry_id}")
        print(f"Dados encontrados para a fórmula: {formula_name}")

        if "unit_cell" not in entry_data or "sites" not in entry_data:
            print("Erro: A resposta da API não contém 'unit_cell' ou 'sites'.")
            return None

        # 4. Extrai os "ingredientes" para montar a estrutura
        lattice_vectors = entry_data["unit_cell"]
        site_strings = entry_data["sites"]

        species = []
        coordinates = []

        # Processa a string de cada átomo para separar a espécie da coordenada
        for site_str in site_strings:
            parts = site_str.split(" @ ")
            if len(parts) == 2:
                species.append(parts[0].strip())
                coords = [float(c) for c in parts[1].strip().split()]
                coordinates.append(coords)
            else:
                print(f"Aviso: Ignorando linha de sítio mal formatada: {site_str}")

        if not species or not coordinates:
            print("Erro: Não foi possível extrair as informações dos sítios atômicos.")
            return None

        # 5. Usa o pymatgen para criar o objeto 'Structure'
        print("Montando a estrutura com o pymatgen...")
        structure = Structure(lattice_vectors, species, coordinates)

        # 6. Converte o objeto 'Structure' para uma string no formato CIF
        print("Convertendo a estrutura para o formato CIF...")
        cif_string = structure.to(fmt="cif", author="MatFinder Test Script")

        return cif_string

    except requests.exceptions.RequestException as e:
        print(f"Erro de rede ao contatar a API do OQMD: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Erro ao processar os dados JSON recebidos da API: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        # O pymatgen pode lançar exceções se os dados forem inconsistentes
        return None


# --- Execução do Teste ---
if __name__ == "__main__":
    # ID escolhido a partir da sua imagem: GdO2, ID 1791911
    test_id = 1791911

    # Chama a função principal
    final_cif = get_cif_from_oqmd(test_id)

    print("\n" + "=" * 50)
    if final_cif:
        print(f"Arquivo CIF gerado com sucesso para o ID {test_id}:\n")
        print(final_cif)

        # Opcional: Salvar o resultado em um arquivo
        filename = f"OQMD_{test_id}.cif"
        with open(filename, "w") as f:
            f.write(final_cif)
        print(f"\nArquivo salvo como '{filename}'")

    else:
        print(f"Falha ao gerar o arquivo CIF para o ID {test_id}.")
    print("=" * 50)

