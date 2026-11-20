<!-- Gerado por tools/sync_agents.py a partir de .kiro/. Não edite aqui. -->

# Instruções do projeto

Válidas para Kiro, Claude Code e OpenCode. A fonte é `.kiro/steering/`; as skills ficam em `.kiro/skills/` (cópia em `.claude/skills/`).

## Produto: Pomodoro para Windows

Aplicativo de Pomodoro para uso pessoal no Windows.

### Objetivo
Ajudar a manter foco com ciclos de 25 min de foco e 5 min de pausa curta, com pausa longa de 15 min a cada 4 focos.

### Funcionalidades (todas implementadas; versão atual em `src/pomodoro/__init__.py`)
- Timer com fases: ocioso, foco, pausa curta, pausa longa. Botões Iniciar/Pausar, Reiniciar e Pular.
- Som de alerta ao fim de cada bloco e notificação toast do Windows.
- Histórico em SQLite: pomodoros e tempo de foco de hoje, da semana e do período (7 dias, 30 dias, mês), com gráfico de barras em Canvas que alterna entre quantidade e tempo. A janela de estatísticas aberta se atualiza sozinha.
- Configurações: durações, ciclos até pausa longa, volume do ruído, toggles de som, toast, ruído e "fechar para a bandeja", tema, "iniciar com o Windows" e "avisar quando houver nova versão".
- Atualizações: aviso de nova versão na tela inicial e seção "Atualizações" nas Configurações, que baixa o instalador da release, confere o SHA-256 e abre a instalação. A verificação usa o `latest.json` da release (sem o limite da API do GitHub).
- O instalador fecha sozinho o app aberto (mutex/evento nomeados) antes de instalar.
- Uma instância só: abrir o app de novo mostra a janela já aberta (evento `PomodoroGatodoroShow`).
- Ruído marrom de fundo (gerado em tempo real), tocando só no foco por padrão, pausado brevemente durante o alerta.
- Bandeja do sistema com menu (iniciar/pausar, abrir, sair).
- Gato animado (`assets/gato_pao.gif`) que anima só enquanto o timer roda.
- Temas: Padrão, Rosa e Escuro (chaves internas `padrao`, `feminino`, `escuro`).
- Ícone do gato no `.exe`, na janela e na bandeja.

### Restrições
- Uso pessoal. Sem assinatura digital do executável (decisão tomada).
- Interface e textos em português do Brasil.
- Dados do usuário ficam em `%APPDATA%\Pomodoro\` (config.json e pomodoro.db).

### Fonte de verdade
- `PLANO.md` registra fases e status. Mantenha os checkboxes atualizados ao concluir algo.
- `docs/TESTE_WINDOWS.md` é o roteiro de testes manuais no Windows.
- `CHANGELOG.md` registra as mudanças voltadas ao usuário; a seção de cada versão vira o texto da release.
- `docs/CONFIGURACAO.md` (usuário) e `docs/DESENVOLVIMENTO.md` (desenvolvimento e publicação) detalham o que o `README.md` resume.

## Stack e ambiente

### Linguagem e bibliotecas
- Python 3.11+ (o projeto roda em 3.11 no venv local).
- `customtkinter` para a interface, `pystray` + `Pillow` para a bandeja, `winotify` para toast (somente Windows), `numpy` + `sounddevice` para o ruído (áudio).
- `sqlite3` da stdlib para o histórico.
- `winsound` e `winreg` são importados de forma lazy e só existem no Windows.
- Testes com `pytest`.
- Empacotamento com PyInstaller; instalador com Inno Setup.
- Rede só via `urllib` da stdlib (atualizações); `ctypes` para os sinais do Windows em `instance.py`.

### Ambiente de desenvolvimento
- O desenvolvimento acontece em Linux. Não há como gerar o `.exe` localmente.
- Venv: `.venv` na raiz. Use `.venv/bin/python` e `.venv/bin/pytest`.
- Instalação em modo editável: `.venv/bin/pip install -e ".[dev]"`.
- O PortAudio não está instalado no Linux, então `import sounddevice` falha. Por isso ele é importado de forma lazy e nos testes é substituído por um módulo falso.

### Comandos úteis
- Testes: `.venv/bin/pytest -q` (sem janelas).
- Testes com janelas reais (precisam de display): `POMODORO_UI_SMOKE=1 .venv/bin/pytest -q`.
- Rodar o app: `.venv/bin/python -m pomodoro`.
- Gerar o GIF do gato: `python tools/make_cat_gif.py`.
- Gerar os ícones: `python tools/make_icon.py`.
- Regenerar AGENTS.md/CLAUDE.md/.claude a partir de `.kiro/`: `.venv/bin/python tools/sync_agents.py`.
- GitHub (releases, Actions): use o `gh` autenticado. Ao acompanhar builds, use `gh run watch <id> --interval 60`; não faça polling da API sem login (limite de 60/hora por IP, compartilhado com o app no Windows da mesma rede).

### Regras de código
- Lógica sem interface fica fora de `ui/` (ex.: `timer.py`, `storage.py`, `autostart.py`, `ui/controller.py`) e é testada sem display.
- Janelas só traduzem eventos em chamadas ao controlador.
- Tkinter não é thread-safe: callbacks de outras threads (bandeja) passam por `window.post()` ou pela fila do `TrayIcon.poll()`.
- Falhas de notificação, áudio, bandeja e registro do Windows são logadas e não derrubam o app.
- Caminhos de assets sempre via `pomodoro.assets`, que funciona no repositório e dentro do `.exe`.
- Não use `sleep()` para contar tempo. Use o clock injetado (`time.monotonic`).
- Não adicione dependências novas sem necessidade. O `.exe` deve continuar pequeno.
- Trabalho de rede ou espera roda em thread daemon e volta para a UI via `window.post()` (ver `UpdateManager`).
- Arquivos lidos/gravados no CI do Windows: sempre `encoding="utf-8"` explícito (redirecionar com `>` no Windows grava em cp1252).

### Dados e configuração
- `Config` (dataclass em `config.py`): chaves inválidas ou ausentes caem no padrão. Campos novos precisam de padrão e de teste de roundtrip.
- Nunca escreva em `%APPDATA%` dentro dos testes; use `tmp_path`.

## Estrutura do projeto

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

### Onde mexer
- Nova regra de ciclo: `timer.py` e `tests/test_timer.py`.
- Nova opção de configuração: `config.py`, `ui/settings.py`, `ui/settings_dialog.py`, e aplicação em `ui/controller.py` ou `ui/main_window.py`.
- Novo tema ou cor: `ui/theme.py`.
- Novo som ou notificação: `notifier.py`.
- Mudança no executável: `release-windows.yml` (PyInstaller) e `packaging/pomodoro.iss`.
- Atualizações: `updater.py` (lógica testável) e a seção em `ui/settings_dialog.py`. Os nomes do mutex/evento em `instance.py` precisam bater com o `[Code]` do `.iss` (`tests/test_instance.py` confere).
- Regras, skills e agentes de IA: edite em `.kiro/` (`steering/`, `skills/`, `agents/*.md`) e rode `python tools/sync_agents.py`.

### Fluxo de trabalho
- Próximas features: `docs/ROADMAP.md` (itens F01, F02... agrupados por versão).
- Cada item: branch `feat/<id>-<slug>` e pull request (agente `feature-builder`), revisão (agente `pr-reviewer`), merge feito pelo usuário.
- Versão lançada quando todos os itens dela estão mesclados (agente `release-manager`).
- Correções pequenas e documentação podem ir direto na `main` quando o usuário pedir.

### Versão
A versão aparece em três lugares e deve ficar igual:
- `pyproject.toml` (`version = "..."`)
- `src/pomodoro/__init__.py` (`__version__`)
- tag Git `vX.Y.Z` (dispara o workflow de release)

O workflow falha se a tag não bater com os dois arquivos. O app compara `__version__` com a última release para oferecer a atualização.

## Regras por área

- Ao mexer em `src/pomodoro/ui/**/*.py`, `src/pomodoro/tray.py`, `src/pomodoro/__main__.py`, siga `.kiro/steering/ui-conventions.md`.
