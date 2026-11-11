---
inclusion: always
---

# Produto: Pomodoro para Windows

Aplicativo de Pomodoro para uso pessoal no Windows.

## Objetivo
Ajudar a manter foco com ciclos de 25 min de foco e 5 min de pausa curta, com pausa longa de 15 min a cada 4 focos.

## Funcionalidades (todas implementadas, versão 0.0.4)
- Timer com fases: ocioso, foco, pausa curta, pausa longa. Botões Iniciar/Pausar, Reiniciar e Pular.
- Som de alerta ao fim de cada bloco e notificação toast do Windows.
- Histórico em SQLite: pomodoros de hoje, da semana e dos últimos 7 dias, com gráfico de barras em Canvas.
- Configurações: durações, ciclos até pausa longa, volume do ruído, toggles de som, toast, ruído e "fechar para a bandeja", tema e "iniciar com o Windows".
- Ruído marrom de fundo (gerado em tempo real), tocando só no foco por padrão, pausado brevemente durante o alerta.
- Bandeja do sistema com menu (iniciar/pausar, abrir, sair).
- Gato animado (`assets/gato_pao.gif`) que anima só enquanto o timer roda.
- Temas: padrão, feminino e escuro.
- Ícone do gato no `.exe`, na janela e na bandeja.

## Restrições
- Uso pessoal. Sem assinatura digital do executável (decisão tomada).
- Interface e textos em português do Brasil.
- Dados do usuário ficam em `%APPDATA%\Pomodoro\` (config.json e pomodoro.db).

## Fonte de verdade
- `PLANO.md` registra fases e status. Mantenha os checkboxes atualizados ao concluir algo.
- `docs/TESTE_WINDOWS.md` é o roteiro de testes manuais no Windows.
