"""Gera o latest.json publicado em cada release (lido pelo app para atualizar).

Uso:
    python tools/make_latest_json.py 0.0.12 dist/pomodoro-gatodoro-x64-setup.exe --output dist/latest.json

O app baixa este arquivo por https://github.com/<repo>/releases/latest/download/latest.json,
que não conta no limite de consultas da API do GitHub.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = "lucasbehrooz/pomodoro-gatodoro"


def build_manifest(version: str, installer: Path) -> dict:
    version = version.lstrip("v")
    tag = f"v{version}"
    digest = hashlib.sha256()
    with installer.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "version": version,
        "tag": tag,
        "url": f"https://github.com/{REPO}/releases/tag/{tag}",
        "installer": {
            "name": installer.name,
            "url": f"https://github.com/{REPO}/releases/download/{tag}/{installer.name}",
            "size": installer.stat().st_size,
            "sha256": digest.hexdigest(),
        },
    }


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 4 or args[2] != "--output":
        raise SystemExit("uso: make_latest_json.py <versao> <instalador> --output <arquivo>")
    manifest = build_manifest(args[0], Path(args[1]))
    Path(args[3]).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
