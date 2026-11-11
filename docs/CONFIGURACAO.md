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
| `sound_enabled` | `true` | Toca o som de alerta ao fim de cada bloco |
| `toast_enabled` | `true` | Mostra a notificação do Windows |
| `brown_noise_enabled` | `false` | Liga o ruído marrom |
| `brown_noise_focus_only` | `true` | Ruído só no foco (`false` toca também nas pausas) |
| `brown_noise_volume` | `0.3` | Volume do ruído, de `0.0` a `1.0` |
| `close_to_tray` | `true` | Fechar a janela envia o app para a bandeja |
| `theme` | `padrao` | Tema: `padrao`, `feminino` (Rosa) ou `escuro` |
| `start_with_windows` | `false` | Abre o app junto com o Windows |

Alterações de duração feitas com um timer em andamento valem a partir do próximo **Reiniciar**.

## Histórico

O banco `pomodoro.db` tem a tabela `sessions`, com um registro por bloco. Cada registro guarda a fase (`focus`, `short_break` ou `long_break`), o início em ISO 8601 no horário local, a duração em segundos e se o bloco foi concluído. As estatísticas contam apenas focos concluídos.

O histórico é mantido indefinidamente. Para apagá-lo, feche o app e remova o arquivo `pomodoro.db`.

## Iniciar com o Windows

Quando ativada, a opção grava o caminho do executável em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, com o nome `Pomodoro`. Se você mover o `.exe` de pasta, desligue e ligue a opção de novo. Desinstalar pelo instalador remove essa entrada.
