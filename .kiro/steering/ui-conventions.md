---
inclusion: fileMatch
fileMatchPattern: ["src/pomodoro/ui/**/*.py", "src/pomodoro/tray.py", "src/pomodoro/__main__.py"]
---

# Convenções de interface

## Threads
- Todos os widgets são criados e alterados na thread do Tk.
- A bandeja roda em outra thread. Eventos dela vão para a fila de `TrayIcon` e são executados em `poll()`, chamado pelo `after()` em `__main__.py`. Use `window.post(fn)` quando precisar executar algo na UI a partir de outra thread.
- Nunca chame `mainloop`, `update` ou `sleep` dentro de callbacks.

## Lógica fora da janela
- Novas regras (transições, registro de sessão, notificações, ruído) entram em `ui/controller.py`, não na janela.
- A janela só chama métodos do controlador e atualiza rótulos. Teste a lógica sem display.

## Tema
- Toda cor nova passa por `ui/theme.py`. Não coloque cores fixas em widgets.
- Os três temas (`padrao`, `feminino`, `escuro`) precisam de todos os campos preenchidos, e o texto precisa manter contraste mínimo de 4,5:1.
- O tema `padrao` usa `None` nos campos de cor para seguir o modo claro/escuro do sistema.
- Ao criar um widget novo, aplique a paleta atual e garanta que trocar o tema em execução atualize o widget.

## Textos e idioma
- Rótulos e mensagens em português do Brasil, com acentuação.
- Mensagens de erro para o usuário são curtas e não mostram traceback.

## Acessibilidade mínima
- Botões com texto claro e alvo de clique razoável (não reduza abaixo de 28 px de altura).
- Não dependa só de cor para indicar estado: o texto da fase e o botão Iniciar/Pausar também indicam.

## Testes
- Use `POMODORO_UI_SMOKE=1` para testes que criam janelas reais. Por padrão eles são pulados.
- Após mudar layout, rode o smoke para garantir que a janela constrói nos três temas.
