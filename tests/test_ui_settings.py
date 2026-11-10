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
