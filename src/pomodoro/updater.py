"""Verificação de nova versão via GitHub Releases.

Só avisa: não baixa nem instala nada. O usuário decide abrir a página da
release e instalar normalmente.

Threading: ``check_in_background`` roda a consulta numa thread daemon e chama
``on_update`` nessa thread. Quem mexe em widgets deve repassar para a thread
do Tk (ex.: ``MainWindow.post``).
"""

from __future__ import annotations

import json
import logging
import re
import threading
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from pomodoro import __version__

logger = logging.getLogger(__name__)

REPO = "lucasbehrooz/pomodoro-gatodoro"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{REPO}/releases/latest"
TIMEOUT_SECONDS = 5.0

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class UpdateInfo:
    version: str  # sem o "v", ex.: "0.0.8"
    url: str  # página da release


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


def fetch_latest_release(timeout: float = TIMEOUT_SECONDS) -> dict:
    """JSON da última release publicada (rascunhos e pré-releases ficam de fora)."""
    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "pomodoro-gatodoro-updater",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def check_for_update(
    current: str = __version__,
    skipped: str = "",
    fetch: Callable[[], dict] = fetch_latest_release,
) -> UpdateInfo | None:
    """UpdateInfo se houver versão mais nova que current e diferente de skipped.

    Qualquer falha (sem internet, limite da API, JSON inesperado) resulta em
    None: a verificação nunca pode atrapalhar o uso do app.
    """
    try:
        data = fetch()
        tag = str(data["tag_name"])
        url = str(data.get("html_url") or RELEASES_URL)
    except Exception:
        logger.info("Não foi possível verificar atualizações", exc_info=True)
        return None
    version = tag.lstrip("v")
    if not is_newer(version, current):
        return None
    if skipped and parse_version(skipped) == parse_version(version):
        return None
    return UpdateInfo(version=version, url=url)


def check_in_background(
    on_update: Callable[[UpdateInfo], None],
    skipped: str = "",
    check: Callable[..., UpdateInfo | None] = check_for_update,
) -> threading.Thread:
    """Roda check_for_update numa thread daemon; chama on_update só se houver versão nova."""

    def run() -> None:
        info = check(skipped=skipped)
        if info is not None:
            on_update(info)

    thread = threading.Thread(target=run, name="update-check", daemon=True)
    thread.start()
    return thread
