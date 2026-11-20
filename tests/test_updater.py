import threading

import pytest

from pomodoro.updater import (
    RELEASES_URL,
    UpdateInfo,
    check_for_update,
    check_in_background,
    is_newer,
    parse_version,
)


def release(tag: str, url: str = "https://example.test/release") -> dict:
    return {"tag_name": tag, "html_url": url}


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


def test_newer_release_returns_info():
    info = check_for_update("0.0.7", fetch=lambda: release("v0.0.8"))
    assert info == UpdateInfo(version="0.0.8", url="https://example.test/release")


def test_same_or_older_release_returns_none():
    assert check_for_update("0.0.7", fetch=lambda: release("v0.0.7")) is None
    assert check_for_update("0.0.7", fetch=lambda: release("v0.0.6")) is None


def test_skipped_version_is_not_announced():
    assert check_for_update("0.0.7", skipped="0.0.8", fetch=lambda: release("v0.0.8")) is None


def test_version_newer_than_skipped_is_announced():
    info = check_for_update("0.0.7", skipped="0.0.8", fetch=lambda: release("v0.0.9"))
    assert info is not None and info.version == "0.0.9"


def test_missing_url_falls_back_to_releases_page():
    info = check_for_update("0.0.7", fetch=lambda: {"tag_name": "v0.0.8"})
    assert info is not None and info.url == RELEASES_URL


@pytest.mark.parametrize("data", [{}, {"tag_name": None}, [], "texto"])
def test_unexpected_json_returns_none(data):
    assert check_for_update("0.0.7", fetch=lambda: data) is None


def test_network_error_returns_none():
    def fail() -> dict:
        raise OSError("sem internet")

    assert check_for_update("0.0.7", fetch=fail) is None


def test_check_in_background_calls_back_only_with_update():
    received: list[UpdateInfo] = []
    info = UpdateInfo("0.0.8", "u")

    check_in_background(received.append, check=lambda skipped: info).join(1)
    check_in_background(received.append, check=lambda skipped: None).join(1)

    assert received == [info]


def test_check_in_background_passes_skipped_and_runs_off_main_thread():
    seen: dict = {}

    def check(skipped: str):
        seen["skipped"] = skipped
        seen["thread"] = threading.current_thread()
        return None

    check_in_background(lambda i: None, skipped="0.0.8", check=check).join(1)
    assert seen["skipped"] == "0.0.8"
    assert seen["thread"] is not threading.main_thread()
