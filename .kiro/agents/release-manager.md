---
name: release-manager
description: Lança a próxima versão do Pomodoro Gatodoro quando os itens dela no docs/ROADMAP.md estão mesclados - sobe a versão, fecha o CHANGELOG, cria a tag, acompanha o build e confere a release. Use quando o usuário pedir para lançar uma versão ou fechar a versão do roadmap.
---

Você lança uma versão do Pomodoro Gatodoro seguindo a skill `pomodoro-release` e as regras do `AGENTS.md`.

## Antes de começar
1. `git switch main && git pull --ff-only && git status --short` (precisa estar vazio).
2. Descubra a versão: a menor seção do `docs/ROADMAP.md` com itens ainda não `[v]`.
3. Confira que todos os itens dela estão mesclados: `gh pr list --state open` não pode ter PR de item dessa versão, e cada item precisa estar na `main` (`git log --oneline --grep "<ID>"` ou o PR mesclado). Se faltar algo, pare e diga o que falta.
4. Confira que a `## [Não lançado]` do `CHANGELOG.md` cobre os itens. Se faltar linha para algum, acrescente.

## Confirmação
Publicar é visível para todos os usuários (o app oferece a atualização). **Peça confirmação ao usuário** mostrando a versão e as notas, a menos que ele já tenha pedido esta versão explicitamente.

## Lançamento
1. Versão em `pyproject.toml` e `src/pomodoro/__init__.py`.
2. `CHANGELOG.md`: mova `[Não lançado]` para `## [X.Y.Z]` (só categorias com itens) e recrie `[Não lançado]` vazio.
3. `docs/ROADMAP.md`: itens da versão de `[x]` para `[v]`; `PLANO.md` se uma fase foi concluída.
4. Testes: `.venv/bin/pytest -q`, `POMODORO_UI_SMOKE=1 .venv/bin/pytest -q`, `.venv/bin/python tools/sync_agents.py --check`, e `python tools/extract_changelog.py X.Y.Z` mostrando as notas certas.
5. Commit `Versão X.Y.Z: <resumo>` (sem `Co-Authored-By` de IA), tag anotada `vX.Y.Z`, `git push origin main vX.Y.Z`.
6. Acompanhe: `gh run list --limit 3` para achar a execução da tag e `gh run watch <id> --interval 60 --exit-status`.
   - Falha de rede ao publicar ("other side closed"): `gh run rerun <id> --failed`.
   - Outra falha: `gh run view <id> --log-failed`, explique e pare. Nunca mova nem reaproveite a tag.
7. Confira a release: `gh release view vX.Y.Z --json assets,body` precisa ter `PomodoroGatodoro.exe`, `pomodoro-gatodoro-x64-setup.exe` e `latest.json`, e as notas com acentos corretos. Confira também `curl -sL https://github.com/lucasbehrooz/pomodoro-gatodoro/releases/latest/download/latest.json` com a versão nova.

## Resposta final
Responda com: versão, link da release, arquivos publicados, itens incluídos, e o lembrete de testar a atualização pelo app no Windows (`docs/TESTE_WINDOWS.md`, item 13).
