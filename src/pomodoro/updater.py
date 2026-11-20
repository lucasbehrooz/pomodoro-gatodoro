"""Atualizações via GitHub Releases: verificar, baixar e abrir o instalador.

Fluxo:
1. ``check_for_update`` consulta a última release e diz se há versão nova.
2. ``download_installer`` baixa o ``pomodoro-gatodoro-x64-setup.exe`` para a
   pasta temporária e confere o SHA-256 informado pelo GitHub.
3. ``launch_installer`` abre o instalador normal (com as telas de sempre). O
   app então se fecha para o instalador poder substituir o executável.

``UpdateManager`` junta tudo com estado observável pela UI. O trabalho de rede
roda em threads daemon; toda mudança de estado é entregue via ``post`` (na
janela, ``MainWindow.post``), então os ouvintes sempre rodam na thread do Tk.
"""

from __future__ import annotations

import enum
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pomodoro import __version__

logger = logging.getLogger(__name__)

REPO = "lucasbehrooz/pomodoro-gatodoro"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{REPO}/releases/latest"
INSTALLER_NAME = "pomodoro-gatodoro-x64-setup.exe"
USER_AGENT = "pomodoro-gatodoro-updater"
TIMEOUT_SECONDS = 5.0
DOWNLOAD_TIMEOUT_SECONDS = 30.0
CHUNK_SIZE = 64 * 1024

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
_SHA256_RE = re.compile(r"^sha256:([0-9a-f]{64})$")


class UpdateError(Exception):
    """Falha ao baixar ou abrir a atualização. A mensagem é exibível ao usuário."""


@dataclass(frozen=True)
class UpdateInfo:
    version: str  # sem o "v", ex.: "0.0.8"
    url: str  # página da release
    installer_url: str | None = None
    installer_size: int | None = None
    installer_sha256: str | None = None  # hex minúsculo


# ---- versões ---------------------------------------------------------------


def parse_version(text: str) -> tuple[int, int, int] | None:
    """'v1.2.3' ou '1.2.3' -> (1, 2, 3). Qualquer outra coisa -> None."""
    match = _VERSION_RE.match(text.strip())
    if match is None:
        return None
    major, minor, patch = (int(g) for g in match.groups())
    return major, minor, patch


def is_newer(candidate: str, current: str) -> bool:
    """True se candidate > current. Versões não reconhecidas nunca são 'mais novas'."""
    new, cur = parse_version(candidate), parse_version(current)
    return new is not None and cur is not None and new > cur


# ---- consulta --------------------------------------------------------------


def fetch_latest_release(timeout: float = TIMEOUT_SECONDS) -> dict:
    """JSON da última release publicada (rascunhos e pré-releases ficam de fora)."""
    request = urllib.request.Request(
        API_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _installer_asset(data: dict) -> tuple[str | None, int | None, str | None]:
    for asset in data.get("assets") or []:
        if not isinstance(asset, dict) or asset.get("name") != INSTALLER_NAME:
            continue
        url = asset.get("browser_download_url")
        size = asset.get("size")
        match = _SHA256_RE.match(str(asset.get("digest") or "").lower())
        return (
            url if isinstance(url, str) and url.startswith("https://") else None,
            size if isinstance(size, int) and size > 0 else None,
            match.group(1) if match else None,
        )
    return None, None, None


def check_for_update(
    current: str = __version__,
    skipped: str = "",
    fetch: Callable[[], dict] = fetch_latest_release,
) -> UpdateInfo | None:
    """UpdateInfo se houver versão mais nova que current e diferente de skipped.

    Lança exceção se a consulta falhar (sem internet, limite da API, JSON
    inesperado). Quem chama decide se mostra o erro ou ignora.
    """
    data = fetch()
    tag = str(data["tag_name"])
    version = tag.lstrip("v")
    if not is_newer(version, current):
        return None
    if skipped and parse_version(skipped) == parse_version(version):
        return None
    installer_url, size, sha256 = _installer_asset(data)
    return UpdateInfo(
        version=version,
        url=str(data.get("html_url") or RELEASES_URL),
        installer_url=installer_url,
        installer_size=size,
        installer_sha256=sha256,
    )


# ---- download e instalação --------------------------------------------------


def _open_download(url: str):  # pragma: no cover - rede real
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS)


def download_installer(
    info: UpdateInfo,
    dest_dir: Path | None = None,
    on_progress: Callable[[int, int | None], None] | None = None,
    opener: Callable[[str], object] = _open_download,
) -> Path:
    """Baixa o instalador e confere tamanho e SHA-256. Retorna o caminho do arquivo.

    O download vai para um ``.part`` e só é renomeado depois de conferido, então
    nunca sobra um instalador incompleto com o nome final.
    """
    if not info.installer_url:
        raise UpdateError("Esta versão não tem instalador para baixar.")
    dest_dir = dest_dir or Path(tempfile.gettempdir())
    final = dest_dir / f"pomodoro-gatodoro-{info.version}-setup.exe"
    partial = final.with_name(final.name + ".part")
    digest = hashlib.sha256()
    received = 0
    try:
        with opener(info.installer_url) as response, partial.open("wb") as out:  # type: ignore[attr-defined]
            total = info.installer_size
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                if on_progress is not None:
                    on_progress(received, total)
    except OSError as exc:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"Falha no download: {exc}") from exc

    if info.installer_size is not None and received != info.installer_size:
        partial.unlink(missing_ok=True)
        raise UpdateError("Download incompleto. Tente de novo.")
    if info.installer_sha256 is not None and digest.hexdigest() != info.installer_sha256:
        partial.unlink(missing_ok=True)
        raise UpdateError("O arquivo baixado não confere (SHA-256). Tente de novo.")
    os.replace(partial, final)
    return final


def launch_installer(path: Path) -> None:
    """Abre o instalador normal. No Windows usa startfile (lida com UAC, se pedido)."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.Popen([str(path)])
    except OSError as exc:
        raise UpdateError(f"Não foi possível abrir o instalador: {exc}") from exc


# ---- estado para a UI --------------------------------------------------------


class UpdateState(enum.Enum):
    IDLE = "idle"  # ainda não verificou
    CHECKING = "checking"
    UP_TO_DATE = "up_to_date"
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    LAUNCHING = "launching"  # instalador aberto; o app vai fechar
    ERROR = "error"


class UpdateManager:
    """Estado das atualizações, compartilhado entre o aviso e as Configurações.

    Parâmetros:
        post: agenda uma função na thread da UI (ex.: MainWindow.post).
        quit_app: fecha o app depois de abrir o instalador.
        Os demais são injetáveis para testes.
    """

    def __init__(
        self,
        post: Callable[[Callable[[], None]], None],
        quit_app: Callable[[], None],
        *,
        current: str = __version__,
        check: Callable[..., UpdateInfo | None] = check_for_update,
        download: Callable[..., Path] = download_installer,
        launch: Callable[[Path], None] = launch_installer,
        start_thread: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self._post = post
        self._quit_app = quit_app
        self.current = current
        self._check = check
        self._download = download
        self._launch = launch
        self._start_thread = start_thread or _daemon_thread
        self.state = UpdateState.IDLE
        self.info: UpdateInfo | None = None
        self.error = ""
        self.progress: tuple[int, int | None] = (0, None)
        self._listeners: list[Callable[[], None]] = []

    # ---- ouvintes (thread da UI) --------------------------------------------

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _set(self, state: UpdateState, **changes: object) -> None:
        self.state = state
        for name, value in changes.items():
            setattr(self, name, value)
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:
                logger.exception("Falha em ouvinte de atualização")

    @property
    def busy(self) -> bool:
        return self.state in (UpdateState.CHECKING, UpdateState.DOWNLOADING, UpdateState.LAUNCHING)

    # ---- ações ---------------------------------------------------------------

    def check(self, silent: bool = False) -> None:
        """Verifica em segundo plano.

        Não filtra a versão ignorada: as Configurações sempre mostram a versão
        nova; quem decide esconder o aviso é a janela principal.
        silent=True (verificação ao abrir o app): falhas não viram estado de erro.
        """
        if self.busy:
            return
        self._set(UpdateState.CHECKING, error="")

        def work() -> None:
            try:
                info = self._check(current=self.current)
            except Exception as exc:
                logger.info("Não foi possível verificar atualizações", exc_info=True)
                if silent:
                    self._post(lambda: self._set(UpdateState.IDLE))
                else:
                    msg = f"Não foi possível verificar: {exc}"
                    self._post(lambda: self._set(UpdateState.ERROR, error=msg))
                return
            if info is None:
                self._post(lambda: self._set(UpdateState.UP_TO_DATE, info=None))
            else:
                self._post(lambda: self._set(UpdateState.AVAILABLE, info=info))

        self._start_thread(work)

    def install(self) -> None:
        """Baixa o instalador, abre e fecha o app. Só age com versão disponível."""
        info = self.info
        if info is None or self.busy:
            return
        self._set(UpdateState.DOWNLOADING, error="", progress=(0, info.installer_size))

        last_step = -1

        def on_progress(done: int, total: int | None) -> None:
            # Um aviso por ponto percentual (ou por MB sem total): sem inundar a fila da UI.
            nonlocal last_step
            step = done * 100 // total if total else done // 1_000_000
            if step != last_step:
                last_step = step
                self._post(lambda: self._set(UpdateState.DOWNLOADING, progress=(done, total)))

        def work() -> None:
            try:
                path = self._download(info, on_progress=on_progress)
                self._launch(path)
            except Exception as exc:
                logger.warning("Falha ao atualizar", exc_info=True)
                msg = str(exc) if isinstance(exc, UpdateError) else f"Falha ao atualizar: {exc}"
                self._post(lambda: self._set(UpdateState.ERROR, error=msg))
                return
            self._post(self._finish_launch)

        self._start_thread(work)

    def _finish_launch(self) -> None:
        self._set(UpdateState.LAUNCHING)
        self._quit_app()


def _daemon_thread(fn: Callable[[], None]) -> None:
    threading.Thread(target=fn, name="updater", daemon=True).start()


def format_progress(done: int, total: int | None) -> str:
    """'Baixando… 42% (15,0 de 35,7 MB)' ou, sem total, 'Baixando… 15,0 MB'."""
    mb = done / 1_000_000
    if not total:
        return f"Baixando… {mb:.1f} MB".replace(".", ",")
    percent = min(100, int(done * 100 / total))
    text = f"Baixando… {percent}% ({mb:.1f} de {total / 1_000_000:.1f} MB)"
    return text.replace(".", ",")
