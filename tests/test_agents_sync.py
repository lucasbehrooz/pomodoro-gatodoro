"""As instruções/skills do Claude Code e OpenCode são geradas a partir de .kiro/."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("sync_agents", ROOT / "tools" / "sync_agents.py")
sync_agents = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_agents)


def test_generated_agent_files_are_in_sync_with_kiro():
    stale = sync_agents.problems()
    assert stale == [], f"Rode `python tools/sync_agents.py`. Desatualizados: {stale}"


def test_frontmatter_parsing():
    meta, body = sync_agents.split_frontmatter(
        '---\ninclusion: fileMatch\nfileMatchPattern: ["a/**/*.py", "b.py"]\n---\n\n# T\n'
    )
    assert meta == {"inclusion": "fileMatch", "fileMatchPattern": ["a/**/*.py", "b.py"]}
    assert body == "# T\n"
    assert sync_agents.split_frontmatter("# sem frontmatter\n") == ({}, "# sem frontmatter\n")


def test_demote_keeps_code_blocks():
    text = "# Título\n```bash\n# comentário\n```\n## Sub\n"
    assert sync_agents._demote(text) == "## Título\n```bash\n# comentário\n```\n### Sub\n"
