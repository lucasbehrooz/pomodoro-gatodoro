# Plano de Desenvolvimento - Pomodoro para Windows

Aplicativo de Pomodoro para Windows, com timer 25/5, notificações, histórico de sessões, bandeja do sistema e ruído marrom de fundo.

## Stack e bibliotecas

| Função | Escolha | Motivo |
|---|---|---|
| Interface | `customtkinter` | Visual moderno sobre Tkinter, sem dependências pesadas |
| Bandeja | `pystray` + `Pillow` | Ícone na system tray com menu |
| Notificação Windows | `winotify` | Toast nativo; `win10toast` está abandonado |
| Som de alerta | `winsound` (stdlib) | Sem dependência extra, apenas Windows |
| Ruído marrom | `numpy` + `sounddevice` | Geração em tempo real, em loop contínuo |
| Histórico | `sqlite3` (stdlib) | Banco local simples |
| Configuração | JSON em `%APPDATA%\Pomodoro\` | Legível e fácil de editar |
| Empacotamento | `PyInstaller` | Gera `.exe` standalone |

Python 3.11 ou superior (a confirmar).

## Estrutura do projeto

```
pomodoro/
├── src/pomodoro/
│   ├── __main__.py      # entry point
│   ├── timer.py         # máquina de estados (sem GUI, testável)
│   ├── config.py        # dataclass + load/save JSON
│   ├── storage.py       # SQLite: registro e consultas de sessões
│   ├── notifier.py      # som + toast do Windows
│   ├── noise.py         # gerador e player de ruído marrom
│   ├── tray.py          # ícone na bandeja
│   ├── autostart.py     # iniciar com o Windows (HKCU\Run)
│   └── ui/              # janelas: timer, estatísticas, configurações
├── assets/              # ícone e sons
├── tests/
├── pyproject.toml
├── PLANO.md
└── README.md
```

## Fases de desenvolvimento

### Fase 0: Setup
- [x] Repositório git, ambiente virtual, `pyproject.toml`, estrutura de pastas.

### Fase 1: Núcleo do timer (sem interface)
- [x] Estados: foco, pausa curta, pausa longa, pausado, ocioso.
- [x] Ciclo 25/5, com pausa longa de 15 min a cada 4 focos.
- [x] Usar `time.monotonic()` para evitar drift (não `sleep()`).
- [x] Testes unitários para transições e contagem de ciclos.

### Fase 2: Interface básica
- [x] Janela CustomTkinter com contador e botões Iniciar / Pausar / Reiniciar / Pular.
- [x] Tick via `after()`, sem bloquear a UI.

### Fase 3: Persistência e estatísticas
- [x] Tabela `sessions` (tipo, início, duração, concluída).
- [x] Tela de histórico: pomodoros de hoje e da semana.
- [x] Gráfico de barras simples em Canvas (sem matplotlib, para não inflar o `.exe`).

### Fase 4: Configurações
- [x] Duração de foco, pausa curta, pausa longa, ciclos até pausa longa, volume.
- [x] Salvar em JSON e aplicar sem reiniciar. (Durações com timer em andamento valem a partir do próximo Reiniciar.)

### Fase 5: Notificações
- [x] Som de alerta ao fim de cada bloco.
- [x] Toast do Windows com o próximo passo ("Hora da pausa").
- [x] Toggle para ligar/desligar cada tipo de notificação.

### Fase 6: Bandeja do sistema
- [x] `pystray` em thread própria. Comunicação com o Tk por fila (Tk não é thread-safe).
- [x] Minimizar para a bandeja e opção de fechar para a bandeja.
- [x] Menu da bandeja: iniciar/pausar, abrir, sair.

### Fase 7: Ruído marrom
- [x] Gerar ruído marrom (white noise integrado e normalizado) em buffers contínuos.
- [x] Reproduzir em thread com `sounddevice`, com fade in/out para evitar cliques.
- [x] Controle de volume e toggle.
- [x] Opção de tocar só durante o foco ou também nas pausas.
- [x] Pausar o ruído brevemente ao tocar o alerta.

### Extras
- [x] Gato animado fazendo pãozinho enquanto o timer executa (`assets/gato_pao.gif`, gerado por `tools/make_cat_gif.py`; pode ser substituído por um GIF real).
- [x] README.md na raiz.

### Fase 8: Empacotamento e testes no Windows
- [x] `PyInstaller --onefile --windowed`, incluindo assets (feito pelo workflow `release-windows.yml`). A DLL do PortAudio vem do pacote `sounddevice`; confirmar no teste que o áudio funciona no `.exe`.
- [ ] Teste manual em Windows: áudio, toast, bandeja, inicialização. (Feito pelo usuário, ver `docs/TESTE_WINDOWS.md`.)

### Fase 9 (opcional)
- [x] Iniciar com o Windows (`autostart.py`, valor HKCU\...\Run; opção em Configurações). Validação no Windows: `docs/TESTE_WINDOWS.md`, item 9.
- [x] Instalador com Inno Setup (`packaging/pomodoro.iss`, gerado pelo workflow). Não compilado localmente; validação: `docs/TESTE_WINDOWS.md`, item 11.

## Pontos de atenção

- **Ambiente de desenvolvimento:** o projeto está sendo desenvolvido em Linux. `winsound`, `winotify` e a bandeja precisam ser validados em Windows. Essas partes ficarão isoladas atrás de interfaces para que a lógica possa ser testada em qualquer sistema.
- **Antivírus:** executáveis gerados pelo PyInstaller podem receber falso positivo.
- **Concorrência de áudio:** o ruído marrom pode competir com o som de alerta. Pausar o ruído brevemente ao tocar o alerta.

## Decisões pendentes

1. **Ruído marrom:** tocar apenas no foco ou também nas pausas? (padrão adotado: apenas no foco)
2. **Fechar a janela:** encerrar o app ou enviar para a bandeja? (padrão adotado: bandeja)
3. **Idioma:** apenas português ou suporte a outros idiomas? (padrão adotado: apenas português)
4. **Versão do Python:** 3.11 ou superior? (padrão adotado: 3.11+)
