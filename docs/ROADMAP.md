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

- [v] **F00 · Verificação por `latest.json`** (commit 6edc9bb; actions com Node 24). Lançado em 0.0.12.
- [v] **F01 · Uma instância só** ([#1](https://github.com/lucasbehrooz/pomodoro-gatodoro/pull/1), ajustes em [#4](https://github.com/lucasbehrooz/pomodoro-gatodoro/pull/4)). Lançado em 0.0.12.
  - Abrir o app com outro já aberto traz a janela existente para frente e sai, em vez de criar um segundo Pomodoro.
  - Windows: abrir duas vezes pelo atalho; abrir com o app na bandeja.
- [v] **F02 · Atalhos de teclado** ([#2](https://github.com/lucasbehrooz/pomodoro-gatodoro/pull/2)). Lançado em 0.0.12.
  - Espaço = Iniciar/Pausar, R = Reiniciar, S = Pular, na janela principal. Não disparam em campos de texto nem nos diálogos.
- [v] **F03 · Meta diária** ([#3](https://github.com/lucasbehrooz/pomodoro-gatodoro/pull/3)). Lançado em 0.0.12.
  - Opção `daily_goal` (0 = desligada, padrão 8). Tela inicial mostra "Hoje: 3/8"; notificação ao bater a meta (uma vez por dia); linha da meta no gráfico.
- [v] **F04 · Sequência de dias** ([#5](https://github.com/lucasbehrooz/pomodoro-gatodoro/pull/5)). Lançado em 0.0.12.
  - Estatísticas mostram "Sequência: N dias" e o recorde.

## 0.0.13: ritmo dos blocos

- [ ] **F05 · Iniciar blocos automaticamente** (pequeno)
  - Opções `auto_start_breaks` e `auto_start_focus` (padrão: desligadas). Ao terminar um bloco, o próximo já começa contando.
  - Onde: `config.py`, formulário, `ui/controller.py` (após transição).
  - Testes: transição com e sem auto-início; sessão gravada corretamente.
- [~] **F06 · Aviso antes do fim** (pequeno) (#7)
  - Opção `pre_end_warning_seconds` (0 = desligado, padrão 60). Som discreto quando faltar esse tempo no foco.
  - Onde: `config.py`, `notifier.py` (som curto), `ui/controller.py` (disparar uma vez por bloco).
  - Testes: dispara uma vez, não dispara em pausa, não dispara se o bloco for menor que o aviso.
- [ ] **F07 · Dica na pausa** (pequeno)
  - A notificação de início de pausa traz uma dica aleatória ("Beba água", "Alongue o pescoço"...). Lista em `ui/tips.py` ou `tips.py`.
  - Testes: a mensagem da pausa contém uma dica da lista; foco não recebe dica.

## 0.0.14: no que eu foquei

- [ ] **F08 · Rótulo da tarefa** (médio)
  - Campo "Em que você está focando?" na tela inicial (opcional). Gravado na sessão (coluna `task` em `sessions`, com migração para bancos existentes). Estatísticas ganham "Tempo por tarefa" no período.
  - Onde: `storage.py` (migração `ALTER TABLE` idempotente), `ui/controller.py`, `ui/main_window.py`, `ui/stats.py`.
  - Testes: migração de banco antigo, gravação com e sem tarefa, agregação por tarefa.

## 0.0.15: meus dados

- [ ] **F09 · Exportar histórico para CSV** (pequeno)
  - Botão "Exportar CSV" nas Estatísticas: salva `pomodoro-historico.csv` (data, hora, fase, duração em minutos, concluída, tarefa) com diálogo "Salvar como". UTF-8 com BOM para abrir certo no Excel.
  - Testes: conteúdo e cabeçalho do CSV, acentos.
- [ ] **F10 · Mapa de calor do ano** (médio)
  - Grade de 53 semanas × 7 dias em Canvas, cor pela faixa de minutos de foco, com o tema atual.
  - Onde: `ui/stats.py` (funções puras de grade e faixa) e `ui/theme.py` (escala de cor por tema).
  - Testes: posição de cada dia, faixas, ano bissexto.

## 0.0.16: conforto

- [ ] **F11 · Modo compacto sempre no topo** (médio)
  - Botão para alternar para uma janela pequena só com o tempo e Iniciar/Pausar, sempre por cima (`-topmost`). Lembra a posição.
- [ ] **F12 · Mais sons de fundo** (médio)
  - Além do ruído marrom: rosa e branco, gerados em tempo real como o marrom. Opção `noise_color`.
  - Onde: `noise.py` (geradores puros testáveis), formulário.

## Backlog (sem versão)

- **F13 · Assinatura do executável**: exige certificado de assinatura de código (custo). Acaba com o aviso do SmartScreen.
