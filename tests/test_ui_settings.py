import pytest

from pomodoro.config import Config
from pomodoro.ui.settings import SettingsError, build_config, form_values


def valid_raw(**overrides) -> dict:
    raw = {
        "focus_minutes": "30",
        "short_break_minutes": "6",
        "long_break_minutes": "20",
        "cycles_before_long_break": "3",
        "brown_noise_volume": 45.0,
        "sound_enabled": False,
        "toast_enabled": True,
        "brown_noise_enabled": True,
        "brown_noise_focus_only": False,
        "close_to_tray": False,
    }
    raw.update(overrides)
    return raw


def test_form_values_shows_volume_as_percent():
    values = form_values(Config(brown_noise_volume=0.3))
    assert values["brown_noise_volume"] == 30.0
    assert values["focus_minutes"] == 25


def test_build_config_parses_valid_values():
    new = build_config(valid_raw(), Config())
    assert new.focus_minutes == 30
    assert new.short_break_minutes == 6
    assert new.long_break_minutes == 20
    assert new.cycles_before_long_break == 3
    assert new.brown_noise_volume == pytest.approx(0.45)
    assert new.sound_enabled is False
    assert new.brown_noise_focus_only is False
    assert new.close_to_tray is False


def test_build_config_keeps_base_for_missing_fields():
    base = Config(focus_minutes=40, close_to_tray=False)
    new = build_config({"short_break_minutes": "7"}, base)
    assert new.focus_minutes == 40
    assert new.short_break_minutes == 7
    assert new.close_to_tray is False


def test_build_config_accepts_text_and_comma_volume():
    new = build_config({"brown_noise_volume": " 12,5 "}, Config())
    assert new.brown_noise_volume == pytest.approx(0.125)


def test_build_config_does_not_mutate_base():
    base = Config(focus_minutes=25)
    build_config({"focus_minutes": "50"}, base)
    assert base.focus_minutes == 25


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("focus_minutes", "abc", "Duração do foco (min): informe um número inteiro."),
        ("focus_minutes", "0", "Duração do foco (min): informe um valor entre 1 e 180."),
        ("short_break_minutes", "61", "Pausa curta (min): informe um valor entre 1 e 60."),
        ("long_break_minutes", "", "Pausa longa (min): informe um número inteiro."),
        ("cycles_before_long_break", "13", "Focos até a pausa longa: informe um valor entre 1 e 12."),
        ("daily_goal", "25", "Meta diária de focos (0 = sem meta): informe um valor entre 0 e 24."),
        ("daily_goal", "-1", "Meta diária de focos (0 = sem meta): informe um valor entre 0 e 24."),
        ("daily_goal", "oito", "Meta diária de focos (0 = sem meta): informe um número inteiro."),
    ],
)
def test_build_config_rejects_invalid_int(field, value, message):
    with pytest.raises(SettingsError) as exc:
        build_config({field: value}, Config())
    assert str(exc.value) == message


@pytest.mark.parametrize("volume", [-1, 101, "muito"])
def test_build_config_rejects_invalid_volume(volume):
    with pytest.raises(SettingsError):
        build_config({"brown_noise_volume": volume}, Config())


def test_settings_error_is_value_error():
    assert issubclass(SettingsError, ValueError)


def test_start_with_windows_checkbox_is_built_and_parsed():
    from pomodoro.ui.settings import BOOL_FIELDS, LABELS

    assert "start_with_windows" in BOOL_FIELDS
    assert LABELS["start_with_windows"] == "Iniciar com o Windows"
    assert form_values(Config(start_with_windows=True))["start_with_windows"] is True
    new = build_config({"start_with_windows": True}, Config())
    assert new.start_with_windows is True
    assert build_config({"start_with_windows": False}, new).start_with_windows is False


def test_check_updates_is_in_form_and_keeps_skipped_version():
    base = Config(check_updates=True, skipped_version="0.0.8")
    assert form_values(base)["check_updates"] is True
    new = build_config(valid_raw(check_updates=False), base)
    assert new.check_updates is False
    assert new.skipped_version == "0.0.8"


def test_update_status_text():
    from pathlib import Path

    from pomodoro.ui.settings_dialog import update_status_text
    from pomodoro.updater import UpdateInfo, UpdateManager, UpdateState

    m = UpdateManager(post=lambda fn: fn(), quit_app=lambda: None, start_thread=lambda fn: fn(),
                      check=lambda current: None, download=lambda info, on_progress: Path("x"))
    assert update_status_text(m) == ""
    m.check()
    assert update_status_text(m) == "Você está na versão mais recente."
    m.state, m.info = UpdateState.AVAILABLE, UpdateInfo("1.0.0", "u")
    assert update_status_text(m) == "Nova versão disponível: 1.0.0"
    m.state, m.progress = UpdateState.DOWNLOADING, (1_000_000, 2_000_000)
    assert update_status_text(m).startswith("Baixando… 50%")
    m.state, m.error = UpdateState.ERROR, "deu ruim"
    assert update_status_text(m) == "deu ruim"


def test_auto_start_checkboxes_are_built_and_parsed():
    from pomodoro.ui.settings import BOOL_FIELDS, LABELS

    assert "auto_start_breaks" in BOOL_FIELDS
    assert "auto_start_focus" in BOOL_FIELDS
    assert LABELS["auto_start_breaks"] == "Iniciar pausas automaticamente"
    assert LABELS["auto_start_focus"] == "Iniciar focos automaticamente"
    values = form_values(Config(auto_start_breaks=False))
    assert values["auto_start_breaks"] is False
    assert values["auto_start_focus"] is True
    new = build_config(valid_raw(auto_start_breaks=False, auto_start_focus=False), Config())
    assert new.auto_start_breaks is False
    assert new.auto_start_focus is False


def test_daily_goal_is_in_form_and_accepts_zero():
    assert form_values(Config(daily_goal=6))["daily_goal"] == 6
    assert build_config({"daily_goal": "0"}, Config()).daily_goal == 0
    assert build_config({"daily_goal": " 12 "}, Config()).daily_goal == 12
