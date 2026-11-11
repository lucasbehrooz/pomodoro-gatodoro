"""Imprime a seção do CHANGELOG.md de uma versão, para usar como texto da release.

Uso:
    python tools/extract_changelog.py 0.0.7

Se a versão não existir no changelog, imprime um texto padrão e sai com código 0,
para que a publicação da release não falhe por falta de notas.
"""

from __future__ import annotations

import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
FALLBACK = "Veja os arquivos abaixo para baixar a versão."


def extract(version: str, text: str) -> str | None:
    """Corpo da seção '## [version]' (sem o cabeçalho), ou None se não existir."""
    lines = text.splitlines()
    header = f"## [{version}]"
    start = next((i for i, line in enumerate(lines) if line.strip() == header), None)
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## ["):
            break
        body.append(line)
    return "\n".join(body).strip()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("uso: extract_changelog.py <versao>")
    section = extract(sys.argv[1], CHANGELOG.read_text(encoding="utf-8"))
    print(section if section else FALLBACK)


if __name__ == "__main__":
    main()
