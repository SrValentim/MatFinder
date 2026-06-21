"""Patches de compatibilidade do Materials Project / emmet-core.

O Materials Project passou a emitir IDs alfanuméricos (ex.: 'mp-aaadipjz'). O
emmet-core fixado (0.84.7rc1) valida MPID com um regex que exige dígitos e faz
int() na parte pós-prefixo, então rejeita os IDs novos com:
    ValidationError: Invalid MPID Format / invalid literal for int().

Aqui relaxamos o validador e a construção do MPID para aceitar alfanuméricos,
SEM trocar a versão do emmet/pymatgen (o que reabriria a 'dependency hell').
Aplicar via apply() antes de qualquer consulta ao MP.
"""

import logging
import re

_applied = False


def apply():
    """Aplica o patch (idempotente)."""
    global _applied
    if _applied:
        return
    try:
        import emmet.core.mpid as _m
        from emmet.core.mpid import MPID

        # 1) Regex usado pelo validador pydantic: aceitar prefixo + alfanumérico.
        _m.mpid_regex = re.compile(r"^([A-Za-z]+-)?[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")

        # 2) MPID.__init__ faz int() na parte pós-prefixo -> falha p/ alfanumérico.
        _orig_init = MPID.__init__

        def _patched_init(self, val):
            try:
                _orig_init(self, val)
            except (ValueError, TypeError):
                s = str(val)
                prefix, sep, rest = s.partition("-")
                self.parts = (prefix, rest) if sep else ("", s)
                self.string = s

        MPID.__init__ = _patched_init

        # 3) __lt__ compara tuplas (str vs int) -> proteger ordenação de IDs mistos.
        _orig_lt = MPID.__lt__

        def _safe_lt(self, other):
            try:
                return _orig_lt(self, other)
            except TypeError:
                return self.string < MPID(other).string

        MPID.__lt__ = _safe_lt

        _applied = True
        logging.info("Patch MPID (IDs alfanumericos do Materials Project) aplicado.")
    except Exception as e:  # pragma: no cover
        logging.warning(f"Nao foi possivel aplicar o patch MPID: {e}")
