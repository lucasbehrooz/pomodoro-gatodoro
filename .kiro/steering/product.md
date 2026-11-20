---
inclusion: always
---

# Produto: Pomodoro para Windows

Aplicativo de Pomodoro para uso pessoal no Windows.

## Objetivo
Ajudar a manter foco com ciclos de 25 min de foco e 5 min de pausa curta, com pausa longa de 15 min a cada 4 focos.

## Funcionalidades (todas implementadas; versão atual em `src/pomodoro/__init__.py`)
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

## Restrições
- Uso pessoal. Sem assinatura digital do executável (decisão tomada).
- Interface e textos em português do Brasil.
- Dados do usuário ficam em `%APPDATA%\Pomodoro\` (config.json e pomodoro.db).

## Fonte de verdade
- `PLANO.md` registra fases e status. Mantenha os checkboxes atualizados ao concluir algo.
- `docs/TESTE_WINDOWS.md` é o roteiro de testes manuais no Windows.
- `CHANGELOG.md` registra as mudanças voltadas ao usuário; a seção de cada versão vira o texto da release.
- `docs/CONFIGURACAO.md` (usuário) e `docs/DESENVOLVIMENTO.md` (desenvolvimento e publicação) detalham o que o `README.md` resume.
