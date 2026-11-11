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
├── tools/               # make_cat_gif.py e make_icon.py (geram os assets)
├── packaging/
│   ├── run_pomodoro.py  # entry point usado pelo PyInstaller
│   └── pomodoro.iss     # script do instalador Inno Setup
├── docs/TESTE_WINDOWS.md  # checklist de testes manuais no Windows
├── .github/workflows/release-windows.yml  # build, instalador e release
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

## Versão
A versão aparece em três lugares e deve ficar igual:
- `pyproject.toml` (`version = "..."`)
- `src/pomodoro/__init__.py` (`__version__`)
- tag Git `vX.Y.Z` (dispara o workflow de release)
