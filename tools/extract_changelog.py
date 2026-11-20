"""Imprime a seção do CHANGELOG.md de uma versão, para usar como texto da release.

Uso:
    python tools/extract_changelog.py 0.0.7 [--output release-notes.md]

Com --output, grava o arquivo em UTF-8. Use isso no CI: no Windows, redirecionar
a saída (``> arquivo``) grava em cp1252 e os acentos chegam quebrados ao GitHub.

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


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    output: Path | None = None
    if len(args) == 3 and args[1] == "--output":
        output = Path(args[2])
    elif len(args) != 1:
        raise SystemExit("uso: extract_changelog.py <versao> [--output ARQUIVO]")
    section = extract(args[0], CHANGELOG.read_text(encoding="utf-8"))
    notes = (section if section else FALLBACK) + "\n"
    if output is not None:
        output.write_text(notes, encoding="utf-8", newline="\n")
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        sys.stdout.write(notes)


if __name__ == "__main__":
    main()
