# Checklist de teste no Windows

Roteiro para testar o `Pomodoro.exe` e o instalador `Pomodoro-Setup-<versão>.exe` em um Windows real. Esta lógica não foi validada em Windows durante o desenvolvimento (feito em Linux): áudio, toast, bandeja, registro e instalador precisam ser conferidos aqui.

Para cada item, marque **OK**, **Falhou** ou preencha **Observação**. Se falhar, anote a mensagem exibida, o horário e o que foi feito antes.

Preparação:
- Use o `Pomodoro.exe` gerado pelo workflow (artefato `Pomodoro-windows` ou release).
- Antes de começar, feche o app se estiver aberto e apague `%APPDATA%\Pomodoro\` para testar do zero (opcional, mas recomendado na primeira rodada).
- Deixe o volume do sistema em um nível audível.

---

## 1. Abertura e aparência

**Passos:** dê dois cliques em `Pomodoro.exe`.
**Esperado:** a janela abre (340x500), mostra "Foco", o tempo `25:00`, "Focos no ciclo: 0/4", o gato, os botões Iniciar, Reiniciar, Pular, Configurações e Estatísticas. Não aparece console.

- Resultado: ( ) OK  ( ) Falhou  Observação: ______________________

**Temas:** em **Configurações → Tema**, escolha **Padrão**, **Feminino** e **Escuro**, clicando em **Salvar** em cada um.
**Esperado:** a janela principal troca de cores logo após salvar; a troca vale sem reiniciar. Textos continuam legíveis em todos.

- Tema Padrão: ( ) OK  ( ) Falhou  Observação: __________________
- Tema Feminino: ( ) OK  ( ) Falhou  Observação: __________________
- Tema Escuro: ( ) OK  ( ) Falhou  Observação: __________________

---

## 2. Contador e controles

**Passos:**
1. Clique em **Iniciar**. Confira que o botão vira **Pausar** e o tempo desce.
2. Espere uns 10 s e clique em **Pausar**. Confira que o tempo para e o botão volta para **Iniciar**.
3. Clique em **Iniciar** de novo e confira que a contagem continua de onde parou.
4. Clique em **Pular**.
5. Clique em **Reiniciar**.

**Esperado:** o tempo desce de um em um segundo sem travar a janela. Pular passa para a pausa curta ("Pausa curta"). Reiniciar volta ao início da fase atual.

- Resultado: ( ) OK  ( ) Falhou  Observação: ______________________

---

## 3. Bloco concluído: som e toast

**Passos:** em **Configurações**, deixe a duração do foco em `1` min, pausa curta em `1` min, e ligue **Som de alerta** e **Notificação do Windows**. Salve. Clique em **Reiniciar** e depois **Iniciar**. Aguarde o fim natural do foco de 1 minuto. **Pular** não conta como bloco concluído e não dispara alerta, então não use Pular para este teste.

**Esperado:**
- Toca um som de alerta.
- Aparece um toast do Windows com o título do app e a mensagem da próxima etapa ("Hora da pausa").
- A fase muda para pausa e o contador de focos sobe para `1/4`.

Repita com os toggles desligados (um por vez, com o mesmo minuto de espera) e confirme que não há som nem toast correspondente.

- Som ligado: ( ) OK  ( ) Falhou  Observação: ______________________
- Toast ligado: ( ) OK  ( ) Falhou  Observação: ______________________
- Com som e toast desligados: ( ) OK  ( ) Falhou  Observação: ______________________

Obs.: se o toast não aparecer, verifique se as notificações do Windows estão ativas (Configurações → Sistema → Notificações) e se o modo "Não perturbe" está desligado.

---

## 4. Histórico e estatísticas

**Passos:** com alguns blocos concluídos do passo 3, clique em **Estatísticas**.

**Esperado:** abre uma janela "Estatísticas" com o total de pomodoros de hoje e da semana, e um gráfico de barras dos últimos dias. Com o app aberto, clicar de novo em **Estatísticas** traz a janela existente para frente (não abre duas). Os números batem com os blocos concluídos.

- Resultado: ( ) OK  ( ) Falhou  Observação: ______________________

---

## 5. Gato animado

**Passos:** com o timer parado (estado inicial), observe o gato por 5 s. Clique em **Iniciar** e observe por 5 s. Clique em **Pausar** e observe.

**Esperado:** o gato anima ("pãozinho") só enquanto o timer está em execução. Parado ou pausado, fica estático.

- Resultado: ( ) OK  ( ) Falhou  Observação: ______________________

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

- Liga no foco: ( ) OK  ( ) Falhou  Observação: ______________________
- Volume respeitado: ( ) OK  ( ) Falhou  Observação: ______________________
- Toggle desliga: ( ) OK  ( ) Falhou  Observação: ______________________
- Opção "só no foco" (pausa silenciosa): ( ) OK  ( ) Falhou  Observação: ______________________
- Opção "também nas pausas": ( ) OK  ( ) Falhou  Observação: ______________________

---

## 7. Pausa do ruído durante o alerta

**Passos:** com o ruído marrom tocando (passo 6) e **Som de alerta** ligado, deixe o foco acabar naturalmente.

**Esperado:** o ruído cai ou para por alguns segundos enquanto o alerta toca, e volta depois. O alerta deve ser audível por cima do ruído.

Obs.: a pausa do ruído só acontece com o som de alerta ligado (comportamento atual do código). Pular não dispara a pausa do ruído.

- Resultado: ( ) OK  ( ) Falhou  Observação: ______________________

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

- Ícone visível: ( ) OK  ( ) Falhou  Observação: ______________________
- Tooltip: ( ) OK  ( ) Falhou  Observação: ______________________
- Menu completo: ( ) OK  ( ) Falhou  Observação: ______________________
- Iniciar/Pausar pela bandeja: ( ) OK  ( ) Falhou  Observação: ______________________
- X manda para a bandeja e reabre: ( ) OK  ( ) Falhou  Observação: ______________________
- Sair pela bandeja: ( ) OK  ( ) Falhou  Observação: ______________________
- Com toggle desligado, X encerra: ( ) OK  ( ) Falhou  Observação: ______________________

---

## 9. Iniciar com o Windows

Religue **Fechar a janela manda para a bandeja** antes deste bloco, se quiser.

**Passos:**
1. Em **Configurações**, marque **Iniciar com o Windows** e clique em **Salvar**.
2. Confira a mensagem na janela principal: deve dizer "Configurações salvas e aplicadas." sem aviso de falha.
3. Abra o Editor do Registro (`regedit`) e vá em `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`. Deve existir o valor **Pomodoro** (tipo REG_SZ) com o caminho entre aspas do `Pomodoro.exe`.
4. Faça logoff e login (ou reinicie o Windows).
5. Confira que o Pomodoro abriu sozinho.
6. Em **Configurações**, desmarque **Iniciar com o Windows**, salve, e confira no `regedit` que o valor **Pomodoro** sumiu.
7. Faça logoff/login e confirme que o app não abre sozinho.

**Esperado:** a opção grava e remove o valor em HKCU (sem pedir administrador). Se o registro falhar, a janela mostra "Não foi possível atualizar 'Iniciar com o Windows'." sem fechar nem travar o app.

- Ligar grava o valor: ( ) OK  ( ) Falhou  Observação: ______________________
- Abre após login: ( ) OK  ( ) Falhou  Observação: ______________________
- Desligar remove o valor: ( ) OK  ( ) Falhou  Observação: ______________________
- Não abre após desligar: ( ) OK  ( ) Falhou  Observação: ______________________

Obs.: ao rodar pelo `.exe` instalado, o valor aponta para o `Pomodoro.exe` no caminho atual. Se o app for movido ou reinstalado em outro lugar, ligue a opção de novo para atualizar o caminho.

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
1. Execute `Pomodoro-Setup-<versão>.exe` (duplo clique). Se o SmartScreen aparecer, veja o item 12.
2. Confira o idioma do assistente (português se o compilador tinha o idioma; senão, inglês).
3. Confira que a instalação aceita o modo "somente para mim" (sem UAC) e instala em `%LOCALAPPDATA%\Programs\Pomodoro`.
4. Na tela de tarefas, confira a opção **Criar atalho na área de trabalho** marcada por padrão.
5. Conclua a instalação. Marque (ou não) "Abrir o Pomodoro" ao final.
6. Confira o atalho no **Menu Iniciar** (pasta Pomodoro) e na área de trabalho.
7. Abra o app pelo atalho.
8. Desinstale: **Configurações → Aplicativos** (ou Painel de Controle) → Pomodoro → Desinstalar. Ou use "Desinstalar Pomodoro" no menu Iniciar.
9. Confira que a pasta do programa, os atalhos e o valor **Pomodoro** em `HKCU\...\Run` foram removidos.
10. Confira que `%APPDATA%\Pomodoro` (config e histórico) foi mantido (comportamento esperado: a desinstalação não apaga os dados do usuário).

- Instalação concluída: ( ) OK  ( ) Falhou  Observação: ______________________
- Atalho no Menu Iniciar: ( ) OK  ( ) Falhou  Observação: ______________________
- Atalho na área de trabalho (tarefa marcada): ( ) OK  ( ) Falhou  Observação: ______________________
- App abre pelo atalho: ( ) OK  ( ) Falhou  Observação: ______________________
- Desinstalação remove programa e atalhos: ( ) OK  ( ) Falhou  Observação: ______________________
- Desinstalação remove o valor de inicialização: ( ) OK  ( ) Falhou  Observação: ______________________
- Dados em %APPDATA% mantidos: ( ) OK  ( ) Falhou  Observação: ______________________

Obs.: a instalação só para o usuário não pede administrador. Se escolher "para todos os usuários", o assistente pedirá UAC e instalará em Arquivos de Programas.

---

## 12. SmartScreen e antivírus

**Passos:** ao executar o `.exe` (o gerado pelo PyInstaller ou o instalador) pela primeira vez, observe se aparece o aviso do Windows Defender SmartScreen ("O Windows protegeu o computador"). Se aparecer, clique em **Mais informações** e depois em **Executar mesmo assim**. Confira também se o antivírus instalado bloqueia ou coloca o arquivo em quarentena.

**Esperado:** o app pode gerar aviso por não ter assinatura digital. O antivírus pode gerar falso positivo (o PyInstaller é conhecido por isso). Anote o que aparece para a documentação e, se houver bloqueio, registre o nome da detecção.

- Aviso SmartScreen: ( ) Apareceu  ( ) Não apareceu  Observação: ______________________
- Antivírus: ( ) Não bloqueou  ( ) Bloqueou/quarentena  Nome da detecção: ______________________

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

Versão testada: ________  Windows (versão/build): ________  Data: ________
