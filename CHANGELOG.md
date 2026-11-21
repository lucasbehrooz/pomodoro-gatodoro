# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Cada versão publicada por tag usa a seção correspondente como texto da release.

## [Não lançado]

## [1.0.0] - 2026-11-21

### Status
- **App concluído**: v1.0.0 estável com todas features core implementadas.
- Roadmap F05-F12 (9 features) + UIs completas.
- 496 testes passando, build Windows estável.

### Recursos
- Timer Pomodoro com fases (foco, pausa curta/longa)
- Histórico em SQLite com estatísticas (dia/semana/período/mês)
- Mapa de calor do ano (grid 53×7 com cores por tema)
- Temas (Padrão, Rosa, Escuro)
- Ruído de fundo (branco, rosa, marrom) com controle de volume
- Configurações completas (durações, ciclos, avisos, auto-início, etc.)
- Notificações toast Windows + som
- Bandeja do sistema com menu
- Ícone gato animado durante foco
- Atualização automática com verificação SHA-256
- Instalador Inno Setup

### Tecnologia
- Python 3.11+ com customtkinter, pystray, winotify
- PyInstaller --onefile com collect-binaries sounddevice
- SQLite para persistência
- GitHub Actions CI/CD Windows

## [0.0.18]


## [0.0.18]

### Adicionado
- **Mapa de calor do ano (F10.1)**: Canvas visual grid 53×7 com cores por tema, mostra histórico completo do ano em uma janela. Botão "Mapa do ano" em Estatísticas.
- **Modo compacto UI (F11.1)**: Janela pequena sempre no topo com timer + Iniciar/Pausar + Sair. Botão "Compacto" em MainWindow.
- **Cores de ruído multi-cor (F12.1)**: BrownNoisePlayer agora usa config.noise_color (branco/rosa/marrom) na inicialização.

## [0.0.17]


## [0.0.17]

### Alterado
- **Build Windows**: PyInstaller agora usa `--onefile` com `--collect-binaries sounddevice` para incluir todas DLLs nativas necessárias no executável único. Resolve erro "Failed to load Python DLL".

## [0.0.16]

## [0.0.16]

### Adicionado
- **Modo compacto (F11)**: opção nas Configurações para ativar janela pequena sempre no topo (só timer e botões Iniciar/Pausar). Lembra posição na próxima abertura.
- **Cores de ruído (F12)**: além do ruído marrom, agora suporta rosa (espectro ~1/f) e branco. Configurável em Configurações → Cor do ruído de fundo. Gerador multi-cor testável em noise.py.

## [0.0.15]

## [0.0.15]

### Adicionado
- **Exportar CSV**: botão "Exportar CSV" nas Estatísticas salva `pomodoro-historico.csv` com colunas: data, hora, fase, duração (min), concluída, tarefa. UTF-8 com BOM para abrir corretamente no Excel.
- **Mapa de calor do ano (Parte 1)**: estrutura de grade 53×7 (semanas × dias), agregação de minutos por dia, e escala de 5 cores por tema (vazio, baixo, médio, alto, muito). UI Canvas fica para patch 0.0.15.1.


## [0.0.14]

### Alterado
- **Rótulo da tarefa**: campo "Em que você está focando?" agora vem **desabilitado por padrão** nas Configurações. Pode ser ligado em **Configurações → Mostrar campo de tarefa na tela inicial** para quem quiser usar.

## [0.0.13]

### Adicionado
- **Iniciar blocos automaticamente**: opções **Iniciar pausas automaticamente** e **Iniciar focos automaticamente** (ligadas por padrão, como antes). Desligadas, ao fim de um bloco o próximo fica parado com a duração cheia até você clicar em **Iniciar**.
- **Aviso antes do fim do foco**: opção **Aviso antes do fim do foco** (padrão 60s, 0 desliga). Um som curto toca quando faltar este tempo no foco.
- **Dica na pausa**: cada notificação de início de pausa traz uma dica aleatória ("Beba água", "Alongue o pescoço"…) para manter a saúde em dia.
- **Rótulo da tarefa**: campo "Em que você está focando?" na tela inicial (opcional). O rótulo é gravado no histórico de cada foco. Nas **Estatísticas**, a seção "Tempo por tarefa" mostra o tempo total por tarefa no período, ordenado por tempo decrescente.

## [0.0.12]

### Adicionado
- Sequência de dias nas Estatísticas: "Sequência: N dias" conta os dias seguidos com pelo menos um foco concluído (inclui hoje se já houver foco, senão vai até ontem), ao lado do "Recorde".
- Meta diária de focos (padrão 8, 0 desliga): a tela inicial mostra "Hoje: 3/8", uma notificação comemora a meta uma vez por dia e o gráfico de Pomodoros ganha a linha da meta.
- Uma instância só: abrir o Pomodoro com outro já aberto traz a janela existente para frente (mesmo se estava na bandeja) em vez de criar um segundo app e um segundo ícone na bandeja.
- Cada release publica um `latest.json` com versão, tamanho e SHA-256 do instalador. O app verifica atualizações por ele, sem gastar o limite da API do GitHub.
- Atalhos de teclado na janela principal: **Espaço** inicia/pausa, **R** reinicia e **S** pula. A dica aparece abaixo dos botões. Segurar a tecla não repete a ação. Não disparam em campos de texto nem nas janelas de Configurações e Estatísticas.

### Alterado
- Workflow usa actions com Node 24 (checkout v7, setup-python v7, upload-artifact v7, action-gh-release v3).

### Corrigido
- "Verificar atualizações" falhava com "HTTP Error 403: rate limit exceeded" quando a rede esgotava as 60 consultas/hora da API do GitHub. Agora usa o `latest.json` e, se ainda assim cair no limite, mostra a partir de que horas tentar de novo.

## [0.0.11]

### Adicionado
- O instalador fecha sozinho o Pomodoro que estiver aberto (inclusive na bandeja) antes de instalar. O app sai normalmente, gravando o bloco em andamento; o que não fechar em 5 s é encerrado.
- Build de validação do instalador a cada push na `main` (sem publicar release).

## [0.0.10]

### Adicionado
- Seção **Atualizações** nas Configurações: mostra a versão instalada, verifica na hora e tem o botão **Atualizar para X.Y.Z**, que baixa o instalador, confere o SHA-256 e abre a instalação.

### Alterado
- O botão do aviso de nova versão na tela inicial agora é **Atualizar** e leva às Configurações.

### Corrigido
- Acentos quebrados nas notas das releases no GitHub.

## [0.0.9]

### Adicionado
- Estatísticas mostram o tempo de foco junto com a quantidade de pomodoros (hoje, semana e período escolhido). O tempo inclui focos interrompidos.
- Gráfico das estatísticas pode mostrar **Pomodoros** ou **Tempo** por dia.

### Alterado
- A janela de estatísticas aberta se atualiza sozinha quando um bloco termina ou ao usar Pular/Reiniciar.
- Seletor de período das estatísticas segue as cores do tema.

## [0.0.8]

### Adicionado
- Aviso de nova versão: ao abrir, o app consulta o GitHub e mostra "Baixar" / "Ignorar versão" quando há uma release mais nova. Pode ser desligado nas configurações.
- Build da release falha se a tag não bater com a versão do app.

## [0.0.7]

### Alterado
- Tema "Feminino" renomeado para "Rosa".
- App renomeado para Pomodoro Gatodoro (janelas, bandeja, notificações e instalador).
- Instalador com nome fixo: `pomodoro-gatodoro-x64-setup.exe`.

### Adicionado
- Licença MIT.
- Notas da release geradas a partir deste changelog.

## [0.0.6]

### Adicionado
- Estatísticas com seletor de período: 7 dias, 30 dias ou mês atual.

## [0.0.5]

### Corrigido
- Botão "Estatísticas" voltou a aparecer na parte de baixo da janela.
- Ícone do gato nas janelas de Configurações e Estatísticas.

## [0.0.4]

### Adicionado
- Opção "Iniciar com o Windows".
- Instalador (Inno Setup) com atalhos e desinstalador.
- Checklist de testes no Windows (`docs/TESTE_WINDOWS.md`).

## [0.0.3]

### Adicionado
- Ícone do gato no executável, na janela e na bandeja do sistema.

## [0.0.2]

### Adicionado
- Seletor de temas: Padrão, Feminino e Escuro.

## [0.0.1]

### Adicionado
- Primeira versão empacotada para Windows, com timer 25/5, histórico, ruído marrom,
  notificações, bandeja e gato animado.
