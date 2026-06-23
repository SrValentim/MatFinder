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


# Email de contato para a "polite pool" do OpenAlex e exigido pela API do Unpaywall.
# E o e-mail publico do mantenedor (ja consta em matfinder/__init__.py).
OA_CONTACT_EMAIL = "Raynnervalentim@hotmail.com"


def _normalize_doi(doi: str) -> str:
    d = (doi or "").strip()
    for pref in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/",
                 "doi.org/", "doi:", "DOI:"):
        if d.lower().startswith(pref.lower()):
            d = d[len(pref):]
    return d.strip().strip("/")


def _download_pdf(url, proxies=None, timeout=60):
    """Baixa a URL e devolve os bytes se for um PDF de verdade; senao None."""
    headers = {"User-Agent": f"MatFinder (mailto:{OA_CONTACT_EMAIL})"}
    resp = requests.get(url, headers=headers, timeout=timeout, proxies=proxies,
                        allow_redirects=True)
    resp.raise_for_status()
    content = resp.content
    ctype = resp.headers.get("Content-Type", "").lower()
    if "application/pdf" in ctype or content[:5] == b"%PDF-":
        return content
    return None


def fetch_oa_pdf(doi: str, proxies=None):
    """Procura a versao de ACESSO ABERTO (legal) de um artigo pelo DOI e baixa o PDF.

    Usa OpenAlex (que agrega os locais de OA do Unpaywall) e, como reforco, a API do
    Unpaywall. Retorna (pdf_bytes, suggested_filename) ou levanta Exception com mensagem
    clara se nao houver versao de acesso aberto disponivel. Usa apenas fontes legais
    de acesso aberto.
    """
    doi_clean = _normalize_doi(doi)
    headers = {"User-Agent": f"MatFinder (mailto:{OA_CONTACT_EMAIL})"}
    candidates = []

    # 1) OpenAlex - inclui os locais de OA do Unpaywall, sem exigir e-mail.
    try:
        r = requests.get(
            f"https://api.openalex.org/works/doi:{doi_clean}",
            params={"mailto": OA_CONTACT_EMAIL},
            headers=headers, timeout=30, proxies=proxies,
        )
        if r.status_code == 200:
            w = r.json()
            locs = [w.get("best_oa_location"), w.get("primary_location")]
            locs += (w.get("locations") or [])
            for loc in locs:
                if isinstance(loc, dict) and loc.get("pdf_url"):
                    candidates.append(loc["pdf_url"])
            oa_url = (w.get("open_access") or {}).get("oa_url")
            if oa_url:
                candidates.append(oa_url)
    except Exception as e:
        logging.warning(f"OpenAlex falhou para {doi_clean}: {e}")

    # 2) Unpaywall - reforco.
    try:
        r = requests.get(
            f"https://api.unpaywall.org/v2/{doi_clean}",
            params={"email": OA_CONTACT_EMAIL},
            headers=headers, timeout=30, proxies=proxies,
        )
        if r.status_code == 200:
            d = r.json()
            for loc in [d.get("best_oa_location")] + (d.get("oa_locations") or []):
                if isinstance(loc, dict):
                    for u in (loc.get("url_for_pdf"), loc.get("url")):
                        if u:
                            candidates.append(u)
    except Exception as e:
        logging.warning(f"Unpaywall falhou para {doi_clean}: {e}")

    # Baixa o primeiro candidato que for realmente um PDF.
    seen = set()
    for url in candidates:
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            pdf = _download_pdf(url, proxies=proxies)
            if pdf:
                logging.info(f"PDF de acesso aberto obtido de: {url}")
                fname = doi_clean.replace("/", "_").replace(":", "_") + ".pdf"
                return pdf, fname
        except Exception as e:
            logging.warning(f"Falha ao baixar PDF de {url}: {e}")

    raise Exception(ptr("Nenhuma versao de acesso aberto (Unpaywall/OpenAlex) foi encontrada para este DOI."))
