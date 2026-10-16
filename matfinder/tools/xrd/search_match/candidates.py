# -*- coding: utf-8 -*-
"""Candidatos de fase para o search-match: filtro de elementos, COD e Materials Project.

- ``ElementFilter``: elementos obrigatórios, possíveis e proibidos. Em sistema
  fechado (padrão), o candidato só pode conter elementos marcados.
- ``Candidate``: uma estrutura candidata (metadados, CIF e resultado da pontuação).
- ``search_cod`` / ``fetch_cod_cifs``: consulta e download no COD, com novas
  tentativas, caminho alternativo por HTTP (o servidor do COD derruba conexões
  TLS com frequência) e cache local.
- ``search_mp``: consulta ao Materials Project (estruturas já vêm na resposta).
- ``group_duplicates``: junta entradas da mesma fase (mesma fórmula, grupo
  espacial e célula), mantendo a de maior pontuação como representante.

O cache fica em %LOCALAPPDATA%/MatFinder/search_match_cache (ou na pasta da
variável MATFINDER_CACHE_DIR), fora do repositório e da pasta do programa.
"""

import hashlib
import itertools
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

COD_HOSTS = ("https://www.crystallography.net", "http://www.crystallography.net")
CACHE_TTL_DAYS = 7
MAX_COD_QUERIES = 16          # consultas exatas por sistema químico numa busca
OPEN_SYSTEM_EXTRA_ELEMENTS = 2  # sistema aberto: até 2 elementos além dos obrigatórios
MAX_CLOSED_SYSTEM_ELEMENTS = 10
_FORMULA_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")


class SearchCancelled(Exception):
    """A busca de candidatos foi cancelada pelo usuário."""


# =============================================================================
# Filtro de elementos
# =============================================================================

@dataclass
class ElementFilter:
    """Restrição de elementos da busca de candidatos.

    required: o candidato precisa conter todos.
    possible: o candidato pode conter.
    forbidden: o candidato não pode conter nenhum.
    allow_others: se False (sistema fechado), só elementos obrigatórios ou possíveis.
    """

    required: list = field(default_factory=list)
    possible: list = field(default_factory=list)
    forbidden: list = field(default_factory=list)
    allow_others: bool = False

    def __post_init__(self):
        self.required = sorted(set(self.required))
        self.possible = sorted(set(self.possible) - set(self.required))
        self.forbidden = sorted(set(self.forbidden))

    def validate(self):
        """Mensagem de erro (em português, para ptr) ou None se o filtro é válido."""
        if not self.required:
            return "Marque pelo menos um elemento como obrigatório."
        if set(self.forbidden) & (set(self.required) | set(self.possible)):
            return "Um elemento não pode ser obrigatório ou possível e proibido ao mesmo tempo."
        if len(self.required) > 8:
            return "O COD aceita no máximo 8 elementos obrigatórios."
        if not self.allow_others and len(self.required) + len(self.possible) > MAX_CLOSED_SYSTEM_ELEMENTS:
            return "Use no máximo 10 elementos entre obrigatórios e possíveis."
        return None

    def allows(self, elements):
        """True se um composto com estes elementos passa no filtro."""
        present = set(elements)
        if not set(self.required) <= present:
            return False
        if present & set(self.forbidden):
            return False
        if not self.allow_others and not present <= (set(self.required) | set(self.possible)):
            return False
        return True

    def chemsys_list(self):
        """Sistemas químicos (ex.: "Ce-O") entre os obrigatórios e obrigatórios + possíveis."""
        out = []
        for k in range(len(self.possible) + 1):
            for extra in itertools.combinations(self.possible, k):
                out.append("-".join(sorted(set(self.required) | set(extra))))
        return sorted(set(out))

    def is_empty(self):
        return not (self.required or self.possible or self.forbidden)

    def to_dict(self):
        return {"required": list(self.required), "possible": list(self.possible),
                "forbidden": list(self.forbidden), "allow_others": bool(self.allow_others)}

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(required=list(data.get("required", [])), possible=list(data.get("possible", [])),
                   forbidden=list(data.get("forbidden", [])), allow_others=bool(data.get("allow_others", False)))


# =============================================================================
# Candidato
# =============================================================================

@dataclass
class Candidate:
    """Uma estrutura candidata, com metadados da fonte e o resultado da pontuação."""

    source: str                      # "COD" ou "MP"
    source_id: str
    formula: str
    elements: tuple = ()
    spacegroup: str = ""
    sg_number: int = 0
    cell: tuple = ()                 # (a, b, c, alpha, beta, gamma)
    mineral: str = ""
    year: str = ""
    e_above_hull: float = None
    theoretical: bool = None
    duplicate_of: str = ""
    cif: str = None
    meta: dict = field(default_factory=dict)
    # resultado da pontuação (preenchido por scoring.score_candidate)
    score: float = 0.0
    subscores: dict = field(default_factory=dict)
    match: object = None
    group_members: list = field(default_factory=list)
    error: str = ""
    reference: object = None         # padrão de referência simulado (para reavaliar sem simular de novo)
    peak_score: float = 0.0          # score só pela lista de picos
    profile_explained: float = None  # fração do perfil explicada (0-1), quando calculada

    @property
    def key(self):
        return f"{self.source}:{self.source_id}"

    @property
    def url(self):
        if self.source == "COD":
            return f"https://www.crystallography.net/cod/{self.source_id}.html"
        return f"https://next-gen.materialsproject.org/materials/{self.source_id}"

    @property
    def label(self):
        sg = f" {self.spacegroup}" if self.spacegroup else ""
        return f"{self.formula}{sg} ({self.source} {self.source_id})"

    def file_name(self):
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{self.formula}_{self.spacegroup}_{self.source}-{self.source_id}")
        return safe.strip("_") + ".cif"

    def summary(self):
        """Dicionário curto e serializável (para tabela/CSV/projeto)."""
        return {"source": self.source, "source_id": self.source_id, "formula": self.formula,
                "spacegroup": self.spacegroup, "score": round(float(self.score), 2),
                "subscores": {k: round(float(v), 4) for k, v in self.subscores.items()},
                "group_size": 1 + len(self.group_members)}


# =============================================================================
# Utilidades
# =============================================================================

def formula_elements(formula):
    """Elementos de uma fórmula (ex.: "- Ce2 O3 -" -> ["Ce", "O"])."""
    return sorted({m.group(1) for m in _FORMULA_TOKEN.finditer(formula or "")})


def pretty_formula(formula):
    """Fórmula reduzida legível (ex.: "- Ce O2 -" -> "CeO2"; "Nb16.8 O42" -> "Nb2O5").

    Células com ocupação parcial dão quantidades fracionárias; quando elas são
    múltiplos exatos de números pequenos, a fórmula é reduzida a inteiros.
    """
    text = (formula or "").replace("-", " ").strip()
    compact = "".join(text.split())
    try:
        from pymatgen.core import Composition
        comp = Composition(compact)
    except Exception:  # noqa: BLE001 - fórmulas do COD às vezes não são parseáveis
        return compact or "?"
    amounts = [comp[el] for el in comp.elements]
    if amounts and any(abs(a - round(a)) > 1e-6 for a in amounts):
        smallest = min(amounts)
        for mult in range(1, 13):
            scaled = [a / smallest * mult for a in amounts]
            if all(abs(v - round(v)) <= 0.005 for v in scaled):  # só múltiplos quase exatos
                ints = {el: int(round(a / smallest * mult)) for el, a in zip(comp.elements, amounts)}
                return Composition(ints).reduced_formula
    return comp.reduced_formula


def clean_spacegroup(symbol):
    """Símbolo compacto: tira espaços e os "1" do símbolo completo (P 1 21/c 1 -> P21/c)."""
    tokens = str(symbol or "").split()
    if len(tokens) == 4 and tokens.count("1") >= 1:
        tokens = [tokens[0]] + [tk for tk in tokens[1:] if tk != "1"]
    return "".join(tokens)


def cache_dir(*parts):
    base = os.environ.get("MATFINDER_CACHE_DIR")
    if not base:
        root = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache")
        base = os.path.join(root, "MatFinder", "search_match_cache")
    path = os.path.join(base, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def _query_cache_path(kind, params):
    digest = hashlib.sha1(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()[:20]
    return os.path.join(cache_dir("queries"), f"{kind}_{digest}.json")


def _read_query_cache(kind, params):
    path = _query_cache_path(kind, params)
    try:
        if time.time() - os.path.getmtime(path) > CACHE_TTL_DAYS * 86400:
            return None
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _write_query_cache(kind, params, rows):
    try:
        with open(_query_cache_path(kind, params), "w", encoding="utf-8") as fh:
            json.dump(rows, fh)
    except OSError as exc:
        logger.debug(f"Cache de consulta não gravado: {exc}")


def describe_error(exc):
    """Texto de um erro (algumas exceções de rede têm mensagem vazia)."""
    text = str(exc).strip()
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status:
        text = f"HTTP {status}" + (f": {text}" if text else "")
    return text or type(exc).__name__


def _check_cancel(cancel):
    if cancel and cancel():
        raise SearchCancelled()


def _http_get(path, params=None, timeout=60, cancel=None, retries=2, session=None):
    """GET no COD com novas tentativas; se o HTTPS falhar, tenta por HTTP."""
    import requests

    getter = session or requests
    last = None
    for host in COD_HOSTS:
        for attempt in range(retries):
            _check_cancel(cancel)
            try:
                response = getter.get(host + path, params=params, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if 400 <= status < 500:
                    raise  # erro definitivo (ex.: CIF inexistente): não adianta repetir
                last = exc
            except requests.RequestException as exc:
                last = exc
            time.sleep(min(2.0, 0.5 * (attempt + 1)))
    raise ConnectionError(f"COD indisponível: {last}")


# =============================================================================
# COD
# =============================================================================

def cod_query_plans(flt):
    """Consultas ao COD para este filtro.

    Sistema fechado: uma consulta EXATA por sistema químico permitido (todos os
    elementos do sistema e nenhum outro). Uma consulta ampla, como "tudo que tem
    oxigênio e até 3 elementos", traz dezenas de milhares de entradas e o servidor
    do COD corta a resposta. Sistema aberto: os obrigatórios, sem os proibidos, com
    até OPEN_SYSTEM_EXTRA_ELEMENTS elementos a mais.
    """
    if flt.allow_others:
        params = {"format": "json", "strictmin": len(flt.required),
                  "strictmax": len(flt.required) + OPEN_SYSTEM_EXTRA_ELEMENTS}
        for i, element in enumerate(flt.required[:8]):
            params[f"el{i + 1}"] = element
        for i, element in enumerate(flt.forbidden[:8]):
            params[f"nel{i + 1}"] = element
        return [params]
    plans = []
    for system in flt.chemsys_list():
        elements = system.split("-")
        if len(elements) > 8:
            continue  # o COD aceita até 8 elementos por consulta
        params = {"format": "json", "strictmin": len(elements), "strictmax": len(elements)}
        for i, element in enumerate(elements):
            params[f"el{i + 1}"] = element
        plans.append(params)
    return plans[:MAX_COD_QUERIES]


def _cod_cell(row):
    try:
        return tuple(float(row[k]) for k in ("a", "b", "c", "alpha", "beta", "gamma"))
    except (KeyError, TypeError, ValueError):
        return ()


def search_cod(flt, cancel=None, use_cache=True, session=None, errors=None):
    """Candidatos do COD (só entradas com coordenadas atômicas e que passam no filtro).

    Consultas que falham entram em ``errors`` (lista) e a busca segue com as
    outras; só levanta erro se todas falharem.
    """
    plans = cod_query_plans(flt)
    rows, failures, seen = [], [], set()
    for params in plans:
        _check_cancel(cancel)
        part = _read_query_cache("cod", params) if use_cache else None
        if part is None:
            try:
                response = _http_get("/cod/result", params=params, timeout=120, cancel=cancel, session=session)
                part = response.json() if response.content.strip() else []
            except SearchCancelled:
                raise
            except Exception as exc:  # noqa: BLE001 - as outras consultas ainda podem responder
                failures.append(f"{_system_of(params)}: {describe_error(exc)}")
                continue
            if not isinstance(part, list):
                part = []
            _write_query_cache("cod", params, part)
        for row in part:
            key = str(row.get("file"))
            if key not in seen:
                seen.add(key)
                rows.append(row)
    if failures:
        if len(failures) == len(plans):
            raise ConnectionError("; ".join(failures))
        if errors is not None:
            errors.extend(failures)
    out = []
    for row in rows:
        if "has coordinates" not in str(row.get("flags") or ""):
            continue
        if row.get("onhold"):
            continue
        elements = formula_elements(row.get("formula"))
        if not elements or not flt.allows(elements):
            continue
        try:
            sg_number = int(row.get("sgNumber") or 0)
        except (TypeError, ValueError):
            sg_number = 0
        out.append(Candidate(
            source="COD", source_id=str(row.get("file")), formula=pretty_formula(row.get("formula")),
            elements=tuple(elements), spacegroup=clean_spacegroup(row.get("sg")), sg_number=sg_number,
            cell=_cod_cell(row), mineral=str(row.get("mineral") or row.get("commonname") or ""),
            year=str(row.get("year") or ""), duplicate_of=str(row.get("duplicateof") or ""),
            meta={"chemname": row.get("chemname"), "doi": row.get("doi"), "title": row.get("title")},
        ))
    return out


def _system_of(params):
    return "-".join(params[k] for k in sorted(params) if k.startswith("el") and not k.startswith("nel"))


def fetch_cod_cif(cod_id, cancel=None, session=None):
    """CIF de uma entrada do COD (do cache local, quando houver)."""
    path = os.path.join(cache_dir("cod"), f"{cod_id}.cif")
    try:
        if os.path.getsize(path) > 0:
            with open(path, encoding="utf-8", errors="replace") as fh:
                return fh.read()
    except OSError:
        pass
    response = _http_get(f"/cod/{cod_id}.cif", timeout=60, cancel=cancel, session=session)
    text = response.text
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as exc:
        logger.debug(f"CIF do COD não gravado no cache: {exc}")
    return text


def fetch_cod_cifs(candidates, progress=None, cancel=None, workers=6, session=None):
    """Baixa em paralelo os CIFs dos candidatos do COD que ainda não têm CIF."""
    pending = [c for c in candidates if c.source == "COD" and not c.cif]
    if not pending:
        return
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_cod_cif, c.source_id, cancel, session): c for c in pending}
        for future in as_completed(futures):
            cand = futures[future]
            try:
                cand.cif = future.result()
            except SearchCancelled:
                for other in futures:
                    other.cancel()
                raise
            except Exception as exc:  # noqa: BLE001 - um CIF ruim não derruba a busca
                cand.error = describe_error(exc)
            done += 1
            if progress:
                progress(done / len(pending))
            _check_cancel(cancel)


# =============================================================================
# Materials Project
# =============================================================================

MP_FIELDS = ["material_id", "formula_pretty", "elements", "symmetry", "energy_above_hull",
             "theoretical", "database_IDs", "structure"]


def find_mp_api_key():
    """Chave da API do Materials Project, nos mesmos lugares em que o MatFinder a guarda."""
    key = os.environ.get("MP_API_KEY", "").strip()
    if key:
        return key
    here = os.path.dirname(os.path.abspath(__file__))
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    places = [os.path.join(os.getcwd(), "config.txt")]
    if os.environ.get("LOCALAPPDATA"):
        places.append(os.path.join(os.environ["LOCALAPPDATA"], "MatFinder", "config.txt"))
    places.append(os.path.join(package_root, "assets", "config", "config.txt"))
    for path in places:
        try:
            with open(path, encoding="utf-8") as fh:
                key = fh.readline().strip()
        except OSError:
            continue
        if len(key) >= 16:
            return key
    return None


def structure_to_cif(structure):
    """CIF da célula convencional (como o MatFinder já exporta do MP); P1 como reserva."""
    from pymatgen.io.cif import CifWriter
    try:
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        conventional = SpacegroupAnalyzer(structure, symprec=0.1).get_conventional_standard_structure()
        return str(CifWriter(conventional, symprec=0.1))
    except Exception:  # noqa: BLE001
        return str(CifWriter(structure))


def mp_query_kwargs(flt, only_experimental=True, max_e_above_hull=0.2):
    kwargs = {}
    if flt.allow_others:
        kwargs["elements"] = list(flt.required)
        if flt.forbidden:
            kwargs["exclude_elements"] = list(flt.forbidden)
    else:
        kwargs["chemsys"] = flt.chemsys_list()
    if only_experimental:
        kwargs["theoretical"] = False
    if max_e_above_hull is not None:
        kwargs["energy_above_hull"] = (0.0, float(max_e_above_hull))
    return kwargs


def _open_rester(api_key):
    from matfinder import _mp_compat
    _mp_compat.apply()
    from mp_api.client import MPRester
    try:
        return MPRester(api_key, mute_progress_bars=True)
    except TypeError:
        return MPRester(api_key)


def search_mp(flt, api_key, only_experimental=True, max_e_above_hull=0.2, cancel=None,
              use_cache=True, rester_factory=None):
    """Candidatos do Materials Project (com o CIF já incluído)."""
    kwargs = mp_query_kwargs(flt, only_experimental, max_e_above_hull)
    rows = _read_query_cache("mp", kwargs) if use_cache else None
    if rows is None:
        _check_cancel(cancel)
        factory = rester_factory or (lambda: _open_rester(api_key))
        with factory() as rester:
            docs = rester.materials.summary.search(fields=MP_FIELDS, **kwargs)
        rows = []
        for doc in docs:
            _check_cancel(cancel)
            try:
                cif = structure_to_cif(doc.structure)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"Estrutura do MP sem CIF ({doc.material_id}): {exc}")
                continue
            symmetry = getattr(doc, "symmetry", None)
            ids = getattr(doc, "database_IDs", None) or {}
            rows.append({
                "material_id": str(doc.material_id), "formula": str(doc.formula_pretty),
                "elements": sorted(str(e) for e in (doc.elements or [])),
                "spacegroup": str(getattr(symmetry, "symbol", "") or ""),
                "sg_number": int(getattr(symmetry, "number", 0) or 0),
                "e_above_hull": None if doc.energy_above_hull is None else float(doc.energy_above_hull),
                "theoretical": bool(doc.theoretical) if doc.theoretical is not None else None,
                "icsd": [str(x) for x in (ids.get("icsd") or [])] if isinstance(ids, dict) else [],
                "cif": cif,
            })
        _write_query_cache("mp", kwargs, rows)
    out = []
    for row in rows:
        if not flt.allows(row["elements"]):
            continue
        out.append(Candidate(
            source="MP", source_id=row["material_id"], formula=row["formula"], elements=tuple(row["elements"]),
            spacegroup=clean_spacegroup(row["spacegroup"]), sg_number=row["sg_number"],
            e_above_hull=row["e_above_hull"], theoretical=row["theoretical"], cif=row["cif"],
            meta={"icsd": row.get("icsd", [])},
        ))
    return out


# =============================================================================
# Duplicatas
# =============================================================================

def _same_phase(a, b, tolerance=0.02):
    if pretty_formula(a.formula) != pretty_formula(b.formula):
        return False
    if a.sg_number and b.sg_number and a.sg_number != b.sg_number:
        return False
    if a.cell and b.cell:
        for x, y in zip(sorted(a.cell[:3]), sorted(b.cell[:3])):
            if abs(x - y) > tolerance * max(x, y):
                return False
    return True


def group_duplicates(candidates):
    """Agrupa entradas da mesma fase; devolve os representantes (o 1º de cada grupo).

    A lista deve vir ordenada pela pontuação: o representante é o melhor do grupo.
    """
    groups = []
    for cand in candidates:
        for group in groups:
            if _same_phase(group[0], cand):
                group.append(cand)
                break
        else:
            groups.append([cand])
    for group in groups:
        group[0].group_members = [c.key for c in group[1:]]
    return [g[0] for g in groups]
