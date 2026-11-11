# Pomodoro Gatodoro para Windows

![Gato fazendo pãozinho](assets/gato_pao.gif)

Aplicativo de Pomodoro para Windows. Alterna blocos de foco (25 min) e pausas curtas (5 min), com uma pausa longa (15 min) a cada 4 focos. Traz ruído marrom de fundo, notificações do Windows, histórico de sessões e ícone na bandeja do sistema.

## Funcionalidades

- Ciclo 25/5 com pausa longa a cada 4 focos. Durações e ciclos são configuráveis.
- Controles de Iniciar/Pausar, Reiniciar e Pular, com contagem de focos no ciclo atual.
- Som de alerta e notificação do Windows (toast) ao fim de cada bloco. Cada tipo pode ser desligado.
- Ruído marrom gerado em tempo real, com volume ajustável. Pode tocar só no foco ou também nas pausas. Ele é pausado brevemente ao tocar o alerta.
- Tela de estatísticas com pomodoros de hoje, da semana (segunda a domingo) e dos últimos 7 dias, e um gráfico de barras diário.
- Ícone na bandeja com menu (Iniciar/Pausar, Abrir, Sair). Fechar a janela pode enviá-la para a bandeja.
- Configurações salvas em JSON e aplicadas sem reiniciar. Durações alteradas com um timer em andamento valem a partir do próximo Reiniciar.

## Instalação para desenvolvedores

### Requisitos

- Python 3.11 ou superior.
- Windows para os recursos de som, toast e bandeja. O código também roda em Linux para desenvolvimento e testes, sem esses recursos.

### Ambiente

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

A instalação em modo editável registra o comando `pomodoro` (definido em `[project.scripts]` no `pyproject.toml`).

### Executar

```bash
python -m pomodoro
# ou, com o venv ativo:
pomodoro
```

## Testes

```bash
pytest
```

A suíte cobre o timer, a configuração, o armazenamento, as estatísticas, o ruído, o notificador e o controlador da UI.

Os testes de interface (`tests/test_ui_window.py` e `tests/test_stats.py`) abrem janelas Tk de verdade. Por isso são **opt-in** e ficam desligados por padrão. Para executá-los, é preciso um display disponível:

```bash
POMODORO_UI_SMOKE=1 pytest tests/test_ui_window.py tests/test_stats.py
```

No PowerShell:

```powershell
$env:POMODORO_UI_SMOKE = "1"; pytest tests/test_ui_window.py tests/test_stats.py
```

## Configuração

As preferências ficam em `%APPDATA%\Pomodoro\config.json`. Se o arquivo não existir ou estiver corrompido, o app usa os padrões abaixo. Chaves desconhecidas são ignoradas. Chaves ausentes assumem o padrão. Também é possível alterar tudo pela tela de Configurações.

| Chave | Padrão | Descrição |
|---|---|---|
| `focus_minutes` | `25` | Duração do foco, em minutos |
| `short_break_minutes` | `5` | Duração da pausa curta, em minutos |
| `long_break_minutes` | `15` | Duração da pausa longa, em minutos |
| `cycles_before_long_break` | `4` | Quantidade de focos até a pausa longa |
| `sound_enabled` | `true` | Toca o som de alerta ao fim de cada bloco |
| `toast_enabled` | `true` | Mostra a notificação do Windows |
| `brown_noise_enabled` | `false` | Liga o ruído marrom |
| `brown_noise_focus_only` | `true` | Ruído só durante o foco (`false` toca também nas pausas) |
| `brown_noise_volume` | `0.3` | Volume do ruído, de `0.0` a `1.0` |
| `close_to_tray` | `true` | Fechar a janela envia o app para a bandeja |

Fora do Windows, o diretório de configuração é `~/.config/Pomodoro/`.

## Dados

O histórico fica no banco SQLite `%APPDATA%\Pomodoro\pomodoro.db`, na tabela `sessions`. Cada registro guarda a fase (`focus`, `short_break` ou `long_break`), o início em ISO 8601 no horário local, a duração em segundos e se a sessão foi concluída. As estatísticas contam apenas focos concluídos.

## Estrutura do projeto

```
pomodoro/
├── src/pomodoro/
│   ├── __main__.py      # entry point (main)
│   ├── timer.py         # máquina de estados do ciclo (sem GUI)
│   ├── config.py        # dataclass Config e load/save em JSON
│   ├── storage.py       # SQLite: registro e consultas de sessões
│   ├── notifier.py      # som (winsound) e toast (winotify)
│   ├── noise.py         # gerador e player de ruído marrom
│   ├── tray.py          # ícone na bandeja (pystray)
│   └── ui/              # controller, janela principal, estatísticas e configurações
├── assets/              # ícone, sons e imagens
├── tests/               # testes com pytest
├── pyproject.toml
├── PLANO.md             # plano de desenvolvimento e fases
└── README.md
```

## Status

Versão atual: 0.0.6. O andamento das fases está em [PLANO.md](PLANO.md). O app foi testado no Windows, e as versões são publicadas em [Releases](https://github.com/lucasbehrooz/pomodoro/releases), com o executável `PomodoroGatodoro.exe` e um instalador.

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).
