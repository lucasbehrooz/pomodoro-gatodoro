"""Extração das notas de release a partir do CHANGELOG.md."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("extract_changelog", ROOT / "tools" / "extract_changelog.py")
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

SAMPLE = """# Changelog

## [Não lançado]

### Adicionado
- Coisa nova.

## [0.0.2]

### Adicionado
- Tema.

## [0.0.1]

- Primeira.
"""


def test_extracts_only_requested_section():
    body = mod.extract("0.0.2", SAMPLE)
    assert body == "### Adicionado\n- Tema."


def test_last_section_runs_to_end():
    assert mod.extract("0.0.1", SAMPLE) == "- Primeira."


def test_unknown_version_returns_none():
    assert mod.extract("9.9.9", SAMPLE) is None


def test_real_changelog_has_every_tagged_version():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for v in ["0.0.1", "0.0.2", "0.0.3", "0.0.4", "0.0.5", "0.0.6"]:
        assert mod.extract(v, text), f"sem entrada para {v}"
