# Como contribuir

Obrigado pelo interesse em ajudar no Pomodoro Gatodoro. O projeto é pequeno e pessoal, então contribuições menores são bem-vindas.

## Antes de começar

- Para correções pequenas, pode abrir um pull request direto.
- Para mudanças maiores (nova funcionalidade, mudança de comportamento), abra uma **issue** antes para alinhar a ideia.
- Relatos de bug também são bem-vindos em Issues. Inclua a versão (está no `pyproject.toml` e na página da release), o que você fez e o que aconteceu.

## Preparar o ambiente

```bash
git clone https://github.com/lucasbehrooz/pomodoro-gatodoro.git
cd pomodoro-gatodoro
python -m venv .venv
source .venv/bin/activate      # no Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

Detalhes sobre execução, testes de interface e publicação estão em [docs/DESENVOLVIMENTO.md](docs/DESENVOLVIMENTO.md).

## Antes de abrir um pull request

- A suíte precisa passar: `pytest`.
- Se mexeu em janelas ou no tema, rode também `POMODORO_UI_SMOKE=1 pytest`.
- Se a mudança afeta o usuário, adicione uma linha em `## [Não lançado]` no `CHANGELOG.md`.
- Atualize a documentação relevante (`README.md` para o usuário, `docs/` para o restante).

## Padrões do projeto

- **Lógica fora da interface:** regras de tempo, histórico e notificações ficam fora de `src/pomodoro/ui/` e são testadas sem janela.
- **Janelas finas:** a janela só chama o controlador e atualiza os widgets.
- **Cores só em `ui/theme.py`:** não coloque cores fixas nos widgets.
- **Textos em português do Brasil,** com acentuação.
- **Sem dependências novas sem necessidade:** o executável precisa continuar pequeno.
- **Testes sem efeito colateral:** não grave em `%APPDATA%`; use diretórios temporários.

## Commits e mensagens

Mensagens curtas no imperativo ou no presente, em português, descrevendo o que mudou. Exemplo: `Corrige contagem de focos após pular bloco`.

## Licença

Ao contribuir, você concorda que sua contribuição será distribuída sob a [licença MIT](LICENSE), a mesma do projeto.
