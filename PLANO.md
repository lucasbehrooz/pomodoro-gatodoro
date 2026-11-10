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
│   └── ui/              # janelas: timer, estatísticas, configurações
├── assets/              # ícone e sons
├── tests/
├── pyproject.toml
├── PLANO.md
└── README.md
```

## Fases de desenvolvimento

### Fase 0: Setup
- [ ] Repositório git, ambiente virtual, `pyproject.toml`, estrutura de pastas.

### Fase 1: Núcleo do timer (sem interface)
- [ ] Estados: foco, pausa curta, pausa longa, pausado, ocioso.
- [ ] Ciclo 25/5, com pausa longa de 15 min a cada 4 focos.
- [ ] Usar `time.monotonic()` para evitar drift (não `sleep()`).
- [ ] Testes unitários para transições e contagem de ciclos.

### Fase 2: Interface básica
- [ ] Janela CustomTkinter com contador e botões Iniciar / Pausar / Reiniciar / Pular.
- [ ] Tick via `after()`, sem bloquear a UI.

### Fase 3: Persistência e estatísticas
- [ ] Tabela `sessions` (tipo, início, duração, concluída).
- [ ] Tela de histórico: pomodoros de hoje e da semana.
- [ ] Gráfico de barras simples em Canvas (sem matplotlib, para não inflar o `.exe`).

### Fase 4: Configurações
- [ ] Duração de foco, pausa curta, pausa longa, ciclos até pausa longa, volume.
- [ ] Salvar em JSON e aplicar sem reiniciar.

### Fase 5: Notificações
- [ ] Som de alerta ao fim de cada bloco.
- [ ] Toast do Windows com o próximo passo ("Hora da pausa").
- [ ] Toggle para ligar/desligar cada tipo de notificação.

### Fase 6: Bandeja do sistema
- [ ] `pystray` em thread própria. Comunicação com o Tk por fila (Tk não é thread-safe).
- [ ] Minimizar para a bandeja e opção de fechar para a bandeja.
- [ ] Menu da bandeja: iniciar/pausar, abrir, sair.

### Fase 7: Ruído marrom
- [ ] Gerar ruído marrom (white noise integrado e normalizado) em buffers contínuos.
- [ ] Reproduzir em thread com `sounddevice`, com fade in/out para evitar cliques.
- [ ] Controle de volume e toggle.
- [ ] Opção de tocar só durante o foco ou também nas pausas.
- [ ] Pausar o ruído brevemente ao tocar o alerta.

### Fase 8: Empacotamento e testes no Windows
- [ ] `PyInstaller --onefile --windowed`, incluindo assets e a DLL do PortAudio.
- [ ] Teste manual em Windows: áudio, toast, bandeja, inicialização.

### Fase 9 (opcional)
- [ ] Iniciar com o Windows.
- [ ] Instalador com Inno Setup.

## Pontos de atenção

- **Ambiente de desenvolvimento:** o projeto está sendo desenvolvido em Linux. `winsound`, `winotify` e a bandeja precisam ser validados em Windows. Essas partes ficarão isoladas atrás de interfaces para que a lógica possa ser testada em qualquer sistema.
- **Antivírus:** executáveis gerados pelo PyInstaller podem receber falso positivo.
- **Concorrência de áudio:** o ruído marrom pode competir com o som de alerta. Pausar o ruído brevemente ao tocar o alerta.

## Decisões pendentes

1. **Ruído marrom:** tocar apenas no foco ou também nas pausas?
2. **Fechar a janela:** encerrar o app ou enviar para a bandeja?
3. **Idioma:** apenas português ou suporte a outros idiomas?
4. **Versão do Python:** 3.11 ou superior?
