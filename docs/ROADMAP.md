# Roadmap de features

Plano das próximas versões. Cada item vira **um branch e um pull request**. Uma versão é lançada quando todos os itens dela estiverem mesclados na `main`.

Fluxo (ver `docs/DESENVOLVIMENTO.md`, seção "Agentes"):

1. `feature-builder` pega o próximo item `[ ]` da versão atual, cria `feat/<id>-<slug>`, implementa, testa e abre o PR.
2. `pr-reviewer` revisa o PR, roda os testes e comenta. O usuário decide o merge.
3. Com todos os itens da versão mesclados, `release-manager` sobe a versão, atualiza o `CHANGELOG.md`, cria a tag e confere a release.

Status: `[ ]` a fazer · `[~]` PR aberto (com link) · `[x]` mesclado · `[v]` lançado na versão indicada.

Regras para todos os itens:
- Textos em português do Brasil; cores só via `ui/theme.py`; lógica fora da janela e testada sem display.
- Opção nova em `Config` precisa de padrão, roundtrip e valor inválido caindo no padrão; aparece em `docs/CONFIGURACAO.md`.
- Mudança visível ao usuário entra em `## [Não lançado]` do `CHANGELOG.md` e, se tiver passo manual, em `docs/TESTE_WINDOWS.md`.

---

## 0.0.12: atualização robusta e uso diário

- [x] **F00 · Verificação por `latest.json`** (já na `main`, commit 6edc9bb). Só falta lançar.
- [~] **F01 · Uma instância só** (pequeno) ([#1](https://github.com/lucasbehrooz/pomodoro-gatodoro/pull/1))
  - Abrir o app com outro já aberto traz a janela existente para frente e sai, em vez de criar um segundo Pomodoro.
  - Onde: `instance.py` (o mutex `PomodoroGatodoroRunning` já existe; detectar `ERROR_ALREADY_EXISTS` e sinalizar um evento `PomodoroGatodoroShow`), `__main__.py` (escutar e chamar `window.show_window` via `post`).
  - Aceite: segunda abertura não cria janela nem ícone na bandeja; a primeira aparece e ganha foco, mesmo se estava na bandeja.
  - Testes: lógica de "já existe" com kernel32 falso; nomes batendo com o `.iss` continuam passando.
  - Windows: abrir duas vezes pelo atalho; abrir com o app na bandeja.
- [ ] **F02 · Atalhos de teclado** (pequeno)
  - Espaço = Iniciar/Pausar, R = Reiniciar, S = Pular, na janela principal. Não disparar quando o foco estiver em campo de texto (diálogos).
  - Onde: `ui/main_window.py` (bind na janela, chamando os mesmos handlers dos botões).
  - Aceite: atalhos funcionam com a janela em foco; botões mostram a dica (ex.: tooltip ou texto "Espaço").
  - Testes: smoke com `event_generate` chamando os handlers.

## 0.0.13: motivação

- [~] **F03 · Meta diária** (pequeno) (#3)
  - Opção `daily_goal` (0 = desligada, padrão 8, faixa 0 a 24). Tela inicial mostra "Hoje: 3/8"; ao bater a meta, uma notificação comemorativa (uma vez por dia).
  - Onde: `config.py`, `ui/settings.py`, `ui/settings_dialog.py`, `ui/controller.py` (contagem do dia e "meta batida"), `ui/main_window.py`, `ui/stats.py` (linha da meta no gráfico de quantidade).
  - Testes: contagem do dia, notificação só uma vez, linha da meta na geometria.
- [ ] **F04 · Sequência de dias** (pequeno)
  - Estatísticas mostram "Sequência: 5 dias" (dias seguidos com pelo menos 1 foco concluído, contando hoje se já houver, senão até ontem) e o recorde.
  - Onde: `storage.py` (consulta de dias com foco), `ui/stats.py` (função pura `streak(days, today)`).
  - Testes: sequência com buraco, hoje sem foco ainda, recorde.

## 0.0.14: ritmo dos blocos

- [ ] **F05 · Iniciar blocos automaticamente** (pequeno)
  - Opções `auto_start_breaks` e `auto_start_focus` (padrão: desligadas). Ao terminar um bloco, o próximo já começa contando.
  - Onde: `config.py`, formulário, `ui/controller.py` (após transição).
  - Testes: transição com e sem auto-início; sessão gravada corretamente.
- [ ] **F06 · Aviso antes do fim** (pequeno)
  - Opção `pre_end_warning_seconds` (0 = desligado, padrão 60). Som discreto quando faltar esse tempo no foco.
  - Onde: `config.py`, `notifier.py` (som curto), `ui/controller.py` (disparar uma vez por bloco).
  - Testes: dispara uma vez, não dispara em pausa, não dispara se o bloco for menor que o aviso.
- [ ] **F07 · Dica na pausa** (pequeno)
  - A notificação de início de pausa traz uma dica aleatória ("Beba água", "Alongue o pescoço"...). Lista em `ui/tips.py` ou `tips.py`.
  - Testes: a mensagem da pausa contém uma dica da lista; foco não recebe dica.

## 0.0.15: no que eu foquei

- [ ] **F08 · Rótulo da tarefa** (médio)
  - Campo "Em que você está focando?" na tela inicial (opcional). Gravado na sessão (coluna `task` em `sessions`, com migração para bancos existentes). Estatísticas ganham "Tempo por tarefa" no período.
  - Onde: `storage.py` (migração `ALTER TABLE` idempotente), `ui/controller.py`, `ui/main_window.py`, `ui/stats.py`.
  - Testes: migração de banco antigo, gravação com e sem tarefa, agregação por tarefa.

## 0.0.16: meus dados

- [ ] **F09 · Exportar histórico para CSV** (pequeno)
  - Botão "Exportar CSV" nas Estatísticas: salva `pomodoro-historico.csv` (data, hora, fase, duração em minutos, concluída, tarefa) com diálogo "Salvar como". UTF-8 com BOM para abrir certo no Excel.
  - Testes: conteúdo e cabeçalho do CSV, acentos.
- [ ] **F10 · Mapa de calor do ano** (médio)
  - Grade de 53 semanas × 7 dias em Canvas, cor pela faixa de minutos de foco, com o tema atual.
  - Onde: `ui/stats.py` (funções puras de grade e faixa) e `ui/theme.py` (escala de cor por tema).
  - Testes: posição de cada dia, faixas, ano bissexto.

## 0.0.17: conforto

- [ ] **F11 · Modo compacto sempre no topo** (médio)
  - Botão para alternar para uma janela pequena só com o tempo e Iniciar/Pausar, sempre por cima (`-topmost`). Lembra a posição.
- [ ] **F12 · Mais sons de fundo** (médio)
  - Além do ruído marrom: rosa e branco, gerados em tempo real como o marrom. Opção `noise_color`.
  - Onde: `noise.py` (geradores puros testáveis), formulário.

## Backlog (sem versão)

- **F13 · Assinatura do executável**: exige certificado de assinatura de código (custo). Acaba com o aviso do SmartScreen.
