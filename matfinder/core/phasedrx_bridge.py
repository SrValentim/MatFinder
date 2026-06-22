"""Ponte (IPC) entre o MatFinder e o PhaseDRX para "Exportar CIF para PhaseDRX".

Fluxos suportados:
  - PhaseDRX aberto DENTRO do MatFinder (mesmo processo)  -> o app_main usa a
    referência direta (self.phasedrx_window_ref).
  - PhaseDRX aberto SEPARADO (PhaseDRX.exe ou --phasedrx, outro processo) e o
    usuário abre o MatFinder depois -> o MatFinder detecta o PhaseDRX via este
    bridge (QLocalServer/QLocalSocket) e envia o CIF por um named pipe local.

Qualquer instância do PhaseDRX (no MatFinder ou standalone) sobe um servidor.
A primeira a subir é dona do pipe; o MatFinder se conecta a ela. Sem rede, sem
dependências externas — só Qt local sockets.
"""

import json
import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "MatFinder_PhaseDRX_Bridge_v1"
_TIMEOUT_MS = 1500


class PhaseDRXBridgeServer(QObject):
    """Escuta um named pipe local; ao receber um CIF, emite cif_received.

    Uso: instanciar dentro do PhaseDRXTool e ligar cif_received a
    load_cif_from_data. Roda no thread da UI (event loop do Qt), então é seguro
    chamar a UI a partir do sinal."""

    cif_received = Signal(str, str)  # (cif_string, filename)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server = None
        try:
            # remove pipe órfão de um processo que morreu sem fechar
            QLocalServer.removeServer(SERVER_NAME)
            self._server = QLocalServer(self)
            if self._server.listen(SERVER_NAME):
                self._server.newConnection.connect(self._on_new_connection)
                logging.info("Bridge PhaseDRX: servidor ativo (%s).", SERVER_NAME)
            else:
                logging.info("Bridge PhaseDRX: nao foi possivel escutar (%s): %s",
                             SERVER_NAME, self._server.errorString())
                self._server = None
        except Exception:
            logging.exception("Bridge PhaseDRX: falha ao iniciar o servidor.")
            self._server = None

    def _on_new_connection(self):
        sock = self._server.nextPendingConnection()
        if sock is None:
            return
        sock.readyRead.connect(lambda s=sock: self._read(s))
        sock.disconnected.connect(sock.deleteLater)

    def _read(self, sock):
        try:
            raw = bytes(sock.readAll().data())
            if not raw:
                return
            payload = json.loads(raw.decode("utf-8"))
            cif = payload.get("cif", "")
            fname = payload.get("filename", "imported.cif")
            if cif:
                self.cif_received.emit(cif, fname)
            try:
                sock.write(b"OK")
                sock.flush()
            except Exception:
                pass
        except Exception:
            logging.exception("Bridge PhaseDRX: erro ao ler payload.")

    def close(self):
        if self._server is not None:
            try:
                self._server.close()
            except Exception:
                pass
            self._server = None


def is_phasedrx_running(timeout_ms: int = 250) -> bool:
    """True se houver um PhaseDRX escutando o bridge (qualquer processo)."""
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    ok = sock.waitForConnected(timeout_ms)
    if ok:
        sock.disconnectFromServer()
    return bool(ok)


def send_cif_to_phasedrx(cif_string: str, filename: str = "imported.cif",
                         timeout_ms: int = _TIMEOUT_MS) -> bool:
    """Envia um CIF ao PhaseDRX que estiver escutando. True se entregue."""
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    if not sock.waitForConnected(timeout_ms):
        return False
    try:
        data = json.dumps({"cif": cif_string, "filename": filename}).encode("utf-8")
        sock.write(data)
        sock.flush()
        sock.waitForBytesWritten(timeout_ms)
        sock.waitForReadyRead(timeout_ms)  # espera o "OK"
        return True
    except Exception:
        logging.exception("Bridge PhaseDRX: falha ao enviar CIF.")
        return False
    finally:
        sock.disconnectFromServer()
