---
name: pomodoro-release
description: Publish a new Pomodoro version - bump version in pyproject.toml and __init__.py, run tests, commit, push, and create tag vX.Y.Z so GitHub Actions builds PomodoroGatodoro.exe and the installer and publishes the release. Use when the user asks for a new version, release, tag, exe build, or instalador.
---

# Publicar uma nova versão do Pomodoro

Use este procedimento para gerar um novo `PomodoroGatodoro.exe` e instalador para download nas releases do GitHub.

## Pré-requisitos
- Trabalhe na branch `main`, com a árvore limpa (`git status`).
- Use a chave SSH do repositório: `GIT_SSH_COMMAND="ssh -i <caminho-da-sua-chave> -o IdentitiesOnly=yes"`. Exporte essa variável antes dos comandos `git push`.

## Passos

1. **Escolha a versão.** Use SemVer simples: `0.0.x` para correções e pequenas funções, `0.x.0` para funcionalidades maiores. Confirme com o usuário se houver dúvida.

2. **Atualize a versão em dois lugares:**
   - `pyproject.toml`: linha `version = "X.Y.Z"`
   - `src/pomodoro/__init__.py`: `__version__ = "X.Y.Z"`

3. **Rode os testes:**
   ```bash
   .venv/bin/pytest -q
   POMODORO_UI_SMOKE=1 .venv/bin/pytest -q
   ```
   Se algo falhar, não publique. Corrija antes.

4. **Atualize o `PLANO.md`** se a versão trouxe funcionalidade nova ou concluiu uma fase.

4b. **Atualize o `CHANGELOG.md`** (obrigatório antes da tag):
   - Crie a seção `## [X.Y.Z]` logo abaixo de `## [Não lançado]`, movendo para ela os itens que estavam em "Não lançado".
   - Use as categorias Adicionado, Alterado, Corrigido ou Removido, em português, uma linha por mudança voltada ao usuário.
   - Deixe `## [Não lançado]` vazio, com as mesmas categorias, para a próxima versão.
   - O workflow usa essa seção como texto da release. Sem ela, a release sai só com a mensagem padrão.

5. **Commit e push:**
   ```bash
   git add pyproject.toml src/pomodoro/__init__.py PLANO.md CHANGELOG.md
   git commit -m "Versão X.Y.Z: <resumo>"
   git push origin main
   ```

6. **Crie a tag anotada e envie:**
   ```bash
   git tag -a vX.Y.Z -m "Pomodoro X.Y.Z: <resumo>"
   git push origin vX.Y.Z
   ```
   O push da tag dispara `.github/workflows/release-windows.yml`, que:
   - roda os testes em Windows;
   - gera `dist/PomodoroGatodoro.exe` com PyInstaller (`--icon assets/gato.ico`);
   - gera `dist/pomodoro-gatodoro-x64-setup.exe` com Inno Setup (`packaging/pomodoro.iss`);
   - publica os dois arquivos na release da tag.

7. **Confirme o resultado.** Verifique `git ls-remote --tags origin` e informe ao usuário o endereço:
   `https://github.com/lucasbehrooz/pomodoro/releases/tag/vX.Y.Z`
   Se o build falhar, o log fica em **Actions → Build Windows**.

## Regras
- **Nunca** mova ou reutilize uma tag que já foi publicada. Para corrigir, publique uma nova versão.
- **Não** faça `git push --force`.
- A publicação é visível para o usuário, então confirme antes de criar a tag, a menos que ele já tenha pedido a versão explicitamente.
- O `.exe` não é assinado. O SmartScreen pode avisar na primeira execução; isso é esperado para uso pessoal.

## Verificação no Windows
Depois de publicar, o usuário testa com `docs/TESTE_WINDOWS.md`. Se encontrar falha, registre no `PLANO.md` e crie a correção em uma nova versão.
