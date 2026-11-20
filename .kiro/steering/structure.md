---
inclusion: always
---

# Estrutura do projeto

```
pomodoro/
├── src/pomodoro/
│   ├── __main__.py      # entry point: monta controller, janela, bandeja e loop de polling
│   ├── assets.py        # caminhos dos assets (repositório e executável PyInstaller)
│   ├── timer.py         # máquina de estados do timer (sem GUI)
│   ├── config.py        # dataclass Config + load/save JSON
│   ├── storage.py       # SQLite: sessões e consultas de contagem
│   ├── notifier.py      # som (winsound) e toast (winotify), com NullNotifier
│   ├── noise.py         # BrownNoiseGenerator + BrownNoisePlayer (sounddevice)
│   ├── tray.py          # TrayIcon (pystray em thread própria, fila de eventos)
│   ├── autostart.py     # "Iniciar com o Windows" via registro HKCU\...\Run
│   ├── updater.py       # verificar/baixar/abrir atualização (latest.json, API como reserva) + UpdateManager
│   ├── instance.py      # mutex/eventos nomeados: instância única e fechamento pelo instalador
│   └── ui/
│       ├── controller.py       # PomodoroController: lógica sem widgets
│       ├── main_window.py      # MainWindow (CTk): só traduz eventos
│       ├── settings.py         # conversão e validação do formulário (puro)
│       ├── settings_dialog.py  # SettingsDialog (CTkToplevel)
│       ├── stats.py            # funções puras + StatsWindow
│       ├── cat.py              # gato animado
│       └── theme.py            # paletas e aplicação de tema
├── tests/               # pytest; test_ui_* e smokes têm opt-in por POMODORO_UI_SMOKE=1
├── assets/              # gato_pao.gif, gato.ico, gato.png
├── tools/
│   ├── make_cat_gif.py, make_icon.py  # geram os assets
│   ├── extract_changelog.py           # seção do CHANGELOG -> notas da release (UTF-8)
│   ├── make_latest_json.py            # latest.json publicado em cada release
│   └── sync_agents.py                 # gera AGENTS.md, CLAUDE.md e .claude/ a partir de .kiro/
├── packaging/
│   ├── run_pomodoro.py  # entry point usado pelo PyInstaller
│   └── pomodoro.iss     # instalador Inno Setup ([Code] fecha o app aberto)
├── docs/                # TESTE_WINDOWS.md, CONFIGURACAO.md, DESENVOLVIMENTO.md
├── .github/workflows/release-windows.yml  # build em tag (release) e em push na main (validação)
├── .kiro/               # fonte das regras (steering) e skills dos agentes de IA
├── AGENTS.md, CLAUDE.md, .claude/  # gerados por tools/sync_agents.py; não edite
├── CHANGELOG.md         # mudanças por versão; vira o texto da release
├── PLANO.md             # fases e status
├── README.md
└── pyproject.toml       # versão do projeto (fonte: version = "x.y.z")
```

## Onde mexer
- Nova regra de ciclo: `timer.py` e `tests/test_timer.py`.
- Nova opção de configuração: `config.py`, `ui/settings.py`, `ui/settings_dialog.py`, e aplicação em `ui/controller.py` ou `ui/main_window.py`.
- Novo tema ou cor: `ui/theme.py`.
- Novo som ou notificação: `notifier.py`.
- Mudança no executável: `release-windows.yml` (PyInstaller) e `packaging/pomodoro.iss`.
- Atualizações: `updater.py` (lógica testável) e a seção em `ui/settings_dialog.py`. Os nomes do mutex/evento em `instance.py` precisam bater com o `[Code]` do `.iss` (`tests/test_instance.py` confere).
- Regras, skills e agentes de IA: edite em `.kiro/` (`steering/`, `skills/`, `agents/*.md`) e rode `python tools/sync_agents.py`.

## Fluxo de trabalho
- Próximas features: `docs/ROADMAP.md` (itens F01, F02... agrupados por versão).
- Cada item: branch `feat/<id>-<slug>` e pull request (agente `feature-builder`), revisão (agente `pr-reviewer`), merge feito pelo usuário.
- Versão lançada quando todos os itens dela estão mesclados (agente `release-manager`).
- Correções pequenas e documentação podem ir direto na `main` quando o usuário pedir.

## Versão
A versão aparece em três lugares e deve ficar igual:
- `pyproject.toml` (`version = "..."`)
- `src/pomodoro/__init__.py` (`__version__`)
- tag Git `vX.Y.Z` (dispara o workflow de release)

O workflow falha se a tag não bater com os dois arquivos. O app compara `__version__` com a última release para oferecer a atualização.
