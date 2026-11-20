# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Cada versão publicada por tag usa a seção correspondente como texto da release.

## [Não lançado]

## [0.0.12]

### Adicionado
- Sequência de dias nas Estatísticas: "Sequência: N dias" conta os dias seguidos com pelo menos um foco concluído (inclui hoje se já houver foco, senão vai até ontem), ao lado do "Recorde".
- Meta diária de focos (padrão 8, 0 desliga): a tela inicial mostra "Hoje: 3/8", uma notificação comemora a meta uma vez por dia e o gráfico de Pomodoros ganha a linha da meta.
- Uma instância só: abrir o Pomodoro com outro já aberto traz a janela existente para frente (mesmo se estava na bandeja) em vez de criar um segundo app e um segundo ícone na bandeja.
- Cada release publica um `latest.json` com versão, tamanho e SHA-256 do instalador. O app verifica atualizações por ele, sem gastar o limite da API do GitHub.
- Atalhos de teclado na janela principal: **Espaço** inicia/pausa, **R** reinicia e **S** pula. A dica aparece abaixo dos botões. Segurar a tecla não repete a ação. Não disparam em campos de texto nem nas janelas de Configurações e Estatísticas.
- Opções **Iniciar pausas automaticamente** e **Iniciar focos automaticamente** (ligadas por padrão, como antes). Desligadas, ao fim de um bloco o próximo fica parado com a duração cheia até você clicar em **Iniciar**.

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
