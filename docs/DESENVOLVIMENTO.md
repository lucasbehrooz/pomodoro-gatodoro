# Desenvolvimento

Guia para quem quer rodar o código-fonte, testar ou publicar uma versão.

## Requisitos

- Python 3.11 ou superior.
- Windows para os recursos de som, notificação, bandeja e inicialização. O código também roda em Linux para desenvolvimento e testes; nesse caso, esses recursos ficam desligados.

## Ambiente

No Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Executar

```bash
python -m pomodoro
# ou, com o venv ativo:
pomodoro
```

## Testes

```bash
pytest
```

Os testes de interface (janelas Tk de verdade) são **opt-in**, porque precisam de um display. Para rodá-los:

```bash
POMODORO_UI_SMOKE=1 pytest
```

No PowerShell:

```powershell
$env:POMODORO_UI_SMOKE = "1"; pytest
```

Os testes não gravam em `%APPDATA%`: usam diretórios temporários.

## Gerar os assets

```bash
python tools/make_cat_gif.py      # assets/gato_pao.gif
python tools/make_icon.py         # assets/gato.ico e assets/gato.png
```

## Estrutura do projeto

```
pomodoro/
├── src/pomodoro/
│   ├── __main__.py      # entry point: monta controller, janela, bandeja e polling
│   ├── assets.py        # caminhos dos assets (repositório e executável)
│   ├── timer.py         # máquina de estados do ciclo (sem GUI)
│   ├── config.py        # dataclass Config e load/save em JSON
│   ├── storage.py       # SQLite: registro e consultas de sessões
│   ├── notifier.py      # som (winsound) e toast (winotify)
│   ├── noise.py         # gerador e player de ruído marrom
│   ├── tray.py          # ícone na bandeja (pystray)
│   ├── autostart.py     # iniciar com o Windows (registro HKCU\...\Run)
│   └── ui/              # controller, janela principal, estatísticas, configurações, tema
├── assets/              # gato animado, ícone e sons
├── tests/               # testes com pytest
├── tools/               # geradores de assets e extrator do changelog
├── packaging/           # entry point do PyInstaller e script do instalador (Inno Setup)
├── docs/                # documentação (configuração, desenvolvimento, teste no Windows)
├── .github/workflows/   # build do .exe, instalador e release
├── CHANGELOG.md         # histórico de versões (usado nas notas da release)
├── PLANO.md             # plano de desenvolvimento e fases
└── pyproject.toml
```

## Instruções para agentes de IA (Kiro, Claude Code, OpenCode)

A fonte única fica em `.kiro/`: regras em `.kiro/steering/` e skills em `.kiro/skills/`. Depois de editar, rode:

```bash
.venv/bin/python tools/sync_agents.py
```

O script gera:

| Arquivo gerado | Usado por |
|---|---|
| `AGENTS.md` (regras sempre ativas) | OpenCode (e Kiro) |
| `CLAUDE.md` (importa o `AGENTS.md`) | Claude Code |
| `.claude/rules/*.md` (regras com `fileMatch`, viram `paths:`) | Claude Code |
| `.claude/skills/*` (cópia das skills) | Claude Code e OpenCode |
| `.claude/agents/*.md` | Claude Code |
| `.opencode/agents/*.md` (`mode: subagent`) | OpenCode |
| `.kiro/agents/*.json` (gerado a partir de `.kiro/agents/*.md`) | Kiro CLI |

Não edite os arquivos gerados. `tests/test_agents_sync.py` falha se eles estiverem diferentes do que o script geraria.

## Roadmap e agentes

O plano das próximas versões fica em `docs/ROADMAP.md`. Três agentes automatizam o ciclo, cada um com uma tarefa:

| Agente | Faz | Não faz |
|---|---|---|
| `feature-builder` | Pega um item (ex.: F03), cria `feat/<id>-<slug>`, implementa com testes e docs, abre o PR e acompanha o CI | merge, tag, release |
| `pr-reviewer` | Roda os testes do branch numa worktree, confere convenções e critérios de aceite e publica a revisão no PR | alterar código, aprovar, merge |
| `release-manager` | Com os itens da versão mesclados: sobe a versão, fecha o `CHANGELOG.md`, cria a tag, acompanha o build e confere a release | lançar sem confirmação; mover tag |

Ciclo de uma versão:

1. "Use o agente feature-builder para implementar o próximo item do roadmap" (repita para cada item).
2. "Use o agente pr-reviewer no PR #N".
3. Você mescla o PR no GitHub (`gh pr merge N --squash`, por exemplo).
4. Com todos os itens da versão mesclados: "Use o agente release-manager para lançar a versão".

No Claude Code os agentes aparecem em `/agents`; no OpenCode, como subagentes; no Kiro CLI, em `.kiro/agents/`. O CI roda testes e build nos pull requests, então o PR mostra se o instalador ainda compila.

Os agentes usam o `gh` autenticado (`gh auth login`).

## Publicar uma versão

O build e a release são feitos pelo GitHub Actions (`.github/workflows/release-windows.yml`). Ao enviar uma tag `vX.Y.Z`, o workflow:

1. roda os testes em Windows;
2. confere se a tag bate com a versão em `pyproject.toml` e `src/pomodoro/__init__.py` (se não bater, o build falha);
3. gera `PomodoroGatodoro.exe` com PyInstaller;
4. gera `pomodoro-gatodoro-x64-setup.exe` com Inno Setup;
5. gera `latest.json` (versão, tamanho e SHA-256 do instalador) com `tools/make_latest_json.py`;
6. publica o `.exe`, o instalador e o `latest.json` na release, com o texto da seção `[X.Y.Z]` do `CHANGELOG.md`.

Passos:

1. Atualize a versão em `pyproject.toml` e em `src/pomodoro/__init__.py`.
2. Mova os itens de `## [Não lançado]` para uma nova seção `## [X.Y.Z]` no `CHANGELOG.md`.
3. Rode os testes e faça o commit.
4. Crie e envie a tag:

   ```bash
   git tag -a vX.Y.Z -m "Pomodoro Gatodoro X.Y.Z"
   git push origin vX.Y.Z
   ```

Não reutilize uma tag já publicada: para corrigir, publique uma nova versão.

Todo push na `main` que mexa em `src/`, `packaging/`, `pyproject.toml` ou no workflow também roda o build completo (testes, `.exe` e instalador), sem publicar release. Os arquivos ficam como artefato da execução, na aba Actions. Assim um erro no `packaging/pomodoro.iss` aparece antes da tag.

O instalador fecha o app aberto pelo mutex `PomodoroGatodoroRunning` e pelo evento `PomodoroGatodoroQuit` (`src/pomodoro/instance.py` e a seção `[Code]` do `.iss`). Se mudar os nomes, mude dos dois lados: `tests/test_instance.py` confere.

O app compara `__version__` com a última release do GitHub para mostrar o aviso de nova versão (`src/pomodoro/updater.py`). Por isso as duas versões precisam acompanhar a tag. Rascunhos e pré-releases não disparam o aviso.

O `.exe` não é assinado digitalmente, por isso o SmartScreen pode avisar na primeira execução.

## Documentação relacionada

- [CONFIGURACAO.md](CONFIGURACAO.md): opções, arquivos e histórico.
- [TESTE_WINDOWS.md](TESTE_WINDOWS.md): roteiro de testes manuais no Windows.
- [PLANO.md](../PLANO.md): fases do projeto e status.
