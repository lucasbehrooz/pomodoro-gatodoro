import pytest

from pomodoro.config import Config, load_config, save_config


def test_missing_file_returns_defaults(tmp_path):
    assert load_config(tmp_path / "nope.json") == Config()


def test_corrupted_file_returns_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{not json", encoding="utf-8")
    assert load_config(p) == Config()


def test_roundtrip(tmp_path):
    p = tmp_path / "sub" / "config.json"
    cfg = Config(focus_minutes=50, brown_noise_enabled=True)
    save_config(cfg, p)
    assert load_config(p) == cfg


def test_unknown_keys_ignored(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"focus_minutes": 30, "chave_antiga": 1}', encoding="utf-8")
    cfg = load_config(p)
    assert cfg.focus_minutes == 30
    assert cfg.short_break_minutes == Config().short_break_minutes


def test_start_with_windows_default_is_false():
    assert Config().start_with_windows is False


def test_start_with_windows_roundtrip(tmp_path):
    p = tmp_path / "config.json"
    save_config(Config(start_with_windows=True), p)
    assert load_config(p).start_with_windows is True


def test_start_with_windows_missing_uses_default(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"focus_minutes": 30}', encoding="utf-8")
    assert load_config(p).start_with_windows is False


@pytest.mark.parametrize("value", ['"sim"', "1", "null", "[]"])
def test_start_with_windows_invalid_uses_default(tmp_path, value):
    p = tmp_path / "config.json"
    p.write_text('{"start_with_windows": %s}' % value, encoding="utf-8")
    assert load_config(p).start_with_windows is False


def test_update_check_defaults():
    cfg = Config()
    assert cfg.check_updates is True
    assert cfg.skipped_version == ""


def test_update_fields_roundtrip(tmp_path):
    p = tmp_path / "config.json"
    save_config(Config(check_updates=False, skipped_version="0.0.8"), p)
    cfg = load_config(p)
    assert cfg.check_updates is False
    assert cfg.skipped_version == "0.0.8"


def test_invalid_update_fields_fall_back_to_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text('{"check_updates": "sim", "skipped_version": 8}', encoding="utf-8")
    cfg = load_config(p)
    assert cfg.check_updates is True
    assert cfg.skipped_version == ""
