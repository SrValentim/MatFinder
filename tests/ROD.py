import requests
import json
from urllib.parse import urlencode  # Para construir a query string corretamente

# URL base para a API de busca da Raman Open Database (ROD)
ROD_SEARCH_BASE_URL = "https://solsa.crystallography.net/rod/result"


def search_rod_by_elements(elements_list: list, result_format: str = "json", timeout: int = 45):
    """
    Busca na Raman Open Database (ROD) por entradas contendo os elementos especificados.

    Args:
        elements_list (list): Uma lista de strings, onde cada string é um símbolo de elemento (ex: ["Si", "C"]).
        result_format (str, optional): O formato desejado para os resultados. Defaults to "json".
        timeout (int, optional): Tempo máximo em segundos para esperar pela resposta. Defaults to 45.

    Returns:
        list or str or None: Uma lista de dicionários se result_format for "json" e a requisição for bem-sucedida,
                             uma string para outros formatos, ou None se ocorrer um erro.
    """
    if not elements_list:
        print("ROD API: A lista de elementos não pode ser vazia.")
        return None

    params = {}
    for i, el_symbol in enumerate(elements_list):
        if i < 8:  # API da ROD, similar à do COD, suporta até el8
            params[f"el{i + 1}"] = el_symbol.strip().capitalize()
        else:
            print(
                f"ROD API: Máximo de 8 elementos suportados para busca. Ignorando extras: {elements_list[8:]}"
            )
            break

    params["format"] = result_format

    # A interface web da ROD tem uma opção "excluding theoretical spectra".
    # A API RESTful documentada (https://wiki.crystallography.net/rod/RESTful_API/)
    # não menciona um parâmetro direto para isso. Pode ser necessário filtrar após a busca.
    # Para este teste, não aplicaremos esse filtro via API.

    print(
        f"ROD API: Buscando por elementos: {', '.join(elements_list)} no formato: {result_format}"
    )
    # Para depuração, você pode querer ver a URL completa:
    # query_string = urlencode(params)
    # full_url = f"{ROD_SEARCH_BASE_URL}?{query_string}"
    # print(f"ROD API: URL da requisição: {full_url}")

    try:
        response = requests.get(ROD_SEARCH_BASE_URL, params=params, timeout=timeout)
        response.raise_for_status()  # Levanta um HTTPError para respostas com erro (4xx ou 5xx)

        if result_format == "json":
            try:
                # A API da ROD para busca por elementos com format=json retorna uma LISTA de entradas
                return response.json()
            except json.JSONDecodeError as json_err:
                print("ROD API: Erro ao decodificar JSON da resposta.")
                print(f"  Status Code: {response.status_code}")
                print(f"  Resposta (primeiros 500 chars): {response.text[:500]}")
                print(f"  Erro JSON: {json_err}")
                return None
        else:
            return response.text

    except requests.exceptions.Timeout as timeout_err:
        print(f"ROD API: Timeout na requisição: {timeout_err}")
    except requests.exceptions.HTTPError as http_err:
        print(f"ROD API: Erro HTTP {http_err.response.status_code}: {http_err}")
        print(f"  Resposta do servidor (primeiros 500 chars): {http_err.response.text[:500]}")
    except requests.exceptions.RequestException as req_err:
        print(f"ROD API: Erro de requisição: {req_err}")

    return None


if __name__ == "__main__":
    print("--- Iniciando Teste de Busca na Raman Open Database (ROD) ---")

    elementos_de_busca = ["Si", "C"]
    # elementos_de_busca = ["Fe", "O"] # Outro exemplo

    print(f"\nBuscando por elementos: {elementos_de_busca}")
    # A API da ROD para busca por elementos retorna uma LISTA de dicionários
    lista_de_entradas = search_rod_by_elements(elementos_de_busca, result_format="json")

    if lista_de_entradas:
        print("\n--- Resultados da Busca (JSON) ---")
        # Imprime o JSON completo de forma legível (pode ser longo)
        # print(json.dumps(lista_de_entradas, indent=4, ensure_ascii=False))

        print(f"\n--- Detalhes das {len(lista_de_entradas)} Entradas Encontradas: ---")
        for i, entry_data in enumerate(lista_de_entradas):
            print(f"\nEntrada {i + 1}:")
            if isinstance(entry_data, dict):
                rod_id = entry_data.get("file", "N/A")
                formula = entry_data.get("formula", "N/A").strip().replace("- ", "").replace(" -", "")  # Limpa hífens
                sg = entry_data.get("sg", "N/A")

                authors = entry_data.get("authors", "")
                title = entry_data.get("title", "")
                journal = entry_data.get("journal", "")
                year = str(entry_data.get("year", ""))
                volume = str(entry_data.get("volume", ""))
                firstpage = str(entry_data.get("firstpage", ""))
                lastpage = str(entry_data.get("lastpage", ""))
                doi = entry_data.get("doi", "")

                bib_parts = []
                if authors: bib_parts.append(authors)
                if title: bib_parts.append(f'"{title}"')
                if journal: bib_parts.append(journal)
                if year: bib_parts.append(year)
                page_info = []
                if volume: page_info.append(volume)
                # if issue: page_info.append(f"({issue})") # 'issue' não parece estar nos dados de exemplo
                if firstpage and lastpage:
                    page_info.append(f"{firstpage}-{lastpage}")
                elif firstpage:
                    page_info.append(firstpage)
                if page_info: bib_parts.append(", ".join(page_info))
                if doi: bib_parts.append(f"DOI: {doi}")
                bibliography = ". ".join(filter(None, bib_parts))

                print(f"  ROD ID: {rod_id}")
                print(f"  Fórmula: {formula}")
                print(f"  Grupo Espacial: {sg}")
                print(f"  Bibliografia: {bibliography if bibliography else 'N/A'}")
                # print(f"  Dados Completos da Entrada: {entry_data}") # Descomente para ver todos os campos
            else:
                print(f"  Entrada {i + 1} não está no formato de dicionário esperado.")

        if not lista_de_entradas:
            print("Nenhuma entrada individual encontrada na lista retornada (lista vazia).")

    else:
        print("\nNenhum dado JSON foi retornado ou ocorreu um erro na busca.")

    print("\n--- Teste Concluído ---")
