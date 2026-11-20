"""Gera as instruções e skills do Claude Code e do OpenCode a partir da pasta .kiro.

Fonte única: edite só em .kiro/ e rode este script.

    python tools/sync_agents.py          # gera/atualiza os arquivos
    python tools/sync_agents.py --check  # só confere (sai com 1 se estiver desatualizado)

O que é gerado:
- .claude/skills/<nome>/  cópia de .kiro/skills/<nome>/ (Claude Code e OpenCode leem
  .claude/skills).
- AGENTS.md  steering com ``inclusion: always`` (OpenCode lê nativamente; Kiro também).
- CLAUDE.md  só importa o AGENTS.md (``@AGENTS.md``) para o Claude Code.
- .claude/rules/<nome>.md  steering com ``inclusion: fileMatch``, com ``paths:`` para o
  Claude Code carregar só ao mexer nesses arquivos. O AGENTS.md aponta para eles.
"""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIRO = ROOT / ".kiro"
CLAUDE_DIR = ROOT / ".claude"
GENERATED = "<!-- Gerado por tools/sync_agents.py a partir de .kiro/. Não edite aqui. -->"

# Ordem das seções do AGENTS.md; arquivos fora da lista vão no fim, em ordem alfabética.
STEERING_ORDER = ["product.md", "tech.md", "structure.md"]


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Frontmatter YAML simples (chave: valor e listas inline ["a", "b"])."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.index("\n---", 4)
    meta: dict[str, object] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = value.strip("\"'")
    return meta, text[end + 4 :].lstrip("\n")


def _steering() -> list[tuple[str, dict[str, object], str]]:
    files = sorted(
        (KIRO / "steering").glob("*.md"),
        key=lambda p: (STEERING_ORDER.index(p.name) if p.name in STEERING_ORDER else 99, p.name),
    )
    return [(p.name, *split_frontmatter(p.read_text(encoding="utf-8"))) for p in files]


def _demote(body: str) -> str:
    """Desce um nível os títulos (# vira ##) para caber dentro do AGENTS.md."""
    out, fenced = [], False
    for line in body.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        out.append("#" + line if line.startswith("#") and not fenced else line)
    return "\n".join(out).rstrip() + "\n"


def build_outputs() -> dict[Path, str]:
    """Arquivos de texto gerados (caminho -> conteúdo)."""
    outputs: dict[Path, str] = {}
    always, scoped = [], []
    for name, meta, body in _steering():
        (scoped if meta.get("inclusion") == "fileMatch" else always).append((name, meta, body))

    parts = [
        GENERATED,
        "",
        "# Instruções do projeto",
        "",
        "Válidas para Kiro, Claude Code e OpenCode. A fonte é `.kiro/steering/`;"
        " as skills ficam em `.kiro/skills/` (cópia em `.claude/skills/`).",
        "",
    ]
    for _, _, body in always:
        parts.append(_demote(body))
    if scoped:
        parts.append("## Regras por área\n")
        for name, meta, _ in scoped:
            patterns = meta.get("fileMatchPattern") or []
            listed = ", ".join(f"`{p}`" for p in patterns) if isinstance(patterns, list) else ""
            parts.append(f"- Ao mexer em {listed}, siga `.kiro/steering/{name}`.")
        parts.append("")
    outputs[ROOT / "AGENTS.md"] = "\n".join(parts).rstrip() + "\n"
    outputs[ROOT / "CLAUDE.md"] = f"{GENERATED}\n\n@AGENTS.md\n"

    for name, meta, body in scoped:
        patterns = meta.get("fileMatchPattern") or []
        paths = "\n".join(f'  - "{p}"' for p in patterns) if isinstance(patterns, list) else ""
        outputs[CLAUDE_DIR / "rules" / name] = f"---\npaths:\n{paths}\n---\n\n{GENERATED}\n\n{body}"
    return outputs


def _skill_dirs() -> list[Path]:
    return sorted(p.parent for p in (KIRO / "skills").glob("*/SKILL.md"))


def problems() -> list[str]:
    """Diferenças entre o que existe e o que seria gerado."""
    found: list[str] = []
    for path, content in build_outputs().items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            found.append(str(path.relative_to(ROOT)))
    for src in _skill_dirs():
        dst = CLAUDE_DIR / "skills" / src.name
        if not dst.exists():
            found.append(str(dst.relative_to(ROOT)))
            continue
        cmp = filecmp.dircmp(src, dst)
        if cmp.left_only or cmp.right_only or cmp.diff_files or _subdirs_differ(cmp):
            found.append(str(dst.relative_to(ROOT)))
    return found


def _subdirs_differ(cmp: filecmp.dircmp) -> bool:
    return any(
        sub.left_only or sub.right_only or sub.diff_files or _subdirs_differ(sub)
        for sub in cmp.subdirs.values()
    )


def sync() -> list[str]:
    changed = problems()
    for path, content in build_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for src in _skill_dirs():
        dst = CLAUDE_DIR / "skills" / src.name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    return changed


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--check"]:
        stale = problems()
        for item in stale:
            print(f"desatualizado: {item}")
        if stale:
            print("Rode: python tools/sync_agents.py")
        return 1 if stale else 0
    if args:
        raise SystemExit("uso: sync_agents.py [--check]")
    for item in sync():
        print(f"atualizado: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
