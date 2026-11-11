# Pomodoro Gatodoro

![Gato fazendo pãozinho](assets/gato_pao.gif)

Um timer Pomodoro para Windows com um gatinho que faz pãozinho enquanto você estuda ou trabalha.

- **Ciclo 25/5:** 25 minutos de foco, 5 de pausa, e 15 de pausa longa a cada 4 focos.
- **Ruído marrom de fundo:** para ajudar a manter a concentração.
- **Avisos:** som e notificação do Windows quando um bloco termina.
- **Histórico:** veja quantos pomodoros você fez hoje, na semana ou no mês.
- **Bandeja:** o app pode ficar minimizado no canto da tela.
- **Temas:** Padrão, Rosa e Escuro.

## Como instalar

1. Acesse a página de [Releases](https://github.com/lucasbehrooz/pomodoro-gatodoro/releases) e abra a versão mais recente.
2. Baixe um dos arquivos:
   - `pomodoro-gatodoro-x64-setup.exe`: instalador, com atalhos no menu Iniciar e na área de trabalho. **Recomendado.**
   - `PomodoroGatodoro.exe`: versão sem instalação. Basta abrir.
3. Dê dois cliques no arquivo baixado.

**Aviso do Windows:** o app ainda não tem assinatura digital, então o Windows pode mostrar a mensagem "O Windows protegeu o computador". Clique em **Mais informações** e depois em **Executar mesmo assim**.

## Como usar

- **Iniciar:** clique em **Iniciar** para começar um foco de 25 minutos.
- **Pausar:** clique em **Pausar** e depois em **Iniciar** para continuar.
- **Reiniciar:** volta o bloco atual ao começo.
- **Pular:** passa para o próximo bloco.
- **Configurações:** ajuste os tempos, os sons, o ruído, o tema e a inicialização com o Windows.
- **Estatísticas:** veja os pomodoros concluídos por dia, na semana ou no mês.

Fechar a janela pode enviar o app para a bandeja, perto do relógio. Clique com o botão direito no ícone para pausar, abrir ou sair.

## Onde ficam seus dados

Configurações e histórico ficam em `%APPDATA%\Pomodoro\`. Os detalhes estão em [docs/CONFIGURACAO.md](docs/CONFIGURACAO.md).

## Para desenvolvedores

Instruções de instalação do código-fonte, testes, estrutura do projeto e publicação de versões estão em [docs/DESENVOLVIMENTO.md](docs/DESENVOLVIMENTO.md).

Quer contribuir? Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).
