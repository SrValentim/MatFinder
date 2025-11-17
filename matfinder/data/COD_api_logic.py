import requests
import json
from urllib.parse import urlencode

COD_SEARCH_BASE_URL = "https://www.crystallography.net/cod/result"
COD_ENTRY_BASE_URL = "https://www.crystallography.net/cod/"


def search_cod_by_elements(elements_list: list, result_format: str = "json", strict_elements: bool = True):
    if not elements_list:
        print("COD API: Lista de elementos vazia.")
        return None

    params = {}
    for i, el_symbol in enumerate(elements_list):
        if i < 8:  # API supports up to el8
            params[f"el{i + 1}"] = el_symbol.strip().capitalize()
        else:
            print(f"COD API: Max 8 elements supported. Ignoring extras: {elements_list[8:]}")
            break

    if strict_elements:
        params["strictmin"] = len(elements_list)
        params["strictmax"] = len(elements_list)

    params["format"] = result_format

    query_string = urlencode(params)
    full_url = f"{COD_SEARCH_BASE_URL}?{query_string}"

    print(f"COD API: Buscando por elementos: {', '.join(elements_list)} (Strict: {strict_elements})")
    print(f"COD API: URL da requisição: {full_url}")

    try:
        response = requests.get(COD_SEARCH_BASE_URL, params=params, timeout=45)
        response.raise_for_status()

        if result_format == "json":
            try:
                return response.json()
            except json.JSONDecodeError as json_err:
                print(f"COD API: Erro ao decodificar JSON: {json_err}")
                print(f"COD API: Status Code: {response.status_code}, Resposta: {response.text[:200]}")
                return None
        return response.text  # For lst, cif, etc.

    except requests.exceptions.RequestException as req_err:
        print(f"COD API: Erro de requisição: {req_err}")
    return None


def get_cod_cif_data(cod_id: str):
    if not cod_id or not cod_id.isdigit():
        print(f"COD API: COD ID '{cod_id}' inválido.")
        return None

    url = f"{COD_ENTRY_BASE_URL}{cod_id}.cif"
    print(f"COD API: Buscando CIF para COD ID: {cod_id} em {url} ...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text  # CIF content
    except requests.exceptions.RequestException as req_err:
        print(f"COD API: Erro ao buscar CIF para {cod_id}: {req_err}")
    return None