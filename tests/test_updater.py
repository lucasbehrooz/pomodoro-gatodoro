import hashlib
import io
from pathlib import Path

import pytest

from pomodoro.updater import (
    INSTALLER_NAME,
    RELEASES_URL,
    UpdateError,
    UpdateInfo,
    UpdateManager,
    UpdateState,
    check_for_update,
    download_installer,
    format_progress,
    is_newer,
    parse_version,
)

PAYLOAD = b"instalador falso " * 1000
PAYLOAD_SHA = hashlib.sha256(PAYLOAD).hexdigest()


def release(tag: str, url: str = "https://example.test/release", assets=None) -> dict:
    return {"tag_name": tag, "html_url": url, "assets": assets or []}


def installer_asset(**overrides) -> dict:
    asset = {
        "name": INSTALLER_NAME,
        "size": len(PAYLOAD),
        "digest": f"sha256:{PAYLOAD_SHA}",
        "browser_download_url": "https://example.test/setup.exe",
    }
    asset.update(overrides)
    return asset


# ---- versões -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0.0.7", (0, 0, 7)),
        ("v1.2.3", (1, 2, 3)),
        (" v0.10.0 ", (0, 10, 0)),
        ("1.2", None),
        ("v1.2.3-beta", None),
        ("abc", None),
        ("", None),
    ],
)
def test_parse_version(text, expected):
    assert parse_version(text) == expected


def test_is_newer_compares_numerically():
    assert is_newer("0.0.10", "0.0.9")
    assert is_newer("0.1.0", "0.0.99")
    assert not is_newer("0.0.7", "0.0.7")
    assert not is_newer("0.0.6", "0.0.7")
    assert not is_newer("lixo", "0.0.7")
    assert not is_newer("0.0.8", "0.0.0-dev")


# ---- check_for_update -------------------------------------------------------------


def test_newer_release_returns_info_with_installer():
    info = check_for_update("0.0.7", fetch=lambda: release("v0.0.8", assets=[installer_asset()]))
    assert info == UpdateInfo(
        version="0.0.8",
        url="https://example.test/release",
        installer_url="https://example.test/setup.exe",
        installer_size=len(PAYLOAD),
        installer_sha256=PAYLOAD_SHA,
    )


def test_release_without_installer_has_no_installer_url():
    other = installer_asset(name="PomodoroGatodoro.exe")
    info = check_for_update("0.0.7", fetch=lambda: release("v0.0.8", assets=[other]))
    assert info is not None and info.installer_url is None


def test_bad_asset_fields_are_ignored():
    bad = installer_asset(
        browser_download_url="http://inseguro.test/setup.exe", size="x", digest="md5:abc"
    )
    info = check_for_update("0.0.7", fetch=lambda: release("v0.0.8", assets=[bad]))
    assert info is not None
    assert (info.installer_url, info.installer_size, info.installer_sha256) == (None, None, None)


def test_same_or_older_release_returns_none():
    assert check_for_update("0.0.7", fetch=lambda: release("v0.0.7")) is None
    assert check_for_update("0.0.7", fetch=lambda: release("v0.0.6")) is None


def test_skipped_version_is_not_announced():
    assert check_for_update("0.0.7", skipped="0.0.8", fetch=lambda: release("v0.0.8")) is None
    info = check_for_update("0.0.7", skipped="0.0.8", fetch=lambda: release("v0.0.9"))
    assert info is not None and info.version == "0.0.9"


def test_missing_url_falls_back_to_releases_page():
    info = check_for_update("0.0.7", fetch=lambda: {"tag_name": "v0.0.8"})
    assert info is not None and info.url == RELEASES_URL


def test_fetch_errors_propagate():
    def fail() -> dict:
        raise OSError("sem internet")

    with pytest.raises(OSError):
        check_for_update("0.0.7", fetch=fail)
    with pytest.raises(KeyError):
        check_for_update("0.0.7", fetch=lambda: {})


# ---- download ---------------------------------------------------------------------


def info_for(**overrides) -> UpdateInfo:
    values = dict(
        version="0.0.8",
        url="u",
        installer_url="https://example.test/setup.exe",
        installer_size=len(PAYLOAD),
        installer_sha256=PAYLOAD_SHA,
    )
    values.update(overrides)
    return UpdateInfo(**values)


def opener_for(data: bytes):
    return lambda url: io.BytesIO(data)


def test_download_verifies_and_reports_progress(tmp_path: Path):
    progress: list[tuple[int, int | None]] = []
    path = download_installer(
        info_for(), tmp_path, on_progress=lambda d, t: progress.append((d, t)),
        opener=opener_for(PAYLOAD),
    )
    assert path == tmp_path / "pomodoro-gatodoro-0.0.8-setup.exe"
    assert path.read_bytes() == PAYLOAD
    assert progress[-1] == (len(PAYLOAD), len(PAYLOAD))
    assert not list(tmp_path.glob("*.part"))


def test_download_rejects_wrong_hash(tmp_path: Path):
    tampered = PAYLOAD[:-1] + b"X"
    with pytest.raises(UpdateError, match="SHA-256"):
        download_installer(info_for(), tmp_path, opener=opener_for(tampered))
    assert list(tmp_path.iterdir()) == []


def test_download_rejects_truncated_file(tmp_path: Path):
    with pytest.raises(UpdateError, match="incompleto"):
        download_installer(info_for(), tmp_path, opener=opener_for(PAYLOAD[:100]))
    assert list(tmp_path.iterdir()) == []


def test_download_network_error_cleans_up(tmp_path: Path):
    class Broken(io.BytesIO):
        def read(self, *a):
            raise OSError("conexão caiu")

    with pytest.raises(UpdateError, match="conexão caiu"):
        download_installer(info_for(), tmp_path, opener=lambda url: Broken())
    assert list(tmp_path.iterdir()) == []


def test_download_without_installer_url(tmp_path: Path):
    with pytest.raises(UpdateError):
        download_installer(info_for(installer_url=None), tmp_path, opener=opener_for(PAYLOAD))


def test_format_progress():
    assert format_progress(15_000_000, 35_700_000) == "Baixando… 42% (15,0 de 35,7 MB)"
    assert format_progress(2_500_000, None) == "Baixando… 2,5 MB"


# ---- UpdateManager ------------------------------------------------------------------


class Harness:
    """UpdateManager síncrono: threads e post rodam na hora."""

    def __init__(self, check=None, download=None, launch=None):
        self.quit_calls = 0
        self.states: list[UpdateState] = []
        self.launched: list[Path] = []
        self.manager = UpdateManager(
            post=lambda fn: fn(),
            quit_app=self._quit,
            current="0.0.7",
            check=check or (lambda current: None),
            download=download or (lambda info, on_progress: Path("setup.exe")),
            launch=launch or self.launched.append,
            start_thread=lambda fn: fn(),
        )
        self.manager.subscribe(lambda: self.states.append(self.manager.state))

    def _quit(self):
        self.quit_calls += 1


def test_manager_check_up_to_date():
    h = Harness()
    h.manager.check()
    assert h.states == [UpdateState.CHECKING, UpdateState.UP_TO_DATE]
    assert h.manager.info is None


def test_manager_check_available_passes_current_version():
    seen = {}
    info = info_for()

    def check(current):
        seen["current"] = current
        return info

    h = Harness(check=check)
    h.manager.check()
    assert seen["current"] == "0.0.7"
    assert h.manager.state is UpdateState.AVAILABLE and h.manager.info == info


def test_manager_check_error_visible_or_silent():
    def fail(current):
        raise OSError("sem internet")

    h = Harness(check=fail)
    h.manager.check()
    assert h.manager.state is UpdateState.ERROR and "sem internet" in h.manager.error

    h = Harness(check=fail)
    h.manager.check(silent=True)
    assert h.manager.state is UpdateState.IDLE and h.manager.error == ""


def test_manager_install_downloads_launches_and_quits():
    def download(info, on_progress):
        on_progress(50, 100)
        on_progress(100, 100)
        return Path("setup.exe")

    h = Harness(check=lambda current: info_for(installer_size=100), download=download)
    h.manager.check()
    h.manager.install()
    assert h.launched == [Path("setup.exe")]
    assert h.quit_calls == 1
    assert h.manager.state is UpdateState.LAUNCHING
    assert UpdateState.DOWNLOADING in h.states


def test_manager_install_error_keeps_app_open():
    def download(info, on_progress):
        raise UpdateError("O arquivo baixado não confere (SHA-256). Tente de novo.")

    h = Harness(check=lambda current: info_for(), download=download)
    h.manager.check()
    h.manager.install()
    assert h.manager.state is UpdateState.ERROR
    assert "SHA-256" in h.manager.error
    assert h.quit_calls == 0 and h.launched == []
    assert h.manager.info is not None  # dá para tentar de novo


def test_manager_install_without_info_does_nothing():
    h = Harness()
    h.manager.install()
    assert h.states == [] and h.quit_calls == 0


def test_manager_ignores_actions_while_busy():
    pending = []
    manager = UpdateManager(
        post=lambda fn: fn(),
        quit_app=lambda: None,
        check=lambda current: None,
        start_thread=pending.append,  # não roda: fica "verificando"
    )
    manager.check()
    manager.check()
    assert manager.busy and len(pending) == 1


def test_manager_listener_errors_do_not_break_others():
    h = Harness()
    h.manager.subscribe(lambda: 1 / 0)  # ouvinte com erro não derruba os outros
    h.manager.check()
    assert h.states[-1] is UpdateState.UP_TO_DATE
