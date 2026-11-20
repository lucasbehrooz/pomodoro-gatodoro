# Configuração e dados

## Onde ficam os arquivos

Tudo fica na pasta `%APPDATA%\Pomodoro\`, por exemplo `C:\Users\seu-usuario\AppData\Roaming\Pomodoro\`. Para abrir, digite `%APPDATA%\Pomodoro` na barra de endereço do Explorador de Arquivos.

- `config.json`: suas preferências.
- `pomodoro.db`: o histórico de pomodoros.

Você pode alterar tudo pela tela **Configurações**. Editar o `config.json` à mão também funciona, desde que o app esteja fechado.

Se o `config.json` não existir ou estiver corrompido, o app usa os valores padrão abaixo. Chaves desconhecidas são ignoradas.

## Opções

| Chave | Padrão | Descrição |
|---|---|---|
| `focus_minutes` | `25` | Duração do foco, em minutos |
| `short_break_minutes` | `5` | Duração da pausa curta, em minutos |
| `long_break_minutes` | `15` | Duração da pausa longa, em minutos |
| `cycles_before_long_break` | `4` | Quantidade de focos até a pausa longa |
| `daily_goal` | `8` | Meta diária de focos concluídos, de `0` a `24` (`0` desliga). Ver [Meta diária](#meta-diária) |
| `sound_enabled` | `true` | Toca o som de alerta ao fim de cada bloco |
| `toast_enabled` | `true` | Mostra a notificação do Windows |
| `brown_noise_enabled` | `false` | Liga o ruído marrom |
| `brown_noise_focus_only` | `true` | Ruído só no foco (`false` toca também nas pausas) |
| `brown_noise_volume` | `0.3` | Volume do ruído, de `0.0` a `1.0` |
| `close_to_tray` | `true` | Fechar a janela envia o app para a bandeja |
| `theme` | `padrao` | Tema: `padrao`, `feminino` (Rosa) ou `escuro` |
| `start_with_windows` | `false` | Abre o app junto com o Windows |
| `check_updates` | `true` | Ao abrir, verifica se há versão nova no GitHub |
| `skipped_version` | `""` | Versão marcada em **Ignorar versão** (não é avisada de novo) |

Alterações de duração feitas com um timer em andamento valem a partir do próximo **Reiniciar**.

## Meta diária

Com `daily_goal` maior que zero, a tela inicial mostra quantos focos você concluiu hoje e a meta, por exemplo "Hoje: 3/8" (com "· meta batida" depois de alcançá-la). Só contam focos concluídos, pelo dia local em que começaram. Com `0`, nada aparece.

No foco que alcança a meta, o app mostra uma notificação comemorativa (se a notificação do Windows estiver ligada). Ela aparece uma vez por dia: o app compara a contagem do dia antes e depois de cada foco concluído, então fechar e abrir o app não repete o aviso. Nas **Estatísticas**, o gráfico de **Pomodoros** ganha uma linha tracejada "Meta N" na altura da meta.

## Histórico

O banco `pomodoro.db` tem a tabela `sessions`, com um registro por bloco. Cada registro guarda a fase (`focus`, `short_break` ou `long_break`), o início em ISO 8601 no horário local, a duração em segundos e se o bloco foi concluído. A quantidade de pomodoros conta apenas focos concluídos. O tempo de foco soma todos os focos, inclusive os interrompidos (pausas não entram).

O histórico é mantido indefinidamente. Para apagá-lo, feche o app e remova o arquivo `pomodoro.db`.

## Iniciar com o Windows

Quando ativada, a opção grava o caminho do executável em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, com o nome `Pomodoro`. Se você mover o `.exe` de pasta, desligue e ligue a opção de novo. Desinstalar pelo instalador remove essa entrada.

## Atualizações

### Aviso na tela inicial

Com `check_updates` ligado, o app consulta a última release publicada no GitHub (`api.github.com`) uma vez a cada abertura. Se houver versão mais nova, aparece um aviso na janela principal:

- **Atualizar** abre as **Configurações**, na seção de atualizações.
- **Ignorar versão** grava essa versão em `skipped_version`. O aviso volta só quando sair uma versão mais nova que ela.

Sem internet, a verificação ao abrir falha em silêncio.

A consulta usa o arquivo `latest.json` publicado em cada release, baixado pelo link `releases/latest/download/latest.json`. Esse link não tem o limite de 60 consultas por hora da API do GitHub, que vale para toda a rede (mesmo IP). A API só é usada como reserva, para releases antigas sem o arquivo. Se ela também estiver no limite, as Configurações mostram "O GitHub limitou as consultas desta rede por um tempo. Tente de novo depois das HH:MM."

### Seção "Atualizações" nas Configurações

Mostra a versão instalada e o botão **Verificar atualizações**, que consulta o GitHub na hora (mesmo com `check_updates` desligado ou com a versão ignorada). Havendo versão nova, aparece **Atualizar para X.Y.Z**:

1. O app baixa `pomodoro-gatodoro-x64-setup.exe` da release para a pasta temporária, mostrando o progresso.
2. Confere o tamanho e o SHA-256 informados pelo GitHub. Se não bater, o arquivo é apagado e nada é executado.
3. Abre o instalador normal, com as telas de sempre, e fecha o app para os arquivos poderem ser substituídos. No fim da instalação, a opção "Abrir o Pomodoro Gatodoro" reabre o app já atualizado.

O instalador não é assinado digitalmente, então o SmartScreen pode avisar ("O Windows protegeu o computador"): clique em **Mais informações** → **Executar mesmo assim**. Quem usa o `PomodoroGatodoro.exe` sem instalação passa a ter a versão instalada depois de atualizar.

Configurações e histórico ficam em `%APPDATA%\Pomodoro\` e não são afetados pela atualização.

### Pomodoro aberto durante a instalação

Não precisa fechar o app antes de instalar. Ao clicar em **Instalar**, o instalador pede para todo Pomodoro aberto (inclusive o que está só na bandeja) fechar. Ele fecha como no **Sair** da bandeja, gravando o bloco em andamento no histórico. O que não fechar em 5 segundos, como versões até a 0.0.10, que não atendem o pedido, é encerrado à força. Nesse caso o bloco em andamento não é gravado.
