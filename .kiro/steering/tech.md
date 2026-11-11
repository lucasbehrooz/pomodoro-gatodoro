---
inclusion: always
---

# Stack e ambiente

## Linguagem e bibliotecas
- Python 3.11+ (o projeto roda em 3.11 no venv local).
- `customtkinter` para a interface, `pystray` + `Pillow` para a bandeja, `winotify` para toast (somente Windows), `numpy` + `sounddevice` para o ruído (áudio).
- `sqlite3` da stdlib para o histórico.
- `winsound` e `winreg` são importados de forma lazy e só existem no Windows.
- Testes com `pytest`.
- Empacotamento com PyInstaller; instalador com Inno Setup.

## Ambiente de desenvolvimento
- O desenvolvimento acontece em Linux. Não há como gerar o `.exe` localmente.
- Venv: `.venv` na raiz. Use `.venv/bin/python` e `.venv/bin/pytest`.
- Instalação em modo editável: `.venv/bin/pip install -e ".[dev]"`.
- O PortAudio não está instalado no Linux, então `import sounddevice` falha. Por isso ele é importado de forma lazy e nos testes é substituído por um módulo falso.

## Comandos úteis
- Testes: `.venv/bin/pytest -q` (sem janelas).
- Testes com janelas reais (precisam de display): `POMODORO_UI_SMOKE=1 .venv/bin/pytest -q`.
- Rodar o app: `.venv/bin/python -m pomodoro`.
- Gerar o GIF do gato: `python tools/make_cat_gif.py`.
- Gerar os ícones: `python tools/make_icon.py`.

## Regras de código
- Lógica sem interface fica fora de `ui/` (ex.: `timer.py`, `storage.py`, `autostart.py`, `ui/controller.py`) e é testada sem display.
- Janelas só traduzem eventos em chamadas ao controlador.
- Tkinter não é thread-safe: callbacks de outras threads (bandeja) passam por `window.post()` ou pela fila do `TrayIcon.poll()`.
- Falhas de notificação, áudio, bandeja e registro do Windows são logadas e não derrubam o app.
- Caminhos de assets sempre via `pomodoro.assets`, que funciona no repositório e dentro do `.exe`.
- Não use `sleep()` para contar tempo. Use o clock injetado (`time.monotonic`).
- Não adicione dependências novas sem necessidade. O `.exe` deve continuar pequeno.

## Dados e configuração
- `Config` (dataclass em `config.py`): chaves inválidas ou ausentes caem no padrão. Campos novos precisam de padrão e de teste de roundtrip.
- Nunca escreva em `%APPDATA%` dentro dos testes; use `tmp_path`.
