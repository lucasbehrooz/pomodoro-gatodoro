---
name: pomodoro-feature
description: Implement a new feature or change in the Pomodoro app with tests and PLANO.md tracking - config option, timer rule, UI control, theme color, or notification. Use when the user asks to add, change, or fix a behavior of the Pomodoro app.
---

# Implementar uma funcionalidade no Pomodoro

Siga este fluxo para qualquer mudança de comportamento. Ele evita regressões em áreas sensíveis (threads, áudio, registro do Windows).

## 1. Entenda onde a mudança entra
Consulte `.kiro/steering/structure.md`:
- Regra de tempo ou ciclo: `timer.py`.
- Regra que envolve sessão, notificação ou ruído: `ui/controller.py`.
- Apenas visual: `ui/main_window.py`, `ui/settings_dialog.py`, `ui/theme.py`.
- Nova opção persistente: `config.py` + formulário em `ui/settings.py`.

## 2. Escreva o teste primeiro (quando for lógica)
- Lógica pura: teste em `tests/test_<módulo>.py`, sem display e sem Windows.
- Opção nova de configuração: campo com padrão, teste de roundtrip e teste de valor inválido caindo no padrão.
- Não grave em `%APPDATA%` dentro de testes: use `tmp_path`.

## 3. Implemente
- Mantenha a janela fina: ela só chama o controlador.
- Se tocar em threads ou bandeja, use `window.post()` ou a fila do `TrayIcon`.
- Se usar código exclusivo do Windows (`winsound`, `winreg`, `winotify`), importe dentro de função e trate a falha com log.
- Cores só via `ui/theme.py`.

## 4. Verifique
```bash
.venv/bin/pytest -q
POMODORO_UI_SMOKE=1 .venv/bin/pytest -q
```
Se o smoke falhar com erro de Tk, corrija antes de seguir. A aparência real só pode ser conferida no Windows.

## 5. Registre
- Atualize `PLANO.md`: marque o item feito ou adicione o novo item.
- Se a mudança afeta o usuário final, atualize `README.md` (funcionalidades ou configuração).
- Se afeta o roteiro de teste manual, acrescente o caso em `docs/TESTE_WINDOWS.md`.

## 6. Entregue
- Mostre ao usuário o que mudou, quais testes passaram e o que só ele pode validar no Windows.
- Não faça commit, push ou tag sem pedido explícito. Para publicar uma versão, use a skill `pomodoro-release`.

## Checklist rápido
- [ ] Teste de lógica criado e passando
- [ ] Suíte completa passando
- [ ] Smoke de janela passando (se tocou em UI)
- [ ] Nenhuma cor fixa fora de `theme.py`
- [ ] Textos em português
- [ ] `PLANO.md` atualizado
