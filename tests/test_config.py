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
