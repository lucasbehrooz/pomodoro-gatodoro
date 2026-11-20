# Checklist de teste no Windows

Roteiro para testar o `PomodoroGatodoro.exe` e o instalador `pomodoro-gatodoro-x64-setup.exe` em um Windows real. Esta lógica não foi validada em Windows durante o desenvolvimento (feito em Linux): áudio, toast, bandeja, registro e instalador precisam ser conferidos aqui.

Para cada item, marque **OK**, **Falhou** ou preencha **Observação**. Se falhar, anote a mensagem exibida, o horário e o que foi feito antes.

Preparação:
- Use o `PomodoroGatodoro.exe` gerado pelo workflow (artefato `PomodoroGatodoro-windows` ou release).
- Antes de começar, feche o app se estiver aberto e apague `%APPDATA%\Pomodoro\` para testar do zero (opcional, mas recomendado na primeira rodada).
- Deixe o volume do sistema em um nível audível.

---

## 1. Abertura e aparência

**Passos:** dê dois cliques em `PomodoroGatodoro.exe`.
**Esperado:** a janela abre (340x500), mostra "Foco", o tempo `25:00`, "Focos no ciclo: 0/4", o gato, os botões Iniciar, Reiniciar, Pular, Configurações e Estatísticas. Não aparece console.

- Resultado: (X) OK  ( ) Falhou  Observação: ______________________

**Temas:** em **Configurações → Tema**, escolha **Padrão**, **Rosa** e **Escuro**, clicando em **Salvar** em cada um.
**Esperado:** a janela principal troca de cores logo após salvar; a troca vale sem reiniciar. Textos continuam legíveis em todos.

- Tema Padrão: (X) OK  ( ) Falhou  Observação: __________________
- Tema Rosa: (X) OK  ( ) Falhou  Observação: Renomeia para Rosa em vez de feminino
- Tema Escuro: (X) OK  ( ) Falhou  Observação: __________________

---

## 2. Contador e controles

**Passos:**
1. Clique em **Iniciar**. Confira que o botão vira **Pausar** e o tempo desce.
2. Espere uns 10 s e clique em **Pausar**. Confira que o tempo para e o botão volta para **Iniciar**.
3. Clique em **Iniciar** de novo e confira que a contagem continua de onde parou.
4. Clique em **Pular**.
5. Clique em **Reiniciar**.

**Esperado:** o tempo desce de um em um segundo sem travar a janela. Pular passa para a pausa curta ("Pausa curta"). Reiniciar volta ao início da fase atual.

- Resultado: (X) OK  ( ) Falhou  Observação: ______________________

---

## 3. Bloco concluído: som e toast

**Passos:** em **Configurações**, deixe a duração do foco em `1` min, pausa curta em `1` min, e ligue **Som de alerta** e **Notificação do Windows**. Salve. Clique em **Reiniciar** e depois **Iniciar**. Aguarde o fim natural do foco de 1 minuto. **Pular** não conta como bloco concluído e não dispara alerta, então não use Pular para este teste.

**Esperado:**
- Toca um som de alerta.
- Aparece um toast do Windows com o título do app e a mensagem da próxima etapa ("Hora da pausa").
- A fase muda para pausa e o contador de focos sobe para `1/4`.

Repita com os toggles desligados (um por vez, com o mesmo minuto de espera) e confirme que não há som nem toast correspondente.

- Som ligado: (X) OK  ( ) Falhou  Observação: ______________________
- Toast ligado: (X) OK  ( ) Falhou  Observação: ______________________
- Com som e toast desligados: (X) OK  ( ) Falhou  Observação: ______________________

Obs.: se o toast não aparecer, verifique se as notificações do Windows estão ativas (Configurações → Sistema → Notificações) e se o modo "Não perturbe" está desligado.

### 3.1. Iniciar blocos automaticamente

**Passos:** com foco e pausa curta em `1` min, ligue o **Ruído marrom**. Em **Configurações**, desmarque **Iniciar pausas automaticamente** e deixe **Iniciar focos automaticamente** marcado. Salve, clique em **Reiniciar** e **Iniciar**. Aguarde o fim natural do foco. Espere uns 20 s e clique em **Iniciar**. Aguarde o fim da pausa. Depois marque as duas opções de novo e repita.

**Esperado:**
- Desmarcada: ao fim do foco tocam som e toast, a fase muda para "Pausa curta" mostrando `01:00` parado, o botão volta para **Iniciar**, o gato para e o ruído some. Ao clicar em **Iniciar**, a pausa conta normalmente.
- Ao fim da pausa (focos automáticos ligados), o foco já começa contando sozinho.
- Nas **Estatísticas**, a pausa aparece com início no horário do clique em **Iniciar**, não no fim do foco.
- Com as duas marcadas (padrão), tudo funciona como antes: o próximo bloco sempre começa contando.

- Pausa esperando Iniciar: ( ) OK  ( ) Falhou  Observação: ______________________
- Padrão (tudo automático): ( ) OK  ( ) Falhou  Observação: ______________________

---

## 4. Histórico e estatísticas

**Passos:** com alguns blocos concluídos do passo 3, clique em **Estatísticas**.

**Esperado:** abre uma janela "Estatísticas" com o total de pomodoros de hoje, da semana e do período, cada um com o tempo de foco (ex.: "Pomodoros hoje: 2 · 50 min de foco"), e um gráfico de barras dos últimos dias. Com o app aberto, clicar de novo em **Estatísticas** traz a janela existente para frente (não abre duas). Os números batem com os blocos concluídos.

**Tempo e gráfico:**
1. Comece um foco, espere 1 minuto e clique em **Pular**. A quantidade de pomodoros não muda, mas o tempo de foco de hoje sobe cerca de 1 min (foco interrompido conta no tempo).
2. No segundo seletor, troque **Pomodoros** por **Tempo**. O gráfico passa a mostrar o tempo por dia (ex.: "25m", "1h05") e a legenda vira "Tempo de foco por dia".
3. Deixe a janela de estatísticas aberta e termine um foco (ou clique em **Reiniciar** com um foco em andamento). Os números se atualizam sozinhos, sem fechar e abrir a janela.

- Resultado: ( ) OK  ( ) Falhou  Observação: ______________________
- Tempo de foco (inclui interrompido): ( ) OK  ( ) Falhou  Observação: ______________________
- Gráfico Pomodoros/Tempo: ( ) OK  ( ) Falhou  Observação: ______________________
- Atualiza sozinha: ( ) OK  ( ) Falhou  Observação: ______________________

---

## 5. Gato animado

**Passos:** com o timer parado (estado inicial), observe o gato por 5 s. Clique em **Iniciar** e observe por 5 s. Clique em **Pausar** e observe.

**Esperado:** o gato anima ("pãozinho") só enquanto o timer está em execução. Parado ou pausado, fica estático.

- Resultado: (X) OK  ( ) Falhou  Observação: ______________________

---

## 6. Ruído marrom

**Passos:**
1. Em **Configurações**, ligue **Ruído marrom**, deixe **Ruído só durante o foco** marcado, volume em `30`. Salve.
2. Clique em **Iniciar** no foco: deve tocar um ruído de fundo suave, com fade in.
3. Mude o volume para `10` e salve. Depois para `80` e salve. Confira que o volume muda.
4. Desligue **Ruído marrom** e salve. Confira que para (fade out). Em seguida, ligue de novo.
5. Desmarque **Ruído só durante o foco**, salve, e deixe o foco terminar e a pausa começar: o ruído deve continuar na pausa.
6. Marque de novo **Ruído só durante o foco**, salve, e confirme que na pausa o ruído para.

**Esperado:** o ruído toca só quando o timer está rodando e respeita o volume e o toggle. Sem cliques audíveis no início e no fim.

- Liga no foco: (X) OK  ( ) Falhou  Observação: ______________________
- Volume respeitado: (X) OK  ( ) Falhou  Observação: ______________________
- Toggle desliga: (X) OK  ( ) Falhou  Observação: ______________________
- Opção "só no foco" (pausa silenciosa): (X) OK  ( ) Falhou  Observação: ______________________
- Opção "também nas pausas": (X) OK  ( ) Falhou  Observação: ______________________

---

## 7. Pausa do ruído durante o alerta

**Passos:** com o ruído marrom tocando (passo 6) e **Som de alerta** ligado, deixe o foco acabar naturalmente.

**Esperado:** o ruído cai ou para por alguns segundos enquanto o alerta toca, e volta depois. O alerta deve ser audível por cima do ruído.

Obs.: a pausa do ruído só acontece com o som de alerta ligado (comportamento atual do código). Pular não dispara a pausa do ruído.

- Resultado: (X) OK  ( ) Falhou  Observação: ______________________

---

## 8. Bandeja do sistema

**Passos:**
1. Confira que o ícone do gato aparece na bandeja (pode estar em "^ ícones ocultos").
2. Passe o mouse sobre o ícone: o tooltip mostra a fase e o tempo.
3. Clique com o botão direito: confira o menu **Iniciar/Pausar**, **Abrir**, separador e **Sair**.
4. Escolha **Iniciar/Pausar** pelo menu e confira que o timer alterna. Com o timer rodando, confira o ponto vermelho no ícone.
5. Com **Fechar a janela manda para a bandeja** ligado (padrão), clique no **X** da janela. A janela some e o app continua na bandeja (o timer segue rodando).
6. Clique duas vezes no ícone (ou em **Abrir**). A janela volta.
7. Com a janela fechada para a bandeja, escolha **Sair** no menu. O app fecha e o ícone some da bandeja.
8. Desligue **Fechar a janela manda para a bandeja** nas configurações, salve e clique no **X**. O app deve encerrar (não ir para a bandeja).

- Ícone visível: (X) OK  ( ) Falhou  Observação: ______________________
- Tooltip: (X) OK  ( ) Falhou  Observação: ______________________
- Menu completo: (X) OK  ( ) Falhou  Observação: ______________________
- Iniciar/Pausar pela bandeja: (X) OK  ( ) Falhou  Observação: ______________________
- X manda para a bandeja e reabre: (X) OK  ( ) Falhou  Observação: ______________________
- Sair pela bandeja: (X) OK  ( ) Falhou  Observação: ______________________
- Com toggle desligado, X encerra: (X) OK  ( ) Falhou  Observação: ______________________

### 8.1. Uma instância só

**Passos:**
1. Com o app aberto e a janela visível, abra o Pomodoro de novo pelo atalho (área de trabalho ou menu Iniciar). Não deve aparecer uma segunda janela nem um segundo ícone na bandeja; a janela existente vem para frente.
2. Minimize a janela e abra o app de novo. A janela volta e ganha o foco.
3. Feche a janela para a bandeja (**X**), clique em outro programa e abra o app de novo. A janela reaparece na frente e com foco, e o timer continua de onde estava.
4. Repita o passo 3 mais duas vezes: deve funcionar todas as vezes.
5. Confira no Gerenciador de Tarefas que só há um processo `PomodoroGatodoro.exe` depois das aberturas.

- Segunda abertura não cria janela nem ícone: ( ) OK  ( ) Falhou  Observação: ______________________
- Janela minimizada volta: ( ) OK  ( ) Falhou  Observação: ______________________
- Janela na bandeja volta com foco: ( ) OK  ( ) Falhou  Observação: ______________________
- Funciona várias vezes seguidas: ( ) OK  ( ) Falhou  Observação: ______________________
- Um processo só: ( ) OK  ( ) Falhou  Observação: ______________________

---

## 9. Iniciar com o Windows

Religue **Fechar a janela manda para a bandeja** antes deste bloco, se quiser.

**Passos:**
1. Em **Configurações**, marque **Iniciar com o Windows** e clique em **Salvar**.
2. Confira a mensagem na janela principal: deve dizer "Configurações salvas e aplicadas." sem aviso de falha.
3. Abra o Editor do Registro (`regedit`) e vá em `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`. Deve existir o valor **Pomodoro** (tipo REG_SZ) com o caminho entre aspas do `PomodoroGatodoro.exe`.
4. Faça logoff e login (ou reinicie o Windows).
5. Confira que o Pomodoro abriu sozinho.
6. Em **Configurações**, desmarque **Iniciar com o Windows**, salve, e confira no `regedit` que o valor **Pomodoro** sumiu.
7. Faça logoff/login e confirme que o app não abre sozinho.

**Esperado:** a opção grava e remove o valor em HKCU (sem pedir administrador). Se o registro falhar, a janela mostra "Não foi possível atualizar 'Iniciar com o Windows'." sem fechar nem travar o app.

- Ligar grava o valor: ( ) OK  ( ) Falhou  Observação: ______________________
- Abre após login: ( ) OK  ( ) Falhou  Observação: ______________________
- Desligar remove o valor: ( ) OK  ( ) Falhou  Observação: ______________________
- Não abre após desligar: ( ) OK  ( ) Falhou  Observação: ______________________

Obs.: ao rodar pelo `.exe` instalado, o valor aponta para o `PomodoroGatodoro.exe` no caminho atual. Se o app for movido ou reinstalado em outro lugar, ligue a opção de novo para atualizar o caminho.

---

## 10. Configuração e banco de dados

**Passos:**
1. Abra o Explorador e digite `%APPDATA%\Pomodoro` na barra de endereço.
2. Abra `config.json` (no Bloco de Notas) e confira que os valores batem com o que foi salvo nas configurações (por exemplo, `"focus_minutes"`, `"theme"`, `"start_with_windows"`).
3. Confira que existe `pomodoro.db` na mesma pasta.
4. (Opcional) Edite `config.json` com um JSON inválido (por exemplo, apague uma vírgula), salve e abra o app. O app deve abrir com os valores padrão, sem travar.
5. Restaure o `config.json` (ou apague para voltar aos padrões).

- Pasta e config.json: ( ) OK  ( ) Falhou  Observação: ______________________
- pomodoro.db criado: ( ) OK  ( ) Falhou  Observação: ______________________
- JSON inválido não quebra o app: ( ) OK  ( ) Falhou  Observação: ______________________

---

## 11. Instalador (Inno Setup)

**Passos:**
1. Execute `pomodoro-gatodoro-x64-setup.exe` (duplo clique). Se o SmartScreen aparecer, veja o item 12.
2. Confira o idioma do assistente (português se o compilador tinha o idioma; senão, inglês).
3. Confira que a instalação aceita o modo "somente para mim" (sem UAC) e instala em `%LOCALAPPDATA%\Programs\Pomodoro Gatodoro`.
4. Na tela de tarefas, confira a opção **Criar atalho na área de trabalho** marcada por padrão.
5. Conclua a instalação. Marque (ou não) "Abrir o Pomodoro Gatodoro" ao final.
6. Confira o atalho no **Menu Iniciar** (pasta Pomodoro Gatodoro) e na área de trabalho.
7. Abra o app pelo atalho.
8. Desinstale: **Configurações → Aplicativos** (ou Painel de Controle) → Pomodoro Gatodoro → Desinstalar. Ou use "Desinstalar Pomodoro Gatodoro" no menu Iniciar.
9. Confira que a pasta do programa, os atalhos e o valor **Pomodoro** em `HKCU\...\Run` foram removidos.
10. Confira que `%APPDATA%\Pomodoro` (config e histórico) foi mantido (comportamento esperado: a desinstalação não apaga os dados do usuário).
11. Instale de novo e abra o app. Inicie um foco e feche a janela para a bandeja. Rode o instalador outra vez (por cima) e clique em **Instalar** sem fechar o app: o Pomodoro deve sumir da bandeja sozinho em até 5 s, a instalação segue sem pedir para fechar nada, e o foco interrompido aparece no tempo de foco das **Estatísticas**.

- Instalação concluída: ( ) OK  ( ) Falhou  Observação: ______________________
- Atalho no Menu Iniciar: ( ) OK  ( ) Falhou  Observação: ______________________
- Atalho na área de trabalho (tarefa marcada): ( ) OK  ( ) Falhou  Observação: ______________________
- App abre pelo atalho: ( ) OK  ( ) Falhou  Observação: ______________________
- Desinstalação remove programa e atalhos: ( ) OK  ( ) Falhou  Observação: ______________________
- Desinstalação remove o valor de inicialização: ( ) OK  ( ) Falhou  Observação: ______________________
- Dados em %APPDATA% mantidos: ( ) OK  ( ) Falhou  Observação: ______________________
- Fecha o app aberto sozinho ao instalar por cima: ( ) OK  ( ) Falhou  Observação: ______________________

Obs.: a instalação só para o usuário não pede administrador. Se escolher "para todos os usuários", o assistente pedirá UAC e instalará em Arquivos de Programas.

---

## 12. SmartScreen e antivírus

**Passos:** ao executar o `.exe` (o gerado pelo PyInstaller ou o instalador) pela primeira vez, observe se aparece o aviso do Windows Defender SmartScreen ("O Windows protegeu o computador"). Se aparecer, clique em **Mais informações** e depois em **Executar mesmo assim**. Confira também se o antivírus instalado bloqueia ou coloca o arquivo em quarentena.

**Esperado:** o app pode gerar aviso por não ter assinatura digital. O antivírus pode gerar falso positivo (o PyInstaller é conhecido por isso). Anote o que aparece para a documentação e, se houver bloqueio, registre o nome da detecção.

- Aviso SmartScreen: ( ) Apareceu  ( ) Não apareceu  Observação: ______________________
- Antivírus: ( ) Não bloqueou  ( ) Bloqueou/quarentena  Nome da detecção: ______________________

---

## 13. Aviso de nova versão e atualização

Precisa de internet. Use uma versão instalada mais antiga que a última release do GitHub (ex.: instale a penúltima release). As versões 0.0.9 e anteriores não têm o botão de atualizar; ele existe a partir da versão seguinte.

**Aviso na tela inicial:**
1. Abra o app. Em alguns segundos aparece, acima dos botões de baixo, "Nova versão disponível: X.Y.Z" com **Atualizar** e **Ignorar versão**. A janela fica um pouco mais alta.
2. Clique em **Atualizar**: abrem as **Configurações**, com a seção **Atualizações** mostrando a versão nova e o botão **Atualizar para X.Y.Z**.
3. Feche as Configurações. Clique em **Ignorar versão**, feche e abra o app: o aviso não aparece mais para essa versão (`"skipped_version"` no `config.json`). Em **Configurações → Verificar atualizações** a versão continua aparecendo.
4. Desmarque **Avisar quando houver nova versão**, salve, apague `"skipped_version"` do `config.json` com o app fechado e abra de novo: nenhum aviso.

**Atualizar pelas Configurações:**
5. Em **Configurações → Atualizações**, confira "Versão instalada: …" e clique em **Verificar atualizações**: aparece "Verificando…" e depois "Nova versão disponível: X.Y.Z".
6. Clique em **Atualizar para X.Y.Z**. O progresso aparece ("Baixando… 42% (15,0 de 35,7 MB)"), depois "Abrindo o instalador…", e o app fecha.
7. O instalador abre normalmente (pode aparecer o SmartScreen: **Mais informações** → **Executar mesmo assim**). Conclua com "Abrir o Pomodoro Gatodoro" marcado.
8. O app reabre na versão nova: **Configurações → Atualizações** mostra a nova "Versão instalada", e **Verificar atualizações** diz "Você está na versão mais recente." Configurações e histórico foram mantidos.
9. Sem internet, clique em **Verificar atualizações**: aparece "Não foi possível verificar: …" e o app continua funcionando.

- Aviso aparece e Atualizar abre as Configurações: ( ) OK  ( ) Falhou  Observação: ______________________
- Ignorar versão vale após reabrir: ( ) OK  ( ) Falhou  Observação: ______________________
- Opção desligada não avisa: ( ) OK  ( ) Falhou  Observação: ______________________
- Verificar atualizações (com e sem versão nova): ( ) OK  ( ) Falhou  Observação: ______________________
- Download com progresso, instalador abre e app fecha: ( ) OK  ( ) Falhou  Observação: ______________________
- App reabre atualizado, dados mantidos: ( ) OK  ( ) Falhou  Observação: ______________________
- Sem internet: mensagem de erro, sem travar: ( ) OK  ( ) Falhou  Observação: ______________________

---

## Resumo

| Seção | Resultado geral |
|---|---|
| 1. Abertura e aparência | ( ) OK  ( ) Falhou |
| 2. Contador e controles | ( ) OK  ( ) Falhou |
| 3. Som e toast | ( ) OK  ( ) Falhou |
| 4. Histórico e estatísticas | ( ) OK  ( ) Falhou |
| 5. Gato animado | ( ) OK  ( ) Falhou |
| 6. Ruído marrom | ( ) OK  ( ) Falhou |
| 7. Pausa do ruído no alerta | ( ) OK  ( ) Falhou |
| 8. Bandeja | ( ) OK  ( ) Falhou |
| 9. Iniciar com o Windows | ( ) OK  ( ) Falhou |
| 10. Configuração e banco | ( ) OK  ( ) Falhou |
| 11. Instalador | ( ) OK  ( ) Falhou |
| 12. SmartScreen e antivírus | ( ) OK  ( ) Falhou |
| 13. Aviso de nova versão e atualização | ( ) OK  ( ) Falhou |

Versão testada: ________  Windows (versão/build): ________  Data: ________
