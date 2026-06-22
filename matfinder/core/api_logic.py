# api_logic.py
# Módulo para gerir toda a lógica de comunicação com APIs externas.

import logging
import requests
import json
import sys
import os
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from mp_api.client import MPRester
from pymatgen.core.structure import Structure
from pymatgen.io.cif import CifWriter
from matfinder.core.translator import ptr

try:
    import cloudscraper

    CLOUDSRAPER_AVAILABLE = True
except ImportError:
    CLOUDSRAPER_AVAILABLE = False
    logging.warning(ptr("Biblioteca 'cloudscraper' não encontrada. O download do Sci-Hub pode falhar."))

# --- Constantes de API ---
ROD_SEARCH_BASE_URL = "https://solsa.crystallography.net/rod/result"
ROD_ENTRY_BASE_URL = "https://solsa.crystallography.net/rod/"


def query_oqmd(elements_list: list, proxies=None):
    """
    Executa uma query na API do OQMD para obter dados de materiais.
    """
    url_base = "http://oqmd.org/oqmdapi/formationenergy"
    elements_str_param = ",".join(elements_list)
    url = (
        f"{url_base}?fields=name,entry_id,spacegroup,ntypes,band_gap,delta_e,stability"
        f"&filter=element_set=({elements_str_param}) AND ntypes={len(elements_list)}"
    )
    logging.info(f"Query OQMD: {url}")
    try:
        response = requests.get(url, timeout=45, proxies=proxies)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro na requisição OQMD ({url}): {req_err}")
        raise
    except json.JSONDecodeError as json_err:
        logging.error(f"Erro ao decodificar JSON da resposta OQMD ({url}): {json_err}")
        raise


def query_mp(elements_list: list, api_key: str, proxies=None):
    """
    Executa uma query na API do Materials Project.
    """
    if not api_key:
        raise Exception(ptr("API_KEY_MISSING_MP_THREAD"))

    old_proxies_env = {}
    if proxies:
        if "http" in proxies:
            old_proxies_env["HTTP_PROXY"] = os.environ.get("HTTP_PROXY")
            os.environ["HTTP_PROXY"] = proxies["http"]
        if "https" in proxies:
            old_proxies_env["HTTPS_PROXY"] = os.environ.get("HTTPS_PROXY")
            os.environ["HTTPS_PROXY"] = proxies["https"]
    logging.info(
        f"Query Materials Project para elementos: {elements_list} "
        f"com proxies: {proxies if proxies else 'Nenhum'}"
    )
    try:
        with MPRester(api_key=api_key) as mpr:
            docs = mpr.materials.summary.search(
                elements=elements_list,
                fields=[
                    "formula_pretty", "material_id", "symmetry", "band_gap",
                    "formation_energy_per_atom", "energy_above_hull",
                    "nelements", "database_IDs",
                ],
            )
            filtered_docs_data = []
            for doc in docs:
                # A lógica de filtragem permanece na UI, mas a busca é aqui.
                # A UI precisa de todos os elementos para filtrar corretamente.
                # if len(doc.elements) == len(elements_list):
                symmetry_data = doc.symmetry.symbol if doc.symmetry else None
                crystal_system_value = (
                    doc.symmetry.crystal_system.value
                    if doc.symmetry and hasattr(doc.symmetry, "crystal_system") and doc.symmetry.crystal_system
                    else None
                )
                db_ids_processed = {}
                if doc.database_IDs:
                    if hasattr(doc.database_IDs, 'model_dump'):
                        db_ids_processed = doc.database_IDs.model_dump(exclude_none=True)
                    elif isinstance(doc.database_IDs, dict):
                        db_ids_processed = doc.database_IDs
                    else:
                        try:
                            db_ids_processed = doc.database_IDs.dict(exclude_none=True)
                        except AttributeError:
                            logging.warning(f"Não foi possível processar database_IDs para {doc.material_id}")

                doc_data = {
                    "formula_pretty": doc.formula_pretty,
                    "material_id": str(doc.material_id),
                    "elements": [el.symbol for el in doc.elements],  # Adicionado para filtragem posterior
                    "symmetry_symbol": symmetry_data,
                    "crystal_system": crystal_system_value,
                    "band_gap": doc.band_gap,
                    "formation_energy_per_atom": doc.formation_energy_per_atom,
                    "energy_above_hull": doc.energy_above_hull,
                    "database_IDs": db_ids_processed,
                }
                filtered_docs_data.append(doc_data)
            return filtered_docs_data
    except Exception as exc:
        logging.error(f"Erro na query Materials Project: {exc}")
        raise
    finally:
        # Restaurar variáveis de ambiente de proxy
        if "HTTP_PROXY" in old_proxies_env:
            if old_proxies_env["HTTP_PROXY"] is None:
                os.environ.pop("HTTP_PROXY", None)
            else:
                os.environ["HTTP_PROXY"] = old_proxies_env["HTTP_PROXY"]
        elif proxies and "http" in proxies:
            os.environ.pop("HTTP_PROXY", None)

        if "HTTPS_PROXY" in old_proxies_env:
            if old_proxies_env["HTTPS_PROXY"] is None:
                os.environ.pop("HTTPS_PROXY", None)
            else:
                os.environ["HTTPS_PROXY"] = old_proxies_env["HTTPS_PROXY"]
        elif proxies and "https" in proxies:
            os.environ.pop("HTTPS_PROXY", None)


def query_rod(elements_list: list, proxies=None):
    """
    Executa uma query na API da Raman Open Database (ROD).
    """
    if not elements_list:
        logging.warning(ptr("ROD API: A lista de elementos não pode ser vazia."))
        return []

    params = {}
    for i, el_symbol in enumerate(elements_list):
        if i < 8:
            params[f"el{i + 1}"] = el_symbol.strip().capitalize()
        else:
            logging.warning(f"ROD API: Máximo de 8 elementos. Ignorando extras: {elements_list[8:]}")
            break
    params["format"] = "json"

    logging.info(f"ROD API: Buscando por elementos: {', '.join(elements_list)}")
    try:
        response = requests.get(ROD_SEARCH_BASE_URL, params=params, timeout=45, proxies=proxies)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as req_err:
        logging.error(f"ROD API: Erro de requisição: {req_err}")
        raise
    except json.JSONDecodeError as json_err:
        logging.error(f"ROD API: Erro ao decodificar JSON: {json_err}")
        raise


def fetch_cif_data_mp(material_id: str, formula_pretty: str, api_key: str, proxies=None):
    """
    Busca os dados de um ficheiro CIF do Materials Project.
    """
    if not api_key:
        raise Exception(ptr("API_KEY_MISSING_MP_THREAD"))

    old_proxies_env = {}
    if proxies:
        if "http" in proxies: old_proxies_env["HTTP_PROXY"] = os.environ.get("HTTP_PROXY"); os.environ["HTTP_PROXY"] = \
        proxies["http"]
        if "https" in proxies: old_proxies_env["HTTPS_PROXY"] = os.environ.get("HTTPS_PROXY"); os.environ[
            "HTTPS_PROXY"] = proxies["https"]

    try:
        with MPRester(api_key=api_key) as mpr:
            structure = mpr.get_structure_by_material_id(material_id, conventional_unit_cell=True)
            if structure:
                try:
                    writer = CifWriter(structure, symprec=0.1, significant_figures=8)
                    cif_string = str(writer)
                except Exception as e:
                    logging.warning(f"CifWriter com simetria falhou: {e}. Usando fallback P1.")
                    cif_string = structure.to(fmt="cif")
                safe_formula = "".join(c if c.isalnum() else "_" for c in formula_pretty)
                suggested_filename = f"MP_{material_id}_{safe_formula}.cif"
                return cif_string, suggested_filename
            else:
                raise Exception(ptr("Estrutura não encontrada para material_id (MP): {}").format(material_id))
    except Exception as e:
        logging.exception(f"Erro ao buscar CIF do MP para ID {material_id}:")
        raise
    finally:
        # Restaurar proxies
        if "HTTP_PROXY" in old_proxies_env:
            if old_proxies_env["HTTP_PROXY"] is None:
                os.environ.pop("HTTP_PROXY", None)
            else:
                os.environ["HTTP_PROXY"] = old_proxies_env["HTTP_PROXY"]
        elif proxies and "http" in proxies:
            os.environ.pop("HTTP_PROXY", None)
        if "HTTPS_PROXY" in old_proxies_env:
            if old_proxies_env["HTTPS_PROXY"] is None:
                os.environ.pop("HTTPS_PROXY", None)
            else:
                os.environ["HTTPS_PROXY"] = old_proxies_env["HTTPS_PROXY"]
        elif proxies and "https" in proxies:
            os.environ.pop("HTTPS_PROXY", None)


def fetch_rod_file_content(rod_id: str, proxies=None):
    """
    Busca o conteúdo de um ficheiro .rod da ROD.
    """
    if not rod_id or not rod_id.isdigit():
        logging.error(f"ROD File Fetch: ID da ROD '{rod_id}' inválido.")
        raise ValueError(ptr("ID da ROD '{}' inválido para busca de ficheiro.").format(rod_id))

    url = f"{ROD_ENTRY_BASE_URL}{rod_id}.rod"
    logging.info(f"ROD File Fetch: Buscando conteúdo de {url} ...")
    try:
        response = requests.get(url, timeout=30, proxies=proxies)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as req_err:
        logging.error(f"ROD File Fetch: Erro ao buscar ficheiro .rod para {rod_id}: {req_err}")
        raise


def fetch_scihub_pdf(doi: str, scihub_base_url: str, proxies=None):
    """
    Tenta descarregar um PDF do Sci-Hub usando um DOI.
    """
    if not CLOUDSRAPER_AVAILABLE:
        raise Exception(ptr("Biblioteca 'cloudscraper' não instalada. Execute 'pip install cloudscraper'."))

    scraper = cloudscraper.create_scraper()
    scihub_domains = list(set([scihub_base_url, "https://sci-hub.se/", "https://sci-hub.st/", "https://sci-hub.ru/"]))
    pdf_content_bytes = None
    final_pdf_url_used = None

    for domain_idx, domain in enumerate(scihub_domains):
        if pdf_content_bytes: break
        target_page_url = f"{domain.rstrip('/')}/{doi}"
        logging.info(f"Tentativa Sci-Hub {domain_idx + 1}/{len(scihub_domains)}: Acessando {target_page_url}")
        try:
            page_response = scraper.get(target_page_url, timeout=30, proxies=proxies)
            page_response.raise_for_status()
            content_type = page_response.headers.get("Content-Type", "").lower()

            if "application/pdf" in content_type:
                pdf_content_bytes = page_response.content
                final_pdf_url_used = target_page_url
                break
            else:
                soup = BeautifulSoup(page_response.text, "html.parser")
                pdf_url_found_in_html = None
                selectors = [("iframe#pdf", "src"), ("embed#pdf", "src"), ('a[onclick*=".pdf"]', "onclick")]
                for tag_selector, attr_name in selectors:
                    element = soup.select_one(tag_selector)
                    if element:
                        if attr_name == "onclick" and "location.href='" in element[attr_name]:
                            pdf_url_found_in_html = element[attr_name].split("location.href='")[1].split("'")[0]
                            break
                        elif element.get(attr_name):
                            pdf_url_found_in_html = element.get(attr_name)
                            break
                if pdf_url_found_in_html:
                    if pdf_url_found_in_html.startswith("//"):
                        pdf_url_found_in_html = "https:" + pdf_url_found_in_html
                    elif not pdf_url_found_in_html.startswith(("http://", "https://")):
                        pdf_url_found_in_html = urljoin(target_page_url, pdf_url_found_in_html)

                    if pdf_url_found_in_html == target_page_url: continue

                    logging.info(f"  Link PDF encontrado no HTML: {pdf_url_found_in_html}")
                    pdf_response = scraper.get(pdf_url_found_in_html, stream=True, timeout=60, proxies=proxies)
                    pdf_response.raise_for_status()
                    if "application/pdf" in pdf_response.headers.get("Content-Type", "").lower():
                        pdf_content_bytes = pdf_response.content
                        final_pdf_url_used = pdf_url_found_in_html
                        break
        except requests.exceptions.RequestException as req_err:
            logging.warning(f"Erro de requisição para {target_page_url}: {req_err}.")
        except Exception as e_parse:
            logging.error(f"Erro ao processar HTML de {target_page_url}: {e_parse}.")

    if pdf_content_bytes:
        logging.info(f"PDF descarregado com sucesso de {final_pdf_url_used or 'URL desconhecida'}")
        suggested_filename = doi.replace("/", "_").replace(":", "_") + ".pdf"
        return pdf_content_bytes, suggested_filename
    else:
        raise Exception(ptr("Não foi possível encontrar ou descarregar o PDF após todas as tentativas."))
