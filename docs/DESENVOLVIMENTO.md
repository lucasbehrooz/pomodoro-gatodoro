# Desenvolvimento

Guia para quem quer rodar o código-fonte, testar ou publicar uma versão.

## Requisitos

- Python 3.11 ou superior.
- Windows para os recursos de som, notificação, bandeja e inicialização. O código também roda em Linux para desenvolvimento e testes; nesse caso, esses recursos ficam desligados.

## Ambiente

No Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Executar

```bash
python -m pomodoro
# ou, com o venv ativo:
pomodoro
```

## Testes

```bash
pytest
```

Os testes de interface (janelas Tk de verdade) são **opt-in**, porque precisam de um display. Para rodá-los:

```bash
POMODORO_UI_SMOKE=1 pytest
```

No PowerShell:

```powershell
$env:POMODORO_UI_SMOKE = "1"; pytest
```

Os testes não gravam em `%APPDATA%`: usam diretórios temporários.

## Gerar os assets

```bash
python tools/make_cat_gif.py      # assets/gato_pao.gif
python tools/make_icon.py         # assets/gato.ico e assets/gato.png
```

## Estrutura do projeto

```
pomodoro/
├── src/pomodoro/
│   ├── __main__.py      # entry point: monta controller, janela, bandeja e polling
│   ├── assets.py        # caminhos dos assets (repositório e executável)
│   ├── timer.py         # máquina de estados do ciclo (sem GUI)
│   ├── config.py        # dataclass Config e load/save em JSON
│   ├── storage.py       # SQLite: registro e consultas de sessões
│   ├── notifier.py      # som (winsound) e toast (winotify)
│   ├── noise.py         # gerador e player de ruído marrom
│   ├── tray.py          # ícone na bandeja (pystray)
│   ├── autostart.py     # iniciar com o Windows (registro HKCU\...\Run)
│   └── ui/              # controller, janela principal, estatísticas, configurações, tema
├── assets/              # gato animado, ícone e sons
├── tests/               # testes com pytest
├── tools/               # geradores de assets e extrator do changelog
├── packaging/           # entry point do PyInstaller e script do instalador (Inno Setup)
├── docs/                # documentação (configuração, desenvolvimento, teste no Windows)
├── .github/workflows/   # build do .exe, instalador e release
├── CHANGELOG.md         # histórico de versões (usado nas notas da release)
├── PLANO.md             # plano de desenvolvimento e fases
└── pyproject.toml
```

## Publicar uma versão

O build e a release são feitos pelo GitHub Actions (`.github/workflows/release-windows.yml`). Ao enviar uma tag `vX.Y.Z`, o workflow:

1. roda os testes em Windows;
2. gera `PomodoroGatodoro.exe` com PyInstaller;
3. gera `pomodoro-gatodoro-x64-setup.exe` com Inno Setup;
4. publica os dois arquivos na release, com o texto da seção `[X.Y.Z]` do `CHANGELOG.md`.

Passos:

1. Atualize a versão em `pyproject.toml` e em `src/pomodoro/__init__.py`.
2. Mova os itens de `## [Não lançado]` para uma nova seção `## [X.Y.Z]` no `CHANGELOG.md`.
3. Rode os testes e faça o commit.
4. Crie e envie a tag:

   ```bash
   git tag -a vX.Y.Z -m "Pomodoro Gatodoro X.Y.Z"
   git push origin vX.Y.Z
   ```

Não reutilize uma tag já publicada: para corrigir, publique uma nova versão.

O `.exe` não é assinado digitalmente, por isso o SmartScreen pode avisar na primeira execução.

## Documentação relacionada

- [CONFIGURACAO.md](CONFIGURACAO.md): opções, arquivos e histórico.
- [TESTE_WINDOWS.md](TESTE_WINDOWS.md): roteiro de testes manuais no Windows.
- [PLANO.md](../PLANO.md): fases do projeto e status.
